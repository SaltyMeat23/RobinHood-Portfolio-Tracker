# update_option_positions.py - Cleaned version

import os
import random
import time
from datetime import datetime
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import robin_stocks.robinhood as r
from config import load_config
from option_utils import (get_option_data_batch, get_simplified_account_data, 
                         get_stock_positions_for_cc_detection, simplified_strategy_detection,
                         get_total_portfolio_value)

def sleep_with_jitter(base_seconds):
    """Sleep with minimal jitter."""
    jitter = base_seconds * random.uniform(0.8, 1.2)
    time.sleep(base_seconds + jitter)

def setup_google_sheets(credentials_file):
    """Initialize Google Sheets connection."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
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





def process_option_positions_efficiently(main_account_id, ira_account_id, config):
    """Process option positions with optimized API usage."""
    combined_positions = []
    
    # Get main account positions
    if main_account_id:
        try:
            main_options = get_open_option_positions(account_number=main_account_id)
            for option in main_options:
                option['account_type'] = 'Main'
                option['account_number'] = main_account_id
                combined_positions.append(option)
        except Exception:
            pass
    
    # Only get IRA positions if IRA account ID is provided and different from main
    if ira_account_id and ira_account_id != main_account_id:
        try:
            ira_options = get_open_option_positions(account_number=ira_account_id)
            for option in ira_options:
                option['account_type'] = 'IRA'
                option['account_number'] = ira_account_id
                combined_positions.append(option)
        except Exception:
            pass
    
    if not combined_positions:
        return []
    
    option_ids = [pos.get('option_id') for pos in combined_positions if pos.get('option_id')]
    
    if not option_ids:
        return []
    
    # Remove duplicates based on option_id to prevent duplicate entries
    seen_option_ids = set()
    unique_positions = []
    for position in combined_positions:
        option_id = position.get('option_id')
        if option_id and option_id not in seen_option_ids:
            seen_option_ids.add(option_id)
            unique_positions.append(position)
    
    combined_positions = unique_positions
    
    option_data, market_data = get_option_data_batch(option_ids)
    account_data = get_simplified_account_data([acc for acc in [main_account_id, ira_account_id] if acc], ira_account_id)
    stock_collateral = get_stock_positions_for_cc_detection([acc for acc in [main_account_id, ira_account_id] if acc])
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


def update_sheet_efficiently(sheet, enriched_positions, total_portfolio_value, config):
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
    try:
        config = load_config()
        
        main_account_id = config["robinhood"]["account_id"]
        ira_account_id = config["robinhood"]["ira_account_id"]
        username = config["robinhood"]["username"]
        password = config["robinhood"]["password"]
        
        if not main_account_id:
            raise ValueError("MAIN_ACCOUNT environment variable must be set")
        
        if not ira_account_id:
            print("⚠️ No IRA_ACCOUNT found, processing main account only")
        
        r.login(username, password, expiresIn=86400, store_session=True)
        
        client = setup_google_sheets(config["google_sheets"]["credentials_file"])
        spreadsheet = client.open(config["google_sheets"]["spreadsheet_name"])
        options_sheet = get_or_create_sheet(spreadsheet, config["google_sheets"]["option_positions_sheet"])
        
        enriched_positions, total_portfolio_value = process_option_positions_efficiently(
            main_account_id, ira_account_id, config
        )
        
        if not enriched_positions:
            options_sheet.update_cell(1, 1, "No option positions found")
            return
        
        update_sheet_efficiently(options_sheet, enriched_positions, total_portfolio_value, config)
        
        print("✅ Option positions update completed")
    
    except Exception as e:
        print(f"❌ Error updating option positions: {e}")
    finally:
        try:
            r.logout()
        except:
            pass