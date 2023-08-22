import requests
import pandas as pd
from persiantools.jdatetime import JalaliDate
import datetime
from persiantools import characters, digits
import pymongo
import analysis
import matplotlib.pyplot as plt

client = pymongo.MongoClient()
db = client['RoundBourse']



url = 'https://gateway.zibal.ir/v1/request'

