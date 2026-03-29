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