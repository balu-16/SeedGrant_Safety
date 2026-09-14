"""Notification orchestration: audience expansion, token resolution, delivery, pruning.

Providers implement ``send_to_tokens`` (Mock logs, FCM v1 delivers). The service
expands an emergency audience (owner + accepted guardians), resolves sendable
tokens via the push-tokens repo, and prunes tokens the provider reports dead.
Without bound repos (tests, mock mode) it degrades to log-only delivery.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.security import hash_token_value

log = get_logger(__name__)


@dataclass
class NotificationResult:
    provider: str
    message_id: str
    delivered_to: list[str] = field(default_factory=list)


@dataclass
class TokenSendReport:
    delivered: list[str] = field(default_factory=list)
    invalid: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)


class NotificationProvider(Protocol):
    @property
    def provider_name(self) -> str: ...

    async def send_to_tokens(self, *, tokens: list[str], title: str, body: str, data: dict) -> TokenSendReport: ...


class MockNotificationProvider:
    """Development provider: logs instead of delivering."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def send_to_tokens(self, *, tokens: list[str], title: str, body: str, data: dict) -> TokenSendReport:
        log.info(
            "MOCK-NOTIFY title=%r body=%r tokens=%d data=%s",
            title,
            body,
            len(tokens),
            data,
        )
        return TokenSendReport(delivered=list(tokens))


class NotificationService:
    def __init__(self, provider: NotificationProvider | None = None) -> None:
        self._provider: NotificationProvider = provider or MockNotificationProvider()
        self._push_tokens: Any = None
        self._guardians: Any = None

    def bind(self, *, push_tokens: Any = None, guardians: Any = None) -> "NotificationService":
        self._push_tokens = push_tokens if push_tokens is not None else self._push_tokens
        self._guardians = guardians if guardians is not None else self._guardians
        return self

    async def _audience(self, protected_user_id: str) -> list[str]:
        audience = [str(protected_user_id)]
        if self._guardians is not None:
            try:
                for gid in await self._guardians.accepted_guardian_user_ids(str(protected_user_id)):
                    if str(gid) not in audience:
                        audience.append(str(gid))
            except Exception as e:
                log.warning("Guardian audience lookup failed: %s", e)
        return audience

    async def _deliver(self, *, audience_user_ids: list[str], title: str, body: str, data: dict) -> NotificationResult:
        tokens: list[str] = []
        if self._push_tokens is not None:
            try:
                rows = await self._push_tokens.tokens_for_users([str(u) for u in audience_user_ids])
                tokens = [str(r["token"]) for r in rows if r.get("token")]
            except Exception as e:
                log.warning("Push-token lookup failed: %s", e)
        try:
            report = await self._provider.send_to_tokens(tokens=tokens, title=title, body=body, data=data)
        except Exception as e:
            log.warning("Push delivery failed: %s", e)
            return NotificationResult(
                provider=self._provider.provider_name,
                message_id="failed",
                delivered_to=[],
            )
        if report.invalid and self._push_tokens is not None:
            for token in report.invalid:
                try:
                    await self._push_tokens.delete_by_token_hash(hash_token_value(token))
                except Exception as e:
                    log.warning("Dead-token prune failed: %s", e)
        return NotificationResult(
            provider=self._provider.provider_name,
            message_id="sent",
            delivered_to=[str(u) for u in audience_user_ids],
        )

    async def notify_emergency_created(
        self, *, protected_user_id: str, emergency_id: str, trigger_type: str
    ) -> NotificationResult:
        return await self._deliver(
            audience_user_ids=await self._audience(protected_user_id),
            title="SOS triggered",
            body=f"Emergency {emergency_id} via {trigger_type}",
            data={
                "kind": "emergency-created",
                "emergency_id": emergency_id,
                "trigger_type": trigger_type,
            },
        )

    async def notify_emergency_updated(
        self, *, protected_user_id: str, emergency_id: str, status: str
    ) -> NotificationResult:
        return await self._deliver(
            audience_user_ids=await self._audience(protected_user_id),
            title="SOS updated",
            body=f"Emergency {emergency_id} is now {status}",
            data={"kind": "emergency-updated", "emergency_id": emergency_id, "status": status},
        )

    async def send_to_users(
        self, *, user_ids: list[str], title: str, body: str, data: dict | None = None
    ) -> NotificationResult:
        """Admin-portal send: test push to one user or broadcast to many."""
        audience: list[str] = []
        for uid in user_ids:
            uid = str(uid)
            if uid not in audience:
                audience.append(uid)
        return await self._deliver(
            audience_user_ids=audience,
            title=title,
            body=body,
            data=data or {"kind": "admin-broadcast"},
        )


def build_notifications(settings: Settings) -> NotificationService:
    """Select the push provider from settings; fall back to mock on any misconfig."""
    if (settings.push_provider or "").strip().lower() == "fcm":
        if not settings.fcm_project_id:
            log.warning("PUSH_PROVIDER=fcm but FCM_PROJECT_ID is empty — using mock provider")
            return NotificationService()
        import os

        if not os.path.exists(settings.fcm_credentials_path):
            log.warning(
                "PUSH_PROVIDER=fcm but credentials missing at %s — using mock provider",
                settings.fcm_credentials_path,
            )
            return NotificationService()
        from app.notifications.fcm import FcmV1Provider

        return NotificationService(
            FcmV1Provider(
                credentials_path=settings.fcm_credentials_path,
                project_id=settings.fcm_project_id,
                dry_run=settings.fcm_dry_run,
            )
        )
    return NotificationService()
