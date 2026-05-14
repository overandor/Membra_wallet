from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Membra SMS Bitcoin Relay"
    environment: str = "development"
    database_url: str = "sqlite:///./membra_sms.sqlite3"
    api_secret: str = "change-me"
    public_base_url: str = "http://localhost:8000"

    sms_provider: str = "console"
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_number: str | None = None

    bitcoin_balance_provider: str = "mock"
    mempool_space_base_url: str = "https://mempool.space/api"

    max_sms_send_sats: int = 100_000
    max_sms_approve_sats: int = 100_000
    require_secure_link_for_all_payments: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
