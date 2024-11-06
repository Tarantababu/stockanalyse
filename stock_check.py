import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

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
                # Get the financial data
                financials = stock.financials
                balance_sheet = stock.balance_sheet
                cashflow = stock.cashflow
                info = stock.info
                
                # Get the most recent values (first column)
                ebit = financials.loc['Operating Income', financials.columns[0]]
                interest_expense = abs(financials.loc['Interest Expense', financials.columns[0]])
                total_revenue = financials.loc['Total Revenue', financials.columns[0]]
                gross_profits = financials.loc['Gross Profit', financials.columns[0]]
                
                # Balance sheet items
                total_assets = balance_sheet.loc['Total Assets', balance_sheet.columns[0]]
                total_current_liabilities = balance_sheet.loc['Total Current Liabilities', balance_sheet.columns[0]]
                total_debt = balance_sheet.loc['Total Debt', balance_sheet.columns[0]]
                total_stockholder_equity = balance_sheet.loc['Total Stockholder Equity', balance_sheet.columns[0]]
                
                # Cash flow items
                operating_cashflow = cashflow.loc['Operating Cash Flow', cashflow.columns[0]]
                
                # Current market data
                market_price = info.get('currentPrice', np.nan)
                market_cap = info.get('marketCap', np.nan)
                
                # Calculate metrics exactly as specified
                metrics = {
                    'Ticker': ticker,
                    'Market Price': market_price,
                    'Market Cap': market_cap
                }
                
                # 1. Interest Coverage Ratio
                if interest_expense != 0:
                    metrics["Interest Coverage"] = ebit / interest_expense
                else:
                    metrics["Interest Coverage"] = None
                
                # 2. Leverage Ratio
                if total_stockholder_equity != 0:
                    metrics["Leverage (%)"] = (total_debt / total_stockholder_equity) * 100
                else:
                    metrics["Leverage (%)"] = None
                
                # 3. Operating Profit (EBIT) Margin
                if total_revenue != 0:
                    metrics["Operating Margin (%)"] = (ebit / total_revenue) * 100
                else:
                    metrics["Operating Margin (%)"] = None
                
                # 4. Gross Margin
                if total_revenue != 0:
                    metrics["Gross Margin (%)"] = (gross_profits / total_revenue) * 100
                else:
                    metrics["Gross Margin (%)"] = None
                
                # 5. Return on Capital Employed (ROCE)
                capital_employed = total_assets - total_current_liabilities
                if capital_employed != 0:
                    metrics["ROCE (%)"] = (ebit / capital_employed) * 100
                else:
                    metrics["ROCE (%)"] = None
                
                # 6. Cash Conversion Ratio
                if operating_cashflow != 0:
                    metrics["Cash Conversion (%)"] = (total_revenue / operating_cashflow) * 100
                else:
                    metrics["Cash Conversion (%)"] = None
                
                # Calculate Revenue Growth
                if len(financials.columns) >= 2:
                    prev_revenue = financials.loc['Total Revenue', financials.columns[1]]
                    if prev_revenue != 0:
                        metrics["Revenue Growth (%)"] = ((total_revenue - prev_revenue) / prev_revenue) * 100
                    else:
                        metrics["Revenue Growth (%)"] = None
                else:
                    metrics["Revenue Growth (%)"] = None
                
                return metrics
                
            except Exception as e:
                st.warning(f"Retrying data fetch for {ticker}... ({str(e)})")
                time.sleep(2)
        else:
            st.error(f"Failed to fetch data for {ticker} after {max_retries} attempts")
            return None

    except Exception as e:
        st.error(f"Error processing {ticker}: {str(e)}")
        return None

def get_cell_color(value, metric):
    """Determine cell background color based on metric thresholds"""
    if pd.isna(value) or value is None:
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
                if pd.isna(val) or val == 'N/A':
                    styles.append('')
                else:
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
                    df[col] = df[col].apply(lambda x: format_str.format(x) if pd.notnull(x) and x is not None else 'N/A')
            
            # Apply styling
            styled_df = df.style.apply(
                apply_style,
                columns=df.columns,
                axis=1
            )
            
            st.dataframe(styled_df)

if __name__ == "__main__":
    main()
