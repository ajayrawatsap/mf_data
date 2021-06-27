# Mutual Funds Capital Gains
This aim of this project is to calculate number of units required to sell a Equity Mutual Fund so that LTCG(Long-term capital gains) is tax Free

For Equity Mutual funds the gains up to 100,000 INR is tax free in a Financial Year. To calculate number of units required to sell a MF scheme so that LTCG is tax free is a complicated process which involves multiple factors such as
1. LTCG is applicable for any unit purchased before one year of selling date
2. LTCG up to 100,000 INR is tax free while above this amount is taxable at 10% 
3. Grand-Fathered clause, which means if you have an investment before 31-Jan-2018, then cost of acquisition would be  purchase price or NAV on 31-Jan-2018 whichever is higher
4. If you have a SIP spanning across multiple years then each cost price, sale price and LTCG has to be calculated individually for each SIP

## How to use the tool
1. The frst step is to get the consolidated account statement from CAMS in PDF Format
2. Convert the PDF to text by cupying the text and pasting it to  text file 
3. Install the required python version 3.9 and rqequired libraries.
4. Copy the git hub project to your local machine and execute the python main function using command line


## FAQ
1. It is assuumed that there are no partial redemptions as the claculations can be wroong
2. For some MF schemes the calculation may not be possible as the Grandfathred NAV could not be found. To resolve such isssues Mnaully manaintin the GF in CSV File
3. The calculation would also be done for Debt funds but you should ignore the. Currently its is not possble to differntial between Equity and Debt Schemes
4. The tool has been tested in Windows 10 OS with python 3.9, but it should also work in linux/linux envirronment
5. I have not been to find a fool proof way to diectrly convert PDF to text programatically. This is work under process and in future the tool would be able to process PDF file directly
6. The limited testing has happened on my own Mutual fund Schemes. In case you encounter bug and issue please report it in issues.

