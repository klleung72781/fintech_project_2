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

sys.path.append('.')
import algo_lib

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

def prediction(ticker, crossover_signal):
    model = load(f'{ticker}_daily.joblib')
    return model.predict(crossover_signal)

def get_bar(ticker):
    return api.get_barset(ticker.upper(), 'day', limit=1)[ticker.upper()][0].c

def make_trade(signal, ticker, amount):
    # first get the last trade on this ticker
    order_list = api.list_orders(
        status = 'closed',
        limit = 200
    )
    order_dict = [
        order._raw for order in order_list
        if order._raw['symbol'] == ticker and order._raw['status'] != 'canceled'
    ]
    last_trade = [] if len(order_dict) == 0 else order_dict[-1]
    last_side = 'sell' if len(order_dict) == 0 else order_dict[-1]['side']

    # decision
    if signal == 1:
        side = 'buy' if last_side == 'sell' else None
        qty = (
            round(amount/api.get_last_quote('TSLA')._raw['askprice'])
            if last_side == 'sell' else None
        )
    elif signal == 0:
        side = 'sell' if last_side == 'buy' else None
        qty = last_trade['qty'] if last_side == 'buy' else None
    else:
        side = None

    # trade!!!
    if side != None:
        print(f'''
    +++++++++++++++++++++++++++++++++++++++++++++++++
    Decision: {side}ing {qty} shares of {ticker}
    +++++++++++++++++++++++++++++++++++++++++++++++++
        ''')
        new_order = api.submit_order(
            symbol = ticker,
            qty = qty,
            side = side,
            type = 'market',
            time_in_force = 'gtc'
        )
        return new_order._raw['client_order_id']
    


def main(args):
    # Init
    ticker = args[0]
    amount = int(args[1])
    print(f'''
    +++++++++++++++++++++++++++++++++++++++++++++++++
    Initialize {ticker} Trading Decision for ${amount}
    +++++++++++++++++++++++++++++++++++++++++++++++++
    ''')
    
    # Load and update historical dataframe
    df = update_df(f'{ticker}_daily.feather')
    
    # Generate signal
    crossover_signal = algo_lib.crossover_signal(
        df, ['crossover_signal']
    ).tail(1)[['crossover_signal']]

    # Make prediction
    signal = prediction(ticker, crossover_signal)[0]
    print(f'''
    +++++++++++++++++++++++++++++++++++++++++++++++++
    Signal = {signal}
    +++++++++++++++++++++++++++++++++++++++++++++++++
    ''')

    # Final execution
    order_id = make_trade(signal, ticker, amount)
    print(f'''
    +++++++++++++++++++++++++++++++++++++++++++++++++
    Order accepted - Client Order ID: {order_id}
    +++++++++++++++++++++++++++++++++++++++++++++++++
    ''')

if __name__ == '__main__':
    main(sys.argv[1:])