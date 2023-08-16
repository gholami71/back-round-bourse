import pymongo
import pandas as pd
import pandas_ta as ta
client = pymongo.MongoClient()
db = client['RoundBourse']



def getDfTse(symbol_list, lenght):
    pipeline = [
        {"$match": {"نماد": {"$in": symbol_list}, "dataInt": {"$gt": lenght}}},
        {"$sort": {"dataInt": -1, "timestump": -1}},
        {"$group": {"_id": "$نماد", "docs": {"$addToSet": "$$ROOT"}}},
        {"$project": {"_id": 1, "top": {"$slice": ["$docs", lenght]}}}
    ]
    # اجرای aggregate بر روی کالکشن
    results = list(db['tse'].aggregate(pipeline))
    data = []
    for item in results:
        for doc in item['top']:
            data.append(doc)
    df = pd.DataFrame(data)
    df = df.sort_values(by='timestump')
    return df


def apply_rsi(group):
    group['RSI'] = ta.rsi(group['آخرین معامله - مقدار'], length=4)
    return group

def apply_sma(group, window_size):
    group['SMA'] = group['آخرین معامله - مقدار'].rolling(window=window_size, min_periods=1).mean()
    return group

def apply_ema(group, window_size):
    group['EMA'] = ta.ema(group['آخرین معامله - مقدار'], length=window_size)
    return group

def apply_wma(group, window_size):
    group['WMA'] = (group['آخرین معامله - مقدار'] * group['حجم']).rolling(window=window_size, min_periods=1).sum() / group['حجم'].rolling(window=window_size, min_periods=1).sum()
    return group

def get_rsi_df_tse(symbol_list,last_day):
    df = getDfTse(symbol_list,24)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_rsi)
    df = df[['dataInt','RSI','نماد']]
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
