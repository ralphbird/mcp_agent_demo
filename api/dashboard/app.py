"""Streamlit dashboard for currency conversion API."""

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# API Configuration
API_BASE_URL = "http://localhost:8000"


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
        response = requests.get(f"{API_BASE_URL}/health")
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
        "Choose a page", ["Currency Converter", "Exchange Rates", "Rate Charts"]
    )

    if page == "Currency Converter":
        show_converter_page()
    elif page == "Exchange Rates":
        show_rates_page()
    elif page == "Rate Charts":
        show_charts_page()


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
        use_container_width=True,
    )

    # Rate comparison
    st.subheader("Rate Comparison")
    selected_currencies = st.multiselect(
        "Select currencies to compare",
        rates_df["currency"].tolist(),
        default=["USD", "EUR", "GBP", "JPY"],
    )

    if selected_currencies:
        filtered_df = rates_df[rates_df["currency"].isin(selected_currencies)]

        # Create horizontal bar chart
        fig = px.bar(
            filtered_df,
            x="rate",
            y="currency",
            orientation="h",
            title="Exchange Rates Comparison (Relative to USD)",
            labels={"rate": "Exchange Rate", "currency": "Currency"},
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def show_charts_page():
    """Show the rate charts page."""
    st.header("📈 Exchange Rate Visualizations")

    rates_data = get_current_rates()
    if not rates_data:
        st.error("Unable to load rates data")
        return

    rates_df = pd.DataFrame(rates_data["rates"])
    rates_df["rate"] = rates_df["rate"].astype(float)

    # Currency strength vs USD
    st.subheader("Currency Strength vs USD")

    # Separate currencies stronger and weaker than USD
    stronger_than_usd = rates_df[rates_df["rate"] < 1.0].copy()
    weaker_than_usd = rates_df[rates_df["rate"] > 1.0].copy()

    col1, col2 = st.columns(2)

    with col1:
        if not stronger_than_usd.empty:
            st.write("**Stronger than USD** (rate < 1.0)")
            fig1 = px.bar(
                stronger_than_usd,
                x="currency",
                y="rate",
                title="Currencies Stronger than USD",
                color="rate",
                color_continuous_scale="greens",
            )
            st.plotly_chart(fig1, use_container_width=True)

    with col2:
        if not weaker_than_usd.empty:
            st.write("**Weaker than USD** (rate > 1.0)")
            fig2 = px.bar(
                weaker_than_usd,
                x="currency",
                y="rate",
                title="Currencies Weaker than USD",
                color="rate",
                color_continuous_scale="reds",
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Pie chart of relative values
    st.subheader("Relative Currency Distribution")

    # For pie chart, we'll use inverse rates to show relative strength
    rates_df["inverse_rate"] = 1 / rates_df["rate"]

    fig3 = px.pie(
        rates_df,
        values="inverse_rate",
        names="currency",
        title="Relative Currency Values (Inverse Rates)",
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Summary statistics
    st.subheader("Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Currencies", len(rates_df))

    with col2:
        st.metric("Strongest Currency", rates_df.loc[rates_df["rate"].idxmin(), "currency"])

    with col3:
        st.metric("Weakest Currency", rates_df.loc[rates_df["rate"].idxmax(), "currency"])

    with col4:
        st.metric("Average Rate", f"{rates_df['rate'].mean():.4f}")


if __name__ == "__main__":
    main()
