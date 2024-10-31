import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import json
import re  # Added missing import for regular expressions

def get_yahoo_data(ticker):
    """Fetch data directly from Yahoo Finance website"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Get summary data
    url = f"https://finance.yahoo.com/quote/{ticker}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Get statistics data
    stats_url = f"https://finance.yahoo.com/quote/{ticker}/key-statistics"
    stats_response = requests.get(stats_url, headers=headers)
    stats_soup = BeautifulSoup(stats_response.text, 'html.parser')
    
    # Extract data from the page
    market_data = {}
    try:
        # Find the script containing the market data
        pattern = re.compile(r'root\.App\.main = (.*);')
        script_data = soup.find('script', text=pattern).string
        if script_data:
            json_data = pattern.search(script_data).group(1)
            data = json.loads(json_data)
            
            # Extract relevant information from the JSON data
            quote_summary = data['context']['dispatcher']['stores']['QuoteSummaryStore']
            
            # Basic Info
            market_data['longName'] = quote_summary.get('price', {}).get('longName', '')
            market_data['regularMarketPrice'] = quote_summary.get('price', {}).get('regularMarketPrice', {}).get('raw', 0)
            market_data['marketCap'] = quote_summary.get('price', {}).get('marketCap', {}).get('raw', 0)
            
            # Valuation Measures
            market_data['trailingPE'] = quote_summary.get('summaryDetail', {}).get('trailingPE', {}).get('raw', 0)
            market_data['forwardPE'] = quote_summary.get('summaryDetail', {}).get('forwardPE', {}).get('raw', 0)
            market_data['priceToSales'] = quote_summary.get('summaryDetail', {}).get('priceToSalesTrailing12Months', {}).get('raw', 0)
            market_data['priceToBook'] = quote_summary.get('defaultKeyStatistics', {}).get('priceToBook', {}).get('raw', 0)
            market_data['enterpriseToEbitda'] = quote_summary.get('defaultKeyStatistics', {}).get('enterpriseToEbitda', {}).get('raw', 0)
            
            # Financial Highlights
            market_data['profitMargin'] = quote_summary.get('financialData', {}).get('profitMargins', {}).get('raw', 0)
            market_data['operatingMargin'] = quote_summary.get('financialData', {}).get('operatingMargins', {}).get('raw', 0)
            market_data['returnOnEquity'] = quote_summary.get('financialData', {}).get('returnOnEquity', {}).get('raw', 0)
            market_data['returnOnAssets'] = quote_summary.get('financialData', {}).get('returnOnAssets', {}).get('raw', 0)
            
            # Balance Sheet
            market_data['totalCash'] = quote_summary.get('financialData', {}).get('totalCash', {}).get('raw', 0)
            market_data['totalDebt'] = quote_summary.get('financialData', {}).get('totalDebt', {}).get('raw', 0)
            market_data['debtToEquity'] = quote_summary.get('financialData', {}).get('debtToEquity', {}).get('raw', 0)
            
            # Cash Flow
            market_data['operatingCashflow'] = quote_summary.get('financialData', {}).get('operatingCashflow', {}).get('raw', 0)
            market_data['freeCashflow'] = quote_summary.get('financialData', {}).get('freeCashflow', {}).get('raw', 0)
            
    except Exception as e:
        st.error(f"Error parsing Yahoo Finance data: {str(e)}")
        
    return market_data

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
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return "N/A"

def get_stock_data(ticker):
    """Fetch both yfinance and Yahoo Finance website data"""
    try:
        # Get yfinance data
        stock = yf.Ticker(ticker)
        
        # Get historical data for TTM metrics
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*2)
        hist_data = stock.history(start=start_date, end=end_date)
        
        # Get Yahoo Finance website data
        market_data = get_yahoo_data(ticker)
        
        if hist_data.empty:
            raise ValueError(f"No historical data found for {ticker}")
            
        return stock, market_data, hist_data
    
    except Exception as e:
        raise Exception(f"Error fetching data for {ticker}: {str(e)}")

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
    
    # Sidebar for stock selection
    st.sidebar.header("Stock Selection")
    ticker = st.sidebar.text_input("Enter Stock Ticker:", value="AAPL").upper()
    
    if st.sidebar.button("Search"):
        try:
            stock, market_data, hist_data = get_stock_data(ticker)
            
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
                    st.write(f"Free Cash Flow Yield: {format_ratio(fcf_yield)}%")
                st.write(f"Operating Cash Flow: {format_number(market_data.get('operatingCashflow', 0))}")
                st.write(f"Free Cash Flow: {format_number(market_data.get('freeCashflow', 0))}")
            
            # Margins & Growth
            with col3:
                st.subheader("Margins & Balance")
                st.write(f"Profit Margin: {format_ratio(market_data.get('profitMargin', 0) * 100)}%")
                st.write(f"Operating Margin: {format_ratio(market_data.get('operatingMargin', 0) * 100)}%")
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
                compare_stock, compare_market_data, compare_hist = get_stock_data(compare_ticker)
                
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
            st.error(f"Error fetching data for {ticker}. Please check the ticker symbol and try again.")
            st.error(str(e))

if __name__ == "__main__":
    main()
