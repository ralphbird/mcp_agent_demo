"""Unit tests for LoadTestManager service."""

from contextlib import suppress
from unittest.mock import AsyncMock, patch

import pytest

from analytics_service.models.load_test import LoadTestConfig, LoadTestStatus
from analytics_service.services.load_test_manager import LoadTestManager


class TestLoadTestManager:
    """Test LoadTestManager functionality."""

    @pytest.fixture(autouse=True)
    async def reset_manager(self):
        """Reset manager state before each test."""
        # Clear singleton instance to ensure clean state
        LoadTestManager._instance = None
        yield
        # Clean up after test - ensure any running load tests are stopped
        if LoadTestManager._instance is not None:
            manager = LoadTestManager._instance
            with suppress(Exception):
                await manager.stop_load_test()  # type: ignore[misc]
        LoadTestManager._instance = None

    def test_singleton_pattern(self):
        """Test LoadTestManager follows singleton pattern."""
        manager1 = LoadTestManager()
        manager2 = LoadTestManager()
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_initial_status(self):
        """Test manager starts in idle status."""
        manager = LoadTestManager()
        response = await manager.get_status()

        assert response.status == LoadTestStatus.IDLE
        assert response.config is None
        assert response.stats.total_requests == 0
        assert response.started_at is None
        assert response.stopped_at is None

    @pytest.mark.asyncio
    async def test_start_load_test_default_config(self):
        """Test starting load test with default configuration."""
        manager = LoadTestManager()
        config = LoadTestConfig()

        # Mock LoadGenerator to avoid actual HTTP requests
        with patch(
            "analytics_service.services.load_test_manager.LoadGenerator"
        ) as mock_load_gen_class:
            mock_load_gen = AsyncMock()
            mock_load_gen_class.return_value = mock_load_gen

            response = await manager.start_load_test(config)

            assert response.status == LoadTestStatus.RUNNING
            assert response.config == config
            assert response.started_at is not None
            assert response.stopped_at is None

            # Verify LoadGenerator was created and started
            mock_load_gen_class.assert_called_once_with(config)
            mock_load_gen.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_load_test_custom_config(self):
        """Test starting load test with custom configuration."""
        manager = LoadTestManager()
        config = LoadTestConfig(
            requests_per_second=5.0,
            currency_pairs=["USD_EUR"],
            amounts=[100.0],
        )

        # Mock LoadGenerator to avoid actual HTTP requests
        with patch(
            "analytics_service.services.load_test_manager.LoadGenerator"
        ) as mock_load_gen_class:
            mock_load_gen = AsyncMock()
            mock_load_gen_class.return_value = mock_load_gen

            response = await manager.start_load_test(config)

            assert response.status == LoadTestStatus.RUNNING
            assert response.config is not None
            assert response.config.requests_per_second == 5.0
            assert response.config.currency_pairs == ["USD_EUR"]
            assert response.config.amounts == [100.0]

    @pytest.mark.asyncio
    async def test_start_load_test_already_running(self):
        """Test starting load test when already running raises error."""
        manager = LoadTestManager()
        config = LoadTestConfig()

        # Mock LoadGenerator to avoid actual HTTP requests
        with patch(
            "analytics_service.services.load_test_manager.LoadGenerator"
        ) as mock_load_gen_class:
            mock_load_gen = AsyncMock()
            mock_load_gen_class.return_value = mock_load_gen

            # Start first load test
            await manager.start_load_test(config)

            # Try to start another one
            with pytest.raises(RuntimeError, match="Load test is already running"):
                await manager.start_load_test(config)

    @pytest.mark.asyncio
    async def test_stop_load_test(self):
        """Test stopping a running load test."""
        manager = LoadTestManager()
        config = LoadTestConfig()

        # Start load test
        start_response = await manager.start_load_test(config)
        assert start_response.status == LoadTestStatus.RUNNING

        # Stop load test
        stop_response = await manager.stop_load_test()
        assert stop_response.status == LoadTestStatus.STOPPED
        assert stop_response.started_at is not None
        assert stop_response.stopped_at is not None
        assert stop_response.stopped_at > stop_response.started_at

    @pytest.mark.asyncio
    async def test_stop_load_test_not_running(self):
        """Test stopping load test when not running."""
        manager = LoadTestManager()

        response = await manager.stop_load_test()
        assert response.status == LoadTestStatus.IDLE

    @pytest.mark.asyncio
    async def test_get_status_during_execution(self):
        """Test getting status while load test is running."""
        manager = LoadTestManager()
        config = LoadTestConfig()

        # Start load test
        start_response = await manager.start_load_test(config)

        # Get status
        status_response = await manager.get_status()
        assert status_response.status == LoadTestStatus.RUNNING
        assert status_response.config == config
        assert status_response.started_at == start_response.started_at

    @pytest.mark.asyncio
    async def test_restart_after_stop(self):
        """Test starting load test after stopping previous one."""
        manager = LoadTestManager()
        config1 = LoadTestConfig(requests_per_second=1.0)
        config2 = LoadTestConfig(requests_per_second=2.0)

        # Start first load test
        await manager.start_load_test(config1)

        # Stop it
        await manager.stop_load_test()

        # Start second load test
        response = await manager.start_load_test(config2)
        assert response.status == LoadTestStatus.RUNNING
        assert response.config is not None
        assert response.config.requests_per_second == 2.0

    @pytest.mark.asyncio
    async def test_stats_initialization(self):
        """Test stats are properly initialized."""
        manager = LoadTestManager()
        config = LoadTestConfig()

        response = await manager.start_load_test(config)
        stats = response.stats

        assert stats.total_requests == 0
        assert stats.successful_requests == 0
        assert stats.failed_requests == 0
        assert stats.avg_response_time_ms == 0.0
        assert stats.min_response_time_ms == 0.0
        assert stats.max_response_time_ms == 0.0
        assert stats.requests_per_second == 0.0
