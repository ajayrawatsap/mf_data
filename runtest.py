
import logging
from src.tests.testmf import UnitTest, MFTestError

if __name__ == "__main__":  
 
    ut = UnitTest()
    try:
      ut.run_basic_test()
      ut.test_redemption()
      ut.test_invested_current_amounts()
      ut.test_hdr_amounts()
    except  MFTestError as e:       
        print(e)

    logging.info(f'{"*" * 50}End Of Unit Test{"*" * 50}')

