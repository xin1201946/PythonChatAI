import importlib

import cv2
from fake_useragent import UserAgent
import json
import wmi
import hashlib
import uuid
from binascii import b2a_hex, a2b_hex
from loguru import logger
import pandas.io.clipboard as cb
import json

import logging
import os
import sys
import threading
import webbrowser
import glob
import PIL.Image as Image
import pyperclip
import requests
from PyQt6 import QtGui, QtCore
from qfluentwidgets.components.material import AcrylicMenu

from qframelesswindow.webengine import FramelessWebEngineView
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QPoint, Qt, QThread, pyqtSignal, QTimer, QEventLoop, QSize, pyqtSlot, QRect, QUrl
from PyQt6.QtGui import QFont, QPixmap, QIcon, QImage, QPainter, QColor, QBrush, QDesktopServices
from PyQt6.QtWidgets import QApplication, QStackedWidget, QVBoxLayout, QFrame, QCompleter, QWidget, QInputDialog, \
	QMessageBox, QFileDialog, QSystemTrayIcon
from qfluentwidgets import FluentTranslator, InfoBarIcon, InfoBar, PushButton, setTheme, Theme, FluentIcon, \
	InfoBarPosition, InfoBarManager, StateToolTip, SystemTrayMenu
from openai import OpenAI
from qfluentwidgets import Dialog, TextEdit, FluentWindow, NavigationItemPosition, SplashScreen, NavigationWidget, \
	isDarkTheme, MessageBox, FlyoutViewBase, BodyLabel, PrimaryPushButton, Flyout, FlyoutView, CaptionLabel, \
	HyperlinkButton, AvatarWidget, NavigationAvatarWidget
from qfluentwidgets import setTheme, Theme, ComboBox, PushButton
from qfluentwidgets import setThemeColor, FluentThemeColor
from qfluentwidgets import (RoundMenu, FluentIcon, Action, BodyLabel,
                            HyperlinkButton, CaptionLabel, setFont, setTheme, Theme, isDarkTheme)
from qfluentwidgets.components.widgets.frameless_window import FramelessWindow
from qfluentwidgets.window.stacked_widget import StackedWidget
from importlib import import_module
import ChatForm
import setting

global yytitle, yyinfo

temperatureselected = 0.2
modelselected = ''
API_URL = ""  # 用户自己写的或者从文件读取的
API_KEY = ""
historyselected = 5

yyinfo = '哎呀，没想到你竟然没网络'
yytitle = '快点关闭你的加速器！'
network = "true"

model = ['gpt-4', 'gpt-4-0314', 'gpt-4-0613', 'gpt-4-32k', 'gpt-4-32k-0314', 'gpt-4-32k-0613', 'gpt-3.5-turbo' \
	, 'gpt-3.5-turbo-0301', 'gpt-3.5-turbo-0613', 'gpt-3.5-turbo-16k', 'gpt-3.5-turbo-16k-0613', 'gpt4-all', \
	     'gpt-4-all', 'gpt-4-plus', 'gpt-4-open', 'gpt-3.5-turbo-0125', 'gpt-4-0125-preview']


class ProfileCard(QWidget):

	def __init__(self, avatarPath: str, name: str, email: str, parent=None):
		super().__init__(parent=parent)
		self.avatar = AvatarWidget(avatarPath, self)
		self.nameLabel = BodyLabel(name, self)
		self.emailLabel = CaptionLabel(email, self)
		self.logoutButton = HyperlinkButton(
			'https://github.com/xin1201946/', '访问我的Github主页', self)

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


class NetworkCheckerThread(QThread):
	# 创建一个自定义信号，用于在任务完成时发送结果
	finished = pyqtSignal(bool)

	def run(self):
		"""
		在另一个线程中运行网络检查，并发出完成信号。
		"""
		result = self.check_network()
		self.finished.emit(result)  # 发送信号

	@staticmethod
	def check_network():
		global network
		try:
			response = requests.get("https://cn.bing.com", timeout=5)
			response.raise_for_status()
			network = "true"
			return True
		except (requests.exceptions.ConnectionError, requests.Timeout, requests.HTTPError):
			network = "false"
			return False


class SystemTrayIcon(QSystemTrayIcon):

	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setIcon(parent.windowIcon())
		self.setToolTip('ChatAI 正在运行...')

		self.menu = SystemTrayMenu(parent=parent)
		self.menu.addActions([
			Action('一言', triggered=self.yiyan),
		])
		self.setContextMenu(self.menu)

	def yiyan(self):
		yiyan('i')
		content = yyinfo+'--'+yytitle
		w = MessageBox(
			title='一言',
			content=content,
			parent=self.parent()
		)
		w.yesButton.setText('关闭')
		w.cancelButton.setVisible(False)
		w.exec()


class Window(FluentWindow):
	""" 主界面 """

	def __init__(self):
		super().__init__()
		self.setWindowIcon(FluentIcon.CHAT.icon())  # 设置图标

		self.splashScreen = SplashScreen(self.windowIcon(), self)
		self.splashScreen.setIconSize(QSize(102, 102))

		log_file = logger.add('ChatAI.log')
		network_thread = NetworkCheckerThread()
		network_thread.start()  # 网络检测线程
		self.stateTooltip = None
		self.show()
		self.load_config()
		yiyan('i')
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		setThemeColor(FluentThemeColor.ORANGE_BRIGHT.color())
		self.windowEffect.setAeroEffect(MyWindow.winId(self))
		# 创建子界面
		self.home = MyWindow('主页', self)
		self.SETTING = SETTINGS('关于', self)
		self.navigationInterface.addWidget(
			routeKey='avatar',
			widget=NavigationAvatarWidget('CanFeng', 'image/MAIN.png'),
			onClick=self.showyiyan,
			position=NavigationItemPosition.BOTTOM
		)
		self.systemTrayIcon = SystemTrayIcon(self)
		self.systemTrayIcon.show()
		self.initNavigation()
		self.initWindow()

		if network == "true":
			self.loadplugin()
		elif network == "false":
			self.showDialog('请检查网络连接，注意你的VPN哟~~', '注意')
			# create other subinterfaces
		self.createSubInterface()

		# close splash screen
		self.splashScreen.finish()

	def createSubInterface(self):
		loop = QEventLoop(self)
		QTimer.singleShot(1000, loop.quit)
		loop.exec()

	def showyiyan(self):
		yiyan('i')
		self.createInfoInfoBar(yyinfo, yytitle, InfoBarIcon.INFORMATION, True, 5000)

	def initNavigation(self):
		self.addSubInterface(self.home, FluentIcon.HOME, '主页', NavigationItemPosition.TOP)
		self.addSubInterface(self.SETTING, FluentIcon.SETTING, "设置", NavigationItemPosition.BOTTOM)

	def initWindow(self):
		self.resize(900, 700)
		self.setWindowTitle('ChatAI')

	@logger.catch
	def createInfoInfoBar(self, message: str, title: str, ICON, isClosable: bool, ShowTime: int):
		w = InfoBar(
			icon=ICON,
			title=title,
			content=message,
			orient=Qt.Orientation.Vertical,  # vertical layout
			isClosable=isClosable,
			position=InfoBarPosition.TOP_RIGHT,
			duration=ShowTime,
			parent=self
		)
		# w.addWidget(PushButton('Action'))
		w.show()

	def copyyiyan(self):

		cb.copy(yyinfo)

	def showDialog(self, title, message):
		title = title
		content = message
		w = Dialog(title, content, self)
		# w.setTitleBarVisible(False)
		# w.setContentCopyable(True)
		if w.exec():
			print('Yes button is pressed')
		else:
			print('Cancel button is pressed')

	def contextMenuEvent(self, e) -> None:
		menu = AcrylicMenu(parent=self)

		# add custom widget
		card = ProfileCard('image/MAIN.png', 'CanFeng', '1324435230@qq.com', menu)
		menu.addWidget(card, selectable=False)
		# menu.addWidget(card, selectable=True, onClick=lambda: print('666'))

		menu.addSeparator()
		menu.addActions([
			Action(FluentIcon.GITHUB, '访问开源ChatAI', triggered=MyWindow.updataurl),
			Action(FluentIcon.MESSAGE, yyinfo + "--" + yytitle, triggered=self.copyyiyan),
		])
		menu.addSeparator()
		menu.exec(e.globalPos())

	@logger.catch
	def loadplugin(self):
		folder_path = 'plugin'  # 这是一个相对路径，根据实际情况修改

		if not os.path.exists(folder_path):
			os.makedirs(folder_path)
		folder_path = 'plugin/download/'  # 这是一个相对路径，根据实际情况修改

		if not os.path.exists(folder_path):
			os.makedirs(folder_path)
		# 插件目录路径
		plugin_dir = os.path.abspath(os.path.join(os.getcwd(), 'plugin\\'))
		if plugin_dir not in sys.path:
			sys.path.append(plugin_dir)
		# 获取插件目录下所有 .py 文件的绝对路径
		py_files = glob.glob(os.path.join(plugin_dir, '*.py'))

		# 遍历每个 .py 文件
		for py_file in py_files:
			# 跳过 __init__.py 之类的特殊模块
			if py_file.endswith("__init__.py"):
				continue

			# 导入模块，例如：如果文件名为 plugin/sub.py，则导入 sub 模块
			module_name = os.path.splitext(os.path.basename(py_file))[0]
			# 去除插件目录部分，仅保留模块名（根据实际情况调整）
			module_name = module_name.replace(f"{os.path.basename(plugin_dir)}.", '')
			module = importlib.import_module('.' + module_name, package='plugin')
			module_name = module_name + ".py"
			if hasattr(module, 'MAIN') and isinstance(getattr(module, 'MAIN'), type):
				app_name = getattr(module, '_APPNAME')
				app_version = getattr(module, '_APPVERSION')
				app_icon = getattr(module, '_APPICON')

				self.SubWindowClass = module.MAIN(app_name, self)
				self.addSubInterface(self.SubWindowClass, app_icon, app_name, NavigationItemPosition.SCROLL)
			else:
				continue

	def loadtip(self, title, message, donetitle):
		if self.stateTooltip:
			self.stateTooltip.setContent(donetitle)
			self.stateTooltip.setState(True)
			self.stateTooltip = None
		else:
			self.stateTooltip = StateToolTip(title, message, self)
			self.stateTooltip.move(510, 30)
			self.stateTooltip.show()

	@logger.catch
	def load_config(self):
		global API_URL, API_KEY, temperatureselected, modelselected, historyselected
		try:
			self.loadtip("加载", "正在加载配置文件,请稍后", "加载完成")
			with open('./config.json', 'r') as config_file:
				config_data = json.load(config_file)
		except FileNotFoundError:
			# 如果文件不存在，则创建一个包含默认值的配置文件
			self.loadtip("加载", "正在加载配置文件,请稍后", "文件不存在，以为您创建文件！")
			config_data = {
				"api_url": API_URL,
				"api_key": API_KEY,
				"temperature": temperatureselected,
				"model": modelselected,
				"history": historyselected
			}
			with open("./config.json", "w") as config_file:
				json.dump(config_data, config_file, indent=4)

		# 更新全局变量
		self.loadtip("加载", "正在加载配置文件,请稍后", "加载完成")
		self.createInfoInfoBar(str(config_data), '配置文件信息', InfoBarIcon.INFORMATION, True, 5000)
		API_URL = config_data.get("api_url", API_URL)
		API_KEY = config_data.get("api_key", API_KEY)
		temperatureselected = config_data.get("temperature", temperatureselected)
		modelselected = config_data.get("model", modelselected)
		historyselected = config_data.get("history", historyselected)


def yiyan(type):
	global yytitle, yyinfo
	url = 'https://v1.hitokoto.cn/?c='+type
	response = requests.get(url)
	if response.status_code == 200:
		# 解析JSON响应
		data = json.loads(response.text)
		yyinfo = data.get("hitokoto")
		yytitle = data.get("from")


class MyWindow(QFrame):

	def __init__(self, text: str, parent=None):
		super().__init__()
		self.ui = ChatForm.Ui_Frame()
		self.ui.setupUi(self)
		self.setObjectName("HOME")
		self.ui.PushButton.clicked.connect(self.send_message)
		self.ui.CommandBar.addAction(Action(FluentIcon.SEND, '发送', triggered=self.send_message, shortcut='Alt+S'))
		self.ui.CommandBar.addSeparator()
		self.ui.TextEdit.setText(yyinfo+'\n\n'+'AI:\n 有什么可以帮助您的吗？')
		self.conversation = []
		self.conversation.append({"role": "system", "content": "您回答时尽量回复中文，并加上表情"})
		self.conversation.append({"role": "assistant", "content": "有什么可以帮助您的吗？[开心][疑问]"})

	def updataurl(self):
		webbrowser.open_new_tab("https://github.com/xin1201946/PythonChatGPT")

	def send_message(self):
		global API_KEY, API_URL
		user_question = self.ui.TextEdit_2.toPlainText()

		if not user_question:
			return
		try:
			if network == "true":
				self.worker = Worker(self.ui, self.conversation, user_question, API_KEY, API_URL)
				if self.worker is not None and self.worker.isRunning():
					self.worker.terminate()  # Terminate the old worker thread if it's still running
				self.ui.TextEdit.append("\n" + os.getlogin() + ": " + self.ui.TextEdit_2.toPlainText())
				self.ui.TextEdit_2.clear()
				self.ui.TextEdit.moveCursor(QtGui.QTextCursor.MoveOperation.End)
				self.ui.TextEdit.append("AI: \n")
				self.worker.textReady.connect(self.ui.TextEdit.insertPlainText)
				self.ui.TextEdit.verticalScrollBar().setValue(self.ui.TextEdit.verticalScrollBar().maximum())

				self.worker.errorOccurred.connect(self.handleWorkerError)
				self.worker.start()
			else:
				print('Error')
		except Exception as e:
			window = Window
			window.showDialog(self, "错误", f"错误: {e}")

	def handleTextReady(self, text):
		"""

		:param text:
		"""
		pass  # Handle the textReady signal

	def handleWorkerError(self, error):
		"""

		:param error:
		"""
		self.ui.TextEdit.append(f"错误: {error}")


class SETTINGS(QFrame):
	def __init__(self, text: str, parent=None):
		super().__init__()
		self.ui = setting.Ui_Frame()
		self.ui.setupUi(self)
		self.initcombo()
		self.setObjectName("SETTINGS")
		self.ui.HyperlinkButton.clicked.connect(self.load_config)
		self.ui.TextEdit.setText(API_URL)
		self.ui.TextEdit.setPlaceholderText("请输入API_URL")
		self.ui.TextEdit_2.setText(API_KEY)
		self.ui.PushButton.clicked.connect(self.save_config)
		self.ui.TextEdit_2.setPlaceholderText("请输入API_KEY")
		self.ui.LineEdit.setText(str(temperatureselected))
		self.ui.LineEdit_2.setText(str(historyselected))
		self.ui.EditableComboBox.setCurrentText(modelselected)

	def initcombo(self):
		for item in model:
			self.ui.EditableComboBox.addItem(item)

	def load_config(self):
		global API_URL, API_KEY, temperatureselected, modelselected, historyselected
		try:
			with open('./config.json', 'r') as config_file:
				config_data = json.load(config_file)
		except FileNotFoundError:
			# 如果文件不存在，则创建一个包含默认值的配置文件
			config_data = {
				"api_url": API_URL,
				"api_key": API_KEY,
				"temperature": temperatureselected,
				"model": modelselected,
				"history": historyselected
			}
			with open("./config.json", "w") as config_file:
				json.dump(config_data, config_file, indent=4)

		# 更新全局变量
		API_URL = config_data.get("api_url", API_URL)
		API_KEY = config_data.get("api_key", API_KEY)
		temperatureselected = config_data.get("temperature", temperatureselected)
		modelselected = config_data.get("model", modelselected)
		historyselected = config_data.get("history", historyselected)
		self.ui.TextEdit.setText(API_URL)
		self.ui.TextEdit_2.setText(API_KEY)
		self.ui.LineEdit.setText(str(temperatureselected))
		self.ui.LineEdit_2.setText(str(historyselected))
		self.ui.EditableComboBox.setCurrentText(modelselected)

	def save_config(self):
		global API_URL, API_KEY, temperatureselected, modelselected, historyselected
		API_URL = self.ui.TextEdit.toPlainText()
		API_KEY = self.ui.TextEdit_2.toPlainText()
		modelselected = self.ui.EditableComboBox.text()
		temperatureselected = float(self.ui.LineEdit.text())
		if temperatureselected > 2.0:
			temperatureselected = 2.0
			self.ui.LineEdit.setText("2.0")
		historyselected = int(self.ui.LineEdit_2.text())
		config_data = {
			"api_url": API_URL,
			"api_key": API_KEY,
			"temperature": float(self.ui.LineEdit.text()),
			"model": self.ui.EditableComboBox.text(),
			"history": int(self.ui.LineEdit_2.text())
		}
		with open("./config.json", "w") as config_file:
			json.dump(config_data, config_file, indent=4)



class Worker(QThread):  ##使用另一个线程获取AI返回的信息，让用户即使网络环境差，也不会应用卡死
	textRead = pyqtSignal(str)
	textReady = pyqtSignal(str)
	errorOccurred = pyqtSignal(str)

	def __init__(self, ui, conversation, user_question, api_key, api_url):
		QThread.__init__(self)
		self.ui = ui
		self.conversation = conversation
		self.user_question = user_question
		self.api_key = api_key
		self.api_url = api_url

	@logger.catch
	def run(self):
		try:
			if len(self.conversation) >= historyselected:
				self.conversation.pop(0)
			self.conversation.append({"role": "user", "content": self.user_question})
			client = OpenAI(api_key=self.api_key, base_url=self.api_url)
			responses = client.chat.completions.create(
				model=modelselected,
				stream=True,
				messages=self.conversation,
				temperature=temperatureselected,
			)

			ai_response = ""
			for chunk in responses:
				if len(chunk.choices) > 0 and chunk.choices[0].delta and chunk.choices[0].delta.content:
					new_content = chunk.choices[0].delta.content
					ai_response += new_content
					word = new_content
					self.textReady.emit(word)
			self.conversation.append({"role": "assistant", "content": ai_response})
		except Exception as e:
			self.errorOccurred.emit(str(e))


if __name__ == '__main__':
	app = QApplication(sys.argv)
	translator = FluentTranslator()
	app.installTranslator(translator)
	w = Window()
	w.show()
	sys.exit(app.exec())
