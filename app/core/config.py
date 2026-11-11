"""App settings. Values come from environment variables or the .env file."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Food Delivery API"
    database_url: str = "sqlite:///./food_delivery.db"

    # Used to sign login tokens. No default on purpose: a secret must never
    # live in the code. See .env.example for how to create one.
    secret_key: str = Field(min_length=32)
    access_token_expire_minutes: int = 60

    # How slow password hashing is. Each +1 doubles the work. Tests use a low
    # number to run fast; never lower it for a real server.
    bcrypt_rounds: int = Field(default=12, ge=4, le=16)

    # AI assistant (optional). Without a key everything else still works and
    # the assistant endpoint answers 503.
    anthropic_api_key: str | None = None
    assistant_model: str = "claude-opus-5-5"


settings = Settings()
