import yfinance as yf
import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_config, setup_logger

def download_stock(symbol,start_date,end_date,interval,logger):
    logger.info(f'starting download for {symbol}')

    try:
        df=yf.download(tickers=symbol,
                       start=start_date,
                       end=end_date,
                       interval=interval,
                       progress=False,
                       auto_adjust=True)
        
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

        #rounding off the values for the ease of calculation
        for col in ["Open", "High", "Low", "Close"]:
            if col in df.columns:
                df[col]=df[col].round(4)
        
        min_expected=50
        if len(df)<min_expected:
            logger.warning(f'{symbol} returned only {len(df)} rows , expected least were {min_expected}')

        else:
            logger.info(f'downloaded {len(df)} rows for {symbol}')


        #here we are forcing the columns to be in a specific order
        desired=["Symbol", "Date", "Open", "High", "Low", "Close", "Volume"]
        df=df.reindex(columns=desired)
        
        return df

    except ConnectionError as e:
        logger.error(
            f'Network error while downloading {symbol} : {e}. '
            f'Check your internet connection'
        )
        return None
        
    except ValueError as e:
        logger.error(
            f"data parsing error for {symbol} : {e}"
        )
        return None

    except Exception as e :
        logger.error(
            f'Unexpected error downloading. '
            f'{type(e).__name__} : {e}'
        )
        return None


def save_stock_data(df,symbol,raw_stock_path,logger):
    os.makedirs(raw_stock_path,exist_ok=True)
    full_path=os.path.join(raw_stock_path,f'{symbol}_raw.csv')
    
    if df is None or df.empty:
        logger.warning(
            f'No data to save for {symbol}'
        )
        return None
    else:
        try:
            df.to_csv(full_path,index=False)
            logger.info(
                f'{symbol} - Saved {len(df)} rows to {full_path}'
            )
            return full_path

        except PermissionError as e:
            logger.error(f"Cannot write {full_path} — file is open in another program. "
                f"Close it and retry.")
            return None

        except Exception as e :
            logger.error(f'failed to save {symbol} data : {type(e).__name__}: {e}')
            return None

def main():
    config,base_dir=load_config()
    log_dir=os.path.join(base_dir,config["paths"]["logs"])
    raw_stock_path=os.path.join(base_dir,config["paths"]["raw_stock"])
    logger=setup_logger(__name__,log_dir,config["logging"]["log_filename"])
    
    logger.info("=" * 60)
    logger.info("STOCK DOWNLOADER — starting")
    logger.info("=" * 60)

    symbols=config["stocks"]["symbols"]
    start_date=config["stocks"]["start_date"]
    end_date=config["stocks"]["end_date"]
    interval=config["stocks"]["interval"]
    
    successful,failed=[],[]

    for symbol in symbols:
        df=download_stock(symbol=symbol,start_date=start_date,end_date=end_date,interval=interval,logger=logger )

        if df is not None:
            saved=save_stock_data(df,symbol,raw_stock_path,logger)
            if saved :
                successful.append(symbol)
            else:
                failed.append(symbol)
        else :
            failed.append(symbol)
    logger.info('='*60)

    if len(failed)==0:
        logger.info(f'COMPLETE - all {len(successful)} downloads completed successfully')
    elif len(successful) == 0 :
        logger.critical(f'COMPLETE - all downloads failed : {symbols}. '
                    f'No data was saved , check internet connection adnd config. ')
    else :
        logger.warning(
            f'COMPLETED - {len(successful)} downloads successful : ({successful}) | '
            f'- {len(failed)} downloads failed ({failed}) '
        )

    logger.info("=" * 60)

if __name__=="__main__":
    main()