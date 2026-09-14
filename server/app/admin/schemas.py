"""Admin portal Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AdminUserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, min_length=7, max_length=32)

    @field_validator("name", "phone")
    @classmethod
    def _reject_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class DeviceAdminUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value


class GuardianForceStatus(BaseModel):
    status: str = Field(pattern="^(pending|accepted|rejected|removed)$")


class PushSendRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    body: str = Field(min_length=1, max_length=500)
    user_ids: list[UUID] | None = None
    all_users: bool = False

    @field_validator("title", "body")
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value
