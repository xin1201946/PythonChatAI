#  Copyright (c) 2024.
#  @Author  : Canfeng
#  @Email     : 1324435230@qq.com
#  About  ABOUT.py
#  @IDE        : PyCharm
#  注：本软件遵循 LGPLv3协议，请在使用、修改或分发时遵守该协议条款。
import json
import os

import requests
from PyQt6.QtWidgets import QFrame
from qfluentwidgets import FluentIcon

import smvedio

global _APPNAME,_APPVERSION,_APPICON,geturl
_APPNAME = "短视频下载"
_APPVERSION = "1.0"
_APPICON = FluentIcon.CLOUD_DOWNLOAD.icon()


class MAIN(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__()
        self.ui = smvedio.Ui_Frame()
        self.ui.setupUi(self)
        self.setObjectName("ShortVedioDownload")
        self.ui.PushButton_2.setEnabled(False)
        self.ui.TextEdit.setReadOnly(True)

        self.ui.PushButton.clicked.connect(self.jiexi)
        self.ui.PushButton_2.clicked.connect(self.download)

    def download(self):
        os.startfile(geturl)

    def jiexi(self):
        url = "http://luck.klizi.cn/api/jx_video.php?url="+self.ui.PlainTextEdit.toPlainText()
        global geturl
        # 发送GET请求
        response = requests.get(url)

        # 检查请求是否成功（HTTP状态码为200）
        if response.status_code == 200:
            # 解析JSON响应
            data = json.loads(response.text)
            dataf=data['data']
            time = dataf['time']
            title = dataf['title']
            geturl = dataf['url']
            self.ui.TextEdit.setText(time + '\n' + title + '\n DONE')
            self.ui.PushButton_2.setEnabled(True)
