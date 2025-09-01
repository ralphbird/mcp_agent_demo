"""Streamlit dashboard for currency conversion API."""

import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


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
        ["Currency Converter", "Exchange Rates", "Historical Trends"],
    )

    if page == "Currency Converter":
        show_converter_page()
    elif page == "Exchange Rates":
        show_rates_page()
    elif page == "Historical Trends":
        show_historical_trends_page()


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

    # Get current rates for currency options
    rates_data = get_current_rates()
    if not rates_data:
        st.error("Unable to load currency data")
        return

    currencies = [rate["currency"] for rate in rates_data["rates"]]

    # Controls for historical data
    col1, col2 = st.columns(2)

    with col1:
        selected_currencies = st.multiselect(
            "Select currencies to view",
            currencies,
            default=["USD", "EUR", "GBP", "JPY"],
            help="Choose currencies to display in the time-series chart",
        )

    with col2:
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
        history_data = get_rates_history(currency=currency, days=days)

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
                title=f"{currency} Exchange Rate Trend (Last {days} days)",
                labels={"rate": "Rate (relative to USD)", "datetime": "Date"},
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

        if all_rates_data:
            df_all = pd.DataFrame(all_rates_data)
            df_all = df_all.sort_values("datetime")

            # Create multi-line chart
            fig = px.line(
                df_all,
                x="datetime",
                y="rate",
                color="currency",
                title=f"Exchange Rate Trends Comparison (Last {days} days)",
                labels={"rate": "Rate (relative to USD)", "datetime": "Date"},
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


if __name__ == "__main__":
    main()
