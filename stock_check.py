import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

def calculate_ratios(ticker):
    """Calculate financial ratios for a given ticker"""
    try:
        # Fetch stock data
        stock = yf.Ticker(ticker)
        
        # Get financial statements
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        # Calculate ratios
        ratios = {}
        
        # 1. Profitability Ratios
        try:
            # Gross Margin
            gross_profit = income_stmt.loc['Gross Profit', income_stmt.columns[0]]
            revenue = income_stmt.loc['Total Revenue', income_stmt.columns[0]]
            ratios['Gross Margin'] = (gross_profit / revenue) * 100 if revenue != 0 else np.nan
            
            # Operating Margin
            operating_income = income_stmt.loc['Operating Income', income_stmt.columns[0]]
            ratios['Operating Margin'] = (operating_income / revenue) * 100 if revenue != 0 else np.nan
            
            # ROCE (Return on Capital Employed)
            total_assets = balance_sheet.loc['Total Assets', balance_sheet.columns[0]]
            current_liabilities = balance_sheet.loc['Total Current Liabilities', balance_sheet.columns[0]]
            capital_employed = total_assets - current_liabilities
            ratios['ROCE'] = (operating_income / capital_employed) * 100 if capital_employed != 0 else np.nan
        except:
            ratios.update({
                'Gross Margin': np.nan,
                'Operating Margin': np.nan,
                'ROCE': np.nan
            })
        
        # 2. Cash Conversion Ratio
        try:
            operating_cash_flow = cash_flow.loc['Operating Cash Flow', cash_flow.columns[0]]
            net_income = income_stmt.loc['Net Income', income_stmt.columns[0]]
            ratios['Cash Conversion Ratio'] = (operating_cash_flow / net_income) * 100 if net_income != 0 else np.nan
        except:
            ratios['Cash Conversion Ratio'] = np.nan
        
        # 3. Financial Stability Ratios
        try:
            # Debt to Equity
            total_debt = balance_sheet.loc['Total Debt', balance_sheet.columns[0]]
            total_equity = balance_sheet.loc['Total Stockholder Equity', balance_sheet.columns[0]]
            ratios['Debt to Equity'] = (total_debt / total_equity) if total_equity != 0 else np.nan
            
            # Interest Coverage Ratio
            interest_expense = abs(income_stmt.loc['Interest Expense', income_stmt.columns[0]])
            ratios['Interest Coverage Ratio'] = (operating_income / interest_expense) if interest_expense != 0 else np.nan
        except:
            ratios.update({
                'Debt to Equity': np.nan,
                'Interest Coverage Ratio': np.nan
            })
        
        return ratios, None
        
    except Exception as e:
        return None, f"Error processing {ticker}: {str(e)}"

def main():
    st.title("Stock Financial Ratio Analysis")
    
    # Input for stock tickers
    ticker_input = st.text_input(
        "Enter stock ticker(s) (comma-separated for multiple)",
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
                st.write(f"Processing {ticker}...")
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
                
                # Round all numbers to 2 decimal places
                df = df.round(2)
                
                # Apply styling
                st.write("### Financial Ratios Analysis")
                st.dataframe(
                    df.style
                    .background_gradient(cmap='RdYlGn', axis=0)
                    .format("{:.2f}")
                )
                
                # Add descriptions
                st.write("### Ratio Descriptions")
                st.write("""
                **Profitability**:
                - Gross Margin (%): Indicates the percentage of revenue that exceeds the cost of goods sold
                - Operating Margin (%): Shows how much profit a company makes on a dollar of sales before interest and taxes
                - ROCE (%): Measures how efficiently a company uses its capital to generate profits
                
                **Cash Generation**:
                - Cash Conversion Ratio (%): Shows how efficiently a company converts profit into cash flow
                
                **Financial Stability**:
                - Debt to Equity: Measures a company's financial leverage
                - Interest Coverage Ratio: Indicates how easily a company can pay interest on its debt
                """)
            
            # Display any errors
            if errors:
                st.error("Errors encountered:")
                for error in errors:
                    st.write(error)

if __name__ == "__main__":
    main()
