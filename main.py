def process_integrated_option_positions(sheets_client, spreadsheet, main_account_id, ira_account_id):
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
            options_sheet = sheets_client.get_or_create_worksheet(spreadsheet, "Option Positions")
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
        account_data = get_simplified_account_data(valid_account_ids)
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
        update_option_positions_sheet(sheets_client, spreadsheet, enriched_positions, total_portfolio_value)
        
    except Exception as e:
        print(f"Error processing option positions: {e}")
