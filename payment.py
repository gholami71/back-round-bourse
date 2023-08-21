
import requests
import random
import pymongo
import datetime
import json
import ast
import crypto
from persiantools import characters, digits
import dateHandler

from flask import render_template
client = pymongo.MongoClient()
db = client['RoundBourse']
token = 'lB-LRA7xf7eDZS7bi1G5HRWHgHiZIcw5i-Y8_fBEwxU' #ADbi9S7g-Yo4sJOHNthFoo3-CQvEhYbFbcPnjC6Gfcw
tokenZibal = '64d8b8bcc3e074001c9e452a'
urlToken = 'https://gateway.zibal.ir/v1/request'
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
    'pro':{'1':36000,'3':107000,'6':208000,'12':390000},
    'proplus':{'1':67000,'3':197000,'6':383000,'12':718000},
    'premium':{'1':263000,'3':774000,'6':1500000,'12':2808000},
}

def CreatePayment(data):
    phone = crypto.decrypt(data['phu'])
    if db['users'].find_one({'phone':phone}) == None:
        return json.dumps({'replay':False,'msg':'خطا در احراز هویت لطفا مجدد وارد سیستم شوید'})
    amount = dicPrice[data['period']['level']][str(data['period']['time'])]
    if data['code'] != '':
        code = db['discount'].find_one({'code':data['code']})
        if code != None:
            if datetime.datetime.now() < code['date'] and int(code['count'])>int(code['use']):
                if code['type'] == 'percent':
                    amount = int((1-(int(code['value'])/100)) * amount)
                    amount = max(amount , 0)
                else:
                    amount = amount - int(code['value'])
                    amount = max(amount , 0)
            else:
                code = ''
        else:
            code = ''
    else:
        code = ''
    if amount == 0:
        pass

    #amount = 1000 # موقت برای توکن تست
    clientRefId = str(random.randint(100000,999999))
    dic ={'amount':int(amount),"payerIdentity":phone,"clientRefId":clientRefId,'date':datetime.datetime.now(),'period':data['period']['time'],'level':data['period']['level'],'discount':code,'addenUser':False}
    data = json.dumps({
        "merchant":tokenZibal,
        "amount": int(amount)*10,
        "callbackUrl": "https://api.roundtrade.ir/payment/verify",
        "orderId": clientRefId,
        "mobile": phone,
    })

    header = {'Content-Type': 'application/json'}

    response = requests.post(url=urlToken,data=data,headers=header)
    
    if response.status_code == 200:
        responseCode = ast.literal_eval(response.text)['trackId']
        dic['responseCode'] = responseCode
        db['payments'].insert_one(dic)
        return {'reply':True,'responseCode':responseCode}
    
    return {'reply':False,'msg':'خطا لطفا مجدد امتحان کنید یا با پشتیبانی تماس بگیرید'}





def CheckPayment(data):
    phone = crypto.decrypt(data['phu'])
    user = db['users'].find_one({'phone':phone})
    if user == None:
        return json.dumps({'reply':False,'msg':'خطا در احراز هویت لطفا مجدد وارد سیستم شوید'})
    try:
        dic = {'label':int(str(data['data']['level']).replace('proplus','2').replace('premium','3').replace('pro','1'))}
        dic['labelName'] = str(data['data']['level']).replace('proplus','پروپلاس').replace('premium','پریمیوم').replace('pro','پرو')
        dic['period'] = str(data['data']['time']).replace('12','یکساله').replace('1','یکماهه').replace('2','دوماهه').replace('3','سه ماهه').replace('6','شش ماهه')
        dic['priceBaseInt'] = dicPrice[data['data']['level']][data['data']['time']]
        dic['priceBaseHorof'] = digits.to_word(dicPrice[data['data']['level']][data['data']['time']])
    except:
        return json.dumps({'reply':False,'msg':'خطا در تشخیص بسته لطفا مجددا بسته اشتراک را انتخاب کنید'})
    if len(data['code'])>0:
        code = db['discount'].find_one({'code':data['code']})
        if code == None:
            dic['pricePayInt'] = dic['priceBaseInt']
            dic['pricePayHorof'] = dic['priceBaseHorof']
            dic['codeMsg'] = 'کد تخفیف یافت نشد'
            dic['codestatus'] = False
        elif datetime.datetime.now() > code['date']:
            dic['pricePayInt'] = dic['priceBaseInt']
            dic['pricePayHorof'] = dic['priceBaseHorof']
            dic['codeMsg'] = 'کد تخفیف منقضی شده است'
            dic['codestatus'] = False
        elif int(code['count'])<=int(code['use']):
            dic['pricePayInt'] = dic['priceBaseInt']
            dic['pricePayHorof'] = dic['priceBaseHorof']
            dic['codeMsg'] = 'ظرفیت مصرف کد تخفیف تمام شده است'
            dic['codestatus'] = False
        else:
            dic['codestatus'] = True
            if code['type'] == 'percent':
                value = code['value']
                dic['codeMsg'] = f'{value} % تخفیف اعمال خواهد شد'
                value = int(value)/100
                dic['pricePayInt'] = int(dic['priceBaseInt'] * (1-value))
                dic['pricePayHorof'] = digits.to_word(dic['pricePayInt'])
            else:
                value = code['value']
                dic['codeMsg'] = f'{value} تومان تخفیف اعمال خواهد شد'
                dic['pricePayInt'] = int(dic['priceBaseInt'] - int(value))
                dic['pricePayHorof'] = digits.to_word(dic['pricePayInt'])
    else:
        dic['pricePayInt'] = dic['priceBaseInt']
        dic['pricePayHorof'] = dic['priceBaseHorof']
        dic['codeMsg'] = ''
        dic['codestatus'] = False

    label = str(user['label']).replace('proplus','2').replace('premium','3').replace('pro','1')
    if label not in ['1','2','3']: label = '0'
    label = int(label)
    level = dic['label']
    if level not in ['1','2','3',1,2,3]: level = '0'
    level = int(level)
    if label>=level:
        datecredit = max(user['datecredit'],datetime.datetime.now())
        addenDay = int(data['data']['time'])*31
        datecredit = datecredit + datetime.timedelta(days=addenDay)
        dic['resetCredit'] = False
    else:
        datecredit = datetime.datetime.now() + datetime.timedelta(days=int(data['data']['time'])*31)
        dic['resetCredit'] = True
    dic['credit'] = dateHandler.toJalaliStr(datecredit)

    return json.dumps({'reply':True,'df':dic})

def VerifyPeyment(track_id,success,status,order_id):
    peyment = db['payments'].find_one({'clientRefId':order_id})
    print(peyment)
    if peyment == None:
        dicres = {'status':False,'msg':'تراکنش یافت نشد'}
        return render_template('returnPayment.html',dicres=dicres)
    if 'addenUser' in peyment.keys():
        if peyment['addenUser']== True:
            dicres = {'status':False,'msg':'تراکنش تکراری و قبلا ثبت شده است'}
            return render_template('returnPayment.html',dicres=dicres)
    db['payments'].update_one({'clientRefId':order_id},{'$set':{'refid':track_id,'success':success,'status':status,'addenUser':False}})
    if int(success)==0:
        dicres = {'status':False,'msg':'خرید نا موفق'}
        return render_template('returnPayment.html',dicres=dicres)

    if len(peyment['discount'])>0:
        discount = db['discount'].find_one({'discount':peyment['discount']})
        if discount == None:
            dicres = {'status':False,'msg':'کد تخفیف یافت نشد'}
            return render_template('returnPayment.html',dicres=dicres)
        use = int(discount['use'])+1
        db['discount'].update_one({'discount':peyment['discount']},{'$set':{'use':use}})

    data = json.dumps({"merchant": tokenZibal,"trackId": track_id})
    header = {'Content-Type': 'application/json'}
    response = requests.post(url='https://gateway.zibal.ir/v1/verify',data=data,headers=header)
    if response.status_code != 200:
        dicres = {'status':False,'msg':'خطای نامشخص لطفا مجدد تلاش کنید یا با پشتیبانی تماس حاصل کنید'}
        return render_template('returnPayment.html',dicres=dicres)
    user = db['users'].find_one({'phone':peyment['payerIdentity']})
    label = str(user['label']).replace('proplus','2').replace('premium','3').replace('pro','1')
    if label not in ['1','2','3']: label = '0'
    label = int(label)
    level = str(peyment['level']).replace('proplus','2').replace('premium','3').replace('pro','1')
    if level not in ['1','2','3']: level = '0'
    level = int(level)
    if label>=level:
        datecredit = max(user['datecredit'],datetime.datetime.now())
        addenDay = int(peyment['period'])*31
        datecredit = datecredit + datetime.timedelta(days=addenDay)
    else:
        datecredit = datetime.datetime.now() + datetime.timedelta(days=int(peyment['period'])*31)
    print(label)
    db['users'].update_one({'phone':peyment['payerIdentity']},{'$set':{'label':peyment['level'],'datecredit':datecredit}})
    db['payments'].update_one({'clientRefId':order_id},{'$set':{'addenUser':True}})
    dicres = {'status':True,'msg':'تراکنش موفق'}
    return render_template('returnPayment.html',dicres=dicres)


