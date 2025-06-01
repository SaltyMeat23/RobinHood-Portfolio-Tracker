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
            "credentials_file": "credentials.json",
            "spreadsheet_name": os.getenv("SPREADSHEET_NAME"),
            "positions_sheet": "Sheet 1"
        }
    }
    
    return config