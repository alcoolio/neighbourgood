"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "NeighbourGood"
    app_version: str = "0.5.0"
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

    # Email / SMTP (optional – logs to console when unconfigured)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_tls: bool = True
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@neighbourgood.local"

    # Frontend URL (used in email notifications)
    frontend_url: str = "http://localhost:3800"

    # CORS
    cors_origins: list[str] = ["http://localhost:3800", "http://localhost:5173"]

    # Instance identity (for federation directory)
    instance_name: str = "My NeighbourGood"
    instance_description: str = ""
    instance_region: str = ""
    instance_url: str = ""
    admin_name: str = ""
    admin_contact: str = ""

    model_config = {"env_prefix": "NG_", "env_file": ".env"}


settings = Settings()
