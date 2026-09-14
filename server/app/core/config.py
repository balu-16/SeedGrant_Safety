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

    @field_validator("jwt_algorithm")
    @classmethod
    def _symmetric_algorithm_only(cls, value: str) -> str:
        # jwt_secret is a symmetric key; asymmetric algorithms would be misused here.
        allowed = {"HS256", "HS384", "HS512"}
        if value not in allowed:
            raise ValueError(f"jwt_algorithm must be one of {sorted(allowed)}")
        return value

    @property
    def is_production(self) -> bool:
        return self.env.strip().lower() in {"production", "prod", "staging"}

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    log_level: str = Field(default="INFO")
    testing: bool = Field(default=False)

    # Accounts with these emails are promoted to admin at startup (bootstrap).
    admin_emails: list[str] = Field(default_factory=list)

    @field_validator("admin_emails", mode="before")
    @classmethod
    def parse_admin_emails(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [e.strip().lower() for e in v.split(",") if e.strip()]
        if isinstance(v, list):
            return [str(e).strip().lower() for e in v if str(e).strip()]
        return []

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
