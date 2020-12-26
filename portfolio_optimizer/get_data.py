import requests
import pandas as pd
from datetime import datetime
from pandas_datareader import data as web

#SNP - China Petroleum & Chemical Corporation (USD)
#ROSN.ME Rosneft (RUB)
#2222.SR - Saudi Arabian Oil (SAR)
#BP - British Petroleum (USD)
#XOM - Exxon Mobil Corporation (USD)


def USD_to_currency_rate(currency):
   base_URL = "https://api.exchangerate-api.com/v4/latest/USD"
   response = requests.get(base_URL, params='base=USD')
   if response.status_code == 200:
      return response.json()['rates'][currency]


assets =  ["SNP", "RDSA.AS", "ROSN.ME", "BP", "XOM"]
currencies = ['USD', 'EUR', 'RUB', 'USD', 'USD']
#assets = ['AAPL', 'AMZN', 'FB', 'GOOGL']
#currencies = ['USD', 'USD', 'USD', 'USD']
stockStartDate = '2013-01-01'
today = datetime.today().strftime('%Y-%m-%d')

df = pd.DataFrame()

for stock, currency in zip(assets, currencies):
   df[stock] = web.DataReader(stock,data_source='yahoo',start=stockStartDate , end=today)['Adj Close']
   df[stock] = df[stock] / USD_to_currency_rate(currency)
   
df.fillna(df.mean(), inplace=True)
df.to_csv("stonks_energy.csv")

