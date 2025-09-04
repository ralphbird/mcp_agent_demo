"""Historical trends page."""

from typing import cast

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.utils import convert_rates_to_base, get_current_rates, get_rates_history


def show_historical_trends_page():
    """Show the historical trends page with time-series charts."""
    st.header("📈 Historical Exchange Rate Trends")

    # Get available currencies
    rates_data = get_current_rates()
    if not rates_data:
        st.error("Unable to load currency data")
        return

    currencies = [rate["currency"] for rate in rates_data["rates"]]

    # Controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        base_currency = st.selectbox(
            "Base Currency",
            currencies,
            index=currencies.index("USD"),
            help="Currency to compare against (rates will be relative to this currency)",
        )

    with col2:
        days = st.selectbox("Time Period", [7, 14, 30], index=2, help="Number of days of history")

    with col3:
        chart_type = st.selectbox("View Type", ["Single Currency", "Multiple Currencies"])

    with col4:
        if chart_type == "Single Currency":
            selected_currencies = [
                st.selectbox("Currency", [c for c in currencies if c != base_currency])
            ]
        else:
            # For multiple currencies, exclude the base currency
            available_currencies = [c for c in currencies if c != base_currency]
            selected_currencies = st.multiselect(
                "Currencies",
                available_currencies,
                default=available_currencies[:3],  # Select first 3 by default
                help="Select multiple currencies to compare",
            )

    if not selected_currencies:
        st.warning("Please select at least one currency to display.")
        return

    st.subheader(f"Exchange Rate Trends (Base: {base_currency})")

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
            st.plotly_chart(fig, use_container_width=True)

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
                title=f"Exchange Rate Comparison vs {base_currency} (Last {days} days)",
                labels={"rate": f"Rate (relative to {base_currency})", "datetime": "Date"},
                line_shape="linear",
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

            # Summary statistics table
            if len(selected_currencies) > 1:
                summary_stats = []
                for currency in selected_currencies:
                    currency_data = cast(pd.Series, df_all[df_all["currency"] == currency]["rate"])
                    if len(currency_data):
                        summary_stats.append(
                            {
                                "Currency": currency,
                                "Current": f"{currency_data.iloc[-1]:.6f}",
                                "Min": f"{currency_data.min():.6f}",
                                "Max": f"{currency_data.max():.6f}",
                                "Avg": f"{currency_data.mean():.6f}",
                                "Volatility": f"{currency_data.std():.6f}",
                            }
                        )

                if summary_stats:
                    st.subheader("Summary Statistics")
                    st.dataframe(pd.DataFrame(summary_stats), use_container_width=True)
        else:
            st.info("No historical data available for the selected currencies")
