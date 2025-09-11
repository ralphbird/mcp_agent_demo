"""Concurrent load test manager for running multiple load tests simultaneously."""

import asyncio
import contextlib
from datetime import UTC, datetime

from analytics_service.logging_config import get_logger
from analytics_service.models.load_test import (
    LoadTestConfig,
    LoadTestResponse,
    LoadTestStats,
    LoadTestStatus,
)
from analytics_service.services.load_generator import LoadGenerator

logger = get_logger(__name__)


class ConcurrentLoadTestInstance:
    """Individual load test instance for concurrent execution."""

    def __init__(self, test_id: str, config: LoadTestConfig) -> None:
        """Initialize load test instance.

        Args:
            test_id: Unique identifier for this load test instance
            config: Load test configuration
        """
        self.test_id = test_id
        self.config = config
        self.status = LoadTestStatus.IDLE
        self.stats = LoadTestStats()
        self.started_at: datetime | None = None
        self.stopped_at: datetime | None = None
        self.error_message: str | None = None
        self.load_generator: LoadGenerator | None = None
        self.stats_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start this load test instance."""
        if self.status != LoadTestStatus.IDLE:
            msg = f"Load test {self.test_id} is not in IDLE state"
            raise RuntimeError(msg)

        try:
            self.status = LoadTestStatus.STARTING
            self.started_at = datetime.now(UTC)
            self.stopped_at = None
            self.error_message = None
            self.stats = LoadTestStats()

            # Create and start load generator
            self.load_generator = LoadGenerator(self.config)
            await self.load_generator.start()

            # Start stats update task
            self.stats_task = asyncio.create_task(self._update_stats_periodically())

            # Metrics recording removed for load_tester

            self.status = LoadTestStatus.RUNNING
            logger.info(
                f"Load test {self.test_id} started with {self.config.requests_per_second} RPS"
            )

        except Exception as e:
            self.status = LoadTestStatus.ERROR
            self.error_message = str(e)
            self.load_generator = None
            logger.error(f"Failed to start load test {self.test_id}: {e}")
            raise

    async def stop(self) -> None:
        """Stop this load test instance."""
        if self.status not in (LoadTestStatus.RUNNING, LoadTestStatus.STARTING):
            return

        self.status = LoadTestStatus.STOPPING

        # Stop load generator
        if self.load_generator:
            final_stats = await self.load_generator.stop()
            self.stats = final_stats
            self.load_generator = None

        # Cancel stats task if running
        if self.stats_task and not self.stats_task.done():
            self.stats_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.stats_task
            self.stats_task = None

        # Metrics recording removed for load_tester

        self.status = LoadTestStatus.STOPPED
        self.stopped_at = datetime.now(UTC)
        logger.info(f"Load test {self.test_id} stopped")

    async def get_response(self) -> LoadTestResponse:
        """Get current response for this load test instance."""
        # Update stats from load generator if running
        if self.load_generator and self.status == LoadTestStatus.RUNNING:
            with contextlib.suppress(Exception):
                # Update stats from load generator, continue if it fails
                self.stats = await self.load_generator.get_current_stats()

        return LoadTestResponse(
            status=self.status,
            config=self.config,
            stats=self.stats,
            started_at=self.started_at,
            stopped_at=self.stopped_at,
            error_message=self.error_message,
        )

    async def _update_stats_periodically(self) -> None:
        """Periodically update statistics from the load generator."""
        try:
            while self.status == LoadTestStatus.RUNNING and self.load_generator:
                await asyncio.sleep(1.0)  # Update stats every second
                try:
                    self.stats = await self.load_generator.get_current_stats()
                except Exception:
                    # Continue if stats update fails
                    continue
        except asyncio.CancelledError:
            pass


class ConcurrentLoadTestManager:
    """Manager for running multiple load tests concurrently."""

    def __init__(self) -> None:
        """Initialize concurrent load test manager."""
        self._load_tests: dict[str, ConcurrentLoadTestInstance] = {}
        self._lock = asyncio.Lock()

    async def start_load_test(self, test_id: str, config: LoadTestConfig) -> LoadTestResponse:
        """Start a new concurrent load test.

        Args:
            test_id: Unique identifier for this load test
            config: Load test configuration

        Returns:
            Load test response with current status

        Raises:
            RuntimeError: If test_id already exists and is running
        """
        async with self._lock:
            if test_id in self._load_tests:
                existing_test = self._load_tests[test_id]
                if existing_test.status in (LoadTestStatus.RUNNING, LoadTestStatus.STARTING):
                    msg = f"Load test {test_id} is already running"
                    raise RuntimeError(msg)
                # Clean up stopped test before starting new one
                del self._load_tests[test_id]

            # Create and start new test instance
            test_instance = ConcurrentLoadTestInstance(test_id, config)
            self._load_tests[test_id] = test_instance

            try:
                await test_instance.start()
                return await test_instance.get_response()
            except Exception:
                # Clean up failed test
                if test_id in self._load_tests:
                    del self._load_tests[test_id]
                raise

    async def stop_load_test(self, test_id: str) -> LoadTestResponse:
        """Stop a specific concurrent load test.

        Args:
            test_id: Identifier of the load test to stop

        Returns:
            Load test response with final status

        Raises:
            KeyError: If test_id not found
        """
        async with self._lock:
            if test_id not in self._load_tests:
                msg = f"Load test {test_id} not found"
                raise KeyError(msg)

            test_instance = self._load_tests[test_id]
            await test_instance.stop()
            return await test_instance.get_response()

    async def stop_all_load_tests(self) -> dict[str, LoadTestResponse]:
        """Stop all running load tests.

        Returns:
            Dictionary of test_id -> final response for all tests
        """
        async with self._lock:
            responses = {}
            for test_id, test_instance in self._load_tests.items():
                await test_instance.stop()
                responses[test_id] = await test_instance.get_response()
            return responses

    async def get_load_test_status(self, test_id: str) -> LoadTestResponse:
        """Get status of a specific load test.

        Args:
            test_id: Identifier of the load test

        Returns:
            Load test response with current status

        Raises:
            KeyError: If test_id not found
        """
        if test_id not in self._load_tests:
            msg = f"Load test {test_id} not found"
            raise KeyError(msg)

        return await self._load_tests[test_id].get_response()

    async def get_all_load_tests_status(self) -> dict[str, LoadTestResponse]:
        """Get status of all load tests.

        Returns:
            Dictionary of test_id -> response for all tests
        """
        responses = {}
        for test_id, test_instance in self._load_tests.items():
            responses[test_id] = await test_instance.get_response()
        return responses

    def get_active_test_ids(self) -> list[str]:
        """Get list of currently active (running or starting) test IDs.

        Returns:
            List of active test IDs
        """
        return [
            test_id
            for test_id, test_instance in self._load_tests.items()
            if test_instance.status in (LoadTestStatus.RUNNING, LoadTestStatus.STARTING)
        ]

    def get_all_test_ids(self) -> list[str]:
        """Get list of all test IDs (active and stopped).

        Returns:
            List of all test IDs
        """
        return list(self._load_tests.keys())

    async def cleanup_stopped_tests(self) -> None:
        """Clean up stopped test instances to free memory."""
        async with self._lock:
            to_remove = [
                test_id
                for test_id, test_instance in self._load_tests.items()
                if test_instance.status in (LoadTestStatus.STOPPED, LoadTestStatus.ERROR)
            ]
            for test_id in to_remove:
                del self._load_tests[test_id]

            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} stopped load test instances")
