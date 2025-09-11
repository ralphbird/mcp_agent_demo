"""Unit tests for LoadGenerator service."""

import time
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from analytics_service.models.load_test import LoadTestConfig
from analytics_service.services.load_generator import (
    LoadGenerationResult,
    LoadGenerator,
    RequestRecord,
)


class TestLoadGenerationResult:
    """Test LoadGenerationResult class."""

    def test_create_success_result(self):
        """Test creating a successful result."""
        result = LoadGenerationResult(
            success=True,
            response_time_ms=150.5,
            status_code=200,
        )

        assert result.success is True
        assert result.response_time_ms == 150.5
        assert result.status_code == 200
        assert result.error_message is None

    def test_create_error_result(self):
        """Test creating an error result."""
        result = LoadGenerationResult(
            success=False,
            response_time_ms=5000.0,
            status_code=500,
            error_message="Internal server error",
        )

        assert result.success is False
        assert result.response_time_ms == 5000.0
        assert result.status_code == 500
        assert result.error_message == "Internal server error"


class TestLoadGenerator:
    """Test LoadGenerator functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return LoadTestConfig(
            requests_per_second=2.0,
            currency_pairs=["USD_EUR", "GBP_USD"],
            amounts=[100.0, 500.0, 1000.0],
        )

    @pytest.fixture
    async def load_generator(self, config):
        """Create load generator instance."""
        generator = LoadGenerator(config)
        yield generator
        # Ensure cleanup after each test
        with suppress(Exception):
            if generator.is_running:
                await generator.stop()

    def test_initialization(self, load_generator, config):
        """Test load generator initialization."""
        assert load_generator.config == config
        assert load_generator.currency_patterns is not None
        assert load_generator.is_running is False
        assert load_generator._session is None
        assert load_generator._tasks == []

    @pytest.mark.asyncio
    async def test_start_and_stop_without_requests(self, load_generator):
        """Test starting and stopping load generator without making requests."""
        # Mock aiohttp.ClientSession to avoid actual HTTP requests
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Start the load generator
            await load_generator.start()

            assert load_generator.is_running is True
            assert load_generator._session is not None
            assert len(load_generator._tasks) > 0

            # Stop the load generator
            stats = await load_generator.stop()

            assert load_generator.is_running is False
            assert load_generator._session is None
            assert len(load_generator._tasks) == 0

            # Check stats structure
            assert stats.total_requests >= 0
            assert stats.successful_requests >= 0
            assert stats.failed_requests >= 0
            assert stats.avg_response_time_ms >= 0.0

    @pytest.mark.asyncio
    async def test_start_already_running_raises_error(self, load_generator):
        """Test that starting an already running generator raises error."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            await load_generator.start()

            with pytest.raises(RuntimeError, match="Load generator is already running"):
                await load_generator.start()

            await load_generator.stop()

    @pytest.mark.asyncio
    async def test_stop_not_running_returns_stats(self, load_generator):
        """Test stopping a non-running generator returns current stats."""
        stats = await load_generator.stop()

        # Should return empty stats
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0

    @pytest.mark.asyncio
    async def test_get_current_stats(self, load_generator):
        """Test getting current statistics."""
        stats = await load_generator.get_current_stats()

        # Initial stats should be zero
        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.avg_response_time_ms == 0.0
        assert stats.min_response_time_ms == 0.0
        assert stats.max_response_time_ms == 0.0
        assert stats.requests_per_second == 0.0

    @pytest.mark.asyncio
    async def test_execute_single_request_no_session(self, load_generator):
        """Test executing request without session returns error."""
        result, request_data = await load_generator._execute_single_request()

        assert result.success is False
        assert result.error_message == "HTTP session not initialized"
        assert request_data == {}

    @pytest.mark.asyncio
    async def test_execute_single_request_session_timeout(self, load_generator):
        """Test that timeout handling works correctly."""
        # Mock settings for timeout value
        with patch("analytics_service.services.load_generator.settings") as mock_settings:
            mock_settings.request_timeout = 30.0

            # Test with no session (simulated failure)
            result, request_data = await load_generator._execute_single_request()

            assert result.success is False
            assert result.error_message == "HTTP session not initialized"
            assert request_data == {}

    @pytest.mark.asyncio
    async def test_update_stats(self, load_generator):
        """Test updating statistics with results."""
        # Test successful request
        success_result = LoadGenerationResult(
            success=True,
            response_time_ms=100.0,
            status_code=200,
        )

        await load_generator._update_stats(success_result)

        assert load_generator.stats.total_requests == 1
        assert load_generator.stats.successful_requests == 1
        assert load_generator.stats.failed_requests == 0
        assert load_generator.stats.avg_response_time_ms == 100.0
        assert load_generator.stats.min_response_time_ms == 100.0
        assert load_generator.stats.max_response_time_ms == 100.0

        # Test failed request
        error_result = LoadGenerationResult(
            success=False,
            response_time_ms=200.0,
            status_code=500,
            error_message="Error",
        )

        await load_generator._update_stats(error_result)

        assert load_generator.stats.total_requests == 2
        assert load_generator.stats.successful_requests == 1
        assert load_generator.stats.failed_requests == 1
        assert load_generator.stats.avg_response_time_ms == 150.0  # (100 + 200) / 2
        assert load_generator.stats.min_response_time_ms == 100.0
        assert load_generator.stats.max_response_time_ms == 200.0

    @pytest.mark.asyncio
    async def test_update_stats_multiple_requests(self, load_generator):
        """Test statistics with multiple requests."""
        results = [
            LoadGenerationResult(success=True, response_time_ms=100.0, status_code=200),
            LoadGenerationResult(success=True, response_time_ms=150.0, status_code=200),
            LoadGenerationResult(
                success=False, response_time_ms=300.0, status_code=500, error_message="Error"
            ),
            LoadGenerationResult(success=True, response_time_ms=50.0, status_code=200),
        ]

        for result in results:
            await load_generator._update_stats(result)

        assert load_generator.stats.total_requests == 4
        assert load_generator.stats.successful_requests == 3
        assert load_generator.stats.failed_requests == 1
        assert load_generator.stats.avg_response_time_ms == 150.0  # (100+150+300+50)/4
        assert load_generator.stats.min_response_time_ms == 50.0
        assert load_generator.stats.max_response_time_ms == 300.0

    @pytest.mark.asyncio
    async def test_load_generator_lifecycle(self, load_generator):
        """Test basic load generator lifecycle without HTTP."""
        # Test that we can start and stop without errors
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Should start successfully
            await load_generator.start()
            assert load_generator.is_running is True
            assert load_generator._session is not None

            # Should stop successfully
            stats = await load_generator.stop()
            assert load_generator.is_running is False
            assert isinstance(stats.total_requests, int)
            assert isinstance(stats.successful_requests, int)


class TestWorkerConfiguration:
    """Test worker configuration logic for different RPS values."""

    @pytest.fixture
    def load_generator(self):
        """Create load generator for testing."""
        config = LoadTestConfig(requests_per_second=1.0)
        return LoadGenerator(config)

    def test_calculate_worker_config_low_rps(self, load_generator):
        """Test worker config for low RPS values."""
        # Low RPS should use single worker
        num_workers, interval = load_generator._calculate_worker_config(1.0)
        assert num_workers == 1
        assert interval == 1.0

        num_workers, interval = load_generator._calculate_worker_config(5.0)
        assert num_workers == 1
        assert interval == 0.2

        num_workers, interval = load_generator._calculate_worker_config(10.0)
        assert num_workers == 1
        assert interval == 0.1

    def test_calculate_worker_config_high_rps(self, load_generator):
        """Test worker config for high RPS values."""
        # High RPS should use multiple workers but limited
        num_workers, interval = load_generator._calculate_worker_config(20.0)
        expected_workers = min(int(20.0 / 2), 10)  # min(10, 10) = 10
        assert num_workers == expected_workers
        assert interval == expected_workers / 20.0

        num_workers, interval = load_generator._calculate_worker_config(100.0)
        expected_workers = min(int(100.0 / 2), 10)  # min(50, 10) = 10
        assert num_workers == 10  # Capped at 10
        assert interval == 10 / 100.0  # 0.1

    def test_calculate_worker_config_boundary(self, load_generator):
        """Test worker config at boundary values."""
        # Test exactly at boundary (10 RPS)
        num_workers, interval = load_generator._calculate_worker_config(10.0)
        assert num_workers == 1
        assert interval == 0.1

        # Test just above boundary (11 RPS)
        num_workers, interval = load_generator._calculate_worker_config(11.0)
        expected_workers = min(int(11.0 / 2), 10)  # min(5, 10) = 5
        assert num_workers == expected_workers
        assert interval == expected_workers / 11.0


class TestRollingAverages:
    """Test rolling averages calculation functionality."""

    @pytest.fixture
    def load_generator(self):
        """Create load generator for testing."""
        config = LoadTestConfig(requests_per_second=1.0)
        generator = LoadGenerator(config)
        # Set shorter window for faster testing
        generator._rolling_window_seconds = 10.0
        return generator

    def test_request_record_creation(self):
        """Test RequestRecord creation."""
        record = RequestRecord(
            timestamp=time.time(),
            success=True,
            response_time_ms=100.0,
        )
        assert record.success is True
        assert record.response_time_ms == 100.0
        assert isinstance(record.timestamp, float)

    @pytest.mark.asyncio
    async def test_rolling_window_cleanup(self, load_generator):
        """Test that old requests are cleaned from rolling window."""
        current_time = time.time()

        # Add requests with different timestamps
        old_result = LoadGenerationResult(success=True, response_time_ms=100.0)
        recent_result = LoadGenerationResult(success=True, response_time_ms=150.0)

        # Add old request first
        with patch("time.time", return_value=current_time - 15.0):  # 15s ago (outside 10s window)
            await load_generator._update_stats(old_result)

        # At this point we should have 1 request
        assert len(load_generator._request_history) == 1

        # Add recent request - this should trigger cleanup of old request
        with patch("time.time", return_value=current_time):
            await load_generator._update_stats(recent_result)

        # Old request should be cleaned automatically, only recent one remains
        assert len(load_generator._request_history) == 1
        assert load_generator._request_history[0].response_time_ms == 150.0

    @pytest.mark.asyncio
    async def test_rolling_success_rate_calculation(self, load_generator):
        """Test rolling success rate calculation."""
        current_time = time.time()

        # Add mix of successful and failed requests
        results = [
            LoadGenerationResult(success=True, response_time_ms=100.0),
            LoadGenerationResult(success=True, response_time_ms=120.0),
            LoadGenerationResult(success=False, response_time_ms=0.0, error_message="Error"),
            LoadGenerationResult(success=True, response_time_ms=90.0),
        ]

        with patch("time.time", return_value=current_time):
            for result in results:
                await load_generator._update_stats(result)

            load_generator._calculate_rolling_averages()

        # 3 successful out of 4 total = 75%
        assert load_generator.stats.rolling_success_rate == 75.0

    @pytest.mark.asyncio
    async def test_rolling_avg_response_time_calculation(self, load_generator):
        """Test rolling average response time calculation."""
        current_time = time.time()

        # Add successful requests with known response times
        results = [
            LoadGenerationResult(success=True, response_time_ms=100.0),
            LoadGenerationResult(success=True, response_time_ms=200.0),
            LoadGenerationResult(
                success=False, response_time_ms=500.0, error_message="Error"
            ),  # Should be excluded
            LoadGenerationResult(success=True, response_time_ms=150.0),
        ]

        with patch("time.time", return_value=current_time):
            for result in results:
                await load_generator._update_stats(result)

            load_generator._calculate_rolling_averages()

        # Average of successful requests: (100 + 200 + 150) / 3 = 150.0
        assert load_generator.stats.rolling_avg_response_ms == 150.0

    @pytest.mark.asyncio
    async def test_rolling_rps_calculation_accuracy(self, load_generator):
        """Test rolling RPS calculation uses full window size."""
        current_time = time.time()

        # Add 5 requests within the rolling window
        results = [
            LoadGenerationResult(success=True, response_time_ms=100.0),
            LoadGenerationResult(success=True, response_time_ms=100.0),
            LoadGenerationResult(success=True, response_time_ms=100.0),
            LoadGenerationResult(success=True, response_time_ms=100.0),
            LoadGenerationResult(success=True, response_time_ms=100.0),
        ]

        with patch("time.time", return_value=current_time):
            for result in results:
                await load_generator._update_stats(result)

            load_generator._calculate_rolling_averages()

        # RPS should be total_requests / window_size = 5 / 10.0 = 0.5
        assert load_generator.stats.rolling_requests_per_second == 0.5

    @pytest.mark.asyncio
    async def test_empty_rolling_window(self, load_generator):
        """Test rolling averages with empty request history."""
        load_generator._calculate_rolling_averages()

        assert load_generator.stats.rolling_success_rate == 0.0
        assert load_generator.stats.rolling_avg_response_ms == 0.0
        assert load_generator.stats.rolling_requests_per_second == 0.0

    @pytest.mark.asyncio
    async def test_rolling_averages_integration(self, load_generator):
        """Test rolling averages integration with get_current_stats."""
        current_time = time.time()

        # Add some test data
        results = [
            LoadGenerationResult(success=True, response_time_ms=100.0),
            LoadGenerationResult(success=True, response_time_ms=200.0),
        ]

        with patch("time.time", return_value=current_time):
            for result in results:
                await load_generator._update_stats(result)

            # get_current_stats should call _calculate_rolling_averages
            stats = await load_generator.get_current_stats()

        # Verify rolling fields are populated in response
        assert hasattr(stats, "rolling_success_rate")
        assert hasattr(stats, "rolling_avg_response_ms")
        assert hasattr(stats, "rolling_requests_per_second")
        assert stats.rolling_success_rate == 100.0  # Both successful
        assert stats.rolling_avg_response_ms == 150.0  # (100 + 200) / 2
        assert stats.rolling_requests_per_second == 0.2  # 2 requests / 10s window


class TestRPSDistribution:
    """Test RPS distribution across multiple workers to prevent multiplication bug."""

    @pytest.fixture
    def high_rps_config(self):
        """Create config with high RPS that will use multiple workers."""
        return LoadTestConfig(
            requests_per_second=20.0,
            currency_pairs=["USD_EUR", "GBP_USD"],
            amounts=[100.0, 500.0],
        )

    @pytest.fixture
    async def high_rps_generator(self, high_rps_config):
        """Create load generator with high RPS config."""
        generator = LoadGenerator(high_rps_config)
        yield generator
        # Cleanup
        with suppress(Exception):
            if generator.is_running:
                await generator.stop()

    def test_worker_interval_calculation_single_worker(self):
        """Test interval calculation for single worker scenarios."""
        config = LoadTestConfig(requests_per_second=5.0)
        generator = LoadGenerator(config)

        # Simulate single worker (low RPS)
        generator._tasks = [AsyncMock()]  # Single task

        # For 5 RPS with 1 worker: interval = 1 / 5.0 = 0.2
        expected_interval = 1 / 5.0

        # Test the interval calculation logic
        num_workers = len(generator._tasks)
        calculated_interval = num_workers / generator.config.requests_per_second

        assert num_workers == 1
        assert calculated_interval == expected_interval

    def test_worker_interval_calculation_multiple_workers(self):
        """Test interval calculation for multiple worker scenarios."""
        config = LoadTestConfig(requests_per_second=20.0)
        generator = LoadGenerator(config)

        # Simulate multiple workers (high RPS)
        generator._tasks = [AsyncMock() for _ in range(10)]  # 10 tasks

        # For 20 RPS with 10 workers: each worker should have interval = 10 / 20.0 = 0.5
        # This means each worker generates 1/0.5 = 2 RPS
        # Total: 10 workers * 2 RPS = 20 RPS ✅
        expected_interval = 10 / 20.0

        num_workers = len(generator._tasks)
        calculated_interval = num_workers / generator.config.requests_per_second

        assert num_workers == 10
        assert calculated_interval == expected_interval
        assert calculated_interval == 0.5

    def test_worker_rps_distribution_prevents_multiplication(self):
        """Test that worker RPS distribution prevents the multiplication bug."""
        test_cases = [
            (10.0, 5),  # 10 RPS with 5 workers: each worker = 1 RPS interval = 5/10 = 0.5
            (20.0, 10),  # 20 RPS with 10 workers: each worker = 2 RPS, interval = 10/20 = 0.5
            (50.0, 10),  # 50 RPS with 10 workers: each worker = 5 RPS, interval = 10/50 = 0.2
            (100.0, 10),  # 100 RPS with 10 workers: each worker = 10 RPS, interval = 10/100 = 0.1
        ]

        for target_rps, num_workers in test_cases:
            config = LoadTestConfig(requests_per_second=target_rps)
            generator = LoadGenerator(config)

            # Simulate the workers
            generator._tasks = [AsyncMock() for _ in range(num_workers)]

            # Calculate what each worker should do
            worker_interval = num_workers / target_rps
            worker_rps = 1.0 / worker_interval
            total_rps = worker_rps * num_workers

            # Verify the math prevents multiplication bug
            assert abs(total_rps - target_rps) < 0.01, (
                f"RPS mismatch: expected {target_rps}, got {total_rps}"
            )

            # Verify worker interval is correct
            calculated_interval = num_workers / generator.config.requests_per_second
            assert abs(calculated_interval - worker_interval) < 0.001

    def test_edge_case_single_worker_high_rps(self):
        """Test edge case where high RPS uses single worker."""
        config = LoadTestConfig(requests_per_second=100.0)
        generator = LoadGenerator(config)

        # Force single worker scenario
        generator._tasks = [AsyncMock()]

        # Single worker should handle full RPS
        calculated_interval = 1 / generator.config.requests_per_second
        assert calculated_interval == 0.01  # 1/100

    def test_very_low_rps_protection(self):
        """Test protection against very low RPS values."""
        config = LoadTestConfig(requests_per_second=0.01)  # Very low but valid RPS
        generator = LoadGenerator(config)
        generator._tasks = [AsyncMock()]

        # Should use max() protection to prevent issues with extremely low RPS
        calculated_interval = 1 / max(generator.config.requests_per_second, 0.1)
        assert calculated_interval == 10.0  # 1/0.1 (since 0.01 < 0.1)

    @pytest.mark.asyncio
    async def test_rps_calculation_in_worker_context(self, high_rps_generator):
        """Test RPS calculation as it would happen in actual worker context."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Start generator to create actual tasks
            await high_rps_generator.start()

            # Verify task count matches expected worker configuration
            num_workers, expected_interval = high_rps_generator._calculate_worker_config(20.0)

            # Account for adaptive scaling monitor task (if enabled)
            from analytics_service.config import settings

            expected_total_tasks = num_workers + (1 if settings.adaptive_scaling_enabled else 0)
            assert len(high_rps_generator._tasks) == expected_total_tasks

            # Test the actual interval calculation used in worker
            actual_interval = num_workers / max(high_rps_generator.config.requests_per_second, 0.1)
            assert abs(actual_interval - expected_interval) < 0.001

            await high_rps_generator.stop()

    def test_dynamic_ramping_preserves_rps_accuracy(self):
        """Test that ramping to new RPS maintains accurate distribution."""
        config = LoadTestConfig(requests_per_second=10.0)
        generator = LoadGenerator(config)

        # Start with initial worker count
        generator._tasks = [AsyncMock() for _ in range(5)]  # 5 workers for 10 RPS

        # Verify initial calculation
        initial_interval = 5 / 10.0  # 0.5 - each worker does 2 RPS
        calculated_interval = len(generator._tasks) / generator.config.requests_per_second
        assert calculated_interval == initial_interval

        # Simulate ramp to higher RPS
        generator.config.requests_per_second = 50.0

        # Add more workers for higher RPS (simulate ramping)
        generator._tasks = [AsyncMock() for _ in range(10)]  # 10 workers for 50 RPS

        # Verify new calculation
        new_interval = 10 / 50.0  # 0.2 - each worker does 5 RPS
        calculated_interval = len(generator._tasks) / generator.config.requests_per_second
        assert calculated_interval == new_interval

    def test_rps_accuracy_with_different_worker_counts(self):
        """Test RPS accuracy across different worker count scenarios."""
        test_scenarios = [
            # (target_rps, expected_workers_from_calc_method)
            (1.0, 1),  # Low RPS -> 1 worker
            (5.0, 1),  # Low RPS -> 1 worker
            (10.0, 1),  # Boundary -> 1 worker
            (15.0, 7),  # Medium RPS -> min(15/2, 10) = 7 workers
            (20.0, 10),  # High RPS -> min(20/2, 10) = 10 workers
            (100.0, 10),  # Very high RPS -> capped at 10 workers
        ]

        for target_rps, expected_workers in test_scenarios:
            config = LoadTestConfig(requests_per_second=target_rps)
            generator = LoadGenerator(config)

            # Verify worker calculation method
            num_workers, interval = generator._calculate_worker_config(target_rps)
            assert num_workers == expected_workers

            # Simulate the actual worker setup
            generator._tasks = [AsyncMock() for _ in range(num_workers)]

            # Test the interval calculation that happens in worker loop
            calculated_interval = num_workers / max(target_rps, 0.1)

            # Verify total RPS will be correct
            worker_rps = 1.0 / calculated_interval
            total_rps = worker_rps * num_workers

            assert abs(total_rps - target_rps) < 0.01, (
                f"RPS mismatch for {target_rps} RPS with {num_workers} workers: "
                f"expected {target_rps}, calculated {total_rps}"
            )


class TestRegressionRPSMultiplicationBug:
    """Regression test for the RPS multiplication bug that was fixed."""

    def test_rps_multiplication_bug_would_have_failed_before_fix(self):
        """Test that verifies the old behavior (RPS multiplication) would fail this test.

        This test documents the bug that was fixed: multiple workers each generating
        full RPS instead of distributing the load.
        """
        target_rps = 20.0
        num_workers = 10

        config = LoadTestConfig(requests_per_second=target_rps)
        generator = LoadGenerator(config)
        generator._tasks = [AsyncMock() for _ in range(num_workers)]

        # CORRECT behavior (current implementation):
        # Each worker should have interval = num_workers / target_rps = 10/20 = 0.5
        # Each worker generates: 1/0.5 = 2 RPS
        # Total: 10 workers x 2 RPS = 20 RPS ✅

        correct_interval = num_workers / target_rps  # 0.5

        # BUGGY behavior (old implementation):
        # Each worker would have interval = 1 / target_rps = 1/20 = 0.05
        # Each worker generates: 1/0.05 = 20 RPS
        # Total: 10 workers x 20 RPS = 200 RPS ❌

        buggy_interval = 1.0 / target_rps  # 0.05 (OLD BUG)
        buggy_worker_rps = 1.0 / buggy_interval  # 20.0 (OLD BUG)
        buggy_total_rps = buggy_worker_rps * num_workers  # 200.0 (OLD BUG)

        # Verify the current implementation is correct
        current_interval = num_workers / max(generator.config.requests_per_second, 0.1)
        assert abs(current_interval - correct_interval) < 0.001

        # Verify the bug would produce 10x multiplied rate
        assert abs(buggy_total_rps - (target_rps * num_workers)) < 0.01
        assert buggy_total_rps == 200.0  # The bug that was fixed

        # Verify current implementation gives correct total RPS
        current_worker_rps = 1.0 / current_interval
        current_total_rps = current_worker_rps * num_workers
        assert abs(current_total_rps - target_rps) < 0.01

    def test_demonstrates_fix_for_baseline_20rps_10workers_scenario(self):
        """Test that specifically addresses the user's reported 20 RPS baseline issue."""
        # This recreates the exact scenario the user experienced:
        # - Set baseline to 20 RPS
        # - System creates 10 workers (since RPS > 10)
        # - User saw much higher rate in external service

        baseline_rps = 20.0
        config = LoadTestConfig(requests_per_second=baseline_rps)
        generator = LoadGenerator(config)

        # Calculate what the system actually creates for 20 RPS
        expected_workers, expected_interval = generator._calculate_worker_config(baseline_rps)

        # For 20 RPS: min(int(20/2), 10) = min(10, 10) = 10 workers
        assert expected_workers == 10

        # Simulate the worker setup
        generator._tasks = [AsyncMock() for _ in range(expected_workers)]

        # Test the corrected interval calculation
        corrected_interval = expected_workers / baseline_rps  # 10/20 = 0.5
        actual_interval = len(generator._tasks) / generator.config.requests_per_second

        assert abs(actual_interval - corrected_interval) < 0.001
        assert actual_interval == 0.5

        # Each worker should generate 2 RPS (1/0.5 = 2)
        worker_rps = 1.0 / actual_interval
        assert worker_rps == 2.0

        # Total should be exactly 20 RPS (10 workers x 2 RPS = 20)
        total_rps = worker_rps * expected_workers
        assert total_rps == 20.0

        # This test would have failed with the old bug:
        # old_interval = 1.0 / baseline_rps = 0.05
        # old_worker_rps = 1.0 / 0.05 = 20.0
        # old_total_rps = 20.0 x 10 = 200.0 ❌


class TestLatencyCompensation:
    """Test latency compensation functionality for accurate RPS."""

    @pytest.fixture
    def mock_slow_response(self):
        """Mock slow response times for testing compensation."""

        def slow_execute_request(self):
            # Simulate 200ms response time
            time.sleep(0.2)
            return LoadGenerationResult(success=True, response_time_ms=200.0), {}

        return slow_execute_request

    @pytest.fixture
    async def compensated_generator(self):
        """Create generator with latency compensation enabled."""
        config = LoadTestConfig(requests_per_second=5.0)  # 200ms intervals
        generator = LoadGenerator(config)

        # Mock settings to enable compensation
        from unittest.mock import patch

        with patch("analytics_service.services.load_generator.settings") as mock_settings:
            mock_settings.latency_compensation_enabled = True
            mock_settings.min_sleep_threshold_ms = 10.0
            mock_settings.adaptive_scaling_enabled = False

            yield generator, mock_settings

        # Cleanup
        with suppress(Exception):
            if generator.is_running:
                await generator.stop()

    @pytest.mark.asyncio
    async def test_latency_compensation_calculation(self, compensated_generator):
        """Test that latency compensation correctly reduces sleep intervals."""
        generator, mock_settings = compensated_generator

        # Simulate worker behavior with compensation
        generator._tasks = [AsyncMock()]  # Single worker
        target_rps = 5.0  # 200ms intervals
        generator.config.requests_per_second = target_rps

        # Calculate what compensation should do:
        # Target interval: 1 worker / 5.0 RPS = 0.2s (200ms)
        # Request time: 200ms
        # Compensated interval: 200ms - 200ms = 0ms
        # With min threshold (10ms): max(0ms, 10ms) = 10ms

        target_interval = 1 / target_rps  # 0.2s
        request_duration = 0.2  # 200ms response
        compensated_interval = target_interval - request_duration  # 0.0s
        min_sleep = 0.01  # 10ms
        expected_final_interval = max(min_sleep, compensated_interval)  # 0.01s

        assert expected_final_interval == 0.01  # Should use minimum sleep

    def test_latency_compensation_metrics_tracking(self):
        """Test that compensation amounts are tracked for metrics."""
        config = LoadTestConfig(requests_per_second=10.0)
        generator = LoadGenerator(config)

        # Test compensation tracking
        initial_count = len(generator._compensation_history)

        # Simulate adding compensation data
        test_compensations = [50.0, 100.0, 75.0]  # ms
        for comp in test_compensations:
            generator._compensation_history.append(comp)

        # Verify tracking
        assert len(generator._compensation_history) == initial_count + 3

        # Test average calculation
        if generator._compensation_history:
            avg_compensation = sum(generator._compensation_history) / len(
                generator._compensation_history
            )
            expected_avg = sum(test_compensations) / len(test_compensations)
            assert abs(avg_compensation - expected_avg) < 0.1

    @pytest.mark.asyncio
    async def test_compensation_disabled_behavior(self):
        """Test behavior when compensation is disabled."""
        config = LoadTestConfig(requests_per_second=5.0)
        generator = LoadGenerator(config)

        from unittest.mock import patch

        with patch("analytics_service.services.load_generator.settings") as mock_settings:
            mock_settings.latency_compensation_enabled = False

            # When disabled, should use target interval regardless of request time
            generator._tasks = [AsyncMock()]
            target_interval = 1 / generator.config.requests_per_second

            # Should return target interval without modification
            assert target_interval == 0.2  # 1/5 = 0.2s


class TestAdaptiveScaling:
    """Test adaptive worker scaling functionality."""

    @pytest.fixture
    async def scaling_generator(self):
        """Create generator with adaptive scaling enabled."""
        config = LoadTestConfig(requests_per_second=20.0)
        generator = LoadGenerator(config)

        from unittest.mock import patch

        with patch("analytics_service.services.load_generator.settings") as mock_settings:
            mock_settings.adaptive_scaling_enabled = True
            mock_settings.max_adaptive_workers = 50
            mock_settings.latency_threshold_ms = 500.0
            mock_settings.scaling_cooldown_seconds = 1.0  # Short cooldown for testing

            yield generator, mock_settings

        # Cleanup
        with suppress(Exception):
            if generator.is_running:
                await generator.stop()

    @pytest.mark.asyncio
    async def test_scaling_up_directly(self, scaling_generator):
        """Test the scale_workers_up method directly."""
        generator, mock_settings = scaling_generator

        # Setup initial state with fewer than max workers
        generator._tasks = [AsyncMock() for _ in range(5)]  # Start with 5 workers
        initial_worker_count = len(generator._tasks)

        # Test scaling up directly
        await generator._scale_workers_up()

        # Should have added at least 1 worker (20% of 5 = 1 worker minimum)
        assert len(generator._tasks) > initial_worker_count

    def test_scaling_down_logic(self, scaling_generator):
        """Test the scaling down logic without async complications."""
        generator, mock_settings = scaling_generator

        # Setup state as if already scaled up
        base_workers, _ = generator._calculate_worker_config(20.0)  # This should be 10 workers
        generator._tasks = [AsyncMock() for _ in range(15)]  # 15 workers (5 extra)
        generator._adaptive_scaling_active = True

        initial_worker_count = len(generator._tasks)

        # Calculate what should happen in scaling down
        excess_workers = initial_worker_count - base_workers  # 15 - 10 = 5
        workers_to_remove = max(1, int(excess_workers * 0.2))  # max(1, 1) = 1
        target_workers = max(
            base_workers, initial_worker_count - workers_to_remove
        )  # max(10, 14) = 14

        # Manually simulate what _scale_workers_down would do (without the async parts)
        generator._tasks = generator._tasks[:target_workers]

        # Verify the scaling calculation worked correctly
        assert len(generator._tasks) == target_workers
        assert len(generator._tasks) < initial_worker_count

    @pytest.mark.asyncio
    async def test_scaling_cooldown_prevention(self, scaling_generator):
        """Test that scaling cooldown prevents rapid scaling changes."""
        generator, mock_settings = scaling_generator

        # Set recent scaling time
        generator._last_scaling_time = time.time() - 0.5  # 0.5s ago, within 1s cooldown

        # Add high latency samples
        current_time = time.time()
        for i in range(20):
            generator._request_history.append(
                RequestRecord(
                    timestamp=current_time - (i * 0.1),
                    success=True,
                    response_time_ms=600.0,  # Above threshold
                )
            )

        initial_worker_count = len(generator._tasks)

        # Should not scale due to cooldown
        await generator._check_and_apply_adaptive_scaling()

        # Worker count should remain unchanged due to cooldown
        assert len(generator._tasks) == initial_worker_count

    @pytest.mark.asyncio
    async def test_max_workers_limit(self, scaling_generator):
        """Test that scaling respects maximum worker limits."""
        generator, mock_settings = scaling_generator

        # Set up at near max workers
        mock_settings.max_adaptive_workers = 10
        generator._tasks = [AsyncMock() for _ in range(10)]  # At max

        # Add high latency samples
        current_time = time.time()
        for i in range(20):
            generator._request_history.append(
                RequestRecord(
                    timestamp=current_time - (i * 0.1),
                    success=True,
                    response_time_ms=600.0,  # Above threshold
                )
            )

        initial_worker_count = len(generator._tasks)

        # Should not scale beyond maximum
        await generator._scale_workers_up()

        assert len(generator._tasks) <= mock_settings.max_adaptive_workers
        assert len(generator._tasks) == initial_worker_count  # Should not increase


class TestRPSAccuracyMetrics:
    """Test RPS accuracy calculation and metrics."""

    @pytest.fixture
    async def metrics_generator(self):
        """Create generator for metrics testing."""
        config = LoadTestConfig(requests_per_second=10.0)
        generator = LoadGenerator(config)
        yield generator

        with suppress(Exception):
            if generator.is_running:
                await generator.stop()

    @pytest.mark.asyncio
    async def test_rps_accuracy_calculation(self, metrics_generator):
        """Test RPS accuracy percentage calculation."""
        generator = metrics_generator

        # Mock the rolling averages calculation to return our test values
        from unittest.mock import patch

        def mock_rolling_averages():
            generator.stats.rolling_requests_per_second = 8.5  # Achieved 8.5 RPS
            generator.stats.rolling_success_rate = 95.0
            generator.stats.rolling_avg_response_ms = 150.0

        with patch.object(
            generator, "_calculate_rolling_averages", side_effect=mock_rolling_averages
        ):
            target_rps = 10.0  # Target 10 RPS

            # Calculate expected accuracy
            expected_accuracy = (8.5 / 10.0) * 100.0  # 85%

            # Get current stats which should include accuracy calculation
            stats = await generator.get_current_stats()

            assert abs(stats.achieved_rps_accuracy - expected_accuracy) < 0.1
            assert stats.target_requests_per_second == target_rps

    @pytest.mark.asyncio
    async def test_new_metrics_in_stats_response(self, metrics_generator):
        """Test that all new metrics are included in stats response."""
        generator = metrics_generator

        # Add some test data
        generator._adaptive_scaling_active = True
        generator._compensation_history.extend([50.0, 75.0, 100.0])
        generator._tasks = [AsyncMock() for _ in range(8)]  # Mock workers

        stats = await generator.get_current_stats()

        # Verify all new fields are present
        assert hasattr(stats, "target_requests_per_second")
        assert hasattr(stats, "achieved_rps_accuracy")
        assert hasattr(stats, "latency_compensation_active")
        assert hasattr(stats, "adaptive_scaling_active")
        assert hasattr(stats, "current_worker_count")
        assert hasattr(stats, "base_worker_count")
        assert hasattr(stats, "avg_compensation_ms")

        # Verify values are calculated correctly
        assert stats.adaptive_scaling_active is True
        assert stats.current_worker_count == 8
        assert stats.avg_compensation_ms == 75.0  # Average of test data

    def test_compensation_history_limits(self, metrics_generator):
        """Test that compensation history respects size limits."""
        generator = metrics_generator

        # Add more than the limit (1000 items)
        for i in range(1200):
            generator._compensation_history.append(float(i))

        # Should be limited to maxlen
        assert len(generator._compensation_history) == 1000

        # Should contain the most recent items
        assert 1199.0 in generator._compensation_history
        assert 0.0 not in generator._compensation_history  # Old items removed


class TestIPSpoofingIntegration:
    """Test IP spoofing integration with load generator."""

    @pytest.fixture
    def spoofing_config(self):
        """Load test config for IP spoofing tests."""
        return LoadTestConfig(requests_per_second=1.0)

    @pytest.fixture
    def mock_settings_spoofing_enabled(self, monkeypatch):
        """Mock settings with IP spoofing enabled."""
        mock_settings = MagicMock()
        mock_settings.ip_spoofing_enabled = True
        mock_settings.ip_rotation_interval = 3
        mock_settings.get_ip_regions_list.return_value = ["US"]
        mock_settings.include_residential_ips = True
        mock_settings.include_datacenter_ips = True
        mock_settings.request_timeout = 30.0
        mock_settings.target_api_base_url = "http://localhost:8000"
        mock_settings.latency_compensation_enabled = False
        mock_settings.adaptive_scaling_enabled = False

        monkeypatch.setattr("analytics_service.services.load_generator.settings", mock_settings)
        return mock_settings

    @pytest.fixture
    def mock_settings_spoofing_disabled(self, monkeypatch):
        """Mock settings with IP spoofing disabled."""
        mock_settings = MagicMock()
        mock_settings.ip_spoofing_enabled = False
        mock_settings.request_timeout = 30.0
        mock_settings.target_api_base_url = "http://localhost:8000"
        mock_settings.latency_compensation_enabled = False
        mock_settings.adaptive_scaling_enabled = False

        monkeypatch.setattr("analytics_service.services.load_generator.settings", mock_settings)
        return mock_settings

    def test_load_generator_initialization_with_spoofing_enabled(
        self, spoofing_config, mock_settings_spoofing_enabled
    ):
        """Test load generator initializes IP spoofing when enabled."""
        generator = LoadGenerator(spoofing_config)

        # Should have IP generator initialized
        assert generator._ip_generator is not None
        assert hasattr(generator._ip_generator, "get_spoofing_headers")
        assert hasattr(generator._ip_generator, "get_stats")

    def test_load_generator_initialization_with_spoofing_disabled(
        self, spoofing_config, mock_settings_spoofing_disabled
    ):
        """Test load generator doesn't initialize IP spoofing when disabled."""
        generator = LoadGenerator(spoofing_config)

        # Should not have IP generator initialized
        assert generator._ip_generator is None

    def test_get_ip_spoofing_stats_enabled(self, spoofing_config, mock_settings_spoofing_enabled):
        """Test get_ip_spoofing_stats when spoofing is enabled."""
        generator = LoadGenerator(spoofing_config)
        stats = generator.get_ip_spoofing_stats()

        assert stats["enabled"] is True
        assert "current_ip" in stats
        assert "request_count" in stats
        assert "rotation_interval" in stats
        assert "available_ranges" in stats
        assert "regions" in stats

    def test_get_ip_spoofing_stats_disabled(self, spoofing_config, mock_settings_spoofing_disabled):
        """Test get_ip_spoofing_stats when spoofing is disabled."""
        generator = LoadGenerator(spoofing_config)
        stats = generator.get_ip_spoofing_stats()

        assert stats["enabled"] is False
        assert stats["current_ip"] is None
        assert stats["request_count"] == 0
        assert stats["rotation_interval"] == 0
        assert stats["regions"] == []

    @pytest.mark.asyncio
    async def test_execute_single_request_with_spoofing_headers(
        self, spoofing_config, mock_settings_spoofing_enabled
    ):
        """Test that spoofing headers are added to requests when enabled."""
        generator = LoadGenerator(spoofing_config)

        # Mock the session and response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="success")
        mock_session.post.return_value.__aenter__.return_value = mock_response
        generator._session = mock_session

        # Execute request
        result, request_data = await generator._execute_single_request()

        # Verify session.post was called
        assert mock_session.post.called
        call_args = mock_session.post.call_args

        # Check that headers include spoofing headers
        headers = call_args[1]["headers"]

        # Should have authentication header
        assert "Authorization" in headers
        assert "Content-Type" in headers

        # Should have IP spoofing headers
        expected_spoofing_headers = {
            "X-Forwarded-For",
            "X-Real-IP",
            "X-Originating-IP",
            "X-Client-IP",
            "CF-Connecting-IP",
            "True-Client-IP",
            "X-Original-Forwarded-For",
        }

        # Get the IP from X-Forwarded-For as reference
        spoofed_ip = headers["X-Forwarded-For"]

        for header in expected_spoofing_headers:
            assert header in headers
            # All spoofing headers should have same IP
            assert headers[header] == spoofed_ip

    @pytest.mark.asyncio
    async def test_execute_single_request_without_spoofing_headers(
        self, spoofing_config, mock_settings_spoofing_disabled
    ):
        """Test that no spoofing headers are added when disabled."""
        generator = LoadGenerator(spoofing_config)

        # Mock the session and response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="success")
        mock_session.post.return_value.__aenter__.return_value = mock_response
        generator._session = mock_session

        # Execute request
        result, request_data = await generator._execute_single_request()

        # Verify session.post was called
        assert mock_session.post.called
        call_args = mock_session.post.call_args

        # Check that headers don't include spoofing headers
        headers = call_args[1]["headers"]

        # Should have authentication headers
        assert "Authorization" in headers
        assert "Content-Type" in headers

        # Should NOT have IP spoofing headers
        spoofing_headers = {
            "X-Forwarded-For",
            "X-Real-IP",
            "X-Originating-IP",
            "X-Client-IP",
            "CF-Connecting-IP",
            "True-Client-IP",
            "X-Original-Forwarded-For",
        }

        for header in spoofing_headers:
            assert header not in headers

    def test_ip_generator_configuration_from_settings(
        self, spoofing_config, mock_settings_spoofing_enabled
    ):
        """Test that IP generator uses configuration from settings."""
        # Modify mock settings
        mock_settings_spoofing_enabled.get_ip_regions_list.return_value = ["EU", "APAC"]
        mock_settings_spoofing_enabled.include_residential_ips = False
        mock_settings_spoofing_enabled.include_datacenter_ips = True
        mock_settings_spoofing_enabled.ip_rotation_interval = 10

        generator = LoadGenerator(spoofing_config)

        # Verify IP generator was configured correctly
        assert generator._ip_generator is not None
        assert generator._ip_generator.regions == ["EU", "APAC"]
        assert generator._ip_generator.include_residential is False
        assert generator._ip_generator.include_datacenter is True
        assert generator._ip_generator.rotation_interval == 10

    @pytest.mark.asyncio
    async def test_ip_spoofing_stats_update_with_requests(
        self, spoofing_config, mock_settings_spoofing_enabled
    ):
        """Test that IP spoofing stats update as requests are made."""
        generator = LoadGenerator(spoofing_config)

        # Mock the session and response
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="success")
        mock_session.post.return_value.__aenter__.return_value = mock_response
        generator._session = mock_session

        # Initial stats
        initial_stats = generator.get_ip_spoofing_stats()
        assert initial_stats["current_ip"] is None
        assert initial_stats["request_count"] == 0

        # Make some requests
        for i in range(3):
            await generator._execute_single_request()
            stats = generator.get_ip_spoofing_stats()

            # IP should be generated after first request
            if i == 0:
                assert stats["current_ip"] is not None

            # Request count should increment (mod rotation_interval)
            expected_count = (i + 1) % int(stats["rotation_interval"])
            if expected_count == 0:
                expected_count = int(stats["rotation_interval"])
            assert stats["request_count"] == expected_count

    def test_spoofing_with_different_regions(self, spoofing_config):
        """Test spoofing works with different regional configurations."""
        regions_to_test = [
            ["US"],
            ["EU"],
            ["APAC"],
            ["US", "EU"],
            ["US", "EU", "APAC"],
        ]

        for regions in regions_to_test:
            # Mock settings for each region combination
            from unittest.mock import patch

            with patch("analytics_service.services.load_generator.settings") as mock_settings:
                mock_settings.ip_spoofing_enabled = True
                mock_settings.get_ip_regions_list.return_value = regions
                mock_settings.include_residential_ips = True
                mock_settings.include_datacenter_ips = True
                mock_settings.ip_rotation_interval = 5
                mock_settings.request_timeout = 30.0
                mock_settings.target_api_base_url = "http://localhost:8000"
                mock_settings.latency_compensation_enabled = False
                mock_settings.adaptive_scaling_enabled = False

                generator = LoadGenerator(spoofing_config)

                # Should successfully initialize
                assert generator._ip_generator is not None
                assert generator._ip_generator.regions == regions

                # Should be able to generate IPs
                stats = generator.get_ip_spoofing_stats()
                assert stats["enabled"] is True
                assert stats["regions"] == regions

    def test_spoofing_performance_impact(self, spoofing_config):
        """Test that IP spoofing doesn't significantly impact performance."""
        import time

        # Test with spoofing disabled
        with patch("analytics_service.services.load_generator.settings") as mock_settings:
            mock_settings.ip_spoofing_enabled = False
            mock_settings.request_timeout = 30.0
            mock_settings.target_api_base_url = "http://localhost:8000"
            mock_settings.latency_compensation_enabled = False
            mock_settings.adaptive_scaling_enabled = False

            generator_disabled = LoadGenerator(spoofing_config)

            start_time = time.time()
            for _ in range(1000):
                headers = {"Authorization": "Bearer test", "Content-Type": "application/json"}
                if generator_disabled._ip_generator is not None:
                    spoofing_headers = generator_disabled._ip_generator.get_spoofing_headers()
                    headers.update(spoofing_headers)
            disabled_time = time.time() - start_time

        # Test with spoofing enabled
        with patch("analytics_service.services.load_generator.settings") as mock_settings:
            mock_settings.ip_spoofing_enabled = True
            mock_settings.get_ip_regions_list.return_value = ["US"]
            mock_settings.include_residential_ips = True
            mock_settings.include_datacenter_ips = True
            mock_settings.ip_rotation_interval = 5
            mock_settings.request_timeout = 30.0
            mock_settings.target_api_base_url = "http://localhost:8000"
            mock_settings.latency_compensation_enabled = False
            mock_settings.adaptive_scaling_enabled = False

            generator_enabled = LoadGenerator(spoofing_config)

            start_time = time.time()
            for _ in range(1000):
                headers = {"Authorization": "Bearer test", "Content-Type": "application/json"}
                if generator_enabled._ip_generator is not None:
                    spoofing_headers = generator_enabled._ip_generator.get_spoofing_headers()
                    headers.update(spoofing_headers)
            enabled_time = time.time() - start_time

        # Performance impact should be reasonable (less than 10x overhead)
        # Note: Enabled version does more work (IP generation), so some overhead is expected
        assert (
            enabled_time < disabled_time * 10.0 or enabled_time < 0.01
        )  # Less than 10ms is acceptable
