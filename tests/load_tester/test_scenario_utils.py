"""Tests for scenario utility functions."""

from load_tester.models.scenarios import (
    LoadTestScenario,
    ScenarioConfig,
    get_scenario_config,
    list_available_scenarios,
)


class TestScenarioUtilities:
    """Test scenario utility functions."""

    def test_get_scenario_config_success(self):
        """Test getting scenario configuration successfully."""
        config = get_scenario_config(LoadTestScenario.LIGHT)
        assert isinstance(config, ScenarioConfig)
        assert config.name == "Light Load Test"

    def test_get_scenario_config_all_scenarios(self):
        """Test getting configuration for all scenarios."""
        for scenario in LoadTestScenario:
            config = get_scenario_config(scenario)
            assert isinstance(config, ScenarioConfig)
            assert config.name
            assert config.description

    def test_list_available_scenarios(self):
        """Test listing all available scenarios."""
        scenarios = list_available_scenarios()
        assert isinstance(scenarios, dict)
        assert len(scenarios) == len(LoadTestScenario)

        # Check all scenarios are included
        for scenario in LoadTestScenario:
            assert scenario.value in scenarios
            assert isinstance(scenarios[scenario.value], str)
            assert len(scenarios[scenario.value]) > 0

    def test_list_available_scenarios_content(self):
        """Test that scenario list contains proper descriptions."""
        scenarios = list_available_scenarios()

        # Check specific scenarios
        assert "light" in scenarios
        assert "baseline" in scenarios["light"].lower() or "minimal" in scenarios["light"].lower()

        assert "moderate" in scenarios
        assert (
            "production" in scenarios["moderate"].lower()
            or "typical" in scenarios["moderate"].lower()
        )

        assert "stress" in scenarios
        assert "maximum" in scenarios["stress"].lower() or "breaking" in scenarios["stress"].lower()
