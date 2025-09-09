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

        # Rolling average tracking (last 10 seconds of requests)
        self._request_history: deque[RequestRecord] = deque()
        self._rolling_window_seconds = 10.0

        # Adaptive scaling state
        self._last_scaling_time = 0.0
        self._adaptive_scaling_active = False

        # Latency compensation tracking
        self._compensation_history: deque[float] = deque(maxlen=1000)  # Last 1000 compensations

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

        # Start adaptive scaling task if enabled
        if settings.adaptive_scaling_enabled:
            scaling_task = asyncio.create_task(self._adaptive_scaling_monitor())
            self._tasks.append(scaling_task)

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

            # Calculate RPS accuracy
            target_rps = self.config.requests_per_second
            achieved_rps = (
                self.stats.rolling_requests_per_second
            )  # Use rolling average for accuracy
            rps_accuracy = (achieved_rps / target_rps * 100.0) if target_rps > 0 else 0.0

            # Calculate average compensation
            avg_compensation = 0.0
            if self._compensation_history:
                avg_compensation = sum(self._compensation_history) / len(self._compensation_history)

            # Get worker counts (exclude adaptive scaling monitor)
            current_workers = 0
            for task in self._tasks:
                coro = task.get_coro()
                coro_name = coro.__name__ if coro and hasattr(coro, "__name__") else str(task)
                if "_adaptive_scaling_monitor" not in coro_name:
                    current_workers += 1

            base_workers, _ = self._calculate_worker_config(target_rps)

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
                # New RPS accuracy and compensation metrics
                target_requests_per_second=target_rps,
                achieved_rps_accuracy=rps_accuracy,
                latency_compensation_active=settings.latency_compensation_enabled,
                adaptive_scaling_active=self._adaptive_scaling_active,
                current_worker_count=current_workers,
                base_worker_count=base_workers,
                avg_compensation_ms=avg_compensation,
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

        # Calculate new worker count (excludes adaptive scaling monitor)
        new_worker_count, new_interval = self._calculate_worker_config(new_rps)

        # Count current worker tasks (exclude adaptive scaling monitor)
        current_worker_count = 0
        scaling_monitor_task = None
        worker_tasks = []

        for task in self._tasks:
            coro = task.get_coro()
            coro_name = coro.__name__ if coro and hasattr(coro, "__name__") else str(task)
            if "_adaptive_scaling_monitor" in coro_name:
                scaling_monitor_task = task
            else:
                worker_tasks.append(task)
                current_worker_count += 1

        if new_worker_count > current_worker_count:
            # Scale up: add more worker tasks
            for _ in range(new_worker_count - current_worker_count):
                task = asyncio.create_task(self._generate_load_worker(new_interval))
                worker_tasks.append(task)
        elif new_worker_count < current_worker_count:
            # Scale down: cancel excess worker tasks
            tasks_to_cancel = worker_tasks[new_worker_count:]
            for task in tasks_to_cancel:
                if not task.done():
                    task.cancel()

            # Wait for cancelled tasks to finish
            if tasks_to_cancel:
                await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

            # Keep only the required number of worker tasks
            worker_tasks = worker_tasks[:new_worker_count]

        # Rebuild task list: workers + scaling monitor (if it exists)
        self._tasks = worker_tasks[:]
        if scaling_monitor_task is not None:
            self._tasks.append(scaling_monitor_task)

        # Note: Existing tasks will naturally adjust to the new interval via their next sleep cycle
        # This provides gradual ramping rather than immediate step changes

    async def _check_and_apply_adaptive_scaling(self) -> None:
        """Check if adaptive scaling should be applied based on current performance."""
        if not settings.adaptive_scaling_enabled or not self.is_running:
            return

        current_time = time.time()

        # Check cooldown period
        if current_time - self._last_scaling_time < settings.scaling_cooldown_seconds:
            return

        # Calculate average response time from recent requests
        self._clean_old_requests()
        if len(self._request_history) < 10:  # Need minimum samples
            return

        recent_response_times = [
            req.response_time_ms for req in self._request_history if req.success
        ]
        if not recent_response_times:
            return

        avg_response_time_ms = sum(recent_response_times) / len(recent_response_times)

        # Check if scaling is needed
        should_scale_up = (
            avg_response_time_ms > settings.latency_threshold_ms
            and len(self._tasks) < settings.max_adaptive_workers
        )

        should_scale_down = (
            avg_response_time_ms
            < settings.latency_threshold_ms * 0.5  # Scale down at 50% of threshold
            and len(self._tasks) > self._calculate_worker_config(self.config.requests_per_second)[0]
            and self._adaptive_scaling_active  # Only scale down if we previously scaled up
        )

        if should_scale_up:
            await self._scale_workers_up()
            self._last_scaling_time = current_time
            self._adaptive_scaling_active = True

        elif should_scale_down:
            await self._scale_workers_down()
            self._last_scaling_time = current_time

    async def _scale_workers_up(self) -> None:
        """Add additional workers to handle high latency."""
        if len(self._tasks) >= settings.max_adaptive_workers:
            return

        # Add 20% more workers or at least 1, up to the maximum
        current_workers = len(self._tasks)
        additional_workers = max(1, int(current_workers * 0.2))
        target_workers = min(current_workers + additional_workers, settings.max_adaptive_workers)

        # Calculate new interval for additional workers
        _, interval = self._calculate_worker_config(self.config.requests_per_second)

        # Add new worker tasks
        for _ in range(target_workers - current_workers):
            task = asyncio.create_task(self._generate_load_worker(interval))
            self._tasks.append(task)

    async def _scale_workers_down(self) -> None:
        """Remove excess workers when latency is low."""
        base_workers, _ = self._calculate_worker_config(self.config.requests_per_second)
        current_workers = len(self._tasks)

        if current_workers <= base_workers:
            self._adaptive_scaling_active = False
            return

        # Remove 20% of excess workers or at least 1
        excess_workers = current_workers - base_workers
        workers_to_remove = max(1, int(excess_workers * 0.2))
        target_workers = max(base_workers, current_workers - workers_to_remove)

        # Cancel excess tasks
        tasks_to_cancel = self._tasks[target_workers:]
        for task in tasks_to_cancel:
            if not task.done():
                task.cancel()

        # Wait for cancelled tasks to complete
        if tasks_to_cancel:
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

        # Update task list
        self._tasks = self._tasks[:target_workers]

        # Check if we've returned to base worker count
        if len(self._tasks) == base_workers:
            self._adaptive_scaling_active = False

    def _clean_old_requests(self) -> None:
        """Remove old requests from the rolling window for accurate averaging."""
        current_time = time.time()
        cutoff_time = current_time - self._rolling_window_seconds
        while self._request_history and self._request_history[0].timestamp < cutoff_time:
            self._request_history.popleft()

    async def _adaptive_scaling_monitor(self) -> None:
        """Monitor performance and apply adaptive scaling as needed."""
        while self.is_running:
            try:
                await self._check_and_apply_adaptive_scaling()
                # Check every 2 seconds for scaling opportunities
                await asyncio.sleep(2.0)
            except asyncio.CancelledError:
                break
            except Exception:
                # Continue monitoring even if scaling fails
                await asyncio.sleep(2.0)

    async def _generate_load_worker(self, initial_interval: float) -> None:
        """Worker coroutine that generates load at specified interval.

        Args:
            initial_interval: Initial time interval between requests in seconds
        """
        if not hasattr(self, "_start_time"):
            self._start_time = time.time()

        while self.is_running:
            try:
                # Record request start time for latency compensation
                request_start_time = time.time()

                # Generate and execute request
                result, request_data = await self._execute_single_request()
                await self._update_stats(result)

                # Metrics recording removed for load_tester

                # Calculate current interval distributed across worker tasks only (exclude monitor tasks)
                num_workers = 0
                for task in self._tasks:
                    coro = task.get_coro()
                    coro_name = coro.__name__ if coro and hasattr(coro, "__name__") else str(task)
                    if "_adaptive_scaling_monitor" not in coro_name:
                        num_workers += 1

                num_workers = max(num_workers, 1)  # Ensure at least 1
                target_interval = num_workers / max(self.config.requests_per_second, 0.1)

                # Apply latency compensation if enabled
                if settings.latency_compensation_enabled:
                    request_duration = time.time() - request_start_time
                    compensated_interval = target_interval - request_duration

                    # Apply minimum sleep threshold to prevent CPU spinning
                    min_sleep_seconds = settings.min_sleep_threshold_ms / 1000.0
                    final_interval = max(min_sleep_seconds, compensated_interval)

                    # Track compensation amount for metrics
                    compensation_ms = (target_interval - final_interval) * 1000.0
                    self._compensation_history.append(compensation_ms)
                else:
                    final_interval = target_interval

                # Wait for next request interval
                await asyncio.sleep(final_interval)

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

                # Use target interval for error sleep (no compensation for errors)
                num_workers = len(self._tasks) if self._tasks else 1
                target_interval = num_workers / max(self.config.requests_per_second, 0.1)
                await asyncio.sleep(target_interval)

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
        """Calculate 10-second rolling averages from recent request history."""
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
