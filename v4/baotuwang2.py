# -*- coding: utf-8 -*-
import io
import base64
import numpy as np
import pickle
import requests
import urllib3

from scrapy import Selector
from abc import ABCMeta, abstractmethod
from PIL import Image, ImageChops
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

urllib3.disable_warnings()

class ErrorLog(object):

    def __init__(self, bg, full, diff, offset):
        self.bg = bg
        self.full = full
        self.diff = diff
        self.offset = offset


class BaseGeetestCrack(metaclass=ABCMeta):
    """验证码破解基础类"""

    def __init__(self, driver):
        self.driver = driver
        self.driver.maximize_window()
        self.error:ErrorLog = None

    def get_decode_image(self, filename, location_list):
        """
        解码base64数据
        :param filename: 图片名称
        :param location_list: 图片内容
        :return:
        """
        _, img = location_list.split(",")
        img = base64.decodebytes(img.encode())
        new_im: Image = Image.open(io.BytesIO(img))
        new_im.convert("RGB")
        new_im.save(filename)
        return new_im

    @abstractmethod
    def crop_captcha_image2(self):
        """返回两张图片"""
        pass

    @abstractmethod
    def calculate_slider_offset(self):
        """计算两张图片的滑动距离"""
        pass

    def get_browser_name(self):
        return str(self.driver).split('.')[2]

    @abstractmethod
    def crack(self):
        pass

    def ease_out_quad(self, x):
        return 1 - (1 - x) * (1 - x)

    def ease_out_quart(self, x):
        return 1 - pow(1 - x, 4)

    def ease_out_expo(self, x):
        if x == 1:
            return 1
        else:
            return 1 - pow(2, -10 * x)

    def get_tracks_2(self, distance, seconds, ease_func):
        """
        根据轨迹离散分布生成的数学生成  # 参考文档  https://www.jianshu.com/p/3f968958af5a
        成功率很高 90% 往上
        :param distance: 缺口位置
        :param seconds:  时间
        :param ease_func: 生成函数
        :return: 轨迹数组
        """
        distance += 20
        tracks = [0]
        offsets = [0]
        for t in np.arange(0.0, seconds, 0.1):
            ease = ease_func
            offset = round(ease(t / seconds) * distance)
            tracks.append(offset - offsets[-1])
            offsets.append(offset)
        tracks.extend([-3, -2, -3, -2, -2, -2, -2, -1, -0, -1, -1, -1])
        return tracks

    def move_to_gap(self, track, element_class="btn_slide"):
        """移动滑块到缺口处"""
        slider = self.driver.find_element_by_class_name(element_class)
        ActionChains(self.driver).click_and_hold(slider).perform()

        while track:
            x = track.pop(0)
            ActionChains(self.driver).move_by_offset(xoffset=x, yoffset=0).perform()
            time.sleep(0.02)

        ActionChains(self.driver).release().perform()

    def compute_gap(self, img1, img2):
        """计算缺口偏移 这种方式成功率很高"""
        # 将图片修改为RGB模式
        img1 = img1.convert("RGB")
        img2 = img2.convert("RGB")

        # 计算差值
        diff = ImageChops.difference(img1, img2)

        # 灰度图
        diff = diff.convert("L")
        # print(self.otsu_threshold(diff))

        table = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        # 二值化 阀值table提前计算好的
        diff = diff.point(table, '1')
        # diff.save("last.png")

        left = 43

        # for w in range(left, diff.size[0]):
        #     lis = []
        #     for h in range(diff.size[1]):
        #         if diff.load()[w, h] == 1:
        #             lis.append(w)
        #         if len(lis) > 5:
        #             self.error = ErrorLog(img1, img2, diff, w)
        #             return w
        for w in range(diff.size[0]-1,left,-1):
            lis = []
            for h in range(diff.size[1]-1,0,-1):
                if diff.load()[w, h] == 1:
                    lis.append(w)
                if len(lis) > 5:
                    self.error = ErrorLog(img1, img2, diff, w)
                    return w-left


    # 测试获取阀值 https://www.jianshu.com/p/c7fb9be02412
    def otsu_threshold(self, im):
        """确认阀值的大致范围"""
        width, height = im.size
        pixel_counts = np.zeros(256)
        for x in range(width):
            for y in range(height):
                pixel = im.getpixel((x, y))
                pixel_counts[pixel] = pixel_counts[pixel] + 1
        # 得到图片的以0-255索引的像素值个数列表
        s_max = (0, -10)
        for threshold in range(256):
            # 遍历所有阈值，根据公式挑选出最好的
            # 更新
            w_0 = sum(pixel_counts[:threshold])  # 得到阈值以下像素个数
            w_1 = sum(pixel_counts[threshold:])  # 得到阈值以上像素个数

            # 得到阈值下所有像素的平均灰度
            u_0 = sum([i * pixel_counts[i] for i in range(0, threshold)]) / w_0 if w_0 > 0 else 0

            # 得到阈值上所有像素的平均灰度
            u_1 = sum([i * pixel_counts[i] for i in range(threshold, 256)]) / w_1 if w_1 > 0 else 0

            # 总平均灰度
            u = w_0 * u_0 + w_1 * u_1

            # 类间方差
            g = w_0 * (u_0 - u) * (u_0 - u) + w_1 * (u_1 - u) * (u_1 - u)

            # 类间方差等价公式
            # g = w_0 * w_1 * (u_0 * u_1) * (u_0 * u_1)

            # 取最大的
            if g > s_max[1]:
                s_max = (threshold, g)
        return s_max[0]


# -*- coding: utf-8 -*-
import functools
import random
import time
from common.logger import logger
from selenium import webdriver


class BTCGeetestCrack(BaseGeetestCrack):
    """比特币滑动验证码破解类"""

    def __init__(self, driver, is_login):
        super().__init__(driver)
        self.is_login = is_login
        self.seeds_dict = {}
        self.headers = {}
        self.session = requests.session()

    def init_page(self):
        self.driver.get("https://ibaotu.com/")
        # js = "document.getElementsByClassName('mobile-New')[0].style.bottom=0;"
        # self.driver.execute_script(js)
        if self.is_login:
            cookies = pickle.load(open("cookies.pkl", "rb"))
            cookie_str = ""
            for cookie in cookies:
                # adding the cookies to the session through webdriver instance
                self.driver.add_cookie(cookie)
                cookie_str += cookie["name"]+"="+cookie["value"]+";"
            if cookie_str != "":
                cookie_str = cookie_str[:-1]
                self.headers.update({"Host": "ibaotu.com",
                                     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
                                     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                                     "Accept-Encoding": "gzip, deflate, br",
                                     "Accept-Language": "zh-CN,zh;q=0.9",
                                     "Connection": "keep-alive",
                                     "Sec-Fetch-Site": "same-origin",
                                     "Sec-Fetch-Mode": "navigate",
                                     "Sec-Fetch-Dest": "document",
                                     "Cookie": cookie_str})

    def release_cookie(self):
        cookies = pickle.load(open("cookies.pkl", "rb"))
        cookie_str = ""
        self.driver.delete_all_cookies()
        for cookie in cookies:
            # adding the cookies to the session through webdriver instance
            self.driver.add_cookie(cookie)
            cookie_str += cookie["name"]+"="+cookie["value"]+";"
        if cookie_str != "":
            cookie_str = cookie_str[:-1]
            self.headers.update({"Host": "ibaotu.com",
                                 "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
                                 "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                                 "Accept-Encoding": "gzip, deflate, br",
                                 "Accept-Language": "zh-CN,zh;q=0.9",
                                 "Connection": "keep-alive",
                                 "Sec-Fetch-Site": "same-origin",
                                 "Sec-Fetch-Mode": "navigate",
                                 "Sec-Fetch-Dest": "document",
                                 "Cookie": cookie_str})

    def input_login_pre(self, element_class="login"):
        input_el = self.driver.find_element_by_css_selector(element_class)
        input_el.click()
        time.sleep(1)

    def input_login(self, element_class="auth-type-Phone"):
        input_el = self.driver.find_element_by_css_selector(element_class)
        input_el.click()
        time.sleep(3.5)

    def input_login2(self, element_class="li.login-compatible-click"):
        input_el = self.driver.find_element_by_css_selector(element_class)
        input_el.click()
        time.sleep(0.5)

    def input_user(self, text="15120096850", element_class="#mo-phone"):
        input_el = self.driver.find_element_by_css_selector(element_class)
        input_el.clear()
        input_el.send_keys(text)
        time.sleep(0.5)

    def input_by_pwd(self, text="assbcd123", element_class="#mo-veri"):
        input_el = self.driver.find_element_by_css_selector(element_class)
        input_el.clear()
        sms = input("短信验证码:\n")
        input_el.send_keys(sms)
        time.sleep(0.5)

    def click_by_id(self, element_class="phone-login-but"):
        search_el = self.driver.find_element_by_class_name(element_class)
        search_el.click()
        time.sleep(3)

    def crop_captcha_image2(self):
        fullbg_js = 'return document.getElementsByClassName("geetest_canvas_bg geetest_absolute")[0].toDataURL("image/png")'
        fullbg = self.driver.execute_script(fullbg_js)  # 调用js方法，同时执行javascript脚本

        bg_js = 'return document.getElementsByClassName("geetest_canvas_fullbg geetest_fade geetest_absolute")[0].toDataURL("image/png")'
        bg = self.driver.execute_script(bg_js)  # 调用js方法，同时执行javascript脚本
        return fullbg, bg

    def calculate_slider_offset(self):
        time.sleep(0.5)
        bimg1, bimg2 = self.crop_captcha_image2()
        img1 = self.get_decode_image("fullbg.png", bimg1)
        img2 = self.get_decode_image("bg.png", bimg2)
        return self.compute_gap(img2, img1)

    def check_response(self):
        """检查是否成功"""
        pickle.dump(self.driver.get_cookies(), open("cookies.pkl","wb"))

    def crack(self):
        """执行破解程序
        """
        self.init_page()
        if not self.is_login:
            # self.input_login_pre()
            # self.input_login()
            # self.input_login2()
            # self.input_user()
            # # 滑块
            # x_offset = 300
            #
            # print(x_offset)
            # track = self.get_tracks_2(x_offset, random.randint(2, 4), self.ease_out_quart)
            # print("滑动轨迹", track)
            # print("滑动距离", functools.reduce(lambda x, y: x + y, track))
            # self.move_to_gap(track)
            # time.sleep(2)
            #
            # self.input_by_pwd()
            # self.click_by_id()

            OK = input("ok")
            if OK != "ok":
                return
            self.check_response()
        else:
            # https://ibaotu.com/tupian/guanggaosheji.html
            # https://ibaotu.com/tupian/guanggaosheji/2.html
            self.driver.get("https://ibaotu.com/tupian/guanggaosheji/2.html")
            time.sleep(2)

            html = Selector(text=self.driver.page_source)
            all_dls = html.css("div.bt-body dl")
            for dl in all_dls:
                id = dl.css("dl::attr(pr-data-id)").extract()[0]
                title = dl.css("dl::attr(pr-data-title)").extract()[0].replace("<strong>", "").replace("</strong>", "")
                self.seeds_dict[id] = title
            print(self.seeds_dict)
            for k, v in self.seeds_dict.items():
                url = "https://ibaotu.com/?m=download&id={}&isSearch=1&kwd=%E5%B9%BF%E5%91%8A%E8%AE%BE%E8%AE%A1".format(k)
                is_click = False
                while 1:
                    self.driver.get(url)
                    time.sleep(1)
                    if is_click:
                        # 开始过验证码
                        if "downVarify" in self.driver.current_url:
                            self.yanzhengma()
                        else:
                            # 点击直接下载
                            self.driver.get(
                                "https://ibaotu.com/?m=download&id={}&isSearch=1&kwd=%E5%B9%BF%E5%91%8A%E8%AE%BE%E8%AE%A1".format(
                                    k))
                            input_el = self.driver.find_element_by_id("downvip")
                            input_el.click()
                            time.sleep(2)
                            if "downVarify" in self.driver.current_url:
                                self.yanzhengma()

                        self.check_response()
                        self.release_cookie()

                    # or 获取下载地址
                    download_url = "https://ibaotu.com/?m=downloadopen&a=open&id={}&down_type=1&attachment_id=&team_down=1".format(k)
                    print(download_url)
                    response_zip = self.session.get(url=download_url, headers=self.headers, stream=True,
                                                    allow_redirects=False, verify=False)
                    if "此图片您已经下载过啦" in response_zip.text:
                        print("{}此图片您已经下载过啦".format(k))
                        time.sleep(2)
                        break
                    Location = response_zip.headers.get("Location")
                    print(Location)
                    time.sleep(3)
                    if ".zip" not in Location:
                        url = "https:"+Location
                        # 点击直接下载
                        is_click = True
                    else:
                        break

    def yanzhengma(self):
        is_over = False
        while not is_over:
            yzm = {'//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08240': '异', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082z0M1g2O0O0O1O0O0O5': '阵', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08200M1g2O0O0O1O0O0O5': '欧', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08200N1w2O0O0O1O0O0O5': '透', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08210M1g2O0O0O1O0O0O5': '笑', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1D2g1O0O0O5': '泽', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1T2g1O0O0O5': '池', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1j2M1O0O0O5': '君', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1z2U1O0O0O5': '德', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082z0N1Q2O0O0O1O0O0O5': '威', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08210N1w2O0O0O1O0O0O5': '穗', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08210O1Q2O0O0O1O0O0O5': '汉', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08220M1Q2O0O0O1O0O0O5': '绿', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08220N1Q2O0O0O1O0O0O5': '秋', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08220O1Q2O0O0O1O0O0O5': '疗', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08240N1A2O0O0O1O0O0O5': '藏', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08250O1A2O0O0O1O0O': '0O5择', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1j2c1O0O0O5': '恩', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1w2O0O0O1O0O0O5': '乡', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08200N1g2O0O0O1O0O0O5': '清', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08210O1A2O0O0O1O0O0O5': '楚', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08250M1Q2O0O0O1O0O0O5': '探', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1j2Q1O0O0O5': '止', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1z2A1O0O0O5': '煦', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1z2M1O0O0O5': '吉', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1z2c1O0O0O5': '祥', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082z0N1g2O0O0O1O0O0O5': '附', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08220N1g2O0O0O1O0O0O5': '遍', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08240N1w2O0O0O1O0O0O5': '壳', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08240O1A2O0O0O1O0O0O5': '迎', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1T2M1O0O0O5': '潮', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1T2k1O0O0O5': '船', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1z2I1O0O0O5': '兴', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1z2k1O0O0O5': '杰', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082y0O1A2O0O0O1O0O0O5': '芽', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08210N1g2O0O0O1O0O0O5': '企', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08230N1w2O0O0O1O0O0O5': '替', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1D2M1O0O0O5': '烟', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1D2c1O0O0O5': '耕', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1D2k1O0O0O5': '慢', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1z2E1O0O0O5': '熹', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1D2I1O0O0O5': '宇', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08220': '讯', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1A2O0O0O1O0O0O5': '龟', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08230M1Q2O0O0O1O0O0O5': '州', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1j2E1O0O0O5': '乐', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1j2Y1O0O0O5': '圣', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1D2E1O0O0O5': '智', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082w0': '游', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082y0M1g2O0O0O1O0O0O5': '垓', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082y0N1g2O0O0O1O0O0O5': '补', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08230M1w2O0O0O1O0O0O5': '吹', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08250O1Q2O0O0O1O0O0O5': '礼', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1D2Y1O0O0O5': '渐', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082y0O1Q2O0O0O1O0O0O5': '永', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082z0M1A2O0O0O1O0O0O5': '瓦', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1D2Q1O0O0O5': '句', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08200': '域', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08230': '辉', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082z0M1Q2O0O0O1O0O0O5': '倾', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1D2g1O0O0O5': '鸿', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082z0': '伍', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08210': '甚', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1g2O0O0O1O0O0O5': '夜', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08220N1A2O0O0O1O0O0O5': '既', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08230N1Q2O0O0O1O0O0O5': '铜', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08240N1Q2O0O0O1O0O0O5': '隙', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08250M1g2O0O0O1O0O0O5': '临', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082y0N1A2O0O0O1O0O0O5': '欢', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082z0N1A2O0O0O1O0O': '0O5演', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1z2Y1O0O0O5': '纯', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1D2Q1O0O0O5': '豪', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1D2U1O0O0O5': '贤', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0O1A2O0O0O1O0O0O5': '映', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082y0N1Q2O0O0O1O0O0O5': '铁', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082z0O1Q2O0O0O1O0O0O5': '永', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08200N1Q2O0O0O1O0O0O5': '洋', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1T2Q1O0O0O5': '横', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1Q2O0O0O1O0O0O5': '纸', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1w2O0O0O1O0O0O5': '兰', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08230M1A2O0O0O1O0O0O5': '井', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08240M1g2O0O0O1O0O0O5': '措', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08240M1w2O0O0O1O0O0O5': '贯', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08250N1Q2O0O0O1O0O0O5': '善', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1D2c1O0O0O5': '宏', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082z0O1A2O0O0O1O0O0O5': '芽', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1T2c1O0O0O5': '希', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08250M1A2O0O0O1O0O0O5': '粘', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08250M1w2O0O0O1O0O0O5': '薄', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08250N1g2O0O0O1O0O0O5': '福', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1D2E1O0O0O5': '伏', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1D2U1O0O0O5': '纯', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082y0': '央', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08230N1g2O0O0O1O0O0O5': '沿', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08240M1Q2O0O0O1O0O0O5': '悟', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1z2Q1O0O0O5': '泰', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1z2g1O0O0O5': '佳', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082z0M1w2O0O0O1O0O0O5': '碳', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08210N1A2O0O0O1O0O0O5': '束', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08230N1A2O0O0O1O0O0O5': '荣', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1j2U1O0O0O5': '胜', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08220O1A2O0O0O1O0O0O5': '夏', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08230M1g2O0O0O1O0O0O5': '访', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1T2I1O0O0O5': '境', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08200O1Q2O0O0O1O0O0O5': '括', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08240M1A2O0O0O1O0O0O5': '旱', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1j2k1O0O0O5': '娱', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082z0N1w2O0O0O1O0O0O5': '牙', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08210M1A2O0O0O1O0O0O5': '脉', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08230O1A2O0O0O1O0O0O5': '客', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1A2O0O0O1O0O0O5': '久', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1T2A1O0O0O5': '鲁', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08200N1A2O0O0O1O0O0O5': '顺', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1j2g1O0O0O5': '达', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08210M1w2O0O0O1O0O0O5': '若', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08240N1g2O0O0O1O0O0O5': '炉', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082y0M1A2O0O0O1O0O0O5': '晶', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08200M1w2O0O0O1O0O0O5': '献', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08250N1w2O0O0O1O0O0O5': '纵', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08200M1A2O0O0O1O0O0O5': '瓦', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08220N1w2O0O0O1O0O0O5': '玉', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1j2A1O0O0O5': '美', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1j2I1O0O0O5': '仁', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08240O1Q2O0O0O1O0O0O5': '铸', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1D2A1O0O0O5': '愿', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08210M1Q2O0O0O1O0O0O5': '宜', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08200M1Q2O0O0O1O0O0O5': '斜', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08250': '序', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08200O1A2O0O0O1O0O0O5': '司', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08210N1Q2O0O0O1O0O0O5': '壮', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0': '振', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082y0M1Q2O0O0O1O0O0O5': '插', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08220M1A2O0O0O1O0O0O5': '愈', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1D2A1O0O0O5': '扬', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1g2O0O0O1O0O0O5': '念', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08230O1Q2O0O0O1O0O0O5': '', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1D2Y1O0O0O5': '敬', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082y0M1w2O0O0O1O0O0O5': '燃', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1T2Y1O0O0O5': '锥', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1T2E1O0O0O5': '繁', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1Q2O0O0O1O0O0O5': '夹', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1T2U1O0O0O5': '掉', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08220M1w2O0O0O1O0O0O5': '染', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08220M1g2O0O0O1O0O0O5': '份', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0M1D2I1O0O0O5': '延', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0N1D2M1O0O0O5': '耀', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V08250N1A2O0O0O1O0O0O5': '句', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082y0N1w2O0O0O1O0O0O5': '咱', '//ibaotu.com/index.php?m=downVarify&a=renderCode&k=Y2V082x0O1Q2O0O0O1O0O0O5': '儒'}
            html = Selector(text=self.driver.page_source)
            word = html.css(".tips span::text").extract_first()
            imgs = html.css(".imgs-wrap img::attr(src)").extract()
            i = 0
            for img_url in imgs:
                i = i + 1
                # 可能没有这个汉字
                if yzm.get(img_url, 0) != 0 and word == yzm.get(img_url):
                    break

            # 模拟点击汉字
            # //div[@class='imgs-wrap']/img[1]
            input_el = self.driver.find_element_by_xpath("//div[@class='imgs-wrap']/img[{}]".format(i))
            input_el.click()
            time.sleep(2)

            result = EC.alert_is_present()(self.driver)
            if result:
                # 获取alert对话框
                dig_alert = self.driver.switch_to.alert
                time.sleep(1)
                # 打印警告对话框内容
                print(dig_alert.text)
                # alert对话框属于警告对话框，我们这里只能接受弹窗
                dig_alert.accept()
                time.sleep(1)
            else:
                print("alert 未弹出！说明过掉验证码了")
                is_over = True


def main():
    """只需修改executable_path"""
    from selenium.webdriver.chrome.options import Options
    options = Options()
    # 我本地的 Google Chrome
    options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    # 我本地的 chromedriver
    driver = webdriver.Chrome(chrome_options=options, executable_path='/Users/yuanlang/work/javascript/chromedriver')
    # 这个js没用到。过滑块可以使用
    with open('stealth.min.js') as f:
        js = f.read()

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": js
    })

    cracker = BTCGeetestCrack(driver, is_login=True)
    cracker.crack()

error=0
if __name__ == "__main__":

    main()
    # dd = {}
    # Cookie = "user_refers=a%3A2%3A%7Bi%3A0%3Bs%3A6%3A%22ibaotu%22%3Bi%3A1%3Bs%3A6%3A%22ibaotu%22%3B%7D; Hm_lvt_2b0a2664b82723809b19b4de393dde93=1607912574; Hm_lvt_4df399c02bb6b34a5681f739d57787ee=1607912575; Hm_lvt_bdba7c5873b3a5c678c7e71b38052312=1607912575; FIRSTVISITED=1607912574.955; bt_guid=c0e6cdecbbc966e11fb24899b5df315e; sign=PHONE; last_auth=3; head_34462354=%2F%2Fpic.ibaotu.com%2Fhead%2Fdefault.png; sign=null; ISREQUEST=1; WEBPARAMS=is_pay=0; web_push_update=1; referer=http%3A%2F%2Fibaotu.com%2F%3Fm%3Dstats%26callback%3DjQuery112409705747194070717_1607934340813%26lx%3D1%26pagelx%3D11%26exectime%3D0.0004%26loadtime%3D36.136%26_%3D1607934340816; login_type=PHONE; auth_id=34462354%7C151%2A%2A%2A96850%7C1609230432%7C8b323b4df882c535ee2f45c01d7f2b14; _sh_hy=a%3A3%3A%7Bi%3A0%3Ba%3A2%3A%7Bs%3A4%3A%22name%22%3Bs%3A12%3A%22%E5%B9%BF%E5%91%8A%E8%AE%BE%E8%AE%A1%22%3Bs%3A5%3A%22count%22%3Bi%3A8888%3B%7Di%3A1%3Ba%3A2%3A%7Bs%3A4%3A%22name%22%3Bs%3A12%3A%22%E7%BD%91%E9%A1%B5%E8%AE%BE%E8%AE%A1%22%3Bs%3A5%3A%22count%22%3Bi%3A2214%3B%7Di%3A2%3Ba%3A2%3A%7Bs%3A4%3A%22name%22%3Bs%3A4%3A%22hzm1%22%3Bs%3A5%3A%22count%22%3Bi%3A1000%3B%7D%7D; md_session_id=20201214002533466; Hm_lpvt_2b0a2664b82723809b19b4de393dde93=1607943206; md_session_expire=1800; Hm_lpvt_4df399c02bb6b34a5681f739d57787ee=1607943207; Hm_lpvt_bdba7c5873b3a5c678c7e71b38052312=1607943207"
    # for c in Cookie.replace(" ","").split(";"):
    #     ss = c.split("=")
    #     # print("{\"name\":\"{0}\",\"value\":\"{1}\"}")
    #     print("driver.add_cookie({\"domain\":\".ibaotu.com\",\"name\":\""+ss[0]+"\",\"value\":\""+ss[1]+"\",\"expires\": \"\",\"path\": \"/\",\"httpOnly\": False,\"HostOnly\": False,\"Secure\": False})")
    #
    # print(dd)

