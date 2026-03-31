import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_config,setup_logger,load_csv

def clean_stock_data(df,symbol,logger,config):

    original_count=len(df)
    logger.info(
        f'[Stock][{symbol} has {original_count} rows'
        f" — now cleaning"
    )
    
    desired=["Symbol", "Date", "Open", "High", "Low", "Close", "Volume"]
    df.reindex(subset=desired)

    before_cols=set(df.columns)
    df.dropna(axis=1,how="all")
    dropped_columns=before_cols-set(df.columns)

    if dropped_columns:
        logger.warning(
            f'[stock] {symbol} dropped entirely empty columns : {dropped_columns}'
        )
        return None
    
    criticals= ["Symbol", "Date", "Open", "High", "Low", "Close"]
    missing_critical=[c for c in criticals if c not in df.columns]
    
    if missing_critical:
        logger.error( 
            f"[stock][{symbol}] Critical columns missing after reindex: "
        f"{missing_critical} — cannot clean this file"
        )
        return None
    

    before=len(df)

    df=df.drop_duplicates(subset=["symbol", "title"],keep="first")
    removed=before-len(df)

    if removed>0:
        logger.warning(
            f'[stock] {symbol} removed {removed} duplicate rows'
        )
    else:
        logger.info(
            f'[stock] {symbol} no duplicate rows found'
        )
    
    before=len(df)
    df=df.dropna(subset=["Date"])
    removed=before-len(df)

    if removed>0:
        logger.warning(
            f'[stock] {symbol} removed {removed} rows with NULL dates'
        )
    else:
        logger.info(
            f'[stock] {symbol} no rows with NULL dates found'
        )
    
    before = len(df)
    df=df.dropna(subset=["Close"])
    removed=before-len(df)

    if removed>0:
        logger.warning(
            f'[stock] {symbol} removed {removed} rows with NULL Close'
        )
    else:
        logger.info(
            f'[stock] {symbol} no rows with NULL Close found'
        )
    
    null_vol=df["Volume"].isnull().sum()
    if null_vol>0:
        df["Volume"]=df["Volume"].fillna(0)
        logger.warning(
            f'[stock] {symbol} {null_vol} rows with NULL Volume found - Filled with 0'
        )

    df["Date"]=pd.to_datetime(df["Date"],errors="coerce").dt.strftime("%Y-%m-%d")

    df["Volume"]=pd.to_numeric(df["Volume"],errors="coerce").fillna(0).astype(int)

    for col in ["Open","High","Low","Close"] :
        df[col]=pd.to_numeric(df[col],errors="coerce").round(4)
    