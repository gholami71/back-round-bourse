import crypto
import pymongo
import json
import datetime
import random

client = pymongo.MongoClient()
db = client['RoundBourse']


def applyphone(data):
    captchacode = crypto.decrypt(data['CaptchaCode'])
    if captchacode != data['UserInput']['captcha']:
        return json.dumps({'reply':False})
    txt = random.randint(10000,99999)
    db['otp'].insert_one({'phone':data['UserInput']['phone'], 'codetext':str(txt), 'date':datetime.datetime.now()})
    print(txt)
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
               'label': 'Pro'
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
        info['creditDay'] = max(0,(credit.days+1))
    else:
        info['creditDay'] = max(0,(credit.days))
    del info['datecredit']
    if 'personality' in info.keys():
        if info['personality'] == 'true':
            info['name'] = info['fullName']
            del info['companyName']
        else:
            info['name'] = info['companyName']
            del info['fullName']
        del info['personality']

    if info['creditDay']==0:
        info['label'] = ''
    else:
        info['label'] = info['label'].replace('Pro','پرو').replace('ProPlus','پرو پلاس').replace('Premium','پریمیوم')
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
    print(data)
    return json.dumps({'reply':True,'data':data})


