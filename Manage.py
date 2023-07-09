import json
import crypto
from ast import literal_eval
import pymongo
import datetime
from persiantools.jdatetime import JalaliDate
import cv2
from cryptography.fernet import Fernet
import base64
import random
import numpy as np
import string

client = pymongo.MongoClient()
db = client['RoundBourse']

userpass = {'username':'admin', 'password':'12345'}

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
   

def captchaGenerate():
    font = cv2.FONT_HERSHEY_COMPLEX
    captcha = np.zeros((40,140,3), np.uint8)
    captcha[:] = (255, 255, 255)#(random.randint(235,255),random.randint(245,255),random.randint(245,255))
    font= cv2.FONT_HERSHEY_SIMPLEX
    texcode = ''
    listCharector =  string.digits
    for i in range(1,5):
        bottomLeftCornerOfText = (random.randint(20,30)*i,35+(random.randint(-5,5)))
        fontScale= random.randint(5,12)/10
        fontColor= (random.randint(0,180),random.randint(50,180),random.randint(70,180))
        thickness= random.randint(1,2)
        lineType= random.randint(1,10)
        text = str(listCharector[random.randint(0,len(listCharector)-1)])
        texcode = texcode+(text)
        cv2.putText(captcha,text,bottomLeftCornerOfText,font,fontScale,fontColor,thickness,lineType)
        if random.randint(0,2)>0:
            pt1 = (random.randint(0,140),random.randint(0,40))
            pt2 = (random.randint(0,140),random.randint(0,40))
            lineColor = (random.randint(20,150),random.randint(40,150),random.randint(80,150))
            cv2.line(captcha,pt1,pt2,lineColor,1)
    stringImg = base64.b64encode(cv2.imencode('.jpg', captcha)[1]).decode()
    return [texcode,stringImg]



def captcha():
    cg = captchaGenerate()
    return json.dumps({'captcha':str(crypto.encrypt(cg[0])),'img':cg[1]})


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
    phone = crypto.decrypt(data['cookie'])
    lastcredit = db['users'].find_one({'phone':phone})['datecredit'].date()
    print(lastcredit)
    label = db['users'].find_one({'phone':phone})['label']
    userinfo = {'lastcredit':lastcredit, 'label':label }
    return json.dumps({'reply':True, 'userinfo':userinfo})



    
def userSetProfile(data):
    user = crypto.decrypt(data['phu'])
    data = data['data']
    db['users'].update_one({'phone':user},{'$set':data})
    return json.dumps({'reply':True})

    
def userGetProfile(data):
    user = crypto.decrypt(data['phu'])
    data = db['users'].find_one({'phone':user},{'_id':0,'dateregister':0,'datecredit':0})
    if data == None: return json.dumps({'reply':False,'msg':'اطلاعات کاربر یافت نشد'})
    return json.dumps({'reply':True,'data':data})

