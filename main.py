import os
import sys
import logging
from datetime import datetime
import subprocess   

base_dir=os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_dir,"src"))

from utils import setup_logger,load_config,ensure_dirs

def run_python_step(step_name,script_path,logger):
    logger.info(f"STARTING : {step_name}")

    try:
        subprocess.run([sys.executable,script_path],check=True)
        logger.info(f"COMPLETED : {step_name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FAILED : {step_name}")
        logger.error(f"ERROR : {e}")
        sys.exit(1)

def run_sql_step(step_name,sql_file,config,logger):
    logger.info(f"STARTING : {step_name}")

    db=config["database"]

    command=(
        f'mysql -u {db["user"]} -p"{db["password"]}" '
        f'-h {db["host"]} -P {db["port"]} '
        f'{db["name"]} < "{sql_file}"'
    )

    try:
        subprocess.run(command,shell=True,check=True)
        logger.info(f"COMPLETED : {step_name}")
    
    except subprocess.CalledProcessError as e :
        logger.error(f"FAILED : {step_name}")
        logger.error(f"ERROR : {e}")
        sys.exit(1)

def main():
    config,base_dir=load_config()   
    ensure_dirs(base_dir,config["paths"])

    log_dir=os.path.join(base_dir,config["paths"]["logs"])
    log_filename=f"pipeline_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"

    logger=setup_logger("pipeline",log_dir,log_filename)

    logger.info("="*60)
    logger.info("PIPELINE STARTED")
    logger.info("="*60)

    steps=[
        ("Stock Data Downloader","src/ingestion/stock_downloader.py"),
        ("News Articles Downloader","src/ingestion/news_scraper.py"),
        ("Data Validation","src/validation/validator.py"),
        ("Data Cleaning","src/cleaning/cleaner.py"),
        ("Sentiment Scoring","src/sentiment/scorer.py"),
        ("Load to MySQL" ,"src/database/loader.py" )
    ]

    for step_name,script in steps:
        script_path=os.path.join(base_dir,script)
        run_python_step(step_name,script_path,logger)
    
    logger.info("="*60)
    logger.info("PYTHON PIPELINE COMPLETED")
    logger.info("="*60)

    sql_steps=[
        ("Populate Derived Tables","sql/populate_derived.sql"),
        ("Create SQL Views","sql/views.sql")
    ]
    for step_name , script in sql_steps:
        sql_path=os.path.join(base_dir,script)
        run_sql_step(step_name,sql_path,config,logger)

    logger.info("="*60)
    logger.info("SQL PIPELINE COMPLETED")
    logger.info("="*60)

if __name__=="__main__":
    main()