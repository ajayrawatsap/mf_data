import os
import logging
import pandas as pd 

import src.tests.testconfig as tc

from collections import namedtuple

from src.parsedata import PDFParser
from src.capitalgains import CapitalGains
from src.initialize import Logger


class MFTestError(Exception):
       pass

class UnitTest():
    def __init__(self, show_logs:bool = False):
        logger = Logger()
        logger.initilaze_logging('no')    
        logging.info(f'{"*" * 50}Start Of Unit Test{"*" * 50}')

    def _is_hdr_output_ok(self, file_path_cas:str, file_path_hdr_out:str, password:str )->bool:
        '''
        Comapres the sum of units to sell from the csv output file
        '''
        dp = PDFParser()
        
        mf_trans_df, mf_hdr_df = dp.parse_mf_data(file_path_cas, password)
        target_ltcg = 100000
        cg = CapitalGains(mf_hdr_df, mf_trans_df)
        cg.prepare_final_data(target_ltcg)

        hdr_df_act = cg.output_hdr_df  

        #convert from decimal to Float
        target_units_sum_act = float(hdr_df_act.target_units.sum())
    

    # Read expected data 
        hdr_df_exp = pd.read_csv(file_path_hdr_out)
        target_units_sum_exp = round(hdr_df_exp.target_units.sum(), 3)
        
        if target_units_sum_act ==  target_units_sum_exp:
            return True
        else:
            logging.error(f"Target Units Do not Match: Expected {target_units_sum_exp}, Got {target_units_sum_act}")
            return False

    def run_basic_test(self):
        
        print("running Basic Test:", end = " ")
        

        file_path_cas = os.path.join( tc.unit_test_base_dir, 'basic', 'cas_june_27.pdf')
        file_path_actual = os.path.join( tc.unit_test_base_dir, 'basic', 'hdr_cas_june_27.csv')

        logging.info(f"running Basic Test for input file {file_path_cas}")
        
        ok = self._is_hdr_output_ok(file_path_cas,file_path_actual, tc.password)
        res = tc.PASS if ok else tc.FAIL
        print(f"{res}")
        logging.info(f"Result:{res}\n")

        if not ok:            
            msg = f"Test Failed for input file {file_path_cas}, output file {file_path_actual}"
            logging.error(msg)
            raise MFTestError(msg)


    def test_redemption(self):

        
        print("running test for rdemeption", end = " ")
      
        dp = PDFParser()    
        file_path_cas = os.path.join( tc.unit_test_base_dir, 'cas_jul_19_21.pdf')

        logging.info(f"running test for rdemeption for file {file_path_cas}")

        mf_trans_df, mf_hdr_df = dp.parse_mf_data(file_path_cas, tc.password)
        cg = CapitalGains(mf_hdr_df, mf_trans_df)

        test_data = []
        Data = namedtuple('Data', ['scheme_name', 'redeemed_units'])
        icici_nf = Data('ICICI Prudential Nifty Next 50 Index Fund - Direct Plan - Growth', 11130.000 )
        test_data.append(icici_nf)

        dsp_scf = Data('DSP Small Cap Fund - Direct Plan - Growth', 0)
        test_data.append(dsp_scf)

        
        for data  in test_data:
            mf_trans_single_df = cg.calc_redeemed_units(data.scheme_name, mf_trans_df)
            redeemed_units = mf_trans_single_df.units_redeemed.sum()
            if not redeemed_units == data.redeemed_units:  
                res =   tc.FAIL    
                print(f"{res}")      
                msg = f"Test Failed for input file { file_path_cas}, scheme {data.scheme_name }: Expected Redeemmed units {data.redeemed_units} , Got {redeemed_units}"
                logging.error(msg)
                raise MFTestError(msg)
            
        res = tc.PASS
        print(f"{res}")
        logging.info(f"Result:{res}\n")
        
    def test_invested_current_amounts(self):
        print("running test for Current Amount and Invested Amount :", end = " ")

        dp = PDFParser()    
        file_path_cas = os.path.join( tc.unit_test_base_dir, 'cas_jul_19_21.pdf')

        logging.info(f"running test for Current Amount and Invested Amount for file {file_path_cas}")

        mf_trans_df, mf_hdr_df = dp.parse_mf_data(file_path_cas, tc.password)
        cg = CapitalGains(mf_hdr_df, mf_trans_df)
        cg._set_gf_nav()
        mf_trans_df  = cg.mf_trans_df

        test_data = []
        Data = namedtuple('Data', ['scheme_name', 'invested_amt', 'current_amt'])

        icici_nf = Data('ICICI Prudential Nifty Next 50 Index Fund - Direct Plan - Growth', 277741, 411315 )
        test_data.append(icici_nf)

        ft_ldf = Data('Franklin India Low Duration Fund - Direct Plan - Growth', 33068, 42704 )
        test_data.append(ft_ldf)

        dsp_scf = Data('DSP Small Cap Fund - Direct Plan - Growth', 759990, 1405390 )
        test_data.append(dsp_scf)

        #  Method to test
        mf_trans_df = cg.set_units_amts_for_redemptions(mf_trans_df)
        ok = True

        for data in test_data:
                mf_trans_single = mf_trans_df[mf_trans_df.scheme_name == data.scheme_name]
                total_invested_amt = round(mf_trans_single.invested_amt.sum(), 0)
                total_current_amt = round(mf_trans_single.current_amt.sum(), 0)

                if total_invested_amt != data.invested_amt:
                    msg = ( f"Test Failed for input file { file_path_cas}, scheme {data.scheme_name }:\n"
                            f"expected invested amount: {data.invested_amt}, got {total_invested_amt}" )
                    ok = False
                    break
                if total_current_amt != data.current_amt:
                    msg = ( f"Test Failed for input file { file_path_cas}, scheme {data.scheme_name }:\n"
                            f"expected current amount: {data.current_amt}, got {total_current_amt}" )
                    ok = False
                    break
                    
        res = tc.PASS if ok else tc.FAIL
        print(res)
        logging.info(f"Result:{res}\n")
        if not ok:
            logging.error(msg)
            raise MFTestError(msg)   

    def test_hdr_amounts(self):
        '''
        Test Aggregate Invested and Current Amount for all MF schemes
        This has been validated against VRO portfolio on 30-07-2021
        '''
        print("running test for Aggregate Current Amount and Invested Amount :", end = " ")
        file_path_cas = os.path.join( tc.unit_test_base_dir, 'cas_jul_29_21.pdf')

        logging.info(f"running test for Aggregate Current Amount and Invested Amount for file {file_path_cas}")

        dp =PDFParser()     
        mf_trans_df, mf_hdr_df = dp.parse_mf_data(file_path_cas, password=tc.password)

        cg = CapitalGains(mf_hdr_df, mf_trans_df)
        cg._set_gf_nav()
        cg._calculate_capital_gains()

        mf_trans_df = cg.set_units_amts_for_redemptions(cg.mf_trans_df)
        

        # Method to be tested
        mf_hdr_df = cg.prepare_hdr_data(mf_hdr_df, mf_trans_df)

        invested_amt_act = round(mf_hdr_df.invested_amt.sum(), 0)
        invested_amt_exp = 8666344.0

        current_amt_act  = round(mf_hdr_df.current_amt.sum(), 0)
        current_amt_exp  = 12911991.0 

        ok = True

        if invested_amt_act != invested_amt_exp:
            msg = ( f"Test Failed for input file { file_path_cas}: "
                    f"expected invested amount: { invested_amt_exp}, got: {invested_amt_act}" )
            ok = False

        if current_amt_act != current_amt_exp:
            msg = ( f"Test Failed for input file { file_path_cas}: "
                    f"expected invested amount: { current_amt_exp}, got: {current_amt_act}" )
            ok = False

        res = tc.PASS if ok else tc.FAIL
        print(res)
        logging.info(f"Result:{res}\n")
        if not ok:
            logging.error(msg)
            raise MFTestError(msg)   

    