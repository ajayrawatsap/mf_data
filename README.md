# Mutual Funds Capital Gains
This aim of this project is to calculate number of units required to sell an Equity Mutual Fund so that LTCG (Long-term capital gains) is tax Free. 
<br>This would be initially a command line tool based on python script. 
<br>In future it is planned to create standalone windows executable and then a proper website based on feedback and demand.

For Equity Mutual funds the gains up to 100,000 INR is tax free in a Financial Year. To calculate number of units required to sell a MF scheme so that LTCG is tax free is a complicated process which involves multiple factors such as
1. LTCG is applicable for any Equity MF units sold after one year of its purchase data
2. LTCG up to 100,000 INR is tax free while above this amount is taxable at 10% 
3. Grand-Fathered clause, which means if you have an investment before 31-Jan-2018, then cost of acquisition would be  purchase price or NAV on 31-Jan-2018 whichever is higher
4. If you have a SIP spanning across multiple years then each cost price, sale price and LTCG has to be calculated individually for each SIP

The input to this tool is PDF File from CAMS containing all transactions for a period.
It produces two output files, [Aggregate](mf_data/data/output/sample_output_mf_totals.csv) file at scheme level and [Transaction](mf_data/data/output/sample_output_mf_transactions.csv) file.

![sample_output_hdr](https://github.com/ajayrawatsap/mf_data/blob/master/data/assets/sample_ouput.PNG)


## How to use the tool
1. The frst step is to get the [consolidated account statement](https://www.camsonline.com/Investors/Statements/Consolidated-Account-Statement) from CAMS in PDF Format. Make sure that you select the option as highlighted in yellow. ![screenshot](https://github.com/ajayrawatsap/mf_data/blob/master/data/assets/cams.PNG)
2. Clone the current github repo. See [help](https://docs.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository-from-github/cloning-a-repository) for more details. On windows it can be done by opening command prompt tool and runing below commands
   ```
   git clone https://github.com/ajayrawatsap/mf_data.git  
   
   ```
   ```
   cd mf_data
   ```

3. Copy  the PDF file to mf_data/data/ folder of repo you downloaded in step 2
   
5. Install the latest [python](https://www.python.org/downloads/)  version 3.9 and required libraries.
   See [requirements.txt ](/requirements.txt) for additional python libraries required and install them using pip command.
7. Execute python main function using command line. Make sure you are executing from path where main.py file is located. Use the correct file name for your file.
    <br>
    <br>option1: Calculate units to sell for tax free LTCG of INR 100000 (default value). 
   ```
   python main.py cams_june_27.pdf password
   ```
    <br>option2: Calculate units to sell for tax free LTCG of user defined value (INR 50000 in this case)
      ```
       python main.py cams_june_27.pdf password 50000
      ```
9. It will create two ouput files in directory  data/output/
    1. output_mf_totals.csv: For each mutual fund scheme it will list the total LTCG, STCG, Percent  Gain and Target units to sell for tax free gains. Check sample [output](mf_data/data/output/sample_output_mf_totals.csv) file
    1. output_mf_transactions.csv: This will list transaction level details and claculations for LTCG, STCG and gain percent. Check  sample [output](mf_data/data/output/sample_output_mf_transactions.csv) file.


## FAQ
#### Does it work for Partial Redemptions
  It is assuumed that there are no partial redemptions as the claculations can be wrong. This will be supported in Future
  
#### Calculations are missing for some schemes  
For some MF schemes the calculation may not be possible as the Grandfathred NAV could not be found in CSV file. To resolve such issues Manualy maintain the Grand Fathered NAV(for date 31.01.2018)  in [CSV File](data/nav/gf_nav_all.csv)
 #### Why Calculations are also done for Debt Funds  
  The calculation would also be done for Debt funds but you should ignore it as LTCG for debt funds are calcuated differently. Currently its is not possible to differentiate between Equity and Debt Schemes
#### On Which OS can the tool run
  The tool has been tested in Windows 10 OS with python 3.9, but it should also work in linux/mac environment
#### Why can't I directly use pdf file as input
 I have not been to find a fool proof way to directly convert PDF to text programatically. This is work under process and in future the tool would be able to process PDF file directly. Any suggestions and help is welcome
#### It does not work correctly for my schemes
 The limited testing has happened on my own Mutual fund Schemes. In case you encounter bug and issue please report it in issues. 
 

