# trading_activity.py - Cleaned version

import robin_stocks.robinhood as r
from datetime import datetime
import pytz
from rate_limit_handler import sleep_with_jitter

def get_last_50_trades(account_ids=None):
    """Get the last 50 filled trades across all account types."""
    all_trades = []
    
    account_mapping = {
        '5QU52702': 'Standard',
        '519517908': 'IRA', 
        '410351639': 'Third'
    }
    
    try:
        for account_id in account_ids or []:
            if not account_id:
                continue
                
            stock_orders = r.get_all_stock_orders(account_number=account_id)
            
            for order in stock_orders:
                if order.get('state') != 'filled':
                    continue
                    
                symbol = 'Unknown'
                try:
                    instrument_url = order.get('instrument')
                    if instrument_url:
                        instrument_data = r.get_instrument_by_url(instrument_url)
                        symbol = instrument_data.get('symbol', 'Unknown')
                except:
                    pass
                
                price = float(order.get('average_price') or order.get('price') or 0)
                quantity = float(order.get('quantity', 0))
                total_value = price * quantity
                
                trade = {
                    'date': order.get('created_at', ''),
                    'account': account_mapping.get(account_id, 'Unknown'),
                    'type': 'Stock',
                    'symbol': symbol,
                    'side': order.get('side', '').title(),
                    'quantity': quantity,
                    'price': price,
                    'total_value': total_value,
                    'fees': float(order.get('fees', 0)),
                    'state': order.get('state', '')
                }
                
                all_trades.append(trade)
                
    except Exception:
        pass
    
    try:
        for account_id in account_ids or []:
            if not account_id:
                continue
                
            option_orders = r.get_all_option_orders(account_number=account_id)
            
            for order in option_orders:
                if order.get('state') != 'filled':
                    continue
                
                symbol = order.get('chain_symbol', 'Unknown')
                direction = order.get('direction', '').title()
                premium = float(order.get('processed_premium') or order.get('premium') or 0)
                quantity = float(order.get('quantity', 1))
                
                trade = {
                    'date': order.get('created_at', ''),
                    'account': account_mapping.get(account_id, 'Unknown'),
                    'type': 'Option',
                    'symbol': symbol,
                    'side': direction,
                    'quantity': quantity,
                    'price': premium / quantity if quantity > 0 else premium,
                    'total_value': premium,
                    'fees': 0.0,
                    'state': order.get('state', '')
                }
                
                all_trades.append(trade)
                
    except Exception:
        pass
    
    try:
        crypto_orders = r.get_all_crypto_orders()
        
        for order in crypto_orders:
            if order.get('state') != 'filled':
                continue
                
            symbol = 'Unknown'
            try:
                crypto_id = order.get('currency_pair_id')
                if crypto_id:
                    crypto_data = r.get_crypto_quote_from_id(crypto_id)
                    symbol = crypto_data.get('symbol', 'Unknown')
            except:
                pass
            
            price = float(order.get('average_price') or order.get('price') or 0)
            quantity = float(order.get('quantity', 0))
            total_value = price * quantity
            
            trade = {
                'date': order.get('created_at', ''),
                'account': 'Main',
                'type': 'Crypto',
                'symbol': symbol,
                'side': order.get('side', '').title(),
                'quantity': quantity,
                'price': price,
                'total_value': total_value,
                'fees': float(order.get('fees', 0)),
                'state': order.get('state', '')
            }
            
            all_trades.append(trade)
            
    except Exception:
        pass
    
    all_trades.sort(key=lambda x: x.get('date', ''), reverse=True)
    recent_trades = all_trades[:50]
    
    return recent_trades

def update_simple_trades_sheet(sheet, trades):
    """Update sheet with simple list of recent trades."""
    try:
        sheet.clear()
        sleep_with_jitter(2.0)
        
        if not trades:
            sheet.update_cell(1, 1, "No filled trades found")
            return
        
        headers = [
            "Date", "Account", "Type", "Symbol", "Side", 
            "Quantity", "Price", "Total Value", "Fees", "Status"
        ]
        
        rows = [
            [f"Last {len(trades)} Filled Trades"],
            [""],
            headers
        ]
        
        for trade in trades:
            date_str = trade.get('date', '')
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    eastern = pytz.timezone('US/Eastern')
                    dt = dt.astimezone(eastern)
                    formatted_date = dt.strftime('%m/%d/%Y %I:%M %p')
                except:
                    formatted_date = date_str[:10]
            else:
                formatted_date = 'N/A'
            
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            total_value = trade.get('total_value', 0)
            fees = trade.get('fees', 0)
            
            row = [
                formatted_date,
                trade.get('account', 'Unknown'),
                trade.get('type', 'Unknown'),
                trade.get('symbol', 'N/A'),
                trade.get('side', 'N/A'),
                f"{quantity:.4f}" if quantity < 10 else f"{quantity:.2f}",
                f"${price:.2f}" if price > 0 else 'N/A',
                f"${total_value:.2f}" if total_value > 0 else 'N/A',
                f"${fees:.2f}" if fees > 0 else '$0.00',
                trade.get('state', 'N/A').title()
            ]
            
            rows.append(row)
        
        sheet.update(values=rows, range_name="A1")
        sleep_with_jitter(2.0)
        
        sheet.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
        sleep_with_jitter(1.0)
        
        sheet.format("A3:J3", {"textFormat": {"bold": True}})
        sleep_with_jitter(1.0)
        
    except Exception:
        pass

def process_simple_trading_activity(spreadsheet, *account_ids):
    """Main function to get last 50 trades and update sheet."""
    
    try:
        valid_account_ids = [acc_id for acc_id in account_ids if acc_id]
        
        if not valid_account_ids:
            return []
        
        recent_trades = get_last_50_trades(valid_account_ids)
        
        if not recent_trades:
            return []
        
        try:
            trades_sheet = spreadsheet.worksheet("Recent Trades")
            trades_sheet.clear()
        except:
            trades_sheet = spreadsheet.add_worksheet(title="Recent Trades", rows=100, cols=15)
        
        sleep_with_jitter(2.0)
        
        update_simple_trades_sheet(trades_sheet, recent_trades)
        
        return recent_trades
        
    except Exception:
        return []