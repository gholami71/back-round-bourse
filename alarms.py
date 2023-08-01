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
        maxDate = db['payamNazer'].find_one({}, sort=[("date", -1)])['date']
        for i in list(set(df['AlarmtType'])):
            if i == 'قیمت':
                dff = df[df['AlarmtType']==i]
                if len(dff)>0:
                    dff['price'] = dff['price'].replace('',0)
                    dff['price'] = dff['price'].astype(int)
                    listTargetSymbol = list(set(dff['symbol']))
                    TseDf = pd.DataFrame(db['tse'].find({'نماد':{"$in": listTargetSymbol},'timestump':maxTimestump}))
                    if (len(TseDf>0)):
                        TseDf = TseDf[['آخرین معامله - مقدار','نماد']]
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
                    TseDf = pd.DataFrame(db['tse'].find({'نماد':{"$in": listTargetSymbol},'timestump':maxTimestump}))
                    if (len(TseDf)>0):
                        TseDf = TseDf[['فروش - حجم','خرید - حجم','نماد']]
                        dff = dff.set_index('symbol').join(TseDf.set_index('نماد')).reset_index()
                        dff['compare'] = ((dff['خرید - حجم']==0) + (dff['فروش - حجم']>0) and (dff['method']=='صف فروش شدن')) or ((dff['خرید - حجم']>0) + (dff['فروش - حجم']==0) and (dff['method']=='صف خرید شدن')) or ((dff['خرید - حجم']>0) and (dff['method']=='جمع شدن صف فروش')) or ((dff['فروش - حجم']>0) and (dff['method']=='ریختن صف خرید'))
                        dff = dff[dff['compare']==True]
                        dff['textMsg'] = 'هشدار برای "' +dff['symbol'] + '" قیمت ' +dff['method']+' '+ dff['آخرین معامله - مقدار'].astype(str)+'\n'+'roundtrade.ir'
                        listTargetId = dff['_id'].to_list()
                        db['alarms'].update_many({'_id':{'$in':listTargetId}},{'$set':{'active':False}})
                        for x in dff.index:
                            print(dff['phone'][x],dff['textMsg'][x])
            elif i == 'پیام ناظر':
                dff = df[df['AlarmtType']==i]
                if len(dff)>0:
                    listTargetSymbol = list(set(dff['symbol']))
                    payamNazerDF = pd.DataFrame(db['payamNazer'].find({'symbol':{'$in':listTargetSymbol}, 'date':maxDate}))
                    if (len(payamNazerDF)>0):
                        payamNazerDF = payamNazerDF[['News_Text','Title','symbol']] 
                        dff = dff[['symbol','method','notification','phone','_id']]        
                        dff = dff.set_index('symbol').join(payamNazerDF.set_index('symbol')).reset_index()
                        dff['compare'] = dff['method'].isin(dff['News_Text']) + (dff['method']=='همه')
                        dff = dff.drop(columns=['Title','News_Text'])
                        dff = dff.drop_duplicates()
                        dff = dff[dff['compare']==True]
                        dff['textMsg'] = 'هشدار برای "' +dff['symbol'] +' :'+ dff['method']+'\n'+'roundtrade.ir'
                        print(dff)
                        listTargetId = dff['_id'].to_list()
                        db['alarms'].update_many({'_id':{'$in':listTargetId}}, {'$set':{'active':False}})









GetAlarmsActive()