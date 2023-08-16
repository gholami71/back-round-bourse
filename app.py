from flask import Flask,request
from flask_cors import CORS
import pymongo
import Manage
import client
import crypto
from waitress import serve
import setproctitle
import payment
clientDb = pymongo.MongoClient()
db = clientDb['RoundBourse']
app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def index():
    return 'Run server'

@app.route('/management/login', methods=['POST'])
def ManagementLogin():
    data = request.get_json()
    return Manage.login(data)

@app.route('/management/atuh', methods=['POST'])
def Managementatuh():
    data = request.get_json()
    return Manage.atuh(data)


@app.route('/management/getcalendar', methods=['POST'])
def Managementgetcalendar():
    data = request.get_json()
    return Manage.getcalendar(data)

@app.route('/management/setcalendar', methods=['POST'])
def Managementsetcalendar():
    data = request.get_json()
    return Manage.setcalendar(data)

@app.route('/management/delcalendar', methods=['POST'])
def Managementdelcalendar():
    data = request.get_json()
    return Manage.delcalendar(data)

@app.route('/managment/setreplyticket', methods=['POST'])
def ManagementSetReplyTicket():
    data = request.get_json()
    return Manage.setReplyTicket(data)


@app.route('/management/discount', methods=['POST'])
def ManagementDiscount():
    data = request.get_json()
    return Manage.Discount(data)


@app.route('/management/getdiscount', methods=['POST'])
def ManagementGetDiscount():
    data = request.get_json()
    return Manage.GetDiscount(data)

@app.route('/management/offdiscount', methods=['POST'])
def ManagementOffDiscount():
    data = request.get_json()
    return Manage.OffDiscount(data)

#این روت برای گرفتن کل اطلاعات کاربران برای پنل مدیریت است
@app.route('/management/getdataallusers', methods=['POST'])
def ManagementGetDataAllUsers():
    data = request.get_json()
    return Manage.getDataAllUsers(data)


#این روت برای گرفتن کل تیکت ها برای پنل مدیریت است
@app.route('/managment/gettickets', methods=['POST'])
def ManagementGetTickets():
    data = request.get_json()
    return Manage.getTickets(data)


@app.route('/user/usercaptcha', methods=['POST', 'GET'])
def captcha():
    return crypto.captcha()

@app.route('/user/applyphone', methods=['POST'])
def applyphone():
    data = request.get_json()
    return client.applyphone(data)

@app.route('/user/coderegistered', methods=['POST'])
def coderegistered():
    data = request.get_json()
    return client.coderegistered(data)

@app.route('/user/atuh', methods=['POST'])
def Useratuh():
    data = request.get_json()
    return client.Useratuh(data)

@app.route('/user/userinfo', methods=['POST'])
def userInfo():
    data = request.get_json()
    return client.userInfo(data)


@app.route('/user/setprofile', methods=['POST'])
def userSetProfile():
    data = request.get_json()
    return client.userSetProfile(data)

@app.route('/user/getprofile', methods=['POST'])
def userGetProfile():
    data = request.get_json()
    return client.userGetProfile(data)

@app.route('/user/setticket', methods=['POST'])
def userSetTicket():
    data = request.get_json()
    return client.setTicket(data)

@app.route('/user/getticket', methods=['POST'])
def userGetTicket():
    data = request.get_json()
    return client.getTicket(data)


@app.route('/user/delticket', methods=['POST'])
def userDelTicket():
    data = request.get_json()
    return client.delTicket(data)

@app.route('/user/setalarm', methods=['POST'])
def userSetAlarm():
    data = request.get_json()
    return client.userSetAlarm(data)

@app.route('/user/getalarm', methods=['POST'])
def userGettAlarm():
    data = request.get_json()
    return client.userGettAlarm(data)

@app.route('/user/getsymbols', methods=['POST'])
def userGetSymbol():
    data = request.get_json()
    return client.userGetSymbol(data)

@app.route('/user/delalarm', methods=['POST'])
def userDelAlarm():
    data = request.get_json()
    return client.userDelAlarm(data)

@app.route('/user/editalarm', methods=['POST'])
def userEditAlarm():
    data = request.get_json()
    return client.userEditAlarm(data)

@app.route('/user/getexplor', methods=['POST'])
def userGetexplor():
    data = request.get_json()
    return client.userGetexplor(data)

@app.route('/user/setcondition', methods=['POST'])
def setcondition():
    data = request.get_json()
    return client.setcondition(data)


@app.route('/payment/create', methods=['POST'])
def CreatePayment():
    data = request.get_json()
    return payment.CreatePayment(data)


@app.route('/payment/checkperpayment', methods=['POST'])
def CheckPayment():
    data = request.get_json()
    return payment.CheckPayment(data)



@app.route('/payment/verify', methods=['POST','GET'])
def VerifyPayment():
    code = request.form.get('code')
    refid = request.form.get('refid')
    clientrefid = request.form.get('clientrefid')
    cardnumber = request.form.get('cardnumber')
    cardhashpan = request.form.get('cardhashpan')
    return payment.VerifyPeyment(code,refid,clientrefid,cardnumber,cardhashpan)


if __name__ == '__main__':
    #setproctitle.setproctitle("BackEnd RoundTrade")
    #serve(app, host="0.0.0.0", port=2100,threads= 8)
    app.run(host='0.0.0.0', debug=True)




