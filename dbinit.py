
"""
This module contains functions that are only run once for inital DB creation
"""


import os
import pandas as pd
import src.constants as ct

import src.utils as ut
# from bs4 import BeautifulSoup
from collections import defaultdict

# https://www.amfiindia.com/nav-history-download

def save_gf_from_text():

    gf_nav_dict = defaultdict(list)
    gf_nav_path_txt = os.path.join(ct.DATA_DIR, ct.NAV_DIR, ct.GF_NAV_INPUT_TXT)  
    gf_nav_file = open(gf_nav_path_txt )

    gf_nav_dict =defaultdict(list)
    gf_nav_list = [ line.rstrip() for line in gf_nav_file]
    gf_nav_file.close()


    for line in gf_nav_list:
        line_split = line.split(';')
        if line_split[0].isnumeric():
            gf_nav_dict['scheme_code'].append(str(line_split[0]))
            gf_nav_dict['scheme_name'].append(line_split[1])
            gf_nav_dict['isin'].append(line_split[2])
            gf_nav_dict['gf_nav'].append(line_split[4])
            gf_nav_dict['gf_nav_date'].append(line_split[7])

    #Save Data in CSV       
    gf_nav_df = pd.DataFrame.from_dict(gf_nav_dict)
    gf_nav_path_csv = os.path.join(ct.DATA_DIR,ct.NAV_DIR, ct.GF_NAV_CSV_FILE)
    gf_nav_df.to_csv(gf_nav_path_csv , index = False)
    print(f"Generated CSV file {gf_nav_path_csv } for Grandathered NAV for all schemes\n")
    return    gf_nav_df


# def save_gf_navs():
#     # From HTML File downloaded from AMFI extract grandfathered NAV for all schemes
#     # and save to a csv file with fields scheme_name and gf_nav

#     gf_nav_dict = {}
#     gf_nav = []
#     scheme_name = []
#     file_path = os.path.join(ct.DATA_DIR, ct.NAV_DIR, ct.GF_NAV_HTML_FILE) 
#     with open(file_path, 'r') as f:
#         soup = BeautifulSoup(f, "html.parser")

#     #Filter on relevant data
#     tags = soup.find_all('tr')
#     for tag in tags:
#         #The first td tag is MF name and next in NAV value
#         if tag.find_all('td'): 
#         #   is either MF scheme name or NAV value
#             value = tag.find_all('td')[0].get_text()
#             try:
#                 gf_nav.append(float(value))
#             except ValueError :
#                 print(value)
#                 scheme_name.append(format_mfname(value ))
#                 print(format_mfname(value ), '\n')
#     gf_nav_dict['scheme_name']  = scheme_name
#     gf_nav_dict['gf_nav']  =      gf_nav
#     gf_nav_df = pd.DataFrame(gf_nav_dict)

#     gf_nav_path = os.path.join(ct.DATA_DIR, ct.NAV_DIR, ct.GF_NAV_CSV_FILE)
#     gf_nav_df.to_csv(gf_nav_path , index = False)
#     logging.info(f"Generated CSV file {gf_nav_path } for Grandathered NAV for all schemes\n")


# https://www.amfiindia.com/net-asset-value/nav-history
#Find NAV for a date and download excel vesrion, save excel as text file


# def save_gf_from_text():
#     file_path = os.path.join(ct.DATA_DIR, ct.NAV_DIR, ct.GF_NAV_INPUT_TXT)
  
#     #Read Text file and create list appending line
#     mf_all_file = open(file_path)
#     mf_all_list = []
#     mf_all_dict =defaultdict(list)
#     mf_all_list = [ line.rstrip() for line in mf_all_file]
#     mf_all_file.close()
    
#     # Create a dict of MF SCheme and GF NAV
#     for i in range(len(mf_all_list)):
#         line_split  = mf_all_list[i].split()
#         try:       
#             gf_nav = float(line_split[0])
#             scheme_name = mf_all_list[i-1]
            
#             scheme_name = ut.rename_mf_scheme(scheme_name)
#             mf_all_dict['scheme_name'].append(scheme_name )
#             mf_all_dict['gf_nav'].append(gf_nav)
#         except ValueError as e:
#             pass

#     #Save Data in CSV
#     mf_all_df = pd.DataFrame.from_dict(mf_all_dict)
#     gf_nav_path = os.path.join(ct.DATA_DIR,ct.NAV_DIR, ct.GF_NAV_CSV_FILE)

#     #Add additinal data in case something is not found in main file
#     missing_gf_nav_file = os.path.join(ct.DATA_DIR, ct.NAV_DIR, ct.GF_MISSING_CSV)  
#     mf_missing_df = pd.read_csv(missing_gf_nav_file)
#     mf_all_df = pd.concat([mf_all_df, mf_missing_df],ignore_index=True, sort=False)


#     mf_all_df.to_csv(gf_nav_path , index = False)
#     print(f"Generated CSV file {gf_nav_path } for Grandathered NAV for all schemes\n")


if __name__ == "__main__":
    save_gf_from_text()