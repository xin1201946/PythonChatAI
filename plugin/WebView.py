#  Copyright (c) 2024.
#  @Author  : Canfeng
#  @Email     : 1324435230@qq.com
#  About  ABOUT.py
#  @IDE        : PyCharm
#  注：本软件遵循 LGPLv3协议，请在使用、修改或分发时遵守该协议条款。
# coding:utf-8
import sys
import re

from PyQt6.QtCore import Qt, QUrl, QRect, QFileInfo
from PyQt6.QtGui import QIcon, QDesktopServices, QColor
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout, QVBoxLayout, QMainWindow, QWidget, QGridLayout, \
    QFormLayout, QFileDialog
from qfluentwidgets import setTheme, Theme, SubtitleLabel, setFont, SplitFluentWindow, FluentIcon, TabBar, PushButton, \
    LineEdit, PillToolButton, ToolButton, InfoBarPosition, InfoBar, RoundMenu, AvatarWidget, BodyLabel, CaptionLabel, \
    HyperlinkButton, isDarkTheme, Action
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets.components.material import AcrylicMenu
from qfluentwidgets.components.widgets.frameless_window import FramelessWindow
from qframelesswindow import AcrylicWindow
from qframelesswindow.webengine import FramelessWebEngineView
global _APPNAME, _APPVERSION, _APPICON
_APPNAME = "ChatAI"
_APPVERSION = "1.0 Beta"
_APPICON = FluentIcon.GAME.icon()
UrlHistory = ''


class FramelessWebEngineView(QWebEngineView):
    def __init__(self, parent):

        if sys.platform == "win32" and isinstance(parent.window(), AcrylicWindow):
            parent.window().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        super().__init__(parent=parent)
        self.setHtml("")

        if isinstance(self.window(), FramelessWindow):
            self.window().updateFrameless()


class ProfileCard(QWidget):
    """ Profile card """

    def __init__(self, avatarPath: str, name: str, email: str, parent=None):
        super().__init__(parent=parent)
        self.avatar = AvatarWidget(avatarPath, self)
        self.nameLabel = BodyLabel(name, self)
        self.emailLabel = CaptionLabel(email, self)
        self.logoutButton = HyperlinkButton(
            'https://github.com/xin1201946/', 'Github主页', self)

        color = QColor(206, 206, 206) if isDarkTheme() else QColor(96, 96, 96)
        self.emailLabel.setStyleSheet('QLabel{color: ' + color.name() + '}')

        color = QColor(255, 255, 255) if isDarkTheme() else QColor(0, 0, 0)
        self.nameLabel.setStyleSheet('QLabel{color: ' + color.name() + '}')
        setFont(self.logoutButton, 13)

        self.setFixedSize(307, 82)
        self.avatar.setRadius(24)
        self.avatar.move(2, 6)
        self.nameLabel.move(64, 13)
        self.emailLabel.move(64, 32)
        self.logoutButton.move(52, 48)


class MAIN(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("SystemWebview")
        self.gridLayout = QGridLayout(self)

        self.backbutton = ToolButton(self)
        self.backbutton.setIcon(FIF.LEFT_ARROW.icon())
        self.backbutton.clicked.connect(self.back)
        self.gridLayout.addWidget(self.backbutton, 1, 0, 1, 1)

        self.homebutton = ToolButton(self)
        self.homebutton.setIcon(FIF.HOME_FILL.icon())
        self.homebutton.clicked.connect(self.home)
        self.gridLayout.addWidget(self.homebutton, 1, 1, 1, 1)

        self.LineEdit_2 = LineEdit(self)
        self.gridLayout.addWidget(self.LineEdit_2, 1, 3, 1, 1)

        self.LineEdit = LineEdit(self)
        self.gridLayout.addWidget(self.LineEdit, 1, 4, 1, 1)

        self.linkbutton = ToolButton(self)
        self.linkbutton.setIcon(FIF.LINK.icon())
        self.linkbutton.clicked.connect(self.link)
        self.gridLayout.addWidget(self.linkbutton, 1, 5, 1, 1)

        self.webView = FramelessWebEngineView(self)
        self.webView.load(QUrl("https://fystart.com/"))
        self.webView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.webView.customContextMenuRequested.connect(self.contextMenuEvent)
        self.webView.loadFinished.connect(self.on_load_finished)
        self.gridLayout.addWidget(self.webView, 2, 0, 1, 6)
    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key.Key_Return or QKeyEvent.key() == Qt.Key.Key_Enter:
            if self.LineEdit.hasFocus():
                self.link()

    def contextMenuEvent(self, e) -> None:
        menu = AcrylicMenu(parent=self)

        card = ProfileCard(avatarPath='image/MAIN.png', name='CanFeng', email='1324435230@qq.com', parent=menu)
        menu.addWidget(card, selectable=False)
        # menu.addWidget(card, selectable=True, onClick=lambda: print('666'))

        menu.addSeparator()
        menu.addActions([
            Action(FluentIcon.LEFT_ARROW, '返回', triggered=self.back),
            Action(FluentIcon.HOME_FILL, '主页', triggered=self.home),
            Action(FluentIcon.RIGHT_ARROW, '前进', triggered=self.forward),
            Action(FluentIcon.RETURN, '刷新', triggered=self.reload),
            Action(FluentIcon.INFO, 'WebKit 537.36  Chrome 112.0.5615.213'),
        ])
        menu.addSeparator()
        menu.exec(self.webView.mapToGlobal(e))

    def reload(self):
        self.webView.reload()

    def on_load_finished(self, success):
        global UrlHistory
        if success:
            # 获取当前URL

            url = self.webView.url().toString()
            if UrlHistory != url:
                UrlHistory = url
                self.LineEdit_2.setText(url)

                # 获取页面标题
                self.webView.page().titleChanged.connect(self.on_title_changed)

    def on_title_changed(self, title):
        self.LineEdit.setText('')
        self.LineEdit.setPlaceholderText(title)

    def back(self):
        self.webView.back()

    def home(self):
        self.webView.load(QUrl("https://fystart.com/"))

    def link(self):
        text = self.LineEdit.text()

        pattern = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:www|WWW).'# http:// 或 https://
            r'(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)'  # 域名
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        # 如果text是URL，则转换为QUrl
        if re.match(pattern, text):
            self.webView.load(QUrl(text))
        else:
            if text.startswith('www.') or text.startswith('WWW.'):
                self.webView.load(QUrl("http://" + text))
            else:
                self.webView.load(QUrl("https://www.bing.com/search?q=" + text))


