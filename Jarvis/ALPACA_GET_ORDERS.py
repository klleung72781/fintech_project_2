import alpaca_trade_api as tradeapi
import requests, json
from config import *
import os
​
import hvplot.pandas
import panel as pn
​
from dotenv import load_dotenv
load_dotenv()
​
APCA_API_BASE_URL='https://paper-api.alpaca.markets'
ACCOUNT_URL = '{}/V2/ACCOUNT'.format(APCA_API_BASE_URL) 
ORDERS_URL = '{}/v2/orders'.format(APCA_API_BASE_URL)
alpaca_api_key = os.getenv("ALPACA_API_KEY")
alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
api = tradeapi.REST(alpaca_api_key, alpaca_secret_key, api_version='v2')
HEADERS = {"APCA-API-KEY-ID": alpaca_api_key, "APCA-API-SECRET-KEY": alpaca_secret_key}
​
​
def  get_account():
    r = requests.get(ACCOUNT_URL, headers= HEADERS )
    
    return json.loads(r.content)
​
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
​
response = create_order("AAPL", 2, "buy", "market", "gtc")
print(response)