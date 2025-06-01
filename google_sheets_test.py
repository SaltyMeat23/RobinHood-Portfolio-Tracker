#!/usr/bin/env python3
"""
Test Google Sheets connection and setup.
Run this to verify your Google Sheets integration is working.
"""

import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def test_google_sheets_setup():
    """Test Google Sheets connection and permissions."""
    
    print("📊 Testing Google Sheets Setup")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    spreadsheet_name = os.getenv('SPREADSHEET_NAME', 'TD Tracker - RH')
    credentials_file = 'credentials.json'
    
    # Check for credentials file
    if not os.path.exists(credentials_file):
        print(f"❌ {credentials_file} not found")
        print("   Download from Google Cloud Console and place in project root")
        return False
    
    print(f"✅ Found {credentials_file}")
    
    # Test connection
    try:
        print("🔐 Testing Google Sheets API connection...")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
        client = gspread.authorize(creds)
        
        print("✅ Google Sheets API connection successful")
        
        # Test spreadsheet access
        print(f"📋 Looking for spreadsheet: '{spreadsheet_name}'...")
        
        try:
            spreadsheet = client.open(spreadsheet_name)
            print(f"✅ Found spreadsheet: '{spreadsheet_name}'")
            
            # Test write permissions
            print("🔒 Testing write permissions...")
            
            # Try to create a test sheet
            try:
                test_sheet = spreadsheet.add_worksheet(title="__TEST_SHEET__", rows=1, cols=1)
                test_sheet.update_cell(1, 1, "Test")
                
                # Clean up
                spreadsheet.del_worksheet(test_sheet)
                print("✅ Write permissions confirmed")
                
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("✅ Write permissions confirmed (test sheet already exists)")
                else:
                    print(f"❌ Write permission error: {e}")
                    print("   Make sure the spreadsheet is shared with your service account email")
                    return False
            
            # Show existing sheets
            print(f"\n📊 Current sheets in '{spreadsheet_name}':")
            for i, sheet in enumerate(spreadsheet.worksheets(), 1):
                print(f"   {i}. {sheet.title}")
            
            # Show service account email
            print(f"\n🔑 Service account email:")
            with open(credentials_file, 'r') as f:
                import json
                creds_data = json.load(f)
                print(f"   {creds_data.get('client_email', 'Not found')}")
                print("   (Make sure your spreadsheet is shared with this email)")
            
            return True
            
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"❌ Spreadsheet '{spreadsheet_name}' not found")
            print("   Create a Google Sheets document with exactly this name")
            print("   Or update SPREADSHEET_NAME in your .env file")
            return False
            
    except Exception as e:
        print(f"❌ Google Sheets API error: {e}")
        print("   Check your credentials.json file")
        print("   Make sure Google Sheets API is enabled in Google Cloud Console")
        return False

def show_setup_instructions():
    """Show detailed setup instructions."""
    
    print("\n📖 Google Sheets Setup Instructions")
    print("=" * 50)
    
    print("1. 🌐 Create Google Cloud Project:")
    print("   - Go to https://console.cloud.google.com/")
    print("   - Create new project or select existing")
    
    print("\n2. 🔧 Enable APIs:")
    print("   - Google Sheets API")
    print("   - Google Drive API")
    
    print("\n3. 🔑 Create Service Account:")
    print("   - Go to IAM & Admin → Service Accounts")
    print("   - Create Service Account")
    print("   - Download JSON credentials")
    print("   - Rename to 'credentials.json' and place in project root")
    
    print("\n4. 📋 Create Spreadsheet:")
    print("   - Create new Google Sheets document")
    print("   - Name it exactly: 'TD Tracker - RH'")
    print("   - Or update SPREADSHEET_NAME in .env file")
    
    print("\n5. 🤝 Share Spreadsheet:")
    print("   - Open your credentials.json file")
    print("   - Find the 'client_email' field")
    print("   - Share your spreadsheet with this email")
    print("   - Give 'Editor' permissions")

def main():
    """Run Google Sheets setup test."""
    
    success = test_google_sheets_setup()
    
    if not success:
        show_setup_instructions()
        print("\n🛠️  Fix the issues above and run this test again")
    else:
        print("\n🎉 Google Sheets setup successful!")
        print("✅ Ready to run the main application")

if __name__ == "__main__":
    main()
