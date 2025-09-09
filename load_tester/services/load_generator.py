"""Async HTTP load generation engine for currency API testing."""

import asyncio
import random
import time
from collections import deque
from typing import NamedTuple

import aiohttp
from pydantic import ValidationError

from load_tester.auth.jwt_generator import get_jwt_token_manager
from load_tester.auth.test_users import get_random_test_user
from load_tester.config import settings
from load_tester.models.load_test import LoadTestConfig, LoadTestStats
from load_tester.services.currency_patterns import CurrencyPatterns


class RequestRecord(NamedTuple):
    """Record of a single request for rolling statistics."""

    timestamp: float
    success: bool
    response_time_ms: float


class LoadGenerationResult:
    """Result of a single load generation request."""

    def __init__(
        self,
        *,
        success: bool,
        response_time_ms: float,
        status_code: int | None = None,
        error_message: str | None = None,
    ) -> None:
        """Initialize load generation result.

        Args:
            success: Whether the request was successful
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
            error_message: Error message if request failed
        """
        self.success = success
        self.response_time_ms = response_time_ms
        self.status_code = status_code
        self.error_message = error_message


class LoadGenerator:
    """Async HTTP load generator for currency conversion API."""

    def __init__(self, config: LoadTestConfig) -> None:
        """Initialize load generator.

        Args:
            config: Load test configuration
        """
        self.config = config
        self.currency_patterns = CurrencyPatterns()
        self.stats = LoadTestStats()
        self.is_running = False
        self._session: aiohttp.ClientSession | None = None
        self._tasks: list[asyncio.Task] = []
        self._stats_lock = asyncio.Lock()

        # JWT authentication management
        self._jwt_token_manager = get_jwt_token_manager()

        # Rolling average tracking (last 60 seconds of requests)
        self._request_history: deque[RequestRecord] = deque()
        self._rolling_window_seconds = 60.0

    def _calculate_worker_config(self, rps: float) -> tuple[int, float]:
        """Calculate optimal number of workers and interval for given RPS.

        Args:
            rps: Target requests per second

        Returns:
            Tuple of (num_workers, interval_per_worker)
        """
        if rps <= 10:
            # For low RPS, use single worker with appropriate interval
            return 1, 1.0 / rps
        # For higher RPS, use multiple workers but limit to reasonable number
        num_workers = min(int(rps / 2), 10)
        interval = num_workers / rps
        return num_workers, interval

    async def start(self) -> None:
        """Start the load generation process."""
        if self.is_running:
            msg = "Load generator is already running"
            raise RuntimeError(msg)

        self.is_running = True
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.request_timeout),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=50),
        )

        # Start load generation tasks
        num_workers, interval = self._calculate_worker_config(self.config.requests_per_second)
        for _ in range(num_workers):
            task = asyncio.create_task(self._generate_load_worker(interval))
            self._tasks.append(task)

    async def stop(self) -> LoadTestStats:
        """Stop the load generation process.

        Returns:
            Final load test statistics
        """
        if not self.is_running:
            return self.stats

        self.is_running = False

        # Cancel all running tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete with cancellation
        if self._tasks:
            # Give a small delay for graceful cancellation
            await asyncio.sleep(0.01)
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Close HTTP session
        if self._session:
            await self._session.close()
            self._session = None

        self._tasks.clear()
        return self.stats

    async def get_current_stats(self) -> LoadTestStats:
        """Get current load test statistics.

        Returns:
            Current statistics
        """
        async with self._stats_lock:
            # Calculate current requests per second
            if self.stats.total_requests > 0:
                elapsed_seconds = time.time() - getattr(self, "_start_time", time.time())
                if elapsed_seconds > 0:
                    self.stats.requests_per_second = self.stats.total_requests / elapsed_seconds

            # Update rolling averages
            self._calculate_rolling_averages()

            return LoadTestStats(
                total_requests=self.stats.total_requests,
                successful_requests=self.stats.successful_requests,
                failed_requests=self.stats.failed_requests,
                avg_response_time_ms=self.stats.avg_response_time_ms,
                min_response_time_ms=self.stats.min_response_time_ms,
                max_response_time_ms=self.stats.max_response_time_ms,
                requests_per_second=self.stats.requests_per_second,
                rolling_success_rate=self.stats.rolling_success_rate,
                rolling_avg_response_ms=self.stats.rolling_avg_response_ms,
                rolling_requests_per_second=self.stats.rolling_requests_per_second,
            )

    async def ramp_to_config(self, new_config: LoadTestConfig) -> None:
        """Ramp load to a new configuration without stopping the test.

        Args:
            new_config: New load test configuration to ramp to
        """
        if not self.is_running:
            msg = "Cannot ramp load - generator is not running"
            raise RuntimeError(msg)

        old_rps = self.config.requests_per_second
        new_rps = new_config.requests_per_second

        # Update configuration (currency patterns and amounts can change immediately)
        self.config = new_config
        self.currency_patterns = CurrencyPatterns()

        # If RPS is the same, no need to adjust tasks
        if old_rps == new_rps:
            return

        # Calculate new task configuration
        new_task_count, new_interval = self._calculate_worker_config(new_rps)
        current_task_count = len(self._tasks)

        if new_task_count > current_task_count:
            # Scale up: add more tasks
            for _ in range(new_task_count - current_task_count):
                task = asyncio.create_task(self._generate_load_worker(new_interval))
                self._tasks.append(task)
        elif new_task_count < current_task_count:
            # Scale down: cancel excess tasks
            tasks_to_cancel = self._tasks[new_task_count:]
            for task in tasks_to_cancel:
                if not task.done():
                    task.cancel()

            # Wait for cancelled tasks to finish
            if tasks_to_cancel:
                await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

            # Keep only the required number of tasks
            self._tasks = self._tasks[:new_task_count]

        # Note: Existing tasks will naturally adjust to the new interval via their next sleep cycle
        # This provides gradual ramping rather than immediate step changes

    async def _generate_load_worker(self, initial_interval: float) -> None:
        """Worker coroutine that generates load at specified interval.

        Args:
            initial_interval: Initial time interval between requests in seconds
        """
        if not hasattr(self, "_start_time"):
            self._start_time = time.time()

        while self.is_running:
            try:
                # Generate and execute request
                result, request_data = await self._execute_single_request()
                await self._update_stats(result)

                # Metrics recording removed for load_tester

                # Calculate current interval distributed across all workers
                num_workers = len(self._tasks) if self._tasks else 1
                current_interval = num_workers / max(self.config.requests_per_second, 0.1)

                # Wait for next request interval
                await asyncio.sleep(current_interval)

            except asyncio.CancelledError:
                break
            except Exception:
                # Log error but continue generating load
                error_result = LoadGenerationResult(
                    success=False,
                    response_time_ms=0.0,
                    error_message="Unexpected worker error",
                )
                await self._update_stats(error_result)

                # Use current interval for error sleep as well
                num_workers = len(self._tasks) if self._tasks else 1
                current_interval = num_workers / max(self.config.requests_per_second, 0.1)
                await asyncio.sleep(current_interval)

    async def _execute_single_request(self) -> tuple[LoadGenerationResult, dict[str, str | float]]:
        """Execute a single currency conversion request.

        Returns:
            Tuple of (result, request_data)
        """
        empty_request_data: dict[str, str | float] = {}

        if not self._session:
            return (
                LoadGenerationResult(
                    success=False,
                    response_time_ms=0.0,
                    error_message="HTTP session not initialized",
                ),
                empty_request_data,
            )

        try:
            # Generate request data (valid or invalid based on error injection settings)
            if (
                self.config.error_injection_enabled
                and random.random() < self.config.error_injection_rate
            ):
                request_data = self.currency_patterns.generate_invalid_request()
            else:
                request_data = self.currency_patterns.generate_random_request()

            # Select random test user and get JWT token for authentication
            test_user = get_random_test_user()
            authorization_header = self._jwt_token_manager.get_authorization_header(test_user)

            # Prepare headers with JWT authentication
            headers = {"Authorization": authorization_header, "Content-Type": "application/json"}

            # Make HTTP request to currency conversion endpoint
            url = f"{settings.target_api_base_url}/api/v1/convert"
            start_time = time.time()

            async with self._session.post(url, json=request_data, headers=headers) as response:
                response_time_ms = (time.time() - start_time) * 1000

                # Read response body to ensure full request completion
                await response.text()

                return (
                    LoadGenerationResult(
                        success=response.status == 200,
                        response_time_ms=response_time_ms,
                        status_code=response.status,
                        error_message=None if response.status == 200 else f"HTTP {response.status}",
                    ),
                    request_data,
                )

        except TimeoutError:
            response_time_ms = settings.request_timeout * 1000
            return (
                LoadGenerationResult(
                    success=False,
                    response_time_ms=response_time_ms,
                    error_message="Request timeout",
                ),
                request_data if "request_data" in locals() else empty_request_data,
            )
        except aiohttp.ClientError as e:
            return (
                LoadGenerationResult(
                    success=False,
                    response_time_ms=0.0,
                    error_message=f"Client error: {e}",
                ),
                request_data if "request_data" in locals() else empty_request_data,
            )
        except ValidationError as e:
            return (
                LoadGenerationResult(
                    success=False,
                    response_time_ms=0.0,
                    error_message=f"Validation error: {e}",
                ),
                request_data if "request_data" in locals() else empty_request_data,
            )
        except Exception as e:
            return (
                LoadGenerationResult(
                    success=False,
                    response_time_ms=0.0,
                    error_message=f"Unexpected error: {e}",
                ),
                request_data if "request_data" in locals() else empty_request_data,
            )

    async def _update_stats(self, result: LoadGenerationResult) -> None:
        """Update load test statistics with result.

        Args:
            result: Result of a single request
        """
        async with self._stats_lock:
            current_time = time.time()

            # Update cumulative stats
            self.stats.total_requests += 1

            if result.success:
                self.stats.successful_requests += 1
            else:
                self.stats.failed_requests += 1

            # Update response time statistics
            if result.response_time_ms > 0:
                if (
                    self.stats.min_response_time_ms == 0
                    or result.response_time_ms < self.stats.min_response_time_ms
                ):
                    self.stats.min_response_time_ms = result.response_time_ms

                if result.response_time_ms > self.stats.max_response_time_ms:
                    self.stats.max_response_time_ms = result.response_time_ms

                # Calculate running average
                total_time = self.stats.avg_response_time_ms * (self.stats.total_requests - 1)
                self.stats.avg_response_time_ms = (
                    total_time + result.response_time_ms
                ) / self.stats.total_requests

            # Add to rolling window
            self._request_history.append(
                RequestRecord(
                    timestamp=current_time,
                    success=result.success,
                    response_time_ms=result.response_time_ms,
                )
            )

            # Clean old records outside the rolling window
            cutoff_time = current_time - self._rolling_window_seconds
            while self._request_history and self._request_history[0].timestamp < cutoff_time:
                self._request_history.popleft()

    def _calculate_rolling_averages(self) -> None:
        """Calculate 1-minute rolling averages from recent request history."""
        if not self._request_history:
            self.stats.rolling_success_rate = 0.0
            self.stats.rolling_avg_response_ms = 0.0
            self.stats.rolling_requests_per_second = 0.0
            return

        current_time = time.time()
        cutoff_time = current_time - self._rolling_window_seconds

        # Filter to requests in the last minute
        recent_requests = [req for req in self._request_history if req.timestamp >= cutoff_time]

        if not recent_requests:
            self.stats.rolling_success_rate = 0.0
            self.stats.rolling_avg_response_ms = 0.0
            self.stats.rolling_requests_per_second = 0.0
            return

        # Calculate rolling metrics
        total_recent = len(recent_requests)
        successful_recent = sum(1 for req in recent_requests if req.success)

        self.stats.rolling_success_rate = (successful_recent / total_recent) * 100.0

        # Average response time for successful requests only
        successful_times = [
            req.response_time_ms
            for req in recent_requests
            if req.success and req.response_time_ms > 0
        ]
        self.stats.rolling_avg_response_ms = (
            sum(successful_times) / len(successful_times) if successful_times else 0.0
        )

        # Requests per second over the rolling window
        # Calculate RPS as total requests in window divided by window size
        self.stats.rolling_requests_per_second = total_recent / self._rolling_window_seconds
