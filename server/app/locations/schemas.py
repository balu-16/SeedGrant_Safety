"""Location schemas with strict lat/lon validation."""

import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("recorded_at")
    @classmethod
    def _bound_recorded_at(cls, value: datetime | None) -> datetime | None:
        # A far-future client timestamp would permanently win the
        # ORDER BY recorded_at DESC "latest location" query.
        if value is None:
            return value
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        if value > datetime.now(UTC) + timedelta(minutes=5):
            raise ValueError("recorded_at cannot be in the future")
        return value


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
