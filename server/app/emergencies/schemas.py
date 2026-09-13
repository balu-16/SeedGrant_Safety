"""Emergency schemas — enums avoid fragile string comparisons."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TriggerType(StrEnum):
    TAG_BUTTON = "TAG_BUTTON"
    TAG_VOICE = "TAG_VOICE"
    APP_BUTTON = "APP_BUTTON"
    APP_VOICE = "APP_VOICE"
    FALL_DETECTION = "FALL_DETECTION"


class EmergencyStatus(StrEnum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class EmergencyCreate(BaseModel):
    trigger_type: TriggerType
    device_id: uuid.UUID | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    note: str | None = Field(default=None, max_length=1000)


class EmergencyStatusUpdate(BaseModel):
    status: EmergencyStatus


class EmergencyPublic(BaseModel):
    id: uuid.UUID
    protected_user_id: uuid.UUID
    device_id: uuid.UUID | None
    trigger_type: str
    status: str
    latitude: float | None
    longitude: float | None
    note: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class EmergencyListResponse(BaseModel):
    items: list[EmergencyPublic]
    total: int
    limit: int
    offset: int
