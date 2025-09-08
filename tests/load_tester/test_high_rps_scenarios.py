"""Tests for high RPS load test scenarios (attack simulation)."""

import pytest
from fastapi.testclient import TestClient

from load_tester.main import app
from load_tester.models.load_test import LoadTestConfig


class TestHighRPSScenarios:
    """Test high RPS scenarios for DDoS attack simulation."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_high_rps_load_test_config_validation(self):
        """Test that high RPS configurations are accepted."""
        # Test various high RPS values that should be valid
        high_rps_values = [100.0, 250.0, 500.0, 750.0, 1000.0]

        for rps in high_rps_values:
            config = LoadTestConfig(requests_per_second=rps)
            assert config.requests_per_second == rps

    def test_high_rps_boundary_validation(self):
        """Test RPS boundary validation for attack scenarios."""
        # Valid high RPS values
        config = LoadTestConfig(requests_per_second=999.9)
        assert config.requests_per_second == 999.9

        config = LoadTestConfig(requests_per_second=1000.0)
        assert config.requests_per_second == 1000.0

        # Invalid - over limit
        with pytest.raises(ValueError):
            LoadTestConfig(requests_per_second=1000.1)

        with pytest.raises(ValueError):
            LoadTestConfig(requests_per_second=1500.0)

    def test_start_high_rps_attack_simulation(self, client):
        """Test starting high RPS load test for attack simulation."""
        attack_config = {
            "config": {
                "requests_per_second": 500.0,  # High RPS for attack simulation
                "currency_pairs": ["USD_EUR", "EUR_USD"],
                "amounts": [100.0, 1000.0],
                "error_injection_enabled": False,
            }
        }

        response = client.post("/api/load-test/start", json=attack_config)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "running"
        assert data["config"]["requests_per_second"] == 500.0

        # Clean up
        client.post("/api/load-test/stop")

    def test_concurrent_high_rps_attack_simulation(self, client):
        """Test starting high RPS concurrent load test."""
        test_id = "ddos_attack_simulation"

        attack_config = {
            "config": {
                "requests_per_second": 300.0,
                "currency_pairs": ["USD_EUR"],
                "amounts": [100.0],
                "error_injection_enabled": False,
            }
        }

        response = client.post(f"/api/load-test/concurrent/{test_id}/start", json=attack_config)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "running"
        assert data["config"]["requests_per_second"] == 300.0

        # Clean up
        client.post(f"/api/load-test/concurrent/{test_id}/stop")

    def test_multiple_concurrent_attack_scenarios(self, client):
        """Test running multiple concurrent high RPS tests (baseline + attack)."""
        # Baseline traffic configuration
        baseline_config = {
            "config": {
                "requests_per_second": 10.0,
                "currency_pairs": ["USD_EUR"],
                "amounts": [100.0],
            }
        }

        # Attack traffic configuration
        attack_config = {
            "config": {
                "requests_per_second": 200.0,
                "currency_pairs": ["USD_EUR"],
                "amounts": [100.0],
            }
        }

        # Start baseline traffic
        baseline_response = client.post(
            "/api/load-test/concurrent/baseline_users/start", json=baseline_config
        )
        assert baseline_response.status_code == 200

        # Start attack traffic
        attack_response = client.post(
            "/api/load-test/concurrent/attack_user/start", json=attack_config
        )
        assert attack_response.status_code == 200

        # Verify both are running
        status_response = client.get("/api/load-test/concurrent/status")
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert "baseline_users" in status_data
        assert "attack_user" in status_data
        assert status_data["baseline_users"]["status"] == "running"
        assert status_data["attack_user"]["status"] == "running"

        # Clean up
        client.post("/api/load-test/concurrent/baseline_users/stop")
        client.post("/api/load-test/concurrent/attack_user/stop")

    def test_high_rps_simple_api_endpoint(self, client):
        """Test simple API endpoint with high RPS."""
        response = client.post("/api/load-test/start/simple?requests_per_second=800.0")
        assert response.status_code == 200

        data = response.json()
        assert data["config"]["requests_per_second"] == 800.0
        assert data["status"] == "running"

        # Clean up
        client.post("/api/load-test/stop")

    def test_attack_scenario_with_error_injection(self, client):
        """Test attack scenario with error injection for realistic traffic."""
        attack_config = {
            "config": {
                "requests_per_second": 400.0,
                "currency_pairs": ["USD_EUR", "GBP_USD"],
                "amounts": [100.0, 500.0, 1000.0],
                "error_injection_enabled": True,
                "error_injection_rate": 0.15,  # 15% error rate
            }
        }

        response = client.post(
            "/api/load-test/concurrent/attack_with_errors/start", json=attack_config
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "running"
        assert data["config"]["requests_per_second"] == 400.0
        assert data["config"]["error_injection_enabled"] is True
        assert data["config"]["error_injection_rate"] == 0.15

        # Clean up
        client.post("/api/load-test/concurrent/attack_with_errors/stop")
