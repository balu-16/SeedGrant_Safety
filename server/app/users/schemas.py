"""User Pydantic schemas (never expose password hashes)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    phone: str
    role: str = "user"
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
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
