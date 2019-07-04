#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from v3.geetest import BaseGeetestCrack
from selenium import webdriver


class IndustryAndCommerceGeetestCrack(BaseGeetestCrack):

    """工商滑动验证码破解类"""

    def __init__(self, driver):
        super(IndustryAndCommerceGeetestCrack, self).__init__(driver)

    def crack(self):
        """执行破解程序
        """
        self.input_by_id()
        self.click_by_id()

        x_offset = self.calculate_slider_offset()-4
        print(x_offset)
        time.sleep(2)
        self.drag_and_drop(x_offset=x_offset,falg=True)

    def grapHtml(self,element_id="gggscpnamebox"):
        content=self.driver.find_element_by_id(element_id)
        print(type(content))
        print(content)



def main():
    driver = webdriver.PhantomJS(executable_path='D:\OtherTool\phantomjs-1.9.7-windows\phantomjs.exe')
    driver.get("http://sh.gsxt.gov.cn/notice")
    cracker = IndustryAndCommerceGeetestCrack(driver)
    cracker.crack()
    #print(driver.get_window_size())
    driver.save_screenshot("screen.png")
    #print(driver.page_source)
    time.sleep(3)
    driver.save_screenshot("screen2.png")
    cracker.grapHtml()
    driver.close()




if __name__ == "__main__":
    main()
