import pymongo
import pandas as pd
import requests
import dateHandler
import time
import datetime
from bs4 import BeautifulSoup
import re
from persiantools import characters, digits

client = pymongo.MongoClient()
db = client['RoundBourse']

def extract_text_inside_parentheses(text):
    matches = re.findall(r'\((\D*?)\d*\)', text)
    return matches


def setTseToDb():
    df = pd.read_excel(requests.get('http://members.tsetmc.com/tsev2/excel/MarketWatchPlus.aspx?d=0',verify=False).content,header=2, engine='openpyxl')
    df = df[~df['نماد'].str.contains(r'\d')]
    df['نماد'] = df['نماد'].apply(characters.ar_to_fa)
    df['نام'] = df['نام'].apply(characters.ar_to_fa)
    #حذف حق تقدم ها
    df = df[~df['نماد'].str.endswith('ح')]
    blackSymbol = db['blackSymbol'].find({},{'symbol':1,'_id':0})
    blackSymbol = [x['symbol'] for x in blackSymbol]
    df = df[~df['نماد'].isin(blackSymbol)]
    df['data'] = dateHandler.toDayJalaliStr()
    df['dataInt'] = dateHandler.toDayJalaliInt()
    df['timestump'] = time.time()
    now = datetime.datetime.now()
    print('start',now)
    df['time'] = str(now.hour) +':'+str(now.minute)+':'+str(now.second)
    df = df.to_dict('records')
    db['tse'].delete_many({'dataInt':dateHandler.toDayJalaliInt()})
    db['tse'].insert_many(df)


def getPayamNazer():
    # دریافت محتوای صفحه HTML با استفاده از کتابخانه requests
    response = requests.get("http://old.tsetmc.com/Loader.aspx?ParTree=151313&Flow=0")
    # اطمینان حاصل از موفقیت دریافت صفحه
    if response.status_code != 200:
        raise Exception(f"خطا در دریافت صفحه: {response.status_code}")
    # ایجاد یک شیء BeautifulSoup برای پردازش صفحه HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    # لیست‌هایی برای ذخیره داده‌ها
    titles = []
    news_texts = []
    # پیدا کردن تمام تگ‌های tr در صفحه
    tr_tags = soup.find_all('tr')
    # پیمایش تمام تگ‌های tr و استخراج اطلاعات مورد نظر
    for i in range(0, len(tr_tags), 2):
        title_row = tr_tags[i]
        time_row = tr_tags[i+1]
        # استخراج عنوان
        title_th = title_row.find('th')
        title = title_th.text.strip() if title_th else None
        # استخراج متن خبر از تگ td
        news_td = time_row.find('td')
        news_text = news_td.text.strip() if news_td else None
        titles.append(title)
        news_texts.append(news_text)
    # ایجاد دیتافریم با اطلاعات استخراج شده
    df = pd.DataFrame({'Title': titles, 'News_Text': news_texts})
    lastDf = pd.DataFrame(db['payamNazer'].find({'date':dateHandler.toDayJalaliInt()}))
    if len(lastDf)>0:
        lastDf = lastDf['News_Text'].to_list()
        df['last'] = df['News_Text'].isin(lastDf)
        df = df[df['last']!=True]
        df = df.drop(columns=['last'])
    if len(df)>0:
        df['date'] = dateHandler.toDayJalaliInt()
        df['datetime'] = datetime.datetime.now()
        df['symbol'] = df['News_Text'].apply(extract_text_inside_parentheses)
        df['num_elements_symbol'] = df['symbol'].apply(len)
        df_list = []
        for i in df.index:
            if df['num_elements_symbol'][i] > 0:
                dff_list = [df.loc[[i]] for x in df['symbol'][i]]
                dff = pd.concat(dff_list)
                dff['symbol'] = df['symbol'][i]
                df_list.append(dff)
        if len(df_list)>0:
            df = pd.concat(df_list).reset_index()
            df = df.drop(columns=['num_elements_symbol','index'])
            df = df.to_dict('records')
            db['payamNazer'].insert_many(df)




while True:
    if dateHandler.isWorkDay():
        if dateHandler.isTimeOpenBourse():
            if dateHandler.minutePerFive():
                CheakingProcessTse = True
                CheakingProcessPayamNazer = True
                while CheakingProcessTse or CheakingProcessPayamNazer:
                    try:
                        if CheakingProcessTse:
                            setTseToDb()
                            CheakingProcessTse = False
                        if CheakingProcessPayamNazer:
                            getPayamNazer()
                            CheakingProcessPayamNazer = False
                        dilay = 60 - datetime.datetime.now().second
                        print('داده های دریافت شد کمتر از 60 ثانیه توقف')
                        time.sleep(dilay)
                    except:
                        print('اختلال در دریافت اطلاعات 3 ثانیه توقف')
                        time.sleep(3)
            else:
                print('دقیقه مناسب دریافت اطلاعات نیست (رند 5 دقیقه) 60 ثانیه توقف')
                dilay = 60 - datetime.datetime.now().second
                time.sleep(dilay)
        else:
            print('ساعت کار بازار نیست 5 دقیقه توقف')
            dilay = 60 - datetime.datetime.now().second
            time.sleep((60*4) + dilay)
    else:
        print('روز کاری بازار نیست 1 ساعت توقف')
        dilay = 60 - datetime.datetime.now().second
        time.sleep((60*59) + dilay)
