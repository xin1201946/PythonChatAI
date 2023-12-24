import getpass
import json
import re
import sys
import time
from qframelesswindow import AcrylicWindow
import requests
from PyQt5.QtCore import QPoint, Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from openai import OpenAI
from qfluentwidgets import InfoBarIcon, InfoBar, InfoBarPosition, \
    InfoBarManager, FluentIcon, FluentTranslator
from qfluentwidgets import setTheme, Theme, StateToolTip
from qfluentwidgets import setThemeColor, FluentThemeColor
from qfluentwidgets.window.stacked_widget import StackedWidget

import form
global z, tt
DEFAULT_API_URL = "sk-"
DEFAULT_API_KEY = "https://api.openai.com/v1/chat/completions"
#当用户未输入Api或Url时将使用默认的Api或Url

def extract_url(ai_response):
    url_pattern = re.compile(r'https?://[^\s]+')
    urls = url_pattern.findall(ai_response)
    return urls[0] if urls else None


def check_network():
    try:
        requests.get("https://www.baidu.com", timeout=3)
        return True
    except requests.ConnectionError:
        return False


@InfoBarManager.register('Custom')
class CustomInfoBarManager(InfoBarManager):
    """ Custom info bar manager """

    def _pos(self, infoBar: InfoBar, parentSize=None):
        p = infoBar.parent()
        parentSize = parentSize or p.size()

        # the position of first info bar
        x = (parentSize.width() - infoBar.width()) // 2
        y = (parentSize.height() - infoBar.height()) // 2

        # get the position of current info bar
        index = self.infoBars[p].index(infoBar)
        for bar in self.infoBars[p][0:index]:
            y += (bar.height() + self.spacing)

        return QPoint(x, y)

    def _slideStartPos(self, infoBar: InfoBar):
        pos = self._pos(infoBar)
        return QPoint(pos.x(), pos.y() - 16)


class MyWindow(AcrylicWindow):
    def __init__(self):
        super().__init__()
        self.ui = form.Ui_Form()
        self.ui.setupUi(self)
        setThemeColor(FluentThemeColor.ORANGE_BRIGHT.color())
        self.ui.LineEdit_2.setClearButtonEnabled(True)
        self.ui.LineEdit_3.setClearButtonEnabled(True)
        self.ui.PushButton_2.clicked.connect(self.showyiyanTip)
        self.ui.HyperlinkLabel_2.clicked.connect(self.uidark)
        self.ui.PushButton_3.clicked.connect(self.about)
        self.ui.PushButton_4.clicked.connect(self.clear)
        self.ui.PushButton.clicked.connect(self.send_message)
        self.stackedWidget = StackedWidget(self)
        self.ui.HyperlinkLabel.clicked.connect(self.hyper)
        self.api_key = self.ui.PasswordLineEdit.text()
        self.api_url = self.ui.LineEdit_2.text()
        self.windowEffect.setAeroEffect(self.winId())
        self.createseccess("特效 Areo 开启成功", "特效管理器")
        setTheme(Theme.AUTO)
        self.homeInterface = QStackedWidget(self, objectName='homeInterface')
        items = ['gpt-3.5-turbo', 'gpt-4', 'gemini-pro-v', 'gpt-3.5-turbo-16k-0613', 'gpt-4-all'] #可供用户选择的Model列表

        self.ui.ComboBox.addItems(items)
        self.ui.ComboBox.currentTextChanged.connect(self.commboxchange)
        self.conversation = []

        self.CustomInfoBar("公告:",
                           "\n本软件每次发送信息都需要时间供Chat GPT反应，期间肯定会无响应，此为正常情况.\n只需耐心等待即可😎\n所有效果都会与暗黑模式冲突，请关闭暗黑模式在开启特效！",
                           FluentIcon.CHAT)
        self.ui.PushButton_5.clicked.connect(self.save_config)
        self.load_config()
        self.stateTooltip = None
        if check_network():
            self.createseccess("您已连接网络", "网络管理程序")
        else:
            self.createWarningInfoBar("请检查您的网络连接!", "网络管理程序", 2000)

    def hyper(self):
        self.CustomInfoBar("？？？",
                           "\n😎😎😎😎😎😎😎😎😎\n",
                           FluentIcon.CODE)

    def commboxchange(self):
        if self.ui.ComboBox.text() != "gpt-3.5-turbo" or self.ui.ComboBox.text() != "gemini-pro-v":
            self.createWarningInfoBar("注意，您使用的是付费模型，请注意额度", "System", 4000)

    def createaboutInfoBar(self):
        content = "作者：XIN \n  本软件遵循 GPL V3.0协议  \n版权所有（C）2023 XIN \n注：\n  本程序为自由软件，在自由软件联盟发布的GNU通用公共许可协议的约束下，你可以对其进行修改再发布。希望发布的这款程序有用，但不保证它有经济价值和适合特定用途。详情参见GNU通用公共许可协议。  "
        w = InfoBar(
            icon=InfoBarIcon.INFORMATION,
            title='关于',
            content=content,
            orient=Qt.Vertical,  # vertical layout
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=-1,
            parent=self
        )
        w.show()

    def createWarningInfoBar(self, message, title, value):
        InfoBar.warning(
            title=title,
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,  # disable close button
            position=InfoBarPosition.TOP_LEFT,
            duration=value,
            parent=self
        )

    def save_config(self):

        config = {
            "api_url": self.api_url,
            "api_key": self.api_key,
        }
        with open("config.json", "w") as config_file:
            json.dump(config, config_file)

    def load_config(self):
        try:
            with open("config.json", "r") as config_file:
                config = json.load(config_file)
                self.api_url = config.get("api_url", DEFAULT_API_URL)
                self.api_key = config.get("api_key", DEFAULT_API_KEY)
                # 使用加载的值更新UI
                self.ui.LineEdit_2.setText(self.api_url)
                self.ui.PasswordLineEdit.setText(self.api_key)
        except FileNotFoundError:
            pass

    def createseccess(self, message, title):
        content = message
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title=title,
            content=content,
            orient=Qt.Vertical,  # vertical layout
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=4000,
            parent=self
        )
        w.show()

    def CustomInfoBar(self, title, message, icon):
        w = InfoBar.new(
            icon=icon,
            # icon=FluentIcon.GITHUB,
            title=title,
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=-1,
            parent=self
        )
        w.setCustomBackgroundColor('white', '#202020')

    def send_message(self):
        # 处理发送消息按钮的函数
        user_question = self.ui.TextEdit_2.toPlainText()

        # 从UI中获取API密钥和API URL

        if self.ui.PasswordLineEdit.text() == "" or self.ui.LineEdit_2.text() == "":
            if DEFAULT_API_KEY != "":
                if DEFAULT_API_URL !="":
                    self.api_url = DEFAULT_API_URL
                self.api_key = DEFAULT_API_KEY
            self.createWarningInfoBar("请输入Api_Key", "System", 4000)
            return
        else:
            self.api_key = self.ui.PasswordLineEdit.text()
            self.api_url = self.ui.LineEdit_2.text()
        systemrole = self.ui.LineEdit_3.text()
        # 检查是否有必填字段为空
        if not user_question:
            self.createWarningInfoBar("你还没输入问题", "System", 4000)
            return

        try:
            if check_network():
                self.conversation.append({"role": "system", "content": systemrole})
                self.conversation.append({"role": "user", "content": user_question})
                client = OpenAI(api_key=self.api_key, base_url=self.api_url)
                response = client.chat.completions.create(
                    model=self.ui.ComboBox.text(),
                    messages=self.conversation
                )
                ai_response = response.choices[0].message.content
                self.ui.TextEdit_2.clear()
                self.conversation.append({"role": "assistant", "content": ai_response})
                self.ui.TextEdit.append(f"\n用户: {user_question}")
                if extract_url(ai_response) != None:
                    self.ui.TextEdit.append(f"\nAI: {ai_response}")
                    text_edit = self.ui.TextEdit()
                    text_edit.insertHtml(f'<a href="{ai_response}">{ai_response}</a><br>')
                else:
                    self.ui.TextEdit.append(f"\nAI: {ai_response}")
            else:
                self.createWarningInfoBar("请检查您的网络连接!", "网络管理程序", 4000)
        except Exception as e:
            self.ui.TextEdit.append(f"错误: {e}")
            self.createWarningInfoBar(f"错误: {e}", "System", -1)

    def clear(self):
        self.ui.TextEdit.clear()

    def about(self):
        self.createaboutInfoBar()

    def uidark(self):
        setTheme(Theme.AUTO)

    # setTheme(Theme.DARK)
    # self.setStyleSheet("Demo{background: rgb(32, 32, 32)}")

    def showyiyanTip(self):
        if check_network():
            yiyan("a")
            self.createseccess(z, tt)
        else:
            self.createWarningInfoBar("请检查您的网络连接!", "网络管理程序", 4000)


def yiyan(type):
    global z, tt
    url = 'https://v1.hitokoto.cn/' + "?c=" + type
    strhtml = requests.get(url)
    html = strhtml.text
    strlist = html.split(',')
    i = 0
    e = 0
    for value in strlist:
        i = i + 1
        if i == 3:
            s = value.split(':')
            ns = s[1]
            ns = ns.strip('"')
            z = ns
        if i == 5:
            s = value.split(':')
            tt = s[1]
            tt = str(tt)
            tt = tt.strip('"')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    translator = FluentTranslator()
    app.installTranslator(translator)
    window = MyWindow()
    window.show()

    sys.exit(app.exec())
