from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Digital Footprint Audit API"
    hibp_api_key: str = ""
    hibp_user_agent: str = "Email-Search-Audit"
    redis_url: str = "redis://redis:6379/0"


settings = Settings()
