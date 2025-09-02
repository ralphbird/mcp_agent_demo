"""Tests for scenario validation and structure."""

from load_tester.models.load_test import LoadTestConfig
from load_tester.models.scenarios import (
    LOAD_TEST_SCENARIOS,
    LoadTestScenario,
    ScenarioConfig,
)


class TestScenarioValidation:
    """Test scenario validation and structure."""

    def test_all_scenarios_defined(self):
        """Test that all scenario enum values have configurations."""
        enum_values = {scenario.value for scenario in LoadTestScenario}
        config_keys = {scenario.value for scenario in LOAD_TEST_SCENARIOS}
        assert enum_values == config_keys, "All scenario enum values must have configurations"

    def test_scenario_configurations_structure(self):
        """Test that all scenario configurations have required fields."""
        for _scenario, config in LOAD_TEST_SCENARIOS.items():
            assert isinstance(config, ScenarioConfig)
            assert config.name
            assert config.description
            assert isinstance(config.config, LoadTestConfig)
            assert config.duration_seconds > 0
            assert config.expected_behavior

    def test_scenario_config_validation(self):
        """Test that scenario configurations pass LoadTestConfig validation."""
        for _scenario, config in LOAD_TEST_SCENARIOS.items():
            # Test that the config is valid by creating a new instance
            load_config = LoadTestConfig(**config.config.model_dump())
            assert load_config.requests_per_second > 0
            assert load_config.requests_per_second <= 100.0  # Max validation
            assert len(load_config.currency_pairs) > 0
            assert len(load_config.amounts) > 0

    def test_scenario_durations_are_reasonable(self):
        """Test that scenario durations are within reasonable bounds."""
        for _scenario, config in LOAD_TEST_SCENARIOS.items():
            # All durations should be at least 30 seconds
            assert config.duration_seconds >= 30
            # And no more than 2 hours (for practical testing)
            assert config.duration_seconds <= 7200
