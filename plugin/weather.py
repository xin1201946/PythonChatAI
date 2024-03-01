#  Copyright (c) 2024.
#  @Author  : Canfeng
#  @Email     : 1324435230@qq.com
#  About  main.py
#  @IDE        : PyCharm
#  注：本软件遵循 GPLv3协议，请在使用、修改或分发时遵守该协议条款。
import json
from datetime import datetime, timedelta

import requests
from PyQt6.QtWidgets import QFrame
from qfluentwidgets import FluentIcon, Action

import wea

global _APPNAME, _APPVERSION, _APPICON, data, num, date,date_day,now_date
num = 1
_APPNAME = "天气"
_APPVERSION = "1.0"
_APPICON = FluentIcon.CLOUD.icon()



class MAIN(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__()
        self.ui = wea.Ui_Frame()
        self.ui.setupUi(self)
        self.setObjectName("getWEATHER")
        self.get_weather()
        self.ui.CommandBar.addAction(Action(FluentIcon.LEFT_ARROW, "上一天", triggered=self.LastDay))
        self.ui.CommandBar.addAction(Action(FluentIcon.HOME_FILL, "今天", triggered=self.get_weather))
        self.ui.CommandBar.addAction(Action(FluentIcon.RIGHT_ARROW, "下一天", triggered=self.NEXTDAY))

    def NEXTDAY(self):
        global num,now_date
        if num > 5:
            num = 5
            pass
        else:
            num = num + 1
            if num > 5:
                return
            if num == 0:
                self.get_weather()
            else:
                data_info = data["data"][num]
                first_date = data_info["date"]
                temperature = data_info["temperature"]
                weather = data_info["weather"]
                manner = data_info["manner"]
                pm = data_info["pm"]

                self.ui.CaptionLabel.setText("温度 : " + temperature)
                self.ui.CaptionLabel_2.setText("风向 : " + manner)
                self.ui.CaptionLabel_3.setText("PM指数 : " + pm)
                self.ui.CaptionLabel_4.setText("天气 : " + weather)
                if first_date == date:
                    now_date = date_day
                    self.ui.CaptionLabel_5.setText("日期 : " + str(now_date) + ", 今天" + first_date)
                else:

                    new_date = datetime.strptime(now_date, "%Y-%m-%d")
                    new_date = new_date + timedelta(days=1)
                    now_date = str(new_date.strftime('%Y-%m-%d'))
                    self.ui.CaptionLabel_5.setText("日期 : " + str(now_date) + ", " + first_date)
    def LastDay(self):
        global num,now_date
        if num == 0:
            num = 0
            pass
        else:
            num = num - 1
            if num < 0:
                self.get_weather()
            else:
                data_info = data["data"][num]
                first_date = data_info["date"]
                temperature = data_info["temperature"]
                weather = data_info["weather"]
                manner = data_info["manner"]
                pm = data_info["pm"]

                self.ui.CaptionLabel.setText("温度 : " + temperature)
                self.ui.CaptionLabel_2.setText("风向 : " + manner)
                self.ui.CaptionLabel_3.setText("PM指数 : " + pm)
                self.ui.CaptionLabel_4.setText("天气 : " + weather)
                if first_date == date:
                    now_date = date_day
                    self.ui.CaptionLabel_5.setText("日期 : " + str(now_date) + ",今天 " + first_date)
                else:
                    new_date = datetime.strptime(now_date, "%Y-%m-%d")
                    new_date = new_date-timedelta(days=1)
                    now_date=str(new_date.strftime('%Y-%m-%d'))
                    self.ui.CaptionLabel_5.setText("日期 : " + str(now_date) + ", " + first_date)
    def get_weather(self):
        url = "https://www.apii.cn/api/weather/"
        global data, date,date_day,now_date
        # 发送GET请求
        response = requests.get(url)

        # 检查请求是否成功（HTTP状态码为200）
        if response.status_code == 200:
            # 解析JSON响应
            data = json.loads(response.text)

            # 提取所需字段
            city = data["city"]
            date_day = data["date_day"]
            now_date=date_day
            warmWords = data["warmWords"]
            # 提取第一个日期项中的详细信息
            first_date_info = data["data"][1]
            date = first_date_info["date"]
            temperature = first_date_info["temperature"]
            weather = first_date_info["weather"]
            manner = first_date_info["manner"]
            pm = first_date_info["pm"]
            self.ui.TitleLabel.setText(city + "  ,  " + weather)
            self.ui.StrongBodyLabel.setText(warmWords)
            self.ui.CaptionLabel.setText("温度 : " + temperature)
            self.ui.CaptionLabel_2.setText("风向 : " + manner)
            self.ui.CaptionLabel_3.setText("PM指数 : " + pm)
            self.ui.CaptionLabel_4.setText("天气 : " + weather)
            self.ui.CaptionLabel_5.setText("日期 : " + date_day + "今天, " + date)
