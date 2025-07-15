# config.py - Updated for Github safety

import os
from dotenv import load_dotenv

def load_config():
    """Load configuration from environment variables."""
    load_dotenv()
    
    # Validate required environment variables
    required_vars = [
        "ROBINHOOD_USER",
        "ROBINHOOD_PASS",
        "MAIN_ACCOUNT",
        "SPREADSHEET_NAME"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    config = {
        "robinhood": {
            "username": os.getenv("ROBINHOOD_USER"),
            "password": os.getenv("ROBINHOOD_PASS"),
            "account_id": os.getenv("MAIN_ACCOUNT"),
            "ira_account_id": os.getenv("IRA_ACCOUNT"),
            "third_account_id": os.getenv("THIRD_ACCOUNT")
        },
        "google_sheets": {
            "credentials_file": os.getenv("CREDENTIALS_FILE", "credentials.json"),
            "spreadsheet_name": os.getenv("SPREADSHEET_NAME"),
            "positions_sheet": os.getenv("POSITIONS_SHEET", "Sheet 1"),
            "option_positions_sheet": os.getenv("OPTION_POSITIONS_SHEET", "Option Positions"),
            "options_orders_sheet": os.getenv("OPTIONS_ORDERS_SHEET", "Options Orders"),
            "account_balances_sheet": os.getenv("ACCOUNT_BALANCES_SHEET", "Account Balances"),
            "all_stock_positions_sheet": os.getenv("ALL_STOCK_POSITIONS_SHEET", "All Stock Positions")
        }
    }
    
    return config