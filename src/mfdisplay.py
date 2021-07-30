
import random
import pandas as pd

import src.constants as ct

def format_amount_cols(df:pd.DataFrame, amount_cols:list[str])->pd.DataFrame:
  # Format amounts to  Rupee symbol, comma seperator and 2 decimals
  for col in amount_cols:    
    df[col] = df[col].map('\u20B9{:,.2f}'.format)
  return df

def format_unit_perc_cols(df:pd.DataFrame, columns:list[str])->pd.DataFrame:
  # Format amounts to  Rupee symbol, comma seperator and 2 decimals
  for col in columns:    
    df[col] = df[col].map('{:,.2f}'.format)
  return df

def convert_date_object_to_string(df:pd.DataFrame, columns:list[str])->pd.DataFrame:
    #Since dates are of type datetime.date need to convert to str and then to datetime 
    df[columns] =  df[columns].astype(str).apply(pd.to_datetime, format = ct.DATE_FORMAT_EXT)
    for col in columns:        
      df[col]  = df[col].dt.strftime(ct.DATE_FORMAT)
    return df


def get_hdr_data_to_display(hdr_df_in:pd.DataFrame)->pd.DataFrame:
    hdr_df = hdr_df_in
    hdr_df = hdr_df.drop(columns = ['folio_no', 'isin', 'amc','scheme_code'])


    amount_cols = ['invested_amt', 'ltcg', 'stcg', 'current_amt', 'target_ltcg']
    hdr_df  = format_amount_cols(hdr_df, amount_cols)


    date_cols = ['latest_nav_date']
    hdr_df = convert_date_object_to_string(hdr_df, date_cols)


    unit_perc_cols = ['latest_nav',		'gf_nav',	'units', 'perc_gain',	'target_units']
    hdr_df = format_unit_perc_cols(hdr_df, unit_perc_cols)
    return hdr_df

def get_trans_data_to_display(trans_df_in:pd.DataFrame)->pd.DataFrame:
    trans_df = trans_df_in
    trans_df  = trans_df.drop(columns = ['folio_no', 'isin', 'units_balance', 'amc','scheme_code'])


    amount_cols = ['invested_amt', 'ltcg', 'stcg', 'cumil_ltcg', 'current_amt']
    trans_df  = format_amount_cols(trans_df, amount_cols)

    date_cols = ['trans_date', 'latest_nav_date']
    trans_df = convert_date_object_to_string(trans_df, date_cols)

    unit_perc_cols = ['latest_nav',		'gf_nav', 'new_purch_nav', 'units', 'purch_nav', 'perc_gain', 'cumil_units']
    trans_df = format_unit_perc_cols(trans_df, unit_perc_cols)
    return trans_df

def get_trans_for_single_scheme(trans_df:pd.DataFrame, scheme_name:str = None)->pd.DataFrame:
    if not scheme_name:
        schemes = list(set(trans_df.scheme_name.to_list()))
        random_idx= random.randint(0, len(schemes)-1)
        scheme_name = schemes[random_idx]    
    
    return trans_df[trans_df.scheme_name == scheme_name]
