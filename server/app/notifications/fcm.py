"""FCM HTTP v1 provider (direct delivery, no Expo push service in the loop).

Auth uses the Firebase service-account JSON with a manually-minted OAuth2 JWT
assertion (PyJWT + httpx only — no google-auth dependency). Access tokens are
cached until ~5 minutes before expiry.
"""

import json
import time

import httpx
import jwt

from app.core.logging import get_logger
from app.notifications.service import TokenSendReport

log = get_logger(__name__)

_FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
_FCM_ENDPOINT = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
# Must match the Android notification channel created by the client.
SOS_CHANNEL_ID = "sos"

_UNREGISTERED_CODE = "UNREGISTERED"


def _is_dead_token(code: str, details: list) -> bool:
    """Only token-scoped FCM errors may prune; payload-level errors must not.

    A bare INVALID_ARGUMENT is frequently payload-level (oversized message,
    bad data field) and says nothing about the token's health.
    """
    if code == _UNREGISTERED_CODE:
        return True
    if code == "INVALID_ARGUMENT":
        return any(
            isinstance(violation, dict) and "token" in str(violation.get("field", ""))
            for detail in details
            if isinstance(detail, dict)
            for violation in (detail.get("fieldViolations") or [])
        )
    return False


class FcmV1Provider:
    """Send to native FCM device tokens via the HTTP v1 API."""

    def __init__(
        self,
        *,
        credentials_path: str,
        project_id: str,
        dry_run: bool = False,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._credentials_path = credentials_path
        self._project_id = project_id
        self._dry_run = dry_run
        self._http = http_client
        self._owns_client = http_client is None
        self._cached_token: str | None = None
        self._cached_expiry: float = 0.0

    @property
    def provider_name(self) -> str:
        return "fcm"

    async def _access_token(self) -> str:
        if self._cached_token and time.time() < self._cached_expiry - 300:
            return self._cached_token
        with open(self._credentials_path, encoding="utf-8") as f:
            creds = json.load(f)
        now = int(time.time())
        assertion = jwt.encode(
            {
                "iss": creds["client_email"],
                "scope": _FCM_SCOPE,
                "aud": creds["token_uri"],
                "iat": now,
                "exp": now + 3600,
            },
            creds["private_key"],
            algorithm="RS256",
            headers={"kid": creds.get("private_key_id")},
        )
        client = self._client()
        try:
            resp = await client.post(
                creds["token_uri"],
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            payload = resp.json()
        finally:
            await self._maybe_close(client)
        self._cached_token = str(payload["access_token"])
        self._cached_expiry = time.time() + int(payload.get("expires_in", 3600))
        return self._cached_token

    def _client(self) -> httpx.AsyncClient:
        return self._http if self._http is not None else httpx.AsyncClient()

    async def _maybe_close(self, client: httpx.AsyncClient) -> None:
        if self._owns_client:
            await client.aclose()

    def _message(self, *, token: str, title: str, body: str, data: dict) -> dict:
        str_data = {str(k): (v if isinstance(v, str) else json.dumps(v)) for k, v in (data or {}).items()}
        return {
            "message": {
                "token": token,
                "notification": {"title": title, "body": body},
                "data": str_data,
                "android": {
                    "priority": "high",
                    "notification": {"channel_id": SOS_CHANNEL_ID},
                },
            },
            "validate_only": self._dry_run,
        }

    async def send_to_tokens(self, *, tokens: list[str], title: str, body: str, data: dict) -> TokenSendReport:
        report = TokenSendReport()
        if not tokens:
            return report
        try:
            bearer = await self._access_token()
        except Exception as e:
            log.warning("FCM auth failed, marking %d tokens failed: %s", len(tokens), e)
            report.failed.extend(tokens)
            return report
        url = _FCM_ENDPOINT.format(project_id=self._project_id)
        client = self._client()
        try:
            for token in tokens:
                try:
                    resp = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {bearer}"},
                        json=self._message(token=token, title=title, body=body, data=data),
                        timeout=15.0,
                    )
                except Exception as e:
                    log.warning("FCM send error for token ending ...%s: %s", token[-6:], e)
                    report.failed.append(token)
                    continue
                if resp.status_code == 200:
                    report.delivered.append(token)
                    continue
                code = ""
                details: list = []
                try:
                    err = resp.json().get("error", {})
                    code = str(err.get("status", ""))
                    raw_details = err.get("details", [])
                    if isinstance(raw_details, list):
                        details = raw_details
                        if details and isinstance(details[0], dict):
                            code = str(details[0].get("errorCode", code))
                except Exception:
                    pass
                if _is_dead_token(code, details):
                    log.info("FCM pruning dead token ending ...%s (%s)", token[-6:], code)
                    report.invalid.append(token)
                else:
                    log.warning("FCM send failed (%s) for token ending ...%s", resp.status_code, token[-6:])
                    report.failed.append(token)
        finally:
            await self._maybe_close(client)
        return report
