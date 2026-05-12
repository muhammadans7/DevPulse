from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str
    redis_url: str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    github_client_id: str
    github_client_secret: str
    github_redirect_uri: str

    environment: str = "development"
    debug: bool = False


settings = Settings()
