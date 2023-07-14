import datetime
from persiantools.jdatetime import JalaliDate
import pymongo
client = pymongo.MongoClient()
db = client['RoundBourse']




def toJalaliStr(date):
    date = str(JalaliDate(date)).replace('-','/')
    return date

def isWorkDay():
    toDay = toJalaliStr(datetime.datetime.now())
    if db['calendar'].find_one({'holiday':toDay}) == None:
        return True
    else:
        return False

def isTimeOpenBourse():
    now = datetime.datetime.now()
    h = now.hour
    m = now.minute
    if h <8: return False
    elif h>=15: return False
    elif h==8 and m<45: return False
    else: return True

def toDayJalaliStr():
    date = str(JalaliDate(datetime.datetime.now())).replace('-','/')
    return date

def toDayJalaliInt():
    date = int(str(JalaliDate(datetime.datetime.now())).replace('-',''))
    return date

def minutePerFive():
    now = datetime.datetime.now()
    m = now.minute
    if m%5 == 0: return True
    else: return False
