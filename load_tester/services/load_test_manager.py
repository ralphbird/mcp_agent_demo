"""Load test execution manager service."""

import asyncio
from contextlib import suppress
from datetime import UTC, datetime
from typing import ClassVar

from load_tester.logging_config import get_logger
from load_tester.models.load_test import (
    LoadTestConfig,
    LoadTestResponse,
    LoadTestStats,
    LoadTestStatus,
)
from load_tester.services.load_generator import LoadGenerator

logger = get_logger(__name__)


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
            RuntimeError: If load test is already running (use ramp_to_config instead)
        """
        # Bind load test context
        load_test_logger = logger.bind(
            requests_per_second=config.requests_per_second,
            currency_pairs_count=len(config.currency_pairs) if config.currency_pairs else 0,
            amounts_count=len(config.amounts) if config.amounts else 0,
        )

        load_test_logger.info(f"Starting load test with {config.requests_per_second} RPS")

        async with self._lock:
            if self._status in (LoadTestStatus.RUNNING, LoadTestStatus.STARTING):
                msg = "Load test is already running"
                load_test_logger.warning(
                    f"Attempted to start load test but one is already running: {self._status}"
                )
                raise RuntimeError(msg)

            try:
                self._status = LoadTestStatus.STARTING
                load_test_logger.info("Load test status changed to STARTING")
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

                # Metrics recording removed for load_tester

                self._status = LoadTestStatus.RUNNING
                return self._get_current_response()

            except Exception as e:
                self._status = LoadTestStatus.ERROR
                self._error_message = str(e)
                self._load_generator = None
                return self._get_current_response()

    async def ramp_to_config(self, config: LoadTestConfig) -> LoadTestResponse:
        """Ramp the current load test to a new configuration without stopping.

        Args:
            config: New load test configuration to ramp to

        Returns:
            Load test response with updated status and configuration

        Raises:
            RuntimeError: If no load test is currently running
        """
        async with self._lock:
            if self._status not in (LoadTestStatus.RUNNING, LoadTestStatus.STARTING):
                msg = "No load test is currently running to ramp"
                raise RuntimeError(msg)

            if not self._load_generator:
                msg = "Load generator not available for ramping"
                raise RuntimeError(msg)

            try:
                # Update manager configuration
                self._config = config
                self._error_message = None

                # Ramp the load generator to new configuration
                await self._load_generator.ramp_to_config(config)

                # Metrics recording removed for load_tester

                return self._get_current_response()

            except Exception as e:
                self._error_message = f"Ramping failed: {e}"
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
                with suppress(asyncio.CancelledError):
                    await self._stats_task
                self._stats_task = None

            # Metrics recording removed for load_tester

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
