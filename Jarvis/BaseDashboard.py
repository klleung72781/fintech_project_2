import numpy as np
import pandas as pd
import ccxt
import asyncio
import os
import matplotlib.pyplot as plt
import alpaca_trade_api as tradeapi
​
import hvplot.pandas
import panel as pn
​
from dotenv import load_dotenv
load_dotenv()
​
pn.extension()
​
​
​
​
def initialize(cash=None):
    """Initialize the dashboard, data storage, and account balances."""
    print("Intializing Account and DataFrame")
​
    # Initialize Account
    account = {"balance": cash, "shares": 0}
​
    # Initialize dataframe
    # @TODO: We will update this later!
    df = fetch_data()
​
    # Intialize the dashboard
    dashboard = build_dashboard()
​
    # @TODO: We will complete the rest of this later!
    return account, df, dashboard
​
​
def build_dashboard():
    """Build the dashboard."""
    loading_text = pn.widgets.StaticText(name="Trading Dashboard", value="Loading...")
    dashboard = pn.Column(loading_text)
    print("init dashboard")
    return dashboard
​
​
def update_dashboard(df, dashboard):
    """Update the dashboard."""
    dashboard[0] = df.hvplot()
    return
​
​
def fetch_data():
    """Fetches the latest prices."""
    # Set Alpaca API key and secret
    alpaca_api_key = os.getenv("ALPACA_API_KEY")
    alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
    api = tradeapi.REST(alpaca_api_key, alpaca_secret_key, api_version='v2')
    
    # Set the ticker
    ticker = "TSLA"
​
    # Set timeframe to '1D'
    timeframe = '1D'
​
    # Set start and end datetimes of 1 year, between now and 365 days ago.
    start_date = pd.Timestamp("2010-06-29", tz="America/New_York").isoformat()
    end_date = pd.Timestamp("2020-10-05", tz="America/New_York").isoformat()
​
    # Get 1 year's worth of historical data for AAPL
    df = api.get_barset(
      ticker,
      timeframe,
      limit=None,
      start=start_date,
      end=end_date,
      after=None,
      until=None,
      ).df
     
     # Drop Outer Table Level
    df = df.droplevel(axis=1, level=0)
​
     # Use the drop function to drop extra columns
    df.drop(columns=['open', 'high', 'low', 'volume'], inplace=True)
​
     # Since this is daily data, we can keep only the date (remove the time) component of the data
    df.index = df.index.date                                                            
     
    return df
​
​
def generate_signals(df):
    """Generates trading signals for a given dataset."""
    print("Generating Signals")
    # Set window
    short_window = 10
​
    signals = df.copy()
    signals["signal"] = 0.0
​
    # Generate the short and long moving averages
    signals["sma10"] = signals["close"].rolling(window=10).mean()
    signals["sma20"] = signals["close"].rolling(window=20).mean()
​
    # Generate the trading signal 0 or 1,
    signals["signal"][short_window:] = np.where(
        signals["sma10"][short_window:] > signals["sma20"][short_window:], 1.0, 0.0
    )
​
    # Calculate the points in time at which a position should be taken, 1 or -1
    signals["entry/exit"] = signals["signal"].diff()
​
    return signals
​
​
def execute_trade_strategy(signals, account):
    """Makes a buy/sell/hold decision."""
​
    print("Executing Trading Strategy!")
​
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
​
    return account
​
​
account, df, dashboard = initialize(10000)
dashboard.servable()
​
​
async def main():
    loop = asyncio.get_event_loop()
​
    while True:
        global account
        global df
        global dashboard
​
        new_df = await loop.run_in_executor(None, fetch_data)
        df = df.append(new_df, ignore_index=True)
​
        min_window = 22
        if df.shape[0] >= min_window:
            signals = generate_signals(df)
            account = execute_trade_strategy(signals, account)
​
        update_dashboard(df, dashboard)
​
        await asyncio.sleep(1)
​
​
# Python 3.7+
loop = asyncio.get_event_loop()
loop.run_until_complete(main())