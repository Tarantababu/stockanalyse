import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

def fetch_financial_metrics(ticker):
    """Fetch and calculate financial metrics for a given ticker"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get financial statements
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow
        
        # Current market data
        info = stock.info
        market_price = info.get('currentPrice', np.nan)
        market_cap = info.get('marketCap', np.nan)
        
        # Calculate metrics
        # Revenue Growth
        latest_revenue = income_stmt.loc['Total Revenue'][0]
        prev_revenue = income_stmt.loc['Total Revenue'][1]
        revenue_growth = ((latest_revenue - prev_revenue) / prev_revenue) * 100
        
        # ROCE
        operating_profit = income_stmt.loc.get('Operating Income', income_stmt.loc.get('EBIT', 0))[0]
        total_assets = balance_sheet.loc['Total Assets'][0]
        current_liabilities = balance_sheet.loc['Total Current Liabilities'][0]
        capital_employed = total_assets - current_liabilities
        roce = (operating_profit / capital_employed) * 100 if capital_employed != 0 else 0
        
        # Gross Margin
        gross_profit = income_stmt.loc['Gross Profit'][0]
        gross_margin = (gross_profit / latest_revenue) * 100 if latest_revenue != 0 else 0
        
        # Operating Profit Margin
        operating_margin = (operating_profit / latest_revenue) * 100 if latest_revenue != 0 else 0
        
        # Cash Conversion
        operating_cash_flow = cashflow.loc['Operating Cash Flow'][0]
        cash_conversion = (latest_revenue / operating_cash_flow) * 100 if operating_cash_flow != 0 else 0
        
        # Leverage
        total_debt = balance_sheet.loc.get('Total Debt', 0)[0]
        total_equity = balance_sheet.loc['Total Stockholder Equity'][0]
        leverage = (total_debt / total_equity) * 100 if total_equity != 0 else 0
        
        # Interest Coverage
        interest_expense = abs(income_stmt.loc.get('Interest Expense', 0)[0])
        interest_coverage = operating_profit / interest_expense if interest_expense != 0 else 0
        
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
            
            # Apply color styling
            def style_df(df):
                return df.style.apply(lambda x: [get_cell_color(float(str(val).replace('$', '').replace(',', '').replace('%', '')) 
                                               if isinstance(val, str) and any(c.isdigit() for c in val) else ''
                                               for val in x], 
                                    axis=1)
            
            styled_df = style_df(df)
            st.dataframe(styled_df)

if __name__ == "__main__":
    main()
