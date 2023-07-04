import json
import crypto
from ast import literal_eval
import pymongo
import datetime
from persiantools.jdatetime import JalaliDate

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
    
    print(date)
    calander = db['calendar'].find_one({'holiday': date})
    if calander !=None:
        return json.dumps({'reply':False, 'msg':'تاریخ تکراری است'}) 

    db['calendar'].insert_one({'holiday':date})  
   
    print(date)  
    return json.dumps({'reply':True})   

def delcalendar(data):
    if atuh(data) == False:
        return json.dumps({'reply':False, 'msg':'خطا '})
    
    date = data['date']
    db['calendar'].delete_one({'holiday':date})
    print(data)
    
    return json.dumps({'reply':True})   
   
    

