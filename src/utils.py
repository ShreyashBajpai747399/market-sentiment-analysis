import os 
import logging
import json

def load_config():
    #base dir is the path of the root directory
    base_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    #config_path is the path of the config file present in root
    config_path=os.path.join(base_dir,'config.json')

    with open(config_path,'r') as f:
        config=json.load(f)

    return config , base_dir

def setup_logger(logger_name,log_dir,log_filename):
    #making a directory with name log_dir to store the logs if it exists , ignore
    os.makedirs(log_dir,exist_ok=True)
    
    #making the path of the log file , where it will be saved
    log_path=os.path.join(log_dir,log_filename)
    
    #creating the logge
    logger=logging.getLogger(logger_name)

    #this checks if the handler for the logger already exist , if they do , it returns true and no new loggers are created 
    if logger.handlers:
        return logger
    #there will never be a case when duplicate loggers are called as we are using __name__ for the logger name , the only case would be calling the logger in the same script twice 
    
    logger.setLevel(logging.INFO)

    formatter=logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(module)s | %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S"
    )

    #the file handler writes to the log file hence the path is given 
    file_handler=logging.FileHandler(log_path,encoding="utf-8")
    file_handler.setFormatter(formatter)

    #the console handler writes to the terminal hence no path needed
    console_handler=logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


    return logger










