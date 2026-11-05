from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://wordmeter:wordmeter@localhost:5432/wordmeter"
    jwt_secret: str = Field(min_length=32)
    access_token_minutes: int = 60 * 24 * 7
    cookie_secure: bool = False

    whisper_model: str = "base"
    whisper_compute_type: str = "int8"
    max_audio_mb: int = 25
    max_audio_seconds: int = 600


settings = Settings()  # type: ignore[call-arg]  # values are read from the environment
