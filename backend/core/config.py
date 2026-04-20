from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Digital Footprint Audit API"
    hibp_api_key: str = ""
    hibp_user_agent: str = "Email-Search-Audit"
    redis_url: str = "redis://redis:6379/0"
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    postgres_db: str = "email_search"
    postgres_user: str = "email_search"
    postgres_password: str = ""
    ws_idle_timeout_seconds: int = 30
    ws_max_message_size_bytes: int = 16384

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.postgres_password and self.postgres_password.lower() in {"change_me", "password", "postgres"}:
            raise ValueError("POSTGRES_PASSWORD must not use a weak default value.")
        if self.ws_idle_timeout_seconds < 5:
            raise ValueError("WS_IDLE_TIMEOUT_SECONDS must be at least 5 seconds.")
        if self.ws_max_message_size_bytes < 1024:
            raise ValueError("WS_MAX_MESSAGE_SIZE_BYTES must be at least 1024 bytes.")
        return self


settings = Settings()
