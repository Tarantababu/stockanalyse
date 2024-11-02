import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

def calculate_growth_rate(data_series):
    """Calculate year-over-year growth rate"""
    if len(data_series) >= 2:
        current = data_series.iloc[0]
        previous = data_series.iloc[1]
        return ((current - previous) / abs(previous)) * 100 if previous != 0 else np.nan
    return np.nan

def calculate_ratios(ticker):
    """Calculate financial ratios for a given ticker"""
    try:
        # Fetch stock data
        stock = yf.Ticker(ticker)
        
        # Get financial statements
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        # Get market data
        info = stock.info
        
        # Calculate ratios
        ratios = {}
        
        # Market Price and P/E
        try:
            ratios['Market Price'] = info.get('currentPrice', np.nan)
            ratios['P/E Ratio'] = info.get('trailingPE', np.nan)
        except Exception as e:
            st.write(f"Error calculating market metrics: {str(e)}")
            ratios.update({
                'Market Price': np.nan,
                'P/E Ratio': np.nan
            })
        
        # Growth Rates
        try:
            # EPS Growth Rate
            if 'Basic EPS' in income_stmt.index:
                eps_growth = calculate_growth_rate(income_stmt.loc['Basic EPS'])
                ratios['EPS Growth Rate (%)'] = eps_growth
            
            # Revenue Growth Rate
            if 'Total Revenue' in income_stmt.index:
                revenue_growth = calculate_growth_rate(income_stmt.loc['Total Revenue'])
                ratios['Revenue Growth Rate (%)'] = revenue_growth
        except Exception as e:
            st.write(f"Error calculating growth rates: {str(e)}")
            ratios.update({
                'EPS Growth Rate (%)': np.nan,
                'Revenue Growth Rate (%)': np.nan
            })
        
        # 1. Profitability Ratios
        try:
            # Gross Margin
            if 'Gross Profit' in income_stmt.index and 'Total Revenue' in income_stmt.index:
                gross_profit = income_stmt.loc['Gross Profit', income_stmt.columns[0]]
                revenue = income_stmt.loc['Total Revenue', income_stmt.columns[0]]
                ratios['Gross Margin (%)'] = (gross_profit / revenue) * 100 if revenue != 0 else np.nan
            
            # Operating Margin
            if 'Operating Income' in income_stmt.index and 'Total Revenue' in income_stmt.index:
                operating_income = income_stmt.loc['Operating Income', income_stmt.columns[0]]
                revenue = income_stmt.loc['Total Revenue', income_stmt.columns[0]]
                ratios['Operating Margin (%)'] = (operating_income / revenue) * 100 if revenue != 0 else np.nan
            
            # ROCE (Return on Capital Employed)
            if ('Total Assets' in balance_sheet.index and 
                'Total Current Liabilities' in balance_sheet.index and 
                'Operating Income' in income_stmt.index):
                total_assets = balance_sheet.loc['Total Assets', balance_sheet.columns[0]]
                current_liabilities = balance_sheet.loc['Total Current Liabilities', balance_sheet.columns[0]]
                operating_income = income_stmt.loc['Operating Income', income_stmt.columns[0]]
                capital_employed = total_assets - current_liabilities
                ratios['ROCE (%)'] = (operating_income / capital_employed) * 100 if capital_employed != 0 else np.nan
            
            # ROIC (Return on Invested Capital)
            if ('Net Income' in income_stmt.index and 
                'Total Assets' in balance_sheet.index and
                'Total Current Liabilities' in balance_sheet.index):
                net_income = income_stmt.loc['Net Income', income_stmt.columns[0]]
                total_assets = balance_sheet.loc['Total Assets', balance_sheet.columns[0]]
                current_liabilities = balance_sheet.loc['Total Current Liabilities', balance_sheet.columns[0]]
                invested_capital = total_assets - current_liabilities
                ratios['ROIC (%)'] = (net_income / invested_capital) * 100 if invested_capital != 0 else np.nan
                
        except Exception as e:
            st.write(f"Error calculating profitability ratios: {str(e)}")
            ratios.update({
                'Gross Margin (%)': np.nan,
                'Operating Margin (%)': np.nan,
                'ROCE (%)': np.nan,
                'ROIC (%)': np.nan
            })
        
        # 2. Cash Conversion Ratio
        try:
            if 'Operating Cash Flow' in cash_flow.index and 'Net Income' in income_stmt.index:
                operating_cash_flow = cash_flow.loc['Operating Cash Flow', cash_flow.columns[0]]
                net_income = income_stmt.loc['Net Income', income_stmt.columns[0]]
                ratios['Cash Conversion (%)'] = (operating_cash_flow / net_income) * 100 if net_income != 0 else np.nan
        except Exception as e:
            st.write(f"Error calculating cash conversion ratio: {str(e)}")
            ratios['Cash Conversion (%)'] = np.nan
        
        # 3. Financial Stability Ratios
        try:
            # Debt to Equity
            if ('Total Debt' in balance_sheet.index and 
                'Total Stockholder Equity' in balance_sheet.index):
                total_debt = balance_sheet.loc['Total Debt', balance_sheet.columns[0]]
                total_equity = balance_sheet.loc['Total Stockholder Equity', balance_sheet.columns[0]]
                ratios['Debt to Equity'] = (total_debt / total_equity) if total_equity != 0 else np.nan
            
            # Interest Coverage Ratio
            if 'Interest Expense' in income_stmt.index and 'Operating Income' in income_stmt.index:
                interest_expense = abs(income_stmt.loc['Interest Expense', income_stmt.columns[0]])
                operating_income = income_stmt.loc['Operating Income', income_stmt.columns[0]]
                ratios['Interest Coverage'] = (operating_income / interest_expense) if interest_expense != 0 else np.nan
        except Exception as e:
            st.write(f"Error calculating stability ratios: {str(e)}")
            ratios.update({
                'Debt to Equity': np.nan,
                'Interest Coverage': np.nan
            })
        
        return ratios, None
        
    except Exception as e:
        return None, f"Error processing {ticker}: {str(e)}"

def main():
    st.title("Stock Financial Ratio Analysis")
    
    # Add description at the top
    st.write("""
    Enter one or more stock tickers to analyze their financial ratios.
    For multiple stocks, separate them with commas (e.g., AAPL, MSFT, GOOGL)
    """)
    
    # Input for stock tickers
    ticker_input = st.text_input(
        "Enter stock ticker(s)",
        placeholder="e.g., AAPL, MSFT, GOOGL"
    )
    
    if st.button("Analyze"):
        if ticker_input:
            # Split and clean tickers
            tickers = [t.strip().upper() for t in ticker_input.split(",")]
            
            # Create progress bar
            progress_bar = st.progress(0)
            
            # Initialize results storage
            all_ratios = {}
            errors = []
            
            # Process each ticker
            for i, ticker in enumerate(tickers):
                with st.spinner(f"Processing {ticker}..."):
                    ratios, error = calculate_ratios(ticker)
                    
                    if error:
                        errors.append(error)
                    else:
                        all_ratios[ticker] = ratios
                    
                    # Update progress bar
                    progress_bar.progress((i + 1) / len(tickers))
            
            # Display results
            if all_ratios:
                # Convert to DataFrame
                df = pd.DataFrame(all_ratios).T
                
                # Reorder columns in a logical grouping
                column_order = [
                    'Market Price',
                    'P/E Ratio',
                    'EPS Growth Rate (%)',
                    'Revenue Growth Rate (%)',
                    'Gross Margin (%)',
                    'Operating Margin (%)',
                    'ROCE (%)',
                    'ROIC (%)',
                    'Cash Conversion (%)',
                    'Debt to Equity',
                    'Interest Coverage'
                ]
                
                # Reorder columns (only include columns that exist)
                df = df[[col for col in column_order if col in df.columns]]
                
                # Round all numbers to 2 decimal places
                df = df.round(2)
                
                # Display the results
                st.write("### Financial Ratios Analysis")
                st.dataframe(df)
                
                # Add descriptions
                st.write("### Metric Descriptions")
                st.write("""
                **Market Metrics**:
                - Market Price: Current stock price
                - P/E Ratio: Price to Earnings ratio
                - EPS Growth Rate: Year-over-year growth in Earnings Per Share
                - Revenue Growth Rate: Year-over-year growth in Total Revenue
                
                **Profitability**:
                - Gross Margin (%): (Gross Profit / Revenue) × 100
                - Operating Margin (%): (Operating Income / Revenue) × 100
                - ROCE (%): (Operating Income / Capital Employed) × 100
                - ROIC (%): (Net Income / Invested Capital) × 100
                
                **Cash & Stability**:
                - Cash Conversion (%): (Operating Cash Flow / Net Income) × 100
                - Debt to Equity: Total Debt / Total Equity
                - Interest Coverage: Operating Income / Interest Expense
                """)
            
            # Display any errors
            if errors:
                st.error("Errors encountered:")
                for error in errors:
                    st.write(error)

if __name__ == "__main__":
    main()
