"""Tests for IP spoofing configuration validation."""

import pytest
from pydantic import ValidationError

from analytics_service.config import LoadTesterSettings


class TestIPSpoofingConfiguration:
    """Test IP spoofing configuration validation."""

    def test_default_configuration(self):
        """Test default IP spoofing configuration."""
        # Create settings without loading .env file to test actual defaults
        from pydantic_settings import SettingsConfigDict

        # Create temporary settings class with no .env file loading
        class TestLoadTesterSettings(LoadTesterSettings):
            model_config = SettingsConfigDict(
                env_file=None,  # Don't load .env file
                env_file_encoding="utf-8",
                case_sensitive=False,
                extra="ignore",
                env_prefix="ANALYTICS_SERVICE_",
            )

        # Clear environment to test actual defaults
        import os

        env_backup = {}
        env_keys = [k for k in os.environ if k.startswith("ANALYTICS_SERVICE_")]
        for key in env_keys:
            env_backup[key] = os.environ.pop(key)

        try:
            settings = TestLoadTesterSettings()

            assert settings.ip_spoofing_enabled is False
            assert settings.ip_rotation_interval == 5
            assert settings.ip_geographic_regions == "US,EU,APAC"
            assert settings.include_datacenter_ips is True
            assert settings.include_residential_ips is True
        finally:
            # Restore environment
            for key, value in env_backup.items():
                os.environ[key] = value

    def test_enable_ip_spoofing(self):
        """Test enabling IP spoofing."""
        settings = LoadTesterSettings(ip_spoofing_enabled=True)

        assert settings.ip_spoofing_enabled is True

    def test_custom_rotation_interval(self):
        """Test custom rotation interval."""
        settings = LoadTesterSettings(ip_rotation_interval=10)

        assert settings.ip_rotation_interval == 10

    def test_custom_geographic_regions_single(self):
        """Test custom geographic regions - single region."""
        settings = LoadTesterSettings(ip_geographic_regions="US")

        assert settings.ip_geographic_regions == "US"
        assert settings.get_ip_regions_list() == ["US"]

    def test_custom_geographic_regions_multiple(self):
        """Test custom geographic regions - multiple regions."""
        settings = LoadTesterSettings(ip_geographic_regions="US,EU")

        assert settings.ip_geographic_regions == "US,EU"
        assert settings.get_ip_regions_list() == ["US", "EU"]

    def test_geographic_regions_case_insensitive(self):
        """Test geographic regions are case insensitive."""
        settings = LoadTesterSettings(ip_geographic_regions="us,eu,apac")

        # Should be normalized to uppercase
        assert settings.ip_geographic_regions == "US,EU,APAC"
        assert settings.get_ip_regions_list() == ["US", "EU", "APAC"]

    def test_geographic_regions_with_spaces(self):
        """Test geographic regions with spaces are handled."""
        settings = LoadTesterSettings(ip_geographic_regions=" US , EU , APAC ")

        # Spaces should be stripped
        assert settings.ip_geographic_regions == "US,EU,APAC"
        assert settings.get_ip_regions_list() == ["US", "EU", "APAC"]

    def test_disable_datacenter_ips(self):
        """Test disabling datacenter IPs."""
        settings = LoadTesterSettings(include_datacenter_ips=False)

        assert settings.include_datacenter_ips is False

    def test_disable_residential_ips(self):
        """Test disabling residential IPs."""
        settings = LoadTesterSettings(include_residential_ips=False)

        assert settings.include_residential_ips is False

    def test_complete_ip_spoofing_config(self):
        """Test complete IP spoofing configuration."""
        settings = LoadTesterSettings(
            ip_spoofing_enabled=True,
            ip_rotation_interval=15,
            ip_geographic_regions="EU,APAC",
            include_datacenter_ips=True,
            include_residential_ips=False,
        )

        assert settings.ip_spoofing_enabled is True
        assert settings.ip_rotation_interval == 15
        assert settings.ip_geographic_regions == "EU,APAC"
        assert settings.get_ip_regions_list() == ["EU", "APAC"]
        assert settings.include_datacenter_ips is True
        assert settings.include_residential_ips is False


class TestIPSpoofingConfigurationValidation:
    """Test IP spoofing configuration validation errors."""

    def test_invalid_rotation_interval_zero(self):
        """Test invalid rotation interval - zero."""
        with pytest.raises(ValidationError) as exc_info:
            LoadTesterSettings(ip_rotation_interval=0)

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("ip_rotation_interval",)
        assert "IP rotation interval must be positive" in error["msg"]

    def test_invalid_rotation_interval_negative(self):
        """Test invalid rotation interval - negative."""
        with pytest.raises(ValidationError) as exc_info:
            LoadTesterSettings(ip_rotation_interval=-5)

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("ip_rotation_interval",)
        assert "IP rotation interval must be positive" in error["msg"]

    def test_invalid_geographic_region_single(self):
        """Test invalid geographic region - single invalid."""
        with pytest.raises(ValidationError) as exc_info:
            LoadTesterSettings(ip_geographic_regions="INVALID")

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("ip_geographic_regions",)
        assert "Invalid region 'INVALID'" in error["msg"]
        assert "Must be one of:" in error["msg"]
        assert "US" in error["msg"] and "EU" in error["msg"] and "APAC" in error["msg"]

    def test_invalid_geographic_region_mixed(self):
        """Test invalid geographic region - mixed valid/invalid."""
        with pytest.raises(ValidationError) as exc_info:
            LoadTesterSettings(ip_geographic_regions="US,INVALID,EU")

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("ip_geographic_regions",)
        assert "Invalid region 'INVALID'" in error["msg"]

    def test_invalid_geographic_region_multiple_invalid(self):
        """Test invalid geographic region - multiple invalid."""
        with pytest.raises(ValidationError) as exc_info:
            LoadTesterSettings(ip_geographic_regions="INVALID1,INVALID2")

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("ip_geographic_regions",)
        # Should catch the first invalid region
        assert "Invalid region 'INVALID1'" in error["msg"]

    def test_empty_geographic_regions(self):
        """Test empty geographic regions."""
        with pytest.raises(ValidationError) as exc_info:
            LoadTesterSettings(ip_geographic_regions="")

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("ip_geographic_regions",)
        assert "At least one geographic region must be specified" in error["msg"]

    def test_geographic_regions_only_whitespace(self):
        """Test geographic regions with only whitespace."""
        with pytest.raises(ValidationError) as exc_info:
            LoadTesterSettings(ip_geographic_regions="   ")

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("ip_geographic_regions",)
        # Whitespace gets stripped and becomes empty string, which is invalid region
        assert (
            "Invalid region" in error["msg"]
            or "At least one geographic region must be specified" in error["msg"]
        )

    def test_geographic_regions_empty_after_split(self):
        """Test geographic regions that become empty after splitting."""
        with pytest.raises(ValidationError) as exc_info:
            LoadTesterSettings(ip_geographic_regions=",,,")

        error = exc_info.value.errors()[0]
        assert error["loc"] == ("ip_geographic_regions",)
        # Empty strings after split are treated as invalid regions
        assert (
            "Invalid region" in error["msg"]
            or "At least one geographic region must be specified" in error["msg"]
        )


class TestIPSpoofingEnvironmentVariables:
    """Test IP spoofing configuration from environment variables."""

    def test_environment_variable_names(self):
        """Test that environment variables use correct prefix."""
        import os

        # Set environment variables
        env_vars = {
            "ANALYTICS_SERVICE_IP_SPOOFING_ENABLED": "true",
            "ANALYTICS_SERVICE_IP_ROTATION_INTERVAL": "7",
            "ANALYTICS_SERVICE_IP_GEOGRAPHIC_REGIONS": "US,EU",
            "ANALYTICS_SERVICE_INCLUDE_DATACENTER_IPS": "false",
            "ANALYTICS_SERVICE_INCLUDE_RESIDENTIAL_IPS": "true",
        }

        # Save original values
        original_values = {}
        for key in env_vars:
            original_values[key] = os.environ.get(key)
            os.environ[key] = env_vars[key]

        try:
            # Create settings (should read from environment)
            settings = LoadTesterSettings()

            assert settings.ip_spoofing_enabled is True
            assert settings.ip_rotation_interval == 7
            assert settings.ip_geographic_regions == "US,EU"
            assert settings.include_datacenter_ips is False
            assert settings.include_residential_ips is True

        finally:
            # Restore original environment
            for key, original_value in original_values.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value

    def test_boolean_environment_variables(self):
        """Test boolean environment variables parsing."""
        import os

        boolean_test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
        ]

        for env_value, expected in boolean_test_cases:
            # Save original
            original = os.environ.get("ANALYTICS_SERVICE_IP_SPOOFING_ENABLED")
            os.environ["ANALYTICS_SERVICE_IP_SPOOFING_ENABLED"] = env_value

            try:
                settings = LoadTesterSettings()
                assert settings.ip_spoofing_enabled is expected, (
                    f"Failed for env_value: {env_value}"
                )
            finally:
                # Restore
                if original is None:
                    os.environ.pop("ANALYTICS_SERVICE_IP_SPOOFING_ENABLED", None)
                else:
                    os.environ["ANALYTICS_SERVICE_IP_SPOOFING_ENABLED"] = original


class TestGetIPRegionsList:
    """Test the get_ip_regions_list helper method."""

    def test_get_ip_regions_list_single(self):
        """Test get_ip_regions_list with single region."""
        settings = LoadTesterSettings(ip_geographic_regions="US")

        regions = settings.get_ip_regions_list()
        assert regions == ["US"]

    def test_get_ip_regions_list_multiple(self):
        """Test get_ip_regions_list with multiple regions."""
        settings = LoadTesterSettings(ip_geographic_regions="US,EU,APAC")

        regions = settings.get_ip_regions_list()
        assert regions == ["US", "EU", "APAC"]

    def test_get_ip_regions_list_with_spaces(self):
        """Test get_ip_regions_list handles spaces correctly."""
        settings = LoadTesterSettings(ip_geographic_regions=" US , EU ")

        regions = settings.get_ip_regions_list()
        assert regions == ["US", "EU"]

    def test_get_ip_regions_list_empty_handling(self):
        """Test get_ip_regions_list handles empty strings in list."""
        # This should not happen due to validation, but test defensive coding
        settings = LoadTesterSettings()

        # Manually set to test edge case (bypassing validation)
        settings.ip_geographic_regions = "US,,EU,"

        regions = settings.get_ip_regions_list()
        # Should filter out empty strings
        assert regions == ["US", "EU"]

    def test_get_ip_regions_list_consistency(self):
        """Test that get_ip_regions_list is consistent with stored value."""
        test_regions = "EU,APAC"
        settings = LoadTesterSettings(ip_geographic_regions=test_regions)

        # Should be consistent between stored value and parsed list
        stored_regions = settings.ip_geographic_regions.split(",")
        parsed_regions = settings.get_ip_regions_list()

        assert stored_regions == parsed_regions


class TestIPSpoofingConfigurationEdgeCases:
    """Test edge cases for IP spoofing configuration."""

    def test_very_large_rotation_interval(self):
        """Test very large rotation interval."""
        settings = LoadTesterSettings(ip_rotation_interval=1000000)

        assert settings.ip_rotation_interval == 1000000

    def test_minimum_valid_rotation_interval(self):
        """Test minimum valid rotation interval."""
        settings = LoadTesterSettings(ip_rotation_interval=1)

        assert settings.ip_rotation_interval == 1

    def test_all_ip_types_disabled_config_allowed(self):
        """Test that configuration allows disabling all IP types."""
        # This should be allowed at config level (IP generator will handle fallback)
        settings = LoadTesterSettings(
            include_datacenter_ips=False,
            include_residential_ips=False,
        )

        assert settings.include_datacenter_ips is False
        assert settings.include_residential_ips is False

    def test_duplicate_regions_handling(self):
        """Test handling of duplicate regions."""
        # Duplicate regions should be normalized (deduplicated) rather than error
        settings = LoadTesterSettings(ip_geographic_regions="US,US,EU")

        # Should normalize to unique regions
        regions = settings.get_ip_regions_list()
        assert "US" in regions
        assert "EU" in regions
        # Should not have duplicates
        assert len([r for r in regions if r == "US"]) == 1

    def test_case_mixed_regions(self):
        """Test mixed case regions are normalized."""
        settings = LoadTesterSettings(ip_geographic_regions="Us,eU,aPaC")

        assert settings.ip_geographic_regions == "US,EU,APAC"
        assert settings.get_ip_regions_list() == ["US", "EU", "APAC"]

    def test_configuration_immutability(self):
        """Test that configuration values can't be accidentally modified."""
        settings = LoadTesterSettings()
        original_regions = settings.ip_geographic_regions

        # Get the list
        regions_list = settings.get_ip_regions_list()

        # Modify the returned list
        regions_list.append("INVALID")

        # Original should be unchanged
        assert settings.ip_geographic_regions == original_regions

        # Getting list again should return original
        new_list = settings.get_ip_regions_list()
        assert "INVALID" not in new_list
