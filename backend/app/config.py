"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "NeighbourGood"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: str = "sqlite:///./neighbourgood.db"

    # Dual-state: "blue" (normal) or "red" (crisis)
    platform_mode: str = "blue"

    # Auth
    secret_key: str = "change-me-in-production-use-a-real-secret"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Uploads
    upload_dir: str = "uploads"
    max_image_size: int = 5 * 1024 * 1024  # 5 MB

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {"env_prefix": "NG_", "env_file": ".env"}


settings = Settings()
