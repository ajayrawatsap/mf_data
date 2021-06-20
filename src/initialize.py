
import os
import logging
import sys
import src.constants as ct


class Logger:
    def __init__(self):        
          pass
    def initilaze_logging(self, display_logs = 'yes'):
  
    
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # create file handler for writing to file 
        log_file_path = os.path.join(ct.DATA_DIR, ct.LOGGING_FILE_NAME)
        file_handler = logging.FileHandler( log_file_path)
        file_handler.setLevel(logging.DEBUG)   

        # create console handler to print logs on console
        # If logging is disabled in config only showw CRITICAL logs
        log_level = logging.CRITICAL   
        if display_logs.lower() == 'yes': log_level = logging.INFO      
        console_handler = logging.StreamHandler(stream = sys.stdout)
        console_handler.setLevel(log_level)

        # create formatter and add it to the handlers       
        formatter = logging.Formatter('[%(asctime)s %(levelname)s %(module)s - %(funcName)s:] %(message)s')
        file_handler.setFormatter(formatter)

        # For  console handler use different formatting ooptions
        formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(formatter)

        # add the handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
