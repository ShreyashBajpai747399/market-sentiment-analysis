import os
import pandas as pd
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
from utils import load_config,setup_logger,load_csv

def check_required_columns(df,required_columns,symbol,data_type,logger):
    missing=[col for col in required_columns if col not in df.columns]

    if missing:
        logger.error(
            f'check complete for {symbol}-{data_type} : {len(missing)} columns missing : {missing}'
        )
        return False
    
    logger.info(
        f'check complete for {symbol}-{data_type} : ALL COLUMNS PRESENT'
        )
    return True

def check_null_values(df,symbol,critical_nulls,data_type,logger):
    failed=False
    for col in df.columns :
        if col not in critical_nulls:
            continue

        null_count=df[col].isnull().sum()

        if null_count>0:
            pct=(null_count/len(df))*100

            if pct>10:
                logger.error(
                    f'{symbol}{data_type} : column {col} has {null_count} NULLS'
                    f'{null_count} nulls {pct:.1f}% of rows '
                    f'it exceeds the threshold of 10%'
                )
                failed=True
            else:
                logger.warning(
                    f"[{data_type}][{symbol}] Column '{col}' has {null_count} NULLs "
                    f"({pct:.1f}% of rows) — exceeds 10% threshold"
                )
        else :
            logger.info(
                f"[{data_type}][{symbol}] Column '{col}' — no nulls ✓"
            )
    return not failed

def check_duplicates(df,subset_cols,symbol,data_type,logger):
    existing_cols=[c for c in subset_cols if c in df.columns]

    #subset columns means that python will check the duplicacy based on all the columns present in the subset
    duplicate_count=df.duplicated(subset=existing_cols).sum()

    if duplicate_count>0:
        logger.error(
            f'{duplicate_count} duplicates found for {data_type}{symbol}'
        )
        return False
    logger.info(
        f'no duplicates found for {data_type}{symbol}'
    )
    return True

def check_stock_price_range(df,symbol,logger,data_type):
    failed=False
    price_cols=["Open","High","Low","Close"]

    for col in price_cols:
        if col not in df.columns:
            continue

        invalid=df[df[col]<=0]

        if len(invalid)>0:
            logger.warning(
               f"[stock][{symbol}] Column '{col}' has "
                f"{len(invalid)} rows with price <= 0. "
                f"Dates affected: {invalid['Date'].tolist()[:5] if "Date" in invalid.columns else []}"
            )
            failed=True
        
        else:
            logger.info(
                f"[stock][{symbol}] '{col}' all values > 0 ✓"
            )
    if "High" in df.columns and "Low" in df.columns:
        invalid_hl=df[df["High"]<df["Low"]]

        if len(invalid_hl)>0:
            logger.warning(
                f"[stock][{symbol}] {len(invalid_hl)} rows where "
                f"High < Low — data is corrupt. "
                f"Dates: {invalid_hl['Date'].tolist()[:5] if "Date" in invalid_hl.columns else []}"
            )
            failed=True
        else:
            logger.info(
                f"[stock][{symbol}]  High >= Low for all rows ✓"
            )
    
    if "Volume" in df.columns:
        invalid_vol=df[df["Volume"]<0]

        if len(invalid_vol) > 0:
            logger.warning(
                f"[stock][{symbol}] {len(invalid_vol)} rows with negative Volume "
                f"Dates: {invalid_vol['Date'].tolist()[:5] if "Date" in invalid.columns else []}"
            )
            failed=True
        else:
            logger.info(
                f"[stock][{symbol}]  vol>=0 for all rows ✓"
            )

    return not failed

def check_row_count(df,symbol,min_rows,logger,data_type):
    if len(df)<min_rows:
        logger.error( 
            f"[{data_type}][{symbol}] Only {len(df)} rows — "
            f"minimum expected is {min_rows}. "
            f"Data is likely incomplete."
            )
        return False
    else:
        logger.info(
            f"[{data_type}][{symbol}] Row count: {len(df)} | Minimum required: {min_rows}"
        )
        return True

def check_date_format(df,date_col,data_type,symbol,logger):
    if date_col not in df:
        logger.warning(
            f'[{data_type}] [{symbol}] date column {date_col} not found '
            f'skipping date format check'
        )
        return True
    pattern=r"^\d{4}-\d{2}-\d{2}$"

    non_null_dates=df[date_col].dropna()
    invalid_dates=non_null_dates[~non_null_dates.astype(str).str.match(pattern)]

    if len(invalid_dates)>0:
        logger.error(
            f'{data_type} {symbol} : {len(invalid_dates)} do not match the YYYY-mm-dd format'
            f'examples : {invalid_dates.tolist()[:3]}'
        )
        return False
    
    logger.info(
        f'row count check complete - all dates are in YYYY-mm-dd format    '
    )
    return True
def validate_stock_file(symbol,raw_stock_path,logger,config):
    
    file_path=os.path.join(raw_stock_path,f'{symbol}_raw.csv')
    
    logger.info(f'starting stock validation checks for {symbol}')

    df=load_csv(file_path,logger)

    if df is None:
        return False
    
    required_columns=["Symbol", "Date", "Open", "High",
                      "Low", "Close", "Volume"]
    
    critical_nulls=["Symbol","Date","Close"]

    results={
        "columns":check_required_columns(df,required_columns,symbol,"stock",logger),
        "nulls":check_null_values(df,symbol,critical_nulls,"stock",logger),
        "duplicates":check_duplicates(df,["Symbol","Date"],symbol,"stock",logger),
        "ranges":check_stock_price_range(df,symbol,logger,"stock"),
        "rows":check_row_count(df,symbol,min_rows=config["validation"]["min_rows"]["stock"],logger=logger,data_type="stock"),
        "dates":check_date_format(df,"Date","stock",symbol,logger)
    }

    passed=all(results.values())
    if passed:
        logger.info(
            f'["stock"] {symbol} passed all validation checks'
        )
    else:
        failed_checks = [k for k, v in results.items() if not v]
        """for k, v in results.items():
            if v == False:
                failed_checks.append(k)"""
        
        logger.error(
            f'["stock"] {symbol} failed checks : {failed_checks}'
        )
    return passed
        
def validate_news_file(symbol,raw_news_path,logger,config):
    file_path=os.path.join(raw_news_path,f"{symbol}_news_raw.csv")
    logger.info(
        f'starting news validation checks for {symbol}'
    )

    df=load_csv(file_path,logger)

    if df is None:
        return False
    
    required_columns=["title","description","link","date","symbol","raw_date"]
    critical_nulls=["symbol","date","title"]

    results={
         "columns":check_required_columns(df,required_columns,symbol,"news",logger),
        "nulls":check_null_values(df,symbol,critical_nulls,"news",logger),
        "duplicates":check_duplicates(df,["symbol","date","title"],symbol,"news",logger),
        "rows":check_row_count(df,symbol,min_rows=config["validation"]["min_rows"]["news"],logger=logger,data_type="news"),
        "dates":check_date_format(df,"date","news",symbol,logger)
    }
    passed=all(results.values())

    if passed:
        logger.info(
            f'SUCCESSFULL - [news] {symbol} passed all checks'
        )

    else:
        failed_checks=[k for k , v in results.items() if not v]
        logger.error(
            f'[news] {symbol} failed checks : {failed_checks}'
        )
    return passed

def main():
    config,base_dir=load_config()
    raw_stock_path=os.path.join(base_dir,config["paths"]["raw_stock"])
    raw_news_path=os.path.join(base_dir,config["paths"]["raw_news"])
    log_dir=os.path.join(base_dir,config['paths']["logs"])
    
    logger=setup_logger(__name__,log_dir,config["logging"]["log_filename"])

    symbols=config["stocks"]["symbols"]

    logger.info("=" * 60)
    logger.info("VALIDATOR — starting")
    logger.info("=" * 60)

    stock_passed,stock_failed=[],[]
    news_passed,news_failed=[],[]

    for symbol in symbols:
        logger.info(
            f'VALIDATING - {symbol}'
        )
        if validate_stock_file(symbol,raw_stock_path,logger,config):
            stock_passed.append(symbol)
        else :
            stock_failed.append(symbol)

        if validate_news_file(symbol,raw_news_path,logger,config):
            news_passed.append(symbol)
        else :
            news_failed.append(symbol)

    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    logger.info(
        f'Stock - Passed : {len(stock_passed)} | failed : {len(stock_failed)} '
    )
    
    logger.info(
        f'News - Passed : {len(news_passed)} | failed : {len(news_failed)} '
    )

    total_failed=len(news_failed)+len(stock_failed)

    if total_failed==0:
        logger.info(
            f'ALL FILES PASSED CHECKS'
        )
    else:
        logger.warning(
            f"{total_failed} file(s) failed validation. "
            f"Review errors above before running cleaning step."
        )

if __name__=="__main__":
    main()

