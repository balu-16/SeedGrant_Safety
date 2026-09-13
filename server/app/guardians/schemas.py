"""Guardian schemas."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class GuardianStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    REMOVED = "removed"


class GuardianInviteRequest(BaseModel):
    guardian_email: EmailStr
    guardian_name: str = Field(default="", max_length=120)
    relation: str = Field(default="", max_length=80)
    is_primary: bool = False


class GuardianStatusUpdate(BaseModel):
    status: GuardianStatus


class GuardianPublic(BaseModel):
    id: uuid.UUID
    protected_user_id: uuid.UUID
    protected_user_name: str | None = None
    guardian_user_id: uuid.UUID | None
    guardian_email: str
    guardian_name: str
    relation: str
    status: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime
