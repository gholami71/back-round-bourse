import requests
import pandas as pd
from persiantools.jdatetime import JalaliDate
import datetime
from persiantools import characters, digits
import pymongo
import analysis
import matplotlib.pyplot as plt

client = pymongo.MongoClient()
db = client['RoundBourse']




df = pd.DataFrame(db['tse'].find({}))
for i in df.index:
    symbol = df['نماد'][i]
    char = symbol[-1]
    if char == 'ح':
        id = df['_id'][i]
        db['tse'].delete_many({'_id':id})
        print(symbol)
