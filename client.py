import crypto
import pymongo
import json
import datetime
import random
import pandas as pd
import dateHandler
from bson import ObjectId
import sms
import analysis

client = pymongo.MongoClient()
db = client['RoundBourse']

limit = {'alarms':{'pro':10, 'proplus':20, 'premium':40}}

def AllowExplor(data):
    try:
        user = crypto.decrypt(data['phu'])
    except:
        return {'reply':False,'msg':'ورود با مشکل مواجه شده است لطفا مجددا وارد شوید'}
    user = db['users'].find_one({'phone':str(user)})
    if user['datecredit']<datetime.datetime.now():
        return {'reply':False,'msg':'اشتراک شما پایان یافته'}

    return {'reply':True,'user':user}


def applyphone(data):
    captchacode = crypto.decrypt(data['CaptchaCode'])
    if captchacode != data['UserInput']['captcha']:
        return json.dumps({'reply':False,'msg':'کد کپچا صحیح نیست'})
    txt = random.randint(10000,99999)
    db['otp'].insert_one({'phone':data['UserInput']['phone'], 'codetext':str(txt), 'date':datetime.datetime.now()})
    sms.OTP(data['UserInput']['phone'], txt)
    return json.dumps({'reply':True})

def coderegistered(data):
    code = data['UserInput']['code']
    phone = data['UserInput']['phone']
    codetext = db['otp'].find_one({'phone': phone}, sort=[('date', -1)])['codetext']
    if code != codetext:
        return json.dumps({'reply':False})
    phoneUser = db['users'].find_one({'phone':phone})
    if phoneUser == None:
        dic = {'phone':phone, 'dateregister':datetime.datetime.now(), 
               'datecredit':datetime.datetime.now()+datetime.timedelta(days=3),
               'label': 'pro'
               }
        db['users'].insert_one(dic)
    else:
        db['users'].update_one({'phone':phone},{'$set':{'lastlogin':datetime.datetime.now()}})
    cookie = crypto.encrypt(data['UserInput']['phone'])
    return json.dumps({'reply':True, 'phu':cookie})


def Useratuh(data):
    try:
        cookie= crypto.decrypt(data['cookie'])
        if db['users'].find_one({'phone':cookie}) == None:
            return json.dumps({'reply':False})
        return json.dumps({'reply':True})
    except:
        return json.dumps({'reply':False})


def userInfo(data):
    user = crypto.decrypt(data['phu'])
    info = db['users'].find_one({'phone':user},{'_id':0,'phone':1,'datecredit':1,'label':1,'companyName':1,'fullName':1,'personality':1})
    credit = info['datecredit'] - datetime.datetime.now()
    if credit.seconds // 3600 > 12:
        if max(0,(credit.days+1))>0:
            info['creditDay'] = str(max(0,(credit.days+1))) + ' روز '
        else:
            info['creditDay'] = str(credit.seconds // 3600) + ' ساعت '
    else:
        info['creditDay'] = max(0,(credit.days))
    del info['datecredit']
    if 'personality' in info.keys():
        if info['personality'] == 'true':
            info['name'] = info['fullName']
        else:
            info['name'] = info['companyName']
            del info['fullName']
        del info['personality']
    if info['creditDay']==0:
        info['label'] = ''
    else:
        info['label'] = info['label'].replace('proplus','پرو پلاس').replace('pro','پرو').replace('premium','پریمیوم')
    if info == None: 
        return json.dumps({'reply':False})
    return json.dumps({'reply':True, 'info':info})


    #کاربر چک شود که قبل از آپدیت در دیتابیس موجود باشد
def userSetProfile(data):
    user = crypto.decrypt(data['phu'])
    data = data['data']
    db['users'].update_one({'phone':user},{'$set':data})
    return json.dumps({'reply':True})

def userGetProfile(data):
    user = crypto.decrypt(data['phu'])
    data = db['users'].find_one({'phone':user},{'_id':0,'dateregister':0,'datecredit':0,'lastlogin':0})
    if data == None: return json.dumps({'reply':False,'msg':'اطلاعات کاربر یافت نشد'})
    return json.dumps({'reply':True,'data':data})


def setTicket(data):
    user = crypto.decrypt(data['phu'])
    dic = {'user':user,'title':data['ticket']['title'],'content':data['ticket']['content'],'date':datetime.datetime.now(),'reply':'','del':False}
    db['support'].insert_one(dic)
    return json.dumps({'reply':True})


def getTicket(data):
    user = crypto.decrypt(data['phu'])
    df = pd.DataFrame(db['support'].find({'user':user},{'user':0}))
    if len(df)==0:
        return json.dumps({'reply':False,'msg':'سابقه تیکه خالی است'})
    df = df.sort_values(by='date',ascending=False)
    df = df[df['del']==False]
    df['_id'] = [str(x) for x in df['_id']]
    df['date'] = [dateHandler.toJalaliStr(x) for x in df['date']]
    df = df.to_dict('records')
    return json.dumps({'reply':True,'df':df})


def delTicket(data):
    user = crypto.decrypt(data['phu'])
    db['support'].update_one({'user':user,'_id':ObjectId(data['id'])},{'$set':{'del':True}})
    return json.dumps({'reply':True})

def userSetAlarm(data):
    phu = crypto.decrypt(data['phu'])
    user = db['users'].find_one({'phone':phu},{'_id':0})
    date = user['datecredit']-datetime.datetime.now()
    if date.days<=0 and date.seconds <=0:
        return json.dumps({'reply':False, 'msg':'شما اشتراک ندارید'})
    lim = limit['alarms'][user['label']]
    numberAlarms = db['alarms'].count_documents({'phone':phu, 'active':True})
    if numberAlarms>=lim :
        return json.dumps({'reply':False, 'msg':f'شما مجاز به ایجاد حداکثر {lim} .هشدار میباشید' })
    dic = data['InputUser']
    if '_id' not in dic.keys():
        dic['date'] = datetime.datetime.now()
        dic['phone'] = phu
        dic['active'] = True
        db['alarms'].insert_one(dic)  
    else:
        _id = dic['_id']
        del dic['_id']
        del dic['date']
        dic['date'] = datetime.datetime.now()
        db['alarms'].update_one({'_id':ObjectId(_id)},{'$set':dic})
    return json.dumps({'reply':True})

def userGettAlarm(data):
    phu = crypto.decrypt(data['phu'])    
    alarms = pd.DataFrame(db['alarms'].find({'phone':phu}))
    if len(alarms) == 0:
        return json.dumps({'reply':False})
   
    alarms['_id'] = [str(x) for x in alarms['_id']]
    alarms['date'] = [dateHandler.toJalaliStr(x) for x in alarms['date']]
    alarms = alarms.to_dict('records')
    
    return json.dumps({'reply':True , 'alarms':alarms})


def userGetSymbol(data):
    phu = crypto.decrypt(data['phu'])    
    user = db['users'].find_one({'phone':phu})
    if user ==None:
        return json.dumps({'reply':False})
    symbols = db['tse'].distinct('نماد')
    return json.dumps({'reply':True, 'symbols':symbols})


def userDelAlarm(data):
    phu = crypto.decrypt(data['phu']) 
    if(db['users'].find_one({'phone':phu}) == None):
        return json.dumps({'reply':False})
    db['alarms'].delete_one({'_id':ObjectId(data['id'])})
    return json.dumps({'reply':True})

def userEditAlarm(data):
    return json.dumps({'reply':True})


def userGetexplor(data):
    allow = AllowExplor(data)
    if allow['reply'] == False:
        return json.dumps(allow)
    user = allow['user']['phone']
    condition = db['conditions'].find({'phone':user},{'_id':0,'phone':0})
    symbols = db['tse'].distinct('نماد')
    dfs = []
    for i in condition:
        if i['type']=='indicator':
            if i['indicator']=='rsi':
                if i['position']=='greater':
                    df = analysis.get_rsi_df_tse(symbols,1)
                    df['con'] = df['RSI']>int(i['value'])
                if i['position']=='less':
                    df = analysis.get_rsi_df_tse(symbols,1)
                    df['con'] = df['RSI']<int(i['value'])
                if i['position']=='cross':
                    df = analysis.get_rsi_df_tse(symbols,int(i['lastday']))
                    df['con'] = df['RSI']<int(i['value'])
                    con = df.groupby('نماد')['con'].nunique() > 1
                    df = df.set_index('نماد').drop(columns='con').join(con).reset_index()
                df = df[df['con']==True]
                df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    symbols = df['نماد'].to_list()
                    df = df[['RSI','نماد']]
                    dfs.append(df)

            if i['indicator']=='cci':
                if i['position']=='greater':
                    df = analysis.get_cci_df_tse(symbols,1)
                    df['con'] = df['CCI']>int(i['value'])
                if i['position']=='less':
                    df = analysis.get_cci_df_tse(symbols,1)
                    df['con'] = df['CCI']<int(i['value'])
                if i['position']=='cross':
                    df = analysis.get_cci_df_tse(symbols,int(i['lastday']))
                    df['con'] = df['CCI']<int(i['value'])
                    con = df.groupby('نماد')['con'].nunique() > 1
                    df = df.set_index('نماد').drop(columns='con').join(con).reset_index()
                df = df[df['con']==True]
                df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    symbols = df['نماد'].to_list()
                    df = df[['CCI','نماد']]
                    dfs.append(df)

            if i['indicator']=='sma':
                if i['position']=='greater':
                    df = analysis.get_sma_df_tse(symbols,int(i['length']))
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['con'] = df['SMA']>df['قیمت']
                if i['position']=='less':
                    df = analysis.get_sma_df_tse(symbols,int(i['length']))
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['con'] = df['SMA']<df['قیمت']
                if i['position']=='cross':
                    df = analysis.get_sma_df_tse(symbols,int(i['length'])+int(i['lastday']))
                    df['con'] = df['SMA']<df['قیمت']
                    con = df.groupby('نماد')['con'].nunique() > 1
                    df = df.set_index('نماد').drop(columns='con').join(con).reset_index()
                df = df[df['con']==True]
                df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    symbols = df['نماد'].to_list()
                    df = df[['SMA','نماد']]
                    df = df.rename(columns={'SMA':'SMA '+str(i['length'])})
                    dfs.append(df)

            if i['indicator']=='ema':
                if i['position']=='greater':
                    df = analysis.get_ema_df_tse(symbols,int(i['length']))
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['con'] = df['EMA']>df['قیمت']
                if i['position']=='less':
                    df = analysis.get_ema_df_tse(symbols,int(i['length']))
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['con'] = df['EMA']<df['قیمت']
                if i['position']=='cross':
                    df = analysis.get_ema_df_tse(symbols,int(i['length'])+int(i['lastday']))
                    df['con'] = df['EMA']<df['قیمت']
                    con = df.groupby('نماد')['con'].nunique() > 1
                    df = df.set_index('نماد').drop(columns='con').join(con).reset_index()
                df = df[df['con']==True]
                df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    symbols = df['نماد'].to_list()
                    df = df[['EMA','نماد']]
                    df = df.rename(columns={'EMA':'EMA '+str(i['length'])})
                    dfs.append(df)

            if i['indicator']=='wma':
                if i['position']=='greater':
                    df = analysis.get_wma_df_tse(symbols,int(i['length']))
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['con'] = df['WMA']>df['قیمت']
                if i['position']=='less':
                    df = analysis.get_wma_df_tse(symbols,int(i['length']))
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['con'] = df['WMA']<df['قیمت']
                if i['position']=='cross':
                    df = analysis.get_wma_df_tse(symbols,int(i['length'])+int(i['lastday']))
                    df['con'] = df['WMA']<df['قیمت']
                    con = df.groupby('نماد')['con'].nunique() > 1
                    df = df.set_index('نماد').drop(columns='con').join(con).reset_index()
                df = df[df['con']==True]
                df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    symbols = df['نماد'].to_list()
                    df = df[['WMA','نماد']]
                    df = df.rename(columns={'WMA':'WMA '+str(i['length'])})

                    dfs.append(df)

            if i['indicator']=='supertrend':
                if i['position']=='greater':
                    df = analysis.get_supertrand_df_tse(symbols,int(i['length']))
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['con'] = df['SuperTrend']>df['قیمت']
                if i['position']=='less':
                    df = analysis.get_supertrand_df_tse(symbols,int(i['length']))
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['con'] = df['SuperTrend']<df['قیمت']
                if i['position']=='cross':
                    df = analysis.get_supertrand_df_tse(symbols,int(i['length'])+int(i['lastday']))
                    df['con'] = df['SuperTrend']<df['قیمت']
                    con = df.groupby('نماد')['con'].nunique() > 1
                    df = df.set_index('نماد').drop(columns='con').join(con).reset_index()
                df = df[df['con']==True]
                df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    symbols = df['نماد'].to_list()
                    df = df[['SuperTrend','نماد']]
                    df = df.rename(columns={'SuperTrend':'SuperTrend '+str(i['length'])})
                    dfs.append(df)


        if i['type']=='candlestick':
            df = analysis.get_candle_df_tse(symbols,int(i['lastday']))

            if i['candlestick'] == 'bullish':
                df['bullish'] = (df['body'] > 2) & (df['top'] < 0.3) & (df['bot'] < 0.3)
                df = df[df['bullish']==True]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['bullish'] = df['dataInt']
                    df = df[['نماد','bullish']]
                    symbols = df['نماد'].to_list()
                    dfs.append(df)

            if i['candlestick'] == 'bearish':
                df['bearish'] = (df['body'] < 2) & (df['top'] < 0.3) & (df['bot'] < 0.3)
                df = df[df['bearish']==True]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['bearish'] = df['dataInt']
                    df = df[['نماد','bearish']]
                    symbols = df['نماد'].to_list()
                    dfs.append(df)

            if i['candlestick'] == 'hummer':
                df['hummer'] = (df['bot'] > (df['body_abs'] *2)) & (df['top'] < df['body_abs'])
                df = df[df['hummer']==True]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['hummer'] = df['dataInt']
                    df = df[['نماد','hummer']]
                    symbols = df['نماد'].to_list()
                    dfs.append(df)

            if i['candlestick'] == 'invertedhammer':
                df['invertedhammer'] = (df['top'] > (df['body_abs'] *2)) & (df['bot'] < df['body_abs'])
                df = df[df['invertedhammer']==True]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['invertedhammer'] = df['dataInt']
                    df = df[['نماد','invertedhammer']]
                    symbols = df['نماد'].to_list()
                    dfs.append(df)

            if i['candlestick'] == 'gravestondoji':
                df['gravestondoji'] = (df['top'] > (df['body_abs'] *4)) & ((df['bot']*2) < df['top'])
                df = df[df['gravestondoji']==True]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['gravestondoji'] = df['dataInt']
                    df = df[['نماد','gravestondoji']]
                    symbols = df['نماد'].to_list()
                    dfs.append(df)

            if i['candlestick'] == 'longleggeddoji':
                df['longleggeddoji'] = (df['bot'] > (df['body_abs'] *4)) & ((df['top']*2) < df['bot'])
                df = df[df['longleggeddoji']==True]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['longleggeddoji'] = df['dataInt']
                    df = df[['نماد','longleggeddoji']]
                    symbols = df['نماد'].to_list()
                    dfs.append(df)

            if i['candlestick'] == 'dragonflydoji':
                df['dragonflydoji'] = (df['bot'] > (df['body_abs'] *4)) & (df['bot'] > (df['body_abs'] *4))
                df = df[df['dragonflydoji']==True]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['dragonflydoji'] = df['dataInt']
                    df = df[['نماد','dragonflydoji']]
                    symbols = df['نماد'].to_list()
                    dfs.append(df)

            if i['candlestick'] == 'star':
                df['star'] = (df['bot'] > (df['body_abs'] *4)) & (df['bot'] > (df['body_abs'] *4)) & (df['body_abs'] < 1.5)
                df = df[df['star']==True]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                else:
                    df = df.groupby('نماد', group_keys=False).apply(lambda group: group.nlargest(1, 'dataInt'))
                    df['star'] = df['dataInt']
                    df = df[['نماد','star']]
                    symbols = df['نماد'].to_list()
                    dfs.append(df)

        if i['type']=='supportresistance':
            if i['supportresistance'] == 'support':
                df = analysis.get_support_df_tse(symbols)
                df = df[df['distance']<=int(i['distance'])]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                df = df[df['distance']>-3]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                df = df[['نماد','support']]
                symbols = df['نماد'].to_list()
                dfs.append(df)

            if i['supportresistance'] == 'resistance':
                df = analysis.get_resistance_df_tse(symbols)
                df = df[df['distance']<=int(i['distance'])]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                df = df[df['distance']>-3]
                if len(df) == 0:
                    return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
                df = df[['نماد','resistance']]
                symbols = df['نماد'].to_list()
                dfs.append(df)

    dff = None
    for i in dfs:
        if dff is None:
            dff = i
        else:
            dff = dff.merge(i,on=['نماد'])
    
    if len(dff) == 0:
        return json.dumps({'reply':False,'msg':'نمادی با شروط قید شده یافت نشد'})
    
    print(dff)
    
    return json.dumps({'reply':False})


def setcondition(data):  
    credit = AllowExplor(data)
    if credit['reply'] == False:
        return json.dumps(credit)
 
    label_user = credit['user']['label']
    count_condition = db['conditions'].count_documents({'phone':credit['user']['phone']})
    label = {'pro':1,'proplus':3, 'premium':9}  
    if label[label_user] <= count_condition:
        return json.dumps({'reply':False,'msg': f'حداکثر شروط برای حساب کاربری شما  {label[label_user]} میباشد.' })
    dic = data['data']
    dic['phone'] = str(credit['user']['phone'])
    if db['conditions'].find_one(dic) != None:
        return json.dumps({'reply':False, 'msg':'شرط تکراری است'})
    db['conditions'].insert_one(dic)
    return json.dumps({'reply':True})


def getcondition(data):
    user = AllowExplor(data)
    if user['reply'] == False:
        return json.dumps(user)
    df = pd.DataFrame(db['conditions'].find({'phone':user['user']['phone']}))
    if len(df)==0:
        return json.dumps({'reply':True,'df':[]})
    df['_id'] = df['_id'].apply(str)
    df = df.to_dict('records')
    return json.dumps({'reply':True,'df':df})


def delcondition(data):
    phu = crypto.decrypt(data['phu']) 
    if(db['users'].find_one({'phone':phu}) == None):
        return json.dumps({'reply':False,'msg':'خطاشناسایی کاربر لطفا مجددا وارد شوید'})
    db['conditions'].delete_many({'phone':phu,'_id':ObjectId(data['id'])})
    return json.dumps({'reply':True})

