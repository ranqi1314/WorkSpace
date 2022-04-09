import codecs
import csv
import json
import os
import time
import requests
import xlwt
import pandas as pd
import pymysql
from lxml import html
from sqlalchemy import create_engine

etree = html.etree

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/99.0.4844.84 Safari/537.36 ',
    'Cookie': 'sessionid=76ef5116-009b-4050-9f1c-71b5d6cc50ac; fvlid=1649167378486TzdWICccvHFV; '
              'che_sessionid=20532853-EAC8-4ACC-8CEE-BF63D0E48531%7C%7C2022-04-05+22%3A02%3A48.169%7C%7C0; '
              'carDownPrice=1; listuserarea=0; sessionip=222.212.179.27; area=510114; '
              'sessionvisit=d1350d91-98ad-4414-b403-4ea67b3c387a; '
              'sessionvisitInfo=76ef5116-009b-4050-9f1c-71b5d6cc50ac||0; '
              'Hm_lvt_d381ec2f88158113b9b76f14c497ed48=1649167379,1649227294; '
              'che_sessionvid=7ED975AF-C925-4F63-890B-D73A6776AF08; SessionSeries=0; userarea=440300; showNum=35; '
              'Hm_lpvt_d381ec2f88158113b9b76f14c497ed48=1649229621; ahuuid=4C5FB467-C2D8-42E9-9638-961CC57A1F05; '
              'v_no=14; visit_info_ad=20532853-EAC8-4ACC-8CEE-BF63D0E48531||7ED975AF-C925-4F63-890B-D73A6776AF08||-1'
              '||-1||14; che_ref=0%7C0%7C0%7C0%7C2022-04-06+15%3A20%3A08.742%7C2022-04-05+22%3A02%3A48.169; '
              'sessionuid=76ef5116-009b-4050-9f1c-71b5d6cc50ac; ahpvno=38; '
              'UsedCarBrowseHistory=0%3A41603275%2C0%3A42427805%2C0%3A43298029%2C0%3A40678120%2C0%3A42806697%2C0'
              '%3A42879514 ',
    'Host': 'www.che168.com'
}


def get_area_pinyin():
    if not os.path.exists('area.txt'):
        url = 'https://www.che168.com/china/a0_0msdgscncgpi1ltocsp1exx0/?pvareaid=100943'
        r_txt = requests.get(url, headers=headers).text
        r_tr = etree.HTML(r_txt)
        area_list = r_tr.xpath('//div[@class="topbar-citypop-scity"]//span[@class="tx"]/a/@areapy')
        area_list = area_list[1:]
        if os.path.exists('area.txt'):
            os.remove('area.txt')
        with open('area.txt', 'w+') as f:
            for area in area_list:
                f.write(area)
                f.write('\n')
        print('保存成功！')
    return
def get_cat_url_false(area,page):
    url_list = []
    print(f'\t开始爬取第{page}页......', end='')
    url = 'https://www.che168.com/' + area.strip() + '/a0_0msdgscncgpi1ltocsp' + str(
        page) + 'exx0/?pvareaid=102179'
    r_txt = requests.get(url, headers=headers).text
    r_tr = etree.HTML(r_txt)
    cars_url = r_tr.xpath(
        '//div[@class="tp-cards-tofu fn-clear"]//ul[@class="viewlist_ul"]//li[@class="cards-li list-photo-li "]/a/@href')
    for car_url in cars_url:
        url_list.append(car_url)
    print(f'第{page}页爬取完成......',end='')
    return url_list
def get_cat_url_true(url_list):
    """
    获取每一辆车的url(正确格式)
    """
    print('调整url反扒格式......',end='')
    for i in range(len(url_list)):
        if url_list[i].startswith('https://topicm.che168.com/'):
            del url_list[i]
        if not url_list[i].startswith('//www.che168.com'):
            url_list[i] = '//www.che168.com' + url_list[i]
        url_list[i] = 'https:' + url_list[i]
    print('调整完成......',end='')
    if os.path.exists('url.txt'):
        os.remove('url.txt')
    with open('url.txt', 'a') as f:
        for url in url_list:
            f.write(url)
            f.write('\n')
    return url_list
def get_cat_info(url_list):
    car_list = []
    car_dict = {}
    print(f'开始独立请求......',end='')
    print(f'保存至列表......', end='')
    for url in url_list:
        car_txt = requests.get(url, headers=headers).text
        car_tr = etree.HTML(car_txt)
        # 0 车名
        car_name = car_tr.xpath('//div[@class="car-box"]/h3/text()')
        if car_name == []:
            continue
        car_name = (''.join(car_name)).strip()
        # 1 里程
        car_mile = car_tr.xpath('//ul[@class="brand-unit-item fn-clear"]/li[1]/h4/text()')
        car_mile = ''.join(car_mile)
        car_mile = int(float(car_mile[0:car_mile.rfind('万')]) * 10000)
        # 2 上牌时间
        car_time = car_tr.xpath('//ul[@class="brand-unit-item fn-clear"]/li[2]/h4/text()')
        car_time = ''.join(car_time)
        car_time = car_time.replace('年', '-')
        car_time = car_time.replace('月', '')
        # 3 挡位/排量
        car_gear_and_output = car_tr.xpath('//ul[@class="brand-unit-item fn-clear"]/li[3]/h4/text()')
        car_gear_and_output = (''.join(car_gear_and_output)).strip()
        # 4 所在地
        car_area = car_tr.xpath('//ul[@class="brand-unit-item fn-clear"]/li[4]/h4/text()')
        car_area = (''.join(car_area)).strip()
        # 5 价格
        car_price = car_tr.xpath('//span[@class="price"]/text()')
        if car_price == ['万']:
            car_price = car_tr.xpath('//div[@class="goodstartmoney"]/text()')
        car_price = (''.join(car_price)).strip()
        car_price = car_price[1:]
        car_price = car_price.replace('万', '')
        car_price = (''.join(car_price)).strip()
        car_price = int(float(car_price) * 10000)
        # 存入字典
        # name,mile,time,go,area,price
        car_dict['name'] = car_name
        car_dict['mile'] = car_mile
        car_dict['time'] = car_time
        car_dict['go'] = car_gear_and_output
        car_dict['area'] = car_area
        car_dict['price'] = car_price
        car_list.append(car_dict.copy())
        print(f'{url_list.index(url)}', end=' ')
        time.sleep(1)
    print('保存完成......', end='')
    return car_list

def get_save_xls(car_list):
    """
    把信息保存至表格
    """
    print('保存至表格......', end='')
    if os.path.exists('data.xls'):
        os.remove('data.xls')
    file = xlwt.Workbook()
    table = file.add_sheet('sheet name')
    table.write(0, 0, "id")
    table.write(0, 1, "name")
    table.write(0, 2, "mile")
    table.write(0, 3, "time")
    table.write(0, 4, "go")
    table.write(0, 5, "area")
    table.write(0, 6, "price")
    for i in range(len(car_list)):
        table.write(i + 1, 0, i + 1)
        table.write(i + 1, 1, car_list[i]['name'])
        table.write(i + 1, 2, car_list[i]['mile'])
        table.write(i + 1, 3, car_list[i]['time'])
        table.write(i + 1, 4, car_list[i]['go'])
        table.write(i + 1, 5, car_list[i]['area'])
        table.write(i + 1, 6, car_list[i]['price'])
    file.save('data.xls')
    print('表格保存完成......',end='')
def get_save_csv(car_list):
    """
    保存至csv
    """
    print('保存至csv......', end='')
    if os.path.exists('data.csv'):
        os.remove('data.csv')
    header = ["name", "mile", "time", "go", "area", "price"]
    with open('data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
    with open('data.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writerows(car_list)
    print('csv保存完成......',end='')
    time.sleep(10)
def get_pymysql_mysql(car_list):
    """
    通过pymysql将csv写入mysql
    """
    print('通过pymysql将csv写入mysql......', end='')
    db = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '123456',
        'db': 'car',
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
def get_pandas_mysql(car_list):
    """
    通过pandas将csv写入mysql
    """
    print('通过pandas将csv写入mysql......', end='')
    engine = create_engine("mysql+pymysql://root:123456@127.0.0.1:3306/car", echo=False, pool_size=10,
                           max_overflow=20)
    df = pd.read_csv('data.csv')
    df.index.name = "id"
    df.to_sql(name="car_id", con=engine, if_exists="replace")
    print('写入成功！')

def get_cat():
    count = 0
    get_area_pinyin()
    with open('area.txt', 'r') as f1:
        area_count=0
        for area in f1:
            print(f'选择地区：{area.strip()}')
            for page in range(1, 3):
                sum = 0
                url_list=[]
                # 获取每页所有url（伪）
                url_list=get_cat_url_false(area, page)
                # 调整所有url（真）
                url_list = get_cat_url_true(url_list)
                sum += (len(url_list))
                area_count += (len(url_list))
                count+=(len(url_list))
                car_list = get_cat_info(url_list)
                print(f'共{sum}辆')
                get_save_xls(car_list)
                get_save_csv(car_list)
                get_pymysql_mysql(car_list)
                get_pandas_mysql(car_list)
                time.sleep(3)
            print(f'\t地区:{area.strip()}，共计{area_count}辆')
        print(f'所有地区共记{count}辆')


if __name__ == '__main__':
    print('程序执行开始......')
    get_cat()
    print('程序执行完毕！')
