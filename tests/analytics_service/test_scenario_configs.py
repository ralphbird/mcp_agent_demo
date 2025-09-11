"""Tests for individual load test scenario configurations."""

from analytics_service.models.scenarios import LOAD_TEST_SCENARIOS, LoadTestScenario


class TestScenarioConfigurations:
    """Test individual scenario configurations."""

    def test_light_scenario_configuration(self):
        """Test light scenario has appropriate configuration."""
        config = LOAD_TEST_SCENARIOS[LoadTestScenario.LIGHT]
        assert config.name == "Light Load Test"
        assert config.config.requests_per_second == 0.5
        assert config.duration_seconds == 60
        assert len(config.config.currency_pairs) == 2
        assert len(config.config.amounts) == 2

    def test_moderate_scenario_configuration(self):
        """Test moderate scenario has appropriate configuration."""
        config = LOAD_TEST_SCENARIOS[LoadTestScenario.MODERATE]
        assert config.name == "Moderate Load Test"
        assert config.config.requests_per_second == 5.0
        assert config.duration_seconds == 120
        assert len(config.config.currency_pairs) == 4
        assert len(config.config.amounts) == 4

    def test_heavy_scenario_configuration(self):
        """Test heavy scenario has appropriate configuration."""
        config = LOAD_TEST_SCENARIOS[LoadTestScenario.HEAVY]
        assert config.name == "Heavy Load Test"
        assert config.config.requests_per_second == 15.0
        assert config.duration_seconds == 300
        assert len(config.config.currency_pairs) == 5
        assert len(config.config.amounts) == 5

    def test_stress_scenario_configuration(self):
        """Test stress scenario has maximum configuration."""
        config = LOAD_TEST_SCENARIOS[LoadTestScenario.STRESS]
        assert config.name == "Stress Test"
        assert config.config.requests_per_second == 25.0
        assert config.duration_seconds == 180
        assert len(config.config.currency_pairs) == 10  # All supported pairs
        assert len(config.config.amounts) == 5

    def test_spike_scenario_configuration(self):
        """Test spike scenario has high RPS, short duration."""
        config = LOAD_TEST_SCENARIOS[LoadTestScenario.SPIKE]
        assert config.name == "Spike Test"
        assert config.config.requests_per_second == 50.0
        assert config.duration_seconds == 30  # Short burst
        assert len(config.config.currency_pairs) == 3
        assert len(config.config.amounts) == 2

    def test_endurance_scenario_configuration(self):
        """Test endurance scenario has long duration."""
        config = LOAD_TEST_SCENARIOS[LoadTestScenario.ENDURANCE]
        assert config.name == "Endurance Test"
        assert config.config.requests_per_second == 3.0
        assert config.duration_seconds == 1800  # 30 minutes
        assert len(config.config.currency_pairs) == 4
        assert len(config.config.amounts) == 3

    def test_scenario_rps_progression(self):
        """Test that scenarios have progressive RPS values."""
        rps_values = {
            LoadTestScenario.LIGHT: 0.5,
            LoadTestScenario.MODERATE: 5.0,
            LoadTestScenario.HEAVY: 15.0,
            LoadTestScenario.STRESS: 25.0,
            LoadTestScenario.SPIKE: 50.0,
        }

        for scenario, expected_rps in rps_values.items():
            config = LOAD_TEST_SCENARIOS[scenario]
            assert config.config.requests_per_second == expected_rps
