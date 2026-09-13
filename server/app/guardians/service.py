"""Guardians service — relationship transition rules enforced here."""

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.guardians.repository import GuardiansRepository
from app.users.repository import UsersRepository

_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"accepted", "rejected", "removed"},
    "accepted": {"removed"},
    "rejected": {"pending", "removed"},
    "removed": set(),
}


class GuardiansService:
    def __init__(self, guardians: GuardiansRepository, users: UsersRepository) -> None:
        self._guardians = guardians
        self._users = users

    async def invite(
        self,
        protected_user_id: str,
        *,
        guardian_email: str,
        guardian_name: str = "",
        relation: str = "",
        is_primary: bool = False,
    ) -> dict:
        email = guardian_email.strip().lower()
        me = await self._users.get_by_id(protected_user_id)
        if me and str(me["email"]).lower() == email:
            raise ValidationAppError("Cannot invite yourself as guardian")
        existing = await self._guardians.find_by_protected_and_email(protected_user_id, email)
        if existing and existing["status"] != "removed":
            raise ConflictError("Guardian already invited")
        guardian_user = await self._users.get_by_email(email)
        guardian_user_id = str(guardian_user["id"]) if guardian_user else None
        if existing and existing["status"] == "removed":
            # Re-invite: move back to pending
            updated = await self._guardians.update_status(str(existing["id"]), "pending")
            if guardian_user_id and updated:
                updated = await self._guardians.link_user(str(existing["id"]), guardian_user_id)
            return updated or existing
        return await self._guardians.create(
            protected_user_id=protected_user_id,
            guardian_email=email,
            guardian_name=guardian_name,
            relation=relation,
            is_primary=is_primary,
            guardian_user_id=guardian_user_id,
        )

    async def list_mine(self, user_id: str) -> list[dict]:
        return await self._guardians.list_for_protected(user_id)

    async def list_protecting_me(self, guardian_user_id: str) -> list[dict]:
        return await self._guardians.list_for_guardian_user(guardian_user_id)

    async def _get_owned(self, protected_user_id: str, guardian_id: str) -> dict:
        rel = await self._guardians.get_by_id(guardian_id)
        if not rel:
            raise NotFoundError("Guardian not found")
        if str(rel["protected_user_id"]) != str(protected_user_id):
            # Allow the linked guardian user to accept their own invite
            if rel.get("guardian_user_id") and str(rel["guardian_user_id"]) == str(protected_user_id):
                return rel
            raise ForbiddenError("Not your guardian relationship")
        return rel

    async def update_status(self, user_id: str, guardian_id: str, status: str) -> dict:
        rel = await self._get_owned(user_id, guardian_id)
        current = str(rel["status"])
        if status not in _ALLOWED_TRANSITIONS.get(current, set()):
            raise ValidationAppError(f"Cannot move guardian from {current} to {status}")
        updated = await self._guardians.update_status(guardian_id, status)
        if not updated:
            raise NotFoundError("Guardian not found")
        return updated

    async def remove(self, user_id: str, guardian_id: str) -> dict:
        return await self.update_status(user_id, guardian_id, "removed")

    async def assert_can_read_protected(self, reader_user_id: str, protected_user_id: str) -> None:
        if str(reader_user_id) == str(protected_user_id):
            return
        ok = await self._guardians.is_accepted_guardian(protected_user_id, reader_user_id)
        if not ok:
            raise ForbiddenError("Not authorized to view this user's data")
