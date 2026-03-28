import yfinance as yf
import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_config, setup_logger

def download_stock(symbol,start_date,end_date,interval,logger):
    logger.info(f'starting download for {symbol}')

    try:
        df=yf.download(ticker=symbol,
                       start=start_date,
                       end=end_date,
                       interval=interval)
        
        if df.empty:
            logger.error(f'no data returned for {symbol}'
                         f"Possible causes: wrong symbol, bad date range, "
                f"or symbol is delisted.")
            return None
        
        df.reset_index(inplace=True)

        df.columns=[col[0] if isinstance(col,tuple) else col
                    for col in df.columns]
        
        df['Symbol']=symbol
        
        #strftime formats datetime into a string
        df['Date']=pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

        for col in ["Open", "High", "Low", "Close"]:
            if col in df.columns:
                df[col]=df[col].round(4)

        
        
