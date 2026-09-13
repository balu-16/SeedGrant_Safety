"""Notification orchestration + FCM v1 provider tests (isolated, no live services)."""

import json

from app.core.config import Settings
from app.notifications.fcm import FcmV1Provider
from app.notifications.service import (
    MockNotificationProvider,
    NotificationService,
    build_notifications,
)
from tests.conftest import FakeGuardians, FakePushTokens


def _settings(**overrides) -> Settings:
    base = dict(
        env="test",
        database_url="",
        jwt_secret="test-secret-that-is-long-enough-for-tests-123",
        jwt_algorithm="HS256",
        access_token_expire_minutes=15,
        refresh_token_expire_days=7,
        cors_origins=["*"],
        testing=True,
    )
    base.update(overrides)
    return Settings(**base)


class FakeResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeHttpClient:
    """Stands in for httpx.AsyncClient: serves OAuth tokens + scripted FCM results."""

    def __init__(self, results: dict[str, FakeResponse] | None = None) -> None:
        self.results = results or {}
        self.posts: list[dict] = []

    async def post(self, url: str, **kwargs) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        if "oauth2.googleapis.com/token" in url:
            return FakeResponse(200, {"access_token": "fake-access", "expires_in": 3600})
        token = (kwargs.get("json") or {}).get("message", {}).get("token", "")
        return self.results.get(token, FakeResponse(200, {"name": "projects/x/messages/1"}))


def _creds_file(tmp_path) -> str:
    """Service-account JSON with a throwaway openssl-generated RSA key (test-only)."""
    import subprocess

    key_pem = subprocess.run(["openssl", "genrsa", "2048"], capture_output=True, text=True, check=True).stdout
    import jwt as pyjwt

    assert pyjwt.encode({"a": 1}, key_pem, algorithm="RS256")
    p = tmp_path / "sa.json"
    p.write_text(
        json.dumps(
            {
                "type": "service_account",
                "project_id": "seedgrant-naveen",
                "private_key_id": "kid-1",
                "private_key": key_pem,
                "client_email": "test@seedgrant-naveen.iam.gserviceaccount.com",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )
    )
    return str(p)


async def _seed_owner_with_guardian(push: FakePushTokens, guards: FakeGuardians) -> tuple[str, str]:
    from app.core.security import hash_token_value

    owner, guardian = "owner-1", "guardian-1"
    await push.upsert(user_id=owner, token_hash=hash_token_value("fcm-owner"), platform="android", token="fcm-owner")
    await push.upsert(user_id=guardian, token_hash=hash_token_value("fcm-guard"), platform="android", token="fcm-guard")
    g = await guards.create(
        protected_user_id=owner,
        guardian_email="g@example.com",
        guardian_user_id=guardian,
    )
    await guards.update_status(g["id"], "accepted")
    pending = await guards.create(protected_user_id=owner, guardian_email="p@example.com")
    assert pending["status"] == "pending"
    return owner, guardian


class RecordingProvider:
    provider_name = "recording"

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def send_to_tokens(self, *, tokens: list[str], title: str, body: str, data: dict):
        from app.notifications.service import TokenSendReport

        self.calls.append({"tokens": list(tokens), "title": title, "body": body, "data": data})
        return TokenSendReport(delivered=list(tokens))


async def test_audience_includes_owner_and_accepted_guardian_only():
    push, guards = FakePushTokens(), FakeGuardians()
    owner, guardian = await _seed_owner_with_guardian(push, guards)
    provider = RecordingProvider()
    svc = NotificationService(provider).bind(push_tokens=push, guardians=guards)  # type: ignore[arg-type]
    res = await svc.notify_emergency_created(protected_user_id=owner, emergency_id="e1", trigger_type="sos")
    assert res.provider == "recording"
    assert set(res.delivered_to) == {owner, guardian}
    sent_tokens = provider.calls[0]["tokens"]
    assert set(sent_tokens) == {"fcm-owner", "fcm-guard"}
    assert provider.calls[0]["data"]["kind"] == "emergency-created"


async def test_invalid_tokens_are_pruned(tmp_path):
    push, guards = FakePushTokens(), FakeGuardians()
    owner, guardian = await _seed_owner_with_guardian(push, guards)
    http = FakeHttpClient(
        {
            "fcm-owner": FakeResponse(
                400, {"error": {"status": "INVALID_ARGUMENT", "details": [{"errorCode": "UNREGISTERED"}]}}
            ),
            "fcm-guard": FakeResponse(200, {"name": "projects/x/messages/2"}),
        }
    )
    creds = _creds_file(tmp_path)
    provider = FcmV1Provider(
        credentials_path=creds,
        project_id="seedgrant-naveen",
        http_client=http,  # type: ignore[arg-type]
    )
    svc = NotificationService(provider).bind(push_tokens=push, guardians=guards)  # type: ignore[arg-type]
    await svc.notify_emergency_created(protected_user_id=owner, emergency_id="e2", trigger_type="sos")
    assert await push.tokens_for_users([owner]) == []  # dead token pruned
    remaining = await push.tokens_for_users([guardian])
    assert [r["token"] for r in remaining] == ["fcm-guard"]


async def test_fcm_payload_shape_and_dry_run(tmp_path):
    creds = _creds_file(tmp_path)
    http = FakeHttpClient()
    provider = FcmV1Provider(
        credentials_path=creds,
        project_id="seedgrant-naveen",
        dry_run=True,
        http_client=http,  # type: ignore[arg-type]
    )
    report = await provider.send_to_tokens(
        tokens=["tok-1"], title="SOS triggered", body="Emergency e via sos", data={"kind": "x", "n": 3}
    )
    assert report.delivered == ["tok-1"]
    send = [p for p in http.posts if "messages:send" in p["url"]][0]
    assert send["url"] == "https://fcm.googleapis.com/v1/projects/seedgrant-naveen/messages:send"
    assert send["headers"]["Authorization"] == "Bearer fake-access"
    msg = send["json"]["message"]
    assert msg["token"] == "tok-1"
    assert msg["android"]["priority"] == "high"
    assert msg["android"]["notification"]["channel_id"] == "sos"
    assert msg["data"] == {"kind": "x", "n": "3"}
    assert send["json"]["validate_only"] is True


async def test_build_notifications_selection(tmp_path):
    assert isinstance(build_notifications(_settings())._provider, MockNotificationProvider)
    assert isinstance(build_notifications(_settings(push_provider="bogus"))._provider, MockNotificationProvider)
    # fcm requested but no credentials file -> safe fallback
    assert isinstance(
        build_notifications(
            _settings(push_provider="fcm", fcm_project_id="p", fcm_credentials_path="/nonexistent.json")
        )._provider,
        MockNotificationProvider,
    )
    creds = _creds_file(tmp_path)
    svc = build_notifications(
        _settings(push_provider="fcm", fcm_project_id="seedgrant-naveen", fcm_credentials_path=creds)
    )
    assert isinstance(svc._provider, FcmV1Provider)


async def test_mock_mode_without_repos_stays_log_only():
    svc = NotificationService()
    res = await svc.notify_emergency_created(protected_user_id="u", emergency_id="e", trigger_type="sos")
    assert res.provider == "mock" and res.delivered_to == ["u"]


async def test_auth_failure_marks_failed_not_invalid(tmp_path):
    class AuthFailClient(FakeHttpClient):
        async def post(self, url: str, **kwargs) -> FakeResponse:
            self.posts.append({"url": url, **kwargs})
            raise RuntimeError("network down")

    creds = _creds_file(tmp_path)
    provider = FcmV1Provider(
        credentials_path=creds,
        project_id="seedgrant-naveen",
        http_client=AuthFailClient(),  # type: ignore[arg-type]
    )
    report = await provider.send_to_tokens(tokens=["t1"], title="t", body="b", data={})
    assert report.failed == ["t1"] and not report.invalid
