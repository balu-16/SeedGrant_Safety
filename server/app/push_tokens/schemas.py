"""Push-token schemas + repository (tokens stored as hashes only)."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Platform(StrEnum):
    ANDROID = "android"
    IOS = "ios"
    WEB = "web"
    UNKNOWN = "unknown"


class PushTokenCreate(BaseModel):
    token: str = Field(min_length=10, max_length=512)
    platform: Platform = Platform.UNKNOWN


class PushTokenPublic(BaseModel):
    id: uuid.UUID
    platform: str
    created_at: datetime
    last_seen_at: datetime
