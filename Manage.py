import json
import crypto
from ast import literal_eval
import pymongo
import datetime
from persiantools.jdatetime import JalaliDate
from cryptography.fernet import Fernet
import pandas as pd
import dateHandler
from bson import ObjectId

client = pymongo.MongoClient()
db = client['RoundBourse']

userpass = {'username':'moeen-azam', 'password':'dg123!@#'}

def login(data):
    if data['username'] == userpass['username'] and data['password']== userpass['password']:
        cryptUserPass = crypto.encrypt(str(userpass))
        return json.dumps({'reply':True, 'uph':cryptUserPass})
    
    return json.dumps({'reply':False})

def atuh(data):
    try:
        userpassword = literal_eval(crypto.decrypt(data['key']))
        if userpassword['username'] == userpass['username'] and userpassword['password']== userpass['password']:
            return json.dumps({'reply':True})
        return json.dumps({'reply':False})
    except:
        return json.dumps({'reply':False})
    

def getcalendar(data):  
    if atuh(data) == False:
        return json.dumps({'reply':False})   
    df = db['calendar'].find({},{'_id':0})
    df = [x['holiday'] for x in df]

    print(df)
    return json.dumps({'reply':True, 'df':df})

def setcalendar(data):  
    if atuh(data) == False:
        return json.dumps({'reply':False})
    date =int(data['date'])/1000
    date = datetime.datetime.fromtimestamp(date)
    date = str(JalaliDate(date)).replace('-','/')
    calander = db['calendar'].find_one({'holiday': date})
    if calander !=None:
        return json.dumps({'reply':False, 'msg':'تاریخ تکراری است'}) 
    db['calendar'].insert_one({'holiday':date})  
    return json.dumps({'reply':True})   

def delcalendar(data):
    if atuh(data) == False:
        return json.dumps({'reply':False, 'msg':'خطا '})
    date = data['date']
    db['calendar'].delete_one({'holiday':date})

    return json.dumps({'reply':True})   
   

def getDataAllUsers(data):
    '''
    این تابع برای گرفتن کل اطلاعات کاربران است
    data: شامل کلید است
    '''
    #این کلید را چک میکند که خود مدیر باشد
    if atuh(data) == False:
        return json.dumps({'reply':False, 'msg':'خطا '})
    df = pd.DataFrame(db['users'].find())
    # ستون ایدی رو تبدیل به رشته میکنیم برای اینکه بتوان به جیسون تبدیل شود
    df['_id'] = df['_id'].astype(str)
    # ستون های که شامل تاریخ هستند رو تبدیل  تاریخ جلالی و سپس به رشته تبدیل میکنم برای اینکه بتوان به جیسون تبدیل شود
    for i in ['dateregister','datecredit','lastlogin']:
        if i in df.columns:
            df[i] = [dateHandler.toJalaliStr(x) for x in df[i]]
    df = df.to_dict('records')
    return json.dumps({'reply':True, 'df':df})



def getTickets(data):
    if atuh(data) == False:
        return json.dumps({'reply':False, 'msg':'خطا '})
    df = pd.DataFrame(db['support'].find())
    if len(df)>0:
        df['_id'] = [str(x) for x in df['_id']]
        df['time'] = [str(x).split(' ')[1].split('.')[0] for x in df['date']]
        df['dateJalali'] = [dateHandler.toJalaliStr(x) for x in df['date']]
        df = df.drop(columns=['date'])
        df = df.to_dict('records')
        return json.dumps({'reply':True, 'df':df})
    else:
        return json.dumps({'reply':True, 'df':[]})


def setReplyTicket(data):
    if atuh(data) == False:
        return json.dumps({'reply':False, 'msg':'خطا '})
    data = data['ansewr']
    db['support'].update_one({'_id':ObjectId(data['_id'])},{'$set':{'reply':data['reply']}})
    return json.dumps({'reply':True})

def Discount(data):
    if atuh(data) == False:
        return json.dumps({'reply':False, 'msg':'خطا '})
    del data['key']
    data['date'] = datetime.datetime.fromtimestamp(int(data['date'])/1000)
    if data['type'] == 'percent':
        data['value'] = min(int(data['value']),100)
    check = db['discount'].find_one({'code':data['code']})
    if check != None:
        return json.dumps({'reply':False, 'msg':'این کد قبلا ثبت شده'})
    data['use'] = 0
    db['discount'].insert_one(data)
    return json.dumps({'reply':True, 'msg':'ثبت شد '})


def GetDiscount(data):
    if atuh(data) == False:
        return json.dumps({'reply':False, 'msg':'خطا '})
    df = pd.DataFrame(db['discount'].find({}))
    if len(df)==0:
        return json.dumps({'reply':False, 'msg':'کد تخفیف خالی است '})
    df['date'] = df['date'].apply(dateHandler.toJalaliStr)
    df['_id'] = df['date'].apply(str)
    df['type'] = df['type'].replace('toman','تومان').replace('percent','درصد')
    df = df.to_dict('records')
    return json.dumps({'reply':True, 'df':df})
