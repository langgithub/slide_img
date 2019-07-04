# encoding: utf-8
"""
--------------------------------------
@describe 模拟数据包发送
@version: 1.0
@project: test
@file: huakuai.py
@author: yuanlang
@time: 2019-04-23 19:11
---------------------------------------
"""
import re
import json
import random
import time
import math
import numpy as np
import requests
from io import BytesIO
from PIL import Image
from scrapy import Selector

# 滑块宽度
slide_w = 45
session=requests.session()


def calculate_slider_offset(img1, img2):
    """
    计算滑动距离
    :param img1: 原图片
    :param img2: 背景图片
    :return:
    """
    w1, h1 = img1.size
    w2, h2 = img2.size
    if w1 != w2 or h1 != h2:
        return False
    left = 0
    for i in range(slide_w, w1):
        if column_similar(img1, img2, i, h1):
            left = i
            break
    return left


def column_similar(img1, img2, x, height):
    """
    在y轴上是否相同
    :param img1:
    :param img2:
    :param x:
    :param height:
    :return:
    """
    for j in range(0, height):
        if is_pixel_equal(img1, img2, x, j):
            return True
    return False


def is_pixel_equal(img1, img2, x, y):
    """
    某个点的像素值是否相同
    :param img1:
    :param img2:
    :param x:
    :param y:
    :return:
    """
    pix1 = img1.load()[x, y]
    pix2 = img2.load()[x, y]
    # R G B 小于60为黑色
    if abs(pix1[0] - pix2[0] < 60) and abs(pix1[1] - pix2[1] < 60) and abs(pix1[2] - pix2[2] < 60):
        # 不相同
        return False
    else:
        # 相同
        return True


def network_to_file(url: str):
    index = url.rfind("/") + 1
    # print(url[index:])
    reponse = session.get(url)
    with open(url[index:], "wb") as f:
        f.write(reponse.content)


def network_to_io(url: str):
    reponse = session.get(url)
    img = Image.open(BytesIO(reponse.content))
    return img


def sigmoid(x, slide_left):
    # 直接返回sigmoid函数
    return slide_left / (1. + np.exp(-x))


def sigmoid_floor(x, slide_left):
    # 直接返回sigmoid函数
    return slide_left / (1. + np.exp(-x))


def plot_sigmoid(time, slide_left):
    """
    模拟鼠标轨迹方程
    :param time: 花费时间
    :param slide_left: 滑块移动距离
    :return:
    """
    x = np.arange(-time, time, 0.1)
    y = sigmoid(x, slide_left)
    return x, y


def random_index(rate):
    """随机变量的概率函数"""
    #
    # 参数rate为list<int>
    # 返回概率事件的下标索引
    start = 0
    index = 0
    randnum = random.randint(1, sum(rate))

    for index, scope in enumerate(rate):
        start += scope
        if randnum <= start:
            break
    return index


def mouse_time():
    """
    mouseTime
    :return:
    """
    # 时间数组
    arr = [7, 8, 9]
    # 时间对应出现概率
    rate = [1, 8, 1]

    def random_rap():
        """更具概率随机时间"""
        return arr[random_index(rate=rate)]

    time_list = []
    start_time = math.floor(time.time() * 1000)
    for i in range(40):
        start_time = random_rap() + start_time
        time_list.append(start_time)
    return time_list


def ying_she(time_list, current=8):
    """
    把时间压缩到0-8的区间
    公式 ： y=（8/（max-min））*（x-min）
    :return:
    """
    max = time_list[0]
    min = time_list[len(time_list) - 1]
    x_list = []
    for i in range(len(time_list) - 1, 0, -1):
        y = (current / (max - min)) * (time_list[i] - min)
        x_list.append(y)
    return np.array(x_list)


def first_data():
    global session
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36"
    }
    response_login = session.get("http://busi.epicc.com.cn/login", headers=headers)
    html = Selector(text=response_login.text)
    challenge = html.css("#challengeID::attr(value)").extract_first()
    jsoncallback = "jQuery111006172527293042014_1556084569011"
    base_url = "http://busi.epicc.com.cn/slidecaptcha/initCaptcha.code?"
    url = base_url + "challenge=" + challenge + "&jsoncallback=" + jsoncallback
    response_change=session.get(url,headers=headers)
    regex=re.compile(jsoncallback+"\((.*?)\)")
    group=regex.findall(response_change.text)
    data=json.loads(group[0])
    print(data)
    return challenge,data


def second_data():
    challenge,data=first_data()
    jsoncallback = "jQuery111006172527293042014_1556084569011"
    backImg="http://busi.epicc.com.cn"+data["captcha"]["backImg"]
    grapImg="http://busi.epicc.com.cn"+data["captcha"]["grapImg"]
    grayBackImg="http://busi.epicc.com.cn"+data["captcha"]["grayBackImg"]
    slideImg="http://busi.epicc.com.cn"+data["captcha"]["slideImg"]

    # network_to_file(backImg)
    # network_to_file(grapImg)
    # network_to_file(grayBackImg)
    # network_to_file(slideImg)

    img1=network_to_io(grapImg)
    img2=network_to_io(grayBackImg)
    left = math.floor(calculate_slider_offset(img1, img2) * 0.9367) - 12
    print(left)
    # 生成时间
    mouseTime = mouse_time()
    # 生成移动距离
    current_x = ying_she(mouseTime) - 4  # 整体偏移
    pageXAxis = np.floor(sigmoid_floor(current_x, left)).tolist()
    pageYAxis = [378] * 40
    typeMouse = [""]*40

    print(challenge)
    print(left)
    typeMouse=",".join(typeMouse)
    print(type(typeMouse),typeMouse)
    pageXAxis=",".join([str(math.floor(x)+585) for x in pageXAxis])
    print(pageXAxis)
    pageYAxis=",".join([str(math.floor(x)) for x in pageYAxis])
    print(pageYAxis)
    mouseTime=",".join([str(math.floor(x)) for x in mouseTime])
    print(mouseTime)

    pageX=str(int(data['captcha']['slideX'])-1)

    slidecaptcha=f"http://busi.epicc.com.cn/slidecaptcha/checkCaptcha.code?challenge={challenge}&pageX={pageX}" \
                 f"&typeMouse={typeMouse}&pageXAxis={pageXAxis}&pageYAxis={pageYAxis}&mouseTime={mouseTime}" \
                 f"&jsoncallback={jsoncallback}"

    print(slidecaptcha)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36"
    }
    response=session.get(slidecaptcha,headers=headers)
    print(response.text)

def test():
    img1 = Image.open("grap5.png")
    img2 = Image.open("grayBack.png")
    # 滑动距离=取整（计算网络流中两张图片的滑动距离值 * （html中实际图片的宽/网络图片的宽））- html中slide滑块距离便宜
    left = math.floor(calculate_slider_offset(img1, img2) * 0.9367) - 12
    print(math.floor(left))
    # 生成时间
    mouseTime = mouse_time()
    # 生成移动距离
    current_x = ying_she(mouseTime) - 4  # 整体偏移
    pageXAxis = np.floor(sigmoid_floor(current_x, math.floor(left))).tolist()
    pageYAxis = [378] * 40

    return mouseTime, pageXAxis, pageYAxis


second_data()

"""
//js debugger
orig = window.startRecord;
window.startRecord=function(str){
    orig(str);
    console.log('-----------typeMouse------------');
    console.log(typeMouse);
    console.log('-----------pageXAxis------------');
    console.log(pageXAxis);
    console.log('-----------pageYAxis------------');
    console.log(pageYAxis);
    console.log('-----------mouseTime------------');
    console.log(mouseTime)
}
"""
# url = "http://busi.epicc.com.cn/hdyz/images_slide/jiaoyu/grayBack.png"
# url="http://busi.epicc.com.cn/hdyz/images_slide/zijiayou/slide5.png"
# network_to_file(url)
