import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Define color thresholds for each metric
def get_color_thresholds():
    return {
        'Gross Margin (%)': {'good': 40, 'neutral': 20},
        'Operating Margin (%)': {'good': 15, 'neutral': 8},
        'ROCE (%)': {'good': 15, 'neutral': 10},
        'ROIC (%)': {'good': 10, 'neutral': 5},
        'Cash Conversion (%)': {'good': 90, 'neutral': 70},
        'Debt to Equity': {'good': 1.0, 'neutral': 2.0, 'reverse': True},  # reverse means lower is better
        'Interest Coverage': {'good': 5, 'neutral': 2},
        'EPS Growth Rate (%)': {'good': 10, 'neutral': 5},
        'Revenue Growth Rate (%)': {'good': 10, 'neutral': 5},
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
        if pd.isna(value):
            return 'background-color: gray'
        
        if metric in thresholds:
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
        return ''

    styled_df = df.style
    
    for column in df.columns:
        if column in thresholds:
            styled_df = styled_df.applymap(lambda x: color_cells(x, column), subset=[column])
    
    return styled_df

[Previous calculate_growth_rate and calculate_ratios functions remain the same]

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
                
                existing_columns = [col for col in column_order if col in df.columns]
                df = df[existing_columns]
                
                # Round all numbers to 2 decimal places
                df = df.round(2)
                
                # Apply styling
                styled_df = style_dataframe(df)
                
                st.write("### Financial Ratios Analysis")
                st.dataframe(styled_df)
                
                # Add descriptions
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
            
            if errors:
                st.error("Errors encountered:")
                for error in errors:
                    st.write(error)

if __name__ == "__main__":
    main()
