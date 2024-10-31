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

def get_stock_info(ticker):
    """Fetch stock information using yfinance"""
    try:
        stock = yf.Ticker(ticker)
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
        st.warning(f"Warning: Using fallback data fetching method for {ticker}")
        return {}

def get_historical_data(ticker, period='1y', interval='1d'):
    """
    Fetch historical price data with specified period and interval
    
    Parameters:
    - period: valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    - interval: valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
    """
    try:
        stock = yf.Ticker(ticker)
        hist_data = stock.history(period=period, interval=interval)
        
        if hist_data.empty:
            raise ValueError("No historical data found")
            
        return hist_data
    except Exception as e:
        raise Exception(f"Could not fetch historical data: {str(e)}")

def format_number(number):
    """Format large numbers with B/M suffix"""
    if isinstance(number, (int, float)):
        if number >= 1e9:
            return f"${number/1e9:.2f}B"
        elif number >= 1e6:
            return f"${number/1e6:.2f}M"
        else:
            return f"${number:,.2f}"
    return "N/A"

def format_ratio(value):
    """Format ratio values with proper error handling"""
    if isinstance(value, (int, float)) and value != 0:
        return f"{value:.2f}"
    return "N/A"

def format_percentage(value):
    """Format percentage values with proper error handling"""
    if isinstance(value, (int, float)):
        return f"{value:.2f}%"
    return "N/A"

def create_metric_chart(data, title, metric_type='price'):
    """Create a plotly chart for various metrics"""
    fig = go.Figure()
    
    if metric_type == 'price':
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            name='Price',
            line=dict(color='#ff7675')
        ))
    else:
        fig.add_trace(go.Bar(
            x=data.index,
            y=data[metric_type],
            name=metric_type,
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Value",
        template="plotly_white",
        height=400
    )
    
    return fig

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
        '10 Years': '10y',
        'Year to Date': 'ytd',
        'Max': 'max'
    }
    
    selected_period = st.sidebar.selectbox(
        "Select Time Period",
        options=list(period_options.keys()),
        index=5  # Default to 1 Year
    )
    
    # Add interval selection based on period
    interval_options = {
        '1 Day': ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h'],
        '5 Days': ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h'],
        '1 Month': ['5m', '15m', '30m', '60m', '90m', '1h', '1d'],
        '3 Months': ['5m', '15m', '30m', '60m', '90m', '1h', '1d'],
        '6 Months': ['15m', '30m', '60m', '90m', '1h', '1d'],
        '1 Year': ['30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo'],
        '2 Years': ['60m', '90m', '1h', '1d', '5d', '1wk', '1mo'],
        '5 Years': ['1d', '5d', '1wk', '1mo'],
        '10 Years': ['1d', '5d', '1wk', '1mo'],
        'Year to Date': ['1d', '5d', '1wk', '1mo'],
        'Max': ['1d', '5d', '1wk', '1mo']
    }
    
    available_intervals = interval_options[selected_period]
    interval_display = {
        '1m': '1 Minute', '2m': '2 Minutes', '5m': '5 Minutes',
        '15m': '15 Minutes', '30m': '30 Minutes', '60m': '1 Hour',
        '90m': '90 Minutes', '1h': '1 Hour', '1d': '1 Day',
        '5d': '5 Days', '1wk': '1 Week', '1mo': '1 Month'
    }
    
    selected_interval = st.sidebar.selectbox(
        "Select Interval",
        options=[interval_display[i] for i in available_intervals],
        index=len(available_intervals)-1  # Default to the last option
    )
    
    # Convert display name back to interval code
    interval_code = {v: k for k, v in interval_display.items()}[selected_interval]
    
    if st.sidebar.button("Search"):
        try:
            # Fetch data
            with st.spinner('Fetching stock data...'):
                market_data = get_stock_info(ticker)
                hist_data = get_historical_data(
                    ticker, 
                    period=period_options[selected_period],
                    interval=interval_code
                )
            
            # Display basic company info
            st.header(f"{market_data.get('longName', ticker)} ({ticker})")
            
            # Create columns for metrics
            col1, col2, col3 = st.columns(3)
            
            # Valuation metrics
            with col1:
                st.subheader("Valuation")
                st.write(f"Market Cap: {format_number(market_data.get('marketCap', 0))}")
                st.write(f"PE (TTM|FWD): {format_ratio(market_data.get('trailingPE'))} | {format_ratio(market_data.get('forwardPE'))}")
                st.write(f"Price To Sales: {format_ratio(market_data.get('priceToSales'))}")
                st.write(f"EV To EBITDA: {format_ratio(market_data.get('enterpriseToEbitda'))}")
                st.write(f"Price to Book: {format_ratio(market_data.get('priceToBook'))}")
            
            # Cash Flow metrics
            with col2:
                st.subheader("Cash Flow")
                if market_data.get('freeCashflow') and market_data.get('marketCap'):
                    fcf_yield = (market_data['freeCashflow'] / market_data['marketCap']) * 100
                    st.write(f"Free Cash Flow Yield: {format_percentage(fcf_yield)}")
                st.write(f"Operating Cash Flow: {format_number(market_data.get('operatingCashflow', 0))}")
                st.write(f"Free Cash Flow: {format_number(market_data.get('freeCashflow', 0))}")
            
            # Margins & Growth
            with col3:
                st.subheader("Margins & Balance")
                st.write(f"Profit Margin: {format_percentage(market_data.get('profitMargin', 0) * 100)}")
                st.write(f"Operating Margin: {format_percentage(market_data.get('operatingMargin', 0) * 100)}")
                st.write(f"Total Cash: {format_number(market_data.get('totalCash', 0))}")
                st.write(f"Total Debt: {format_number(market_data.get('totalDebt', 0))}")
                if market_data.get('totalCash') is not None and market_data.get('totalDebt') is not None:
                    net_debt = market_data['totalDebt'] - market_data['totalCash']
                    st.write(f"Net Debt: {format_number(net_debt)}")
            
            # Charts
            st.subheader("Price History")
            st.plotly_chart(create_metric_chart(hist_data, "Stock Price", 'price'))
            
            # Compare functionality
            st.subheader("Compare Stocks")
            compare_ticker = st.text_input("Enter ticker to compare:", "")
            
            if compare_ticker:
                try:
                    with st.spinner('Fetching comparison data...'):
                        compare_market_data = get_stock_info(compare_ticker)
                        compare_hist = get_historical_data(
                            compare_ticker,
                            period=period_options[selected_period],
                            interval=interval_code
                        )
                    
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
                    
                except Exception as e:
                    st.error(f"Error comparing with {compare_ticker}: {str(e)}")
                
        except Exception as e:
            st.error(f"Error analyzing {ticker}: {str(e)}")

if __name__ == "__main__":
    main()
