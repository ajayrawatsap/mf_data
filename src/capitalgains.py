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

        # self.mf_trans_df['units_redeemed']  = 0

        # self._set_gf_nav()
        # self._calculate_capital_gains()

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

    def _get_stcg_ltcg(self,trans_date:datetime.date,latest_nav:float, latest_nav_date:datetime.date,
                       new_purh_nav:float, units:float, mf_type:str )->tuple[float, float ]:
        ltcg =  0
        stcg =  0
        date_one_year_ago  = latest_nav_date - relativedelta(years=1)
        date_3_year_ago    = latest_nav_date - relativedelta(years=3)

        if latest_nav is None or new_purh_nav is None or units is None:
            logging.warning(f"For Transaction date {trans_date} data is missing: Skipping capital Gains Calculation")
            return Decimal(0), Decimal(0)
        else:
            capital_gains = (latest_nav - new_purh_nav) * units

        if mf_type == ct.MF_EQUITY:
            #Transaction date is  earlier than a year ago, gains are STCG for Equity Funds
            if trans_date >= date_one_year_ago:
                stcg =  capital_gains     
            #Transaction date is later than a than a year ago, gains are LTCG
            elif trans_date < date_one_year_ago:
                ltcg = capital_gains

        elif mf_type == ct.MF_DEBT:
            #Transaction date is  earlier than 3 years ago, gains are STCG for Debt Funds
             if trans_date >= date_3_year_ago:
                stcg =  capital_gains     
             #Transaction date is later than 3 yaers gains are LTCG for debt funds
             elif trans_date < date_3_year_ago:
                ltcg = capital_gains
        return ltcg, stcg

    def _get_new_purch_nav(self,trans_date: datetime, price:float,  gf_nav:float,mf_type:str ) -> float:
        '''
        #Return the New Purchase NAV based on transaction date
        For transaction earlier than 31-JAN-2018, the new purchase NAV is max of gf_nav or 
        For transaction later than 31-JAN-2018, the new purchase NAV is same as purchase nav
        For Debt Funds no GrandFathered clause is applicable hence return the orig purchase price
        '''
        if mf_type == ct.MF_EQUITY:
            if trans_date <= pd.to_datetime(ct.GF_NAV_DATE, format= ct.DATE_FORMAT):
                return max(gf_nav,price )
            elif trans_date > pd.to_datetime(ct.GF_NAV_DATE, format= ct.DATE_FORMAT):
                return price   
        elif mf_type == ct.MF_DEBT:
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
            logging.warning( self.mf_trans_df.loc[null_idx].to_dict())
        else:
            logging.info(f"No Missing data Found:" )


        #if transaction date is before Jan-2018 use grand fathered NAV else use current NAV for calculating capital gains
        self.mf_trans_df['new_purch_nav'] = self.mf_trans_df.apply(lambda x: 
                                                                   self._get_new_purch_nav(x.trans_date, 
                                                                                           x.purch_nav, 
                                                                                           x.gf_nav,
                                                                                           x.type  ), 
                                                                    axis = 1)

        #Calculate the STCG or LTCG using New Purchase NAV per transaction
        self.mf_trans_df[['ltcg', 'stcg']] = self.mf_trans_df.apply(lambda x:  
                                                                    self._get_stcg_ltcg( x.trans_date,
                                                                                         x.latest_nav,
                                                                                         x.latest_nav_date,
                                                                                         x.new_purch_nav,                                                      
                                                                                         x.units,
                                                                                         x.type ) ,
                                                                    axis = 1, 
                                                                    result_type= 'expand')

        #Set Cumiltaive sum of LTCG and Units for each MF scheme
        self.mf_trans_df['cumil_ltcg'] = self.mf_trans_df.groupby('scheme_name')['ltcg'].transform(pd.Series.cumsum)
        self.mf_trans_df['cumil_units'] = self.mf_trans_df.groupby('scheme_name')['units'].transform(pd.Series.cumsum)                                                            

        #Latest Amount and Percent Gain
        # self.mf_trans_df['current_amt'] = self.mf_trans_df.units * self.mf_trans_df.latest_nav
        # self.mf_trans_df['perc_gain'] =   ((self.mf_trans_df['current_amt'] - self.mf_trans_df['amount']) /  self.mf_trans_df['amount']) * 100

        
        logging.info('\n' )

    def if_gf_nav_ok(self, mf_trans_single_df:pd.DataFrame)->bool:
        '''
            In case Transaction was done after date 31-Jan-2018  then gf nav is not required: 
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
        Use it to claculate the target units based on input target LTCG    
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
            logging.info(f'For Scheme {scheme_name} Total LTCG {ltcg_amt: .2f} is less than target LTCG {target_ltcg}: Sell {units_to_sell:.3f} units for LTCG of {ltcg_amt: .2f}') 
            msg = ( f'Total LTCG {ltcg_amt: .2f} is less than target LTCG {target_ltcg}: '
                    f'Sell {units_to_sell:.3f} units for LTCG of {ltcg_amt: .2f}' )

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
                    logging.info(f'For Scheme {scheme_name}: Sell {units_to_sell:.3f} units for LTCG of {ltcg_amt: .2f}')  
                    msg =   f'Sell {units_to_sell:.3f} units for LTCG of {ltcg_amt: .2f}'
                    return ltcg_amt, round(units_to_sell, 3), msg


    def calc_redeemed_units(self,scheme_name:str, mf_trans_df:pd.DataFrame)->pd.DataFrame:
        '''
        Input is scheme name and dataframe having all trasnactions for all schemes.
        Return a DataFrame for a single scheme with redeemed units as new column 
        Calculate Total Units redeeemed for a MF scheme. 
        Use this to exhaust  units on FIFO basis, and set redeemed units per transaction.     
        '''

        def get_redeemed_units(units:Decimal, total_redeemed_units:Decimal)->Decimal:
                '''
                helper method to be called with apply method on dataframe
                '''
                nonlocal consumed_units
                nonlocal stop_calc        
                
                #exclude non purchase transactions e,g.. redemptions or when all units are exhauasted
                if units < 0 or stop_calc  == True:
                    return 0

                # Total redeemed units consumed so far
                consumed_units += units

                redeemed_units = 0

                # ALl units are set to redeemed until we find partial consumption 
                if consumed_units <= total_redeemed_units:
                    redeemed_units = units
                else:
                    redeemed_units = units - (consumed_units - total_redeemed_units)
                    stop_calc = True

                return redeemed_units

        
        # Filter data for  a single scheme
        mf_trans_single_df =  mf_trans_df[mf_trans_df.scheme_name == scheme_name].copy()

        mf_trans_single_df['units_redeemed']  = 0

        # Fiter transactions where units are redeemed
        redemptions_df = mf_trans_single_df[mf_trans_single_df.trans_type == ct.TRANS_TYPE_REDEMPTION]

        

        #Get total redeemmed units
        total_redeemed_units= abs(redemptions_df.units.sum())

        # No Redemptions: Do nothing
        if  total_redeemed_units > 0:        
    
            logging.info(f'For Scheme {scheme_name}, {total_redeemed_units} units are redeemed:setting redeemed units as FIFO ')
            
            consumed_units = 0
            stop_calc  =  False

            # set redeemed units against each transaction in order of FIFO
            mf_trans_single_df['units_redeemed'] = mf_trans_single_df.apply(lambda x: 
                                                                        get_redeemed_units(x.units,
                                                                                        total_redeemed_units ),
                                                                            axis = 1)
    
        return mf_trans_single_df


    def set_units_amts_for_redemptions(self,mf_trans_df:pd.DataFrame)->pd.DataFrame:
        '''
        Set redeeemed units,  remaining units, invested amount and current amount for 
        units that are left are consuming redeemed units. 
        Do it for all schemes one by one , even if no redemptions exist, redeemed units will be set 0
        Adds new columns ['units_redeemed', 'units_remain', 'invested_amt' , 'current_amt'] to input dataframe
        '''
        
        mf_schemes_list = self.mf_hdr_df.scheme_name.to_list()       
        
        mf_trans_concat = pd.DataFrame()

        for scheme_name in mf_schemes_list:
            mf_trans_single_df = self.calc_redeemed_units(scheme_name, mf_trans_df)    
            
            mf_trans_concat =  pd.concat([mf_trans_concat, mf_trans_single_df])   
        
        # Set Redeemed units            
        mf_trans_df = pd.merge(mf_trans_df, mf_trans_concat['units_redeemed'], left_index=True, right_index=True, how = 'left')

        #Units remaining after taking redemptions into account
        mf_trans_df['units_remain'] =  mf_trans_df.units -  mf_trans_df.units_redeemed

        #For redemptions Transactions set remaining units to 0
        mf_trans_df.loc[mf_trans_df.units_remain < 0, 'units_remain'] = 0

        #The actual invested amount and current amount has to be calculated on basis of units left after redemption
        mf_trans_df['invested_amt'] = (mf_trans_df.units_remain * mf_trans_df.purch_nav).astype(float).round(2)    
        mf_trans_df['current_amt'] = (mf_trans_df.units_remain * mf_trans_df.latest_nav).astype(float).round(2)

        mf_trans_df['perc_gain'] =   ((mf_trans_df['current_amt'] - mf_trans_df['invested_amt']) /  mf_trans_df['invested_amt']) * 100


        return  mf_trans_df  

    def prepare_hdr_data(self, mf_hdr_df:pd.DataFrame, mf_trans_df:pd.DataFrame, target_ltcg = 100000)->pd.DataFrame:
        '''
        Create Header DataFrame by
        (1) Aggregating Transaction data amounts and units
        (2) Setting the target units to sell for a target LTCG
        (3) Merging with existig headr MF data 
        '''

        # calculates aggregates from MF Transaction Data
        agg = {
                'invested_amt': pd.NamedAgg(column= 'invested_amt', aggfunc = 'sum'),
                'units': pd.NamedAgg(column= 'units_remain',  aggfunc = 'sum'),
                'ltcg': pd.NamedAgg(column= 'ltcg', aggfunc = 'sum') ,
                'stcg': pd.NamedAgg(column= 'stcg', aggfunc = 'sum'),
                'current_amt': pd.NamedAgg(column= 'current_amt', aggfunc = 'sum') 
            }
        mf_trans_grp_df = mf_trans_df.groupby('scheme_name').agg(**agg).reset_index()

        mf_trans_grp_df['perc_gain'] =   ((mf_trans_grp_df['current_amt'] - mf_trans_grp_df['invested_amt']) / 
                                                mf_trans_grp_df['invested_amt'] * 100 )


        #Prepare Units to sell for a Target LTCG
        hdr_dict = defaultdict(list) 

        mf_schemes_list = mf_hdr_df.scheme_name.to_list()
        for scheme_name in mf_schemes_list:
            target_ltcg_sell, target_units, msg  = self.calc_units_to_sell(scheme_name, target_ltcg)
            hdr_dict['scheme_name'].append(scheme_name)
            hdr_dict['target_ltcg'].append(target_ltcg_sell)
            hdr_dict['target_units'].append(target_units)
            hdr_dict['comments'].append(msg)


        mf_hdr_ltcg_df = pd.DataFrame.from_dict(hdr_dict )

        #Merge all HDR data to create a single dataframe
        mf_hdr_df_out = pd.merge(mf_hdr_df, mf_trans_grp_df, on ='scheme_name', how = 'left' )
        mf_hdr_df_out = pd.merge(mf_hdr_df_out, mf_hdr_ltcg_df, on ='scheme_name', how = 'left')
        return mf_hdr_df_out




    def prepare_final_data(self,target_ltcg:float)->None:
        '''
        This is main method and can be called afte setting the data in constrcutor
        Calculates the Target Units to sell for input LTCG amount
        Aggregates Data at Mutual Fund Scheme level
        Output MF Transaction and Header data into CSV File in data/ouput folder
        '''

        self._set_gf_nav()
        self._calculate_capital_gains()
        
        #Set Redeemded units and Invested, Current Amounts
        self.mf_trans_df = self.set_units_amts_for_redemptions(self.mf_trans_df)


        # Create HDR MF data will aggregate data and units to sell for target LTCG
        self.mf_hdr_df = self.prepare_hdr_data(self.mf_hdr_df, self.mf_trans_df, target_ltcg)

        # hdr_dict = defaultdict(list)

        # mf_schemes_list = self.mf_hdr_df.scheme_name.to_list()
        # for scheme_name in mf_schemes_list:
        #     target_ltcg_sell, target_units, msg  = self.calc_units_to_sell(scheme_name, target_ltcg)
        #     hdr_dict['scheme_name'].append(scheme_name)
        #     hdr_dict['target_ltcg'].append(target_ltcg_sell)
        #     hdr_dict['target_units'].append(target_units)
        #     hdr_dict['comments'].append(msg)

        # #MF Header data with Target LTCG and Units to sell
        # mf_hdr_ltcg_df = pd.DataFrame.from_dict(hdr_dict )


        # # calculater aggregates from MF Transaction Data
        # agg = {'amount': pd.NamedAgg(column= 'amount', aggfunc = 'sum'),
        #     'units': pd.NamedAgg(column= 'units',  aggfunc = 'sum'),
        #     'ltcg': pd.NamedAgg(column= 'ltcg', aggfunc = 'sum') ,
        #     'stcg': pd.NamedAgg(column= 'stcg', aggfunc = 'sum'),
        #     'current_amt': pd.NamedAgg(column= 'current_amt', aggfunc = 'sum') }
        # mf_trans_grp_df = self.mf_trans_df.groupby('scheme_name').agg(**agg).reset_index()
        # mf_trans_grp_df['perc_gain'] =   ((mf_trans_grp_df['current_amt'] - mf_trans_grp_df['amount'].astype(float)) / 
        #                                      mf_trans_grp_df['amount'].astype(float) * 100 )

        # # Merge all header data
        # self.mf_hdr_df = pd.merge(self.mf_hdr_df, mf_trans_grp_df, on ='scheme_name', how = 'left' )
        # self.mf_hdr_df = pd.merge(self.mf_hdr_df, mf_hdr_ltcg_df, on ='scheme_name', how = 'left' )
        
        # Prepare Output data to download as CSV File
        self.output_hdr_df = self.mf_hdr_df.copy()
        self.output_trans_df = self.mf_trans_df.copy()

    
       
        
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





    