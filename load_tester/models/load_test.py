"""Load test request and response models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


def _get_all_currency_pairs() -> list[str]:
    """Get all available currency pairs from currency patterns.

    Returns:
        List of all currency pairs in format "FROM_TO"
    """
    # Import here to avoid circular imports
    from load_tester.services.currency_patterns import CurrencyPatterns

    patterns = CurrencyPatterns()
    return patterns.get_all_currency_pairs_list()


def _get_all_amounts() -> list[float]:
    """Get all available transaction amounts for all currency pairs.

    Each amount is appropriate for its from currency context.

    Returns:
        List of all unique amounts across all currency pairs with their appropriate from-currency amounts
    """
    # Import here to avoid circular imports
    from load_tester.services.currency_patterns import CurrencyPatterns

    patterns = CurrencyPatterns()
    all_pairs = patterns.get_all_currency_pairs_list()
    return patterns.get_all_amounts_for_pairs(all_pairs)


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
        default_factory=_get_all_currency_pairs,
        description="Currency pairs to test (defaults to all available pairs)",
    )
    amounts: list[float] = Field(
        default_factory=_get_all_amounts,
        description="Transaction amounts to test (defaults to all available amounts)",
    )
    error_injection_enabled: bool = Field(
        default=False,
        description="Enable error injection to generate requests that will fail",
    )
    error_injection_rate: float = Field(
        default=0.05,
        ge=0.0,
        le=0.5,
        description="Percentage of requests that should intentionally fail (0.0-0.5)",
    )

    @classmethod
    def create_full_config(
        cls,
        requests_per_second: float = 1.0,
        error_injection_enabled: bool = False,
        error_injection_rate: float = 0.05,
    ) -> "LoadTestConfig":
        """Create a config with all currency pairs and appropriate amounts.

        This is the recommended way to create configs that use all available
        currency pairs with amounts appropriate to each pair's from currency.

        Args:
            requests_per_second: Target requests per second
            error_injection_enabled: Enable error injection for realistic testing
            error_injection_rate: Percentage of requests that should fail (0.0-0.5)

        Returns:
            LoadTestConfig with all pairs and appropriate amounts
        """
        return cls(
            requests_per_second=requests_per_second,
            currency_pairs=_get_all_currency_pairs(),
            amounts=_get_all_amounts(),
            error_injection_enabled=error_injection_enabled,
            error_injection_rate=error_injection_rate,
        )

    def ensure_complete_config(self) -> "LoadTestConfig":
        """Ensure this config has all currency pairs and appropriate amounts.

        If currency_pairs or amounts are empty/missing, populate them with defaults.

        Returns:
            LoadTestConfig with complete currency pairs and amounts
        """
        # Check for empty lists as well as None/missing
        currency_pairs = (
            self.currency_pairs
            if (self.currency_pairs and len(self.currency_pairs) > 0)
            else _get_all_currency_pairs()
        )
        amounts = self.amounts if (self.amounts and len(self.amounts) > 0) else _get_all_amounts()

        return LoadTestConfig(
            requests_per_second=self.requests_per_second,
            currency_pairs=currency_pairs,
            amounts=amounts,
            error_injection_enabled=self.error_injection_enabled,
            error_injection_rate=self.error_injection_rate,
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
