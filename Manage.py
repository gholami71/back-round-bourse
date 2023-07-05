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
    captcha = np.zeros((50,250,3), np.uint8)
    captcha[:] = (234, 228, 228)#(random.randint(235,255),random.randint(245,255),random.randint(245,255))
    font= cv2.FONT_HERSHEY_SIMPLEX
    texcode = ''
    listCharector =  string.digits
    for i in range(1,5):
        bottomLeftCornerOfText = (random.randint(35,45)*i,35+(random.randint(-8,8)))
        fontScale= random.randint(7,15)/10
        fontColor= (random.randint(0,180),random.randint(0,180),random.randint(0,180))
        thickness= random.randint(1,2)
        lineType= 1
        text = str(listCharector[random.randint(0,len(listCharector)-1)])
        texcode = texcode+(text)
        cv2.putText(captcha,text,bottomLeftCornerOfText,font,fontScale,fontColor,thickness,lineType)
        if random.randint(0,2)>0:
            pt1 = (random.randint(0,250),random.randint(0,50))
            pt2 = (random.randint(0,250),random.randint(0,50))
            lineColor = (random.randint(0,150),random.randint(0,150),random.randint(0,150))
            cv2.line(captcha,pt1,pt2,lineColor,1)
    #address = 'C:\\Users\\moeen\\Desktop\\project\\pishkar\\Front\\pishkar\\public\\captcha\\'+texcode+'.jpg'
    stringImg = base64.b64encode(cv2.imencode('.jpg', captcha)[1]).decode()
    return [texcode,stringImg]



def captcha():
    cg = captchaGenerate()
    return json.dumps({'captcha':str(crypto.encrypt(cg[0])),'img':cg[1]})


def applyphone(data):
    captchacode = crypto.decrypt(data['CaptchaCode'].decode())
    print(captchacode)
    return json.dumps({'reply':True})


def coderegistered(data):
    return json.dumps({'reply':True})



    

