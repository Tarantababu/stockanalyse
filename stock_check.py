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
        info = stock.info
        
        # Debug prints to see available fields
        st.write(f"Available Balance Sheet Fields for {ticker}:")
        st.write(balance_sheet.index.tolist())
        
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
        
        # Financial Stability Ratios - Debt to Equity
        try:
            # First attempt: Using total debt fields
            if 'Long Term Debt' in balance_sheet.index and 'Short Term Debt' in balance_sheet.index:
                long_term_debt = balance_sheet.loc['Long Term Debt', balance_sheet.columns[0]]
                short_term_debt = balance_sheet.loc['Short Term Debt', balance_sheet.columns[0]]
                total_debt = long_term_debt + short_term_debt
            elif 'Total Debt' in balance_sheet.index:
                total_debt = balance_sheet.loc['Total Debt', balance_sheet.columns[0]]
            else:
                # Try alternative field names
                possible_debt_fields = [
                    'Total Debt', 'Long Term Debt', 
                    'Total Long Term Debt', 'Total Current Liabilities'
                ]
                total_debt = None
                for field in possible_debt_fields:
                    if field in balance_sheet.index:
                        total_debt = balance_sheet.loc[field, balance_sheet.columns[0]]
                        break

            # Get Total Equity
            possible_equity_fields = [
                'Total Stockholder Equity', 
                'Stockholders Equity',
                'Total Equity'
            ]
            total_equity = None
            for field in possible_equity_fields:
                if field in balance_sheet.index:
                    total_equity = balance_sheet.loc[field, balance_sheet.columns[0]]
                    break

            if total_debt is not None and total_equity is not None and total_equity != 0:
                ratios['Debt to Equity'] = (total_debt / total_equity)
            else:
                # Try getting from info object as fallback
                ratios['Debt to Equity'] = info.get('debtToEquity', np.nan)
                if ratios['Debt to Equity'] is not None:
                    ratios['Debt to Equity'] = ratios['Debt to Equity'] / 100  # Convert from percentage

        except Exception as e:
            st.write(f"Error calculating Debt to Equity ratio: {str(e)}")
            ratios['Debt to Equity'] = np.nan

        # Calculate rest of the metrics
        try:
            # Growth Rates
            if 'Basic EPS' in income_stmt.index:
                eps_growth = calculate_growth_rate(income_stmt.loc['Basic EPS'])
                ratios['EPS Growth Rate (%)'] = eps_growth
            
            if 'Total Revenue' in income_stmt.index:
                revenue_growth = calculate_growth_rate(income_stmt.loc['Total Revenue'])
                ratios['Revenue Growth Rate (%)'] = revenue_growth
                
            # Profitability Ratios
            if 'Gross Profit' in income_stmt.index and 'Total Revenue' in income_stmt.index:
                gross_profit = income_stmt.loc['Gross Profit', income_stmt.columns[0]]
                revenue = income_stmt.loc['Total Revenue', income_stmt.columns[0]]
                ratios['Gross Margin (%)'] = (gross_profit / revenue) * 100 if revenue != 0 else np.nan
            
            if 'Operating Income' in income_stmt.index and 'Total Revenue' in income_stmt.index:
                operating_income = income_stmt.loc['Operating Income', income_stmt.columns[0]]
                revenue = income_stmt.loc['Total Revenue', income_stmt.columns[0]]
                ratios['Operating Margin (%)'] = (operating_income / revenue) * 100 if revenue != 0 else np.nan
            
            # ROCE and ROIC
            if ('Total Assets' in balance_sheet.index and 
                'Total Current Liabilities' in balance_sheet.index and 
                'Operating Income' in income_stmt.index):
                total_assets = balance_sheet.loc['Total Assets', balance_sheet.columns[0]]
                current_liabilities = balance_sheet.loc['Total Current Liabilities', balance_sheet.columns[0]]
                operating_income = income_stmt.loc['Operating Income', income_stmt.columns[0]]
                capital_employed = total_assets - current_liabilities
                ratios['ROCE (%)'] = (operating_income / capital_employed) * 100 if capital_employed != 0 else np.nan
            
            if 'Net Income' in income_stmt.index:
                net_income = income_stmt.loc['Net Income', income_stmt.columns[0]]
                invested_capital = total_assets - current_liabilities if 'total_assets' in locals() else np.nan
                ratios['ROIC (%)'] = (net_income / invested_capital) * 100 if invested_capital != 0 else np.nan
            
            # Cash Conversion
            if 'Operating Cash Flow' in cash_flow.index and 'Net Income' in income_stmt.index:
                operating_cash_flow = cash_flow.loc['Operating Cash Flow', cash_flow.columns[0]]
                net_income = income_stmt.loc['Net Income', income_stmt.columns[0]]
                ratios['Cash Conversion (%)'] = (operating_cash_flow / net_income) * 100 if net_income != 0 else np.nan
            
            # Interest Coverage
            if 'Interest Expense' in income_stmt.index and 'Operating Income' in income_stmt.index:
                interest_expense = abs(income_stmt.loc['Interest Expense', income_stmt.columns[0]])
                operating_income = income_stmt.loc['Operating Income', income_stmt.columns[0]]
                ratios['Interest Coverage'] = (operating_income / interest_expense) if interest_expense != 0 else np.nan
                
        except Exception as e:
            st.write(f"Error calculating other ratios: {str(e)}")
            ratios.update({
                'EPS Growth Rate (%)': np.nan,
                'Revenue Growth Rate (%)': np.nan,
                'Gross Margin (%)': np.nan,
                'Operating Margin (%)': np.nan,
                'ROCE (%)': np.nan,
                'ROIC (%)': np.nan,
                'Cash Conversion (%)': np.nan,
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
