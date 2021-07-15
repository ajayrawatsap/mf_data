from __future__ import annotations

import os
import logging
import pandas as pd
import src.constants as ct


from datetime import datetime
from collections import defaultdict
from decimal import Decimal
from dateutil.relativedelta import relativedelta

class CapitalGains:
    def  __init__(self, mf_hdr_df:pd.DataFrame, mf_trans_df:pd.DataFrame):   
        self.mf_hdr_df = mf_hdr_df
        self.mf_trans_df = mf_trans_df
        self.output_hdr_df = pd.DataFrame
        self.output_trans_df = pd.DataFrame

        self._set_gf_nav()
        self._calculate_capital_gains()

    def _set_gf_nav(self):

        def decimal_from_value(value:float)->Decimal:
            return Decimal(value)
        logging.debug(f"Setting Grandfathered NAV for all Schemes for NAV date 18-JAN-2018")

        #Set GF Nav on MF Header Data
        gf_nav_df = pd.read_csv(  os.path.join(ct.DATA_DIR, ct.NAV_DIR, ct.GF_NAV_CSV_FILE),
                                  converters= {'gf_nav': decimal_from_value} )
        # self.mf_hdr_df = pd.merge( self.mf_hdr_df, gf_nav_df, on ='scheme_name', how = 'left')\
        gf_nav_df = gf_nav_df[['scheme_code', 'gf_nav']]
        gf_nav_df['scheme_code'] = gf_nav_df['scheme_code'].astype(str)
        self.mf_hdr_df = pd.merge( self.mf_hdr_df, gf_nav_df, on ='scheme_code', how = 'left')

        #MF Schemes for which GF Nav was not found
        mf_gf_nav_null =   self.mf_hdr_df[self.mf_hdr_df.gf_nav.isnull()].scheme_name.value_counts().index.to_list()

        #Remove transactions for which GF nav is not found
        # self.mf_hdr_df =  self.mf_hdr_df.dropna(subset = ['gf_nav'])

        #Join Transactional and Header data to capture NAV data (Latest naV, GF Nav etc)
        self.mf_trans_df = pd.merge(self.mf_trans_df, self.mf_hdr_df, on ='scheme_name', how = 'inner' )

        #Log the Schemes for which GF NAV is missing
        if len(mf_gf_nav_null) > 0:
            logging.warning(f"For Schemes below Grandfathered NAV was not Found")
            for scheme in mf_gf_nav_null:
                logging.warning(scheme)

    def _get_stcg_ltcg(self,trans_date:datetime,latest_nav:float, latest_nav_date:datetime,
                 new_purh_nav:float, units:float )->tuple[float, float ]:
        ltcg =  0
        stcg =  0
        date_one_year_ago  = latest_nav_date - relativedelta(years=1)
        capital_gains = (latest_nav - new_purh_nav) * units

        #Transaction date is  earlier than a year ago, gains are STCG
        if trans_date >= date_one_year_ago:
            stcg =  capital_gains     
        #Transaction date is later than a than a year ago, gains are LTCG
        elif trans_date < date_one_year_ago:
            ltcg = capital_gains
        return ltcg, stcg

    def _get_new_purch_nav(self,trans_date: datetime, price:float,  gf_nav:float ) -> float:
        '''
        #Return the New Purchase NAV based on transaction date
        for transaction earlier than 31-JAN-2018, the new purchase NAV is max of gf_nav or 
        for transaction later than 31-JAN-2018, the new purchase NAV is same as purchase nav
        '''
        if trans_date <= pd.to_datetime(ct.GF_NAV_DATE, format= ct.DATE_FORMAT):
            return max(gf_nav,price )
        elif trans_date > pd.to_datetime(ct.GF_NAV_DATE, format= ct.DATE_FORMAT):
            return price    

    def _calculate_capital_gains(self):
        '''        
        Set New purchase price based on transaction date 
        Calculate LTCG and STCG based on transaction date

        '''

      
        #Check if there is any row with missing value
        null_idx = self.mf_trans_df.index[self.mf_trans_df.isna().any(axis =1)].tolist()
        if len(null_idx) > 0:
            logging.warning(f"{len(null_idx)} rows are missing values for one or more columns.")
        else:
            logging.info(f"No Missing data Found:" )


        #if transaction date is before Jan-2018 use grand fathered NAV else use current NAV for calculating capital gains
        self.mf_trans_df['new_purch_nav'] = self.mf_trans_df.apply(lambda x: 
                                                                   self._get_new_purch_nav(x.trans_date, 
                                                                                           x.purch_nav, 
                                                                                           x.gf_nav ), 
                                                                    axis = 1)

        #Calculate the STCG or LTCG using New Purchase NAV per transaction
        self.mf_trans_df[['ltcg', 'stcg']] = self.mf_trans_df.apply(lambda x:  
                                                                    self._get_stcg_ltcg( x.trans_date,
                                                                                         x.latest_nav,
                                                                                         x.latest_nav_date,
                                                                                         x.new_purch_nav,                                                      
                                                                                         x.units ) ,
                                                                    axis = 1, 
                                                                    result_type= 'expand')

        #Set Cumiltaive sum of LTCG and Units for each MF scheme
        self.mf_trans_df['cumil_ltcg'] = self.mf_trans_df.groupby('scheme_name')['ltcg'].transform(pd.Series.cumsum)
        self.mf_trans_df['cumil_units'] = self.mf_trans_df.groupby('scheme_name')['units'].transform(pd.Series.cumsum)                                                            

        #Latest Amount and Percent Gain
        self.mf_trans_df['current_amt'] = self.mf_trans_df.units * self.mf_trans_df.latest_nav
        self.mf_trans_df['perc_gain'] =   ((self.mf_trans_df['current_amt'] - self.mf_trans_df['amount']) /  self.mf_trans_df['amount']) * 100

        #Round to 2 decimals
        # cols_to_round = ['perc_gain','current_amt','ltcg', 'stcg', 'cumil_ltcg', 'cumil_units']
        # self.mf_trans_df[cols_to_round] = self.mf_trans_df[cols_to_round].round(2)   
   

    def if_gf_nav_ok(self, mf_trans_single_df:pd.DataFrame)->bool:
        '''
            In case GF NAV not required because Transaction was done after date 31-Jan-2018  then gf nav is not required: 
            If there exists transaction before cut off date then gf nav  is required
        '''
        # create a dataframe of trasnactions on or before cut off date of 31-Jan-2018
        gf_cut_off_date = datetime.strptime(ct.GF_NAV_DATE, ct.DATE_FORMAT).date()
        mf_trans_before_31_jan_2018 = mf_trans_single_df[mf_trans_single_df.trans_date <= gf_cut_off_date ]
        
        # if there exists trasnactions before cut off date GF NAV is required
        if mf_trans_before_31_jan_2018.shape[0] > 0:
            # If the sum of new purchase is 0 it means no GrandFathered NAV was found
            gf_nav_sum = mf_trans_before_31_jan_2018.gf_nav.sum()
            if  gf_nav_sum == 0:
                return False
        
        return True

    def calc_units_to_sell(self,scheme_name:str, target_ltcg:float = 100000)->tuple[float, float,str]:
        '''
        Calculate cumilative LTCG and units for a single MF scheme
        Use it to claculate the traget units based on input target LTCG    
        '''
        
        ltcg_amt, units_to_sell = 0, 0 
        mf_trans_single_df = self.mf_trans_df[self.mf_trans_df.scheme_name == scheme_name ]    
       
       
        # if transaction exists before  31-Jan-2018 but no GF nav found, no claculation is possible
        if not self.if_gf_nav_ok( mf_trans_single_df ):
            logging.warning(f'For Scheme {scheme_name}: Transaction prior to 31-Jan-2018 exist but no GrandFathered NAV found')  
            gf_nav_file_name = os.path.join(ct.DATA_DIR, ct.NAV_DIR, ct.GF_NAV_CSV_FILE)
            msg  =  (  f'Transactions prior to 31-Jan-2018 exist but no GrandFathered NAV found:' 
                       f'Manualy Maintain the NAV for  date 31-Jan-2018 in file {gf_nav_file_name }' )
            return 0, 0, msg



        mf_trans_single_df = mf_trans_single_df[mf_trans_single_df.ltcg > 0]
        num_rows = mf_trans_single_df.shape[0]
        # No LTCG found return zero
        if  num_rows == 0:  
            logging.info(f'For Scheme {scheme_name} No LTCG exists hence calculation is not applicable')  
            msg  =  f'No LTCG exists hence calculation is not applicable'   
            return 0, 0, msg

        # Boundray Condition. If the Total Cumlative LTCG(last Transation) is less than Target LTCG return all units
        if mf_trans_single_df.iloc[-1].cumil_ltcg < target_ltcg:  
            units_to_sell = mf_trans_single_df.iloc[-1].cumil_units
            ltcg_amt = mf_trans_single_df.iloc[-1].cumil_ltcg
            logging.info(f'For Scheme {scheme_name} Total LTCG {ltcg_amt: .3f} is less than target LTCG {target_ltcg}: Sell {units_to_sell:.2f} units for LTCG of {ltcg_amt: .3f}') 
            msg = f'Total LTCG {ltcg_amt: .3f} is less than target LTCG {target_ltcg}: Sell {units_to_sell:.3f} units for LTCG of {ltcg_amt: .3f}'
            return ltcg_amt, units_to_sell, msg
        # Calculate using cumilative data
        for i in range(0, num_rows):      
            
                row = mf_trans_single_df.iloc[i]
                
                if row.cumil_ltcg >= target_ltcg:        
                # first trasnaction LTCG is greater than Target LTCG use first trsnastion dataa
                    if i == 0:
                        prev_row = row
                    else:
                        prev_row =     mf_trans_single_df.iloc[i-1]
                    
                    # Consume partial delta units from thershold transaction
                    delta_ltcg =   target_ltcg - prev_row.cumil_ltcg
                    delta_units=  delta_ltcg / (row.latest_nav - row.new_purch_nav	)	
                    units_to_sell =   delta_units + prev_row.cumil_units
                    ltcg_amt =  prev_row.cumil_ltcg +    delta_units *(row.latest_nav - row.new_purch_nav)     
                    logging.info(f'For Scheme {scheme_name}: Sell {units_to_sell:.3f} units for LTCG of {ltcg_amt: .3f}')  
                    msg =   f'Sell {units_to_sell:.3f} units for LTCG of {ltcg_amt: .3f}'
                    return ltcg_amt, round(units_to_sell, 3), msg
    
    def prepare_final_data(self,target_ltcg:float)->None:
        '''
        This is main method and can be called afte setting the data in constrcutor
        Calculates the Target Units to sell for input LTCG amount
        Aggregates Data at Mutual Fund Scheme level
        Output MF Transaction and Header data into CSV File in data/ouput folder
        '''
        hdr_dict = defaultdict(list)

        mf_schemes_list = self.mf_hdr_df.scheme_name.to_list()
        for scheme_name in mf_schemes_list:
            target_ltcg_sell, target_units, msg  = self.calc_units_to_sell(scheme_name, target_ltcg)
            hdr_dict['scheme_name'].append(scheme_name)
            hdr_dict['target_ltcg'].append(target_ltcg_sell)
            hdr_dict['target_units'].append(target_units)
            hdr_dict['comments'].append(msg)

        #MF Header data with Target LTCG and Units to sell
        mf_hdr_ltcg_df = pd.DataFrame.from_dict(hdr_dict )


        # calculater aggregates from MF Transaction Data
        agg = {'amount': pd.NamedAgg(column= 'amount', aggfunc = 'sum'),
            'units': pd.NamedAgg(column= 'units',  aggfunc = 'sum'),
            'ltcg': pd.NamedAgg(column= 'ltcg', aggfunc = 'sum') ,
            'stcg': pd.NamedAgg(column= 'stcg', aggfunc = 'sum'),
            'current_amt': pd.NamedAgg(column= 'current_amt', aggfunc = 'sum') }
        mf_trans_grp_df = self.mf_trans_df.groupby('scheme_name').agg(**agg).reset_index()
        mf_trans_grp_df['perc_gain'] =   (mf_trans_grp_df['current_amt'] - mf_trans_grp_df['amount']) /  mf_trans_grp_df['amount'] * 100

        # Merge all header data
        self.mf_hdr_df = pd.merge(self.mf_hdr_df, mf_trans_grp_df, on ='scheme_name', how = 'left' )
        self.mf_hdr_df = pd.merge(self.mf_hdr_df, mf_hdr_ltcg_df, on ='scheme_name', how = 'left' )
        
        # Prepare Output data to download as CSV File
        self.output_hdr_df = self.mf_hdr_df.copy()
        self.output_trans_df = self.mf_trans_df.copy()

    
        # # Convert Dates to DD-MMM-YYYY Format
        # self.output_hdr_df['latest_nav_date'] = self.output_hdr_df['latest_nav_date'].dt.strftime(ct.DATE_FORMAT)

       

        # for col in ['trans_date', 'latest_nav_date']:
        #     self.output_trans_df[col] =  self.output_trans_df[col].dt.strftime(ct.DATE_FORMAT)
        
        #Round to 3 decimals : Need to convert Decimal to Float before rounding else does not work  
        cols_to_round = ['ltcg',	'stcg',	'current_amt',	'perc_gain',	'target_ltcg']
        self.output_hdr_df[cols_to_round] = self.output_hdr_df[cols_to_round].astype(float).round(3)   
        

        cols_to_round  = ['ltcg', 'stcg','cumil_ltcg',	'cumil_units',	'current_amt',	'perc_gain']
        self.output_trans_df[cols_to_round] = self.output_trans_df[cols_to_round].astype(float).round(3)   

        #Write to File
        out_hdr_file = os.path.join(ct.DATA_DIR, ct.OUT_DIR, ct.OUT_FILE_HDR)
        self.output_hdr_df.to_csv(out_hdr_file, index= False)
        logging.info(f'File: {out_hdr_file} written to disk')

        out_trans_file = os.path.join(ct.DATA_DIR, ct.OUT_DIR, ct.OUT_FILE_TRANS)
        self.output_trans_df.to_csv(out_trans_file, index= False)
        logging.info(f'File: {out_trans_file} written to disk\n')





    