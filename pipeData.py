import pymongo
import pandas as pd
import requests
import dateHandler
import time
import datetime
client = pymongo.MongoClient()
db = client['RoundBourse']



def setTseToDb():
    df = pd.read_excel(requests.get('http://members.tsetmc.com/tsev2/excel/MarketWatchPlus.aspx?d=0',verify=False).content,header=2)
    df = df[~df['نماد'].str.contains(r'\d')]
    df['data'] = dateHandler.toDayJalaliStr()
    df['dataInt'] = dateHandler.toDayJalaliInt()
    df['timestump'] = time.time()
    now = datetime.datetime.now()
    df['time'] = str(now.hour) +':'+str(now.minute)+':'+str(now.second)
    df = df.to_dict('records')
    db['tse'].insert_many(df)

while True:
    if dateHandler.isWorkDay():
        if dateHandler.isTimeOpenBourse():
            if dateHandler.minutePerFive():
                setTseToDb()
                time.sleep(60)
            else:
                time.sleep(60)
        else:
            time.sleep(60*5)
    else:
        time.sleep(60*60)




