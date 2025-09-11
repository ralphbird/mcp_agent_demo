"""Basic tests for ConcurrentLoadTestManager functionality."""

import pytest

from analytics_service.models.load_test import LoadTestConfig, LoadTestStatus
from analytics_service.services.concurrent_load_test_manager import ConcurrentLoadTestManager


class TestConcurrentLoadTestManagerBasic:
    """Basic tests for ConcurrentLoadTestManager functionality."""

    @pytest.fixture
    def manager(self):
        """Create a test concurrent load test manager."""
        return ConcurrentLoadTestManager()

    @pytest.fixture
    def test_config(self):
        """Create a test load test configuration."""
        return LoadTestConfig(
            requests_per_second=1.0,
            currency_pairs=["USD_EUR"],
            amounts=[100.0],
        )

    @pytest.mark.asyncio
    async def test_start_single_load_test(self, manager, test_config):
        """Test starting a single load test through manager."""
        test_id = "test_single_start"

        response = await manager.start_load_test(test_id, test_config)

        assert response.status == LoadTestStatus.RUNNING
        assert response.config == test_config
        assert test_id in manager._load_tests

        # Clean up
        await manager.stop_load_test(test_id)

    @pytest.mark.asyncio
    async def test_stop_load_test(self, manager, test_config):
        """Test stopping a load test through manager."""
        test_id = "test_single_stop"

        # Start test
        await manager.start_load_test(test_id, test_config)
        assert test_id in manager._load_tests

        # Stop test
        response = await manager.stop_load_test(test_id)
        assert response.status == LoadTestStatus.STOPPED

    @pytest.mark.asyncio
    async def test_get_load_test_status(self, manager, test_config):
        """Test getting status of a specific load test."""
        test_id = "test_status"

        # Start test
        await manager.start_load_test(test_id, test_config)

        # Get status
        response = await manager.get_load_test_status(test_id)
        assert response.status == LoadTestStatus.RUNNING
        assert response.config == test_config

        # Clean up
        await manager.stop_load_test(test_id)

    @pytest.mark.asyncio
    async def test_get_active_test_ids(self, manager, test_config):
        """Test getting active test IDs."""
        # Initially empty
        active_ids = manager.get_active_test_ids()
        assert active_ids == []

        # Start a test
        test_id = "test_active"
        await manager.start_load_test(test_id, test_config)

        # Check active IDs
        active_ids = manager.get_active_test_ids()
        assert test_id in active_ids

        # Clean up
        await manager.stop_load_test(test_id)
