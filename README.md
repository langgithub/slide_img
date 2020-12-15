
## 滑块验证码破解
注意：v3项目可用，附带测试成功率，只需替换driver。若是用于其他项目，修改相应selector
![样式](/1501562814610_.pic_hd.jpg)

### 方式一 数据发包
```
如zhongguorenshou.py,思路
1.请求背景图片
2.两张图片滑动距离（有的需要图片还原）
3.更具滑动距离模拟生成鼠标滑动参数和时间
```

### 方式二 driver
```
ru industry.py
基于selenium+phantomjs 原理

1.phantomjs 是一款基于浏览器内核软件
2.通过selenium模拟人为操作
3.缺点：和浏览器操作一样，慢
4.优势：不用模拟鼠标滑动，易过调
```

### 方式三 收集滑动轨迹，存放到数据库
```
1.请求背景图片
2.两张图片滑动距离（有的需要图片还原）
3.采用js hook 方式手机滑动轨迹
```

### 目录介绍
1. v1 是老版本工商滑块 （无法使用了）
2. v2 通过发包的方式过滑块 （滑块跟新块，基本不考虑，无法使用）
3. v3 推荐使用滑块方式
4. v4 过掉包图网的滑块验证码和点选验证码（主要核心看点是stealth.min.js） 用于隐藏selenium 和 puppeteer特征隐藏

more: v3介绍
亮点一：v3中的滑动距离计算，采用计算两张图片差值进行灰度化，在二值化（采用类间方差）
亮点二：轨迹生成方面采用算法更高效

### 介绍js hook
```
//目标hook函数startRecord
//添加自己的日志代码
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
```

注：个人博客 https://langgithub.github.io/

