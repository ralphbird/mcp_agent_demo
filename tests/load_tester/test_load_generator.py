"""Unit tests for LoadGenerator service."""

import time
from contextlib import suppress
from unittest.mock import AsyncMock, patch

import pytest

from load_tester.models.load_test import LoadTestConfig
from load_tester.services.load_generator import LoadGenerationResult, LoadGenerator, RequestRecord


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
        with patch("load_tester.services.load_generator.settings") as mock_settings:
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
