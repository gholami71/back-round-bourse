from flask import Flask,request
from flask_cors import CORS
import pymongo
import Manage
import client
import crypto

clientDb = pymongo.MongoClient()
db = clientDb['RoundBourse']
app = Flask(__name__)
CORS(app)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)




