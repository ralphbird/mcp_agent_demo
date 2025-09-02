"""Load test execution manager service."""

import asyncio
from contextlib import suppress
from datetime import UTC, datetime
from typing import ClassVar

from load_tester.middleware.metrics import record_load_test_start, record_load_test_stop
from load_tester.models.load_test import (
    LoadTestConfig,
    LoadTestResponse,
    LoadTestStats,
    LoadTestStatus,
)
from load_tester.services.load_generator import LoadGenerator


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
        self._load_generator: LoadGenerator | None = None
        self._stats_task: asyncio.Task | None = None
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

            try:
                self._status = LoadTestStatus.STARTING
                self._config = config
                self._stats = LoadTestStats()
                self._started_at = datetime.now(UTC)
                self._stopped_at = None
                self._error_message = None

                # Create and start load generator
                self._load_generator = LoadGenerator(config)
                await self._load_generator.start()

                # Start stats update task
                self._stats_task = asyncio.create_task(self._update_stats_periodically())

                # Record metrics
                record_load_test_start(config.requests_per_second)

                self._status = LoadTestStatus.RUNNING
                return self._get_current_response()

            except Exception as e:
                self._status = LoadTestStatus.ERROR
                self._error_message = str(e)
                self._load_generator = None
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

            # Stop load generator
            if self._load_generator:
                final_stats = await self._load_generator.stop()
                self._stats = final_stats
                self._load_generator = None

            # Cancel stats task if running
            if self._stats_task and not self._stats_task.done():
                self._stats_task.cancel()
                self._stats_task = None

            # Record metrics
            record_load_test_stop()

            self._status = LoadTestStatus.STOPPED
            self._stopped_at = datetime.now(UTC)

            return self._get_current_response()

    async def get_status(self) -> LoadTestResponse:
        """Get current load test status and statistics.

        Returns:
            Current load test response
        """
        # Update stats from load generator if running
        if self._load_generator and self._status == LoadTestStatus.RUNNING:
            with suppress(Exception):
                self._stats = await self._load_generator.get_current_stats()

        return self._get_current_response()

    async def _update_stats_periodically(self) -> None:
        """Periodically update statistics from the load generator."""
        try:
            while self._status == LoadTestStatus.RUNNING and self._load_generator:
                await asyncio.sleep(1.0)  # Update stats every second
                try:
                    self._stats = await self._load_generator.get_current_stats()
                except Exception:
                    # Continue if stats update fails
                    continue
        except asyncio.CancelledError:
            pass

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
