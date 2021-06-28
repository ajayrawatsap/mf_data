# Mutual Funds Capital Gains
This aim of this project is to calculate number of units required to sell a Equity Mutual Fund so that LTCG(Long-term capital gains) is tax Free

For Equity Mutual funds the gains up to 100,000 INR is tax free in a Financial Year. To calculate number of units required to sell a MF scheme so that LTCG is tax free is a complicated process which involves multiple factors such as
1. LTCG is applicable for any unit purchased before one year of selling date
2. LTCG up to 100,000 INR is tax free while above this amount is taxable at 10% 
3. Grand-Fathered clause, which means if you have an investment before 31-Jan-2018, then cost of acquisition would be  purchase price or NAV on 31-Jan-2018 whichever is higher
4. If you have a SIP spanning across multiple years then each cost price, sale price and LTCG has to be calculated individually for each SIP

## How to use the tool
1. The frst step is to get the [consolidated account statement](https://new.camsonline.com/Investors/Statements/Consolidated-Account-Statement) from CAMS in PDF Format. Make sure that you select the option as highlighted in yellow. ![screenshot](https://github.com/ajayrawatsap/mf_data/blob/master/data/assets/cams.PNG)

3. Convert the PDF to text by copying the text and pasting it to  text file . 
    It is imortant to note that the pdf file is password protected and copy is not possble by default. 
    To enable copying open the pdf in chrome browser and then click print button ![print](https://github.com/ajayrawatsap/mf_data/blob/master/data/assets/print_chrome.PNG)
    Use CTLR+A to select all CTRL+C to copy all text. Paste the text in text file and save file to directory  data/ . Check  [sample_data.txt](/data/sample_data.txt) file, your file should also be in same directory.
5. Install the latest [python](https://www.python.org/downloads/)  version 3.9 and required libraries.
   See [requirements.txt ](/requirements.txt) for additional python libraries required and install them using pip command.
7. Copy the git hub project to your local machine and execute the python main function using command line by changing path to root folder where main.py file is located.
8. It will create two ouput files in directory  data/output/
    1. output_mf_totals.csv: For each mutual fund scheme it will list the total LTCC, STCG, Percent  Gain and Target units to sell for tax free gains. Check sample [output](data/output/output_mf_totals.csv) file
    1. output_mf_transactions.csv: This will list transaction level details and claculations for LTCG, STCG and gain percent. Check  sample [output](data/output/output_mf_transactions.csv) file.


## FAQ
1. It is assuumed that there are no partial redemptions as the claculations can be wroong
2. For some MF schemes the calculation may not be possible as the Grandfathred NAV could not be found. To resolve such isssues Mnaully manaintin the GF in CSV File
3. The calculation would also be done for Debt funds but you should ignore the. Currently its is not possble to differntial between Equity and Debt Schemes
4. The tool has been tested in Windows 10 OS with python 3.9, but it should also work in linux/linux envirronment
5. I have not been to find a fool proof way to diectrly convert PDF to text programatically. This is work under process and in future the tool would be able to process PDF file directly
6. The limited testing has happened on my own Mutual fund Schemes. In case you encounter bug and issue please report it in issues.

