import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

def safe_get_value(df, row_name, position=0):
    """Safely get value from financial statements"""
    try:
        if row_name in df.index:
            return df.iloc[position][row_name]
        return 0
    except:
        return 0

def fetch_financial_metrics(ticker):
    """Fetch and calculate financial metrics for a given ticker"""
    try:
        # Add delay between requests to avoid rate limiting
        time.sleep(1)
        
        stock = yf.Ticker(ticker)
        
        # Get financial statements with retries
        max_retries = 3
        for _ in range(max_retries):
            try:
                income_stmt = stock.income_stmt
                balance_sheet = stock.balance_sheet
                cashflow = stock.cash_flow
                info = stock.info
                break
            except Exception as e:
                st.warning(f"Retrying data fetch for {ticker}...")
                time.sleep(2)
        else:
            st.error(f"Failed to fetch data for {ticker} after {max_retries} attempts")
            return None
        
        # Current market data
        market_price = info.get('currentPrice', np.nan)
        market_cap = info.get('marketCap', np.nan)
        
        # Calculate metrics using safe getter
        latest_revenue = safe_get_value(income_stmt, 'Total Revenue')
        prev_revenue = safe_get_value(income_stmt, 'Total Revenue', 1)
        
        # Revenue Growth
        revenue_growth = ((latest_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue != 0 else 0
        
        # ROCE
        operating_profit = safe_get_value(income_stmt, 'Operating Income')
        if operating_profit == 0:
            operating_profit = safe_get_value(income_stmt, 'EBIT')
            
        total_assets = safe_get_value(balance_sheet, 'Total Assets')
        current_liabilities = safe_get_value(balance_sheet, 'Total Current Liabilities')
        capital_employed = total_assets - current_liabilities
        roce = (operating_profit / capital_employed * 100) if capital_employed != 0 else 0
        
        # Gross Margin
        gross_profit = safe_get_value(income_stmt, 'Gross Profit')
        gross_margin = (gross_profit / latest_revenue * 100) if latest_revenue != 0 else 0
        
        # Operating Profit Margin
        operating_margin = (operating_profit / latest_revenue * 100) if latest_revenue != 0 else 0
        
        # Cash Conversion
        operating_cash_flow = safe_get_value(cashflow, 'Operating Cash Flow')
        cash_conversion = (latest_revenue / operating_cash_flow * 100) if operating_cash_flow != 0 else 0
        
        # Leverage
        total_debt = safe_get_value(balance_sheet, 'Total Debt')
        if total_debt == 0:
            total_debt = safe_get_value(balance_sheet, 'Long Term Debt') + safe_get_value(balance_sheet, 'Short Term Debt')
            
        total_equity = safe_get_value(balance_sheet, 'Total Stockholder Equity')
        leverage = (total_debt / total_equity * 100) if total_equity != 0 else 0
        
        # Interest Coverage
        interest_expense = abs(safe_get_value(income_stmt, 'Interest Expense'))
        interest_coverage = (operating_profit / interest_expense) if interest_expense != 0 else 0
        
        return {
            'Ticker': ticker,
            'Market Price': market_price,
            'Market Cap': market_cap,
            'Revenue Growth (%)': revenue_growth,
            'ROCE (%)': roce,
            'Gross Margin (%)': gross_margin,
            'Operating Margin (%)': operating_margin,
            'Cash Conversion (%)': cash_conversion,
            'Leverage (%)': leverage,
            'Interest Coverage': interest_coverage
        }
    except Exception as e:
        st.error(f"Error processing {ticker}: {str(e)}")
        return None

def get_cell_color(value, metric):
    """Determine cell background color based on metric thresholds"""
    if pd.isna(value):
        return ''
        
    colors = {
        'ROCE (%)': [(20, 'lightgreen'), (25, 'darkgreen')],
        'Gross Margin (%)': [(50, 'lightgreen'), (75, 'darkgreen')],
        'Operating Margin (%)': [(20, 'lightgreen'), (25, 'darkgreen')],
        'Cash Conversion (%)': [(98, 'lightgreen'), (100, 'darkgreen')],
        'Leverage (%)': [(25, 'lightgreen'), (40, 'darkgreen')],
        'Interest Coverage': [(14, 'lightgreen'), (16, 'darkgreen')]
    }
    
    if metric in colors:
        thresholds = colors[metric]
        for threshold, color in reversed(thresholds):
            if value > threshold:
                return f'background-color: {color}'
    return ''

def apply_style(row, columns):
    """Apply styling to each cell in the row"""
    styles = []
    for col_name, val in row.items():
        if col_name in columns:
            try:
                # Clean the value string and convert to float
                clean_val = str(val).replace('$', '').replace(',', '').replace('%', '')
                if any(c.isdigit() for c in clean_val):
                    num_val = float(clean_val)
                    styles.append(get_cell_color(num_val, col_name))
                else:
                    styles.append('')
            except:
                styles.append('')
        else:
            styles.append('')
    return styles

def main():
    st.title("Terry Smith Investment Analysis")
    
    # Input for tickers
    tickers_input = st.text_input("Enter stock tickers (comma-separated)", "AAPL,MSFT,GOOGL")
    
    if st.button("Analyze"):
        tickers = [ticker.strip() for ticker in tickers_input.split(',')]
        
        # Create progress bar
        progress_bar = st.progress(0)
        
        # Process each ticker
        results = []
        for i, ticker in enumerate(tickers):
            st.write(f"Processing {ticker}...")
            result = fetch_financial_metrics(ticker)
            if result:
                results.append(result)
            progress_bar.progress((i + 1) / len(tickers))
        
        if results:
            # Create DataFrame
            df = pd.DataFrame(results)
            
            # Format numbers
            format_dict = {
                'Market Price': '${:,.2f}',
                'Market Cap': '${:,.0f}',
                'Revenue Growth (%)': '{:.1f}%',
                'ROCE (%)': '{:.1f}%',
                'Gross Margin (%)': '{:.1f}%',
                'Operating Margin (%)': '{:.1f}%',
                'Cash Conversion (%)': '{:.1f}%',
                'Leverage (%)': '{:.1f}%',
                'Interest Coverage': '{:.1f}'
            }
            
            for col, format_str in format_dict.items():
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: format_str.format(x) if pd.notnull(x) else 'N/A')
            
            # Apply styling
            styled_df = df.style.apply(
                apply_style,
                columns=df.columns,
                axis=1
            )
            
            st.dataframe(styled_df)

if __name__ == "__main__":
    main()
