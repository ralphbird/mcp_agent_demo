"""Configuration settings for the Currency Conversion API."""

from pathlib import Path

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    database_url: str = "sqlite:///currency_demo.db"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Dashboard Configuration
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8501

    # API Base URL for dashboard
    api_base_url: str = "http://localhost:8000"

    # Data directory for persistent storage
    data_directory: str = "data"

    @computed_field
    @property
    def data_dir(self) -> Path:
        """Get the data directory as a Path object."""
        # Check if we're running in Docker
        if Path("/app/data").exists():
            return Path("/app/data")
        return Path(self.data_directory)

    @field_validator("api_port", "dashboard_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port numbers are in valid range."""
        if not 1 <= v <= 65535:
            msg = "Port must be between 1 and 65535"
            raise ValueError(msg)
        return v

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v:
            msg = "Database URL cannot be empty"
            raise ValueError(msg)
        return v


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get the database URL for backward compatibility."""
    return settings.database_url


def get_data_dir() -> Path:
    """Get the data directory for backward compatibility."""
    return settings.data_dir
