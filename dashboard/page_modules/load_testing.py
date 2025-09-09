"""Load testing page."""

import time

import streamlit as st

from dashboard.utils import (
    check_load_tester_health,
    get_load_test_scenarios,
    get_load_test_status,
    get_scenario_details,
    start_custom_load_test,
    start_load_test_scenario,
    start_simple_load_test,
    stop_load_test,
)
from load_tester.models.load_test import _get_all_amounts, _get_all_currency_pairs


def show_load_testing_page():
    """Show the load testing control and monitoring page."""
    st.header("🔥 Load Testing Dashboard")

    # Check load tester health (only show if there's an issue)
    load_tester_health = check_load_tester_health()
    if not load_tester_health:
        st.error("❌ Load Tester service is not accessible")
        st.info("Make sure the Load Tester service is running at http://localhost:8001")
        return

    # Get current test status
    status = get_load_test_status()
    if not status:
        return

    # Display current status
    st.subheader("📊 Current Test Status")

    status_color = {
        "idle": "🟢",
        "starting": "🟡",
        "running": "🔴",
        "stopping": "🟡",
        "stopped": "🟠",
        "error": "❌",
    }.get(status["status"], "⚪")

    st.info(f"{status_color} **Status**: {status['status'].upper()}")

    # Real-time test information
    if status["status"] in ["running", "starting", "stopping"]:
        if status.get("config"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Target RPS", status["config"]["requests_per_second"])
            with col2:
                error_injection = status["config"].get("error_injection_enabled", False)
                error_rate = status["config"].get("error_injection_rate", 0) * 100
                injection_status = f"✅ {error_rate:.1f}%" if error_injection else "❌ Disabled"
                st.metric("Error Injection", injection_status)

        # Live statistics
        if status.get("stats"):
            st.subheader("📈 Live Statistics (1-Minute Rolling Average)")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Requests", status["stats"]["total_requests"])
            with col2:
                rolling_success_rate = status["stats"].get("rolling_success_rate", 0.0)
                st.metric("Success Rate (1m)", f"{rolling_success_rate:.1f}%")
            with col3:
                rolling_avg_response = status["stats"].get("rolling_avg_response_ms", 0.0)
                st.metric("Avg Response (1m)", f"{rolling_avg_response:.1f}ms")
            with col4:
                rolling_rps = status["stats"].get("rolling_requests_per_second", 0.0)
                st.metric("Current RPS (1m)", f"{rolling_rps:.2f}")

    # Main Control Panel
    st.subheader("🎮 Load Test Controls")

    # Show different controls based on current state
    if status["status"] == "error":
        st.error("⚠️ Load test is in error state. Use Emergency Stop to reset.")

    elif status["status"] in ["running", "starting", "stopping"]:
        # Show ramping and stop controls for active tests
        st.info(
            "💡 **Load Ramping**: You can seamlessly transition to different load levels without stopping the current test."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🛑 Stop Load Test", type="secondary"):
                result = stop_load_test()
                if result:
                    st.success("Load test stopped successfully!")
                    st.rerun()

        with col2:
            # Show ramp controls
            st.markdown("**🔄 Ramp to New Load Level:**")

        # Ramping tabs
        ramp_tab1, ramp_tab2 = st.tabs(["📋 Ramp to Scenario", "⚙️ Ramp to Custom"])

        with ramp_tab1:
            st.markdown("**Transition to a different scenario:**")
            scenarios = get_load_test_scenarios()
            if scenarios:
                scenario_names = list(scenarios.keys())
                ramp_scenario = st.selectbox(
                    "Ramp to Scenario",
                    scenario_names,
                    key="ramp_scenario_select",
                    help="Seamlessly transition to this scenario's load level",
                )

                if ramp_scenario:
                    scenario_details = get_scenario_details(ramp_scenario)
                    if scenario_details:
                        current_rps = status.get("config", {}).get("requests_per_second", 0)
                        target_rps = scenario_details["config"]["requests_per_second"]

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Current RPS", f"{current_rps}")
                        with col2:
                            st.metric("Target RPS", f"{target_rps}")

                        ramp_direction = (
                            "⬆️ Ramp Up"
                            if target_rps > current_rps
                            else "⬇️ Ramp Down"
                            if target_rps < current_rps
                            else "🔄 Update Config"
                        )

                        if st.button(
                            f"{ramp_direction} to {scenario_details['name']}",
                            type="primary",
                            key="ramp_scenario_btn",
                        ):
                            result = start_load_test_scenario(
                                ramp_scenario
                            )  # This will now ramp instead of fail
                            if result:
                                st.success(f"Successfully ramped to {scenario_details['name']}!")
                                st.rerun()

        with ramp_tab2:
            st.markdown("**Ramp to custom configuration:**")

            col1, col2 = st.columns(2)
            with col1:
                current_config = status.get("config", {})
                current_rps = current_config.get("requests_per_second", 5.0)

                ramp_rps = st.slider(
                    "Target Requests per Second",
                    min_value=0.1,
                    max_value=50.0,
                    value=float(current_rps),
                    step=0.1,
                    help="New load level to ramp to",
                    key="ramp_rps_slider",
                )

                # Use all currency pairs and amounts automatically
                ramp_currency_pairs = _get_all_currency_pairs()
                ramp_amounts = _get_all_amounts()

            with col2:
                # Show ramping direction
                ramp_direction = (
                    "⬆️ Ramp Up"
                    if ramp_rps > current_rps
                    else "⬇️ Ramp Down"
                    if ramp_rps < current_rps
                    else "🔄 Update Config"
                )
                st.metric("Ramping Direction", ramp_direction)

            if ramp_currency_pairs and ramp_amounts:
                custom_ramp_config = {
                    "requests_per_second": ramp_rps,
                    "currency_pairs": ramp_currency_pairs,
                    "amounts": ramp_amounts,
                }

                if st.button(
                    f"🚀 {ramp_direction} (RPS: {current_rps} → {ramp_rps})",
                    type="primary",
                    key="ramp_custom_btn",
                ):
                    result = start_custom_load_test(
                        custom_ramp_config
                    )  # This will now ramp instead of fail
                    if result:
                        st.success(
                            f"Successfully ramped load from {current_rps} to {ramp_rps} RPS!"
                        )
                        st.rerun()

    elif status["status"] == "stopped":
        st.warning(
            "🔶 Load test has been stopped. You can start a new test or use Reset to return to idle state."
        )

        # Add reset and restart options for stopped tests
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Reset to Idle", type="secondary"):
                # Reset by getting fresh status (this will show idle state)
                st.rerun()

        with col2:
            st.markdown("**🚀 Quick Restart:**")

        # Quick restart options
        restart_col1, restart_col2 = st.columns(2)

        with restart_col1:
            if st.button("🚀 Restart Light Test (1 RPS)", type="primary"):
                result = start_simple_load_test(
                    1.0, error_injection_enabled=False, error_injection_rate=0.05
                )
                if result:
                    st.success("Light test restarted!")
                    st.rerun()

        with restart_col2:
            if st.button("🚀 Restart Moderate Test (5 RPS)", type="primary"):
                result = start_simple_load_test(
                    5.0, error_injection_enabled=False, error_injection_rate=0.05
                )
                if result:
                    st.success("Moderate test restarted!")
                    st.rerun()

    else:
        # Show start options for inactive tests
        tab1, tab2, tab3 = st.tabs(["📋 Scenario Tests", "🚀 Simple Test", "⚙️ Custom Test"])

        with tab1:
            st.markdown("**Choose from predefined load test scenarios:**")

            scenarios = get_load_test_scenarios()
            if scenarios:
                # Create scenario cards
                scenario_names = list(scenarios.keys())
                selected_scenario = st.selectbox(
                    "Select Load Test Scenario",
                    scenario_names,
                    help="Choose a predefined scenario with optimized settings",
                )

                if selected_scenario:
                    # Get scenario details
                    scenario_details = get_scenario_details(selected_scenario)
                    if scenario_details:
                        # Display scenario information
                        st.info(
                            f"📖 **{scenario_details['name']}**\n\n{scenario_details['description']}"
                        )

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Target RPS", scenario_details["config"]["requests_per_second"]
                            )
                        with col2:
                            st.metric(
                                "Recommended Duration", f"{scenario_details['duration_seconds']}s"
                            )
                        with col3:
                            st.metric("Configuration", "Auto-Optimized")

                        st.success(
                            "🎯 **Auto-Configuration**: Optimized settings with comprehensive test coverage"
                        )

                        st.markdown(
                            f"**Expected Behavior:** {scenario_details['expected_behavior']}"
                        )

                        # Start scenario button
                        if st.button(f"🚀 Start {scenario_details['name']}", type="primary"):
                            result = start_load_test_scenario(selected_scenario)
                            if result:
                                st.success(f"Started {scenario_details['name']} successfully!")
                                st.rerun()

        with tab2:
            st.markdown("**Quick load test with automatic configuration:**")
            st.success(
                "🎯 **Auto-Configuration**: Optimized settings with comprehensive test coverage"
            )

            simple_rps = st.slider(
                "Requests per Second",
                min_value=0.1,
                max_value=50.0,
                value=5.0,
                step=0.1,
                help="Number of requests to send per second. All currency pairs and appropriate amounts will be used automatically.",
            )

            # Error injection settings
            st.markdown("**🔬 Error Injection (Advanced):**")
            error_injection_col1, error_injection_col2 = st.columns(2)

            with error_injection_col1:
                error_injection_enabled = st.checkbox(
                    "Enable Error Injection",
                    value=False,
                    help="Include a percentage of invalid requests for realistic testing",
                )

            with error_injection_col2:
                if error_injection_enabled:
                    error_injection_rate = st.slider(
                        "Error Rate",
                        min_value=0.01,
                        max_value=0.30,
                        value=0.05,
                        step=0.01,
                        format="%.2f",
                        help="Percentage of requests that will be invalid (1%-30%)",
                    )
                else:
                    error_injection_rate = 0.05
                    st.text("Error Rate: 5% (disabled)")

            if error_injection_enabled:
                st.info(
                    "🧪 **Error Injection**: Includes invalid requests like unsupported currencies (XXX, ZZZ), "
                    "negative amounts, zero amounts, wrong currency formats, etc. This simulates real-world traffic patterns."
                )

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Target RPS", f"{simple_rps}")
            with col2:
                error_display = (
                    f"{error_injection_rate:.1%}" if error_injection_enabled else "Disabled"
                )
                st.metric("Error Injection", error_display)

            if st.button("🚀 Start Simple Load Test", type="primary"):
                result = start_simple_load_test(
                    simple_rps, error_injection_enabled, error_injection_rate
                )
                if result:
                    if error_injection_enabled:
                        st.success(
                            f"Simple load test started with {error_injection_rate:.1%} error injection!"
                        )
                    else:
                        st.success("Simple load test started successfully!")
                    st.rerun()
                else:
                    st.error("Failed to start load test. Check the API connection.")

        with tab3:
            st.markdown("**Configure a custom load test:**")

            col1, col2 = st.columns(2)

            with col1:
                custom_rps = st.slider(
                    "Requests per Second",
                    min_value=0.1,
                    max_value=50.0,
                    value=5.0,
                    step=0.1,
                    help="Number of requests to send per second",
                )

                # Use all currency pairs and amounts automatically
                currency_pairs = _get_all_currency_pairs()
                amounts = _get_all_amounts()

            with col2:
                st.info(
                    "💡 **Simplified**: Auto-configured with all currency pairs and optimized amounts"
                )

            if currency_pairs and amounts and st.button("🚀 Start Custom Test", type="primary"):
                custom_config = {
                    "requests_per_second": custom_rps,
                    "currency_pairs": currency_pairs,
                    "amounts": amounts,
                }
                result = start_custom_load_test(custom_config)
                if result:
                    st.success("Custom load test started successfully!")
                    st.rerun()

    # Quick Links
    st.subheader("🔗 Quick Links")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("[📋 Load Tester API Docs](http://localhost:8001/docs)")
    with col2:
        st.markdown("[📊 Load Tester Metrics](http://localhost:8001/metrics)")
    with col3:
        st.markdown("[🎯 Available Scenarios](http://localhost:8001/api/load-test/scenarios)")

    st.info(
        "💡 **Tip**: Load tests help identify performance bottlenecks and capacity limits. Use different scenarios to test various load patterns and system behavior."
    )

    # Auto-refresh for running tests (moved to end so controls render first)
    if status["status"] == "running":
        time.sleep(2)  # Brief pause to prevent excessive CPU usage
        st.rerun()
