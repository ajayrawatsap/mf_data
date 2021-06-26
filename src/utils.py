
from  datetime import datetime


def is_valid_date(date_text:str, date_format:str)->bool:
    try:
        datetime.strptime(date_text, date_format)
        return True
    except:
        return False

def rename_mf_scheme(scheme_name:str)->str:
    scheme_name = scheme_name.replace('-', ' - ')

    #Convert MF scheme in Camel Case
    scheme_name =  ' '.join([text.title() for text in scheme_name.split()])

    
    scheme_name = scheme_name.replace('Plan', '')
    scheme_name = scheme_name.replace('Option', '')

    #Remove Spaces within seperator '-
    scheme_name  =  '-'.join([text.strip() for text in scheme_name.split('-')])


    return scheme_name 
