import logging
import os
import src.constants as ct

from src.parsedata import DataParser
from src.initialize import Logger
from src.capitalgains import CapitalGains

def main(file_name:str, display_logs ='yes', target_ltcg:float = 100000.00 ):


    logger = Logger()
    logger.initilaze_logging(display_logs)    

    logging.info(f'{"*" * 50}Start Of Process{"*" * 50}')

    dp = DataParser()
    file_path = os.path.join(ct.DATA_DIR, file_name)
    mf_trans_df, mf_hdr_df = dp.parse_mf_data(file_path)

 
    cg = CapitalGains(mf_hdr_df, mf_trans_df)
    cg.prepare_final_data(target_ltcg)

    logging.info(f'{"*" * 50}End Of Process{"*" * 50}\n') 

if __name__ == "__main__":
    main('sample_data.txt')

