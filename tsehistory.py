import requests
import pandas as pd
from persiantools.jdatetime import JalaliDate
import datetime
from persiantools import characters, digits
import pymongo
client = pymongo.MongoClient()
db = client['RoundBourse']

#df = requests.get(url='http://members.tsetmc.com/tsev2/excel/MarketWatchPlus.aspx?d=14020517').content
#df = pd.read_excel(df)


today = datetime.datetime.now()
newDate = today
for i in range(0,730,1):
    newDate = today - datetime.timedelta(days=i)
    dt = datetime.datetime(newDate.year,newDate.month,newDate.day,15,0,0)
    week = newDate.weekday()
    if week != 2 or week != 4:
        jalali = JalaliDate.to_jalali(newDate)
        jalaliStr = str(jalali).replace('-','/')
        jalaliInt =int(str(jalali).replace('-',''))
        chack = db['tse'] .count_documents({'dataInt':jalaliInt})
        if chack == 0:
            res = requests.get(url=f'http://members.tsetmc.com/tsev2/excel/MarketWatchPlus.aspx?d={jalali}')
            if res.status_code == 200:
                df = pd.read_excel(res.content,header=2, engine='openpyxl') 
                if len(df)>10:
                    df = df[~df['نماد'].str.contains(r'\d')]

                    df['نماد'] = df['نماد'].apply(characters.ar_to_fa)
                    df['نام'] = df['نام'].apply(characters.ar_to_fa)
                    df['data'] = jalaliStr
                    df['dataInt'] = jalaliInt
                    df['timestump'] = dt.timestamp()
                    df['time'] = str(dt.hour) +':'+str(dt.minute)+':'+str(dt.second)
                    df = df.to_dict('records')
                    db['tse'].insert_many(df)

                    print(jalaliStr,len(df))
                    


                


                
