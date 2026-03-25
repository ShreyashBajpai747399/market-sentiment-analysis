import yfinance as yf
import pandas as pd
import os
import datetime as dt

def get_stock_data(ticker):
        
    curr_date=dt.date.today()
        
    data=yf.download(ticker,start='01-01-2000',end=curr_date)
        
    if isinstance(data.columns,pd.MultiIndex):
        data.columns=data.columns.get_level_values(0)
        
    data.reset_index(inplace=True)

    folderpath=f'../../data/raw/{ticker}'
    os.makedirs(folderpath,exist_ok=True)

    filepath=f'{folderpath}/{ticker}_stock_data.csv'
    data.to_csv(filepath,index=False)
        
    print(f'the data is saved in {ticker} file')

