#!/usr/bin/env python3
"""
Test environment setup and configuration.
Run this to verify your environment variables and basic setup.
"""

import os
from dotenv import load_dotenv

def test_env_setup():
    """Test environment variable setup."""
    print("🔧 Testing Environment Setup")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for .env file
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Create .env file from .env.template")
        return False
    
    print("✅ Found .env file")
    
    # Required variables
    required_vars = {
        'ROBINHOOD_USER': 'Robinhood username',
        'ROBINHOOD_PASS': 'Robinhood password',
        'MAIN_ACCOUNT': 'Main account ID',
        'SPREADSHEET_NAME': 'Google Sheets name'
    }
    
    optional_vars = {
        'IRA_ACCOUNT': 'IRA account ID',
        'THIRD_ACCOUNT': 'Third account ID'
    }
    
    all_good = True
    
    print("\n🔍 Checking Required Variables:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'PASS' in var:
                display_value = '*' * len(value)
            elif len(value) > 10:
                display_value = value[:6] + '...'
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Missing ({description})")
            all_good = False
    
    print("\n🔍 Checking Optional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            display_value = value[:6] + '...' if len(value) > 10 else value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ⚠️  {var}: Not set ({description})")
    
    # Check for credentials.json
    print("\n🔍 Checking Google Credentials:")
    if os.path.exists('credentials.json'):
        print("   ✅ credentials.json found")
        
        # Try to parse it
        try:
            import json
            with open('credentials.json', 'r') as f:
                creds = json.load(f)
                if 'client_email' in creds:
                    print(f"   ✅ Service account email: {creds['client_email']}")
                else:
                    print("   ⚠️  No client_email found in credentials.json")
        except Exception as e:
            print(f"   ❌ Error reading credentials.json: {e}")
            all_good = False
    else:
        print("   ❌ credentials.json not found")
        print("       Download from Google Cloud Console")
        all_good = False
    
    # Check Python dependencies
    print("\n🔍 Checking Python Dependencies:")
    required_packages = [
        'robin_stocks',
        'gspread',
        'oauth2client',
        'python-dotenv',
        'pytz'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}: Not installed")
            all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 Environment setup looks good!")
        print("✅ Ready to run: python main.py")
    else:
        print("🛠️  Please fix the issues above before continuing")
        print("\n📖 Setup Guide:")
        print("1. Copy .env.template to .env and fill in your values")
        print("2. Download credentials.json from Google Cloud Console")
        print("3. Install missing packages: pip install -r requirements.txt")
        print("4. Run: python test_google_sheets.py to test Google Sheets")
        print("5. Run: python find_account_ids.py to find your account IDs")
    
    return all_good

if __name__ == "__main__":
    test_env_setup()
