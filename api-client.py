import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

tickers = ["VOO", "MSFT"]

endDate = datetime.today()
startDate = endDate - timedelta(days=2*365)
print(startDate)

prices_dataframe = pd.DataFrame()

#['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'] #availible options
for ticker in tickers:
    data = yf.download(ticker, start=startDate,end=endDate)
    # prices_dataframe[ticker] = data['Close']
    # prices_dataframe[ticker] = data['Open']
    for column in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if column in data.columns:
            prices_dataframe[f'{ticker} {column}'] = data[column]
        else:
            print("no data in column")
prices_dataframe.to_sql()

print(prices_dataframe)




