#!/usr/bin/env python3
# -*- coding:utf-8 -*- 
# author：yuanlang 
# creat_time: 2020/12/14 上午10:36
# file: baotuwang.py

import os
import re
import time
import json
import urllib3
import requests
import threading
from common.proxy_helper import get_proxy
from scrapy import Selector
from queue import Queue
from tqdm import tqdm
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings()


class BaotuDownload(object):
    page_list = []
    seeds_dict = {}
    seeds = None
    session = None
    headers = None

    def __init__(self, page_list, headers):
        self.page_list = page_list
        self.seeds = Queue()
        self.session = requests.session()
        self.headers = headers
        self.download_info()

    def download_info(self):
        for page in self.page_list:
            verify_url = "http://123.57.36.150:11001/asyncInvoke?group=langcode2&action=getCookie"
            response_cookie = requests.get(verify_url)
            rj = json.loads(response_cookie.text)
            self.headers.update({"Cookie": rj["data"]})
            resp = self.session.get(page, headers=self.headers, verify=False)
            html = Selector(text=resp.text)
            all_dls = html.css("div.bt-body dl")
            for dl in all_dls:
                id = dl.css("dl::attr(pr-data-id)").extract()[0]
                title = dl.css("dl::attr(pr-data-title)").extract()[0].replace("<strong>", "").replace("</strong>", "")
                self.seeds_dict[id] = title
            print(self.seeds_dict)

    def run(self):
        t = threading.Thread(target=self.down_thread)
        t.start()

        for _seed_k, _seed_v in self.seeds_dict.items():
            if "广告设计" in _seed_v:
                while 1:
                    download_url = "https://ibaotu.com/?m=downloadopen&a=open&id={}&down_type=1&attachment_id=&team_down=1".format(
                        _seed_k)
                    print(download_url)
                    response_zip = self.session.get(url=download_url, headers=self.headers, stream=True,
                                                    allow_redirects=False, verify=False)
                    if "此图片您已经下载过啦" in response_zip.text:
                        print("{}此图片您已经下载过啦".format(_seed_k))
                        break
                    Location = response_zip.headers.get("Location")
                    if ".zip" not in Location:
                        verify_url = "http://123.57.36.150:11001/asyncInvoke?group=langcode2&action=getCookie2&id={}".format(
                            _seed_k)
                        response_cookie = requests.get(verify_url)
                        rj = json.loads(response_cookie.text)
                        self.headers.update({"Cookie": rj["data"],
                                             "Host": "ibaotu.com",
                                             "Referer": "https://ibaotu.com/?m=download&id={}&to=233".format(_seed_k),
                                             "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                                             "Accept-Encoding": "gzip, deflate, br",
                                             "Accept-Language": "zh-CN,zh;q=0.9",
                                             "Connection": "keep-alive",
                                             "Sec-Fetch-Site": "same-origin",
                                             "Sec-Fetch-Mode": "navigate",
                                             "Sec-Fetch-Dest": "document"})
                        # input("检查")
                    else:
                        # 保存下载链接
                        print("文件：{}.zip url:{}即将开始下载...".format(self.seeds_dict[_seed_k], Location))
                        time.sleep(5)
                        # self.seeds.put((self.seeds_dict[_seed_k], Location))
                        # time.sleep(1 * 60)

                        break

    def down_thread(self):
        with ThreadPoolExecutor(max_workers=2) as t:
            while 1:
                if not self.seeds.empty():
                    name, download_url = self.seeds.get()
                    t.submit(self.download_from_url, download_url, name + ".zip")

    def download_from_url(self, url, dst):
        """
        @param: url to download file
        @param: dst place to put the file
        :return: bool
        """
        # 获取文件长度
        try:
            file_size = int(urlopen(url).info().get('Content-Length', -1))
        except Exception as e:
            print(e)
            print("错误，访问url: %s 异常" % url)
            return False

        # 文件大小
        if os.path.exists(dst):
            first_byte = os.path.getsize(dst)
        else:
            first_byte = 0
        if first_byte >= file_size:
            return file_size

        header = {"Range": "bytes=%s-%s" % (first_byte, file_size)}
        pbar = tqdm(
            total=file_size, initial=first_byte,
            unit='B', unit_scale=True, desc=url.split('/')[-1])

        # 访问url进行下载
        req = requests.get(url, headers=header, stream=True, verify=False)
        try:
            with(open(dst, 'ab')) as f:
                for chunk in req.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(1024)
        except Exception as e:
            print(e)
            return False

        pbar.close()
        return True


if __name__ == "__main__":
    page_list = ["https://ibaotu.com/tupian/guanggaosheji.html"]
    download_header = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
        # "Cookie": "md_session_id=20201214001036331; user_refers=a%3A2%3A%7Bi%3A0%3Bs%3A6%3A%22ibaotu%22%3Bi%3A1%3Bs%3A6%3A%22ibaotu%22%3B%7D; Hm_lvt_2b0a2664b82723809b19b4de393dde93=1607912574; md_session_expire=1800; Hm_lvt_4df399c02bb6b34a5681f739d57787ee=1607912575; Hm_lvt_bdba7c5873b3a5c678c7e71b38052312=1607912575; FIRSTVISITED=1607912574.955; bt_guid=c0e6cdecbbc966e11fb24899b5df315e; referer=http%3A%2F%2Fibaotu.com%2F%3Fm%3Dstats%26callback%3DjQuery112409263551908178111_1607912605274%26lx%3D3%26pagelx%3D13%26exectime%3D0.0191%26loadtime%3D0.678%26_%3D1607912605276; sign=PHONE; login_type=PHONE; last_auth=3; auth_id=34462354%7C151%2A%2A%2A96850%7C1609208726%7C31b39faf3220246828eb35cee0fb2819; head_34462354=%2F%2Fpic.ibaotu.com%2Fhead%2Fdefault.png; sign=null; ISREQUEST=1; WEBPARAMS=is_pay=0; web_push_update=1; _sh_hy=a%3A2%3A%7Bi%3A0%3Ba%3A2%3A%7Bs%3A4%3A%22name%22%3Bs%3A12%3A%22%E5%B9%BF%E5%91%8A%E8%AE%BE%E8%AE%A1%22%3Bs%3A5%3A%22count%22%3Bi%3A8888%3B%7Di%3A1%3Ba%3A2%3A%7Bs%3A4%3A%22name%22%3Bs%3A4%3A%22hzm1%22%3Bs%3A5%3A%22count%22%3Bi%3A1000%3B%7D%7D; Hm_lpvt_2b0a2664b82723809b19b4de393dde93=1607913165; Hm_lpvt_4df399c02bb6b34a5681f739d57787ee=1607913165; Hm_lpvt_bdba7c5873b3a5c678c7e71b38052312=1607913165",
        # "Cookie": "md_session_id=20201214001036331; user_refers=a%3A2%3A%7Bi%3A0%3Bs%3A6%3A%22ibaotu%22%3Bi%3A1%3Bs%3A6%3A%22ibaotu%22%3B%7D; Hm_lvt_2b0a2664b82723809b19b4de393dde93=1607912574; md_session_expire=1800; Hm_lvt_4df399c02bb6b34a5681f739d57787ee=1607912575; Hm_lvt_bdba7c5873b3a5c678c7e71b38052312=1607912575; FIRSTVISITED=1607912574.955; bt_guid=c0e6cdecbbc966e11fb24899b5df315e; referer=http%3A%2F%2Fibaotu.com%2F%3Fm%3Dstats%26callback%3DjQuery112409263551908178111_1607912605274%26lx%3D3%26pagelx%3D13%26exectime%3D0.0191%26loadtime%3D0.678%26_%3D1607912605276; sign=PHONE; login_type=PHONE; last_auth=3; auth_id=34462354%7C151%2A%2A%2A96850%7C1609208726%7C31b39faf3220246828eb35cee0fb2819; head_34462354=%2F%2Fpic.ibaotu.com%2Fhead%2Fdefault.png; sign=null; ISREQUEST=1; WEBPARAMS=is_pay=0; web_push_update=1; _sh_hy=a%3A2%3A%7Bi%3A0%3Ba%3A2%3A%7Bs%3A4%3A%22name%22%3Bs%3A12%3A%22%E5%B9%BF%E5%91%8A%E8%AE%BE%E8%AE%A1%22%3Bs%3A5%3A%22count%22%3Bi%3A8888%3B%7Di%3A1%3Ba%3A2%3A%7Bs%3A4%3A%22name%22%3Bs%3A4%3A%22hzm1%22%3Bs%3A5%3A%22count%22%3Bi%3A1000%3B%7D%7D; Hm_lpvt_2b0a2664b82723809b19b4de393dde93=1607916843; Hm_lpvt_4df399c02bb6b34a5681f739d57787ee=1607916844; Hm_lpvt_bdba7c5873b3a5c678c7e71b38052312=1607916844",
        "Cookie": "user_refers=a%3A2%3A%7Bi%3A0%3Bs%3A6%3A%22ibaotu%22%3Bi%3A1%3Bs%3A6%3A%22ibaotu%22%3B%7D; Hm_lvt_2b0a2664b82723809b19b4de393dde93=1607912574; Hm_lvt_4df399c02bb6b34a5681f739d57787ee=1607912575; Hm_lvt_bdba7c5873b3a5c678c7e71b38052312=1607912575; FIRSTVISITED=1607912574.955; bt_guid=c0e6cdecbbc966e11fb24899b5df315e; referer=http%3A%2F%2Fibaotu.com%2F%3Fm%3Dstats%26callback%3DjQuery112409263551908178111_1607912605274%26lx%3D3%26pagelx%3D13%26exectime%3D0.0191%26loadtime%3D0.678%26_%3D1607912605276; sign=PHONE; login_type=PHONE; last_auth=3; auth_id=34462354%7C151%2A%2A%2A96850%7C1609208726%7C31b39faf3220246828eb35cee0fb2819; head_34462354=%2F%2Fpic.ibaotu.com%2Fhead%2Fdefault.png; sign=null; ISREQUEST=1; WEBPARAMS=is_pay=0; web_push_update=1; _sh_hy=a%3A2%3A%7Bi%3A0%3Ba%3A2%3A%7Bs%3A4%3A%22name%22%3Bs%3A12%3A%22%E5%B9%BF%E5%91%8A%E8%AE%BE%E8%AE%A1%22%3Bs%3A5%3A%22count%22%3Bi%3A8888%3B%7Di%3A1%3Ba%3A2%3A%7Bs%3A4%3A%22name%22%3Bs%3A4%3A%22hzm1%22%3Bs%3A5%3A%22count%22%3Bi%3A1000%3B%7D%7D; md_session_id=20201214001425859; md_session_expire=1800; Hm_lpvt_2b0a2664b82723809b19b4de393dde93=1607928238; Hm_lpvt_bdba7c5873b3a5c678c7e71b38052312=1607928238; Hm_lpvt_4df399c02bb6b34a5681f739d57787ee=1607928238"
    }
    down = BaotuDownload(page_list=page_list, headers=download_header)
    down.run()


"https://ibaotu.com/?m=download&id=64454&to=233"