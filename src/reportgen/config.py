from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for local development and future deployment."""

    app_name: str = "reportgen"
    environment: str = "development"
    output_root: Path = Field(default=Path("output"))
    schema_version: str = "1.0.0"
    default_currency: str = "INR"
    anthropic_api_key: str | None = None
    model_name: str = "claude-3-7-sonnet-latest"
    min_slide_count: int = 5
    max_slide_count: int = 8
    max_planning_retries: int = 2
    pdf_converter_mode: str = "auto"
    libreoffice_path: Path | None = None
    powerpoint_path: Path | None = None
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="REPORTGEN_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
