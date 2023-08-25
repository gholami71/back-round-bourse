import requests
import pandas as pd
from persiantools.jdatetime import JalaliDate
import datetime
from persiantools import characters, digits
import pymongo
import analysis

client = pymongo.MongoClient()
db = client['RoundBourse']

blackSymbol = db['blackSymbol'].find({},{'symbol':1,'_id':0})
blackSymbol = [x['symbol'] for x in blackSymbol]
for i in blackSymbol:
    db['tse'].delete_many({'نماد':i})