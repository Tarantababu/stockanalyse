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

        # Calculate ratios
        ratios = {}

        # ROCE and ROIC Calculations
        try:
            # Extract required values
            # For Total Capital Employed:
            # Capital Employed = Total Assets - Current Liabilities
            total_assets = balance_sheet.loc['Total Assets', balance_sheet.columns[0]]
            
            # Try different field names for current liabilities
            current_liabilities_fields = [
                'Total Current Liabilities',
                'Current Liabilities',
                'Total Current Liab'
            ]
            
            current_liabilities = None
            for field in current_liabilities_fields:
                if field in balance_sheet.index:
                    current_liabilities = balance_sheet.loc[field, balance_sheet.columns[0]]
                    break
            
            if current_liabilities is None:
                raise ValueError("Could not find current liabilities")

            # Try different field names for operating income
            operating_income_fields = [
                'Operating Income',
                'EBIT',
                'Operating Income Or Loss',
                'Income Before Tax'
            ]
            
            operating_income = None
            for field in operating_income_fields:
                if field in income_stmt.index:
                    operating_income = income_stmt.loc[field, income_stmt.columns[0]]
                    break
            
            if operating_income is None:
                raise ValueError("Could not find operating income")

            # Try different field names for net income
            net_income_fields = [
                'Net Income',
                'Net Income Common Stockholders',
                'Net Income From Continuing Ops'
            ]
            
            net_income = None
            for field in net_income_fields:
                if field in income_stmt.index:
                    net_income = income_stmt.loc[field, income_stmt.columns[0]]
                    break
            
            if net_income is None:
                raise ValueError("Could not find net income")

            # Calculate Capital Employed
            capital_employed = total_assets - current_liabilities

            # Calculate ROCE
            # ROCE = (Operating Income / Capital Employed) × 100
            if capital_employed != 0 and operating_income is not None:
                roce = (operating_income / capital_employed) * 100
                ratios['ROCE (%)'] = roce
            else:
                ratios['ROCE (%)'] = np.nan

            # Calculate ROIC
            # ROIC = (Net Income / Capital Employed) × 100
            if capital_employed != 0 and net_income is not None:
                roic = (net_income / capital_employed) * 100
                ratios['ROIC (%)'] = roic
            else:
                ratios['ROIC (%)'] = np.nan

            # Debug information
            st.write(f"\nDebug - Values used for {ticker}:")
            st.write(f"Total Assets: {total_assets:,.2f}")
            st.write(f"Current Liabilities: {current_liabilities:,.2f}")
            st.write(f"Capital Employed: {capital_employed:,.2f}")
            st.write(f"Operating Income: {operating_income:,.2f}")
            st.write(f"Net Income: {net_income:,.2f}")
            st.write(f"ROCE: {ratios['ROCE (%)']:,.2f}%")
            st.write(f"ROIC: {ratios['ROIC (%)']:,.2f}%")

        except Exception as e:
            st.write(f"Error calculating ROCE/ROIC: {str(e)}")
            ratios['ROCE (%)'] = np.nan
            ratios['ROIC (%)'] = np.nan

        # Market Price and P/E
        try:
            ratios['Market Price'] = info.get('currentPrice', np.nan)
            ratios['P/E Ratio'] = info.get('trailingPE', np.nan)
        except Exception as e:
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
            ratios.update({
                'EPS Growth Rate (%)': np.nan,
                'Revenue Growth Rate (%)': np.nan
            })

        # Profitability Ratios
        try:
            if 'Gross Profit' in income_stmt.index and 'Total Revenue' in income_stmt.index:
                gross_profit = income_stmt.loc['Gross Profit', income_stmt.columns[0]]
                revenue = income_stmt.loc['Total Revenue', income_stmt.columns[0]]
                ratios['Gross Margin (%)'] = (gross_profit / revenue) * 100 if revenue != 0 else np.nan
            
            if 'Operating Income' in income_stmt.index and 'Total Revenue' in income_stmt.index:
                operating_income = income_stmt.loc['Operating Income', income_stmt.columns[0]]
                revenue = income_stmt.loc['Total Revenue', income_stmt.columns[0]]
                ratios['Operating Margin (%)'] = (operating_income / revenue) * 100 if revenue != 0 else np.nan
        except Exception as e:
            ratios.update({
                'Gross Margin (%)': np.nan,
                'Operating Margin (%)': np.nan
            })

        # Debt to Equity
        try:
            # Try to calculate from balance sheet first
            if 'Long Term Debt' in balance_sheet.index and 'Short Term Debt' in balance_sheet.index:
                long_term_debt = balance_sheet.loc['Long Term Debt', balance_sheet.columns[0]]
                short_term_debt = balance_sheet.loc['Short Term Debt', balance_sheet.columns[0]]
                total_debt = long_term_debt + short_term_debt
                total_equity = balance_sheet.loc['Total Stockholder Equity', balance_sheet.columns[0]]
                ratios['Debt to Equity'] = (total_debt / total_equity) if total_equity != 0 else np.nan
            else:
                # Fallback to info object
                ratios['Debt to Equity'] = info.get('debtToEquity', np.nan)
                if ratios['Debt to Equity'] is not None:
                    ratios['Debt to Equity'] = ratios['Debt to Equity'] / 100
        except Exception as e:
            ratios['Debt to Equity'] = np.nan

        # Cash Conversion and Interest Coverage
        try:
            if 'Operating Cash Flow' in cash_flow.index and 'Net Income' in income_stmt.index:
                operating_cash_flow = cash_flow.loc['Operating Cash Flow', cash_flow.columns[0]]
                net_income = income_stmt.loc['Net Income', income_stmt.columns[0]]
                ratios['Cash Conversion (%)'] = (operating_cash_flow / net_income) * 100 if net_income != 0 else np.nan

            if 'Interest Expense' in income_stmt.index and 'Operating Income' in income_stmt.index:
                interest_expense = abs(income_stmt.loc['Interest Expense', income_stmt.columns[0]])
                operating_income = income_stmt.loc['Operating Income', income_stmt.columns[0]]
                ratios['Interest Coverage'] = (operating_income / interest_expense) if interest_expense != 0 else np.nan
        except Exception as e:
            ratios.update({
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
                existing_columns = [col for col in column_order if col in df.columns]
                df = df[existing_columns]
                
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
