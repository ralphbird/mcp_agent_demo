"""Load test execution manager service."""

import asyncio
from datetime import UTC, datetime
from typing import ClassVar

from load_tester.models.load_test import (
    LoadTestConfig,
    LoadTestResponse,
    LoadTestStats,
    LoadTestStatus,
)


class LoadTestManager:
    """Manages load test execution state and operations."""

    _instance: ClassVar["LoadTestManager | None"] = None
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    def __new__(cls) -> "LoadTestManager":
        """Singleton pattern for load test manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize load test manager."""
        if hasattr(self, "_initialized"):
            return

        self._status = LoadTestStatus.IDLE
        self._config: LoadTestConfig | None = None
        self._stats = LoadTestStats()
        self._started_at: datetime | None = None
        self._stopped_at: datetime | None = None
        self._error_message: str | None = None
        self._task: asyncio.Task | None = None
        self._initialized = True

    async def start_load_test(self, config: LoadTestConfig) -> LoadTestResponse:
        """Start a load test with the given configuration.

        Args:
            config: Load test configuration

        Returns:
            Load test response with current status

        Raises:
            RuntimeError: If load test is already running
        """
        async with self._lock:
            if self._status in (LoadTestStatus.RUNNING, LoadTestStatus.STARTING):
                msg = "Load test is already running"
                raise RuntimeError(msg)

            self._status = LoadTestStatus.STARTING
            self._config = config
            self._stats = LoadTestStats()
            self._started_at = datetime.now(UTC)
            self._stopped_at = None
            self._error_message = None

            # For phase 1, we just simulate starting the load test
            # In later phases, this will launch actual load generation
            self._status = LoadTestStatus.RUNNING

            return self._get_current_response()

    async def stop_load_test(self) -> LoadTestResponse:
        """Stop the currently running load test.

        Returns:
            Load test response with current status
        """
        async with self._lock:
            if self._status not in (LoadTestStatus.RUNNING, LoadTestStatus.STARTING):
                return self._get_current_response()

            self._status = LoadTestStatus.STOPPING

            # Cancel running task if exists
            if self._task and not self._task.done():
                self._task.cancel()

            self._status = LoadTestStatus.STOPPED
            self._stopped_at = datetime.now(UTC)

            return self._get_current_response()

    async def get_status(self) -> LoadTestResponse:
        """Get current load test status and statistics.

        Returns:
            Current load test response
        """
        return self._get_current_response()

    def _get_current_response(self) -> LoadTestResponse:
        """Get the current load test response.

        Returns:
            Current load test response
        """
        return LoadTestResponse(
            status=self._status,
            config=self._config,
            stats=self._stats,
            started_at=self._started_at,
            stopped_at=self._stopped_at,
            error_message=self._error_message,
        )
