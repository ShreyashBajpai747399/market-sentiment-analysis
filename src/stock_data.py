import yfinance as yf
import pandas as pd
import os
import datetime as dt
companys=['TCS.NS','INFY.NS','WIPRO.NS','AAPL','GOOGL','MSFT','AMZN']

def get_data_stock(tickr):
        
    curr_date=dt.date.today()
        
    data=yf.download(tickr,start='01-01-2000',end=curr_date)
        
    if isinstance(data.columns,pd.MultiIndex):
        data.columns=data.columns.get_level_values(0)
        
    data.reset_index(inplace=True)

    folderpath=f'../../data/raw/{tickr}'
    os.makedirs(folderpath,exist_ok=True)

    filepath=f'{folderpath}/{tickr}_stock_data.csv'
    data.to_csv(filepath,index=False)
        
    print(f'the data is saved in {tickr} file')

