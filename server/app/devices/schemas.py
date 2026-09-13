"""Device schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    name: str = Field(default="Smart Safety Tag", min_length=1, max_length=120)
    device_secret: str | None = Field(default=None, min_length=8, max_length=128)


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    battery_pct: int | None = Field(default=None, ge=0, le=100)
    connection_state: str | None = Field(default=None, pattern="^(offline|online|unknown)$")


class DevicePairRequest(BaseModel):
    device_secret: str | None = Field(default=None, min_length=1, max_length=128)


class DevicePublic(BaseModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    battery_pct: int | None
    connection_state: str
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DeviceStatus(BaseModel):
    id: uuid.UUID
    name: str
    connected: bool
    battery_pct: int | None
    connection_state: str
    last_seen_at: datetime | None
