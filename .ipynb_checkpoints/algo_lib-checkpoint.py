# algotrading library
import pandas as pd
import yfinance as yf

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
        period = '730h',
        interval = '1h'
    )
    return data

# generate crossover signal
def crossover_signal(df):
    SHORT_WINDOW = 50
    LONG_WINDOW = 200
    
    # Construct a `Fast` and `Slow` Exponential Moving Average from short and long windows, respectively
    df['fast_close'] = df.Close.ewm(halflife = SHORT_WINDOW).mean()
    df['slow_close'] = df.Close.ewm(halflife = SHORT_WINDOW).mean()

    # Construct a crossover trading signal
    df['crossover_long'] = np.where(df.fast_close > df.slow_close, 1.0, 0.0)
    df['crossover_short'] = np.where(df.fast_close < df.slow_close, -1.0, 0.0)
    df['crossover_signal'] = df.crossover_long + df.crossover_short

    return df