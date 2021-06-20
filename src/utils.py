
from  datetime import datetime


def is_valid_date(date_text:str, date_format:str)->bool:
    try:
        datetime.strptime(date_text, date_format)
        return True
    except:
        return False
