"""Tests for scenario metadata and descriptions."""

from load_tester.models.scenarios import LOAD_TEST_SCENARIOS


class TestScenarioMetadata:
    """Test scenario metadata and descriptions."""

    def test_scenario_descriptions_are_informative(self):
        """Test that all scenarios have meaningful descriptions."""
        for _scenario, config in LOAD_TEST_SCENARIOS.items():
            # Description should be at least 20 characters
            assert len(config.description) >= 20
            # Should contain relevant keywords
            description_lower = config.description.lower()
            assert any(
                word in description_lower
                for word in ["load", "test", "traffic", "performance", "system", "capacity"]
            )

    def test_scenario_expected_behaviors_are_defined(self):
        """Test that all scenarios have expected behavior descriptions."""
        for _scenario, config in LOAD_TEST_SCENARIOS.items():
            # Expected behavior should be defined
            assert config.expected_behavior
            assert len(config.expected_behavior) >= 15
            # Should contain system or performance related terms
            behavior_lower = config.expected_behavior.lower()
            assert any(
                word in behavior_lower
                for word in ["system", "performance", "response", "handle", "stable", "degrade"]
            )

    def test_scenario_names_are_descriptive(self):
        """Test that scenario names are descriptive."""
        expected_names = {
            "light": "Light Load Test",
            "moderate": "Moderate Load Test",
            "heavy": "Heavy Load Test",
            "stress": "Stress Test",
            "spike": "Spike Test",
            "endurance": "Endurance Test",
        }

        for scenario, config in LOAD_TEST_SCENARIOS.items():
            assert config.name == expected_names[scenario.value]
