import pymongo
import pandas as pd
import pandas_ta as ta
from sklearn.linear_model import LinearRegression as reg
import numpy as np
client = pymongo.MongoClient()
db = client['RoundBourse']



#def getDfTse(symbol_list, lenght):
#    pipeline = [
#        {"$match": {"نماد": {"$in": symbol_list}, "dataInt": {"$gt": lenght}}},
#        {"$sort": {"dataInt": -1}},
#        {"$group": {"_id": "$نماد", "docs": {"$addToSet": "$$ROOT"}}},
#        {"$project": {"_id": 1, "top": {"$slice": ["$docs", lenght]}}}
#    ]
#    # اجرای aggregate بر روی کالکشن
#    results = list(db['tse'].aggregate(pipeline,allowDiskUse=True))
#    data = []
#    for item in results:
#        for doc in item['top']:
#            data.append(doc)
#    df = pd.DataFrame(data)
#    df = df.sort_values(by='timestump')
#    return df

def getDfTse(symbol_list, length):
    pipeline = [
        {"$match": {"نماد": {"$in": symbol_list}, "dataInt": {"$gt": length}}},
        {"$sort": {"dataInt": -1}},
        {"$group": {"_id": "$نماد", "docs": {"$push": "$$ROOT"}}},
        {"$project": {"_id": 1, "top": {"$slice": ["$docs", length]}}},
        {"$unwind": "$top"},
        {"$replaceRoot": {"newRoot": "$top"}}
    ]
    
    results = list(db['tse'].aggregate(pipeline, allowDiskUse=True))
    df = pd.DataFrame(results)
    df = df.sort_values(by='timestump')
    return df

def apply_To100Int(x):
    return int(float(x)*100)

def apply_rsi(group):
    group['RSI'] = ta.rsi(group['آخرین معامله - مقدار'], length=14)
    group['RSI'] = group['RSI'].fillna(0)
    group['RSI'] = group['RSI'].apply(int)
    return group



def apply_reg(group, columns):
    x = np.arange(len(group)).reshape(-1,1)
    y = group[columns]
    model = reg().fit(x, y)
    coefficient = model.coef_[0]
    price_y = group['آخرین معامله - مقدار']
    model = reg().fit(x, price_y )
    price_coefficient = model.coef_[0]
    group = group[group['dataInt']== group['dataInt'].max()]
    group['coefficient'] = coefficient
    group['price_coefficient'] = price_coefficient
    group = group[['نماد','coefficient','price_coefficient','dataInt',columns]]
    return group
    

def apply_cci(group):
    group['CCI'] = ta.cci(high=group['بیشترین'], low=group['کمترین'], close=group['آخرین معامله - مقدار'], length=20)
    group['CCI'] = group['CCI'].fillna(0)
    group['CCI'] = group['CCI'].apply(int)
    return group

def apply_sma(group, window_size):
    group['SMA'] = group['آخرین معامله - مقدار'].rolling(window=window_size, min_periods=1).mean()
    group['SMA'] = group['SMA'].apply(round)
    return group

def apply_ema(group, window_size):
    group['EMA'] = ta.ema(group['آخرین معامله - مقدار'], length=window_size)
    group['EMA'] = group['EMA'].apply(round)
    return group

def apply_wma(group, window_size):
    group['WMA'] = (group['آخرین معامله - مقدار'] * group['حجم']).rolling(window=window_size, min_periods=1).sum() / group['حجم'].rolling(window=window_size, min_periods=1).sum()
    group['WMA'] = group['WMA'].apply(round)
    return group

def apply_supertrend(group, length):
    group['SuperTrend'] = ta.supertrend(high=group['بیشترین'], low=group['کمترین'], close=group['آخرین معامله - مقدار'], length=length, multiplier=3)
    return group

def apply_support(group):
    if len(group)<20:
        group = group[group['dataInt']==group['dataInt'].max()]
        group['support'] = 0
        return group
    
    group['normalPrice'] = (group['قیمت پایانی - مقدار'] - group['قیمت پایانی - مقدار'].min()) / (group['قیمت پایانی - مقدار'].max() - group['قیمت پایانی - مقدار'].min())
    group['minPrice'] = group['قیمت پایانی - مقدار'].rolling(window=5,center=True,min_periods=1).min()
    group['minNormal'] = group['normalPrice'].rolling(window=5,center=True,min_periods=1).min()
    if len(group)<10:
        group = group[group['dataInt']==group['dataInt'].max()]
        group = group.drop(columns=['normalPrice','minPrice','minNormal'])
        group['support'] = 0
        return group
    group['minNormal']=group['minNormal'].fillna(0)
    group['minNormal'] = group['minNormal'].apply(apply_To100Int)
    group['count'] = group.groupby('minNormal')['minNormal'].transform('count')
    latest_price = group[group['dataInt'] == group['dataInt'].max()]['قیمت پایانی - مقدار'].values[0]
    df = group[group['minPrice']<=latest_price]
    if len(df) == 0: 
        group = group[group['dataInt']==group['dataInt'].max()]
        group = group.drop(columns=['normalPrice','minPrice','minNormal','count'])
        group['support'] = 0
        return group
    df = df[df['count']>5]
    if len(df) == 0: 
        group = group[group['dataInt']==group['dataInt'].max()]
        group = group.drop(columns=['normalPrice','minPrice','minNormal','count'])
        group['support'] = 0
        return group
    df['distanc'] = latest_price - df['minPrice']
    minTarget = df[df['distanc']==df['distanc'].min()]['minNormal'].values[0]
    support = df[df['minNormal']==minTarget]['minPrice'].mean()
    group = group[group['dataInt']==group['dataInt'].max()]
    group['support'] = support
    group = group.drop(columns=['normalPrice','minPrice','minNormal','count'])
    return group


def apply_resistance(group):
    if len(group)<20:
        group = group[group['dataInt']==group['dataInt'].max()]
        group['resistance'] = 0
        return group
    group['normalPrice'] = (group['قیمت پایانی - مقدار'] - group['قیمت پایانی - مقدار'].min()) / (group['قیمت پایانی - مقدار'].max() - group['قیمت پایانی - مقدار'].min())
    group['maxPrice'] = group['قیمت پایانی - مقدار'].rolling(window=5,center=True,min_periods=1).max()
    group['maxNormal'] = group['normalPrice'].rolling(window=5,center=True,min_periods=1).max()
    df = group.fillna(0)
    if len(df)<10:
        group = group[group['dataInt']==group['dataInt'].max()]
        group = group.drop(columns=['normalPrice','maxPrice','maxNormal'])
        group['resistance'] = 0
        return group
    print('-'*20)
    print(group)
    group['maxNormal'] = group['maxNormal'].apply(apply_To100Int)
    group['count'] = group.groupby('maxNormal')['maxNormal'].transform('count')
    latest_price = group[group['dataInt'] == group['dataInt'].max()]['قیمت پایانی - مقدار'].values[0]
    df = group[group['maxPrice']>=latest_price]
    if len(df) == 0: 
        group = group[group['dataInt']==group['dataInt'].max()]
        group = group.drop(columns=['normalPrice','maxPrice','maxNormal','count'])
        group['resistance'] = 0
        return group
    df = df[df['count']>5]
    if len(df) == 0: 
        group = group[group['dataInt']==group['dataInt'].max()]
        group = group.drop(columns=['normalPrice','maxPrice','maxNormal','count'])
        group['resistance'] = 0
        return group
    df['distanc'] = latest_price - df['maxPrice']
    minTarget = df[df['distanc']==df['distanc'].min()]['maxNormal'].values[0]
    resistance = df[df['maxNormal']==minTarget]['maxPrice'].mean()
    group = group[group['dataInt']==group['dataInt'].max()]
    group['resistance'] = resistance
    group = group.drop(columns=['normalPrice','maxPrice','maxNormal','count'])
    return group

def apply_gain(group):
    if len(group)>0:
        firstPrice = group[group['dataInt']==group['dataInt'].min()]
        firstPrice = firstPrice['قیمت پایانی - مقدار'][firstPrice.index.max()]
        lastPrice = group[group['dataInt']==group['dataInt'].max()]
        lastPrice = lastPrice['قیمت پایانی - مقدار'][lastPrice.index.max()]
        gain = lastPrice / firstPrice
        gain = (gain - 1) * 1000
        gain = int(gain) / 10
        group = group[group['dataInt']==group['dataInt'].max()]
        group['gain'] = gain
        group = group[['نماد','dataInt','gain']]
        return group
    
def apply_value(group):
    if len(group)>0:
        group['value'] = int(group['ارزش'].mean())
        group = group[group['dataInt']==group['dataInt'].max()]
        group = group[['نماد','dataInt','value']]
        return group

def get_deverconverCCI_df_tse(symbol_list):
    df = getDfTse(symbol_list, 30)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_cci)
    df = df.groupby('نماد', group_keys=False).apply(apply_reg,columns='CCI')
    return df

def get_diverconverRSI_df_tse(symbol_list):
    df = getDfTse(symbol_list, 30)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_rsi)
    df = df.groupby('نماد', group_keys=False).apply(apply_reg,columns='RSI')
    return df

def get_rsi_df_tse(symbol_list,last_day):
    df = getDfTse(symbol_list,last_day+14)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_rsi)
    df = df[['dataInt','RSI','نماد']]
    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(last_day, 'dataInt'))
    return df

def get_cci_df_tse(symbol_list,last_day):
    df = getDfTse(symbol_list,last_day+20)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_cci)
    df = df[['dataInt','CCI','نماد']]
    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(last_day, 'dataInt'))
    return df

def get_sma_df_tse(symbol_list,last_day):
    df = getDfTse(symbol_list,last_day*2)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_sma,window_size=last_day)
    df = df[['dataInt','SMA','نماد','آخرین معامله - مقدار']]
    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(last_day, 'dataInt'))
    df = df.rename(columns={'آخرین معامله - مقدار':'قیمت'})
    return df

def get_ema_df_tse(symbol_list,last_day):
    df = getDfTse(symbol_list,last_day*2)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_ema,window_size=last_day)
    df = df[['dataInt','EMA','نماد','آخرین معامله - مقدار']]
    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(last_day, 'dataInt'))
    df = df.rename(columns={'آخرین معامله - مقدار':'قیمت'})
    return df

def get_wma_df_tse(symbol_list,last_day):
    df = getDfTse(symbol_list,last_day*2)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_wma,window_size=last_day)
    df = df[['dataInt','WMA','نماد','آخرین معامله - مقدار']]
    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(last_day, 'dataInt'))
    df = df.rename(columns={'آخرین معامله - مقدار':'قیمت'})
    return df

def get_supertrand_df_tse(symbol_list,last_day):
    df = getDfTse(symbol_list,last_day*2)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_supertrend,length=last_day)
    df = df[['dataInt','SuperTrend','نماد','آخرین معامله - مقدار']]
    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(last_day, 'dataInt'))
    df = df.rename(columns={'آخرین معامله - مقدار':'قیمت'})
    return df

def get_candle_df_tse(symbol_list,last_day):
    df = getDfTse(symbol_list,last_day)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df['body'] = ((df['آخرین معامله - مقدار'] / df['اولین']) - 1) * 100
    df['body_abs'] = df['body'].apply(abs)
    df['top'] = df.apply(lambda row: row['اولین'] if row['اولین'] > row['آخرین معامله - مقدار'] else row['آخرین معامله - مقدار'], axis=1)
    df['top'] = ((df['بیشترین'] / df['top']) - 1)*100
    df['bot'] = df.apply(lambda row: row['اولین'] if row['اولین'] < row['آخرین معامله - مقدار'] else row['آخرین معامله - مقدار'], axis=1)
    df['bot'] = ((df['bot'] / df['کمترین']) - 1)*100
    df['all'] = ((df['بیشترین'] / df['کمترین']) - 1)*100
    df = df[['body','body_abs','top','bot','نماد','dataInt']]
    return df



def get_support_df_tse(symbol_list):
    df = getDfTse(symbol_list,365)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_support)
    df = df[['نماد','support','dataInt','آخرین معامله - مقدار']]
    df = df.rename(columns={'آخرین معامله - مقدار':'قیمت'})
    df = df[df['support']>0]
    df['distance'] = ((df['قیمت'] / df['support']) - 1) * 100
    df['distance'] = df['distance'].apply(int)
    df['support'] = df['support'].apply(int)
    return df



def get_resistance_df_tse(symbol_list):
    df = getDfTse(symbol_list,365)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_resistance)
    df = df[['نماد','resistance','dataInt','آخرین معامله - مقدار']]
    df = df.rename(columns={'آخرین معامله - مقدار':'قیمت'})
    df = df[df['resistance']>0]
    df['distance'] = ((df['resistance'] / df['قیمت']) - 1) * 100
    df['distance'] = df['distance'].apply(int)
    df['resistance'] = df['resistance'].apply(int)
    return df

def get_gain_df_tse(symbol_list,lenght):
    df = getDfTse(symbol_list,lenght)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_gain)
    return df


def get_value_df_tse(symbol_list, length):
    df = getDfTse(symbol_list,length)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_value)
    return df

    

