import os
import time

import requests
from lxml import html

etree = html.etree

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
    'cookie': '__yjs_duid=1_1a45793d5aa2979e92c575f9bec383ae1649303373012; Hm_lvt_c59f2e992a863c2744e1ba985abaea6c=1649411483,1649413132,1649428194,1649477782; PHPSESSID=25hgpihtnu79u83vd4vopa2d47; zkhanmlusername=%D2%BB%C3%D7%C1%F9%B5%C4%C8%BE%C6%E2; zkhanmluserid=5866185; zkhanmlgroupid=1; zkhanmlrnd=yrUivX3UvX4jAkxtlpV4; zkhanmlauth=3dd6e02cd6942bc96c88accb6493d1d1; Hm_lpvt_c59f2e992a863c2744e1ba985abaea6c=1649479148; yjs_js_security_passport=273f64c5da9a3a62c18e8dfbef351a0a4b7b09e9_1649481526_js',
    'host': 'pic.netbian.com'
}


def get_classify():
    url = 'https://pic.netbian.com/'
    r = requests.get(url, headers=headers)
    r.encoding = r.apparent_encoding
    r_tr = etree.HTML(r.text)
    classify = r_tr.xpath('/html/body/div[1]/div/ul/li[2]/div/a/@href')
    classify_url_list = []
    for url in classify:
        url = 'https://pic.netbian.com' + url
        classify_url_list.append(url)
    classify_name_list = r_tr.xpath('/html/body/div[1]/div/ul/li[2]/div/a/@title')
    classify_name_dict = dict(zip(num_list, classify_name_list))
    classify_url_dict = dict(zip(num_list, classify_url_list))
    return classify_name_dict, classify_url_dict


def get_classify_page(classify_url_dict):
    classify_page_list = []
    for i in range(0, 12):
        r_txt = requests.get(classify_url_dict[i], headers=headers).text
        r_tr = etree.HTML(r_txt)
        classify_page = r_tr.xpath('/html/body/div[2]/div/div[4]/a[7]/text()')
        classify_page = ''.join(classify_page)
        classify_page_list.append(classify_page)
    classify_page_list[-3] = 5
    classify_page_dict = dict(zip(num_list, classify_page_list))
    return classify_page_dict


def get_url_false(url):
    pic_url_flase = []
    r = requests.get(url, headers=headers)
    r.encoding = r.apparent_encoding
    r_tr = etree.HTML(r.text)
    pic_url = r_tr.xpath('/html/body/div[2]/div/div[3]/ul/li/a/@href')
    for url in pic_url:
        url = 'https://pic.netbian.com' + url
        pic_url_flase.append(url)
    return pic_url_flase


def get_url_true(pic_url_flase):
    url_list = []
    name_list = []
    for url in pic_url_flase:
        print(f'{(pic_url_flase.index(url)+1)}', end=' ')
        r = requests.get(url, headers=headers)
        r.encoding = r.apparent_encoding
        r_tr = etree.HTML(r.text)
        pic_url = r_tr.xpath('/html/body/div[2]/div[1]/div[2]/div[1]/div[2]/a/img/@src')
        pic_name = r_tr.xpath('/html/body/div[2]/div[1]/div[2]/div[1]/div[2]/a/img/@title')
        for url, name in zip(pic_url, pic_name):
            url_list.append('https://pic.netbian.com' + url)
            name_list.append(name)
    return url_list, name_list

def get_save_pic(url_list, name_list):
    for url, name in zip(url_list, name_list):
        r_content = requests.get(url, headers=headers).content
        pic_path = path +'/'+ name+'.jpg'
        with open(pic_path, 'wb') as file:
            file.write(r_content)

def get_url(num, page):
    page_url_list = []
    page_url_list.append(classify_url_dict[num])
    for i in range(2, page + 1):
        url = classify_url_dict[num] + 'index_' + str(i) + '.html'
        page_url_list.append(url)
    for url in page_url_list:
        print(f'\n\t爬取第{(page_url_list.index(url) + 1)}页:', end='')
        pic_url_flase = get_url_false(url)
        pic_url, pic_name=get_url_true(pic_url_flase)
        get_save_pic(pic_url, pic_name)





if __name__ == '__main__':
    start = time.time()
    num_list = [i for i in range(0, 12)]
    classify_name_dict, classify_url_dict = get_classify()
    classify_page_dict = get_classify_page(classify_url_dict)
    print(f'{"-" * 100}')
    for i in range(0, 12):
        if i == 6:
            print(f'{i}:{classify_name_dict[i]}')
        print(f'{i}:{classify_name_dict[i]}', end=' ')
    print(f'\n{"-" * 100}')
    num = int(input('请输入你想要爬取类别的编号：'))
    print(f'\t你选择的类别是{classify_name_dict[num]},共{classify_page_dict[i]}页')
    if not os.path.exists('./pic'):
        os.mkdir('./pic')
    path = './pic/' + classify_name_dict[num]
    if not os.path.exists(path):
        os.mkdir(path)
    page = int(input('请输入你想要爬取的页数:'))
    print('开始爬取：', end='')
    get_url(num, page)
    print('\n爬取完成！')
