import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json
import re
import time
from requests.exceptions import RequestException

def fetch_with_retry(ticker, retries=3, delay=1):
    """Fetch ticker data with retry logic"""
    for attempt in range(retries):
        try:
            stock = yf.Ticker(ticker)
            # Test the connection by accessing a simple property
            _ = stock.info['regularMarketPrice']
            return stock
        except Exception as e:
            if attempt == retries - 1:  # Last attempt
                raise Exception(f"Failed to fetch data for {ticker} after {retries} attempts: {str(e)}")
            time.sleep(delay)  # Wait before retrying
    return None

def get_stock_info(ticker):
    """Fetch stock information using yfinance with retry logic"""
    try:
        stock = fetch_with_retry(ticker)
        if stock is None:
            return {}
            
        info = stock.info
        return {
            'longName': info.get('longName', ticker),
            'marketCap': info.get('marketCap', 0),
            'trailingPE': info.get('trailingPE', 0),
            'forwardPE': info.get('forwardPE', 0),
            'priceToSales': info.get('priceToSalesTrailing12Months', 0),
            'priceToBook': info.get('priceToBook', 0),
            'enterpriseToEbitda': info.get('enterpriseToEbitda', 0),
            'profitMargin': info.get('profitMargins', 0),
            'operatingMargin': info.get('operatingMargins', 0),
            'returnOnEquity': info.get('returnOnEquity', 0),
            'returnOnAssets': info.get('returnOnAssets', 0),
            'totalCash': info.get('totalCash', 0),
            'totalDebt': info.get('totalDebt', 0),
            'freeCashflow': info.get('freeCashflow', 0),
            'operatingCashflow': info.get('operatingCashflow', 0)
        }
    except Exception as e:
        st.warning(f"Warning: Unable to fetch complete data for {ticker}: {str(e)}")
        return {}

def get_historical_data(ticker, period='1y', interval='1d', retries=3):
    """Fetch historical price data with retry logic"""
    for attempt in range(retries):
        try:
            stock = yf.Ticker(ticker)
            hist_data = stock.history(period=period, interval=interval)
            
            if hist_data.empty:
                raise ValueError(f"No historical data found for {ticker}")
                
            return hist_data
        except Exception as e:
            if attempt == retries - 1:  # Last attempt
                raise Exception(f"Could not fetch historical data for {ticker}: {str(e)}")
            time.sleep(1)  # Wait before retrying
    
    raise Exception(f"Failed to fetch historical data for {ticker} after {retries} attempts")

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_cached_stock_data(ticker, period, interval):
    """Cache stock data to avoid repeated API calls"""
    try:
        market_data = get_stock_info(ticker)
        hist_data = get_historical_data(ticker, period, interval)
        return market_data, hist_data
    except Exception as e:
        raise Exception(f"Error fetching data: {str(e)}")

# [Previous format_number, format_ratio, format_percentage, and create_metric_chart functions remain the same]

def main():
    st.title("Stock Analysis Dashboard")
    
    # Sidebar for stock selection and settings
    st.sidebar.header("Stock Selection")
    ticker = st.sidebar.text_input("Enter Stock Ticker:", value="AAPL").upper()
    
    # Add period selection
    period_options = {
        '1 Day': '1d',
        '5 Days': '5d',
        '1 Month': '1mo',
        '3 Months': '3mo',
        '6 Months': '6mo',
        '1 Year': '1y',
        '2 Years': '2y',
        '5 Years': '5y',
        'Year to Date': 'ytd',
        'Max': 'max'
    }
    
    selected_period = st.sidebar.selectbox(
        "Select Time Period",
        options=list(period_options.keys()),
        index=5  # Default to 1 Year
    )
    
    # Add interval selection
    interval_options = {
        '1 Day': ['1m', '2m', '5m', '15m', '30m', '60m'],
        '5 Days': ['5m', '15m', '30m', '60m'],
        '1 Month': ['30m', '60m', '1d'],
        '3 Months': ['1d', '1wk'],
        '6 Months': ['1d', '1wk'],
        '1 Year': ['1d', '1wk', '1mo'],
        '2 Years': ['1d', '1wk', '1mo'],
        '5 Years': ['1d', '1wk', '1mo'],
        'Year to Date': ['1d', '1wk', '1mo'],
        'Max': ['1d', '1wk', '1mo']
    }
    
    interval_display = {
        '1m': '1 Minute', '2m': '2 Minutes', '5m': '5 Minutes',
        '15m': '15 Minutes', '30m': '30 Minutes', '60m': '1 Hour',
        '1d': '1 Day', '1wk': '1 Week', '1mo': '1 Month'
    }
    
    available_intervals = interval_options[selected_period]
    selected_interval = st.sidebar.selectbox(
        "Select Interval",
        options=[interval_display[i] for i in available_intervals],
        index=len(available_intervals)-1
    )
    
    interval_code = {v: k for k, v in interval_display.items()}[selected_interval]
    
    if st.sidebar.button("Search"):
        try:
            with st.spinner('Fetching stock data...'):
                market_data, hist_data = get_cached_stock_data(
                    ticker,
                    period_options[selected_period],
                    interval_code
                )
            
            if not market_data:
                st.warning(f"Limited data available for {ticker}")
            
            # Display basic company info
            st.header(f"{market_data.get('longName', ticker)} ({ticker})")
            
            # [Rest of the display code remains the same until comparison part]
            
            # Compare functionality
            st.subheader("Compare Stocks")
            compare_ticker = st.text_input("Enter ticker to compare:", "")
            
            if compare_ticker:
                try:
                    with st.spinner('Fetching comparison data...'):
                        compare_market_data, compare_hist = get_cached_stock_data(
                            compare_ticker,
                            period_options[selected_period],
                            interval_code
                        )
                    
                    if not compare_hist.empty and not hist_data.empty:
                        # Normalize prices for comparison
                        hist_data_norm = hist_data['Close'] / hist_data['Close'].iloc[0] * 100
                        compare_hist_norm = compare_hist['Close'] / compare_hist['Close'].iloc[0] * 100
                        
                        # Create comparison chart
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=hist_data_norm.index, y=hist_data_norm,
                                               name=ticker, mode='lines'))
                        fig.add_trace(go.Scatter(x=compare_hist_norm.index, y=compare_hist_norm,
                                               name=compare_ticker, mode='lines'))
                        
                        fig.update_layout(
                            title=f"Price Comparison (Normalized to 100)",
                            xaxis_title="Date",
                            yaxis_title="Normalized Price",
                            template="plotly_white",
                            height=400
                        )
                        
                        st.plotly_chart(fig)
                        
                        # Compare key metrics
                        comparison_df = pd.DataFrame({
                            'Metric': ['Market Cap', 'P/E (TTM)', 'Price/Sales', 'EV/EBITDA'],
                            ticker: [
                                format_number(market_data.get('marketCap', 0)),
                                format_ratio(market_data.get('trailingPE')),
                                format_ratio(market_data.get('priceToSales')),
                                format_ratio(market_data.get('enterpriseToEbitda'))
                            ],
                            compare_ticker: [
                                format_number(compare_market_data.get('marketCap', 0)),
                                format_ratio(compare_market_data.get('trailingPE')),
                                format_ratio(compare_market_data.get('priceToSales')),
                                format_ratio(compare_market_data.get('enterpriseToEbitda'))
                            ]
                        })
                        
                        st.write("Metric Comparison")
                        st.dataframe(comparison_df)
                    else:
                        st.error("Unable to create comparison: No data available for one or both stocks")
                        
                except Exception as e:
                    st.error(f"Error comparing with {compare_ticker}: {str(e)}")
                
        except Exception as e:
            st.error(f"Error analyzing {ticker}: {str(e)}")

if __name__ == "__main__":
    main()
