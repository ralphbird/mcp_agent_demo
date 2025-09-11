"""Integration tests for Load Test Scenario and Reporting API endpoints."""

from contextlib import suppress

import pytest
from fastapi.testclient import TestClient

from analytics_service.main import app
from analytics_service.models.load_test import LoadTestStatus
from analytics_service.services.load_test_manager import LoadTestManager


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


class TestScenarioEndpoints:
    """Test scenario-related API endpoints."""

    def test_list_scenarios_endpoint(self, client):
        """Test listing available scenarios."""
        response = client.get("/api/load-test/scenarios")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "light" in data
        assert "moderate" in data
        assert "heavy" in data
        assert "stress" in data
        assert "spike" in data
        assert "endurance" in data

        # Check descriptions are meaningful
        for _scenario, description in data.items():
            assert isinstance(description, str)
            assert len(description) > 10

    def test_get_specific_scenario(self, client):
        """Test getting configuration for a specific scenario."""
        response = client.get("/api/load-test/scenarios/light")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Light Load Test"
        assert data["description"]
        assert data["config"]["requests_per_second"] == 0.5
        assert data["duration_seconds"] == 60
        assert data["expected_behavior"]

    def test_get_nonexistent_scenario(self, client):
        """Test getting configuration for nonexistent scenario."""
        response = client.get("/api/load-test/scenarios/nonexistent")
        assert response.status_code == 422  # Validation error for invalid enum

    def test_start_scenario_light(self, client):
        """Test starting light scenario."""
        response = client.post("/api/load-test/scenarios/light/start")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == LoadTestStatus.RUNNING
        assert data["config"]["requests_per_second"] == 0.5

    def test_start_scenario_moderate(self, client):
        """Test starting moderate scenario."""
        response = client.post("/api/load-test/scenarios/moderate/start")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == LoadTestStatus.RUNNING
        assert data["config"]["requests_per_second"] == 5.0
        assert len(data["config"]["currency_pairs"]) == 4

    def test_start_scenario_already_running(self, client):
        """Test starting scenario when another is already running ramps to new scenario."""
        # Start first scenario
        response = client.post("/api/load-test/scenarios/light/start")
        assert response.status_code == 200
        first_data = response.json()
        assert first_data["config"]["requests_per_second"] == 0.5

        # Try to start another scenario - should ramp instead of fail
        response = client.post("/api/load-test/scenarios/moderate/start")
        assert response.status_code == 200

        # Should have ramped to moderate scenario configuration
        second_data = response.json()
        assert second_data["status"] == LoadTestStatus.RUNNING
        assert second_data["config"]["requests_per_second"] == 5.0  # moderate scenario RPS

    def test_start_nonexistent_scenario(self, client):
        """Test starting nonexistent scenario."""
        response = client.post("/api/load-test/scenarios/nonexistent/start")
        assert response.status_code == 422  # Validation error

    def test_scenario_configurations_match_expected(self, client):
        """Test that all scenarios have expected configurations."""
        expected_scenarios = {
            "light": {"rps": 0.5, "duration": 60},
            "moderate": {"rps": 5.0, "duration": 120},
            "heavy": {"rps": 15.0, "duration": 300},
            "stress": {"rps": 25.0, "duration": 180},
            "spike": {"rps": 50.0, "duration": 30},
            "endurance": {"rps": 3.0, "duration": 1800},
        }

        for scenario_name, expected in expected_scenarios.items():
            response = client.get(f"/api/load-test/scenarios/{scenario_name}")
            assert response.status_code == 200

            data = response.json()
            assert data["config"]["requests_per_second"] == expected["rps"]
            assert data["duration_seconds"] == expected["duration"]


class TestReportingEndpoints:
    """Test reporting API endpoints."""

    def test_get_report_idle_status(self, client):
        """Test getting report when no test has run."""
        response = client.get("/api/load-test/report")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == LoadTestStatus.IDLE
        assert data["success_rate"] == 0.0
        assert data["avg_rps_achieved"] == 0.0
        assert data["performance_grade"] in ["A", "B", "C", "D", "F"]
        assert len(data["recommendations"]) > 0

    def test_get_report_markdown_format(self, client):
        """Test getting report in Markdown format."""
        response = client.get("/api/load-test/report/markdown")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"

        content = response.text
        assert "# Load Test Report" in content
        assert "## Test Summary" in content
        assert "## Performance Metrics" in content
        assert "## Recommendations" in content

    def test_get_scenario_report_light(self, client):
        """Test getting report for specific scenario."""
        response = client.get("/api/load-test/scenarios/light/report")
        assert response.status_code == 200

        data = response.json()
        assert data["scenario_name"] == "Light Load Test"
        assert data["status"] == LoadTestStatus.IDLE  # No test running

    def test_get_scenario_report_nonexistent(self, client):
        """Test getting report for nonexistent scenario."""
        response = client.get("/api/load-test/scenarios/nonexistent/report")
        assert response.status_code == 422  # Validation error

    def test_report_after_scenario_start(self, client):
        """Test getting report after starting a scenario."""
        # Start a scenario
        start_response = client.post("/api/load-test/scenarios/light/start")
        assert start_response.status_code == 200

        # Get scenario-specific report
        report_response = client.get("/api/load-test/scenarios/light/report")
        assert report_response.status_code == 200

        data = report_response.json()
        assert data["scenario_name"] == "Light Load Test"
        assert data["status"] == LoadTestStatus.RUNNING
        assert data["requests_per_second"] == 0.5

    def test_markdown_report_content_structure(self, client):
        """Test that Markdown report has proper structure."""
        response = client.get("/api/load-test/report/markdown")
        assert response.status_code == 200

        content = response.text
        lines = content.split("\n")

        # Check for required sections
        section_headers = [line for line in lines if line.startswith("## ")]
        expected_sections = [
            "Test Summary",
            "Test Configuration",
            "Execution Timeline",
            "Performance Metrics",
            "Recommendations",
        ]

        for expected_section in expected_sections:
            assert any(expected_section in header for header in section_headers)

    def test_report_includes_test_id(self, client):
        """Test that reports include test ID."""
        response = client.get("/api/load-test/report")
        assert response.status_code == 200

        data = response.json()
        assert "test_id" in data
        assert data["test_id"].startswith("test_")


class TestEndpointIntegration:
    """Test integration between different endpoints."""

    def test_root_endpoint_includes_new_endpoints(self, client):
        """Test that root endpoint includes all new endpoints."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        endpoints = data["endpoints"]

        # Check for scenario endpoints
        assert "scenarios" in endpoints
        assert "scenario_start" in endpoints
        assert "scenario_report" in endpoints

        # Check for reporting endpoints
        assert "report" in endpoints
        assert "report_markdown" in endpoints

    def test_scenario_workflow_complete(self, client):
        """Test complete scenario workflow: list -> get -> start -> report."""
        # 1. List scenarios
        scenarios_response = client.get("/api/load-test/scenarios")
        assert scenarios_response.status_code == 200
        scenarios = scenarios_response.json()
        assert "light" in scenarios

        # 2. Get specific scenario
        scenario_response = client.get("/api/load-test/scenarios/light")
        assert scenario_response.status_code == 200

        # 3. Start scenario
        start_response = client.post("/api/load-test/scenarios/light/start")
        assert start_response.status_code == 200
        assert start_response.json()["status"] == LoadTestStatus.RUNNING

        # 4. Get report
        report_response = client.get("/api/load-test/scenarios/light/report")
        assert report_response.status_code == 200
        report = report_response.json()
        assert report["scenario_name"] == "Light Load Test"
        assert report["status"] == LoadTestStatus.RUNNING
