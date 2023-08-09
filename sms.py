from melipayamak import Api


username = '9011010959'
password = '@8F20'

api = Api(username,password)
sms = api.sms()

def OTP(phone, CodeTxt):
    print(CodeTxt)
    sms.send_by_base_number(CodeTxt, phone, '154061')





#to = '09123456789'
#_from = '5000...'
#text = 'تست وب سرویس ملی پیامک'
#response = sms.send(to,_from,text)
