import pymongo
import pandas as pd
import dateHandler
import time
import datetime
client = pymongo.MongoClient()
db = client['RoundBourse']



def GetAlarmsActive():
    df = pd.DataFrame(db['alarms'].find({'active':True}))
    if len(df)>0:
        maxTimestump = db['tse'].find_one({}, sort=[("timestump", -1)])['timestump']
        for i in list(set(df['AlarmtType'])):
            if i == 'قیمت':
                dff = df[df['AlarmtType']==i]
                if len(dff)>0:
                    dff['price'] = dff['price'].astype(int)
                    listTargetSymbol = list(set(dff['symbol']))
                    TseDf = pd.DataFrame(db['tse'].find({'نماد':{"$in": listTargetSymbol},'timestump':maxTimestump}))[['آخرین معامله - مقدار','نماد']]
                    dff = dff.set_index('symbol').join(TseDf.set_index('نماد')).reset_index()
                    dff['compare'] = (dff['price']<dff['آخرین معامله - مقدار']) == (dff['method']=='بیشتر')
                    dff = dff[dff['compare']==True]
                    dff['textMsg'] = 'هشدار برای "' +dff['symbol'] + '" قیمت ' +dff['method']+' '+ dff['آخرین معامله - مقدار'].astype(str)+'\n'+'roundtrade.ir'
                    listTargetId = dff['_id'].to_list()
                    db['alarms'].update_many({'_id':{'$in':listTargetId}},{'$set':{'active':False}})
                    for x in dff.index:
                        print(dff['phone'][x],dff['textMsg'][x])
            elif i == 'صف':
                dff = df[df['AlarmtType']==i]
                if len(dff)>0:
                    listTargetSymbol = list(set(dff['symbol']))
                    TseDf = pd.DataFrame(db['tse'].find({'نماد':{"$in": listTargetSymbol},'timestump':maxTimestump}))[['فروش - حجم','خرید - حجم','نماد']]
                    dff = dff.set_index('symbol').join(TseDf.set_index('نماد')).reset_index()
                    dff['compare'] = ((dff['خرید - حجم']==0) + (dff['فروش - حجم']>0) and (dff['method']=='صف فروش شدن')) or ((dff['خرید - حجم']>0) + (dff['فروش - حجم']==0) and (dff['method']=='صف خرید شدن')) or ((dff['خرید - حجم']>0) and (dff['method']=='جمع شدن صف فروش')) or ((dff['فروش - حجم']>0) and (dff['method']=='ریختن صف خرید'))
                    dff = dff[dff['compare']==True]
                    dff['textMsg'] = 'هشدار برای "' +dff['symbol'] + '" قیمت ' +dff['method']+' '+ dff['آخرین معامله - مقدار'].astype(str)+'\n'+'roundtrade.ir'
                    listTargetId = dff['_id'].to_list()
                    db['alarms'].update_many({'_id':{'$in':listTargetId}},{'$set':{'active':False}})
                    for x in dff.index:
                        print(dff['phone'][x],dff['textMsg'][x])
            elif i == 'پیام ناظر':
                pass








GetAlarmsActive()