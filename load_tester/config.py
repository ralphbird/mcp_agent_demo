"""Configuration settings for the Load Tester API."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoadTesterSettings(BaseSettings):
    """Load tester settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="LOAD_TESTER_",
    )

    # Load Tester Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8001

    # Target API Configuration
    target_api_base_url: str = "http://localhost:8000"

    # JWT Configuration (for generating test tokens)
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"

    # Load Test Configuration
    default_requests_per_second: float = 1.0
    max_requests_per_second: float = 100.0
    request_timeout: float = 30.0

    @field_validator("api_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port numbers are in valid range."""
        if not 1 <= v <= 65535:
            msg = "Port must be between 1 and 65535"
            raise ValueError(msg)
        return v

    @field_validator("default_requests_per_second", "max_requests_per_second")
    @classmethod
    def validate_rps(cls, v: float) -> float:
        """Validate requests per second values."""
        if v <= 0:
            msg = "Requests per second must be positive"
            raise ValueError(msg)
        return v

    @field_validator("request_timeout")
    @classmethod
    def validate_timeout(cls, v: float) -> float:
        """Validate timeout values."""
        if v <= 0:
            msg = "Request timeout must be positive"
            raise ValueError(msg)
        return v


# Global settings instance
settings = LoadTesterSettings()
