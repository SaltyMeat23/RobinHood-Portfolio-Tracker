#!/usr/bin/env python3
"""
Find your Robinhood account IDs.
Run this script to discover your account numbers for the .env file.
"""

import robin_stocks.robinhood as r
from config import load_config

def find_account_ids():
    """Find and display all account IDs."""
    print("🔍 Finding Your Robinhood Account IDs")
    print("=" * 50)
    
    try:
        config = load_config()
        
        print("🔐 Logging into Robinhood...")
        r.login(config["robinhood"]["username"], config["robinhood"]["password"])
        
        print("📊 Fetching account information...")
        
        # Get all accounts
        try:
            all_accounts = r.get_all_accounts()
            if all_accounts:
                print(f"\n✅ Found {len(all_accounts)} accounts:")
                for i, account in enumerate(all_accounts, 1):
                    account_id = account.get('account_number', 'Unknown')
                    account_type = account.get('type', 'Unknown')
                    print(f"   {i}. Account ID: {account_id} (Type: {account_type})")
            else:
                print("❌ No accounts found using get_all_accounts()")
        except Exception as e:
            print(f"⚠️  get_all_accounts() failed: {e}")
        
        # Get primary account (alternative method)
        try:
            primary_account = r.load_account_profile(info=None)
            if primary_account and 'account_number' in primary_account:
                account_id = primary_account['account_number']
                print(f"\n📋 Primary Account ID: {account_id}")
                
                # Try to determine account type
                account_type = "Standard"
                if 'account_type' in primary_account:
                    if 'ira' in primary_account['account_type'].lower():
                        account_type = "IRA"
                
                print(f"   Account Type: {account_type}")
                
            else:
                print("❌ Could not get primary account information")
        except Exception as e:
            print(f"⚠️  load_account_profile() failed: {e}")
        
        print("\n" + "=" * 50)
        print("📝 Next Steps:")
        print("1. Copy the account IDs you want to track")
        print("2. Update your .env file:")
        print("   MAIN_ACCOUNT=your_main_account_id")
        print("   IRA_ACCOUNT=your_ira_account_id (if you have one)")
        print("   THIRD_ACCOUNT=your_third_account_id (if you have one)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Check your ROBINHOOD_USER and ROBINHOOD_PASS in .env")
        print("- Make sure you can log into Robinhood website")
        print("- You may need to complete 2FA verification")
    
    finally:
        try:
            r.logout()
        except:
            pass

if __name__ == "__main__":
    find_account_ids()