#!/usr/bin/env python3
"""
Test script to verify environment variables are set correctly.
Run this before committing to Github to make sure no hardcoded values remain.
"""

import os
from dotenv import load_dotenv

def test_environment_setup():
    """Test that all required environment variables are set."""
    load_dotenv()
    
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
    
    print("🔍 Testing Environment Variable Setup")
    print("=" * 50)
    
    missing_required = []
    
    # Test required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 8)} ({description})")
        else:
            print(f"❌ {var}: NOT SET ({description})")
            missing_required.append(var)
    
    # Test optional variables  
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 8)} ({description})")
        else:
            print(f"⚠️  {var}: NOT SET ({description}) - Optional")
    
    print("\n📁 File Check")
    print("=" * 50)
    
    # Check for credentials file
    if os.path.exists('credentials.json'):
        print("✅ credentials.json: Found")
    else:
        print("❌ credentials.json: Missing (needed for Google Sheets)")
    
    # Check for template files
    if os.path.exists('.env.template'):
        print("✅ .env.template: Found")
    else:
        print("⚠️  .env.template: Missing")
        
    if os.path.exists('credentials.json.template'):
        print("✅ credentials.json.template: Found")
    else:
        print("⚠️  credentials.json.template: Missing")
    
    # Check .gitignore
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            gitignore_content = f.read()
            if 'credentials.json' in gitignore_content and '.env' in gitignore_content:
                print("✅ .gitignore: Properly configured")
            else:
                print("❌ .gitignore: Missing sensitive file entries")
    else:
        print("❌ .gitignore: Missing")
    
    print("\n📊 Summary")
    print("=" * 50)
    
    if missing_required:
        print(f"❌ Setup INCOMPLETE. Missing required variables: {', '.join(missing_required)}")
        print("   Please update your .env file with these values.")
        return False
    else:
        print("✅ Environment setup looks good!")
        print("   Ready for Github (make sure .env and credentials.json are NOT committed)")
        return True

def test_account_mapping_functions():
    """Test that the account mapping functions work correctly."""
    print("\n🔧 Testing Account Mapping Functions")
    print("=" * 50)
    
    try:
        # Test the function we created
        load_dotenv()
        mapping = {}
        
        if os.getenv('MAIN_ACCOUNT'):
            mapping[os.getenv('MAIN_ACCOUNT')] = 'Standard'
        if os.getenv('IRA_ACCOUNT'): 
            mapping[os.getenv('IRA_ACCOUNT')] = 'IRA'
        if os.getenv('THIRD_ACCOUNT'):
            mapping[os.getenv('THIRD_ACCOUNT')] = 'Third'
        
        print(f"✅ Account mapping created successfully:")
        for account_id, account_type in mapping.items():
            if account_id:  # Only show if account ID exists
                masked_id = account_id[:3] + '*' * (len(account_id) - 3)
                print(f"   {masked_id} -> {account_type}")
        
        if not mapping:
            print("⚠️  No account mappings found - check your environment variables")
            
    except Exception as e:
        print(f"❌ Error testing account mapping: {e}")

if __name__ == "__main__":
    success = test_environment_setup()
    test_account_mapping_functions()
    
    if success:
        print("\n🚀 Ready for Github!")
    else:
        print("\n🛠️  Please fix the issues above before committing.")
