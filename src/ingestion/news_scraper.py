import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_config, setup_logger

config , base_dir= load_config()

def build_rss_url(symbol,config):
    base_url=config["news"]["rss_base_url"]
    rss_params=config["news"]["rss_params"]

    full_url= f"{base_url}?s={symbol}&{rss_params}"

    return full_url


def fetch_rss_feed(url,symbol,logger):
    try:
        logger.info(f"Fetching RSS feed for {symbol} — {url}")

        response=requests.get(url,
                              timeout=10, # this is the time for which the request waits before sending timeout error
                              headers={"User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                    )
            }
        )
        if response.status_code==200:
            logger.info(f"RSS feed fetched successfully for {symbol}")
            return response.text
        elif response.status_code==429:
            logger.error(f'rate limited by Yahoo for {symbol}'
                         f'try increasing the timeout')
            return None
        else :
            logger.error(
                f'HTTP {response.status_code} recieved for {symbol}'
                f"URL : {url}"
            )
            return None
        
    except requests.exceptions.ConnectionError:
        logger.error(
            f'Connection failed for {symbol}'
            f'Check your internet connection'
        )
        return None
    except requests.exceptions.Timeout:
        logger.error(
            f'Request timed out for {symbol} after 10 seconds'
        ) 
        return None
    except Exception as e :
        logger.error(
            f'unexpected error for {symbol} while fetching'
            f'{type(e).__name__} : {e}' 
        )
        return None
    
def parse_rss_feed(xml_feed,logger,symbol,max_articles):
    try:    
        soup=BeautifulSoup(xml_feed,"lxml-xml")
        items=soup.find_all("item")

        if not items:
            logger.warning(f'no <item> tags found for {symbol}'
                           f'feed structure might have change')
        
        logger.info(f'found {len(items)} articles for {symbol}')

        articles=[]

        for item in items[:max_articles]:

            title=item.find("title")
            title=title.get_text(strip=True) if title else None

            description=item.find("description")
            description=description.get_text(strip=True) if description else None

            link=item.find("link")
            link=link.get_text(strip=True) if link else None

            pub_date=item.find("date")
            pub_date=pub_date.get_text(strip=True) if pub_date else None

            if not title :
                logger.warning(
                    f'skipping article with no title for {symbol}'
                )
                continue
            cleaned_pub_date=clean_pub_date(pub_date,logger)

            articles.append({"title":title,
                             "description":description,
                             "link":link,
                             "date":cleaned_pub_date,
                             "symbol":symbol,
                             "raw_date":pub_date
                             })
            
        logger.info(
            f'successfully parsed {len(articles)} for {symbol}'
        )

        return articles
    
    except Exception as e :
        logger.error(
            f'unable to parse XML for {symbol} : {type(e).__name__}'
        )

        return []
    

def clean_pub_date(pub_date_str,logger):
    if not pub_date_str :
        return None
    
    try:
        cleaned=pd.to_datetime(pub_date_str,
                               format  = "%a, %d %b %Y %H:%M:%S %z",
                               utc = True).strftime("%Y-%m-%d")
        return cleaned
    
    except Exception :
        try :
            cleaned = pd.to_datetime(pub_date_str).strftime("%Y-%m-%d")
            return cleaned
        except Exception :
            logger.warning(f'could not parse date : {pub_date_str} saving as None ')
            return None
        
def save_news_data(articles,raw_news_path,symbol,logger):
    if not articles:
        logger.warning(f'no articles found for {symbol}')
        return None
    
    os.makedirs(raw_news_path,exist_ok=True)

    df=pd.DataFrame(articles)
    file_name=f'{symbol}_news_raw.csv'
    file_path=os.path.join(raw_news_path,file_name)

    try:
        df.to_csv(file_path,index=False,encoding='utf-8')
        logger.info(f'saved {len(df)} articles to {raw_news_path} SUCCESSFULLY')
        return True
    
    except PermissionError as e :
        logger.error(
            f'cannot write to {file_name} , file may be open somewhere else'
        )
        return None

    except Exception as e:
        logger.error(
            f'an unexpected error occured for {symbol}' 
            f'{type(e).__name__} : {e}'
        )
        return None

def main():
    config,base_dir=load_config()
    log_dir=os.path.join(base_dir,config["paths"]["logs"])
    log_file_name=config["logging"]["log_filename"]
    raw_news_path=os.path.join(base_dir,config["paths"]["raw_news"])

    logger=setup_logger(__name__,log_dir=log_dir,log_filename=log_file_name)

    logger.info("="*60)
    logger.info(f'NEWS SCRAPER - STARTING')
    logger.info("="*60)

    symbols=config["stocks"]["symbols"]
    max_articles=config["news"]["max_articles_per_symbol"]
    delay=config["news"]["request_delay_seconds"]

    successful,failed=[],[]

    for symbol in symbols:
        logger.info(f"── Processing {symbol} ──")
        url=build_rss_url(symbol,config)
        xml_text=fetch_rss_feed(url,symbol,logger)

        if xml_text is None:
            failed.append(symbol)
            continue

        articles=parse_rss_feed(xml_text,logger,symbol,max_articles)

        if not articles:
            failed.append(symbol)
            continue

        """not articles: checks if the article is an empty list 
        whereas xml_text is None: checks if it is "None" 
        if an empty string was passed , it would returned false"""

        saved=save_news_data(articles,raw_news_path,symbol,logger)

        if saved:
            successful.append(symbol)
        else:
            failed.append(symbol)
        
        if symbol!=symbols[-1]:
            logger.info(
                f'waiting {delay}s before next request..'
            )
            time.sleep(delay)

    logger.info("="*60)
        
    if len(failed)==0:
        logger.info(
            f'COMPLETE — ALL {len(failed)} SYMBOLS SCRAPED SUCCESSFULLY'
        )        
        
    elif len(successful)==0:
            logger.critical(
            f'FAILED — FAILED TO SCRAPE ALL {len(failed)}'
            f'check internet or feed URL'
        )  
             
    else:
        logger.warning(
            f'FAILED TO SCRAPE {len(failed)} ARTICLLES : {failed}'
            f'{len(successful)} ARTICLES WERE SCRAPED SUCCESSFULLY : {successful}'
        )

    logger.info("="*60)

if __name__=="__main__":
    main()

    