# -*- coding: utf-8 -*-
import io
import base64
import numpy as np

from abc import ABCMeta, abstractmethod
from PIL import Image, ImageChops
from selenium.webdriver.common.action_chains import ActionChains


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

    def move_to_gap(self, track, element_class="geetest_slider_button"):
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
from v3.logger import logger
from selenium import webdriver


class BTCGeetestCrack(BaseGeetestCrack):
    """比特币滑动验证码破解类"""

    def __init__(self, driver):
        super().__init__(driver)

    def init_page(self):
        self.driver.get("https://exchange.fcoin.pro/u/login/cellphone")

    def input_by_user(self, text="17621972154", element_class="input[name='cellphone']"):
        input_el = self.driver.find_element_by_css_selector(element_class)
        input_el.clear()
        input_el.send_keys(text)
        time.sleep(0.5)

    def input_by_pwd(self, text="assbcd123", element_class="input[name='password']"):
        input_el = self.driver.find_element_by_css_selector(element_class)
        input_el.clear()
        input_el.send_keys(text)
        time.sleep(0.5)

    def click_by_id(self, element_id="//*[@id=\"root\"]/div[2]/div/div/form/button"):
        search_el = self.driver.find_element_by_xpath(element_id)
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
        js = "return document.getElementsByClassName('geetest_wind')[0].style.display"
        result = self.driver.execute_script(js)
        if result == "block":
            global error
            # 日志收集
            t = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(time.time()))
            img_bg = f"img/{t}_bg.png"
            img_fullbg = f"img/{t}_fullbg.png"
            img_diff = f"img/{t}_diff.png"
            self.error.bg.save(img_bg)
            self.error.full.save(img_fullbg)
            self.error.diff.save(img_diff)
            logger.debug(f"img_bg=>{img_bg} img_fullbg=>{img_fullbg} img_diff=>{img_diff} offset=>{self.error.offset}")
            error=error+1

    def crack(self):
        """执行破解程序
        """
        self.init_page()
        time.sleep(5)
        self.input_by_user()
        self.input_by_pwd()
        self.click_by_id()

        x_offset = self.calculate_slider_offset() - 8
        print(x_offset)
        print(x_offset)
        track = self.get_tracks_2(x_offset, random.randint(2, 4), self.ease_out_quart)
        print("滑动轨迹", track)
        print("滑动距离", functools.reduce(lambda x, y: x + y, track))
        self.move_to_gap(track)
        time.sleep(2)
        self.check_response()
        self.driver.close()

    def grapHtml(self, element_id="gggscpnamebox"):
        content = self.driver.find_element_by_id(element_id)
        print(type(content))
        print(content)


def main():
    """只需修改executable_path"""
    driver = webdriver.Chrome(executable_path='/Users/yuanlang/work/javascript/chromedriver')
    cracker = BTCGeetestCrack(driver)
    cracker.crack()

error=0
if __name__ == "__main__":

    for i in range(50):
        main()
        print(f"测试结果50次，失败：{error}")
