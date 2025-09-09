"""Tests for load test ramping functionality."""

import asyncio
from contextlib import suppress

import pytest

from load_tester.models.load_test import LoadTestConfig, LoadTestStatus
from load_tester.services.load_generator import LoadGenerator
from load_tester.services.load_test_manager import LoadTestManager


@pytest.fixture(autouse=True)
async def reset_load_test_manager():
    """Reset load test manager before each test."""
    # Clear singleton instance to ensure clean state
    LoadTestManager._instance = None
    yield
    # Clean up after test - ensure any running load tests are stopped
    if LoadTestManager._instance is not None:
        manager = LoadTestManager._instance
        with suppress(Exception):
            await manager.stop_load_test()  # type: ignore[misc]
    LoadTestManager._instance = None


class TestLoadGenerator:
    """Test load generator ramping functionality."""

    async def test_ramp_to_config_not_running(self):
        """Test ramping when generator is not running fails."""
        config = LoadTestConfig(
            requests_per_second=1.0, currency_pairs=["USD_EUR"], amounts=[100.0]
        )
        generator = LoadGenerator(config)

        new_config = LoadTestConfig(
            requests_per_second=2.0, currency_pairs=["USD_GBP"], amounts=[200.0]
        )

        with pytest.raises(RuntimeError, match="Cannot ramp load - generator is not running"):
            await generator.ramp_to_config(new_config)

    async def test_ramp_to_higher_rps(self):
        """Test ramping to higher RPS increases worker tasks."""
        config = LoadTestConfig(
            requests_per_second=5.0,
            currency_pairs=["USD_EUR"],
            amounts=[100.0],  # Will use 1 worker
        )
        generator = LoadGenerator(config)

        try:
            await generator.start()
            initial_task_count = len(generator._tasks)
            assert initial_task_count == 1  # Should start with 1 worker

            # Ramp to higher RPS that requires more workers
            new_config = LoadTestConfig(
                requests_per_second=30.0,  # Will use min(30/2, 10) = 10 workers
                currency_pairs=["USD_EUR", "USD_GBP"],
                amounts=[100.0, 200.0],
            )

            await generator.ramp_to_config(new_config)

            # Should have more tasks now
            assert len(generator._tasks) > initial_task_count
            assert len(generator._tasks) == 10  # Should have 10 workers
            assert generator.config.requests_per_second == 30.0
            assert generator.config.currency_pairs == ["USD_EUR", "USD_GBP"]
            assert generator.config.amounts == [100.0, 200.0]

        finally:
            await generator.stop()

    async def test_ramp_to_lower_rps(self):
        """Test ramping to lower RPS reduces worker tasks."""
        config = LoadTestConfig(
            requests_per_second=40.0,  # Will use min(40/2, 10) = 10 workers
            currency_pairs=["USD_EUR", "USD_GBP", "USD_JPY"],
            amounts=[100.0, 200.0, 300.0],
        )
        generator = LoadGenerator(config)

        try:
            await generator.start()
            initial_task_count = len(generator._tasks)
            assert initial_task_count == 10  # Should start with 10 workers

            # Ramp to lower RPS that uses fewer workers
            new_config = LoadTestConfig(
                requests_per_second=5.0,
                currency_pairs=["USD_EUR"],
                amounts=[100.0],  # Will use 1 worker
            )

            await generator.ramp_to_config(new_config)

            # Should have fewer tasks now
            assert len(generator._tasks) < initial_task_count
            assert len(generator._tasks) == 1  # Should have 1 worker now
            assert generator.config.requests_per_second == 5.0
            assert generator.config.currency_pairs == ["USD_EUR"]
            assert generator.config.amounts == [100.0]

        finally:
            await generator.stop()

    async def test_ramp_to_same_rps(self):
        """Test ramping to same RPS only updates config."""
        config = LoadTestConfig(
            requests_per_second=2.0, currency_pairs=["USD_EUR"], amounts=[100.0]
        )
        generator = LoadGenerator(config)

        try:
            await generator.start()
            initial_task_count = len(generator._tasks)

            # Ramp to same RPS but different config
            new_config = LoadTestConfig(
                requests_per_second=2.0,  # Same RPS
                currency_pairs=["USD_GBP", "USD_JPY"],  # Different pairs
                amounts=[200.0, 300.0],  # Different amounts
            )

            await generator.ramp_to_config(new_config)

            # Task count should be the same
            assert len(generator._tasks) == initial_task_count
            # But config should be updated
            assert generator.config.currency_pairs == ["USD_GBP", "USD_JPY"]
            assert generator.config.amounts == [200.0, 300.0]

        finally:
            await generator.stop()


class TestLoadTestManager:
    """Test load test manager ramping functionality."""

    async def test_ramp_to_config_not_running(self):
        """Test ramping when no test is running fails."""
        manager = LoadTestManager()

        config = LoadTestConfig(
            requests_per_second=2.0, currency_pairs=["USD_EUR"], amounts=[100.0]
        )

        with pytest.raises(RuntimeError, match="No load test is currently running to ramp"):
            await manager.ramp_to_config(config)

    async def test_ramp_to_config_success(self):
        """Test successful ramping to new configuration."""
        manager = LoadTestManager()

        # Start initial test
        initial_config = LoadTestConfig(
            requests_per_second=1.0, currency_pairs=["USD_EUR"], amounts=[100.0]
        )

        try:
            response = await manager.start_load_test(initial_config)
            assert response.status == LoadTestStatus.RUNNING

            # Ramp to new configuration
            new_config = LoadTestConfig(
                requests_per_second=3.0,
                currency_pairs=["USD_EUR", "USD_GBP"],
                amounts=[100.0, 200.0],
            )

            ramp_response = await manager.ramp_to_config(new_config)
            assert ramp_response.status == LoadTestStatus.RUNNING
            assert ramp_response.config == new_config

        finally:
            await manager.stop_load_test()

    async def test_ramp_to_config_generator_unavailable(self):
        """Test ramping when load generator is unavailable."""
        manager = LoadTestManager()

        # Manually set status to running but no generator
        manager._status = LoadTestStatus.RUNNING
        manager._config = LoadTestConfig(
            requests_per_second=1.0, currency_pairs=["USD_EUR"], amounts=[100.0]
        )
        manager._load_generator = None

        new_config = LoadTestConfig(
            requests_per_second=2.0, currency_pairs=["USD_GBP"], amounts=[200.0]
        )

        with pytest.raises(RuntimeError, match="Load generator not available for ramping"):
            await manager.ramp_to_config(new_config)

    async def test_ramp_to_config_generator_error(self):
        """Test ramping when generator ramping fails."""
        manager = LoadTestManager()

        # Start initial test
        initial_config = LoadTestConfig(
            requests_per_second=1.0, currency_pairs=["USD_EUR"], amounts=[100.0]
        )

        try:
            await manager.start_load_test(initial_config)

            # Stop the generator to cause ramp error
            if manager._load_generator:
                await manager._load_generator.stop()

            # Try to ramp - should catch error and set error message
            new_config = LoadTestConfig(
                requests_per_second=2.0, currency_pairs=["USD_GBP"], amounts=[200.0]
            )

            response = await manager.ramp_to_config(new_config)
            assert response.error_message is not None
            assert "Ramping failed" in response.error_message

        finally:
            await manager.stop_load_test()

    async def test_multiple_ramps_in_sequence(self):
        """Test multiple ramping operations in sequence."""
        manager = LoadTestManager()

        # Start initial test
        config1 = LoadTestConfig(
            requests_per_second=1.0, currency_pairs=["USD_EUR"], amounts=[100.0]
        )

        try:
            await manager.start_load_test(config1)

            # First ramp
            config2 = LoadTestConfig(
                requests_per_second=3.0,
                currency_pairs=["USD_EUR", "USD_GBP"],
                amounts=[100.0, 200.0],
            )
            response2 = await manager.ramp_to_config(config2)
            assert response2.config == config2

            # Second ramp
            config3 = LoadTestConfig(
                requests_per_second=0.5, currency_pairs=["USD_JPY"], amounts=[50.0]
            )
            response3 = await manager.ramp_to_config(config3)
            assert response3.config == config3
            assert response3.status == LoadTestStatus.RUNNING

        finally:
            await manager.stop_load_test()

    async def test_ramp_preserves_stats_and_timing(self):
        """Test ramping preserves existing stats and timing information."""
        manager = LoadTestManager()

        # Start initial test
        initial_config = LoadTestConfig(
            requests_per_second=1.0, currency_pairs=["USD_EUR"], amounts=[100.0]
        )

        try:
            start_response = await manager.start_load_test(initial_config)
            original_started_at = start_response.started_at

            # Allow some time for stats to accumulate
            await asyncio.sleep(0.1)

            # Ramp to new configuration
            new_config = LoadTestConfig(
                requests_per_second=2.0, currency_pairs=["USD_GBP"], amounts=[200.0]
            )

            ramp_response = await manager.ramp_to_config(new_config)

            # Started time should be preserved
            assert ramp_response.started_at == original_started_at
            # Status should still be running
            assert ramp_response.status == LoadTestStatus.RUNNING
            # Config should be updated
            assert ramp_response.config == new_config
            # Should not have stopped time
            assert ramp_response.stopped_at is None

        finally:
            await manager.stop_load_test()
