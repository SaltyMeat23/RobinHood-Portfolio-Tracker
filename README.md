# Robinhood Portfolio Tracker

A comprehensive Python application that automatically tracks your Robinhood investment portfolio and updates Google Sheets with real-time data including stock positions, options positions, trading activity, and account balances. Get the Google Sheets template for this project here https://docs.google.com/spreadsheets/d/1p7d5IQvx6HOy743MbOxrXWiub-0oaMNpHq32wiSR1_8/edit?usp=sharing . Rename the file "TD Tracker - RH" before continuing on. 

## 🚀 Quick Setup Summary

1. **Clone repository**
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Create Google Sheets document named:** `"TD Tracker - RH"`
4. **Set up Google Cloud service account and share spreadsheet**
5. **Configure environment variables:** `cp .env.template .env` and edit
6. **Test setup:** `python test_google_sheets.py`
7. **Run application:** `python main.py`

---

## 🌟 Features

- **Multi-Account Support**: Track Standard, IRA, and additional accounts
- **Real-Time Portfolio Tracking**: Live stock positions with current values and allocation percentages
- **Options Monitoring**: Detailed options positions with Greeks, strategy detection, and P&L tracking
- **Trading Activity**: Recent trades across all asset classes (stocks, options, crypto)
- **Account Balances**: Cash, equity, and collateral tracking across all accounts
- **Google Sheets Integration**: Automatic updates to organized spreadsheets
- **Strategy Detection**: Automatically identifies Covered Calls, Cash-Secured Puts, etc.
- **Rate Limiting**: Built-in protection against API rate limits

## 📊 Data Tracked

### Stock Positions
- Current holdings with real-time prices
- Portfolio allocation percentages
- Gain/loss calculations
- Account distribution

### Options Positions
- Open positions with Greeks (Delta, Theta, Gamma, Vega)
- Strategy identification (CC, CSP, Spreads)
- Implied volatility tracking
- Expiration dates and strike prices

### Trading Activity
- Recent trades across all accounts
- Options premium tracking
- Weekly performance summaries
- Transaction history

### Account Information
- Cash balances and equity
- Options collateral requirements
- Available buying power
- Multi-account consolidation

## 🚀 Setup Instructions

### Prerequisites

- Python 3.7+
- Robinhood account
- Google Cloud Platform account (for Sheets API)
- Google Sheets document

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/robinhood-portfolio-tracker.git
   cd robinhood-portfolio-tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Sheets**
   
   **Create the Required Spreadsheet:**
   - Create a new Google Sheets document
   - **Important:** Name it exactly `"TD Tracker - RH"` (or update your `.env` file with your preferred name)
   - The application will automatically create the following sheets:
     - `Account Balances` - Cash, equity, and collateral by account
     - `All Stock Positions` - Current holdings with allocations  
     - `Option Positions` - Active options with Greeks and strategies
     - `Options Orders` - Historical options trading activity
     - `Recent Trades` - Latest transactions across all assets

   **Set up Google Sheets API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Sheets API and Google Drive API
   - Create a Service Account and download the JSON credentials
   - Rename the downloaded file to `credentials.json` and place in project root
   - **Important:** Share your "TD Tracker - RH" spreadsheet with the service account email (found in credentials.json)
     - Give it "Editor" permissions so the app can update the sheets

4. **Configure Environment Variables**
   ```bash
   cp .env.template .env
   ```
   Edit `.env` file with your credentials:
   ```
   ROBINHOOD_USER=your_robinhood_username
   ROBINHOOD_PASS=your_robinhood_password
   MAIN_ACCOUNT=your_main_account_id
   IRA_ACCOUNT=your_ira_account_id
   THIRD_ACCOUNT=your_third_account_id
   SPREADSHEET_NAME=TD Tracker - RH
   ```
   
   **⚠️ Important:** Make sure `SPREADSHEET_NAME` exactly matches your Google Sheets document name!

5. **Find Your Account IDs**
   Run this helper script to find your Robinhood account IDs:
   ```python
   import robin_stocks.robinhood as r
   from config import load_config
   
   config = load_config()
   r.login(config["robinhood"]["username"], config["robinhood"]["password"])
   
   accounts = r.load_account_profile(info=None)
   print("Your account ID:", accounts['account_number'])
   ```

### Running the Application

**First-time setup verification:**
```bash
# Test your environment setup
python test_env_setup.py

# Test Google Sheets connection specifically
python test_google_sheets.py

# Find your Robinhood account IDs (if needed)
python find_account_ids.py
```

**Run the main application:**
```bash
python main.py
```

The application will:
1. Log into Robinhood
2. Fetch all portfolio data
3. Create/update sheets in your "TD Tracker - RH" spreadsheet
4. Display execution summary

**Expected output:**
```
🔐 Logging in to Robinhood...
📊 Connecting to Google Sheets...
💰 Processing account balances...
📈 Processing stock positions...
📊 Processing options orders...
📊 Processing option positions...
📊 Processing recent trades...
🎯 Total execution time: 45.2 seconds
```

## 📁 Project Structure

```
robinhood-portfolio-tracker/
├── main.py                    # Main execution script
├── config.py                  # Configuration management
├── positions.py               # Stock positions processing
├── options_orders.py          # Options orders and tracking
├── trading_activity.py        # Recent trading activity
├── earnings_calculator.py     # Realized gains calculator
├── rate_limit_handler.py      # API rate limiting
├── multi_account_handler.py   # Multi-account utilities
├── utils.py                   # General utilities
├── requirements.txt           # Python dependencies
├── .env.template              # Environment variables template
├── credentials.json.template  # Google API credentials template
└── README.md                  # This file
```

## 🛡️ Security Features

- Environment variable configuration
- No hardcoded credentials
- Secure Google Service Account authentication
- Rate limiting to prevent API abuse
- Session management with automatic logout

## 📊 Google Sheets Setup

### Required Spreadsheet
The application requires a Google Sheets document named **`"TD Tracker - RH"`** (or whatever you specify in your `.env` file as `SPREADSHEET_NAME`).

### Sheet Structure
The application will automatically create and manage these sheets:

| Sheet Name | Purpose | Auto-Created |
|------------|---------|--------------|
| **Account Balances** | Cash, equity, collateral by account type | ✅ |
| **All Stock Positions** | Current stock holdings with allocation % | ✅ |
| **Option Positions** | Active options with Greeks and strategies | ✅ |
| **Options Orders** | Historical options trading activity | ✅ |
| **Recent Trades** | Latest 50 transactions across all assets | ✅ |

### Google Cloud Setup Steps
1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing one

2. **Enable Required APIs**
   - Google Sheets API
   - Google Drive API (for file access)

3. **Create Service Account**
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Download the JSON credentials file
   - Rename to `credentials.json` and place in project root

4. **Share Spreadsheet**
   - Open your `credentials.json` file
   - Find the `client_email` field (looks like: `your-service@project.iam.gserviceaccount.com`)
   - Share your "TD Tracker - RH" spreadsheet with this email
   - **Give "Editor" permissions**

### Troubleshooting Google Sheets
- **"Spreadsheet not found"** → Check spelling of spreadsheet name in `.env`
- **"Permission denied"** → Make sure spreadsheet is shared with service account email
- **"API not enabled"** → Enable Google Sheets API and Google Drive API in Cloud Console

## 📁 Project Structure

```txt
robin-stocks>=3.0.0
gspread>=5.0.0
oauth2client>=4.1.3
python-dotenv>=0.19.0
pytz>=2021.3
python-dateutil>=2.8.2
pandas>=1.3.0
```

## 🔧 Configuration

### Google Sheets Setup
The application creates several sheets:
- **Account Balances**: Cash, equity, and collateral by account
- **All Stock Positions**: Current holdings with allocations
- **Option Positions**: Active options with Greeks and strategies
- **Options Orders**: Historical options trading activity
- **Recent Trades**: Latest transactions across all assets

### What Your Sheets Will Look Like

**Account Balances Sheet:**
```
Account Balances
Last Updated: 2025-01-15 10:30:25

Total Equity                    $45,230.50
Total Cash (Including CSP)      $12,450.30
Cash for Options Collateral     $8,200.00
Available Cash                  $4,250.30

Standard Account    $35,430.20
IRA Account        $9,800.30
```

**Option Positions Sheet:**
```
Account | Symbol | Strike | Expiration | Type | Strategy | Quantity | Current Price | Total Value | Allocation % | Delta | Theta
Main    | AAPL   | 150.00 | 2025-02-21 | CALL | Covered Call | 2 | $3.45 | $690.00 | 1.53% | 0.65 | -0.12
IRA     | SPY    | 420.00 | 2025-03-15 | PUT  | Cash-Secured Put | 1 | $2.10 | $210.00 | 0.46% | -0.35 | -0.08
```

**Recent Trades Sheet:**
```
Date        | Account | Type   | Symbol | Side | Quantity | Price  | Total Value | Fees
01/15/2025  | Main    | Option | AAPL   | Sell | 2        | $3.50  | $700.00     | $0.00
01/14/2025  | IRA     | Stock  | VTI    | Buy  | 100      | $245.30| $24,530.00  | $0.00
```

## 📋 Requirements

## ⚠️ Important Notes

- **Google Sheets Setup**: Must have a spreadsheet named exactly `"TD Tracker - RH"` (or match your `SPREADSHEET_NAME` in `.env`)
- **Service Account Permissions**: The spreadsheet must be shared with your service account email with "Editor" access
- **Never commit credentials**: Keep `.env` and `credentials.json` files private
- **Rate Limiting**: The application includes built-in delays to respect API limits
- **Data Accuracy**: Always verify important financial data independently
- **Account Types**: Supports multiple account types (Standard, IRA, etc.)

## 🛠️ Troubleshooting

### Common Google Sheets Issues
- **"Spreadsheet 'TD Tracker - RH' not found"**
  - Check spelling of spreadsheet name
  - Verify `SPREADSHEET_NAME` in your `.env` file
  - Make sure spreadsheet exists in your Google Drive

- **"The caller does not have permission"**
  - Share spreadsheet with service account email (found in `credentials.json`)
  - Give "Editor" permissions, not just "Viewer"
  - Wait a few minutes after sharing

- **"API has not been used in project"**
  - Enable Google Sheets API in Google Cloud Console
  - Enable Google Drive API as well
  - Make sure you're using the correct project

### Common Robinhood Issues
- **"Invalid credentials"**
  - Check username/password in `.env` file
  - Try logging into Robinhood website to verify credentials
  - May need to complete 2FA verification

- **"Account not found"**
  - Run `python find_account_ids.py` to get correct account IDs
  - Update `.env` file with correct account numbers

### Environment Setup Issues
- **"Missing required environment variables"**
  - Run `python test_env_setup.py` to diagnose
  - Make sure `.env` file exists and has all required values
  - Check for typos in variable names

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚖️ Disclaimer

This software is for educational and personal use only. Always verify financial data independently. The authors are not responsible for any financial decisions made based on this tool.

## 🔗 Related Projects

- [robin-stocks](https://github.com/jmfernandes/robin_stocks) - Python library for Robinhood API
- [gspread](https://github.com/burnash/gspread) - Google Sheets Python API

## 📞 Support

For questions or issues:
1. Check existing GitHub issues
2. Create a new issue with detailed description
3. Include relevant error messages and setup details

---

**Happy Trading! 📈**
