
import requests
import random
import pymongo
import datetime
import json
import ast
import crypto

client = pymongo.MongoClient()
db = client['RoundBourse']
token = 'lB-LRA7xf7eDZS7bi1G5HRWHgHiZIcw5i-Y8_fBEwxU'
url = 'https://api.payping.ir'


dicPrice= {
    'pro':{'1':1000,'3':3000,'6':6000,'12':12000},
    'proPlus':{'1':10000,'3':30000,'6':60000,'12':120000},
    'primium':{'1':100000,'3':300000,'6':600000,'12':1200000},
}

def CreatePayment(data):
    phone = crypto.decrypt(data['phu'])
    if db['users'].find_one({'phone':phone}) == None:
        return json.dumps({'replay':False,'msg':'خطا در احراز هویت لطفا مجدد وارد سیستم شوید'})
    amount = dicPrice[data['level']][str(data['period']['time'])]
    amount = 1000 # موقت برای توکن تست
    clientRefId = str(random.randint(100000,999999))
    dic ={'amount':int(amount),"payerIdentity":phone,"clientRefId":clientRefId,'date':datetime.datetime.now()}
    data = json.dumps({
        "amount": int(amount),
        "payerIdentity": phone,
        "returnUrl": "https://app.roundtrade.ir/returnpayment",
        "clientRefId": clientRefId
    })
    header = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    response = requests.post(url=url+'/v2/pay',data=data,headers=header)
    if response.status_code == 200:
        responseCode = ast.literal_eval(response.text)['code']
        dic['responseCode'] = responseCode
        db['payments'].insert_one(dic)
        return {'reply':True,'responseCode':responseCode}
    return {'reply':False,'msg':'خطا لطفا مجدد امتحان کنید یا با پشتیبانی تماس بگیرید'}

