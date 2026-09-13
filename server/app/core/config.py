"""Centralized typed configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Smart Safety Tag API")
    env: str = Field(default="development")
    database_url: str = Field(default="")
    db_sslmode: str = Field(default="prefer")
    db_pool_min: int = Field(default=1)
    db_pool_max: int = Field(default=10)

    jwt_secret: str = Field(default="change-me-in-production-min-32-chars")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    log_level: str = Field(default="INFO")
    testing: bool = Field(default=False)

    # Supabase API access (URL + keys). The asyncpg data layer keeps using
    # DATABASE_URL (privileged, server-side only); these are for Supabase-API
    # calls (REST/auth-admin/storage) where key-based access applies.
    supabase_url: str = Field(default="")
    supabase_anon_key: str = Field(default="")
    supabase_service_role_key: str = Field(default="")

    push_provider: str = Field(default="mock")
    fcm_project_id: str = Field(default="")
    fcm_credentials_path: str = Field(default="./fcm-service-account.json")
    fcm_dry_run: bool = Field(default=False)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: object) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v or v == "*":
                return ["*"]
            return [o.strip() for o in v.split(",") if o.strip()]
        if isinstance(v, list):
            return [str(o) for o in v]
        return ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
