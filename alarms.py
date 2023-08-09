import pymongo
import pandas as pd
import dateHandler
import time
import datetime
import sms
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
                        dff['textMsg'] = [dff['symbol'],dff['method']]
                        listTargetId = dff['_id'].to_list()
                        db['alarms'].update_many({'_id':{'$in':listTargetId}},{'$set':{'active':False}})
                        for x in dff.index:
                            sms.smsAlarm(dff['phone'][x],dff['textMsg'][x][0],dff['textMsg'][x][1])
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
                        dff['textMsg'] = [dff['symbol'],dff['method']]
                        listTargetId = dff['_id'].to_list()
                        db['alarms'].update_many({'_id':{'$in':listTargetId}},{'$set':{'active':False}})
                        for x in dff.index:
                            sms.smsAlarm(dff['phone'][x],dff['textMsg'][x][0],dff['textMsg'][x][1])

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
                        dff['textMsg'] = [dff['symbol'],dff['method']]
                        listTargetId = dff['_id'].to_list()
                        db['alarms'].update_many({'_id':{'$in':listTargetId}}, {'$set':{'active':False}})
                        for x in dff.index:
                            sms.smsAlarm(dff['phone'][x],dff['textMsg'][x][0],dff['textMsg'][x][1])






while True:
    if dateHandler.isWorkDay():
        if dateHandler.isTimeOpenBourse():
            if dateHandler.minutePerSeven():
                CheakingProcess = True
                while CheakingProcess:
                    try:
                        GetAlarmsActive()
                        dilay = 60 - datetime.datetime.now().second
                        print('شروط بررسی شد یک دقیقه توقف"')
                        time.sleep(dilay)
                    except:

                        print('بررسی شروط با خطا مواجه شد 3 ثانیه توقف')
                        time.sleep(3)
            else:
                print('زمان بررسی شروع شروط نرسیده 60 ثانیه توقف')
                dilay = 60 - datetime.datetime.now().second
                time.sleep(dilay)
        else:
            print('ساعت کاری بازار پایان یافته 5 دقیقه توقف')
            dilay = 60 - datetime.datetime.now().second
            time.sleep((60*4) + dilay)
    else:
        print('بازار بسته است یک ساعت توقف')
        dilay = 60 - datetime.datetime.now().second
        time.sleep((60*59) + dilay)