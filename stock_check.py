import streamlit as st
import yfinance as yf
import pandas as pd

# Set Streamlit page title and layout
st.title("Terry Smith's Investment Metrics App")
st.markdown("Add tickers separated by commas and click search to view metrics.")

# Input section for comma-separated tickers
tickers_input = st.text_input("Enter Tickers (comma-separated)", "AAPL, MSFT, GOOGL")
tickers = [ticker.strip().upper() for ticker in tickers_input.split(",")]

# Define metrics calculations
def calculate_metrics(data):
    metrics = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Retrieve required financial data
            price = info.get("currentPrice")
            market_cap = info.get("marketCap")
            total_revenue = info.get("totalRevenue")
            gross_profit = info.get("grossProfits")
            operating_cashflow = info.get("operatingCashflow")
            total_debt = info.get("totalDebt")
            total_assets = info.get("totalAssets")
            current_liabilities = info.get("totalCurrentLiabilities")
            total_equity = info.get("totalStockholderEquity")
            interest_expense = info.get("interestExpense")
            operating_income = info.get("ebit")

            # Calculate metrics
            revenue_growth = (info.get("revenueGrowth") or 0) * 100
            gross_margin = (gross_profit / total_revenue * 100) if gross_profit and total_revenue else None
            operating_profit_margin = (operating_income / total_revenue * 100) if operating_income and total_revenue else None
            roce = (operating_income / (total_assets - current_liabilities) * 100) if operating_income and total_assets and current_liabilities else None
            cash_conversion = (operating_cashflow / total_revenue * 100) if operating_cashflow and total_revenue else None
            leverage_ratio = (total_debt / total_equity * 100) if total_debt and total_equity else None
            interest_cover = (operating_income / interest_expense) if operating_income and interest_expense else None

            metrics.append([
                ticker, price, market_cap, revenue_growth, roce, gross_margin, operating_profit_margin, cash_conversion, leverage_ratio, interest_cover
            ])
        except Exception as e:
            st.write(f"Error retrieving data for {ticker}: {e}")

    return pd.DataFrame(metrics, columns=[
        "Ticker", "Market Price", "Market Cap", "Total Revenue Growth (%)", 
        "ROCE (%)", "Gross Margin (%)", "Operating Profit Margin (%)", 
        "Cash Conversion (%)", "Leverage (%)", "Interest Cover"
    ])

# Button to calculate and display metrics
if st.button("Search"):
    data = calculate_metrics(tickers)

    # Color the metrics based on conditions
    def apply_colors(val, threshold_1, threshold_2, color_light, color_dark):
        if val is not None:
            if val > threshold_2:
                return f"background-color: {color_dark}"
            elif val > threshold_1:
                return f"background-color: {color_light}"
        return ""

    def highlight_metrics(row):
        colors = {
            "ROCE (%)": (20, 25, "lightgreen", "darkgreen"),
            "Gross Margin (%)": (50, 75, "lightgreen", "darkgreen"),
            "Operating Profit Margin (%)": (20, 25, "lightgreen", "darkgreen"),
            "Cash Conversion (%)": (98, 100, "lightgreen", "darkgreen"),
            "Leverage (%)": (25, 40, "lightgreen", "darkgreen"),
            "Interest Cover": (14, 16, "lightgreen", "darkgreen"),
        }
        styles = []
        for column, (threshold_1, threshold_2, color_light, color_dark) in colors.items():
            val = row[column]
            styles.append(apply_colors(val, threshold_1, threshold_2, color_light, color_dark))
        return styles

    styled_data = data.style.apply(highlight_metrics, axis=1)

    # Display the styled dataframe
    st.write(styled_data, unsafe_allow_html=True)
