"""Tests for load test ramping API endpoints."""

from contextlib import suppress

import pytest
from fastapi.testclient import TestClient

from load_tester.main import app
from load_tester.models.load_test import LoadTestStatus
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


@pytest.fixture
def client():
    """Create test client for load tester."""
    with TestClient(app) as test_client:
        yield test_client


class TestRampingAPIEndpoints:
    """Test ramping API endpoints."""

    def test_start_endpoint_ramps_when_running(self, client):
        """Test that start endpoint ramps instead of failing when test is running."""
        # Start initial test
        initial_config = {
            "config": {
                "requests_per_second": 1.0,
                "currency_pairs": ["USD_EUR"],
                "amounts": [100.0],
            }
        }

        start_response = client.post("/api/load-test/start", json=initial_config)
        assert start_response.status_code == 200
        assert start_response.json()["status"] == LoadTestStatus.RUNNING

        # Try to start another test - should ramp instead of fail
        new_config = {
            "config": {
                "requests_per_second": 3.0,
                "currency_pairs": ["USD_EUR", "USD_GBP"],
                "amounts": [100.0, 200.0],
            }
        }

        ramp_response = client.post("/api/load-test/start", json=new_config)
        assert ramp_response.status_code == 200

        data = ramp_response.json()
        assert data["status"] == LoadTestStatus.RUNNING
        assert data["config"]["requests_per_second"] == 3.0
        assert data["config"]["currency_pairs"] == ["USD_EUR", "USD_GBP"]

    def test_scenario_start_endpoint_ramps_when_running(self, client):
        """Test that scenario start endpoint ramps instead of failing."""
        # Start initial scenario
        start_response = client.post("/api/load-test/scenarios/light/start")
        assert start_response.status_code == 200
        assert start_response.json()["status"] == LoadTestStatus.RUNNING

        # Try to start different scenario - should ramp instead of fail
        ramp_response = client.post("/api/load-test/scenarios/moderate/start")
        assert ramp_response.status_code == 200

        data = ramp_response.json()
        assert data["status"] == LoadTestStatus.RUNNING
        # Should have moderate scenario config (5.0 RPS)
        assert data["config"]["requests_per_second"] == 5.0

    def test_dedicated_ramp_endpoint(self, client):
        """Test the dedicated /ramp endpoint."""
        # Start initial test first
        initial_config = {
            "config": {
                "requests_per_second": 1.0,
                "currency_pairs": ["USD_EUR"],
                "amounts": [100.0],
            }
        }

        start_response = client.post("/api/load-test/start", json=initial_config)
        assert start_response.status_code == 200

        # Use dedicated ramp endpoint
        ramp_config = {
            "config": {
                "requests_per_second": 5.0,
                "currency_pairs": ["USD_EUR", "USD_GBP", "USD_JPY"],
                "amounts": [100.0, 250.0, 500.0],
            }
        }

        ramp_response = client.post("/api/load-test/ramp", json=ramp_config)
        assert ramp_response.status_code == 200

        data = ramp_response.json()
        assert data["status"] == LoadTestStatus.RUNNING
        assert data["config"]["requests_per_second"] == 5.0
        assert len(data["config"]["currency_pairs"]) == 3

    def test_ramp_endpoint_no_test_running(self, client):
        """Test ramp endpoint fails when no test is running."""
        ramp_config = {
            "config": {
                "requests_per_second": 2.0,
                "currency_pairs": ["USD_EUR"],
                "amounts": [100.0],
            }
        }

        response = client.post("/api/load-test/ramp", json=ramp_config)
        assert response.status_code == 409
        assert "No load test is currently running to ramp" in response.json()["detail"]

    def test_scenario_ramp_endpoint(self, client):
        """Test the dedicated scenario ramp endpoint."""
        # Start initial test
        initial_config = {
            "config": {
                "requests_per_second": 1.0,
                "currency_pairs": ["USD_EUR"],
                "amounts": [100.0],
            }
        }

        start_response = client.post("/api/load-test/start", json=initial_config)
        assert start_response.status_code == 200

        # Ramp to specific scenario
        ramp_response = client.post("/api/load-test/scenarios/heavy/ramp")
        assert ramp_response.status_code == 200

        data = ramp_response.json()
        assert data["status"] == LoadTestStatus.RUNNING
        # Should have heavy scenario config (15.0 RPS)
        assert data["config"]["requests_per_second"] == 15.0

    def test_scenario_ramp_endpoint_no_test_running(self, client):
        """Test scenario ramp endpoint fails when no test is running."""
        response = client.post("/api/load-test/scenarios/moderate/ramp")
        assert response.status_code == 409
        assert "No load test is currently running to ramp" in response.json()["detail"]

    def test_scenario_ramp_endpoint_invalid_scenario(self, client):
        """Test scenario ramp endpoint with invalid scenario."""
        # Start initial test
        initial_config = {
            "config": {
                "requests_per_second": 1.0,
                "currency_pairs": ["USD_EUR"],
                "amounts": [100.0],
            }
        }

        client.post("/api/load-test/start", json=initial_config)

        # Try to ramp to invalid scenario
        response = client.post("/api/load-test/scenarios/nonexistent/ramp")
        assert response.status_code == 422  # Validation error

    def test_ramping_preserves_test_session(self, client):
        """Test that ramping preserves the test session and statistics."""
        # Start initial test
        initial_config = {
            "config": {
                "requests_per_second": 1.0,
                "currency_pairs": ["USD_EUR"],
                "amounts": [100.0],
            }
        }

        start_response = client.post("/api/load-test/start", json=initial_config)
        original_started_at = start_response.json()["started_at"]

        # Ramp to new config
        ramp_config = {
            "config": {
                "requests_per_second": 3.0,
                "currency_pairs": ["USD_GBP"],
                "amounts": [200.0],
            }
        }

        ramp_response = client.post("/api/load-test/ramp", json=ramp_config)
        ramped_data = ramp_response.json()

        # Should preserve original start time
        assert ramped_data["started_at"] == original_started_at
        # Should still be running
        assert ramped_data["status"] == LoadTestStatus.RUNNING
        # Should have new configuration
        assert ramped_data["config"]["requests_per_second"] == 3.0

    def test_multiple_ramps_in_sequence(self, client):
        """Test multiple ramping operations in sequence."""
        # Start initial test
        start_response = client.post("/api/load-test/scenarios/light/start")
        assert start_response.status_code == 200
        assert start_response.json()["config"]["requests_per_second"] == 0.5

        # Ramp to moderate
        ramp1_response = client.post("/api/load-test/scenarios/moderate/ramp")
        assert ramp1_response.status_code == 200
        assert ramp1_response.json()["config"]["requests_per_second"] == 5.0

        # Ramp to heavy
        ramp2_response = client.post("/api/load-test/scenarios/heavy/ramp")
        assert ramp2_response.status_code == 200
        assert ramp2_response.json()["config"]["requests_per_second"] == 15.0

        # Ramp back to light
        ramp3_response = client.post("/api/load-test/scenarios/light/ramp")
        assert ramp3_response.status_code == 200
        assert ramp3_response.json()["config"]["requests_per_second"] == 0.5

    def test_ramping_updates_status_response(self, client):
        """Test that ramping updates are reflected in status endpoint."""
        # Start initial test
        client.post("/api/load-test/scenarios/light/start")

        # Get initial status
        status_response = client.get("/api/load-test/status")
        assert status_response.json()["config"]["requests_per_second"] == 0.5

        # Ramp to different scenario
        client.post("/api/load-test/scenarios/moderate/ramp")

        # Get updated status
        updated_status_response = client.get("/api/load-test/status")
        updated_data = updated_status_response.json()

        assert updated_data["config"]["requests_per_second"] == 5.0
        assert updated_data["status"] == LoadTestStatus.RUNNING

    def test_stop_after_ramping_works(self, client):
        """Test that stopping works correctly after ramping."""
        # Start and ramp
        client.post("/api/load-test/scenarios/light/start")
        client.post("/api/load-test/scenarios/heavy/ramp")

        # Verify it's running with ramped config
        status_response = client.get("/api/load-test/status")
        assert status_response.json()["config"]["requests_per_second"] == 15.0

        # Stop the test
        stop_response = client.post("/api/load-test/stop")
        assert stop_response.status_code == 200
        assert stop_response.json()["status"] == LoadTestStatus.STOPPED
