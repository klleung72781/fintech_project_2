import requests, json
from config import *
import os
from alpaca_trade_api import StreamConn
import alpaca_trade_api as tradeapi
import threading
import time
import datetime
import logging
import argparse
import hvplot.pandas

import panel as pn
from dotenv import load_dotenv
load_dotenv()

pn.extension()


# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True


APCA_API_BASE_URL='https://paper-api.alpaca.markets'
ACCOUNT_URL = '{}/V2/ACCOUNT'.format(APCA_API_BASE_URL) 
ORDERS_URL = '{}/v2/orders'.format(APCA_API_BASE_URL)
alpaca_api_key = os.getenv("ALPACA_API_KEY")
alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
api = tradeapi.REST(alpaca_api_key, alpaca_secret_key, api_version='v2')
HEADERS = {"APCA-API-KEY-ID": alpaca_api_key, "APCA-API-SECRET-KEY": alpaca_secret_key}


def  initialize(cash=400000):
    """Initialize the dashboard, data storage, and account balances."""
    print("Intializing Account and DataFrame")
    account = requests.get(ACCOUNT_URL, headers= HEADERS)
    
    # Initialize dataframe
    # @TODO: We will update this later!
    df = fetch_data()

    # Intialize the dashboard
    dashboard = build_dashboard()
    
    return json.loads(account.content),  df, dashboard


def build_dashboard():
    """Build the dashboard."""
    loading_text = pn.widgets.StaticText(name="Trading Dashboard", value="Loading...")
    dashboard = pn.Column(loading_text)
    print("init dashboard")
    return dashboard


def update_dashboard(df, dashboard):
    """Update the dashboard."""
    dashboard[0] = df.hvplot()
    return


def fetch_data():
    # Set the ticker
    ticker = "TSLA"

    # Set timeframe to '1D'
    timeframe = '1D'

    # Get 1 year's worth of historical data for AAPL
    df = api.get_barset(
      ticker,
      timeframe,
      limit=None,
      after=None,
      until=None,
      ).df
     
     # Drop Outer Table Level
    df = df.droplevel(axis=1, level=0)

     # Use the drop function to drop extra columns
    df.drop(columns=['open', 'high', 'low', 'volume'], inplace=True)

     # Since this is daily data, we can keep only the date (remove the time) component of the data
    df.index = df.index.date                                                            
     
    return df

def generate_signals(df):
    """Generates trading signals for a given dataset."""
    print("Generating Signals")
    # Set window
    short_window = 1

    signals = df.copy()
    signals["signal"] = 0.0

    # Generate the short and long moving averages
    signals["sma10"] = signals["close"].rolling(window=1).mean()
    signals["sma20"] = signals["close"].rolling(window=2).mean()

    # Generate the trading signal 0 or 1,
    signals["signal"][short_window:] = np.where(
        signals["sma10"][short_window:] > signals["sma20"][short_window:], 1.0, 0.0
    )

    # Calculate the points in time at which a position should be taken, 1 or -1
    signals["entry/exit"] = signals["signal"].diff()

    return signals

def execute_trade_strategy(signals, account):
    """Makes a buy/sell/hold decision."""

    print("Executing Trading Strategy!")

    if signals["entry/exit"].iloc[-1] == 1.0:
        print("buy")
        number_to_buy = round(account["balance"] / signals["close"].iloc[-1], 0) * 0.001
        account["balance"] -= number_to_buy * signals["close"].iloc[-1]
        account["shares"] += number_to_buy
    elif signals["entry/exit"].iloc[-1] == -1.0:
        print("sell")
        account["balance"] += signals["close"].iloc[-1] * account["shares"]
        account["shares"] = 0
    else:
        print("hold")

    return account


def create_order(symbol, qty, side, type, time_in_force):
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": type,
        "time_in_force": time_in_force
    }
    r = requests.post(ORDERS_URL, headers=HEADERS, json=data)
    
    return json.loads(r.content)

response = create_order("AAPL", 2, "buy", "market", "gtc")
print(response)






