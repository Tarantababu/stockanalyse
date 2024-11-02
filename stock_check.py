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

        # Rest of the metrics (keeping them from previous code)
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
                ratios['ROIC (%)'] = (net_income / capital_employed) * 100 if capital_employed != 0 else np.nan
            
        except Exception as e:
            st.write(f"Error calculating other ratios: {str(e)}")
            ratios.update({
                'EPS Growth Rate (%)': np.nan,
                'Revenue Growth Rate (%)': np.nan,
                'Gross Margin (%)': np.nan,
                'Operating Margin (%)': np.nan,
                'ROCE (%)': np.nan,
                'ROIC (%)': np.nan
            })
        
        return ratios, None
        
    except Exception as e:
        return None, f"Error processing {ticker}: {str(e)}"
