"""Users service — business rules for profile read/update."""

from app.core.exceptions import NotFoundError
from app.users.repository import UsersRepository


class UsersService:
    def __init__(self, users: UsersRepository) -> None:
        self._users = users

    async def get_me(self, user_id: str) -> dict:
        user = await self._users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    async def update_me(self, user_id: str, *, name: str | None, phone: str | None) -> dict:
        user = await self._users.update(user_id, name=name, phone=phone)
        if not user:
            raise NotFoundError("User not found")
        return user
