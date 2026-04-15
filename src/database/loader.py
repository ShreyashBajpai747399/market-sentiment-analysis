import os 
import sys
import mysql.connector
import pandas as pd
import logging
from datetime import datetime , timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_config,load_csv,setup_logger

def connect_to_database(config,logger):
    try:
        conn=mysql.connector.connect(
            host = config["database"]["host"],
            port=config["database"]["port"],
            database=config["database"]["name"],
            user=config["database"]["user"],
            password=config["database"]["password"],
            charset=config["database"]["charset"]
            )
        
        logger.info("mysql connection established")
        return conn
    
    except mysql.connector.Error as e :
        f'failed to connect to the database : {e} . '
        f'check credentials in config.json and ensure MySQL is running'
        return None

def fill_DIM_DATE(conn,config,logger):

    cursor=conn.cursor()
    start=datetime.strptime(config["stocks"]["start_date"],"%Y-%m-%d")
    end=datetime.today()
    dates=pd.date_range(start=start,end=end,freq="D") 
    
    inserted,skipped=0,0

    for date in dates:
        is_trading=date.weekday()<5

        cursor.execute(""" INSERT IGNORE INTO DIM_DATE (full_date,year,month,day,day_of_week,is_trading_day) VALUES (%s, %s, %s, %s, %s, %s);""",(
            date.strftime("%Y-%m-%d"),
            int(date.year),
            int(date.month),
            int(date.day),
            date.strftime("%A"),
            is_trading
        ))

        if cursor.rowcount==1:
            inserted+=1
        else :
            skipped+=1

    conn.commit()
    cursor.close()
    logger.info(
        f"dim_date — inserted: {inserted} | skipped: {skipped}"
    )
    
def get_symbol_map(conn):
    cursor=conn.cursor()
    cursor.execute("select symbol,symbol_id from DIM_SYMBOL;")
    mapping={row[0]:row[1] for row in cursor.fetchall()}
    cursor.close()
    return mapping

def get_date_map(conn):
    cursor=conn.cursor()
    cursor.execute("select full_date,date_id from DIM_DATE;")
    mapping={str(row[0]):row[1] for row in cursor.fetchall()}
    cursor.close()
    return mapping

def load_stock_prices(conn,config,base_dir,symbol_map,date_map,logger):
    cursor=conn.cursor()
    stock_path=os.path.join(base_dir,config["paths"]["processed_stock"])
    symbols=config["stocks"]["symbols"]
    total_inserted,total_skipped=0,0

    for symbol in symbols:
        file_path=os.path.join(stock_path,f"{symbol}_stock_processed.csv")
        if not os.path.exists(file_path):
            logger.warning(f"[loader][stock] Not found: {file_path} — skipping")
            continue

        df=pd.read_csv(file_path)
        inserted,skipped=0,0
        for _,row in df.iterrows():
            symbol_id=symbol_map.get(str(row["Symbol"]))
            date_id=date_map.get(str(row["Date"]))
            if not symbol_id or not date_id:
                logger.warning(
                     f"[loader][stock] No ID for "
                    f"{row['Symbol']} {row['Date']} — skipping row"
                )
                continue

            cursor.execute("""insert ignore into Fact_Stock_Prices (symbol_id, date_id, open, high, low, close, volume) values(%s,%s,%s,%s,%s,%s,%s);""",(
                symbol_id,
                date_id,
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                int(row["Volume"])
            ))

            if cursor.rowcount==1:
                inserted+=1
            else:
                skipped+=1
            
        conn.commit()
        logger.info(
            f"[loader][stock][{symbol}] "
            f"inserted: {inserted} | skipped: {skipped}"
        )
        total_inserted+=inserted
        total_skipped+=skipped
    cursor.close()
    logger.info(
        f"[loader][stock] TOTAL — "
        f"inserted: {total_inserted} | skipped: {total_skipped}"
    )

def load_news_articles(conn,config,base_dir,date_map,symbol_map,logger):
    cursor=conn.cursor()
    sentiment_path=os.path.join(base_dir,config["paths"]["sentiment"])
    symbols=config["stocks"]["symbols"]
    total_inserted,total_skipped=0,0

    for symbol in symbols:
        file_path=os.path.join(sentiment_path,f"{symbol}_sentiment.csv")
        if not os.path.exists(file_path):
            logger.warning(f"[loader][news] Not found: {file_path} — skipping")
            continue

        df=pd.read_csv(file_path)
        inserted,skipped=0,0

        for _,row in df.iterrows():
            date_id=date_map.get(str(row["date"]))
            symbol_id=symbol_map.get(row["symbol"])
            if not date_id or not symbol_id:
                logger.warning(
                    f"[loader][news] No ID for "
                    f"{row['symbol']} {row['date']} — skipping row"
                )
                continue
            cursor.execute("""insert ignore into Fact_News_Articles (symbol_id, date_id, title, link,compound_score, positive_score,negative_score, neutral_score,sentiment_label) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(
                symbol_id,
                date_id,
                str(row["title"])[:500],
                str(row["link"])[:1000],
                float(row["compound_score"]),
                float(row["positive_score"]),
                float(row["negative_score"]),
                float(row["neutral_score"]),
                str(row["sentiment_label"])
            ))

            if cursor.rowcount==1:
                inserted+=1
            else:
                skipped+=1
        
        conn.commit()
        logger.info(
            f"[loader][news][{symbol}] "
            f"inserted: {inserted} | skipped: {skipped}"
        )

        total_inserted+=inserted
        total_skipped+=skipped
    
    cursor.close()
    logger.info(
        f"[loader][news] TOTAL — "
        f"inserted: {total_inserted} | skipped: {total_skipped}"
    )

def main():
    config,base_dir=load_config()
    log_dir=config["paths"]["logs"]
    log_filename=config["logging"]["log_filename"]
    logger=setup_logger(__name__,log_dir,log_filename)

    logger.info("="*60)
    logger.info(f'STARTING LOADER ')
    logger.info("="*60)

    conn=connect_to_database(config,logger)
    
    try:
        logger.info(
            f'STEP 1 — POPULATING DIM_DATE'
        )
        fill_DIM_DATE(conn,config,logger)

        cursor=conn.cursor()
        cursor.execute("select count(*) from DIM_DATE;")
        count=cursor.fetchone()[0]
        logger.info(f"DIM_SYMBOL has {count} rows")

        logger.info("STEP 2 — BUILDING LOOKUP MAPS  ")
        symbol_map=get_symbol_map(conn)
        date_map=get_date_map(conn)

        logger.info(
            f"Maps ready — {len(symbol_map)} SYMBOLS , {len(date_map)} DATES"
        )

        
        logger.info("STEP 3 — LOADING FACT_STOCK_PRICES ")
        load_stock_prices(conn,config,base_dir,symbol_map,date_map,logger)
        
        
        logger.info("STEP 3 — LOADING FACT_NEWS_ARTICLES ")
        load_news_articles(conn,config,base_dir,date_map,symbol_map,logger)

        logger.info("="*60)
        logger.info(
            f"LOADING SUCCESSFULL"
        )
        logger.info("="*60)

    except Exception as e :
        logger.critical(
            f"LOADER CRASHED {type(e).__name__} : {e}"
        )

    finally:
        conn.close()
        logger.info(""
        "MySQL CONNECTION CLOSED")

if __name__=="__main__":
    main()