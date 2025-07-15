#!/usr/bin/env python3
"""
Build script for creating RobinHood Portfolio Tracker executable.
"""

import os
import sys
import subprocess
import shutil

def create_executable():
    """Create the executable using PyInstaller."""
    
    print("🔨 Building RobinHood Portfolio Tracker executable...")
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("release"):
        shutil.rmtree("release")
    
    # PyInstaller command - simplified for better compatibility
    cmd = [
        "pyinstaller",
        "--onefile",                    # Create a single executable file
        "--name=RobinhoodTracker",      # Name of the executable
        "--hidden-import=robin_stocks",
        "--hidden-import=gspread", 
        "--hidden-import=oauth2client",
        "--hidden-import=dotenv",
        "--hidden-import=pytz",
        "--hidden-import=pandas",
        "--hidden-import=cryptography",
        "main.py"
    ]
    
    try:
        print("Running PyInstaller...")
        result = subprocess.run(cmd, check=True)
        print("✅ Executable created successfully!")
        print(f"📁 Executable location: {os.path.abspath('dist/RobinhoodTracker.exe')}")
        
        # Create a release folder with necessary files
        release_dir = "release"
        os.makedirs(release_dir)
        
        # Copy executable
        if os.path.exists("dist/RobinhoodTracker.exe"):
            shutil.copy("dist/RobinhoodTracker.exe", f"{release_dir}/RobinhoodTracker.exe")
        else:
            print("⚠️ Executable not found in expected location")
            return False
        
        # Copy template files
        if os.path.exists("credentials.json.template"):
            shutil.copy("credentials.json.template", f"{release_dir}/credentials.json.template")
        
        shutil.copy("README.md", f"{release_dir}/README.md")
        
        # Create a simple setup instruction file
        setup_instructions = """# RobinHood Portfolio Tracker - Executable Release

## Quick Setup:

1. Create a .env file with your credentials:
   ```
   ROBINHOOD_USER=your_email@example.com
   ROBINHOOD_PASS=your_password
   MAIN_ACCOUNT=your_main_account_id
   IRA_ACCOUNT=your_ira_account_id (optional)
   THIRD_ACCOUNT=your_third_account_id (optional)
   SPREADSHEET_NAME=TD Tracker - RH
   ```

2. Setup Google Sheets:
   - Rename credentials.json.template to credentials.json
   - Add your Google Service Account credentials to credentials.json
   - Share your Google Sheet with the service account email

3. Run RobinhoodTracker.exe

For detailed setup instructions, see README.md
"""
        
        with open(f"{release_dir}/SETUP.md", "w") as f:
            f.write(setup_instructions)
        
        print(f"📦 Release package created in: {os.path.abspath(release_dir)}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating executable: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def main():
    """Main build function."""
    if not create_executable():
        sys.exit(1)
    
    print("\n🎉 Build completed successfully!")
    print("\n📋 To distribute:")
    print("1. Copy the 'release' folder")
    print("2. Users should follow the instructions in SETUP.md")
    print("3. Run RobinhoodTracker.exe")

if __name__ == "__main__":
    main()