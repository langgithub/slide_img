# -*- coding: utf-8 -*-

import time
import uuid
import io
import random

from PIL import Image
from selenium.webdriver.common.action_chains import ActionChains


class BaseGeetestCrack(object):

    """验证码破解基础类"""

    def __init__(self, driver):
        self.driver = driver
        self.driver.maximize_window()

    def input_by_id(self, text=u"上海卫诚", element_id="keyword"):
        """输入查询关键词

        :text: Unicode, 要输入的文本
        :element_id: 输入框网页元素id

        """
        input_el = self.driver.find_element_by_id(element_id)
        input_el.clear()
        input_el.send_keys(text)
        time.sleep(1)

    def click_by_id(self, element_id="buttonSearch"):
        """点击查询按钮

        :element_id: 查询按钮网页元素id

        """
        search_el = self.driver.find_element_by_id(element_id)
        search_el.click()
        time.sleep(1)

    def calculate_slider_offset(self):
        """计算滑块偏移位置，必须在点击查询按钮之后调用

        :returns: Number

        """
        time.sleep(0.5)
        img1 = self.crop_captcha_image()
        self.drag_and_drop(x_offset=200)
        time.sleep(0.5)
        img2 = self.crop_captcha_image()
        w1, h1 = img1.size
        w2, h2 = img2.size
        if w1 != w2 or h1 != h2:
            return False
        left = 0
        for i in range(45, w1):
            if not self.columnSimilar(img1,img2,i,h1):
                left = i
                break
        return left

    def columnSimilar(self, img1, img2, x ,height):
        for j in range(0,90):
            if not self.is_pixel_equal(img1, img2, x, j):
                return False
        return True

    def is_pixel_equal(self, img1, img2, x, y):
        pix1 = img1.load()[x, y]
        pix2 = img2.load()[x, y]
        #R G B 小于60为黑色
        if (abs(pix1[0] - pix2[0] < 60) and abs(pix1[1] - pix2[1] < 60) and abs(pix1[2] - pix2[2] < 60)):
            return True
        else:
            return False

    def crop_captcha_image(self, element_id="gt_box"):
        """截取验证码图片

        :element_id: 验证码图片网页元素id
        :returns: StringIO, 图片内容

        """
        captcha_el = self.driver.find_element_by_class_name(element_id)
        location = captcha_el.location
        size = captcha_el.size
        left = int(location['x'])
        top = int(location['y'])
        #left = 1010
        #top = 535
        right = left + int(size['width'])
        bottom = top + int(size['height'])
        #right = left + 523
        #bottom = top + 235
        print(left, top, right, bottom)
        screenshot = self.driver.get_screenshot_as_png()
        screenshot = Image.open(io.BytesIO(screenshot))
        captcha = screenshot.crop((left, top, right, bottom))
        captcha.save("%s.png" % uuid.uuid4())
        return captcha

    def get_browser_name(self):
        """获取当前使用浏览器名称
        :returns: TODO

        """
        return str(self.driver).split('.')[2]

    # 根据缺口的位置模拟x轴移动的轨迹
    def get_track(self,length):
        list = []
        # 间隔通过随机范围函数来获得,每次移动一步或者两步
        x = random.randint(10, 15)
        # 生成轨迹并保存到list内
        while length - x >= 15:
            list.append(x)
            length = length - x
            x = random.randint(10, 15)
        # 最后五步都是一步步移动
        x = random.randint(3, 5)
        while length - x >= 5:
            list.append(x)
            length = length - x
            x = random.randint(3, 5)
            # 最后五步都是一步步移动
        for i in range(length):
            list.append(1)
        return list

    def drag_and_drop(self, x_offset=0, y_offset=0, element_class="gt_slider_knob",falg=False):
        """拖拽滑块

        :x_offset: 相对滑块x坐标偏移
        :y_offset: 相对滑块y坐标偏移
        :element_class: 滑块网页元素CSS类名

        """
        #self.driver.save_screenshot("1.png")
        dragger = self.driver.find_element_by_class_name(element_class)
        action = ActionChains(self.driver)
        print(x_offset, y_offset)
        if not falg:
            action.drag_and_drop_by_offset(dragger, x_offset, y_offset).perform()
        else:
            # 生成x的移动轨迹点
            track_list = self.get_track(x_offset)
            # 获得滑动圆球的高度
            y = dragger.location['y']
            # 鼠标点击元素并按住不放
            print("第一步,点击元素")
            action.click_and_hold(dragger).perform()
            time.sleep(0.15)
            print("第二步，拖动元素")
            track_string = ""
            count=0
            for track in track_list:
                count=count+track
                #track_string = track_string + "{%d,%d}," % (track, y)
                #self.driver.save_screenshot("move%s.png" % count)
                action.move_by_offset(track,yoffset=0).perform()
                action.reset_actions()
                # 间隔时间也通过随机函数来获得,间隔不能太快,否则会被认为是程序执行
                ti=random.randint(10, 30-track) / 100
                time.sleep(ti)
                print(ti)

            print(track_string)
            print("第三步，释放鼠标")
            # 释放鼠标
            action.release().perform()
            time.sleep(0.5)
            self.driver.save_screenshot("okkkk%s.png" % uuid.uuid4())
        time.sleep(0.5)
        #self.driver.save_screenshot("okkkk%s.png" % uuid.uuid4())



    def move_to_element(self, element_class="gt_slider_knob"):
        """鼠标移动到网页元素上

        :element: 目标网页元素

        """
        time.sleep(1)
        element = self.driver.find_element_by_class_name(element_class)
        action = ActionChains(self.driver)
        action.move_to_element(element).perform()
        time.sleep(0.5)

    def crack(self):
        """执行破解程序

        """
        raise NotImplementedError



