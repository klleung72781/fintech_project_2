# algotrading library
import pandas as pd
import yfinance as yf
import numpy as np

# max daily price
def historical_daily(ticker):
    data = yf.download(
        tickers = ticker,
        period = 'max',
        interval = '1d'
    )
    return data

def historical_hourly(ticker):
    data = yf.download(
        tickers = ticker,
        period = '730d',# max hourly history needs to be hardcoded
        interval = '1h'
    )
    return data

# generate crossover signal
def crossover_signal(df, x_var_list):
    # Set short and long windows
    SHORT_WINDOW = 50
    LONG_WINDOW = 200
    
    # Construct a `Fast` and `Slow` Exponential Moving Average from short and long windows, respectively
    df['fast_close'] = df.Close.ewm(halflife = SHORT_WINDOW).mean()
    df['slow_close'] = df.Close.ewm(halflife = LONG_WINDOW).mean()

    # Construct a crossover trading signal
    df['crossover_long'] = np.where(df.fast_close > df.slow_close, 1.0, 0.0)
    df['crossover_short'] = np.where(df.fast_close < df.slow_close, -1.0, 0.0)
    df['crossover_signal'] = df.crossover_long + df.crossover_short

    df.crossover_signal = df.crossover_signal.shift(1)
    df.dropna(subset=x_var_list, inplace=True)
    df.dropna(subset=['Daily_return'], inplace=True)
    return df.replace([np.inf, -np.inf], np.nan)