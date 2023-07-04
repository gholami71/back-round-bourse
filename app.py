from flask import Flask,request
from flask_cors import CORS
import pymongo
import Manage

client = pymongo.MongoClient()
db = client['RoundBourse']
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)




