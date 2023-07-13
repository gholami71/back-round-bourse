import datetime
from persiantools.jdatetime import JalaliDate
 



def toJalaliStr(date):
    date = str(JalaliDate(date)).replace('-','/')
    return date