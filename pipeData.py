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
    df = pd.read_excel(requests.get('http://members.tsetmc.com/tsev2/excel/MarketWatchPlus.aspx?d=0',verify=False).content,header=2)
    df = df[~df['نماد'].str.contains(r'\d')]
    df['نماد'] = df['نماد'].apply(characters.ar_to_fa)
    df['نام'] = df['نام'].apply(characters.ar_to_fa)
    df['data'] = dateHandler.toDayJalaliStr()
    df['dataInt'] = dateHandler.toDayJalaliInt()
    df['timestump'] = time.time()
    now = datetime.datetime.now()
    print('start',now)
    df['time'] = str(now.hour) +':'+str(now.minute)+':'+str(now.second)
    df = df.to_dict('records')
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
              setTseToDb()
              getPayamNazer()
              dilay = 60 - datetime.datetime.now().second
              time.sleep(dilay)
              print('Information received. I wait at most "60 seconds"')
          else:
              print('I took time, the information has not arrived, we will wait for "60 second" at most')
              dilay = 60 - datetime.datetime.now().second
              time.sleep(dilay)
      else:
          print('The working hours of the market are over. We will wait for "5 minutes" at most')
          dilay = 60 - datetime.datetime.now().second
          time.sleep((60*4) + dilay)
  else:
      print('The market is closed today, we will wait for "1 hour" at most')
      dilay = 60 - datetime.datetime.now().second
      time.sleep((60*59) + dilay)
