"""Tests for IP generator service functionality."""

import ipaddress
import re
from ipaddress import IPv4Address

from analytics_service.services.ip_generator import IPGenerator


class TestIPGenerator:
    """Test IP generator basic functionality."""

    def test_initialization_default(self):
        """Test default initialization."""
        generator = IPGenerator()

        assert generator.regions == ["US", "EU", "APAC"]
        assert generator.include_residential is True
        assert generator.include_datacenter is True
        assert generator.rotation_interval == 5
        assert generator._current_ip is None
        assert generator._request_count == 0
        assert len(generator._available_ranges) > 0

    def test_initialization_custom(self):
        """Test custom initialization parameters."""
        generator = IPGenerator(
            regions=["US"],
            include_residential=False,
            include_datacenter=True,
            rotation_interval=10,
        )

        assert generator.regions == ["US"]
        assert generator.include_residential is False
        assert generator.include_datacenter is True
        assert generator.rotation_interval == 10

    def test_initialization_invalid_region(self):
        """Test initialization with invalid region."""
        # Should not crash, but invalid regions should be ignored
        generator = IPGenerator(regions=["INVALID", "US"])

        # Should only build ranges for valid regions
        assert len(generator._available_ranges) > 0

    def test_get_next_ip_generates_valid_ip(self):
        """Test that get_next_ip returns valid IP addresses."""
        generator = IPGenerator(regions=["US"], rotation_interval=1)

        for _ in range(10):
            ip = generator.get_next_ip()

            # Verify it's a valid IP address
            assert re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)

            # Verify it can be parsed as IPv4Address
            ipv4_addr = IPv4Address(ip)
            assert ipv4_addr.is_global or ipv4_addr.is_private

    def test_ip_rotation_interval(self):
        """Test that IP rotation happens at specified intervals."""
        generator = IPGenerator(regions=["US"], rotation_interval=3)

        # First 3 requests should return same IP
        ip1 = generator.get_next_ip()
        ip2 = generator.get_next_ip()
        ip3 = generator.get_next_ip()

        assert ip1 == ip2 == ip3

        # 4th request should generate new IP
        ip4 = generator.get_next_ip()

        # Should be different (very high probability with large IP space)
        assert ip4 != ip1

    def test_ip_rotation_immediate(self):
        """Test that IP rotation with interval=1 changes every time."""
        generator = IPGenerator(regions=["US"], rotation_interval=1)

        ips = set()
        for _ in range(10):
            ip = generator.get_next_ip()
            ips.add(ip)

        # Should have generated multiple unique IPs (high probability)
        assert len(ips) >= 5  # Allow some duplicates due to randomness

    def test_get_spoofing_headers_structure(self):
        """Test that spoofing headers have correct structure."""
        generator = IPGenerator(regions=["US"])
        headers = generator.get_spoofing_headers()

        expected_headers = {
            "X-Forwarded-For",
            "X-Real-IP",
            "X-Originating-IP",
            "X-Client-IP",
            "CF-Connecting-IP",
            "True-Client-IP",
            "X-Original-Forwarded-For",
        }

        assert set(headers.keys()) == expected_headers

        # All headers should have the same IP value
        ip_values = set(headers.values())
        assert len(ip_values) == 1

        # Verify the IP is valid
        ip = next(iter(ip_values))
        IPv4Address(ip)  # Should not raise exception

    def test_get_spoofing_headers_rotation(self):
        """Test that spoofing headers rotate IPs correctly."""
        generator = IPGenerator(regions=["US"], rotation_interval=2)

        # First set of headers
        headers1 = generator.get_spoofing_headers()
        headers2 = generator.get_spoofing_headers()

        # Should be same IP (within rotation interval)
        assert headers1["X-Forwarded-For"] == headers2["X-Forwarded-For"]

        # Third request should rotate
        headers3 = generator.get_spoofing_headers()

        # Should be different IP (high probability)
        assert headers3["X-Forwarded-For"] != headers1["X-Forwarded-For"]

    def test_reset_rotation(self):
        """Test reset_rotation forces new IP on next request."""
        generator = IPGenerator(regions=["US"], rotation_interval=10)

        ip1 = generator.get_next_ip()
        ip2 = generator.get_next_ip()

        # Should be same (within interval)
        assert ip1 == ip2

        # Reset rotation
        generator.reset_rotation()

        # Next request should generate new IP
        ip3 = generator.get_next_ip()
        assert ip3 != ip1

    def test_get_current_ip(self):
        """Test get_current_ip method."""
        generator = IPGenerator(regions=["US"])

        # Initially should be None
        assert generator.get_current_ip() is None

        # After generating IP, should return current IP
        ip = generator.get_next_ip()
        assert generator.get_current_ip() == ip

    def test_get_stats(self):
        """Test get_stats method returns correct information."""
        generator = IPGenerator(regions=["US", "EU"], rotation_interval=3)

        stats = generator.get_stats()

        assert "current_ip" in stats
        assert "request_count" in stats
        assert "rotation_interval" in stats
        assert "available_ranges" in stats
        assert "regions" in stats

        assert stats["rotation_interval"] == 3
        assert stats["regions"] == ["US", "EU"]
        assert stats["request_count"] == 0
        assert isinstance(stats["available_ranges"], int) and stats["available_ranges"] > 0

    def test_stats_updates_with_usage(self):
        """Test that stats update correctly as generator is used."""
        generator = IPGenerator(regions=["US"], rotation_interval=5)

        # Generate some IPs
        for i in range(3):
            generator.get_next_ip()
            stats = generator.get_stats()

            assert stats["request_count"] == (i + 1) % 5
            if i == 0:
                assert stats["current_ip"] is not None


class TestIPGeneratorRegionalDistribution:
    """Test IP generator regional distribution functionality."""

    def test_us_only_regions(self):
        """Test generator with US region only."""
        generator = IPGenerator(regions=["US"], rotation_interval=1)

        # Generate multiple IPs and verify they're from expected ranges
        ips = set()
        for _ in range(20):
            ip = generator.get_next_ip()
            ips.add(ip)

        # Verify we get variety in IPs (with rotation_interval=1, should get many unique)
        assert len(ips) >= 5

    def test_eu_only_regions(self):
        """Test generator with EU region only."""
        generator = IPGenerator(regions=["EU"])

        # Should generate valid IPs
        for _ in range(5):
            ip = generator.get_next_ip()
            IPv4Address(ip)  # Should not raise exception

    def test_apac_only_regions(self):
        """Test generator with APAC region only."""
        generator = IPGenerator(regions=["APAC"])

        # Should generate valid IPs
        for _ in range(5):
            ip = generator.get_next_ip()
            IPv4Address(ip)  # Should not raise exception

    def test_multiple_regions(self):
        """Test generator with multiple regions."""
        generator = IPGenerator(regions=["US", "EU", "APAC"])

        # Should have more available ranges
        stats = generator.get_stats()
        assert isinstance(stats["available_ranges"], int) and stats["available_ranges"] > 1000

    def test_residential_only(self):
        """Test generator with residential IPs only."""
        generator = IPGenerator(
            regions=["US"],
            include_residential=True,
            include_datacenter=False,
        )

        # Should generate valid IPs
        for _ in range(5):
            ip = generator.get_next_ip()
            IPv4Address(ip)  # Should not raise exception

    def test_datacenter_only(self):
        """Test generator with datacenter IPs only."""
        generator = IPGenerator(
            regions=["US"],
            include_residential=False,
            include_datacenter=True,
        )

        # Should generate valid IPs
        for _ in range(5):
            ip = generator.get_next_ip()
            IPv4Address(ip)  # Should not raise exception

    def test_no_ip_types_fallback(self):
        """Test generator fallback when no IP types enabled."""
        generator = IPGenerator(
            regions=["US"],
            include_residential=False,
            include_datacenter=False,
        )

        # Should fall back to test ranges
        ip = generator.get_next_ip()
        IPv4Address(ip)  # Should not raise exception

        # Should be from test ranges (198.51.100.x or 203.0.113.x)
        ip_addr = IPv4Address(ip)
        test_network1 = ipaddress.IPv4Network("198.51.100.0/24")
        test_network2 = ipaddress.IPv4Network("203.0.113.0/24")

        assert ip_addr in test_network1 or ip_addr in test_network2


class TestIPGeneratorEdgeCases:
    """Test IP generator edge cases and error conditions."""

    def test_empty_regions_list(self):
        """Test generator with empty regions list."""
        generator = IPGenerator(regions=[])

        # Should fall back to test ranges
        ip = generator.get_next_ip()
        IPv4Address(ip)  # Should not raise exception

    def test_invalid_regions_only(self):
        """Test generator with only invalid regions."""
        generator = IPGenerator(regions=["INVALID1", "INVALID2"])

        # Should fall back to test ranges
        ip = generator.get_next_ip()
        IPv4Address(ip)  # Should not raise exception

    def test_mixed_valid_invalid_regions(self):
        """Test generator with mix of valid and invalid regions."""
        generator = IPGenerator(regions=["US", "INVALID", "EU"])

        # Should work with valid regions only
        stats = generator.get_stats()
        assert isinstance(stats["available_ranges"], int) and stats["available_ranges"] > 0

    def test_zero_rotation_interval(self):
        """Test generator behavior with various rotation intervals."""
        # rotation_interval=1 should change every request
        generator = IPGenerator(regions=["US"], rotation_interval=1)

        # Very likely to be different with large IP space
        # Allow for small chance of collision
        ips = set()
        for _ in range(10):
            ips.add(generator.get_next_ip())

        assert len(ips) >= 5  # Should get variety

    def test_large_rotation_interval(self):
        """Test generator with large rotation interval."""
        generator = IPGenerator(regions=["US"], rotation_interval=1000)

        # Should keep same IP for many requests
        ips = set()
        for _ in range(50):
            ips.add(generator.get_next_ip())

        # Should be same IP for all requests
        assert len(ips) == 1

    def test_concurrent_access_simulation(self):
        """Test generator behavior under concurrent-like access patterns."""
        generator = IPGenerator(regions=["US"], rotation_interval=3)

        # Simulate concurrent access patterns
        results = []
        for _batch in range(5):
            batch_ips = []
            for _ in range(3):
                batch_ips.append(generator.get_next_ip())
            results.append(batch_ips)

        # Within each batch of 3, IPs should be same
        for batch_ips in results:
            assert batch_ips[0] == batch_ips[1] == batch_ips[2]

        # Between batches, IPs should be different (high probability)
        batch_unique_ips = [batch[0] for batch in results]
        assert len(set(batch_unique_ips)) >= 3  # Allow some collision


class TestIPGeneratorNetworkValidation:
    """Test IP generator network range validation."""

    def test_generated_ips_are_not_reserved(self):
        """Test that generated IPs are not from reserved ranges."""
        generator = IPGenerator(regions=["US", "EU", "APAC"])

        for _ in range(50):
            ip = generator.get_next_ip()
            ip_addr = IPv4Address(ip)

            # Should not be loopback, multicast, or other reserved ranges
            assert not ip_addr.is_loopback
            assert not ip_addr.is_multicast
            assert not ip_addr.is_reserved
            # Allow private ranges as some test ranges might be private

    def test_generated_ips_variety(self):
        """Test that generated IPs show good variety."""
        generator = IPGenerator(regions=["US", "EU", "APAC"], rotation_interval=1)

        # Generate many IPs and check for variety
        ips = set()
        for _ in range(100):
            ip = generator.get_next_ip()
            ips.add(ip)

        # Should get good variety (allowing for some randomness)
        assert len(ips) >= 30

    def test_ip_ranges_distribution(self):
        """Test that IPs are distributed across different network ranges."""
        generator = IPGenerator(regions=["US"], rotation_interval=1)

        # Generate IPs and check first octet distribution
        first_octets = set()
        for _ in range(100):
            ip = generator.get_next_ip()
            first_octet = int(ip.split(".")[0])
            first_octets.add(first_octet)

        # Should span multiple first octets (indicating different networks)
        assert len(first_octets) >= 5

    def test_fallback_ip_ranges_valid(self):
        """Test that fallback IP ranges are from valid test networks."""
        generator = IPGenerator(regions=[], include_residential=False, include_datacenter=False)

        # Should use test ranges when no other ranges available
        for _ in range(10):
            ip = generator.get_next_ip()
            ip_addr = IPv4Address(ip)

            # Should be from RFC 5737 test ranges
            test_net1 = ipaddress.IPv4Network("198.51.100.0/24")
            test_net2 = ipaddress.IPv4Network("203.0.113.0/24")

            assert ip_addr in test_net1 or ip_addr in test_net2


class TestIPGeneratorBurstMode:
    """Test IP generator burst mode functionality."""

    def test_burst_mode_initialization(self):
        """Test burst mode initialization."""
        generator = IPGenerator(burst_mode=True)

        assert generator.burst_mode is True
        stats = generator.get_stats()
        assert stats["burst_mode"] is True

    def test_burst_mode_single_ip_persistence(self):
        """Test that burst mode uses single IP for multiple requests."""
        generator = IPGenerator(regions=["US"], burst_mode=True, rotation_interval=1)

        # Get multiple IPs - should all be the same in burst mode
        ip1 = generator.get_next_ip()
        ip2 = generator.get_next_ip()
        ip3 = generator.get_next_ip()
        ip4 = generator.get_next_ip()
        ip5 = generator.get_next_ip()

        # All IPs should be identical in burst mode
        assert ip1 == ip2 == ip3 == ip4 == ip5
        assert generator.get_current_ip() == ip1

    def test_burst_mode_vs_normal_mode_behavior(self):
        """Test difference between burst mode and normal mode."""
        # Normal mode with very short rotation interval
        normal_generator = IPGenerator(regions=["US"], burst_mode=False, rotation_interval=1)

        # Burst mode
        burst_generator = IPGenerator(regions=["US"], burst_mode=True, rotation_interval=1)

        # Normal mode should rotate IPs (generate them but don't store for comparison)
        [normal_generator.get_next_ip() for _ in range(5)]

        # Burst mode should use same IP
        burst_ips = [burst_generator.get_next_ip() for _ in range(5)]

        # Normal mode might have different IPs (though not guaranteed due to randomness)
        # Burst mode should definitely have all same IPs
        assert len(set(burst_ips)) == 1, "Burst mode should use single IP"
        assert all(ip == burst_ips[0] for ip in burst_ips), "All burst IPs should be identical"

    def test_burst_mode_spoofing_headers_consistency(self):
        """Test that spoofing headers are consistent in burst mode."""
        generator = IPGenerator(regions=["US"], burst_mode=True)

        # Get multiple sets of headers
        headers1 = generator.get_spoofing_headers()
        headers2 = generator.get_spoofing_headers()
        headers3 = generator.get_spoofing_headers()

        # All headers should have the same IP addresses
        assert (
            headers1["X-Forwarded-For"]
            == headers2["X-Forwarded-For"]
            == headers3["X-Forwarded-For"]
        )
        assert headers1["X-Real-IP"] == headers2["X-Real-IP"] == headers3["X-Real-IP"]
        assert headers1["X-Client-IP"] == headers2["X-Client-IP"] == headers3["X-Client-IP"]

    def test_burst_mode_stats_tracking(self):
        """Test that stats properly track burst mode status."""
        generator = IPGenerator(regions=["US"], burst_mode=True)

        # Generate some IPs
        for _ in range(10):
            generator.get_next_ip()

        stats = generator.get_stats()
        assert stats["burst_mode"] is True
        assert stats["current_ip"] is not None
        assert stats["request_count"] == 0  # Burst mode doesn't increment request count
