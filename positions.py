# positions.py - Cleaned version

import robin_stocks.robinhood as r
import time
from rate_limit_handler import sleep_with_jitter

def calculate_current_value(symbol, quantity):
    """Calculate current value of position based on latest price."""
    if not symbol or not quantity:
        return "0.00"
    
    try:
        qty = float(quantity)
        
        try:
            latest_price = r.get_latest_price(symbol)
            
            if latest_price and len(latest_price) > 0 and latest_price[0] is not None:
                price = float(latest_price[0])
                return f"{price * qty:.2f}"
            else:
                return "0.00"
        except Exception:
            return "0.00"
    except Exception:
        return "0.00"

def calculate_total_portfolio_value(positions=None):
    """Calculate total portfolio value from phoenix account or positions."""
    total_value = 0.0
    
    try:
        phoenix_data = r.account.load_phoenix_account()
        if phoenix_data:
            if 'total_equity' in phoenix_data:
                total_equity = float(phoenix_data.get('total_equity', 0))
                total_value += total_equity
                return total_value
            
            if 'portfolio_equity' in phoenix_data:
                portfolio_equity = float(phoenix_data.get('portfolio_equity', 0))
                total_value += portfolio_equity
                return total_value
    except Exception:
        pass
    
    if positions:
        for position in positions:
            instrument_url = position.get('instrument')
            quantity = position.get('quantity', '0')
            
            if instrument_url and quantity:
                try:
                    instrument_data = r.get_instrument_by_url(instrument_url)
                    symbol = instrument_data.get('symbol', 'N/A')
                    position_value = float(calculate_current_value(symbol, quantity))
                    total_value += position_value
                except Exception:
                    continue
    
    if total_value <= 0:
        try:
            portfolio_data = r.load_portfolio_profile()
            if portfolio_data and 'equity' in portfolio_data:
                total_value = float(portfolio_data['equity'])
        except Exception:
            pass
    
    return total_value if total_value > 0 else 1.0

def get_current_value_float(symbol, quantity):
    """Get current value as float for calculations."""
    if not symbol or not quantity:
        return 0.0
    
    try:
        qty = float(quantity)
        latest_price = r.get_latest_price(symbol)
        
        if latest_price and len(latest_price) > 0 and latest_price[0] is not None:
            price = float(latest_price[0])
            return price * qty
        else:
            return 0.0
    except Exception:
        return 0.0

def process_all_positions(sheet, main_positions, ira_positions, total_portfolio_value=None):
    """Process and update all positions data to sheet with allocation percentages."""
    
    combined_positions = []
    
    for position in main_positions:
        position['account_type'] = 'Main'
        combined_positions.append(position)
    
    for position in ira_positions:
        position['account_type'] = 'IRA'
        combined_positions.append(position)
    
    if not combined_positions:
        sheet.update_cell(1, 1, "No positions found")
        return
    
    if not total_portfolio_value or total_portfolio_value <= 0:
        total_portfolio_value = calculate_total_portfolio_value(combined_positions)
    
    sheet.update_cell(1, 10, f"Total Portfolio Value: ${total_portfolio_value:.2f}")
        
    enriched_positions = []
    total_allocated_value = 0.0
    position_values = []
    
    for position in combined_positions:
        instrument_url = position.get('instrument')
        
        if instrument_url:
            try:
                instrument_data = r.get_instrument_by_url(instrument_url)
                
                symbol = instrument_data.get('symbol', 'N/A')
                quantity = float(position.get('quantity', '0'))
                current_value_float = get_current_value_float(symbol, quantity)
                
                total_allocated_value += current_value_float
                
                position_values.append({
                    'position': position,
                    'instrument_data': instrument_data,
                    'current_value': current_value_float
                })
            except Exception:
                position_values.append({
                    'position': position,
                    'instrument_data': None,
                    'current_value': 0.0
                })
    
    for pos_data in position_values:
        position = pos_data['position']
        instrument_data = pos_data['instrument_data']
        current_value_float = pos_data['current_value']
        
        if instrument_data:
            try:
                symbol = instrument_data.get('symbol', 'N/A')
                
                allocation_percentage = (current_value_float / total_portfolio_value) * 100 if total_portfolio_value > 0 else 0
                current_value = f"{current_value_float:.2f}"
                
                enriched_position = {
                    'Account': position.get('account_type', 'Unknown'),
                    'Symbol': symbol,
                    'Name': instrument_data.get('simple_name') or instrument_data.get('name', 'N/A'),
                    'Quantity': position.get('quantity', '0'),
                    'Average Buy Price': position.get('average_buy_price', '0'),
                    'Current Price': next(iter(r.get_latest_price(symbol) or [0]), 0),
                    'Current Value': current_value,
                    'Allocation %': f"{allocation_percentage:.2f}%",
                    'Created At': position.get('created_at', 'N/A'),
                    'Updated At': position.get('updated_at', 'N/A')
                }
                
                enriched_positions.append(enriched_position)
            except Exception:
                enriched_position = {
                    'Account': position.get('account_type', 'Unknown'),
                    'Symbol': 'Error',
                    'Name': 'Error fetching data',
                    'Quantity': position.get('quantity', '0'),
                    'Average Buy Price': position.get('average_buy_price', '0'),
                    'Current Price': '0.00',
                    'Current Value': '0.00',
                    'Allocation %': '0.00%',
                    'Created At': position.get('created_at', 'N/A'),
                    'Updated At': position.get('updated_at', 'N/A')
                }
                enriched_positions.append(enriched_position)
        else:
            enriched_position = {
                'Account': position.get('account_type', 'Unknown'),
                'Symbol': 'Error',
                'Name': 'Error fetching data',
                'Quantity': position.get('quantity', '0'),
                'Average Buy Price': position.get('average_buy_price', '0'),
                'Current Price': '0.00',
                'Current Value': '0.00',
                'Allocation %': '0.00%',
                'Created At': position.get('created_at', 'N/A'),
                'Updated At': position.get('updated_at', 'N/A')
            }
            enriched_positions.append(enriched_position)
    
    if not enriched_positions:
        sheet.update_cell(1, 1, "No enriched positions found")
        return
    
    enriched_positions.sort(key=lambda x: float(x['Allocation %'].strip('%') or 0), reverse=True)
    
    headers = list(enriched_positions[0].keys())
    
    rows = [
        ["Stock Positions"], 
        [f"Total Portfolio Value: ${total_portfolio_value:.2f}"],
        [""],
        headers
    ]  
    
    for position in enriched_positions:
        rows.append([position.get(header, '') for header in headers])
    
    sheet.update(values=rows, range_name="A1")
    
    sheet.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
    sheet.format("A2", {"textFormat": {"bold": True}})
    
    for i, header in enumerate(headers, start=1):
        cell = f"{chr(64+i)}4"
        sheet.format(cell, {"textFormat": {"bold": True}})
    
    return total_portfolio_value