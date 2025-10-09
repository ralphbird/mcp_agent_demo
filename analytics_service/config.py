"""Configuration settings for the Load Tester API."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoadTesterSettings(BaseSettings):
    """Analytics service settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="ANALYTICS_SERVICE_",
    )

    # Load Tester Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 9001

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
    max_adaptive_workers: int = 150
    latency_threshold_ms: float = 500.0  # Scale up if avg latency exceeds this
    scaling_cooldown_seconds: float = 5.0  # Minimum time between scaling operations

    # Rate Accuracy Monitoring Configuration
    target_accuracy_threshold: float = 0.85  # Alert if achieved RPS < 85% of target
    accuracy_measurement_window_seconds: float = 30.0  # Window for measuring RPS accuracy

    # IP Spoofing Configuration
    ip_spoofing_enabled: bool = False  # Enable X-Forwarded-For header spoofing
    ip_rotation_interval: int = 5  # Change IP every N requests
    ip_geographic_regions: str = "US,EU,APAC"  # Comma-separated regions
    include_datacenter_ips: bool = True  # Include cloud/datacenter IP ranges
    include_residential_ips: bool = True  # Include ISP residential IP ranges

    # Traffic Variability Configuration
    traffic_variability_enabled: bool = True  # Enable realistic traffic patterns
    jitter_percentage: float = 0.15  # Random timing variation (±15% of interval)
    burst_probability: float = 0.05  # Chance of micro-bursts per request cycle
    burst_multiplier: float = 2.0  # RPS multiplier during micro-bursts
    burst_duration_ms: float = 200.0  # Duration of micro-bursts in milliseconds
    baseline_fluctuation_amplitude: float = 0.1  # Baseline RPS variation amplitude (±10%)
    baseline_fluctuation_period_seconds: float = 30.0  # Period of baseline fluctuations

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

    @field_validator("ip_rotation_interval")
    @classmethod
    def validate_ip_rotation_interval(cls, v: int) -> int:
        """Validate IP rotation interval."""
        if v <= 0:
            msg = "IP rotation interval must be positive"
            raise ValueError(msg)
        return v

    @field_validator("ip_geographic_regions")
    @classmethod
    def validate_ip_regions(cls, v: str) -> str:
        """Validate IP geographic regions."""
        if not v or not v.strip():
            msg = "At least one geographic region must be specified"
            raise ValueError(msg)

        valid_regions = {"US", "EU", "APAC"}
        regions = [r.strip().upper() for r in v.split(",") if r.strip()]

        if not regions:
            msg = "At least one geographic region must be specified"
            raise ValueError(msg)

        for region in regions:
            if region not in valid_regions:
                msg = (
                    f"Invalid region '{region}'. Must be one of: {', '.join(sorted(valid_regions))}"
                )
                raise ValueError(msg)

        # Remove duplicates while preserving order
        unique_regions = []
        seen = set()
        for region in regions:
            if region not in seen:
                unique_regions.append(region)
                seen.add(region)

        return ",".join(unique_regions)  # Normalize to uppercase, deduplicated

    @field_validator("jitter_percentage")
    @classmethod
    def validate_jitter_percentage(cls, v: float) -> float:
        """Validate jitter percentage."""
        if not 0.0 <= v <= 0.5:
            msg = "Jitter percentage must be between 0.0 and 0.5 (0%-50%)"
            raise ValueError(msg)
        return v

    @field_validator("burst_probability")
    @classmethod
    def validate_burst_probability(cls, v: float) -> float:
        """Validate burst probability."""
        if not 0.0 <= v <= 0.2:
            msg = "Burst probability must be between 0.0 and 0.2 (0%-20%)"
            raise ValueError(msg)
        return v

    @field_validator("burst_multiplier")
    @classmethod
    def validate_burst_multiplier(cls, v: float) -> float:
        """Validate burst multiplier."""
        if not 1.0 <= v <= 10.0:
            msg = "Burst multiplier must be between 1.0 and 10.0"
            raise ValueError(msg)
        return v

    @field_validator("burst_duration_ms")
    @classmethod
    def validate_burst_duration(cls, v: float) -> float:
        """Validate burst duration."""
        if not 50.0 <= v <= 2000.0:
            msg = "Burst duration must be between 50.0 and 2000.0 milliseconds"
            raise ValueError(msg)
        return v

    @field_validator("baseline_fluctuation_amplitude")
    @classmethod
    def validate_baseline_fluctuation_amplitude(cls, v: float) -> float:
        """Validate baseline fluctuation amplitude."""
        if not 0.0 <= v <= 0.3:
            msg = "Baseline fluctuation amplitude must be between 0.0 and 0.3 (0%-30%)"
            raise ValueError(msg)
        return v

    @field_validator("baseline_fluctuation_period_seconds")
    @classmethod
    def validate_baseline_fluctuation_period(cls, v: float) -> float:
        """Validate baseline fluctuation period."""
        if v <= 0:
            msg = "Baseline fluctuation period must be positive"
            raise ValueError(msg)
        return v

    def get_ip_regions_list(self) -> list[str]:
        """Get IP geographic regions as a list.

        Returns:
            List of region codes (e.g., ['US', 'EU', 'APAC'])
        """
        return [r.strip().upper() for r in self.ip_geographic_regions.split(",") if r.strip()]


# Global settings instance
settings = LoadTesterSettings()
