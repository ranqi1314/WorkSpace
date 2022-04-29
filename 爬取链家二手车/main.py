import codecs
import csv
import json
import os
import time
import random
import requests
import xlwt
import openpyxl
import pandas as pd
import pymysql
from copyheaders import headers_raw_to_dict
from lxml import html
from sqlalchemy import create_engine

etree = html.etree

def speedprogress():
    scale = 50
    print("开始数据清理".center(scale // 2, "-"))
    start = time.perf_counter()
    for i in range(scale + 1):
        a = '*' * i
        b = '.' * (scale - i)
        c = (i / scale) * 100
        dur = time.perf_counter() - start
        print("\r{:^3.0f}%[{}->{}]{:.2f}s".format(c, a, b, dur), end='')
        time.sleep(0.1)
    print("\n" + "清理完成！".center(scale // 2, '-'))

def get_regions(headers):
    print('开始获取地区列表:')
    url = 'https://cd.lianjia.com/ershoufang/'
    r = requests.get(url, headers=headers)
    r_tr = etree.HTML(r.text)
    # print(r.text)
    regions=[]
    regions_false = r_tr.xpath('//div[@data-role="ershoufang"]//a/@href')
    for region in regions_false:
        regions.append('https://cd.lianjia.com'+region)
    regions_true = r_tr.xpath('//div[@data-role="ershoufang"]//a/text()')
    print('获取完成')
    return regions, regions_true


def get_houses(headers):
    regions, regions_true=get_regions(headers)
    num=1
    for region,region_true in zip(regions,regions_true):
        for i in range(2):
            print(f'开始获取成都{region_true}，第{i+1}页：',end='\t')
            url=region+'pg'+str(i)
            r = requests.get(url, headers=headers)
            r_tr = etree.HTML(r.text)
            prices = []
            list_houses=[]
            dict_houses={}
            # 户型 面积 朝向 装修 楼层 时间 楼型
            bases = r_tr.xpath(
                '//div[@class="leftContent"]//ul[@class="sellListContent"]//li//div[@class="info clear"]//div[@class="address"]//div[@class="houseInfo"]/text()')
            # 单平价格
            price_all = r_tr.xpath(
                '//div[@class="leftContent"]//ul[@class="sellListContent"]//li//div[@class="info clear"]//div[@class="priceInfo"]//div[@class="unitPrice"]//span/text()')
            for price in price_all:
                if '参考价:' in price:
                    price = price.replace('参考价:', '')
                    if ',' in price:
                        price = price.replace(',', '')
                    price = price.strip()
                    price = price[:-3]
                    prices.append(price)
            # 标题
            titles = r_tr.xpath(
                '//div[@class="leftContent"]//ul[@class="sellListContent"]//li//div[@class="info clear"]//div[@class="title"]//a/text()')
            # 合并
            for base, price, title in zip(bases, prices, titles):
                base = str(base)
                base = base.split('|')
                temp = [region_true, title]
                for i in base:
                    i = i.strip()
                    temp.append(i)
                if len(temp) < 9:
                    continue
                temp.append(price)
                temp[3] = temp[3][:-2]
                total = round(float(temp[3]) * int(temp[9]), 2)
                temp.append(total)
                # 存入列表
                dict_houses['region'] = temp[0]
                dict_houses['title'] = temp[1]
                dict_houses['class'] = temp[2]
                dict_houses['area'] = temp[3]
                dict_houses['direction'] = temp[4]
                dict_houses['renovation'] = temp[5]
                dict_houses['floor']=temp[6]
                dict_houses['time'] = temp[7]
                dict_houses['building'] = temp[8]
                dict_houses['price'] = temp[9]
                dict_houses['total'] = temp[10]
                list_houses.append(dict_houses.copy())
            print(f'获取完成!共{len(list_houses)}条数据！')
            time.sleep(3)
            get_save_xls(list_houses,num)
            get_save_csv(list_houses)
            get_pymysql_mysql(list_houses)
            get_pandas_mysql(list_houses)
            num=num+len(list_houses)


def get_save_xls(list_houses,num):
    print('保存至表格......', end='')
    wb = openpyxl.load_workbook('data.xlsx')
    table=wb.active
    for i in range(len(list_houses)):
        table.append(
            [i+num, list_houses[i]['region'], list_houses[i]["title"], list_houses[i]["class"], list_houses[i]["direction"], list_houses[i]["direction"], list_houses[i]["renovation"], list_houses[i]["floor"], list_houses[i]["time"],list_houses[i]["building"], list_houses[i]["price"],list_houses[i]["total"]])

    wb.save('data.xlsx')
    print('表格保存完成......')
def get_save_csv(list_houses):
    print('保存至csv......', end='')
    header =['region','title','class','area','direction','renovation','floor','time','building','price','total']
    with open('data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
    with open('data.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writerows(list_houses)
    print('csv保存完成......')
    time.sleep(10)
def get_pymysql_mysql(list_houses):
    """
    通过pymysql将csv写入mysql
    """
    print('通过pymysql将csv写入mysql......', end='')
    db = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'db': 'houses_1',
        'charset': 'utf8'
    }
    conn = pymysql.connect(**db)
    cursor = conn.cursor()
    with open('data.csv', 'r', encoding='utf-8') as f:
        read = csv.reader(f)
        for i in list(read)[1:]:
            x = tuple(i)
            sql = "INSERT INTO car VALUES" + str(x)
            cursor.execute(sql)
        conn.commit()
        cursor.close()
        conn.close()
    print('写入成功！')
def get_pandas_mysql(list_houses):
    """
    通过pandas将csv写入mysql
    """
    print('通过pandas将csv写入mysql......', end='')
    engine = create_engine("mysql+pymysql://root:123456@127.0.0.1:3306/houses_1", echo=False, pool_size=10,
                           max_overflow=20)
    df = pd.read_csv('data.csv')
    df.index.name = "id"
    df.to_sql(name="hourse_id", con=engine, if_exists="replace")
    print('写入成功！')

if __name__ == '__main__':
    num=1
    print('程序执行开始......')
    speedprogress()
    #表格
    if os.path.exists('data.xlsx'):
        os.remove('data.xlsx')
    wb=openpyxl.Workbook()
    table=wb.active
    table.append(['id','region','title','class','area','direction','renovation','floor','time','building','price','total'])
    wb.save('data.xlsx')
    #CSV
    if os.path.exists('data.csv'):
        os.remove('data.csv')

    headers = b'''
    Cookie: lianjia_uuid=41ac64c8-49bc-48d3-b336-8941e2bba868; select_city=510100; lianjia_ssid=d5897cf6-ae77-4d52-a693-a8df9c91106e; _jzqc=1; _jzqy=1.1651041096.1651041096.1.jzqsr=baidu.-; _jzqckmp=1; UM_distinctid=18069b7d1fa48b-0fca92d400b6cf-6b3e555b-144000-18069b7d1fb1268; sajssdk_2015_cross_new_user=1; _smt_uid=6268e348.2b5f37a7; _ga=GA1.2.1667364023.1651041098; _gid=GA1.2.379739704.1651041098; gr_user_id=d74134a8-f7df-418c-aad5-1dba6ef4a4c8; Hm_lvt_9152f8221cb6243a53c83b956842be8a=1651041109; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2218069b7d28a2ba-00daaa780a3c89-6b3e555b-1327104-18069b7d28b11c2%22%2C%22%24device_id%22%3A%2218069b7d28a2ba-00daaa780a3c89-6b3e555b-1327104-18069b7d28b11c2%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22%22%2C%22%24latest_referrer_host%22%3A%22%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%7D%7D; login_ucid=2000000239818951; lianjia_token=2.0013f0e5c8773ed0e3025dccf93a9f5c7d; lianjia_token_secure=2.0013f0e5c8773ed0e3025dccf93a9f5c7d; security_ticket=JW9qs8Nb+0ADLZyj8r4a2dZF7tW7/ACweZmYTZthHNLP+vrf18m0YyRTK2FnMEbAIhUkq+jiiZX0sT+UrDMv3SVPvOUARaC5x24Zkj8dcMDXWpm/tuMQBVzjiJgs+jbVQt1/2fycbfpmeBSFew0rHBJ1aO8OtY0GHkH9XMM/xnw=; gr_session_id_a1a50f141657a94e=f96c92cf-3fbc-4650-ab0d-2b471d63f957; _jzqa=1.3496520880349231600.1651041096.1651041096.1651048254.2; gr_session_id_a1a50f141657a94e_f96c92cf-3fbc-4650-ab0d-2b471d63f957=true; Hm_lpvt_9152f8221cb6243a53c83b956842be8a=1651049867; _jzqb=1.4.10.1651048254.1; _gat=1; _gat_past=1; _gat_global=1; _gat_new_global=1; _gat_dianpu_agent=1
    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'''
    headers = headers_raw_to_dict(headers)
    get_houses(headers)
    time.sleep(10)
    print('程序执行完毕！')
