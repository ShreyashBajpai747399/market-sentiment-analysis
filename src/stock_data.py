import yfinance as yf
import pandas as pd
from pathlib import path
import datetime as dt

def get_stock_data(ticker):
        
    curr_date=dt.date.today()
        
    data=yf.download(ticker,start='2000-01-01',end=curr_date)
        
    if isinstance(data.columns,pd.MultiIndex):
        data.columns=data.columns.get_level_values(0)
        
    data.reset_index(inplace=True)

    currdir=path(__file__).resolve().parent
    folderpath=currdir.parent / 'data' / 'raw' / ticker
    folderpath.mkdir(parents=True,exist_ok=True)


    filepath=folderpath/f'{ticker}_stock_data.csv'
    
    data.to_csv(filepath,index=False)
        
    print(f'the data is saved in {ticker} file')

