"""Load testing control page for the dashboard."""

import time
from typing import Any

import requests
import streamlit as st

from dashboard.utils import ANALYTICS_SERVICE_URL


def check_and_handle_auto_stop_timers():
    """Check if any tests should be automatically stopped based on duration."""
    if "auto_stop_timer" not in st.session_state:
        return

    current_time = time.time()
    tests_to_stop = []

    for test_id, timer_info in st.session_state.auto_stop_timer.items():
        elapsed_time = current_time - timer_info["start_time"]
        if elapsed_time >= timer_info["duration"]:
            tests_to_stop.append(test_id)

    # Stop expired tests
    for test_id in tests_to_stop:
        timer_info = st.session_state.auto_stop_timer[test_id]
        try:
            response = requests.post(f"{ANALYTICS_SERVICE_URL}/api/load-test/stop", timeout=10)
            if response.status_code == 200:
                st.success(
                    f"✅ {timer_info['test_type'].title()} test automatically stopped after {timer_info['duration']} seconds"
                )
            else:
                st.warning(f"⚠️ Failed to auto-stop {timer_info['test_type']} test: {response.text}")
        except Exception as e:
            st.error(f"❌ Error auto-stopping {timer_info['test_type']} test: {e!s}")

        # Remove from session state
        del st.session_state.auto_stop_timer[test_id]


def show_attack_simulation_page():
    """Display the load testing control page."""
    # Check for auto-stop timers first
    check_and_handle_auto_stop_timers()

    st.header("🔥 Load Testing Control")
    st.markdown(
        """
        This page allows you to run various load testing scenarios against the external Currency API
        for performance testing and validation.

        **⚠️ Note**: This will generate load against the external API. Ensure the API is ready to handle test traffic.
        """
    )

    # Create two columns for different test types
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 Baseline Load Test")
        st.markdown("Simulate steady user traffic")

        baseline_rps = st.slider(
            "Requests per Second", min_value=1, max_value=50, value=35, help="Steady request rate"
        )

        continuous_mode = st.checkbox(
            "🔄 Continuous Baseline",
            help="Run baseline continuously until manually stopped",
        )

        duration = None
        if not continuous_mode:
            duration = st.number_input(
                "Duration (seconds)",
                min_value=10,
                max_value=1200,
                value=60,
                help="How long to run the test",
            )

        if st.button("🟢 Start Baseline Test", key="start_baseline"):
            if continuous_mode:
                start_continuous_baseline(baseline_rps)
            elif duration is not None:
                start_load_test("baseline", baseline_rps, duration)

    with col2:
        st.subheader("⚡ Ramping Burst Load Test")
        st.markdown("Test with gradually increasing burst traffic (10 steps over duration)")

        burst_rps = st.slider(
            "Peak RPS",
            min_value=10,
            max_value=2000,
            value=800,
            help="Peak request rate to reach by end of test. Starts at 10% and ramps up gradually.",
        )

        burst_duration = st.number_input(
            "Burst Duration (seconds)",
            min_value=30,
            max_value=1200,
            value=1200,
            help="Total duration for ramping up to peak RPS (minimum 30s for effective ramping)",
        )

        if st.button("⚡ Start Burst Test", key="start_burst"):
            start_load_test("burst", burst_rps, burst_duration)

    # Control buttons
    st.subheader("🎛️ Test Controls")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔴 Stop All Tests", key="stop_all"):
            stop_all_tests()

    with col2:
        if st.button("🛑 Stop Baseline", key="stop_baseline"):
            stop_baseline_test()

    with col3:
        if st.button("🛑 Stop Burst", key="stop_burst"):
            stop_burst_test()

    with col4:
        if st.button("📊 Get Report", key="get_report"):
            show_test_report()

    # Status display
    st.subheader("📊 Current Test Status")

    # Check for active timers and display countdown
    if "auto_stop_timer" in st.session_state and st.session_state.auto_stop_timer:
        current_time = time.time()
        for _test_id, timer_info in st.session_state.auto_stop_timer.items():
            elapsed_time = current_time - timer_info["start_time"]
            remaining_time = max(0, timer_info["duration"] - elapsed_time)

            if remaining_time > 0:
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                st.info(
                    f"⏱️ {timer_info['test_type'].title()} test will auto-stop in: {minutes:02d}:{seconds:02d}"
                )

    # Get status of both main and baseline load tests
    main_status = get_load_test_status()
    baseline_status = get_baseline_test_status()

    # Display baseline status
    if baseline_status:
        st.write("**🔄 Continuous Baseline Test**")
        display_status_table(baseline_status, test_name="Baseline")
        st.divider()

    # Display main test status
    if main_status and main_status.get("status") != "idle":
        st.write("**⚡ Main Load Test**")
        display_status_table(main_status, test_name="Main")
    elif not baseline_status:
        st.info("No active load tests")

    # Auto-refresh for countdown timer
    if "auto_stop_timer" in st.session_state and st.session_state.auto_stop_timer:
        time.sleep(1)  # Small delay before refresh
        st.rerun()


def start_continuous_baseline(rps: float) -> None:
    """Start a continuous baseline load test using concurrent API."""
    try:
        # Use minimal config - let the API populate all currency pairs and amounts automatically
        config = {
            "requests_per_second": rps,
            "error_injection_enabled": True,
            "error_injection_rate": 0.02,  # Low error rate for realistic baseline
        }

        response = requests.post(
            f"{ANALYTICS_SERVICE_URL}/api/load-test/concurrent/baseline/start",
            json={"config": config},
            timeout=10,
        )

        if response.status_code == 200:
            st.success("✅ Continuous baseline load test started successfully!")
        elif response.status_code == 409:  # Conflict - baseline already running
            # Stop existing baseline test and start new one
            st.info("🔄 Stopping existing baseline test and starting new one...")

            # Stop the existing baseline test
            stop_response = requests.post(
                f"{ANALYTICS_SERVICE_URL}/api/load-test/concurrent/baseline/stop",
                timeout=10,
            )

            if stop_response.status_code == 200:
                # Try starting the new baseline test
                retry_response = requests.post(
                    f"{ANALYTICS_SERVICE_URL}/api/load-test/concurrent/baseline/start",
                    json={"config": config},
                    timeout=10,
                )

                if retry_response.status_code == 200:
                    st.success("✅ Baseline test restarted with new configuration!")
                else:
                    st.error(f"❌ Failed to restart baseline test: {retry_response.text}")
            else:
                st.error(f"❌ Failed to stop existing baseline test: {stop_response.text}")
        else:
            st.error(f"❌ Failed to start baseline test: {response.text}")

    except Exception as e:
        st.error(f"❌ Error starting baseline test: {e!s}")


def start_load_test(test_type: str, rps: float, duration: int) -> None:
    """Start a load test with the specified parameters."""
    try:
        if test_type == "burst":
            # Use ramping burst test for gradual load increase
            params = {
                "target_rps": rps,
                "duration_seconds": duration,
                "error_injection_enabled": True,
                "error_injection_rate": 0.05,
            }

            response = requests.post(
                f"{ANALYTICS_SERVICE_URL}/api/load-test/burst-ramp", params=params, timeout=10
            )
        else:
            # Use regular load test for baseline
            config = {
                "requests_per_second": rps,
                "error_injection_enabled": False,
                "error_injection_rate": 0.01,
                "burst_mode": False,
            }

            response = requests.post(
                f"{ANALYTICS_SERVICE_URL}/api/load-test/start", json={"config": config}, timeout=10
            )

        if response.status_code == 200:
            if test_type == "burst":
                st.success(
                    f"✅ Ramping burst test started! Will gradually increase from {rps * 0.1:.1f} to {rps} RPS over {duration} seconds."
                )
            else:
                st.success(
                    f"✅ {test_type.title()} load test started successfully! Will run for {duration} seconds."
                )

            # Schedule automatic stop after duration
            if "auto_stop_timer" not in st.session_state:
                st.session_state.auto_stop_timer = {}

            st.session_state.auto_stop_timer[test_type] = {
                "start_time": time.time(),
                "duration": duration,
                "test_type": test_type,
            }

        elif (
            response.status_code == 409 or response.status_code == 500
        ):  # Conflict or error - test already running
            # Stop existing test and start new one
            st.info("🔄 Stopping existing test and starting new one...")

            # Stop any existing test
            stop_response = requests.post(f"{ANALYTICS_SERVICE_URL}/api/load-test/stop", timeout=10)

            if stop_response.status_code == 200:
                # Try starting the new test
                if test_type == "burst":
                    retry_response = requests.post(
                        f"{ANALYTICS_SERVICE_URL}/api/load-test/burst-ramp",
                        params=params,
                        timeout=10,
                    )
                else:
                    retry_response = requests.post(
                        f"{ANALYTICS_SERVICE_URL}/api/load-test/start",
                        json={"config": config},
                        timeout=10,
                    )

                if retry_response.status_code == 200:
                    if test_type == "burst":
                        st.success(
                            f"✅ Burst test restarted! Will gradually increase from {rps * 0.1:.1f} to {rps} RPS over {duration} seconds."
                        )
                    else:
                        st.success(f"✅ {test_type.title()} test restarted with new configuration!")

                    # Schedule automatic stop after duration for restarted test
                    if "auto_stop_timer" not in st.session_state:
                        st.session_state.auto_stop_timer = {}

                    st.session_state.auto_stop_timer[test_type] = {
                        "start_time": time.time(),
                        "duration": duration,
                        "test_type": test_type,
                    }
                else:
                    st.error(f"❌ Failed to restart {test_type} test: {retry_response.text}")
            else:
                st.error(f"❌ Failed to stop existing test: {stop_response.text}")
        else:
            st.error(f"❌ Failed to start {test_type} test: {response.text}")

    except Exception as e:
        st.error(f"❌ Error starting load test: {e!s}")


def stop_baseline_test() -> None:
    """Stop the continuous baseline load test."""
    try:
        response = requests.post(
            f"{ANALYTICS_SERVICE_URL}/api/load-test/concurrent/baseline/stop", timeout=10
        )

        if response.status_code == 200:
            st.success("✅ Baseline load test stopped successfully!")
        else:
            st.error(f"❌ Failed to stop baseline test: {response.text}")

    except Exception as e:
        st.error(f"❌ Error stopping baseline test: {e!s}")


def stop_burst_test() -> None:
    """Stop the current burst/main load test."""
    try:
        response = requests.post(f"{ANALYTICS_SERVICE_URL}/api/load-test/stop", timeout=10)

        if response.status_code == 200:
            st.success("✅ Burst load test stopped successfully!")

            # Clear any auto-stop timers for burst test
            if (
                "auto_stop_timer" in st.session_state
                and "burst" in st.session_state.auto_stop_timer
            ):
                del st.session_state.auto_stop_timer["burst"]
        else:
            st.error(f"❌ Failed to stop burst test: {response.text}")

    except Exception as e:
        st.error(f"❌ Error stopping burst test: {e!s}")


def stop_all_tests() -> None:
    """Stop all running load tests."""
    try:
        # Stop main load test
        response1 = requests.post(f"{ANALYTICS_SERVICE_URL}/api/load-test/stop", timeout=10)

        # Stop all concurrent tests (including baseline)
        response2 = requests.post(
            f"{ANALYTICS_SERVICE_URL}/api/load-test/concurrent/stop-all", timeout=10
        )

        if response1.status_code == 200 and response2.status_code == 200:
            st.success("✅ All load tests stopped successfully!")
        else:
            st.error(
                f"❌ Failed to stop some tests. Main: {response1.text}, Concurrent: {response2.text}"
            )

        # Clear any auto-stop timers
        if "auto_stop_timer" in st.session_state:
            st.session_state.auto_stop_timer.clear()

    except Exception as e:
        st.error(f"❌ Error stopping tests: {e!s}")


def get_baseline_test_status() -> dict[str, Any] | None:
    """Get the current status of the baseline load test."""
    try:
        response = requests.get(
            f"{ANALYTICS_SERVICE_URL}/api/load-test/concurrent/baseline/status", timeout=10
        )

        if response.status_code == 200:
            return response.json()
        return None

    except Exception:
        # Baseline test not running or doesn't exist
        return None


def get_load_test_status() -> dict[str, Any] | None:
    """Get the current status of load tests."""
    try:
        response = requests.get(f"{ANALYTICS_SERVICE_URL}/api/load-test/status", timeout=10)

        if response.status_code == 200:
            return response.json()
        return None

    except Exception as e:
        st.error(f"❌ Error getting status: {e!s}")
        return None


def show_test_report() -> None:
    """Display the test report."""
    try:
        response = requests.get(f"{ANALYTICS_SERVICE_URL}/api/load-test/report", timeout=10)

        if response.status_code == 200:
            report = response.json()
            st.json(report)
        else:
            st.error("❌ No test report available")

    except Exception as e:
        st.error(f"❌ Error getting report: {e!s}")


def display_status_table(status_data: dict[str, Any], test_name: str = "Test") -> None:
    """Display simplified status of load tests."""
    if not status_data:
        return

    # Display current test status
    status = status_data.get("status", "unknown")
    config = status_data.get("config", {})

    # Status indicator
    status_color = "🟢" if status == "running" else "🔴" if status == "stopped" else "🟡"
    st.write(f"**Status**: {status_color} {status.upper()}")

    if config:
        st.write(f"**Configuration**: {config.get('requests_per_second', 0)} RPS")
