import requests
import pandas as pd
from persiantools.jdatetime import JalaliDate
import datetime
from persiantools import characters, digits
import pymongo
import analysis
client = pymongo.MongoClient()
db = client['RoundBourse']




df = pd.DataFrame(db['tse'].find({'نماد':'ویسا'}))
df = df.sort_values(by='dataInt')
df['قیمت_نرمال'] = (df['قیمت پایانی - مقدار'] - df['قیمت پایانی - مقدار'].min()) / (df['قیمت پایانی - مقدار'].max() - df['قیمت پایانی - مقدار'].min())
df['minPrice'] = df['قیمت پایانی - مقدار'].rolling(window=5,center=True,min_periods=1).min()
df['min'] = df['قیمت_نرمال'].rolling(window=5,center=True,min_periods=1).min()
df['min'] = df['min'] * 100
df['min'] = df['min'].apply(int)
df['count'] = df.groupby('min')['min'].transform('count')
df = df.sort_values('count')
latest_price = df[df['dataInt'] == df['dataInt'].max()]['قیمت پایانی - مقدار'].values[0]
df = df[df['minPrice']<=latest_price]
df = df[df['count']>2]
df['distanc'] = latest_price - df['minPrice'] 
minTarget = df[df['distanc']==df['distanc'].min()]['min'].values[0]
support = df[df['min']==minTarget]['minPrice'].mean()
df['soppurt'] = support
print(df)