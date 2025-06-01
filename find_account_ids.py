# find_account_ids.py
import robin_stocks.robinhood as r
from config import load_config

def main():
    config = load_config()
    r.login(config["robinhood"]["username"], config["robinhood"]["password"])
    
    accounts = r.load_account_profile(info=None)
    print("Your account ID:", accounts['account_number'])

if __name__ == "__main__":
    main()