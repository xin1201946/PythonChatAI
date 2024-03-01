#  Copyright (c) 2024.
#  @Author  : Canfeng
#  @Email     : 1324435230@qq.com
#  About  main.py
#  @IDE        : PyCharm
#  注：本软件遵循 GPLv3协议，请在使用、修改或分发时遵守该协议条款。
import os
import cv2
import requests
from PyQt6.QtCore import Qt, QEasingCurve, QUrl
from PyQt6.QtGui import QPicture, QPixmap
from PyQt6.QtWidgets import QFrame
from qfluentwidgets import FluentIcon, Action, InfoBar, InfoBarPosition, SubtitleLabel, ScrollArea, ImageLabel, \
    LineEdit, MessageBoxBase
import pic
from fake_useragent import UserAgent

global _APPNAME, _APPVERSION, _APPICON
_APPNAME = "每日一图"
_APPVERSION = "1.5.0"
_APPICON = FluentIcon.DOCUMENT.icon()


def resize_image(input_image_path, output_image_path):
    # 读取原始图像
    original_image = cv2.imread(input_image_path)

    if original_image is not None:
        # 获取原始图像的宽度和高度
        original_height, original_width, _ = original_image.shape

        # 计算水平和垂直缩放因子
        height_factor = 640 / original_height
        width_factor = 960 / original_width

        # 使用最小的缩放因子来保持原图的宽高比
        scale_factor = min(height_factor, width_factor)

        # 计算目标尺寸
        target_height = int(original_height * scale_factor)
        target_width = int(original_width * scale_factor)

        # 进行缩放操作
        resized_image = cv2.resize(original_image, (target_width, target_height), interpolation=cv2.INTER_AREA)

        # 保存缩放后的图像
        cv2.imwrite(output_image_path, resized_image)
    else:
        pass


# 使用函数的例子

class MAIN(QFrame):
    def __init__(self, text: str, parent=None):
        super().__init__()
        self.ui = pic.Ui_Frame()
        self.ui.setupUi(self)
        self.setObjectName("EveryDayPic")
        self.get_Picture()
        self.moyu()
        self.ui.CommandBar.addAction(Action(FluentIcon.ADD, '摸鱼日报', triggered=self.OpenMOYUFILE))
        self.ui.CommandBar.addAction(Action(FluentIcon.PLAY, '打开每日一图', triggered=self.OpenFILE))
        self.ui.CommandBar.addAction(Action(FluentIcon.REMOVE, '刷新每日一图', triggered=self.get_Picture))

    def OpenFILE(self):
        path = os.getcwd()
        os.startfile(path + '/plugin/download/Image.jpg')

    def OpenMOYUFILE(self):
        path = os.getcwd()
        os.startfile(path + '/plugin/download/MoYu.jpg')


    def moyu(self):
        url = "https://api.52vmy.cn/api/wl/moyu"
        save_path = "./plugin/download/"

        # 检查目标路径是否存在，如果不存在则创建
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # 发送GET请求，由于该地址会自动跳转，我们需要允许重定向
        response = requests.get(url, allow_redirects=True)

        # 获取最终重定向后的URL
        actual_url = response.url
        file_name = "MoYu.jpg"
        # 下载图片
        with open(os.path.join(save_path, file_name), 'wb') as out_file:
            out_file.write(response.content)

    def get_Picture(self):
        url = "https://bing.img.run/rand.php"

        # 目标保存路径
        save_path = "./plugin/download/"

        # 检查目标路径是否存在，如果不存在则创建
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # 发送GET请求，由于该地址会自动跳转，我们需要允许重定向
        try:

            response = requests.get(url)
            response.raise_for_status()  # 如果响应状态不是200，抛出HTTPError异常
        except requests.exceptions.RequestException as e:
            print(f"请求发生错误: {e}")
        else:
            file_name = "Image.jpg"
            # 下载图片
            with open(os.path.join(save_path, file_name), 'wb') as out_file:
                out_file.write(response.content)
            resize_image('./plugin/download/Image.jpg', './plugin/download/ImageForSmall.jpg')
            self.ui.ImageLabel.setPixmap("./plugin/download/ImageForSmall.jpg")
