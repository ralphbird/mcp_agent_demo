"""Integration tests for Load Tester API endpoints."""

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


class TestLoadTesterEndpoints:
    """Test load tester control endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Currency API Load Tester"
        assert data["version"] == "0.1.0"
        assert "docs" in data
        assert "endpoints" in data
        assert "start" in data["endpoints"]
        assert "stop" in data["endpoints"]
        assert "status" in data["endpoints"]

    def test_get_status_initial(self, client):
        """Test status endpoint returns idle status initially."""
        response = client.get("/api/load-test/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == LoadTestStatus.IDLE
        assert data["config"] is None
        assert data["stats"]["total_requests"] == 0
        assert data["started_at"] is None
        assert data["stopped_at"] is None

    def test_start_load_test_default_config(self, client):
        """Test starting load test with default configuration."""
        response = client.post("/api/load-test/start", json={})
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == LoadTestStatus.RUNNING
        assert data["config"] is not None
        assert data["config"]["requests_per_second"] == 1.0
        assert data["started_at"] is not None
        assert data["stopped_at"] is None

    def test_start_load_test_custom_config(self, client):
        """Test starting load test with custom configuration."""
        config = {
            "config": {
                "requests_per_second": 5.0,
                "currency_pairs": ["USD_EUR", "GBP_USD"],
                "amounts": [100.0, 500.0],
            }
        }

        response = client.post("/api/load-test/start", json=config)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == LoadTestStatus.RUNNING
        assert data["config"]["requests_per_second"] == 5.0
        assert data["config"]["currency_pairs"] == ["USD_EUR", "GBP_USD"]
        assert data["config"]["amounts"] == [100.0, 500.0]

    def test_start_load_test_already_running(self, client):
        """Test starting load test when already running ramps to new config."""
        # Start first load test
        response = client.post("/api/load-test/start", json={})
        assert response.status_code == 200
        original_config = response.json()["config"]

        # Try to start another one with different config - should ramp instead of fail
        new_config_request = {
            "config": {
                "requests_per_second": 5.0,
                "currency_pairs": ["USD_EUR", "USD_GBP"],
                "amounts": [100.0, 200.0],
            }
        }
        response = client.post("/api/load-test/start", json=new_config_request)
        assert response.status_code == 200

        # Should have ramped to new configuration
        new_data = response.json()
        assert new_data["status"] == "running"
        assert new_data["config"]["requests_per_second"] == 5.0
        assert new_data["config"] != original_config

    def test_stop_load_test(self, client):
        """Test stopping a running load test."""
        # Start load test first
        response = client.post("/api/load-test/start", json={})
        assert response.status_code == 200

        # Stop the load test
        response = client.post("/api/load-test/stop")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == LoadTestStatus.STOPPED
        assert data["started_at"] is not None
        assert data["stopped_at"] is not None

    def test_stop_load_test_not_running(self, client):
        """Test stopping load test when not running returns current status."""
        response = client.post("/api/load-test/stop")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == LoadTestStatus.IDLE

    def test_get_status_during_execution(self, client):
        """Test getting status while load test is running."""
        # Start load test
        start_response = client.post("/api/load-test/start", json={})
        assert start_response.status_code == 200

        # Get status
        status_response = client.get("/api/load-test/status")
        assert status_response.status_code == 200

        data = status_response.json()
        assert data["status"] == LoadTestStatus.RUNNING
        assert data["config"] is not None
        assert data["started_at"] is not None

    def test_start_stop_start_sequence(self, client):
        """Test starting, stopping, and starting again."""
        # First start
        response = client.post("/api/load-test/start", json={})
        assert response.status_code == 200
        assert response.json()["status"] == LoadTestStatus.RUNNING

        # Stop
        response = client.post("/api/load-test/stop")
        assert response.status_code == 200
        assert response.json()["status"] == LoadTestStatus.STOPPED

        # Start again
        response = client.post("/api/load-test/start", json={})
        assert response.status_code == 200
        assert response.json()["status"] == LoadTestStatus.RUNNING

    def test_invalid_config_validation(self, client):
        """Test validation of invalid configuration values."""
        # Test negative requests per second
        config = {
            "config": {
                "requests_per_second": -1.0,
            }
        }

        response = client.post("/api/load-test/start", json=config)
        assert response.status_code == 422

        # Test requests per second too high
        config = {
            "config": {
                "requests_per_second": 101.0,
            }
        }

        response = client.post("/api/load-test/start", json=config)
        assert response.status_code == 422

    def test_start_simple_load_test_default(self, client):
        """Test starting simple load test with default configuration."""
        response = client.post("/api/load-test/start/simple?requests_per_second=2.0")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == LoadTestStatus.RUNNING
        assert data["config"] is not None
        assert data["config"]["requests_per_second"] == 2.0
        assert data["started_at"] is not None
        assert data["stopped_at"] is None

        # Should auto-configure with all currency pairs and amounts
        assert len(data["config"]["currency_pairs"]) > 0
        assert len(data["config"]["amounts"]) > 0

        # Should include major currency pairs
        pairs = data["config"]["currency_pairs"]
        expected_major_pairs = ["USD_EUR", "EUR_USD", "USD_GBP", "GBP_USD"]
        for pair in expected_major_pairs:
            assert pair in pairs, f"Expected major pair {pair} not found in auto-configured pairs"

    def test_start_simple_load_test_custom_rps(self, client):
        """Test starting simple load test with custom RPS."""
        custom_rps = 5.5
        response = client.post(f"/api/load-test/start/simple?requests_per_second={custom_rps}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == LoadTestStatus.RUNNING
        assert data["config"]["requests_per_second"] == custom_rps

        # Should still auto-configure pairs and amounts
        assert len(data["config"]["currency_pairs"]) > 0
        assert len(data["config"]["amounts"]) > 0

    def test_start_simple_load_test_invalid_rps_low(self, client):
        """Test starting simple load test with RPS too low."""
        response = client.post("/api/load-test/start/simple?requests_per_second=0.05")
        assert response.status_code == 422

        error_detail = response.json()["detail"]
        assert "must be between 0.1 and 100.0" in error_detail

    def test_start_simple_load_test_invalid_rps_high(self, client):
        """Test starting simple load test with RPS too high."""
        response = client.post("/api/load-test/start/simple?requests_per_second=150.0")
        assert response.status_code == 422

        error_detail = response.json()["detail"]
        assert "must be between 0.1 and 100.0" in error_detail

    def test_start_simple_load_test_boundary_values(self, client):
        """Test starting simple load test with boundary RPS values."""
        # Test minimum valid value
        response = client.post("/api/load-test/start/simple?requests_per_second=0.1")
        assert response.status_code == 200
        assert response.json()["config"]["requests_per_second"] == 0.1

        # Stop current test
        client.post("/api/load-test/stop")

        # Test maximum valid value
        response = client.post("/api/load-test/start/simple?requests_per_second=100.0")
        assert response.status_code == 200
        assert response.json()["config"]["requests_per_second"] == 100.0

    def test_start_simple_already_running_ramps_instead(self, client):
        """Test that starting simple load test when already running ramps instead."""
        # Start first simple load test
        response = client.post("/api/load-test/start/simple?requests_per_second=2.0")
        assert response.status_code == 200
        original_rps = response.json()["config"]["requests_per_second"]
        assert original_rps == 2.0

        # Try to start another with different RPS - should ramp instead of fail
        response = client.post("/api/load-test/start/simple?requests_per_second=8.0")
        assert response.status_code == 200

        # Should have ramped to new RPS
        new_data = response.json()
        assert new_data["status"] == "running"
        assert new_data["config"]["requests_per_second"] == 8.0

        # Should still have auto-configured pairs and amounts
        assert len(new_data["config"]["currency_pairs"]) > 0
        assert len(new_data["config"]["amounts"]) > 0

    def test_start_simple_comprehensive_auto_configuration(self, client):
        """Test that simple load test provides comprehensive auto-configuration."""
        response = client.post("/api/load-test/start/simple?requests_per_second=3.0")
        assert response.status_code == 200

        data = response.json()
        config = data["config"]

        # Should have comprehensive currency pair coverage
        pairs = config["currency_pairs"]
        assert len(pairs) >= 20, "Should have at least 20 currency pairs for comprehensive testing"

        # Should include both directions for major pairs
        assert "USD_EUR" in pairs and "EUR_USD" in pairs
        assert "USD_GBP" in pairs and "GBP_USD" in pairs
        assert "EUR_GBP" in pairs and "GBP_EUR" in pairs

        # Should have diverse amount ranges
        amounts = config["amounts"]
        assert len(amounts) >= 15, "Should have at least 15 different amounts"

        # Should include small, medium, and large amounts
        assert any(amt < 1000 for amt in amounts), "Should include small amounts"
        assert any(1000 <= amt <= 10000 for amt in amounts), "Should include medium amounts"
        assert any(amt > 10000 for amt in amounts), "Should include large amounts"

        # Amounts should be sorted
        assert amounts == sorted(amounts), "Amounts should be sorted"

    def test_start_simple_matches_create_full_config(self, client):
        """Test that simple endpoint matches LoadTestConfig.create_full_config behavior."""
        from load_tester.models.load_test import LoadTestConfig

        # Get config from simple endpoint
        response = client.post("/api/load-test/start/simple?requests_per_second=4.0")
        assert response.status_code == 200
        api_config = response.json()["config"]

        # Get config from create_full_config method
        model_config = LoadTestConfig.create_full_config(requests_per_second=4.0)

        # Should match exactly
        assert api_config["requests_per_second"] == model_config.requests_per_second
        assert api_config["currency_pairs"] == model_config.currency_pairs
        assert api_config["amounts"] == model_config.amounts
