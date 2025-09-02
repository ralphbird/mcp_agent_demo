"""Streamlit dashboard for currency conversion API."""

import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
LOAD_TESTER_URL = os.getenv("LOAD_TESTER_URL", "http://localhost:8001")


def get_current_rates():
    """Fetch current exchange rates from the API."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/rates")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch rates: {e}")
        return None


def convert_currency(amount, from_currency, to_currency):
    """Convert currency using the API."""
    try:
        payload = {
            "amount": float(amount),
            "from_currency": from_currency,
            "to_currency": to_currency,
        }
        response = requests.post(f"{API_BASE_URL}/api/v1/convert", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to convert currency: {e}")
        return None


def check_api_health():
    """Check if the API is healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def get_rates_history(currency=None, days=7):
    """Fetch historical exchange rates from the API."""
    try:
        params = {"days": days}
        if currency:
            params["currency"] = currency
        response = requests.get(f"{API_BASE_URL}/api/v1/rates/history", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch historical rates: {e}")
        return None


def convert_rates_to_base(rates_data, target_base_currency):
    """Convert rates from USD base to a different base currency.

    Args:
        rates_data: Historical rates data from API (all relative to USD)
        target_base_currency: The currency to use as the new base

    Returns:
        Converted rates data with new base currency
    """
    if not rates_data or not rates_data.get("rates"):
        return rates_data

    # If target base is USD, no conversion needed
    if target_base_currency == "USD":
        return rates_data

    # Get the base currency rate for each timestamp
    target_rates = []

    # Group rates by timestamp to find the base currency rate
    rates_by_timestamp = {}
    for rate in rates_data["rates"]:
        timestamp = rate["recorded_at"]
        if timestamp not in rates_by_timestamp:
            rates_by_timestamp[timestamp] = {}
        rates_by_timestamp[timestamp][rate["currency"]] = float(rate["rate"])

    # Convert each rate relative to the new base currency
    for timestamp, currencies in rates_by_timestamp.items():
        if target_base_currency not in currencies:
            continue  # Skip if base currency rate not available for this timestamp

        base_rate = currencies[target_base_currency]

        for currency, usd_rate in currencies.items():
            if currency != target_base_currency:
                # Convert from USD rate to new base currency rate
                # If 1 USD = X target_base and 1 USD = Y currency
                # Then 1 target_base = Y/X currency
                converted_rate = usd_rate / base_rate if base_rate != 0 else 0

                target_rates.append(
                    {"currency": currency, "rate": converted_rate, "recorded_at": timestamp}
                )

    return {"rates": target_rates}


# Load Testing API Functions
def get_load_test_status():
    """Get current load test status."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/status", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to get load test status: {e}")
        return None


def get_load_test_scenarios():
    """Get available load test scenarios."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/scenarios", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to get scenarios: {e}")
        return None


def get_scenario_details(scenario):
    """Get details for a specific scenario."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/scenarios/{scenario}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to get scenario details: {e}")
        return None


def start_load_test_scenario(scenario):
    """Start a load test scenario."""
    try:
        response = requests.post(
            f"{LOAD_TESTER_URL}/api/load-test/scenarios/{scenario}/start", timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to start load test: {e}")
        return None


def start_custom_load_test(config):
    """Start a custom load test."""
    try:
        payload = {"config": config}
        response = requests.post(f"{LOAD_TESTER_URL}/api/load-test/start", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to start custom load test: {e}")
        return None


def stop_load_test():
    """Stop the current load test."""
    try:
        response = requests.post(f"{LOAD_TESTER_URL}/api/load-test/stop", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to stop load test: {e}")
        return None


def get_load_test_report():
    """Get detailed load test report."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/api/load-test/report", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to get load test report: {e}")
        return None


def check_load_tester_health():
    """Check if load tester service is healthy."""
    try:
        response = requests.get(f"{LOAD_TESTER_URL}/", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Currency Conversion Dashboard",
        page_icon="💱",
        layout="wide",
    )

    st.title("💱 Currency Conversion Dashboard")
    st.markdown("A demo dashboard for the Currency Conversion API")

    # Check API health
    health = check_api_health()
    if health:
        st.success(f"✅ API is healthy - {health['service']}")
    else:
        st.error("❌ API is not accessible")
        st.stop()

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Currency Converter", "Exchange Rates", "Historical Trends", "Load Testing"],
    )

    if page == "Currency Converter":
        show_converter_page()
    elif page == "Exchange Rates":
        show_rates_page()
    elif page == "Historical Trends":
        show_historical_trends_page()
    elif page == "Load Testing":
        show_load_testing_page()


def show_converter_page():
    """Show the currency converter page."""
    st.header("💰 Currency Converter")

    # Get current rates for currency options
    rates_data = get_current_rates()
    if not rates_data:
        st.error("Unable to load currency data")
        return

    currencies = [rate["currency"] for rate in rates_data["rates"]]

    # Input form
    col1, col2, col3 = st.columns(3)

    with col1:
        amount = st.number_input(
            "Amount",
            min_value=0.01,
            value=100.0,
            step=0.01,
            format="%.2f",
        )

    with col2:
        from_currency = st.selectbox("From Currency", currencies, index=currencies.index("USD"))

    with col3:
        to_currency = st.selectbox("To Currency", currencies, index=currencies.index("EUR"))

    if st.button("Convert", type="primary"):
        if from_currency == to_currency:
            st.warning("Please select different currencies")
        else:
            result = convert_currency(amount, from_currency, to_currency)
            if result:
                st.success("✅ Conversion successful!")

                # Display result
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Original Amount",
                        f"{float(result['amount']):.2f} {result['from_currency']}",
                    )
                with col2:
                    st.metric(
                        "Converted Amount",
                        f"{float(result['converted_amount']):.2f} {result['to_currency']}",
                    )

                # Additional details
                st.subheader("Conversion Details")
                details_data = {
                    "Exchange Rate": f"{float(result['exchange_rate']):.6f}",
                    "Conversion ID": result["conversion_id"],
                    "Timestamp": result["conversion_timestamp"],
                    "Rate Source": result["metadata"]["rate_source"],
                }

                for key, value in details_data.items():
                    st.text(f"{key}: {value}")


def show_rates_page():
    """Show the exchange rates page."""
    st.header("📊 Current Exchange Rates")

    rates_data = get_current_rates()
    if not rates_data:
        st.error("Unable to load rates data")
        return

    st.info(
        f"Base Currency: {rates_data['base_currency']} | Last Updated: {rates_data['timestamp']}"
    )

    # Create DataFrame for better display
    rates_df = pd.DataFrame(rates_data["rates"])
    rates_df["rate"] = rates_df["rate"].astype(float)
    rates_df = rates_df.sort_values("currency")

    # Display rates table
    st.subheader("Exchange Rates Table")
    st.dataframe(
        rates_df,
        column_config={
            "currency": "Currency",
            "rate": st.column_config.NumberColumn("Rate (to USD)", format="%.6f"),
            "last_updated": "Last Updated",
        },
        hide_index=True,
        width="stretch",
    )


def show_historical_trends_page():
    """Show the historical trends page with time-series charts."""
    st.header("📈 Historical Exchange Rate Trends")

    st.info(
        "💡 **Base Currency Selection**: Choose your base currency to see how other currencies perform relative to it. "
        "For example, selecting EUR as base shows how many USD, GBP, etc. you get for 1 EUR. "
        "When you change the base currency, your selected currencies are preserved (with automatic swapping if needed)."
    )

    # Get current rates for currency options
    rates_data = get_current_rates()
    if not rates_data:
        st.error("Unable to load currency data")
        return

    currencies = [rate["currency"] for rate in rates_data["rates"]]

    # Initialize session state for currency management
    if "previous_base_currency" not in st.session_state:
        st.session_state.previous_base_currency = "USD"
    if "previous_selected_currencies" not in st.session_state:
        st.session_state.previous_selected_currencies = ["EUR", "GBP"]

    # Controls for historical data
    col1, col2, col3 = st.columns(3)

    with col1:
        base_currency = st.selectbox(
            "Base currency",
            currencies,
            index=currencies.index("USD") if "USD" in currencies else 0,
            help="Currency to use as the base for rate calculations",
        )

    # Handle base currency change logic
    if base_currency != st.session_state.previous_base_currency:
        old_base = st.session_state.previous_base_currency
        old_selected = st.session_state.previous_selected_currencies.copy()

        # Check if the new base currency was in the selected currencies
        if base_currency in old_selected:
            # Remove new base from selected and add old base
            new_selected = [c for c in old_selected if c != base_currency]
            if old_base not in new_selected:
                new_selected.append(old_base)
        else:
            # Keep existing selected currencies (they'll be filtered below)
            new_selected = old_selected.copy()

        # Update session state
        st.session_state.previous_base_currency = base_currency
        st.session_state.previous_selected_currencies = new_selected

    with col2:
        # Filter out the base currency from target currencies
        available_currencies = [c for c in currencies if c != base_currency]

        # Determine default selection
        if base_currency == st.session_state.previous_base_currency:
            # No base currency change, use stored selection
            current_default = [
                c
                for c in st.session_state.previous_selected_currencies
                if c in available_currencies
            ]
        else:
            # Base currency just changed, use the updated selection
            current_default = [
                c
                for c in st.session_state.previous_selected_currencies
                if c in available_currencies
            ]

        # If no valid defaults, use fallback
        if not current_default:
            current_default = (
                available_currencies[:2] if len(available_currencies) >= 2 else available_currencies
            )

        selected_currencies = st.multiselect(
            "Select currencies to view",
            available_currencies,
            default=current_default,
            help="Choose currencies to display in the time-series chart",
        )

        # Update session state with current selection
        st.session_state.previous_selected_currencies = selected_currencies

    with col3:
        days = st.selectbox(
            "Time period",
            [7, 14, 30, 60, 90],
            index=2,
            help="Number of days of historical data to display",
        )

    if not selected_currencies:
        st.warning("Please select at least one currency to display trends.")
        return

    # Fetch and display historical data for each currency
    st.subheader("Time-Series Rate Charts")

    if len(selected_currencies) == 1:
        # Single currency detailed view
        currency = selected_currencies[0]

        # Get historical data for all currencies to enable base currency conversion
        if base_currency == "USD":
            history_data = get_rates_history(currency=currency, days=days)
        else:
            # Need all currencies to convert to different base
            history_data = get_rates_history(days=days)
            history_data = convert_rates_to_base(history_data, base_currency)
            # Filter to selected currency after conversion
            if history_data and history_data.get("rates"):
                history_data["rates"] = [
                    r for r in history_data["rates"] if r["currency"] == currency
                ]

        if history_data and history_data["rates"]:
            # Create DataFrame for plotting
            df_history = pd.DataFrame(
                [
                    {
                        "date": rate["recorded_at"][:10],  # Extract date part
                        "datetime": pd.to_datetime(rate["recorded_at"]),
                        "rate": float(rate["rate"]),
                        "currency": rate["currency"],
                    }
                    for rate in history_data["rates"]
                ]
            )

            # Sort by datetime
            df_history = df_history.sort_values("datetime")

            # Create line chart
            fig = px.line(
                df_history,
                x="datetime",
                y="rate",
                title=f"{currency} Exchange Rate Trend vs {base_currency} (Last {days} days)",
                labels={"rate": f"Rate (relative to {base_currency})", "datetime": "Date"},
                line_shape="linear",
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, width="stretch")

            # Display statistics
            col1, col2, col3, col4 = st.columns(4)

            rates_list = df_history["rate"].tolist()
            current_rate = rates_list[-1] if rates_list else 0
            min_rate = df_history["rate"].min()
            max_rate = df_history["rate"].max()
            avg_rate = df_history["rate"].mean()

            with col1:
                st.metric("Current Rate", f"{current_rate:.6f}")
            with col2:
                st.metric("Minimum", f"{min_rate:.6f}")
            with col3:
                st.metric("Maximum", f"{max_rate:.6f}")
            with col4:
                st.metric("Average", f"{avg_rate:.6f}")

        else:
            st.info(f"No historical data available for {currency}")

    else:
        # Multiple currencies comparison
        all_rates_data = []

        if base_currency == "USD":
            # Fetch each currency individually when USD is base
            for currency in selected_currencies:
                history_data = get_rates_history(currency=currency, days=days)

                if history_data and history_data["rates"]:
                    for rate in history_data["rates"]:
                        all_rates_data.append(
                            {
                                "datetime": pd.to_datetime(rate["recorded_at"]),
                                "rate": float(rate["rate"]),
                                "currency": rate["currency"],
                            }
                        )
        else:
            # Fetch all currencies and convert to new base currency
            history_data = get_rates_history(days=days)
            history_data = convert_rates_to_base(history_data, base_currency)

            if history_data and history_data["rates"]:
                for rate in history_data["rates"]:
                    if rate["currency"] in selected_currencies:
                        all_rates_data.append(
                            {
                                "datetime": pd.to_datetime(rate["recorded_at"]),
                                "rate": float(rate["rate"]),
                                "currency": rate["currency"],
                            }
                        )

        if all_rates_data:
            df_all = pd.DataFrame(all_rates_data)
            df_all = df_all.sort_values("datetime")

            # Create multi-line chart
            fig = px.line(
                df_all,
                x="datetime",
                y="rate",
                color="currency",
                title=f"Exchange Rate Trends vs {base_currency} (Last {days} days)",
                labels={"rate": f"Rate (relative to {base_currency})", "datetime": "Date"},
                line_shape="linear",
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, width="stretch")

            # Summary table
            st.subheader("Rate Summary")
            summary_data = []

            for currency in selected_currencies:
                currency_data = df_all[df_all["currency"] == currency]
                if not currency_data.empty:
                    rates = currency_data["rate"].tolist()
                    current_rate = rates[-1] if rates else 0

                    summary_data.append(
                        {
                            "Currency": currency,
                            "Current Rate": f"{current_rate:.6f}",
                            "Min Rate": f"{currency_data['rate'].min():.6f}",
                            "Max Rate": f"{currency_data['rate'].max():.6f}",
                            "Avg Rate": f"{currency_data['rate'].mean():.6f}",
                            "Records": len(currency_data),
                        }
                    )

            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, width="stretch")

        else:
            st.info("No historical data available for the selected currencies.")

    # Note about data
    st.info(
        "📊 Historical data is simulated for demonstration purposes. In a production system, this would connect to real exchange rate data sources."
    )


def show_load_testing_page():
    """Show the load testing control and monitoring page."""
    st.header("🔥 Load Testing Dashboard")

    # Check load tester health
    load_tester_health = check_load_tester_health()
    if not load_tester_health:
        st.error("❌ Load Tester service is not accessible")
        st.info("Make sure the Load Tester service is running at http://localhost:8001")
        return

    st.success(
        f"✅ Load Tester service is healthy - {load_tester_health.get('message', 'Unknown')}"
    )

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
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Target RPS", status["config"]["requests_per_second"])
            with col2:
                st.metric("Currency Pairs", len(status["config"]["currency_pairs"]))
            with col3:
                st.metric("Test Amounts", len(status["config"]["amounts"]))

        # Live statistics
        if status.get("stats"):
            st.subheader("📈 Live Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Requests", status["stats"]["total_requests"])
            with col2:
                success_rate = (
                    status["stats"]["successful_requests"]
                    / max(status["stats"]["total_requests"], 1)
                ) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
            with col3:
                st.metric("Avg Response Time", f"{status['stats']['avg_response_time_ms']:.1f}ms")
            with col4:
                st.metric("Current RPS", f"{status['stats']['requests_per_second']:.2f}")

        # Auto-refresh for running tests
        if status["status"] == "running":
            st.rerun()

    # Control Panel
    st.subheader("🎮 Test Control Panel")

    if status["status"] in ["running", "starting", "stopping"]:
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

                ramp_currency_pairs = st.multiselect(
                    "Currency Pairs",
                    [
                        "USD_EUR",
                        "USD_GBP",
                        "EUR_GBP",
                        "USD_JPY",
                        "USD_CAD",
                        "USD_AUD",
                        "USD_CHF",
                        "USD_CNY",
                        "USD_SEK",
                        "USD_NZD",
                    ],
                    default=current_config.get("currency_pairs", ["USD_EUR", "USD_GBP"]),
                    help="Update currency pairs to test",
                    key="ramp_currency_pairs",
                )

            with col2:
                ramp_amounts = st.multiselect(
                    "Test Amounts",
                    [10.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0],
                    default=current_config.get("amounts", [100.0, 500.0, 1000.0]),
                    help="Update transaction amounts to test",
                    key="ramp_amounts",
                )

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

    else:
        # Show start options for inactive tests
        tab1, tab2 = st.tabs(["📋 Scenario Tests", "⚙️ Custom Test"])

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
                            st.metric(
                                "Currency Pairs", len(scenario_details["config"]["currency_pairs"])
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

                currency_pairs = st.multiselect(
                    "Currency Pairs",
                    [
                        "USD_EUR",
                        "USD_GBP",
                        "EUR_GBP",
                        "USD_JPY",
                        "USD_CAD",
                        "USD_AUD",
                        "USD_CHF",
                        "USD_CNY",
                        "USD_SEK",
                        "USD_NZD",
                    ],
                    default=["USD_EUR", "USD_GBP"],
                    help="Currency pairs to test",
                )

            with col2:
                amounts = st.multiselect(
                    "Test Amounts",
                    [10.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0],
                    default=[100.0, 500.0, 1000.0],
                    help="Transaction amounts to test",
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

    # Test Results and Analysis
    st.subheader("📊 Test Analysis & Results")

    if status["status"] in ["stopped", "error"] or st.button("🔄 Refresh Report"):
        report = get_load_test_report()
        if report and report.get("stats", {}).get("total_requests", 0) > 0:
            # Performance Grade
            grade_color = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴", "F": "⚫"}.get(
                report["performance_grade"], "⚪"
            )

            st.success(f"{grade_color} **Performance Grade: {report['performance_grade']}**")

            # Key Metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Requests", f"{report['stats']['total_requests']:,}")
            with col2:
                st.metric("Success Rate", f"{report['success_rate']:.1f}%")
            with col3:
                st.metric("Avg Response Time", f"{report['stats']['avg_response_time_ms']:.1f}ms")
            with col4:
                st.metric("Achieved RPS", f"{report['avg_rps_achieved']:.2f}")

            # Performance Chart
            if report["stats"]["total_requests"] > 0:
                chart_data = pd.DataFrame(
                    {
                        "Metric": ["Successful", "Failed"],
                        "Count": [
                            report["stats"]["successful_requests"],
                            report["stats"]["failed_requests"],
                        ],
                        "Percentage": [report["success_rate"], 100 - report["success_rate"]],
                    }
                )

                fig = px.pie(
                    chart_data,
                    values="Count",
                    names="Metric",
                    title="Request Success/Failure Distribution",
                    color_discrete_map={"Successful": "#28a745", "Failed": "#dc3545"},
                )
                st.plotly_chart(fig, use_container_width=True)

            # Recommendations
            if report.get("recommendations"):
                st.subheader("💡 Performance Recommendations")
                for i, rec in enumerate(report["recommendations"], 1):
                    st.info(f"**{i}.** {rec}")

            # Detailed Stats
            with st.expander("📋 Detailed Statistics"):
                stats_data = {
                    "Metric": [
                        "Total Requests",
                        "Successful Requests",
                        "Failed Requests",
                        "Average Response Time",
                        "Minimum Response Time",
                        "Maximum Response Time",
                        "Target RPS",
                        "Achieved RPS",
                    ],
                    "Value": [
                        f"{report['stats']['total_requests']:,}",
                        f"{report['stats']['successful_requests']:,}",
                        f"{report['stats']['failed_requests']:,}",
                        f"{report['stats']['avg_response_time_ms']:.1f}ms",
                        f"{report['stats']['min_response_time_ms']:.1f}ms",
                        f"{report['stats']['max_response_time_ms']:.1f}ms",
                        f"{report['requests_per_second']:.1f}",
                        f"{report['avg_rps_achieved']:.2f}",
                    ],
                }
                st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
        else:
            st.info("No test results available. Run a load test to see performance analysis.")

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


if __name__ == "__main__":
    main()
