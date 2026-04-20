from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_WS_IDLE_TIMEOUT_SECONDS = 5
MIN_WS_MESSAGE_SIZE_BYTES = 1024
MIN_POSTGRES_PASSWORD_LENGTH = 12


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Digital Footprint Audit API"
    hibp_api_key: str = ""
    hibp_user_agent: str = "Email-Search-Audit"
    redis_url: str = "redis://redis:6379/0"
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    postgres_db: str = ""
    postgres_user: str = ""
    postgres_password: str = ""
    ws_idle_timeout_seconds: int = 30
    ws_max_message_size_bytes: int = 16384
    rate_limit_salt: str = "email-search-rate-limit"

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        weak_passwords = {"change_me", "changeme", "password", "postgres", "admin", "root"}
        postgres_values = (self.postgres_db, self.postgres_user, self.postgres_password)
        if any(postgres_values) and not all(postgres_values):
            raise ValueError("POSTGRES_DB, POSTGRES_USER, and POSTGRES_PASSWORD must all be configured together.")
        if all(postgres_values):
            if len(self.postgres_password) < MIN_POSTGRES_PASSWORD_LENGTH:
                raise ValueError(
                    f"POSTGRES_PASSWORD must be at least {MIN_POSTGRES_PASSWORD_LENGTH} characters long."
                )
            if self.postgres_password.lower() in weak_passwords:
                raise ValueError("POSTGRES_PASSWORD must not use a weak default value.")
        if self.ws_idle_timeout_seconds < MIN_WS_IDLE_TIMEOUT_SECONDS:
            raise ValueError(f"WS_IDLE_TIMEOUT_SECONDS must be at least {MIN_WS_IDLE_TIMEOUT_SECONDS} seconds.")
        if self.ws_max_message_size_bytes < MIN_WS_MESSAGE_SIZE_BYTES:
            raise ValueError(f"WS_MAX_MESSAGE_SIZE_BYTES must be at least {MIN_WS_MESSAGE_SIZE_BYTES} bytes.")
        return self


settings = Settings()
