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
    

    #reindexing , dropping null columns if any 
    desired=["Symbol", "Date", "Open", "High", "Low", "Close", "Volume"]
    df=df.reindex(columns=desired)
    before_cols=set(df.columns)
    df=df.dropna(axis=1,how="all")
    dropped_columns=before_cols-set(df.columns)

    if dropped_columns:
        logger.warning(
            f'[stock] {symbol} dropped entirely empty columns : {dropped_columns}'
        )
    
    criticals= ["Symbol", "Date", "Open", "High", "Low", "Close"]
    missing_critical=[c for c in criticals if c not in df.columns]
    
    if missing_critical:
        logger.error( 
            f"[stock][{symbol}] Critical columns missing after reindex: "
        f"{missing_critical} — cannot clean this file"
        )
        return None
    
    
    #dropping duplicates
    before=len(df)
    
    df=df.drop_duplicates(subset=["Symbol", "Date"],keep="first")
    removed=before-len(df)

    if removed>0:
        logger.warning(
            f'[stock] {symbol} removed {removed} duplicate rows'
        )
    else:
        logger.info(
            f'[stock] {symbol} no duplicate rows found'
        )

    #dropping NULLs and value corerction
    for col in ["Open","High","Low","Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(4)

    before = len(df)
    df=df.dropna(subset=["Symbol", "Date", "Open", "High", "Low", "Close"])
    removed=before-len(df)

    if removed>0:
        logger.warning(
            f'[stock] {symbol} removed {removed} rows with NULL values'
        )
    else:
        logger.info(
            f'[stock] {symbol} no rows with NULL value found'
        )

    #volume an date correction
    df["Volume"]=pd.to_numeric(df["Volume"],errors="coerce").fillna(0).astype(int)
    
    df["Date"]=pd.to_datetime(df["Date"],errors="coerce")
    df = df.dropna(subset=["Date"])
    df=df.sort_values("Date")
    df["Date"]=df["Date"].dt.strftime("%Y-%m-%d")

    
    # all columns bad price / price less than 0 correction
    bad_price=df[(df["Close"] <= 0) |
    (df["Open"]  <= 0) |
    (df["High"]  <= 0) |
    (df["Low"]   <= 0) |
    (df["High"]  <  df["Low"])|
    (df["Low"]<=df["Open"])|
    (df["Low"]<=df["Close"])|
    (df["High"]>=df["Open"])|
    (df["High"]>=df["Close"])]
    if len(bad_price)>0:
        logger.warning(
            f"[stock][{symbol}] Found {len(bad_price)} rows with invalid price data — removing"
        )
        df=df.drop(bad_price.index)

    #sorting and reset index
    df=df.reset_index(drop=True)
    
    final_count=len(df)
    logger.info(
        f"[stock][{symbol}] Cleaning complete — "
        f"{original_count} → {final_count} rows "
        f"({original_count - final_count} removed total)"
    )
    return df

def clean_news_data(df,symbol,logger,config):
    original_count=len(df)
    logger.info(
        f"[news][{symbol}] Starting cleaning — {original_count} rows"
    )    

    #remove duplicates
    before=len(df)
    df=df.drop_duplicates(subset=["symbol","title","date"],keep="first")
    df=df.drop_duplicates(subset=["link"],keep="first")
    removed=before-len(df)
    if removed>0:
        logger.warning(
            f'[news] {symbol} removed {removed} duplicate rows' 
        )

    #filtering relevant information 

    def filter_relevant_news(df,symbol,logger):
        if symbol not in config["symbol_keywords"]:
            logger.warning(
                f"[{symbol}] No keyword list defined in SYMBOL_KEYWORDS. "
                f"Skipping relevance filter — all articles kept."
            )
            return df    
    
        keywords=config["symbol_keywords"][symbol]
        original_count=len(df)

        def is_relevant(title):
            if not isinstance(title,str):
                return True
            
            title_lower=title.lower()
            return any(keyword in title_lower for keyword in keywords)
        relevant_mask=df["title"].apply(is_relevant)
        
        df_filtered=df[relevant_mask].copy()
        
        removed_count=original_count-len(df)
        
        if removed_count > 0:
                logger.warning(
                    f"[{symbol}] Relevance filter removed {removed_count} articles "
                    f"({(removed_count / original_count) * 100:.1f}%) as irrelevant. "
                    f"{len(df_filtered)} articles remaining."
                )
        else:
            logger.info(
                f"[{symbol}] Relevance filter passed — "
                f"all {original_count} articles appear relevant."
            )
        if len(df_filtered) == 0:
            logger.critical(
                f"[{symbol}] Relevance filter removed ALL articles. "
                f"Keyword list may be too strict. "
                f"Returning unfiltered data to prevent data loss."
            )
            return df
    
        return df_filtered

    #title cleaning 
    df= filter_relevant_news(df,symbol,logger)
    before=len(df)
    #strip title
    df["title"]=df["title"].str.strip()
    df=df[df["title"]!=""]
    #remove very short title
    df=df[df["title"].str.len()>8]
    #remove invalid symbols
    df=df[df["title"].str.contains(r"[A-Za-z]",regex=True)]
    #remove nulls
    df=df.dropna(subset=["title"])
    removed=before-len(df)
    if removed>0:
        logger.warning(
            f'[news] {symbol} removed {removed} rows with NULL title' 
        )
    

    #NULL description
    null_desc=df["description"].isnull().sum()
    if null_desc:
        df["description"]=df["description"].fillna("")
        logger.warning(
            f"[news][{symbol}] Filled {null_desc} null descriptions with empty string"
        )
    

    #stripping whitespaces

    
    df["description"]=df["description"].str.strip()

    #datetime formatting and removing NULLs
    df["date"]=pd.to_datetime(df["date"],errors="coerce")

    before=len(df)
    df=df.dropna(subset=["date"])
    removed=before-len(df)
    if removed > 0:
        logger.warning(
            f"[news][{symbol}] Dropped {removed} rows where date "
            f"could not be parsed"
        )
    df["date"]=df["date"].dt.strftime("%Y-%m-%d")

    
    #enforcing column order/reindexing
    desired=["symbol", "date", "title", "description", "link"]
    df=df.reindex(columns=desired)
    before_cols=set(df.columns)
    df=df.dropna(axis=1,how="all")
    dropped_columns=before_cols-set(df.columns)

    if dropped_columns:
        logger.warning(
            f'[news] {symbol} dropped entirely empty columns : {dropped_columns}'
        )
    
    #adding text column
    df["text"]=df["title"] + " " + df["description"]
    #sorting and reset index
    df=df.sort_values("date")
    df=df.reset_index(drop=True)

    final_count=len(df)
    logger.info(
        f"[news][{symbol}] Cleaning complete — "
        f"{original_count} → {final_count} rows "
        f"({original_count - final_count} removed total)"
    )
    return df

def save_clean_data(df,symbol,output_path,file_suffix,logger):
    os.makedirs(output_path,exist_ok=True)
    file_name=f'{symbol}_{file_suffix}_processed.csv'
    full_path=os.path.join(output_path,file_name)

    try:
        df.to_csv(full_path,index=False)
        logger.info(
            f'saved {len(df)} rows to {full_path}'
        )
        return full_path
    except PermissionError:
        logger.error(
            f'cannot write to {full_path} file may be open somewhere else'
        )
        return None
    
    except Exception as e :
        logger.error(
            f'failed to save to {full_path} : {type(e).__name__} : {e}'
        ) 
        return None

    
def main():
    config,base_dir=load_config()
    log_dir=os.path.join(base_dir,config["paths"]["logs"])
    log_filename=config["logging"]["log_filename"]
    raw_stock_path=os.path.join(base_dir,config["paths"]["raw_stock"])
    raw_news_path=os.path.join(base_dir,config["paths"]["raw_news"])
    processed_stock_path=config["paths"]["processed_stock"]
    processed_news_path=config["paths"]["processed_news"]
    
    logger=setup_logger(__name__,log_dir,log_filename)

    
    logger.info("=" * 60)
    logger.info("CLEANER — starting")
    logger.info("=" * 60)

    symbols=config["stocks"]["symbols"]

    stock_success,stock_failed=[],[]
    news_success,news_failed=[],[]

    for symbol in symbols:
        logger.info(
            f'cleaning - {symbol}'
        )
        stock_path=os.path.join(raw_stock_path,f"{symbol}_raw.csv")
        df_stock=load_csv(stock_path,logger)

        if df_stock is not None:
            df_cleaned_stock=clean_stock_data(df_stock,symbol,logger,config)
            if df_cleaned_stock is not None:
                saved=save_clean_data(df_cleaned_stock,symbol,processed_stock_path,"stock",logger)
            if saved:
                stock_success.append(symbol)
            else :
                stock_failed.append(symbol)
        else:
            stock_failed.append(symbol)
        
        news_path=os.path.join(raw_news_path,f"{symbol}_news_raw.csv")
        df_news=load_csv(news_path,logger)

        if df_news is not None:
            df_cleaned_news=clean_news_data(df_news,symbol,logger,config)
            if df_cleaned_news is not None:
                saved=save_clean_data(df_cleaned_news,symbol,processed_news_path,"news",logger)
            if saved:
                news_success.append(symbol)
            else:
                news_failed.append(symbol)
        else:
            news_failed.append(symbol)
        
    
    logger.info("=" * 60)
    logger.info("CLEANING SUMMARY")
    logger.info("=" * 60)

    total_failed=len(news_failed) + len(stock_failed)
    total_passed=len(news_success) + len(stock_success)
    if total_failed==0:
        logger.info(
            f'all files cleaned successfully'
        )
    elif total_passed==0:
        logger.critical(
            f'FAILED TO CLEAN ANY FILE - NO FILE WAS CLEANED'
        )
    
    else:
        logger.warning(
            f"{total_failed} file(s) failed — review errors above"
        )
    
    logger.info("="*60)

if __name__=="__main__":
    main()