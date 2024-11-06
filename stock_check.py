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
            gross_profits = info.get("grossProfits")
            operating_cashflow = info.get("operatingCashflow")
            total_debt = info.get("totalDebt")
            total_assets = info.get("totalAssets")
            total_current_liabilities = info.get("totalCurrentLiabilities")
            total_stockholder_equity = info.get("totalStockholderEquity")
            interest_expense = info.get("interestExpense")
            ebit = info.get("ebit")  # Operating Profit / EBIT

            # Calculate metrics with additional None checks to avoid errors
            metrics_dict = {}
            
            # 1. Interest Coverage Ratio: Operating Profit / Interest Expense
            if ebit is not None and interest_expense is not None and interest_expense != 0:
                metrics_dict["Interest Coverage"] = ebit / interest_expense
            else:
                metrics_dict["Interest Coverage"] = None  # Avoid division by zero or missing data

            # 2. Leverage Ratio: Total Debt / Total Equity
            if total_debt is not None and total_stockholder_equity is not None and total_stockholder_equity != 0:
                metrics_dict["Leverage (%)"] = (total_debt / total_stockholder_equity) * 100
            else:
                metrics_dict["Leverage (%)"] = None  # Avoid division by zero or missing data

            # 3. Operating Profit (EBIT) Margin: (Operating Profit / Revenue) * 100
            if ebit is not None and total_revenue is not None and total_revenue != 0:
                metrics_dict["Operating Profit Margin (%)"] = (ebit / total_revenue) * 100
            else:
                metrics_dict["Operating Profit Margin (%)"] = None  # Avoid division by zero or missing data

            # 4. Gross Margin: (Gross Profit / Revenue) * 100
            if gross_profits is not None and total_revenue is not None and total_revenue != 0:
                metrics_dict["Gross Margin (%)"] = (gross_profits / total_revenue) * 100
            else:
                metrics_dict["Gross Margin (%)"] = None  # Avoid division by zero or missing data

            # 5. Return on Capital Employed (ROCE): (Operating Profit / Capital Employed) * 100
            if ebit is not None and total_assets is not None and total_current_liabilities is not None:
                capital_employed = total_assets - total_current_liabilities
                if capital_employed != 0:
                    metrics_dict["ROCE (%)"] = (ebit / capital_employed) * 100
                else:
                    metrics_dict["ROCE (%)"] = None  # Avoid division by zero or missing data
            else:
                metrics_dict["ROCE (%)"] = None

            # 6. Cash Conversion Ratio: (Net Sales / Operating Cash Flow) * 100
            if total_revenue is not None and operating_cashflow is not None and operating_cashflow != 0:
                metrics_dict["Cash Conversion (%)"] = (total_revenue / operating_cashflow) * 100
            else:
                metrics_dict["Cash Conversion (%)"] = None  # Avoid division by zero or missing data

            # Append data to metrics
            metrics.append([
                ticker, price, market_cap, 
                info.get("revenueGrowth") * 100 if info.get("revenueGrowth") is not None else None,
                metrics_dict["ROCE (%)"], 
                metrics_dict["Gross Margin (%)"], 
                metrics_dict["Operating Profit Margin (%)"], 
                metrics_dict["Cash Conversion (%)"], 
                metrics_dict["Leverage (%)"], 
                metrics_dict["Interest Coverage"]
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
        if pd.notna(val):  # Only apply if val is not None or NaN
            if val > threshold_2:
                return f"background-color: {color_dark}"
            elif val > threshold_1:
                return f"background-color: {color_light}"
        return ""

    def highlight_metrics(row):
        # Specify the conditions for each column requiring color coding
        colors = {
            "ROCE (%)": (20, 25, "lightgreen", "darkgreen"),
            "Gross Margin (%)": (50, 75, "lightgreen", "darkgreen"),
            "Operating Profit Margin (%)": (20, 25, "lightgreen", "darkgreen"),
            "Cash Conversion (%)": (98, 100, "lightgreen", "darkgreen"),
            "Leverage (%)": (25, 40, "lightgreen", "darkgreen"),
            "Interest Cover": (14, 16, "lightgreen", "darkgreen"),
        }
        
        # Apply colors to each column in the row
        styles = []
        for column in row.index:
            if column in colors:
                threshold_1, threshold_2, color_light, color_dark = colors[column]
                styles.append(apply_colors(row[column], threshold_1, threshold_2, color_light, color_dark))
            else:
                styles.append("")  # No styling for columns without conditions
        return styles

    # Apply highlighting function and ensure correct row-wise application
    styled_data = data.style.apply(highlight_metrics, axis=1)

    # Display the styled dataframe
    st.dataframe(styled_data)
