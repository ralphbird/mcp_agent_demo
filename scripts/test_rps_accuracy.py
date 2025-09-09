#!/usr/bin/env python3
"""Test script to validate RPS accuracy improvements with latency compensation."""

import asyncio

from load_tester.models.load_test import LoadTestConfig
from load_tester.services.load_generator import LoadGenerator


async def test_rps_accuracy_without_compensation():
    """Test RPS accuracy with compensation disabled."""
    print("🧪 Testing RPS accuracy WITHOUT latency compensation...")

    # Configure for no compensation
    from load_tester.config import settings

    settings.latency_compensation_enabled = False
    settings.adaptive_scaling_enabled = False

    config = LoadTestConfig(
        requests_per_second=10.0,
        currency_pairs=["USD_EUR"],  # Single pair for predictable testing
        amounts=[100.0],
        error_injection_enabled=False,
    )

    generator = LoadGenerator(config)

    try:
        # Start the generator
        await generator.start()

        # Let it run for 30 seconds
        print("Running for 30 seconds...")
        await asyncio.sleep(30)

        # Get final stats
        stats = await generator.get_current_stats()

        print(f"Target RPS: {stats.target_requests_per_second:.1f}")
        print(f"Achieved RPS: {stats.rolling_requests_per_second:.1f}")
        print(f"Accuracy: {stats.achieved_rps_accuracy:.1f}%")
        print(f"Avg Response Time: {stats.rolling_avg_response_ms:.1f}ms")
        print(f"Total Requests: {stats.total_requests}")

        return stats.achieved_rps_accuracy, stats.rolling_avg_response_ms

    finally:
        await generator.stop()


async def test_rps_accuracy_with_compensation():
    """Test RPS accuracy with compensation enabled."""
    print("\n🚀 Testing RPS accuracy WITH latency compensation...")

    # Configure for compensation
    from load_tester.config import settings

    settings.latency_compensation_enabled = True
    settings.adaptive_scaling_enabled = True

    config = LoadTestConfig(
        requests_per_second=10.0,
        currency_pairs=["USD_EUR"],  # Single pair for predictable testing
        amounts=[100.0],
        error_injection_enabled=False,
    )

    generator = LoadGenerator(config)

    try:
        # Start the generator
        await generator.start()

        # Let it run for 30 seconds
        print("Running for 30 seconds...")
        await asyncio.sleep(30)

        # Get final stats
        stats = await generator.get_current_stats()

        print(f"Target RPS: {stats.target_requests_per_second:.1f}")
        print(f"Achieved RPS: {stats.rolling_requests_per_second:.1f}")
        print(f"Accuracy: {stats.achieved_rps_accuracy:.1f}%")
        print(f"Avg Response Time: {stats.rolling_avg_response_ms:.1f}ms")
        print(f"Avg Compensation: {stats.avg_compensation_ms:.1f}ms")
        print(f"Adaptive Scaling Active: {stats.adaptive_scaling_active}")
        print(f"Workers: {stats.current_worker_count} (base: {stats.base_worker_count})")
        print(f"Total Requests: {stats.total_requests}")

        return stats.achieved_rps_accuracy, stats.rolling_avg_response_ms

    finally:
        await generator.stop()


async def main():
    """Run RPS accuracy validation tests."""
    print("🎯 RPS Accuracy Validation Test Suite")
    print("=" * 50)

    # Test without compensation
    accuracy_without, response_time_without = await test_rps_accuracy_without_compensation()

    # Wait a bit between tests
    await asyncio.sleep(5)

    # Test with compensation
    accuracy_with, response_time_with = await test_rps_accuracy_with_compensation()

    # Compare results
    print("\n📊 RESULTS SUMMARY")
    print("=" * 50)
    print("Without Compensation:")
    print(f"  - Accuracy: {accuracy_without:.1f}%")
    print(f"  - Avg Response: {response_time_without:.1f}ms")

    print("\nWith Compensation:")
    print(f"  - Accuracy: {accuracy_with:.1f}%")
    print(f"  - Avg Response: {response_time_with:.1f}ms")

    improvement = accuracy_with - accuracy_without
    print(f"\n🎉 Accuracy Improvement: {improvement:+.1f}%")

    if improvement > 5.0:
        print("✅ SIGNIFICANT improvement with latency compensation!")
    elif improvement > 0:
        print("✅ Positive improvement with latency compensation")
    else:
        print("❌ No improvement detected - may need investigation")

    # Recommendations
    print("\n💡 RECOMMENDATIONS")
    print("=" * 50)
    if accuracy_with >= 95:
        print("🌟 Excellent RPS accuracy achieved!")
    elif accuracy_with >= 85:
        print("✅ Good RPS accuracy - within acceptable range")
    else:
        print("⚠️ RPS accuracy below 85% - consider:")
        print("  - Reducing target RPS")
        print("  - Optimizing target API performance")
        print("  - Increasing worker scaling limits")


if __name__ == "__main__":
    asyncio.run(main())
