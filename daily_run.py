import alpaca_trade_api as tradeapi
import os
import sys
import numpy as np
import pandas as pd
import pyarrow
import argparse
from joblib import load
from datetime import date
from dotenv import load_dotenv
load_dotenv()

#authentication and connection details
api_key = os.getenv('ALPACA_API_KEY')
api_secret = os.getenv('ALPACA_SECRET_KEY')
base_url = 'https://paper-api.alpaca.markets'

#instantiate REST API
api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')

#obtain account information
account = api.get_account()
print(account)

def update_df(file_name):
    df = pd.read_feather(file_name)
    df.drop(df.tail(1).index, inplace=True) #dropping last empty row
    
    # append df with new data
    last_close = get_bar('TSLA')
    today = date.today()
    new_row = pd.Series({
        'Date': today.strftime("%Y-%m-%d"),
        'Close': last_close,
        'Daily_return': last_close - df.Close[len(df)-1]
    })
    df = df.append(new_row, ignore_index=True)
    
    df.set_index('Date', inplace=True)
    df.index = df.index.astype('<M8[ns]')
    return df

def generate_signal(df):
    #generating signal
    SHORT_WINDOW = 50
    LONG_WINDOW = 200
    df['fast_close'] = df.Close.ewm(halflife = SHORT_WINDOW).mean()
    df['slow_close'] = df.Close.ewm(halflife = SHORT_WINDOW).mean()

    df['crossover_long'] = np.where(df.fast_close > df.slow_close, 1.0, 0.0)
    df['crossover_short'] = np.where(df.fast_close < df.slow_close, -1.0, 0.0)
    df['crossover_signal'] = df.crossover_long + df.crossover_short

    return df.tail(1)[['crossover_signal']]

def prediction(crossover_signal):
    model = load('random1_forest_model.joblib')
    return model.predict(crossover_signal)

def get_bar(ticker):
    return api.get_barset(ticker.upper(), 'day', limit=1)[ticker.upper()][0].c

def trading_decision(ticker, side):
    api.submit_order(
        symbol = ticker,
        qty = 1,
        side = 'buy'
    )


def main(args):
    print(args[0])
    df = update_df('df_close.feather')
    crossover_signal = generate_signal(df)
    print(prediction(crossover_signal))

if __name__ == '__main__':
    main(sys.argv[1:])