# define modules to import
import os
import numpy as np
import pandas as pd
import ccxt
import asyncio
import hvplot.pandas
import nltk
import requests
import re
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from bs4 import BeautifulSoup as bs
import panel as pn
pn.extension()
from dotenv import load_dotenv
load_dotenv()
nltk.download('vader_lexicon')


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
    from requests_oauthlib import OAuth1
    url_rest = "https://api.twitter.com/1.1/search/tweets.json"
    auth = OAuth1(
        os.getenv('TWTR_API_KEY'),
        os.getenv('TWTR_API_SECRET'),
        os.getenv('TWTR_ACCESS_TOKEN'),
        os.getenv('TWTR_TOKEN_SECRET')
    )
    params = {'q': handle, 'count': count, 'lang': 'en',  'result_type': 'recent'}
    headers = {"Authorization": f"Bearer {twtr_token}"}
    results = requests.get(url_rest, params=params, auth=auth)
    return results.text if results.status_code == 200 else None