# options_orders.py - Cleaned version

import robin_stocks.robinhood as r
from datetime import datetime, timedelta
import pytz
from rate_limit_handler import retry_on_rate_limit, sleep_with_jitter

def get_ira_option_orders(account_number, page_size=50, cursor=None):
    """Custom function for IRA account options orders."""
    url = "https://api.robinhood.com/options/orders/"
    params = {'account_numbers': account_number, 'page_size': page_size}
    if cursor:
        params['cursor'] = cursor
    
    response = r.request_get(url, 'regular', params)
    return response

def get_all_ira_option_orders(account_number, max_pages=10):
    """Get all options orders for IRA account across multiple pages."""
    all_orders = []
    cursor = None
    
    for page in range(1, max_pages + 1):
        response = get_ira_option_orders(account_number, cursor=cursor)
        if not response or 'results' not in response:
            break
            
        orders = response['results']
        if not orders:
            break
            
        all_orders.extend(orders)
        
        if 'next' not in response or not response['next']:
            break
            
        next_url = response['next']
        cursor = next_url.split('cursor=')[1].split('&')[0] if 'cursor=' in next_url else None
        if not cursor:
            break
            
        sleep_with_jitter(1.0)
    
    return all_orders

def get_all_options_orders(account_number=None):
    """Retrieve all options orders."""
    try:
        if account_number == '519517908':
            orders = get_all_ira_option_orders(account_number)
            
            if orders and account_number:
                for order in orders:
                    order['account_id'] = account_number
            
            return orders
        
        options_orders = r.get_all_option_orders(account_number=account_number)
        
        if isinstance(options_orders, dict) and 'results' in options_orders:
            orders = options_orders['results']
        elif isinstance(options_orders, list):
            orders = options_orders
        else:
            return []
            
        if orders and account_number:
            for order in orders:
                order['account_id'] = account_number
        
        return orders
        
    except Exception:
        return []

def format_date(date_string):
    """Format Robinhood date strings."""
    if not date_string:
        return ''
    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        eastern = pytz.timezone('US/Eastern')
        dt = dt.astimezone(eastern)
        return dt.strftime('%m/%d/%Y %I:%M %p')
    except Exception:
        return date_string

def safe_float(value, default=0.0):
    """Safely convert value to float."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace('$', '').replace(',', '').strip())
        except (ValueError, TypeError):
            return default
    return default

def extract_quantity(order):
    """Extract quantity from order legs."""
    quantity = 0
    if 'legs' in order and isinstance(order['legs'], list):
        for leg in order['legs']:
            leg_qty = safe_float(leg.get('quantity', 0))
            if leg_qty > 0:
                quantity += leg_qty
    
    if quantity == 0:
        quantity = safe_float(order.get('quantity', 0))
    
    return quantity

def enrich_option_orders(orders):
    """Enhance orders with additional information."""
    enriched_orders = []
    
    account_mapping = {
        '5QU52702': 'Standard',
        '519517908': 'IRA',
        '410351639': 'Third'
    }
    
    for order in orders:
        try:
            enriched = order.copy()
            
            account_number = order.get('account_number', 'Unknown')
            enriched['account_type'] = account_mapping.get(account_number, 'Unknown')
            
            enriched['created_at_formatted'] = format_date(order.get('created_at'))
            enriched['updated_at_formatted'] = format_date(order.get('updated_at'))
            
            enriched['symbol'] = order.get('chain_symbol', 'Unknown')
            premium = safe_float(order.get('processed_premium', 0)) or safe_float(order.get('premium', 0))
            enriched['total_premium'] = premium
            
            quantity = extract_quantity(order)
            enriched['quantity'] = quantity
            enriched['premium_per_contract'] = premium / quantity if quantity > 0 else 0
            
            direction = order.get('direction', '').lower()
            if direction == 'debit':
                enriched['direction_formatted'] = "Buy (Debit)"
            elif direction == 'credit':
                enriched['direction_formatted'] = "Sell (Credit)"
            else:
                enriched['direction_formatted'] = direction.capitalize() if direction else "Unknown"
            
            if 'legs' in order and order['legs']:
                option_types = set()
                strikes = set()
                expirations = set()
                
                for leg in order['legs']:
                    if leg.get('option_type'):
                        option_types.add(leg['option_type'].upper())
                    strike = safe_float(leg.get('strike_price', 0))
                    if strike > 0:
                        strikes.add(strike)
                    if leg.get('expiration_date'):
                        expirations.add(leg['expiration_date'])
                
                enriched['option_types'] = '/'.join(sorted(option_types)) if option_types else "Unknown"
                enriched['strikes'] = '/'.join([f"${strike:.2f}" for strike in sorted(strikes)]) if strikes else "N/A"
                enriched['expirations'] = '/'.join(sorted(expirations)) if expirations else "N/A"
                
                leg_count = len(order['legs'])
                if leg_count == 1:
                    enriched['strategy'] = f"Single {next(iter(option_types), 'Option')}"
                elif leg_count == 2:
                    if len(option_types) == 1 and len(strikes) == 2:
                        enriched['strategy'] = f"{next(iter(option_types))} Vertical"
                    elif len(option_types) == 2 and len(strikes) == 1:
                        enriched['strategy'] = "Straddle"
                    elif len(option_types) == 2 and len(strikes) == 2:
                        enriched['strategy'] = "Strangle"
                    else:
                        enriched['strategy'] = "2-Leg Strategy"
                else:
                    enriched['strategy'] = f"{leg_count}-Leg Strategy"
            else:
                enriched['option_types'] = "Unknown"
                enriched['strikes'] = "N/A"
                enriched['expirations'] = "N/A"
                enriched['strategy'] = "Unknown"
            
            enriched_orders.append(enriched)
            
        except Exception:
            enriched_orders.append(order)
    
    return enriched_orders

def calculate_weekly_premium_stats(orders, weeks_back=8):
    """Calculate weekly premium statistics."""
    weekly_stats = {}
    account_stats = {}
    
    today = datetime.now(pytz.UTC)
    cutoff_date = today - timedelta(weeks=weeks_back)
    
    account_mapping = {'5QU52702': 'Standard', '519517908': 'IRA', '410351639': 'Third'}
    
    for order in orders:
        try:
            if order.get('state', '').lower() != 'filled':
                continue
                
            date_str = order.get('created_at', '')
            if not date_str:
                continue
                
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if dt < cutoff_date:
                continue
            
            week_start = dt - timedelta(days=dt.weekday())
            week_key = week_start.strftime('%Y-%m-%d')
            account_type = account_mapping.get(order.get('account_id', ''), 'Unknown')
            
            if week_key not in weekly_stats:
                weekly_stats[week_key] = {'premium': 0.0, 'btc_premium': 0.0, 'count': 0}
            if account_type not in account_stats:
                account_stats[account_type] = {}
            if week_key not in account_stats[account_type]:
                account_stats[account_type][week_key] = {'premium': 0.0, 'btc_premium': 0.0, 'count': 0}
            
            premium = float(order.get('total_premium', 0.0))
            if premium <= 0:
                continue
                
            direction = order.get('direction', '').lower()
            is_sell = 'sell' in direction or 'credit' in direction
            is_buy = 'buy' in direction or 'debit' in direction
            
            weekly_stats[week_key]['count'] += 1
            account_stats[account_type][week_key]['count'] += 1
            
            if is_sell:
                weekly_stats[week_key]['premium'] += premium
                account_stats[account_type][week_key]['premium'] += premium
            elif is_buy:
                weekly_stats[week_key]['btc_premium'] += premium
                account_stats[account_type][week_key]['btc_premium'] += premium
                
        except Exception:
            continue
    
    for stats in weekly_stats.values():
        stats['net_premium'] = stats['premium'] - stats['btc_premium']
    
    for account_weeks in account_stats.values():
        for stats in account_weeks.values():
            stats['net_premium'] = stats['premium'] - stats['btc_premium']
    
    sorted_weeks = sorted(weekly_stats.items(), key=lambda x: x[0], reverse=True)
    sorted_accounts = {acc: sorted(weeks.items(), key=lambda x: x[0], reverse=True) 
                      for acc, weeks in account_stats.items()}
    
    return sorted_weeks, sorted_accounts

def create_fixed_weekly_table(account_type, account_stats, start_row, weeks_to_show=8):
    """Create a fixed-position weekly premium table for a specific account."""
    table_data = [
        [f"{account_type} Weekly Premium Summary"],
        ["Week", "Total Premium", "BTC Premium", "Net Premium"]
    ]
    
    today = datetime.now()
    
    for i in range(weeks_to_show):
        week_start = today - timedelta(days=today.weekday() + (i * 7))
        week_key = week_start.strftime('%Y-%m-%d')
        
        week_stats = None
        if account_type in account_stats:
            for week, stats in account_stats[account_type]:
                if week == week_key:
                    week_stats = stats
                    break
        
        if week_stats:
            total_premium = week_stats.get('premium', 0.0)
            btc_premium = week_stats.get('btc_premium', 0.0)
            net_premium = week_stats.get('net_premium', 0.0)
        else:
            total_premium = btc_premium = net_premium = 0.0
        
        table_data.append([
            week_key,
            f"${total_premium:.2f}",
            f"${btc_premium:.2f}",
            f"${net_premium:.2f}"
        ])
    
    return table_data, start_row + len(table_data) + 2

@retry_on_rate_limit
def update_options_orders_sheet(sheet, orders):
    """Update sheet with options orders and fixed account tables."""
    if not orders:
        sheet.update_cell(1, 1, "No options orders found")
        return
    
    sheet.clear()
    sleep_with_jitter(3.0)
    
    enriched_orders = enrich_option_orders(orders)
    filtered_orders = [order for order in enriched_orders if order.get('state', '').lower() != 'cancelled']
    sorted_orders = sorted(filtered_orders, key=lambda x: x.get('created_at', ''), reverse=True)
    
    weekly_stats, account_stats = calculate_weekly_premium_stats(enriched_orders)
    
    headers = ["Date", "Account", "Symbol", "Strategy", "Direction", 
               "Option Types", "Strike Prices", "Expiration", "Quantity", "Premium", "State"]
    
    main_table = [["Options Order History"], [""], headers]
    
    for order in sorted_orders[:20]:
        try:
            premium = safe_float(order.get('total_premium', 0))
            row = [
                order.get('created_at_formatted', ''),
                order.get('account_type', 'Unknown'),
                order.get('symbol', 'N/A'),
                order.get('strategy', 'N/A'),
                order.get('direction_formatted', 'N/A'),
                order.get('option_types', 'N/A'),
                order.get('strikes', 'N/A'),
                order.get('expirations', 'N/A'),
                order.get('quantity', 0),
                f"${premium:.2f}",
                order.get('state', 'N/A').capitalize()
            ]
            main_table.append(row)
        except Exception:
            continue
    
    sheet.update(values=main_table, range_name="A1")
    sleep_with_jitter(3.0)
    
    account_positions = {
        'Standard': 25,
        'IRA': 36,
        'Third': 47
    }
    
    for account_type in ['Standard', 'IRA', 'Third']:
        start_row = account_positions[account_type]
        
        table_data, next_row = create_fixed_weekly_table(account_type, account_stats, start_row)
        
        end_row = start_row + len(table_data) - 1
        range_name = f"A{start_row}:D{end_row}"
        
        try:
            sheet.update(values=table_data, range_name=range_name)
            sleep_with_jitter(2.0)
            
            header_cell = f"A{start_row}"
            sheet.format(header_cell, {"textFormat": {"bold": True, "fontSize": 12}})
            sleep_with_jitter(1.0)
            
            column_header_row = start_row + 1
            header_range = f"A{column_header_row}:D{column_header_row}"
            sheet.format(header_range, {"textFormat": {"bold": True}})
            sleep_with_jitter(1.0)
            
        except Exception:
            pass
    
    try:
        sheet.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
        sheet.format("A3:K3", {"textFormat": {"bold": True}})
    except Exception:
        pass

def process_options_orders(spreadsheet, main_account_id=None, ira_account_id=None):
    """Main processing function."""
    
    try:
        all_orders = []
        
        for account_id, account_name in [(main_account_id, "main"), (ira_account_id, "IRA")]:
            if account_id:
                try:
                    orders = get_all_options_orders(account_number=account_id)
                    if orders:
                        all_orders.extend(orders)
                except Exception:
                    pass
        
        if not all_orders:
            return []
        
        try:
            options_orders_sheet = spreadsheet.worksheet("Options Orders")
            options_orders_sheet.clear()
        except:
            options_orders_sheet = spreadsheet.add_worksheet(title="Options Orders", rows=1000, cols=20)
        
        update_options_orders_sheet(options_orders_sheet, all_orders)
        
        return all_orders
        
    except Exception:
        return []