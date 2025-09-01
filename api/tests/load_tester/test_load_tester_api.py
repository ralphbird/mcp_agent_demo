"""Integration tests for Load Tester API endpoints."""

import pytest
from fastapi.testclient import TestClient
from load_tester.main import app
from load_tester.models.load_test import LoadTestStatus
from load_tester.services.load_test_manager import LoadTestManager


@pytest.fixture(autouse=True)
def reset_load_test_manager():
    """Reset load test manager before each test."""
    # Clear singleton instance to ensure clean state
    LoadTestManager._instance = None
    yield
    # Clean up after test
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
        """Test starting load test when already running returns 409."""
        # Start first load test
        response = client.post("/api/load-test/start", json={})
        assert response.status_code == 200

        # Try to start another one
        response = client.post("/api/load-test/start", json={})
        assert response.status_code == 409
        assert "Load test is already running" in response.json()["detail"]

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
