import crypto
import pymongo
import json
import datetime
import random
import pandas as pd
import dateHandler
from bson import ObjectId
import sms

client = pymongo.MongoClient()
db = client['RoundBourse']

limit = {'alarms':{'pro':10, 'proplus':20, 'premium':40}}

def AllowExplor(data):
    try:
        user = crypto.decrypt(data['phu'])
    except:
        return {'reply':False,'msg':'ورود با مشکل مواجه شده است لطفا مجددا وارد شوید'}
    print(user)
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
    data = data['inp']
    print(data)
    if data['type'] == 'indicator':
        if data['indicator'] == 'rsi':
            df =0
    return json.dumps({'reply':False})


def setcondition(data):  
    credit = AllowExplor(data)
    if credit['reply'] == False:
        return json.dumps(credit)
 
    label_user = credit['user']['label']
    count_condition = db['conditions'].count_documents({'phone':credit['user']['phone']})
    label = {'pro':1,'proplus':3, 'premium':9}  
    print(count_condition)
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
    print(data)
    db['conditions'].delete_many({'phone':phu,'_id':ObjectId(data['id'])})
    return json.dumps({'reply':True})

