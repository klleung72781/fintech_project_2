# define modules to import
import os
import numpy as np
import pandas as pd
import ccxt
import asyncio
import hvplot.pandas
import nltk
import requests
import alpaca_trade_api as tradeapi
from alpaca_trade_api import StreamConn
from joblib import load
import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from bs4 import BeautifulSoup as bs
import pyarrow
import asyncio
import sys
import panel as pn
pn.extension()
from dotenv import load_dotenv
load_dotenv()
nltk.download('vader_lexicon')

# initiate trade api
api = tradeapi.REST(
    os.getenv('ALPACA_API_KEY'),
    os.getenv('ALPACA_SECRET_KEY'),
    base_url='https://paper-api.alpaca.markets'
)

# NLP on earnings transcripts of TSLA
## Find sources of transcripts - transcripts are downloaded in ./transcripts
def transcripts():
    import glob
    files = glob.glob("./transcripts/*.htm")
    htmls = [bs(open(file), 'html.parser') for file in files]

    transcript_df = pd.DataFrame(
        {
            'html': htmls
        }
    )
    return transcript_df

def transcript_nlp(ticker='TSLA'):
    analyzer = SentimentIntensityAnalyzer()
    response = requests.get(f'http://www.conferencecalltranscripts.org/?co={ticker}')
    html = bs(response.content, 'html.parser')
    ps = html.findAll('p')
    df = pd.DataFrame(
        {
            'p': [p.text for p in ps],
            'href': [p.findChild('a')['href'] for p in ps]
        }
    )
    df = df[
        (df.href.str.startswith('/include?location=')) &
        (df.p.str.contains('Source: '))
    ].copy()
    df['p_components'] = df.p.apply(
        lambda p: re.split(' \| |\\n', p)
    )
    df['date'] = df.p_components.apply(
        lambda p: p[2]
    )
    df.date = df.date.astype('datetime64[ns]')
    df.set_index('date', inplace=True)
    df.href = df.href.apply(
        lambda p: p[18:]
    )
    df['source'] = df.p_components.apply(
        lambda p: p[4][8:].strip()
    )
    df = df[df.source.isin(['Motley Fool', 'Thomson'])].copy()
    df['articles'] = df.apply(
        lambda row: analyzer.polarity_scores(' '.join([p.text for p in bs(requests.get(row['href']).content, 'html.parser').findAll('p')])),
        axis = 1
    )
    return df

## NLP classification - King/George

## Ticker tweets NLP (Good2Have) - King
def tweet_search_by_user(handle, count=10):
    file_name = f'tweets_{handle}.feather'
    # read or init a dataFrame
    if os.path.isfile(file_name):
        df = pd.read_feather(file_name)
    else:
        df = pd.DataFrame()
    
    from requests_oauthlib import OAuth1
    url_rest = "https://api.twitter.com/1.1/search/tweets.json"
    auth = OAuth1(
        os.getenv('TWTR_API_KEY'),
        os.getenv('TWTR_API_SECRET'),
        os.getenv('TWTR_ACCESS_TOKEN'),
        os.getenv('TWTR_TOKEN_SECRET')
    )
    
    params = {'q': handle, 'count': count, 'lang': 'en',  'result_type': 'recent'}
    if df.empty == False:
        params['since_id'] = df.id.max()

    headers = {"Authorization": f"Bearer {os.getenv('TWTR_BEARER_TOKEN')}"}
    results = requests.get(url_rest, params=params, auth=auth)
    if results.status_code == 200:
        df.append(pd.DataFrame.from_dict(json.loads(response.text)['statuses']))
        df.write_feather(file_name)
    
    return df


# main streaming connection - King
def main(args):
    print(f'Start Streaming ticker: {args[0]}')

    conn = StreamConn(
        os.getenv('ALPACA_API_KEY'),
        os.getenv('ALPACA_SECRET_KEY'),
        base_url='https://paper-api.alpaca.markets'
    )

    @conn.on(r'^trade_updates$')
    async def on_account_updates(conn, channel, account):
        print('account', account)

    @conn.on(r'^status$')
    async def on_status(conn, channel, data):
        print('polygon status update', data)

    @conn.on(r'^AM$')
    async def on_minute_bars(conn, channel, bar):
        print('bars', bar)

    @conn.on(r'^A$')
    async def on_second_bars(conn, channel, bar):
        print('bars', bar)

    async def periodic():
        while True:
            if api.get_clock().is_open == False:
                print('Market is not open, exiting...')
                sys.exit(1)
            await asyncio.sleep(30)
            
    loop = conn.loop
    loop.run_until_complete(asyncio.gather(
        conn.subscribe(['trade_updates', f'AM.{args[0]}']),
        periodic(),
    ))
    loop.close()

if __name__ == '__main__':
    main(sys.argv[1:])