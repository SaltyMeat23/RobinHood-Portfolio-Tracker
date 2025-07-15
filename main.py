# main.py - Cleaned version with minimal debug output

import time
from config import load_config
import robin_stocks.robinhood as r
from positions import process_all_positions
from options_orders import process_options_orders
from rate_limit_handler import retry_on_rate_limit, sleep_with_jitter
from option_utils import (get_option_data_batch, get_simplified_account_data, 
                         get_stock_positions_for_cc_detection, simplified_strategy_detection,
                         get_total_portfolio_value, get_account_type_mapping)
import gspread
from oauth2client.service_account import ServiceAccountCredentials






def process_integrated_option_positions(sheets_client, spreadsheet, main_account_id, ira_account_id, config):
    """Process option positions."""
    try:
        combined_positions = []
        
        # Get main account positions
        if main_account_id:
            try:
                main_options = r.get_open_option_positions(account_number=main_account_id)
                for option in main_options:
                    option['account_type'] = 'Main'
                    option['account_number'] = main_account_id
                    combined_positions.append(option)
                print(f"Found {len(main_options)} main account options")
            except Exception as e:
                print(f"Error getting main account options: {e}")
        
        # Only get IRA positions if IRA account ID is provided, valid, and different from main
        if ira_account_id and ira_account_id != main_account_id and ira_account_id.strip():
            try:
                ira_options = r.get_open_option_positions(account_number=ira_account_id)
                for option in ira_options:
                    option['account_type'] = 'IRA'
                    option['account_number'] = ira_account_id
                    combined_positions.append(option)
                print(f"Found {len(ira_options)} IRA account options")
            except Exception as e:
                print(f"Error getting IRA account options: {e}")
        else:
            print("Skipping IRA account - not provided or same as main account")
        
        if not combined_positions:
            options_sheet = sheets_client.get_or_create_worksheet(spreadsheet, config["google_sheets"]["option_positions_sheet"])
            sheets_client.update_cells(options_sheet, [["No option positions found"]], "A1")
            return
        
        # Remove duplicates based on option_id
        seen_option_ids = set()
        unique_positions = []
        for position in combined_positions:
            option_id = position.get('option_id')
            if option_id and option_id not in seen_option_ids:
                seen_option_ids.add(option_id)
                unique_positions.append(position)
            elif option_id:
                print(f"Duplicate option_id found and removed: {option_id}")
        
        combined_positions = unique_positions
        print(f"Processing {len(combined_positions)} unique option positions")
        
        option_ids = [pos.get('option_id') for pos in combined_positions if pos.get('option_id')]
        
        if not option_ids:
            return
        
        # Filter account_ids to only include valid ones
        valid_account_ids = [acc_id for acc_id in [main_account_id, ira_account_id] 
                           if acc_id and acc_id.strip()]
        
        option_data, market_data = get_option_data_batch(option_ids)
        account_data = get_simplified_account_data(valid_account_ids, ira_account_id)
        stock_collateral = get_stock_positions_for_cc_detection(valid_account_ids)
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
        
        print(f"Successfully enriched {len(enriched_positions)} option positions")
        update_option_positions_sheet(sheets_client, spreadsheet, enriched_positions, total_portfolio_value, config)
        
    except Exception as e:
        print(f"Error processing option positions: {e}")

def update_option_positions_sheet(sheets_client, spreadsheet, enriched_positions, total_portfolio_value, config):
    """Update sheet with option positions."""
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
    
    options_sheet = sheets_client.get_or_create_worksheet(spreadsheet, config["google_sheets"]["option_positions_sheet"])
    
    sheets_client.clear_worksheet(options_sheet)
    sleep_with_jitter(1.0)
    
    sheets_client.update_cells(options_sheet, rows, "A1")
    sleep_with_jitter(1.0)
    
    sheets_client.format_cell(options_sheet, "A1", {"textFormat": {"bold": True, "fontSize": 14}})
    sleep_with_jitter(0.5)
    
    sheets_client.format_cell(options_sheet, "A4:Q4", {"textFormat": {"bold": True}})

def update_account_balance_sheet(sheet, account_balances, monthly_earnings=None):
    """Update the account balance sheet."""
    sheet.clear()
    sleep_with_jitter(3.0)
    
    current_date = time.strftime("%Y-%m-%d %H:%M:%S")

    if 'unsettled_funds' not in account_balances:
        account_balances['unsettled_funds'] = 0.0

    summary_data = [
        ["Account Balances"],
        [f"Last Updated: {current_date}"],
        [""],
        ["Total Equity", f"${account_balances['total_equity']:.2f}"],
        ["Total Cash (Including CSP Collateral)", f"${account_balances['total_cash']:.2f}"],
        ["Cash for Options Collateral (CSPs)", f"${account_balances['cash_for_options_collateral']:.2f}"],
        ["Available Cash", f"${account_balances['available_cash']:.2f}"],
        ["Unsettled Funds", f"${account_balances['unsettled_funds']:.2f}"],
        ["Total Account Value", f"${account_balances['total_equity']:.2f}"],
        [""],
        ["Earnings Calculator: ⏸️ TEMPORARILY DISABLED"],
        [""]
    ]
    
    sheet.update(values=summary_data, range_name="A1:B12")
    sleep_with_jitter(2.0)

    standard_balance = account_balances['by_account'].get('Standard', {})
    standard_data = [
        ["Standard Account"],
        ["Equity", f"${standard_balance.get('equity', 0.0):.2f}"],
        ["Cash", f"${standard_balance.get('cash', 0.0):.2f}"],
        ["Cash for Options Collateral", f"${standard_balance.get('options_collateral', 0.0):.2f}"],
        ["Available Cash", f"${standard_balance.get('available_cash', 0.0):.2f}"],
        ["Unsettled Funds", f"${standard_balance.get('unsettled_funds', 0.0):.2f}"],
        ["Total", f"${standard_balance.get('equity', 0.0):.2f}"],
        [""],
        [""],
        [""]
    ]
    
    sheet.update(values=standard_data, range_name="A14:B23")
    sleep_with_jitter(2.0)

    ira_balance = account_balances['by_account'].get('IRA', {})
    ira_data = [
        ["IRA Account"],
        ["Equity", f"${ira_balance.get('equity', 0.0):.2f}"],
        ["Cash", f"${ira_balance.get('cash', 0.0):.2f}"],
        ["Cash for Options Collateral", f"${ira_balance.get('options_collateral', 0.0):.2f}"],
        ["Available Cash", f"${ira_balance.get('available_cash', 0.0):.2f}"],
        ["Unsettled Funds", f"${ira_balance.get('unsettled_funds', 0.0):.2f}"],
        ["Total", f"${ira_balance.get('equity', 0.0):.2f}"],
        [""],
        [""],
        [""]
    ]
    
    sheet.update(values=ira_data, range_name="A25:B34")
    sleep_with_jitter(2.0)

    third_balance = account_balances['by_account'].get('Third', {})
    third_data = [
        ["Third Account"],
        ["Equity", f"${third_balance.get('equity', 0.0):.2f}"],
        ["Cash", f"${third_balance.get('cash', 0.0):.2f}"],
        ["Cash for Options Collateral", f"${third_balance.get('options_collateral', 0.0):.2f}"],
        ["Available Cash", f"${third_balance.get('available_cash', 0.0):.2f}"],
        ["Unsettled Funds", f"${third_balance.get('unsettled_funds', 0.0):.2f}"],
        ["Total", f"${third_balance.get('equity', 0.0):.2f}"],
        [""],
        [""],
        [""]
    ]
    
    sheet.update(values=third_data, range_name="A36:B45")
    sleep_with_jitter(2.0)

    crypto_balance = account_balances['by_account'].get('Crypto', {})
    crypto_data = [
        ["Crypto Account"],
        ["Equity", f"${crypto_balance.get('equity', 0.0):.2f}"],
        ["Total", f"${crypto_balance.get('equity', 0.0):.2f}"],
        [""],
        [""],
        [""]
    ]
    
    sheet.update(values=crypto_data, range_name="A47:B52")
    sleep_with_jitter(2.0)

    earnings_disabled_data = [
        ["Monthly Earnings Summary"],
        ["⏸️ Earnings Calculator Temporarily Disabled"],
        ["Will be re-enabled in a future update"],
        [""],
        [""]
    ]
    
    sheet.update(values=earnings_disabled_data, range_name="A54:B58")
    sleep_with_jitter(2.0)

    try:
        sheet.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
        sleep_with_jitter(1.0)
        
        sheet.format("A11", {"textFormat": {"bold": True}, "backgroundColor": {"red": 1.0, "green": 0.8, "blue": 0.6}})
        sleep_with_jitter(1.0)
        
        sheet.format("A14", {"textFormat": {"bold": True, "fontSize": 12}})
        sheet.format("A25", {"textFormat": {"bold": True, "fontSize": 12}})
        sheet.format("A36", {"textFormat": {"bold": True, "fontSize": 12}})
        sheet.format("A47", {"textFormat": {"bold": True, "fontSize": 12}})
        sleep_with_jitter(1.0)
        
        sheet.format("A54", {"textFormat": {"bold": True, "fontSize": 12}})
        sheet.format("A55", {"textFormat": {"bold": True}, "backgroundColor": {"red": 1.0, "green": 0.8, "blue": 0.6}})
        
    except Exception:
        pass

def get_account_balances(main_account_id=None, ira_account_id=None, third_account_id=None):
    """Calculate total balance across all accounts."""
    balances = {
        'total_equity': 0.0,
        'total_cash': 0.0,
        'cash_for_options_collateral': 0.0,
        'available_cash': 0.0,
        'unsettled_funds': 0.0,
        'by_account': {}
    }
    
    try:
        account_types = {}
        if main_account_id:
            account_types[main_account_id] = 'Standard'
        if ira_account_id:
            account_types[ira_account_id] = 'IRA'
        if third_account_id:
            account_types[third_account_id] = 'Third'
        
        for account_number, account_type in account_types.items():
            try:
                account_data = r.load_account_profile(account_number=account_number)
                portfolio_url = f"https://api.robinhood.com/portfolios/{account_number}/"
                portfolio_data = r.request_get(portfolio_url, 'regular')
                
                if not portfolio_data:
                    continue
                
                equity = float(portfolio_data.get('equity', 0))
                cash = float(account_data.get('cash', 0))
                cash_held_for_options = float(account_data.get('cash_held_for_options_collateral', 0))
                available_cash = cash - cash_held_for_options
                unsettled_funds = float(account_data.get('unsettled_funds', 0))
                
                balances['total_equity'] += equity
                balances['total_cash'] += cash
                balances['cash_for_options_collateral'] += cash_held_for_options
                balances['unsettled_funds'] += unsettled_funds
                
                balances['by_account'][account_type] = {
                    'equity': equity,
                    'cash': cash,
                    'options_collateral': cash_held_for_options,
                    'available_cash': available_cash,
                    'unsettled_funds': unsettled_funds,
                    'total': equity
                }
                
                sleep_with_jitter(1.0)
                
            except Exception:
                continue
        
        balances['available_cash'] = balances['total_cash'] - balances['cash_for_options_collateral']
        
        try:
            phoenix_data = r.account.load_phoenix_account()
            if phoenix_data and 'crypto' in phoenix_data and isinstance(phoenix_data['crypto'], dict):
                crypto_value = phoenix_data['crypto'].get('equity', 0)
                
                crypto_equity = 0.0
                if isinstance(crypto_value, dict) and 'amount' in crypto_value:
                    crypto_equity = float(crypto_value['amount'])
                elif isinstance(crypto_value, (int, float, str)):
                    crypto_equity = float(crypto_value)
                
                if crypto_equity > 0:
                    balances['total_equity'] += crypto_equity
                    balances['by_account']['Crypto'] = {
                        'equity': crypto_equity,
                        'cash': 0.0,
                        'unsettled_funds': 0.0,
                        'total': crypto_equity
                    }
        except Exception:
            pass
        
    except Exception:
        pass
        
    return balances

def process_stock_positions(spreadsheet, main_account_id, ira_account_id, config):
    """Process stock positions and update the relevant sheet."""
    try:
        all_stock_positions_sheet = spreadsheet.worksheet(config["google_sheets"]["all_stock_positions_sheet"])
        all_stock_positions_sheet.clear()
        
        main_positions = r.get_open_stock_positions(account_number=main_account_id)
        
        ira_positions = []
        if ira_account_id:
            ira_positions = r.get_open_stock_positions(account_number=ira_account_id)
        
        total_portfolio_value = process_all_positions(all_stock_positions_sheet, main_positions, ira_positions)
        
        return total_portfolio_value
    except Exception:
        return None

def connect_to_sheets_pure(credentials_file, spreadsheet_name):
    """Connect to Google Sheets."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open(spreadsheet_name)
    return client, spreadsheet

def get_or_create_worksheet_pure(spreadsheet, title, rows=1000, cols=20):
    """Get or create worksheet."""
    try:
        return spreadsheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)

def main():
    """Main execution function."""
    start_time = time.time()
    
    try:
        config = load_config()
        
        main_account_id = config["robinhood"]["account_id"]
        ira_account_id = config["robinhood"]["ira_account_id"]
        third_account_id = config["robinhood"]["third_account_id"]

        if not main_account_id:
            raise ValueError("MAIN_ACCOUNT environment variable must be set")
        if not ira_account_id:
            print("⚠️  Warning: IRA_ACCOUNT not set, IRA features will be disabled")
        
        print("🔐 Logging in to Robinhood...")
        r.login(config["robinhood"]["username"], config["robinhood"]["password"], 
                expiresIn=86400, store_session=True)
        
        print("📊 Connecting to Google Sheets...")
        client, spreadsheet = connect_to_sheets_pure(
            config["google_sheets"]["credentials_file"],
            config["google_sheets"]["spreadsheet_name"]
        )
        
        class PureSheetsWrapper:
            def __init__(self, client, spreadsheet):
                self.client = client
                self.spreadsheet = spreadsheet
            
            def get_or_create_worksheet(self, spreadsheet, title, rows=1000, cols=20):
                return get_or_create_worksheet_pure(spreadsheet, title, rows, cols)
            
            def update_cells(self, worksheet, data, range_name="A1"):
                if data:
                    worksheet.update(values=data, range_name=range_name)
            
            def clear_worksheet(self, worksheet):
                worksheet.clear()
            
            def format_cell(self, worksheet, cell_range, format_dict):
                worksheet.format(cell_range, format_dict)
        
        sheets_client = PureSheetsWrapper(client, spreadsheet)
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        return
    
    print("💰 Processing account balances...")
    try:
        account_balances = get_account_balances(main_account_id, ira_account_id)
        monthly_earnings = None
        
        balance_sheet = sheets_client.get_or_create_worksheet(
            spreadsheet, config["google_sheets"]["account_balances_sheet"], rows=50, cols=20
        )
        
        update_account_balance_sheet(balance_sheet, account_balances, monthly_earnings)
        print("✅ Account balances processed")
        
    except Exception as e:
        print(f"❌ Error processing account balances: {e}")

    print("📈 Processing stock positions...")
    try:
        total_portfolio_value = process_stock_positions(spreadsheet, main_account_id, ira_account_id, config)
        print("✅ Stock positions processed")
    except Exception as e:
        print(f"❌ Error processing stock positions: {e}")
    
    print("📊 Processing options orders...")
    try:
        process_options_orders(spreadsheet, main_account_id, ira_account_id, config, third_account_id)
        print("✅ Options orders processed")
    except Exception as e:
        print(f"❌ Error processing options orders: {e}")

    print("📊 Processing option positions...")
    try:
        process_integrated_option_positions(sheets_client, spreadsheet, main_account_id, ira_account_id, config)
        print("✅ Option positions processed")
    except Exception as e:
        print(f"❌ Error processing option positions: {e}")

    print("📊 Processing recent trades...")
    try:
        from trading_activity import process_simple_trading_activity
        
        account_ids = [acc_id for acc_id in [main_account_id, ira_account_id] if acc_id]
        recent_trades = process_simple_trading_activity(spreadsheet, *account_ids)
        
        if recent_trades:
            print("✅ Recent trades processed")
        else:
            print("⚠️ No recent trades found")
            
    except Exception as e:
        print(f"❌ Error processing recent trades: {e}")

    execution_time = time.time() - start_time
    print(f"\n🎯 Total execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()