import logging
import os
import src.constants as ct

from src.parsedata import DataParser, PDFParser
from src.initialize import Logger
from src.capitalgains import CapitalGains
import argparse

# def main(file_name:str, display_logs ='yes', target_ltcg:float = 100000.00 ):
def main(display_logs ='no'):
  
    parser = argparse.ArgumentParser()
    parser.add_argument("file_name", help="Name of CAMS PDF file stored in data directory", type = str)
    parser.add_argument("password", help="password for pdf file", type = str)
    parser.add_argument("target_ltcg",  nargs='?',   default = 100000, help="Target LTCG amount that you want tax free:Default INR 100000", type = int )
    args = parser.parse_args()
    
    file_name = args.file_name
    password = args.password
    target_ltcg = args.target_ltcg

    logger = Logger()
    logger.initilaze_logging(display_logs)    

    logging.info(f'{"*" * 50}Start Of Process{"*" * 50}')
    logging.info(f'File Name  {file_name}, Target LTCG is { target_ltcg}')

    dp =PDFParser()
    file_path = os.path.join(ct.DATA_DIR, file_name)
    mf_trans_df, mf_hdr_df = dp.parse_mf_data(file_path, password=password)

 
    cg = CapitalGains(mf_hdr_df, mf_trans_df)
    cg.prepare_final_data(target_ltcg)

    logging.info(f'{"*" * 50}End Of Process{"*" * 50}\n') 

if __name__ == "__main__":
    main()

