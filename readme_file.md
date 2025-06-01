# Robinhood Portfolio Tracker

A comprehensive Python application that automatically tracks your Robinhood investment portfolio and updates Google Sheets with real-time data including stock positions, options positions, trading activity, and account balances.

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

3. **Set up Google Sheets API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Sheets API
   - Create a Service Account and download the JSON credentials
   - Rename the downloaded file to `credentials.json` and place in project root
   - Share your Google Sheets document with the service account email

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
   SPREADSHEET_NAME=your_spreadsheet_name
   ```

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

```bash
python main.py
```

The application will:
1. Log into Robinhood
2. Fetch all portfolio data
3. Update Google Sheets with organized information
4. Display execution summary

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

## 📋 Requirements

Create a `requirements.txt` file with:

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

### Customization
- Modify sheet names in `main.py`
- Adjust rate limiting in `rate_limit_handler.py`
- Customize data fields in respective processing modules

## ⚠️ Important Notes

- **Never commit credentials**: Keep `.env` and `credentials.json` files private
- **Rate Limiting**: The application includes built-in delays to respect API limits
- **Data Accuracy**: Always verify important financial data independently
- **Account Types**: Supports multiple account types (Standard, IRA, etc.)

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