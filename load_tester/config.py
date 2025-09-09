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

    # Latency Compensation Configuration
    latency_compensation_enabled: bool = True  # Enable to compensate for request latency
    min_sleep_threshold_ms: float = 1.0  # Minimum sleep to prevent CPU spinning

    # Adaptive Worker Scaling Configuration
    adaptive_scaling_enabled: bool = True  # Enable adaptive scaling based on latency
    max_adaptive_workers: int = 50
    latency_threshold_ms: float = 500.0  # Scale up if avg latency exceeds this
    scaling_cooldown_seconds: float = 5.0  # Minimum time between scaling operations

    # Rate Accuracy Monitoring Configuration
    target_accuracy_threshold: float = 0.85  # Alert if achieved RPS < 85% of target
    accuracy_measurement_window_seconds: float = 30.0  # Window for measuring RPS accuracy

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

    @field_validator("min_sleep_threshold_ms")
    @classmethod
    def validate_min_sleep_threshold(cls, v: float) -> float:
        """Validate minimum sleep threshold."""
        if v < 0:
            msg = "Minimum sleep threshold must be non-negative"
            raise ValueError(msg)
        return v

    @field_validator("max_adaptive_workers")
    @classmethod
    def validate_max_adaptive_workers(cls, v: int) -> int:
        """Validate maximum adaptive workers."""
        if v <= 0:
            msg = "Maximum adaptive workers must be positive"
            raise ValueError(msg)
        if v > 200:
            msg = "Maximum adaptive workers should not exceed 200 for safety"
            raise ValueError(msg)
        return v

    @field_validator("latency_threshold_ms")
    @classmethod
    def validate_latency_threshold(cls, v: float) -> float:
        """Validate latency threshold."""
        if v <= 0:
            msg = "Latency threshold must be positive"
            raise ValueError(msg)
        return v

    @field_validator("scaling_cooldown_seconds")
    @classmethod
    def validate_scaling_cooldown(cls, v: float) -> float:
        """Validate scaling cooldown period."""
        if v < 0:
            msg = "Scaling cooldown must be non-negative"
            raise ValueError(msg)
        return v

    @field_validator("target_accuracy_threshold")
    @classmethod
    def validate_accuracy_threshold(cls, v: float) -> float:
        """Validate target accuracy threshold."""
        if not 0.1 <= v <= 1.0:
            msg = "Target accuracy threshold must be between 0.1 and 1.0"
            raise ValueError(msg)
        return v

    @field_validator("accuracy_measurement_window_seconds")
    @classmethod
    def validate_accuracy_window(cls, v: float) -> float:
        """Validate accuracy measurement window."""
        if v <= 0:
            msg = "Accuracy measurement window must be positive"
            raise ValueError(msg)
        return v


# Global settings instance
settings = LoadTesterSettings()
