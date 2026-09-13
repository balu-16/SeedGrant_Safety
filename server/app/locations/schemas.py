"""Location schemas with strict lat/lon validation."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class LocationSource(StrEnum):
    PHONE_GPS = "phone_gps"
    MANUAL = "manual"
    TAG_BLE = "tag_ble"
    FUSED = "fused"
    MOCK = "mock"


class LocationCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, gt=0, le=100000)
    source: LocationSource = LocationSource.PHONE_GPS
    device_id: uuid.UUID | None = None
    recorded_at: datetime | None = None


class LocationPublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    device_id: uuid.UUID | None
    latitude: float
    longitude: float
    accuracy_m: float | None
    source: str
    recorded_at: datetime
    created_at: datetime


class LocationHistoryResponse(BaseModel):
    items: list[LocationPublic]
    total: int
    limit: int
    offset: int
