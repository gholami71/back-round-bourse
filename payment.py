
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


error_messages = {
    1: "تراكنش توسط شما لغو شد",
    2: "رمز کارت اشتباه است.",
    3: "cvv2 یا تاریخ انقضای کارت وارد نشده است",
    4: "موجودی کارت کافی نیست.",
    5: "تاریخ انقضای کارت گذشته است و یا اشتباه وارد شده.",
    6: "کارت شما مسدود شده است",
    7: "تراکنش مورد نظر توسط درگاه یافت نشد",
    8: "بانک صادر کننده کارت شما مجوز انجام تراکنش را صادر نکرده است",
    9: "مبلغ تراکنش مشکل دارد",
    10: "شماره کارت اشتباه است.",
    11: "ارتباط با درگاه برقرار نشد، مجددا تلاش کنید",
    12: "خطای داخلی بانک رخ داده است",
    15: "این تراکنش قبلا تایید شده است",
    18: "کاربر پذیرنده تایید نشده است",
    19: "هویت پذیرنده کامل نشده است و نمی تواند در مجموع بیشتر از ۵۰ هزار تومان دریافتی داشته باشد",
    25: "سرویس موقتا از دسترس خارج است، لطفا بعدا مجددا تلاش نمایید",
    26: "کد پرداخت پیدا نشد",
    27: "پذیرنده مجاز به تراکنش با این مبلغ نمی باشد",
    28: "لطفا از قطع بودن فیلتر شکن خود مطمئن شوید",
    29: "ارتباط با درگاه برقرار نشد",
    31: "امکان تایید پرداخت قبل از ورود به درگاه بانک وجود ندارد",
    38: "آدرس سایت پذیرنده نا معتبر است",
    39: "پرداخت ناموفق، مبلغ به حساب پرداخت کننده برگشت داده خواهد شد",
    44: "RefId نامعتبر است",
    46: "توکن ساخت پرداخت با توکن تایید پرداخت مغایرت دارد",
    47: "مبلغ تراکنش مغایرت دارد",
    48: "پرداخت از سمت شاپرک تایید نهایی نشده است",
    49: "ترمینال فعال یافت نشد، لطفا مجددا تلاش کنید"
}

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
    dic ={'amount':int(amount),"payerIdentity":phone,"clientRefId":clientRefId,'date':datetime.datetime.now(),'period':data['period']['time'],'level':data['level']}
    data = json.dumps({
        "amount": int(amount),
        "payerIdentity": phone,
        "returnUrl": "https://api.roundtrade.ir/payment/verify",
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



def CheckPayment(data):
    phone = crypto.decrypt(data['phu'])
    print(data)
    if db['users'].find_one({'phone':phone}) == None:
        return json.dumps({'replay':False,'msg':'خطا در احراز هویت لطفا مجدد وارد سیستم شوید'})
    return json.dumps({'replay':False,'msg':'خطا در احراز هویت لطفا مجدد وارد سیستم شوید'})


def VerifyPeyment(code,refid,clientrefid,cardnumber,cardhashpan):
    peyment = db['payments'].find_one({'clientRefId':clientrefid})
    if peyment == None:
        return 'یافت نشد'
    db['payments'].update_one({'clientRefId':clientrefid},{'$set':{'refid':refid,'cardnumber':cardnumber,'cardhashpan':cardhashpan,'addenUser':False}})
    if int(refid)<=49:
        return error_messages[int(refid)]
    data = json.dumps({"refId": str(refid),"amount": int(peyment['amount'])})
    header = {'Content-Type': 'application/json','Authorization': f'Bearer {token}'}
    response = requests.post(url=url+'/v2/pay/verify',data=data,headers=header)
    if response.status_code != 200:
        return 'خطای ناشناخته'
    user = db['users'].find_one({'phone':peyment['payerIdentity']})
    label = str(user['label']).replace('ProPlus','2').replace('Premium','3').replace('Pro','1')
    if label not in ['1','2','3']: label = '0'
    label = int(label)
    level = str(peyment['level']).replace('ProPlus','2').replace('Premium','3').replace('Pro','1')
    if level not in ['1','2','3']: level = '0'
    level = int(level)
    if label>=level:
        datecredit = max(user['datecredit'],datetime.datetime.now())
        datecredit = datecredit + datetime.timedelta(days=int(peyment['period']*30))
    else:
        datecredit = datetime.datetime.now() + datetime.timedelta(days=int(peyment['period']*30))
    db['users'].update_one({'phone':peyment['payerIdentity']},{'$set':{'label':peyment['level'],'datecredit':datecredit}})
    db['payments'].update_one({'clientRefId':clientrefid},{'$set':{'addenUser':True}})
    return f'code:{code}\nrefid:{refid}\nclientrefid:{clientrefid}\ncardnumber:{cardnumber}\ncardhashpan:{cardhashpan}'
