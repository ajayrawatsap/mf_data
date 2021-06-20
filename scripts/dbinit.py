
"""
This module contains functions that are only run once for inital DB creation
"""

import os
import logging
import pandas as pd
# import mf_data.src.constants as ct
# import src.common.util as ut

from bs4 import BeautifulSoup

DATA_DIR =  'data'
NAV_DIR =   'nav'
GF_NAV_HTML_FILE = 'gf_nav_all.html'
GF_NAV_CSV_FILE = 'gf_nav_all.csv'

def format_mfname(scheme_name:str)->str:
    #Format so that there are no spaces with seperator  '-'    
    return '-'.join([text.strip() for text in scheme_name.split('-')])


def save_gf_navs():
    # From HTML File downloaded from AMFI extract grandfathered NAV for all schemes
    # and save to a csv file with fields scheme_name and gf_nav

    gf_nav_dict = {}
    gf_nav = []
    scheme_name = []
    file_path = os.path.join(DATA_DIR,NAV_DIR, GF_NAV_HTML_FILE) 
    with open(file_path, 'r') as f:
        soup = BeautifulSoup(f, "html.parser")

    #Filter on relevant data
    tags = soup.find_all('tr')
    for tag in tags:
        #The first td tag is MF name and next in NAV value
        if tag.find_all('td'): 
        #   is either MF scheme name or NAV value
            value = tag.find_all('td')[0].get_text()
            try:
                gf_nav.append(float(value))
            except ValueError :
                scheme_name.append(format_mfname(value ))
    gf_nav_dict['scheme_name']  = scheme_name
    gf_nav_dict['gf_nav']  =      gf_nav
    gf_nav_df = pd.DataFrame(gf_nav_dict)

    gf_nav_path = os.path.join(DATA_DIR,NAV_DIR, GF_NAV_CSV_FILE)
    gf_nav_df.to_csv(gf_nav_path , index = False)
    logging.info(f"Generated CSV file {gf_nav_path } for Grandathered NAV for all schemes\n")

if __name__ == "__main__":
    save_gf_navs()