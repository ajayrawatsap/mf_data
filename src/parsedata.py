
from __future__ import annotations

import re
import logging
import pandas as pd
import casparser
import src.constants as ct
import src.utils as ut

from typing import Iterator
from collections import defaultdict
from  datetime import datetime
from src.utils import is_valid_date




class PDFParser:
    def __init__(self):
        pass
    
    def parse_mf_data(self,file_path:str, password:str = '')->tuple[pd.DataFrame,pd.DataFrame]: 
        # data in nested dictionary form  
        mf_data = casparser.read_cas_pdf(file_path, password )   

        mf_trans_dict = defaultdict(list)
        mf_hdr_df    = defaultdict(list)
        # Each folio is a list item for each folio
        for folio in  mf_data['folios']:
            
            #Scheme Header level Information in list folio['schemes']:
            for scheme in folio['schemes']:

                #Exclude Portfolio without any meaninful data:e.g. segregated portfolio
                if scheme['isin'] is None:
                    continue
                
                # AMC Level Data
                mf_hdr_df['amc'].append(folio['amc'])
                mf_hdr_df['folio_no'].append(folio['folio'])
                
                #Scheme Level Data
                mf_hdr_df['scheme_name'].append(scheme['scheme'])
                mf_hdr_df['isin'].append(scheme['isin'])
                mf_hdr_df['scheme_code'].append(scheme['amfi'])
                mf_hdr_df['latest_nav'].append(scheme['valuation']['nav'])
                mf_hdr_df['latest_nav_date'].append(scheme['valuation']['date'])
                
                # Scheme Transaction level information
                for trans in scheme['transactions']:         
                    
                
                    mf_trans_dict['scheme_name'].append(scheme['scheme'])              
                    mf_trans_dict['trans_date'].append(trans['date'])
                    mf_trans_dict['amount'].append(trans['amount'])
                    mf_trans_dict['units'].append(trans['units'])
                    mf_trans_dict['purch_nav'].append(trans['nav'])
                    mf_trans_dict['nav_balance'].append(trans['balance'])
                    mf_trans_dict['trans_type'].append(trans['type'])

        mf_hdr_df = pd.DataFrame.from_dict(mf_hdr_df)
        mf_trans_df = pd.DataFrame.from_dict(mf_trans_dict)
        mf_trans_df = mf_trans_df[mf_trans_df.trans_type != 'STAMP_DUTY_TAX']
        logging.debug(f'Number of Mutual Funds Scheme: {mf_hdr_df.shape[0]}\n')

        return  mf_trans_df, mf_hdr_df




class DataParser:
    def __init__(self):
        pass
    def _read_data_from_file(self,file_path:str)->list[str]:
        file_mf = open(file_path)
        #remove new line character at end
        mf_data_list = [ line.rstrip() for line in file_mf ]
        file_mf.close()

        logging.info(f'File {file_path} sucessfully read, found { len( mf_data_list)} records\n')
        return mf_data_list

    def _generate_batch(self, mf_data_list:list[str] )->Iterator[list[str]]:
        """
        yeild batches for data corresponding to a single Mutual Fund    
        A MF transaction will start with keyword PAN, hence create a batch of
        data between two instances of keyword 'PAN'
        """
        for i, _ in enumerate(mf_data_list):
         if mf_data_list[i].startswith('PAN'):
           first_idx = i
           break

        for i in range(first_idx+1, len(mf_data_list)):
            if mf_data_list[i].startswith('PAN'):
                yield mf_data_list[first_idx:i+1]
                first_idx = i

        # For last batch
        yield mf_data_list[first_idx:]

    def _get_latest_nav(self, line:str)->tuple[float, datetime]:
        line = line.replace(':', '').replace(',', '')  
        latest_nav_data = line.split()
        latest_nav_date = latest_nav_data[2]
        latest_nav_date = datetime.strptime(latest_nav_date, ct.DATE_FORMAT)
        latest_nav = float(latest_nav_data[4])
        return  latest_nav,   latest_nav_date

    def _get_numerical_data(self,line:str)->tuple[float, float, float]:
        nums = line.split()[-4:]
        nums= [value.replace(',', '') for value in nums]
        # all(isinstance(x,float) for x in amt ), amt
        try:
            nums= [float(value) for value in nums]
        except ValueError:
            raise ValueError(f'Invalid data in {nums} while parsing numerical data')
        amount = nums[0]
        
        units  = nums[1]
        purch_nav=  nums[2]
        return amount, units, purch_nav

    def _parse_mf_scheme_name(self,mf_data:list[str])->str:  

        #MF scheme name can be split in multiple lines.
        scheme_name = ''
        for text in mf_data[1:]:
            if text[:5] != 'Folio':
                scheme_name = scheme_name + text
            else:
                break
    

        #Remove brackets and texts inside brackets
        # Input: 'D788-DSP Small Cap Fund - Direct Plan - Growth (formerly DSP Micro Cap Fund)(Advisor: DIRECT) Registrar : CAMS'	
        # Output:'D788-DSP Small Cap Fund - Direct Plan - Growth Registrar : CAMS'
        scheme_name= re.sub(r'\(.*?\)\ *', '', scheme_name)

        # input : 'D788-DSP Small Cap Fund - Direct Plan - Growth Registrar : CAMS'
        # output: 'D788-DSP Small Cap Fund - Direct Plan - Growth'
        scheme_name = scheme_name.split('Registrar')[0].strip()

        # input: 'D788-DSP Small Cap Fund - Direct Plan - Growth'
        # output:'DSP Small Cap Fund-Direct Plan-Growth'
        scheme_name =  '-'.join([text.strip() for text in scheme_name.split('-')[1:]])     

        #Convert GROWTH to Camelcase (Growth)
        # input :'4859909139674 Franklin India Ultra Short Bond Fund Super Institutional Plan-Direct-GROWTH'
        # output: '4859909139674 Franklin India Ultra Short Bond Fund Super Institutional Plan-Direct-Growth'
        # scheme_words = scheme_name.split('-')
        # scheme_words[-1] = scheme_words[-1].title()
        
        # input:'Mirae Asset Tax Saver Fund-Direct Growth'
        # output:'Mirae Asset Tax Saver Fund-Direct-Growth'
        # if scheme_words[-1] == 'Direct Growth':
        #     scheme_words[-1] = 'Direct-Growth'
        # scheme_name = '-'.join([text for text in  scheme_words])     

        #Remove leading digits for funds like Franklin
        # input:'4859909139674 Franklin India Ultra Short Bond Fund Super Institutional Plan-Direct-Growth'
        # output: 'Franklin India Ultra Short Bond Fund Super Institutional Plan-Direct-Growth'
        if scheme_name .split()[0].isnumeric():
            scheme_name = ' '.join([text for text in scheme_name .split()[1:]])
        
        #Remove Spaces, and simplify MF Option and Plan names
        scheme_name = ut.rename_mf_scheme(scheme_name)
        return scheme_name  

    def parse_mf_data(self,file_path:str)->tuple[pd.DataFrame,pd.DataFrame]:
        '''
        Read the text file having MF tranactions from CAMS+FTAMIL
        Generate Batches for single MF scheme and parse MF data
        Transaction data and Latest NAV will be parsed from text file
        '''
        mf_data_dict =defaultdict(list)
        mf_nav_dict =defaultdict(list)

        mf_data_list = self._read_data_from_file(file_path)

        # loop over a batch having data for single MF Scheme
        for mf_data in self._generate_batch(mf_data_list):
            
            mf_scheme = self._parse_mf_scheme_name(mf_data)
            logging.debug(f'Parsing data for MF {mf_scheme}')
            
            for line in mf_data:
                date_text = line[:11]

                #only process lines which start with date
                if is_valid_date(date_text,  ct.DATE_FORMAT ):
                
                    try:
                        amount, units, purch_nav = self._get_numerical_data(line)                
                    except ValueError:
                        continue
                    else:                  
                        mf_data_dict['scheme_name'].append(mf_scheme) 
                        trans_date = datetime.strptime(date_text, ct.DATE_FORMAT)
                        mf_data_dict['trans_date'].append(trans_date)
                        mf_data_dict['amount'].append(amount)
                        mf_data_dict['units'].append(units)
                        mf_data_dict['purch_nav'].append(purch_nav)

                #Latest Nav and Date in separate dict      
                if line[:6] == 'NAV on':        
                    latest_nav, latest_nav_date =   self._get_latest_nav(line)

                    #For segregated Portfolios the NAV will be zero, we will ignore them
                    if latest_nav != 0:
                        mf_nav_dict['scheme_name'].append(mf_scheme)
                        mf_nav_dict['latest_nav'].append(latest_nav)
                        mf_nav_dict['latest_nav_date'].append(latest_nav_date)
                        logging.debug(f'Latest Nav:{latest_nav}, Nav Date:{latest_nav}')
                    else:
                        logging.debug(f'Latest Nav:{latest_nav}, MF Scheme{mf_scheme} will be ignored')


        mf_trans_df = pd.DataFrame.from_dict(mf_data_dict)       
        mf_hdr_df = pd.DataFrame.from_dict(mf_nav_dict)
        logging.debug(f'Number of Mutual Funds Scheme: {mf_hdr_df.shape[0]}\n')
        return  mf_trans_df, mf_hdr_df