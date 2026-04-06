import os 
import sys
import mysql.connector
import pandas as pd
from datetime import datetime , timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_config,load_csv,setup_logger

def connect_to_database(config,logger):
    try:
        conn=mysql.connector.connect(
            host = config["database"]["host"],
            port=config["database"]["port"],
            name=config["database"]["name"],
            user=config["database"]["user"],
            password=config["database"]["password"],
            charset=config["database"]["charset"]
            )
        
        logger.info("mysql connection established")
        return conn
    
    except mysql.connector.error as e :
        f'failed to connect to the database : {e} . '
        f'check credentials in config.json and ensure MySQL is running'
        return None

def fill_DIM_DATE(conn,config,logger):

    cursor=conn.cursor()
    start=datetime.strptime(config["stocks"]["start_date"],"%Y-%m-%d")
    end=datetime.today()
    dates=pd.date_range(start=start,freq="D") 
    
    inserted,skipped=0

    for date in dates:
        is_trading=date.weekday<5

        cursor.execute(""" INSERT IGNORE INTO DIM_DATES (full_date,year,month,day,day_of_week,is_trading_day) VALUES (%s, %s, %s, %s, %s, %s)""",(
            date.strftime("%Y-%m-%d"),
            int(date.year),
            int(date.month),
            int(date.day),
            date.strftime("%A"),
            is_trading
        ))

        if cursor.row_count()==1:
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
    cursor.execure("select symbol,symbol_id from DIM_SYMBOL")
    mapping={row[0]:row[1] for row in cursor.fetchall()}
    conn.close()
    return mapping

def get_date_map(conn):
    cursor=conn.cursor()
    cursor.execute("select full_date,date_id from DIM_DATE")
    mapping={str(row[0]):row[1] for row in cursor.fetchall()}
    conn.close()
    return mapping