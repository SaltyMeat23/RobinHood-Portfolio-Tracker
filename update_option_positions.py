# update_option_positions.py - Cleaned version

import os
import random
import time
from datetime import datetime
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import robin_stocks.robinhood as r

SHEET_NAME = "TD Tracker - May Update"
POSITION_SHEET_NAME = "Option Positions"

def sleep_with_jitter(base_seconds):
    """Sleep with minimal jitter."""
    jitter = base_seconds * random.uniform(0.8, 1.2)
    time.sleep(base_seconds + jitter)

def setup_google_sheets():
    """Initialize Google Sheets connection."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    return client

def get_or_create_sheet(spreadsheet, sheet_name):
    """Get existing sheet or create a new one."""
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)

def get_open_option_positions(account_number=None):
    """Get all open option positions for the specified account."""
    try:
        return r.get_open_option_positions(account_number=account_number)
    except Exception:
        return []

def get_option_data_batch(option_ids):
    """Get option instrument and market data in batch."""
    option_data = {}
    market_data = {}
    
    for option_id in option_ids:
        try:
            instrument = r.get_option_instrument_data_by_id(option_id)
            if isinstance(instrument, list) and instrument:
                instrument = instrument[0]
            option_data[option_id] = instrument or {}
            
            market = r.get_option_market_data_by_id(option_id)
            if isinstance(market, list) and market:
                market = market[0]
            market_data[option_id] = market or {}
            
            time.sleep(0.3)
            
        except Exception:
            option_data[option_id] = {}
            market_data[option_id] = {}
    
    return option_data, market_data

def get_simplified_account_data(account_ids):
    """Get essential account data for strategy detection."""
    account_data = {}
    
    for account_id in account_ids:
        try:
            account_info = r.load_account_profile(account_number=account_id)
            account_data[account_id] = {
                'cash_for_options': float(account_info.get('cash_held_for_options_collateral', 0)),
                'type': 'IRA' if account_id == '519517908' else 'Standard'
            }
        except Exception:
            account_data[account_id] = {'cash_for_options': 0, 'type': 'Unknown'}
    
    return account_data

def get_stock_positions_for_cc_detection(account_ids):
    """Get stock positions for covered call detection."""
    stock_collateral = {}
    
    for account_id in account_ids:
        try:
            positions = r.get_open_stock_positions(account_number=account_id)
            
            for position in positions:
                try:
                    instrument_url = position.get('instrument')
                    if not instrument_url:
                        continue
                        
                    instrument_data = r.get_instrument_by_url(instrument_url)
                    symbol = instrument_data.get('symbol', '')
                    
                    if symbol:
                        shares_total = float(position.get('quantity', 0))
                        shares_collateral = float(position.get('shares_held_for_options_collateral', 0))
                        
                        if symbol not in stock_collateral:
                            stock_collateral[symbol] = {}
                        
                        stock_collateral[symbol][account_id] = {
                            'total_shares': shares_total,
                            'collateral_shares': shares_collateral
                        }
                        
                    time.sleep(0.2)
                    
                except Exception:
                    continue
                    
        except Exception:
            continue
    
    return stock_collateral

def simplified_strategy_detection(position, account_data, stock_collateral):
    """Detect option strategy type."""
    symbol = position.get('symbol', '')
    option_type = position.get('option_type', '').upper()
    strike_price = float(position.get('strike_price', 0))
    account_id = position.get('account_number', '')
    quantity = float(position.get('quantity', 0))
    
    strategy = f"{option_type} Position"
    
    if option_type == 'CALL' and symbol in stock_collateral:
        account_stocks = stock_collateral[symbol].get(account_id, {})
        
        collateral_shares = account_stocks.get('collateral_shares', 0)
        if collateral_shares >= (quantity * 100):
            strategy = "Covered Call (CC)"
        else:
            total_shares = account_stocks.get('total_shares', 0)
            if total_shares >= (quantity * 100):
                strategy = "Covered Call (CC) - Holdings"
    
    elif option_type == 'PUT':
        account_info = account_data.get(account_id, {})
        cash_for_options = account_info.get('cash_for_options', 0)
        required_cash = strike_price * quantity * 100
        
        if cash_for_options >= required_cash * 0.9:
            strategy = "Cash-Secured Put (CSP)"
    
    return strategy

def process_option_positions_efficiently(main_account_id, ira_account_id):
    """Process option positions with optimized API usage."""
    main_options = get_open_option_positions(account_number=main_account_id)
    ira_options = get_open_option_positions(account_number=ira_account_id)
    
    combined_positions = []
    
    for option in main_options:
        option['account_type'] = 'Main'
        option['account_number'] = main_account_id
        combined_positions.append(option)
    
    for option in ira_options:
        option['account_type'] = 'IRA'
        option['account_number'] = ira_account_id
        combined_positions.append(option)
    
    if not combined_positions:
        return []
    
    option_ids = [pos.get('option_id') for pos in combined_positions if pos.get('option_id')]
    
    if not option_ids:
        return []
    
    option_data, market_data = get_option_data_batch(option_ids)
    account_data = get_simplified_account_data([main_account_id, ira_account_id])
    stock_collateral = get_stock_positions_for_cc_detection([main_account_id, ira_account_id])
    total_portfolio_value = get_total_portfolio_value()
    
    enriched_positions = []
    
    for position in combined_positions:
        option_id = position.get('option_id')
        if not option_id or option_id not in option_data:
            continue
        
        opt_data = option_data[option_id]
        mkt_data = market_data[option_id]
        
        if not opt_data or not mkt_data:
            continue
        
        position['symbol'] = opt_data.get('chain_symbol', 'N/A')
        position['strike_price'] = opt_data.get('strike_price', 'N/A')
        position['expiration_date'] = opt_data.get('expiration_date', 'N/A')
        position['option_type'] = opt_data.get('type', 'N/A').upper()
        
        try:
            position['quantity'] = float(position.get('quantity', 0))
            position['average_price'] = float(position.get('average_price', 0))
            position['current_price'] = float(mkt_data.get('adjusted_mark_price', 0))
        except (ValueError, TypeError):
            position['quantity'] = 0
            position['average_price'] = 0
            position['current_price'] = 0
        
        total_value = position['current_price'] * position['quantity'] * 100
        position['total_value'] = total_value
        position['allocation_percentage'] = (total_value / total_portfolio_value * 100 
                                           if total_portfolio_value > 0 else 0)
        
        position['delta'] = mkt_data.get('delta', 'N/A')
        position['theta'] = mkt_data.get('theta', 'N/A')
        position['gamma'] = mkt_data.get('gamma', 'N/A')
        position['vega'] = mkt_data.get('vega', 'N/A')
        position['implied_volatility'] = mkt_data.get('implied_volatility', 'N/A')
        position['open_interest'] = mkt_data.get('open_interest', 'N/A')
        
        position['strategy_type'] = simplified_strategy_detection(
            position, account_data, stock_collateral
        )
        
        enriched_positions.append(position)
    
    return enriched_positions, total_portfolio_value

def get_total_portfolio_value():
    """Get total portfolio value."""
    try:
        phoenix_data = r.account.load_phoenix_account()
        if phoenix_data and 'total_equity' in phoenix_data:
            return float(phoenix_data.get('total_equity', 0))
    except Exception:
        pass
    
    return 100000.0

def update_sheet_efficiently(sheet, enriched_positions, total_portfolio_value):
    """Update sheet with minimal API calls."""
    enriched_positions.sort(key=lambda x: x.get('allocation_percentage', 0), reverse=True)
    
    headers = [
        'Account', 'Symbol', 'Strike Price', 'Expiration Date', 
        'Option Type', 'Strategy Type', 'Quantity', 'Average Price', 'Current Price',
        'Total Value', 'Allocation %', 'Implied Volatility', 'Delta', 
        'Theta', 'Gamma', 'Vega', 'Open Interest'
    ]
    
    rows = [
        ["Option Positions"],
        [f"Total Portfolio Value: ${total_portfolio_value:.2f}"],
        [""],
        headers
    ]
    
    for position in enriched_positions:
        option_row = [
            position.get('account_type', 'Unknown'),
            position.get('symbol', 'N/A'),
            position.get('strike_price', 'N/A'),
            position.get('expiration_date', 'N/A'),
            position.get('option_type', 'N/A'),
            position.get('strategy_type', 'N/A'),
            position.get('quantity', 0),
            f"${position.get('average_price', 0):.2f}",
            f"${position.get('current_price', 0):.2f}",
            f"${position.get('total_value', 0):.2f}",
            f"{position.get('allocation_percentage', 0):.2f}%",
            position.get('implied_volatility', 'N/A'),
            position.get('delta', 'N/A'),
            position.get('theta', 'N/A'),
            position.get('gamma', 'N/A'),
            position.get('vega', 'N/A'),
            position.get('open_interest', 'N/A')
        ]
        rows.append(option_row)
    
    sheet.clear()
    sleep_with_jitter(1.0)
    
    sheet.update(values=rows, range_name="A1")
    sleep_with_jitter(1.0)
    
    sheet.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
    sleep_with_jitter(0.5)
    
    sheet.format("A4:Q4", {"textFormat": {"bold": True}})

def main():
    """Main execution function."""
    load_dotenv()
    username = os.getenv("ROBINHOOD_USER")
    password = os.getenv("ROBINHOOD_PASS")
    main_account_id = os.getenv("MAIN_ACCOUNT") or "5QU52702"
    ira_account_id = os.getenv("traditional_Ira") or "519517908"
    
    try:
        r.login(username, password, expiresIn=86400, store_session=True)
        
        client = setup_google_sheets()
        spreadsheet = client.open(SHEET_NAME)
        options_sheet = get_or_create_sheet(spreadsheet, POSITION_SHEET_NAME)
        
        enriched_positions, total_portfolio_value = process_option_positions_efficiently(
            main_account_id, ira_account_id
        )
        
        if not enriched_positions:
            options_sheet.update_cell(1, 1, "No option positions found")
            return
        
        update_sheet_efficiently(options_sheet, enriched_positions, total_portfolio_value)
        
        print("✅ Option positions update completed")
    
    except Exception as e:
        print(f"❌ Error updating option positions: {e}")
    finally:
        try:
            r.logout()
        except:
            pass

if __name__ == "__main__":
    main()