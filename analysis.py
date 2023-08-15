import pymongo
import pandas as pd
import pandas_ta as ta
client = pymongo.MongoClient()
db = client['RoundBourse']






def getDfTse(lenght):
    pipeline = [
        {"$match": {"dataInt": {"$gt": lenght}}},
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
    group['RSI'] = ta.rsi(group['آخرین معامله - مقدار'], length=14)
    return group


def get_rsi_df_tse():
    df = getDfTse(24)
    df = df.drop_duplicates(subset=['نماد','dataInt'],keep='last')
    df = df.groupby('نماد',group_keys=False).apply(apply_rsi)
    df = df[['dataInt','RSI','نماد']]
    return df