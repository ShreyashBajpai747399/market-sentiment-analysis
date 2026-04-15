import pandas as pd
import os
import sys
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_config , load_csv , setup_logger

#creating the analyser (could've been skipped but if we want to create the analyser in any other file then we can use this)
def get_analyser():
    return SentimentIntensityAnalyzer()

def score_text(text,analyser):
    if not isinstance(text,str) or text.strip()=="":
        return {
            "compound":0.0,
            "pos":0.0,
            "neg":0.0,
            "neu":1.0
        }
    scores=analyser.polarity_scores(text)
    return scores

def get_sentiment_label(compound_score,config):
    positive_threshold=config["sentiment"]["positive_threshold"]
    negative_threshold=config["sentiment"]["negative_threshold"]

    if compound_score>=positive_threshold:
        return "POSITIVE"
    elif compound_score<=negative_threshold:
        return "NEGATIVE"
    else:
        return "NEUTRAL"
    
def score_news_file(symbol,processed_news_path,sentiment_path,analyser,config,logger):

    file_path=os.path.join(processed_news_path,f'{symbol}_news_processed.csv')
    df=load_csv(filepath=file_path,logger=logger)

    
    if df is None:
        logger.error(
            f"[sentiment][{symbol}] Could not load news file — skipping"
        )
        return False
    
    df["link"] = df["link"].str.strip().str.split("?").str[0]
    
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    output_path=os.path.join(sentiment_path,f"{symbol}_sentiment.csv")
    if os.path.exists(output_path):
        existing_df=pd.read_csv(output_path)
        existing_df["link"] = existing_df["link"].str.strip().str.split("?").str[0]
        already_scored=set(existing_df["link"].str.strip())
        df=df[~df["link"].str.strip().isin(already_scored)]  
    
    if df.empty:
        logger.warning(
            f'[sentiment] {symbol} no new articles to score '
        )
        return True
    logger.info(
        f'[sentiment] {symbol} scoring {len(df)} articles'
    )

    if "text" in df.columns:
        score_col="text"
        logger.info(
            f"[sentiment][{symbol}] Using 'text' column for scoring"
        )
    elif "title" in df.columns:
        score_col="title"
        logger.warning(
            f"[sentiment][{symbol}] 'text' columns not found"  
            f"Using 'title' column for scoring"
        )
    else:
        logger.error(
            f"[sentiment][{symbol}] Neither 'text' nor 'title' "
            f"column found — cannot score"
        )
        return False

    scores_list=df[score_col].apply(score_text,analyser=analyser)

    scores_df=pd.DataFrame(scores_list.tolist())

    scores_df=scores_df.rename(
        columns={
            "compound":"compound_score",
            "pos":"positive_score",
            "neg":"negative_score",
            "neu":"neutral_score"   
        }
    )

    scores_df["sentiment_label"]=scores_df["compound_score"].apply(
        lambda score:get_sentiment_label(score,config)
    )
    df=pd.concat([df.reset_index(drop=True),scores_df.reset_index(drop=True)],axis=1)
    label_counts=df["sentiment_label"].value_counts()
    logger.info(
        f"[sentiment][{symbol}] Distribution — "
        f"POSITIVE: {label_counts.get('POSITIVE', 0)} | "
        f"NEGATIVE: {label_counts.get('NEGATIVE', 0)} | "
        f"NEUTRAL: {label_counts.get('NEUTRAL', 0)}"
    )

    
    cols_to_drop = ["text", "description"]
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
    
    df["symbol"]=symbol

    desired = [
    "date",
    "symbol",
    "title",
    "link",
    "compound_score",
    "positive_score",
    "negative_score",
    "neutral_score",
    "sentiment_label"
    ]
    
    df=df[[c for c in desired if c in df.columns]]

    os.makedirs(sentiment_path,exist_ok=True)
    try:
        file_exists = os.path.exists(output_path)
        df.to_csv(output_path, index=False,mode="a",header=not file_exists )
        logger.info(
            f"[sentiment][{symbol}] Saved {len(df)} scored rows "
            f"→ {output_path}"
        )
        return True
    except Exception as e :
        logger.error(
            f'[sentiment] {symbol} failed to save :'
            f'{type(e).__name__} : {e}'
        )
        return False

def main():
    config,base_dir=load_config()
    processed_news_path=os.path.join(base_dir,config["paths"]["processed_news"])
    sentiment_path=os.path.join(base_dir,config["paths"]["sentiment"])
    symbols=config["stocks"]["symbols"]
    logger=logging.getLogger(__name__)


    logger.info("="*60)
    logger.info("STARTING SENTIMENT ANALYSER")
    logger.info("="*60)

    analyser=get_analyser()
    logger.info(
        f'VADER ANALYSER INITIALISED'
    )

    successful,failed=[],[]

    for symbol in symbols:
        logger.info(f'SCORING {symbol}')
        try:
            saved = score_news_file(symbol,processed_news_path,sentiment_path,analyser,config,logger)
            if saved:
                successful.append(symbol)
            else:
                failed.append(symbol)
        
        except Exception as e :
            logger.error(
                f'[sentiment] {symbol} crashed. '
                f'{type(e).__name__} : {e}'
            )
            failed.append(symbol)
    
    if failed==[]:
        logger.info(f"ALL SYMBOLS SCORED SUCCESSFULLY : {successful}")
    elif successful==[]:
        logger.error(
            f"FAILED TO SCORE ALL {len(symbols)} SYMBOLS : {failed}"
        )
    else:
        logger.warning(
            f'FAILED TO SCORE {len(failed)}  SYMBOLS : {failed} | '
            f'{len(successful)} SYMBOLS SCORED SUCCESSFULLY : {successful}'
        )
    logger.info("="*60)

if __name__=="__main__":
    main()