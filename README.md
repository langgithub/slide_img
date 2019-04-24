
## 滑块验证码破解

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

注：滑块更新太快，需要clone下来自行修改

