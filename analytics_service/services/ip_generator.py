"""IP address generation service for request masking."""

import random
from ipaddress import IPv4Address, IPv4Network
from typing import ClassVar


class IPGenerator:
    """Generate realistic client IP addresses for request spoofing."""

    # Real ISP and datacenter IP ranges by region
    IP_RANGES: ClassVar[dict[str, dict[str, list[str]]]] = {
        "US": {
            "residential": [
                # Comcast/Xfinity
                "73.0.0.0/8",
                "98.0.0.0/8",
                "174.0.0.0/8",
                "76.0.0.0/8",
                # Verizon
                "108.0.0.0/8",
                "71.0.0.0/8",
                "97.0.0.0/8",
                # AT&T
                "99.0.0.0/8",
                "72.0.0.0/8",
                "75.0.0.0/8",
                # Charter/Spectrum
                "24.0.0.0/8",
                "70.0.0.0/8",
                "96.0.0.0/8",
            ],
            "datacenter": [
                # AWS US regions
                "54.0.0.0/8",
                "52.0.0.0/8",
                "3.0.0.0/8",
                # Google Cloud
                "35.0.0.0/8",
                "104.154.0.0/16",
                # Microsoft Azure
                "13.64.0.0/11",
                "40.64.0.0/10",
                # DigitalOcean
                "159.89.0.0/16",
                "138.197.0.0/16",
            ],
        },
        "EU": {
            "residential": [
                # Deutsche Telekom (Germany)
                "77.0.0.0/8",
                "91.0.0.0/8",
                "212.0.0.0/8",
                # Orange (France)
                "86.0.0.0/8",
                "90.0.0.0/8",
                # BT (UK)
                "81.0.0.0/8",
                "87.0.0.0/8",
                # Telecom Italia
                "79.0.0.0/8",
                "93.0.0.0/8",
                # Vodafone Europe
                "82.0.0.0/8",
                "84.0.0.0/8",
            ],
            "datacenter": [
                # AWS Europe
                "18.0.0.0/8",
                "34.0.0.0/8",
                # Google Cloud Europe
                "35.156.0.0/16",
                "35.198.0.0/16",
                # Azure Europe
                "13.69.0.0/16",
                "40.67.0.0/16",
                # Hetzner
                "78.46.0.0/15",
                "138.201.0.0/16",
            ],
        },
        "APAC": {
            "residential": [
                # NTT (Japan)
                "126.0.0.0/8",
                "210.0.0.0/8",
                # KDDI (Japan)
                "117.0.0.0/8",
                "124.0.0.0/8",
                # China Telecom
                "114.0.0.0/8",
                "116.0.0.0/8",
                # Singtel (Singapore)
                "165.21.0.0/16",
                "203.116.0.0/16",
                # Telstra (Australia)
                "101.0.0.0/8",
                "103.0.0.0/8",
            ],
            "datacenter": [
                # AWS Asia Pacific
                "13.228.0.0/16",
                "52.74.0.0/16",
                # Google Cloud APAC
                "35.187.0.0/16",
                "35.236.0.0/16",
                # Azure APAC
                "13.75.0.0/16",
                "40.83.0.0/16",
                # Alibaba Cloud
                "47.74.0.0/15",
                "8.208.0.0/16",
            ],
        },
    }

    def __init__(
        self,
        regions: list[str] | None = None,
        *,
        include_residential: bool = True,
        include_datacenter: bool = True,
        rotation_interval: int = 5,
        burst_mode: bool = False,
    ):
        """Initialize IP generator.

        Args:
            regions: Geographic regions to include (US, EU, APAC)
            include_residential: Include residential ISP ranges
            include_datacenter: Include cloud/datacenter ranges
            rotation_interval: Number of requests before rotating IP
            burst_mode: If True, stick to single IP for entire burst instead of rotating
        """
        self.regions = regions or ["US", "EU", "APAC"]
        self.include_residential = include_residential
        self.include_datacenter = include_datacenter
        self.rotation_interval = rotation_interval
        self.burst_mode = burst_mode

        self._current_ip: str | None = None
        self._request_count = 0
        self._available_ranges: list[IPv4Network] = []

        self._build_ip_pools()

    def _build_ip_pools(self) -> None:
        """Build the pool of available IP ranges based on configuration."""
        self._available_ranges.clear()

        for region in self.regions:
            if region not in self.IP_RANGES:
                continue

            region_ranges = self.IP_RANGES[region]

            if self.include_residential and "residential" in region_ranges:
                for cidr in region_ranges["residential"]:
                    try:
                        # Use smaller subnets for better distribution
                        network = IPv4Network(cidr, strict=False)
                        # Break large /8 networks into /16 for better variety
                        if network.prefixlen <= 16:
                            for subnet in network.subnets(new_prefix=16):
                                self._available_ranges.append(subnet)
                        else:
                            self._available_ranges.append(network)
                    except ValueError:
                        # Skip invalid CIDR ranges
                        continue

            if self.include_datacenter and "datacenter" in region_ranges:
                for cidr in region_ranges["datacenter"]:
                    try:
                        network = IPv4Network(cidr, strict=False)
                        # Use datacenter ranges as-is (usually smaller)
                        self._available_ranges.append(network)
                    except ValueError:
                        # Skip invalid CIDR ranges
                        continue

    def get_next_ip(self) -> str:
        """Get the next IP address for spoofing.

        Returns:
            IP address string for use in headers
        """
        # In burst mode, stick to the same IP once generated
        if self.burst_mode:
            if self._current_ip is None:
                self._current_ip = self._generate_new_ip()
            return self._current_ip

        # Normal mode: rotate IP if interval reached or no current IP
        if self._current_ip is None or self._request_count >= self.rotation_interval:
            self._current_ip = self._generate_new_ip()
            self._request_count = 0

        self._request_count += 1
        return self._current_ip

    def _generate_new_ip(self) -> str:
        """Generate a new random IP address from available ranges.

        Returns:
            Random IP address string
        """
        if not self._available_ranges:
            # Fallback to safe test ranges if no pools configured
            return self._generate_test_ip()

        # Select random network range
        network = random.choice(self._available_ranges)

        # Generate random IP within that range
        # Skip network and broadcast addresses
        network_int = int(network.network_address)
        broadcast_int = int(network.broadcast_address)

        # Ensure we have at least 2 usable addresses
        if broadcast_int - network_int < 3:
            return str(network.network_address + 1)

        # Generate random host address (skip network + 1 and broadcast - 1)
        host_int = random.randint(network_int + 1, broadcast_int - 1)

        return str(IPv4Address(host_int))

    def _generate_test_ip(self) -> str:
        """Generate IP from RFC 5737 test ranges as fallback.

        Returns:
            Test IP address string
        """
        # Use RFC 5737 documentation ranges as fallback
        test_ranges = [
            "198.51.100.0/24",  # TEST-NET-2
            "203.0.113.0/24",  # TEST-NET-3
        ]

        network = IPv4Network(random.choice(test_ranges))
        host_int = random.randint(
            int(network.network_address) + 1,
            int(network.broadcast_address) - 1,
        )

        return str(IPv4Address(host_int))

    def get_spoofing_headers(self) -> dict[str, str]:
        """Generate headers for IP spoofing.

        Returns:
            Dictionary of headers to add to HTTP requests
        """
        spoofed_ip = self.get_next_ip()

        return {
            "X-Forwarded-For": spoofed_ip,
            "X-Real-IP": spoofed_ip,
            "X-Originating-IP": spoofed_ip,
            "X-Client-IP": spoofed_ip,
            "CF-Connecting-IP": spoofed_ip,  # Cloudflare format
            "True-Client-IP": spoofed_ip,  # Akamai format
            "X-Original-Forwarded-For": spoofed_ip,
        }

    def reset_rotation(self) -> None:
        """Reset IP rotation counter to force new IP on next request."""
        self._request_count = self.rotation_interval

    def get_current_ip(self) -> str | None:
        """Get currently active spoofed IP.

        Returns:
            Current IP address or None if not generated yet
        """
        return self._current_ip

    def get_stats(self) -> dict[str, int | str | list[str] | bool | None]:
        """Get generator statistics.

        Returns:
            Dictionary with current stats
        """
        return {
            "current_ip": self._current_ip,
            "request_count": self._request_count,
            "rotation_interval": self.rotation_interval,
            "burst_mode": self.burst_mode,
            "available_ranges": len(self._available_ranges),
            "regions": self.regions,
        }
