"""Basic tests for concurrent load test API endpoints."""

import pytest
from fastapi.testclient import TestClient

from analytics_service.main import app


class TestConcurrentLoadTestAPIBasic:
    """Basic tests for concurrent load test API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def test_config(self):
        """Create a test configuration for API requests."""
        return {
            "config": {
                "requests_per_second": 2.0,
                "currency_pairs": ["USD_EUR"],
                "amounts": [100.0],
                "error_injection_enabled": False,
                "error_injection_rate": 0.05,
            }
        }

    def test_start_concurrent_load_test_basic(self, client, test_config):
        """Test starting a concurrent load test via API."""
        test_id = "api_test_basic"

        response = client.post(f"/api/load-test/concurrent/{test_id}/start", json=test_config)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["config"]["requests_per_second"] == 2.0

        # Clean up
        client.post(f"/api/load-test/concurrent/{test_id}/stop")

    def test_get_concurrent_load_test_status_basic(self, client, test_config):
        """Test getting status of a concurrent load test."""
        test_id = "api_test_status_basic"

        # Start test first
        start_response = client.post(f"/api/load-test/concurrent/{test_id}/start", json=test_config)
        assert start_response.status_code == 200

        # Get status
        status_response = client.get(f"/api/load-test/concurrent/{test_id}/status")
        assert status_response.status_code == 200

        data = status_response.json()
        assert data["status"] == "running"
        assert data["config"]["requests_per_second"] == 2.0

        # Clean up
        client.post(f"/api/load-test/concurrent/{test_id}/stop")

    def test_stop_concurrent_load_test_basic(self, client, test_config):
        """Test stopping a concurrent load test via API."""
        test_id = "api_test_stop_basic"

        # Start test first
        start_response = client.post(f"/api/load-test/concurrent/{test_id}/start", json=test_config)
        assert start_response.status_code == 200

        # Stop test
        stop_response = client.post(f"/api/load-test/concurrent/{test_id}/stop")
        assert stop_response.status_code == 200

        data = stop_response.json()
        assert data["status"] == "stopped"

    def test_get_active_concurrent_test_ids_basic(self, client, test_config):
        """Test getting list of active concurrent test IDs."""
        # Start a test
        test_id = "api_active_basic"
        start_response = client.post(f"/api/load-test/concurrent/{test_id}/start", json=test_config)
        assert start_response.status_code == 200

        # Get active IDs
        response = client.get("/api/load-test/concurrent/active")
        assert response.status_code == 200

        active_ids = response.json()
        assert isinstance(active_ids, list)
        assert test_id in active_ids

        # Clean up
        client.post(f"/api/load-test/concurrent/{test_id}/stop")
