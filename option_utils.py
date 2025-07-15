# option_utils.py - Shared utilities for option processing

import time
import robin_stocks.robinhood as r
from rate_limit_handler import sleep_with_jitter


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


def get_simplified_account_data(account_ids, ira_account_id=None):
    """Get essential account data for strategy detection."""
    account_data = {}
    
    for account_id in account_ids:
        try:
            account_info = r.load_account_profile(account_number=account_id)
            account_data[account_id] = {
                'cash_for_options': float(account_info.get('cash_held_for_options_collateral', 0)),
                'type': 'IRA' if account_id == ira_account_id else 'Standard'
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


def get_total_portfolio_value():
    """Get total portfolio value."""
    try:
        phoenix_data = r.account.load_phoenix_account()
        if phoenix_data and 'total_equity' in phoenix_data:
            return float(phoenix_data.get('total_equity', 0))
    except Exception:
        pass
    
    return 100000.0


def get_account_type_mapping(main_account_id, ira_account_id, third_account_id=None):
    """Create account type mapping based on provided account IDs."""
    mapping = {}
    
    if main_account_id:
        mapping[main_account_id] = 'Standard'
    if ira_account_id:
        mapping[ira_account_id] = 'IRA'
    if third_account_id:
        mapping[third_account_id] = 'Third'
    
    return mapping