# multi_account_handler.py - Cleaned version

import robin_stocks.robinhood as r

def get_all_accounts():
    """Get all available accounts from Robinhood."""
    try:
        return r.account.get_all_accounts()
    except Exception:
        return []

def format_account_numbers_param(account_ids):
    """Format account numbers for use in API requests."""
    if not account_ids:
        return None
        
    valid_accounts = [acc for acc in account_ids if acc]
    
    if not valid_accounts:
        return None
        
    return ','.join(valid_accounts)

def get_multi_account_options_orders(account_ids):
    """Get options orders for multiple accounts in a single API call."""
    account_numbers = format_account_numbers_param(account_ids)
    
    if not account_numbers:
        return []
    
    try:
        options_orders = r.orders.get_all_option_orders(account_numbers=account_numbers)
        return options_orders
    except Exception:
        return []

def get_multi_account_positions(account_ids):
    """Get positions for multiple accounts."""
    all_positions = []
    
    for account_id in account_ids:
        if not account_id:
            continue
            
        try:
            positions = r.account.get_all_positions(account_number=account_id)
            
            for position in positions:
                position['account_id'] = account_id
                
            all_positions.extend(positions)
        except Exception:
            pass
    
    return all_positions

def get_account_type_mapping(account_ids=None):
    """Create a mapping of account IDs to account types."""
    mapping = {}
    
    try:
        accounts = r.account.get_all_accounts()
        
        for account in accounts:
            account_id = account.get('account_number')
            
            if account_ids and account_id not in account_ids:
                continue
                
            account_type = "Standard"
            
            account_type_field = account.get('type')
            if account_type_field:
                if 'ira' in account_type_field.lower():
                    account_type = "IRA"
            
            mapping[account_id] = account_type
    except Exception:
        pass
    
    return mapping

def enrich_orders_with_account_info(orders, account_mapping=None):
    """Add account type information to orders."""
    if not account_mapping:
        account_mapping = get_account_type_mapping()
    
    enriched_orders = []
    
    for order in orders:
        enriched = order.copy()
        
        account_id = order.get('account_id')
        if account_id and account_id in account_mapping:
            enriched['account_type'] = account_mapping[account_id]
        else:
            enriched['account_type'] = "Unknown"
            
        enriched_orders.append(enriched)
    
    return enriched_orders