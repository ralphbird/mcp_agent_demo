"""Load test scenario definitions and presets."""

from enum import Enum

from pydantic import BaseModel, Field

from load_tester.models.load_test import LoadTestConfig


class LoadTestScenario(str, Enum):
    """Predefined load test scenarios."""

    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    STRESS = "stress"
    SPIKE = "spike"
    ENDURANCE = "endurance"


class ScenarioConfig(BaseModel):
    """Configuration for a load test scenario."""

    name: str = Field(description="Scenario name")
    description: str = Field(description="Scenario description")
    config: LoadTestConfig = Field(description="Load test configuration")
    duration_seconds: int = Field(description="Recommended test duration in seconds")
    expected_behavior: str = Field(description="Expected system behavior under this load")


# Predefined load test scenarios
LOAD_TEST_SCENARIOS: dict[LoadTestScenario, ScenarioConfig] = {
    LoadTestScenario.LIGHT: ScenarioConfig(
        name="Light Load Test",
        description="Baseline load test with minimal traffic to verify basic functionality",
        config=LoadTestConfig(
            requests_per_second=0.5,
            currency_pairs=["USD_EUR", "USD_GBP"],
            amounts=[100.0, 500.0],
        ),
        duration_seconds=60,
        expected_behavior="System should handle easily with minimal resource usage",
    ),
    LoadTestScenario.MODERATE: ScenarioConfig(
        name="Moderate Load Test",
        description="Typical production load to verify normal operation capacity",
        config=LoadTestConfig(
            requests_per_second=5.0,
            currency_pairs=["USD_EUR", "USD_GBP", "EUR_GBP", "USD_JPY"],
            amounts=[100.0, 500.0, 1000.0, 2500.0],
        ),
        duration_seconds=120,
        expected_behavior="System should perform normally with good response times",
    ),
    LoadTestScenario.HEAVY: ScenarioConfig(
        name="Heavy Load Test",
        description="High traffic load to test system limits and performance degradation",
        config=LoadTestConfig(
            requests_per_second=15.0,
            currency_pairs=["USD_EUR", "USD_GBP", "EUR_GBP", "USD_JPY", "USD_CAD"],
            amounts=[100.0, 250.0, 500.0, 1000.0, 2500.0],
        ),
        duration_seconds=300,
        expected_behavior="System may show increased response times but should remain stable",
    ),
    LoadTestScenario.STRESS: ScenarioConfig(
        name="Stress Test",
        description="Maximum sustainable load to find breaking point and failure modes",
        config=LoadTestConfig(
            requests_per_second=25.0,
            currency_pairs=[
                "USD_EUR",
                "USD_GBP",
                "EUR_GBP",
                "USD_JPY",
                "USD_CAD",
                "USD_AUD",
                "USD_CHF",
                "USD_CNY",
                "USD_SEK",
                "USD_NZD",
            ],
            amounts=[100.0, 250.0, 500.0, 1000.0, 2500.0],
        ),
        duration_seconds=180,
        expected_behavior="System will likely show performance degradation and may fail",
    ),
    LoadTestScenario.SPIKE: ScenarioConfig(
        name="Spike Test",
        description="Sudden traffic spike to test system elasticity and recovery",
        config=LoadTestConfig(
            requests_per_second=50.0,
            currency_pairs=["USD_EUR", "USD_GBP", "EUR_GBP"],
            amounts=[100.0, 1000.0],
        ),
        duration_seconds=30,
        expected_behavior="System should handle short bursts or gracefully degrade",
    ),
    LoadTestScenario.ENDURANCE: ScenarioConfig(
        name="Endurance Test",
        description="Extended moderate load to test system stability over time",
        config=LoadTestConfig(
            requests_per_second=3.0,
            currency_pairs=["USD_EUR", "USD_GBP", "EUR_GBP", "USD_JPY"],
            amounts=[100.0, 500.0, 1000.0],
        ),
        duration_seconds=1800,  # 30 minutes
        expected_behavior="System should maintain consistent performance over extended periods",
    ),
}


def get_scenario_config(scenario: LoadTestScenario) -> ScenarioConfig:
    """Get configuration for a specific load test scenario.

    Args:
        scenario: The load test scenario

    Returns:
        Scenario configuration

    Raises:
        KeyError: If scenario is not found
    """
    return LOAD_TEST_SCENARIOS[scenario]


def list_available_scenarios() -> dict[str, str]:
    """List all available load test scenarios.

    Returns:
        Dictionary mapping scenario names to descriptions
    """
    return {scenario.value: config.description for scenario, config in LOAD_TEST_SCENARIOS.items()}
