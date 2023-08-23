
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
tokenZibal = 'zibal' #'64d8b8bcc3e074001c9e452a'
creat_url = 'https://gateway.zibal.ir/v1/request'
return_url = 'http://localhost:5000/payment/verify'#'https://api.roundtrade.ir/payment/verify'


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
                code = code['code']
            else:code = ''
        else:code = ''
    else:code = ''
    
    #برای خرید هایی که با کد تخفیف مبلغ خریدشون صفر میشه باید یه فکری برداشت
    if amount == 0:pass

    clientRefId = str(random.randint(100000,999999))
    dic ={'amount':int(amount),"payerIdentity":phone,"clientRefId":clientRefId,'date':datetime.datetime.now(),'period':data['period']['time'],'level':data['period']['level'],'discount':code,'addenUser':False}
    print(dic)
    data = json.dumps({
        "merchant":tokenZibal,
        "amount": int(amount)*10,
        "callbackUrl": return_url,
        "orderId": clientRefId,
        "mobile": phone,
    })
    header = {'Content-Type': 'application/json'}
    response = requests.post(url=creat_url,data=data,headers=header)
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
                dic['pricePayInt'] = int(int(dic['priceBaseInt']) * (1-value))
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
        discount = db['discount'].find_one({'code':peyment['discount']})
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
    db['users'].update_one({'phone':peyment['payerIdentity']},{'$set':{'label':peyment['level'],'datecredit':datecredit}})
    db['payments'].update_one({'clientRefId':order_id},{'$set':{'addenUser':True}})
    dicres = {'status':True,'msg':'تراکنش موفق'}
    return render_template('returnPayment.html',dicres=dicres)


