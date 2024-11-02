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

def get_color_thresholds():
    return {
        'Gross Margin (%)': {'good': 40, 'neutral': 20},
        'Operating Margin (%)': {'good': 15, 'neutral': 8},
        'ROCE (%)': {'good': 15, 'neutral': 10},
        'ROIC (%)': {'good': 10, 'neutral': 5},
        'Cash Conversion (%)': {'good': 90, 'neutral': 70},
        'Debt to Equity': {'good': 1.0, 'neutral': 2.0, 'reverse': True},
        'Interest Coverage': {'good': 5, 'neutral': 2},
        'EPS Growth Rate (%)': {'good': 10, 'neutral': 5},
        'Revenue Growth Rate (%)': {'good': 10, 'neutral': 5},
        'Upside Potential (%)': {'good': 20, 'neutral': 10},
        'Downside Risk (%)': {'good': 10, 'neutral': 20, 'reverse': True}
    }

def calculate_valuation_metrics(ticker, info, ratios):
    """Calculate valuation metrics for a stock"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get forward P/E and other metrics
        forward_pe = info.get('forwardPE', np.nan)
        trailing_pe = info.get('trailingPE', np.nan)
        industry = info.get('industry', 'N/A')
        sector = info.get('sector', 'N/A')
        
        # Try to get sector PE ratio from a different endpoint
        try:
            stock_info = stock.get_info()
            industry_pe = stock_info.get('pegRatio', np.nan) * forward_pe  # Using PEG ratio to estimate industry PE
            if pd.isna(industry_pe):
                industry_pe = stock_info.get('industryPE', forward_pe)
        except:
            industry_pe = forward_pe
        
        # Get time period info
        try:
            latest_quarter = stock.quarterly_financials.columns[0].strftime('%Y-%m-%d')
            latest_annual = stock.financials.columns[0].strftime('%Y-%m-%d')
        except:
            latest_quarter = "N/A"
            latest_annual = "N/A"
        
        # Calculate fair value range
        current_price = info.get('currentPrice', np.nan)
        if not pd.isna(forward_pe) and not pd.isna(current_price):
            # Calculate fair value ranges
            conservative_pe = min(forward_pe, industry_pe) * 0.8
            optimistic_pe = max(forward_pe, industry_pe) * 1.2
            
            # Get forward EPS
            forward_eps = current_price / forward_pe if forward_pe != 0 else np.nan
            
            # Calculate fair value ranges
            conservative_value = forward_eps * conservative_pe
            fair_value = forward_eps * forward_pe
            optimistic_value = forward_eps * optimistic_pe
            
            # Determine if undervalued/overvalued
            if current_price < conservative_value:
                valuation_status = "Undervalued"
            elif current_price > optimistic_value:
                valuation_status = "Overvalued"
            else:
                valuation_status = "Fair Valued"
            
            # Calculate upside/downside potential
            upside_potential = ((optimistic_value - current_price) / current_price) * 100
            downside_risk = ((current_price - conservative_value) / current_price) * 100
            
            return {
                'Forward P/E': forward_pe,
                'Industry P/E': industry_pe,
                'Industry': industry,
                'Sector': sector,
                'Fair Value': fair_value,
                'Value Range': f"${conservative_value:.2f} - ${optimistic_value:.2f}",
                'Valuation Status': valuation_status,
                'Upside Potential (%)': upside_potential,
                'Downside Risk (%)': downside_risk,
                'Latest Quarter': latest_quarter,
                'Latest Annual': latest_annual
            }
        else:
            return {
                'Forward P/E': np.nan,
                'Industry P/E': np.nan,
                'Industry': industry,
                'Sector': sector,
                'Fair Value': np.nan,
                'Value Range': "N/A",
                'Valuation Status': "Unable to Calculate",
                'Upside Potential (%)': np.nan,
                'Downside Risk (%)': np.nan,
                'Latest Quarter': latest_quarter,
                'Latest Annual': latest_annual
            }
    except Exception as e:
        st.write(f"Error calculating valuation metrics: {str(e)}")
        return {
            'Forward P/E': np.nan,
            'Industry P/E': np.nan,
            'Industry': "N/A",
            'Sector': "N/A",
            'Fair Value': np.nan,
            'Value Range': "N/A",
            'Valuation Status': "Error in Calculation",
            'Upside Potential (%)': np.nan,
            'Downside Risk (%)': np.nan,
            'Latest Quarter': "N/A",
            'Latest Annual': "N/A"
        }

def calculate_rating(ratios):
    """Calculate rating based on key metrics"""
    weights = {
        'Gross Margin (%)': 0.15,
        'Operating Margin (%)': 0.20,
        'ROCE (%)': 0.20,
        'Cash Conversion (%)': 0.15,
        'Debt to Equity': 0.15,
        'Interest Coverage': 0.15
    }
    
    thresholds = get_color_thresholds()
    score = 0
    total_weight = 0
    
    for metric, weight in weights.items():
        if metric in ratios and not pd.isna(ratios[metric]):
            value = ratios[metric]
            if metric == 'Debt to Equity':  # Lower is better for Debt to Equity
                if value <= thresholds[metric]['good']:
                    score += weight * 3
                elif value <= thresholds[metric]['neutral']:
                    score += weight * 2
                else:
                    score += weight * 1
            else:  # Higher is better for other metrics
                if value >= thresholds[metric]['good']:
                    score += weight * 3
                elif value >= thresholds[metric]['neutral']:
                    score += weight * 2
                else:
                    score += weight * 1
            total_weight += weight
    
    if total_weight > 0:
        final_score = (score / total_weight)
        # Convert to letter grade
        if final_score >= 2.7:
            return 'A'
        elif final_score >= 2.3:
            return 'B'
        elif final_score >= 2.0:
            return 'C'
        elif final_score >= 1.7:
            return 'D'
        else:
            return 'F'
    return 'N/A'

def style_dataframe(df):
    """Apply color styling to dataframe based on thresholds"""
    thresholds = get_color_thresholds()
    
    def color_cells(value, metric):
        # Handle non-numeric and special cases
        if pd.isna(value):
            return 'background-color: gray'
        
        # Special handling for Valuation Status column
        if metric == 'Valuation Status':
            if value == 'Undervalued':
                return 'background-color: lightgreen'
            elif value == 'Overvalued':
                return 'background-color: lightcoral'
            elif value == 'Fair Valued':
                return 'background-color: lightgray'
            return ''
            
        # Skip columns that don't need coloring
        if metric not in thresholds:
            return ''
            
        # Handle numeric values
        try:
            value = float(value)
            if 'reverse' in thresholds[metric] and thresholds[metric]['reverse']:
                if value <= thresholds[metric]['good']:
                    return 'background-color: lightgreen'
                elif value <= thresholds[metric]['neutral']:
                    return 'background-color: lightgray'
                else:
                    return 'background-color: lightcoral'
            else:
                if value >= thresholds[metric]['good']:
                    return 'background-color: lightgreen'
                elif value >= thresholds[metric]['neutral']:
                    return 'background-color: lightgray'
                else:
                    return 'background-color: lightcoral'
        except:
            return ''

    # Initialize style
    styled_df = df.style
    
    # Apply styling column by column
    for column in df.columns:
        if column in thresholds or column == 'Valuation Status':
            styled_df = styled_df.applymap(lambda x: color_cells(x, column), subset=[column])
    
    return styled_df

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
            if capital_employed != 0 and operating_income is not None:
                roce = (operating_income / capital_employed) * 100
                ratios['ROCE (%)'] = roce
            else:
                ratios['ROCE (%)'] = np.nan

            # Calculate ROIC
            if capital_employed != 0 and net_income is not None:
                roic = (net_income / capital_employed) * 100
                ratios['ROIC (%)'] = roic
            else:
                ratios['ROIC (%)'] = np.nan

        except Exception as e:
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

        # Add valuation metrics
        valuation_metrics = calculate_valuation_metrics(ticker, info, ratios)
        ratios.update(valuation_metrics)

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
            if 'Long Term Debt' in balance_sheet.index and 'Short Term Debt' in balance_sheet.index:
                long_term_debt = balance_sheet.loc['Long Term Debt', balance_sheet.columns[0]]
                short_term_debt = balance_sheet.loc['Short Term Debt', balance_sheet.columns[0]]
                total_debt = long_term_debt + short_term_debt
                total_equity = balance_sheet.loc['Total Stockholder Equity', balance_sheet.columns[0]]
                ratios['Debt to Equity'] = (total_debt / total_equity) if total_equity != 0 else np.nan
            else:
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
    
    st.write("""
    Enter one or more stock tickers to analyze their financial ratios.
    For multiple stocks, separate them with commas (e.g., AAPL, MSFT, GOOGL)
    """)
    
    ticker_input = st.text_input(
        "Enter stock ticker(s)",
        placeholder="e.g., AAPL, MSFT, GOOGL"
    )
    
    if st.button("Analyze"):
        if ticker_input:
            tickers = [t.strip().upper() for t in ticker_input.split(",")]
            progress_bar = st.progress(0)
            all_ratios = {}
            errors = []
            ratings = {}
            
            for i, ticker in enumerate(tickers):
                with st.spinner(f"Processing {ticker}..."):
                    ratios, error = calculate_ratios(ticker)
                    
                    if error:
                        errors.append(error)
                    else:
                        all_ratios[ticker] = ratios
                        # Calculate rating
                        ratings[ticker] = calculate_rating(ratios)
                    
                    progress_bar.progress((i + 1) / len(tickers))
            
            if all_ratios:
                # Convert to DataFrame
                df = pd.DataFrame(all_ratios).T
                
                # Add ratings column
                df['Rating'] = pd.Series(ratings)
                
                # Reorder columns
                column_order = [
                    'Rating',
                    'Market Price',
                    'Fair Value',
                    'Value Range',
                    'Valuation Status',
                    'Forward P/E',
                    'Industry P/E',
                    'Industry',
                    'Sector',
                    'Upside Potential (%)',
                    'Downside Risk (%)',
                    'P/E Ratio',
                    'EPS Growth Rate (%)',
                    'Revenue Growth Rate (%)',
                    'Gross Margin (%)',
                    'Operating Margin (%)',
                    'ROCE (%)',
                    'ROIC (%)',
                    'Cash Conversion (%)',
                    'Debt to Equity',
                    'Interest Coverage',
                    'Latest Quarter',
                    'Latest Annual'
                ]
                
                existing_columns = [col for col in column_order if col in df.columns]
                df = df[existing_columns]
                
                # Round all numbers to 2 decimal places
                df = df.round(2)
                
                # Apply styling
                styled_df = style_dataframe(df)
                
                st.write("### Financial Ratios Analysis")
                st.dataframe(styled_df)
                
                # Add descriptions
                st.write("### Valuation Analysis")
                st.write("""
                **Valuation Metrics**:
                - Fair Value: Calculated based on forward P/E and industry comparisons
                - Value Range: Conservative to optimistic value range
                - Valuation Status: Indicates if the stock is Undervalued, Fair Valued, or Overvalued
                - Forward P/E: Expected price-to-earnings ratio based on projected earnings
                - Industry P/E: Average P/E ratio for the industry
                - Upside Potential: Potential percentage gain to optimistic value
                - Downside Risk: Potential percentage loss to conservative value
                """)

                st.write("### Rating System")
                st.write("""
                **Rating Criteria**:
                - A: Excellent financial health and performance
                - B: Good financial health and performance
                - C: Average financial health and performance
                - D: Below average financial health and performance
                - F: Poor financial health and performance
                
                **Key Metrics and Thresholds**:
                - Gross Margin: Good > 40%, Neutral > 20%
                - Operating Margin: Good > 15%, Neutral > 8%
                - ROCE: Good > 15%, Neutral > 10%
                - Cash Conversion: Good > 90%, Neutral > 70%
                - Debt to Equity: Good < 1.0, Neutral < 2.0
                - Interest Coverage: Good > 5x, Neutral > 2x
                """)
                
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

                # Add time period information to descriptions
                st.write("### Data Time Periods")
                st.write("""
                - Financial Ratios: Based on latest quarterly and annual reports
                - Market Data: Real-time or delayed based on exchange
                - Growth Rates: Year-over-year comparison
                - Valuation Metrics: Forward-looking based on analyst estimates
        
        Note: Check 'Latest Quarter' and 'Latest Annual' columns for specific dates of financial data.
        """)

                
            
            # Display any errors
            if errors:
                st.error("Errors encountered:")
                for error in errors:
                    st.write(error)

if __name__ == "__main__":
    main()
