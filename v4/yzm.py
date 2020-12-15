#!/usr/bin/env python3
# -*- coding:utf-8 -*- 
# author：yuanlang 
# creat_time: 2020/12/15 下午1:15
# file: yzm.py

import time
import requests
import threading
from scrapy import Selector
from common.proxy_helper import get_proxy
from concurrent.futures import ThreadPoolExecutor


img_dic = {}
running = True
count = 1
lock = threading.Lock()


def fetch():
    url = "https://ibaotu.com/index.php?m=downVarify&a=index&id=442418"
    response = requests.get(url, proxies=get_proxy())
    html = Selector(text=response.text)
    imgs = html.css(".imgs-wrap img::attr(src)").extract()
    for img_url in imgs:
        url = "https:" + img_url
        value = img_dic.get(url, 0)
        img_dic[url] = value + 1


def down():
    global running
    with ThreadPoolExecutor(max_workers=200) as t:
        while running:
            t.submit(fetch)
            with lock:
                global count
                print("当前下载第 {}次".format(count))
                if count >= 20000:
                    running = False
                else:
                    count = count + 1

    global img_dic
    with open("yzm.txt", "w") as f:
        for k, v in img_dic.items():
            f.writelines(k + "\n")


def download_img():
    with open("yzm.txt","r") as f:
        urls = f.readlines()

    urls = [url.replace("\n","") for url in urls]
    print(urls)
    print(len(urls))
    map = {}
    for url in urls:
        item = url.split(",")
        map[item[0].replace("https:","")] = item[1]
    print(map)

def sigle_test():
    for i in range(10000):
        url = "https://ibaotu.com/index.php?m=downVarify&a=index&id=442418"
        response = requests.get(url, proxies=get_proxy())
        html = Selector(text=response.text)
        imgs = html.css(".imgs-wrap img::attr(src)").extract()
        for img_url in imgs:
            url = "https:" + img_url
            print(url)
            value = img_dic.get(url, 0)
            img_dic[url] = value + 1
            # time.sleep(0.5)

# down()
download_img()

