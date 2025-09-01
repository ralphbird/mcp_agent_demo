"""Load test request and response models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class LoadTestStatus(str, Enum):
    """Load test execution status."""

    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class LoadTestConfig(BaseModel):
    """Configuration for load test execution."""

    requests_per_second: float = Field(
        default=1.0,
        gt=0,
        le=100.0,
        description="Number of requests per second to generate",
    )
    currency_pairs: list[str] = Field(
        default_factory=lambda: ["USD_EUR", "USD_GBP", "EUR_GBP", "USD_CAD", "USD_JPY"],
        description="Currency pairs to test",
    )
    amounts: list[float] = Field(
        default_factory=lambda: [100.0, 250.0, 500.0, 1000.0, 2500.0],
        description="Transaction amounts to test",
    )


class StartLoadTestRequest(BaseModel):
    """Request to start a load test."""

    config: LoadTestConfig = Field(
        default_factory=LoadTestConfig,
        description="Load test configuration",
    )


class LoadTestStats(BaseModel):
    """Load test execution statistics."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    requests_per_second: float = 0.0


class LoadTestResponse(BaseModel):
    """Load test status and statistics response."""

    status: LoadTestStatus
    config: LoadTestConfig | None = None
    stats: LoadTestStats = Field(default_factory=LoadTestStats)
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    error_message: str | None = None
