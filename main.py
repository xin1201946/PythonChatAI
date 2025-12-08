import importlib
from concurrent.futures import ThreadPoolExecutor

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
from plugin_manager import PluginManager
from plugin_manager_ui import PluginManagerUI

global yytitle, yyinfo

# Configuration constants
DEFAULT_THREAD_POOL_WORKERS = 4  # Number of worker threads for background tasks
WORKER_CANCEL_TIMEOUT_MS = 1000  # Timeout in milliseconds for worker thread cancellation

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
		
		# Initialize thread pool for background tasks
		self._executor = ThreadPoolExecutor(max_workers=DEFAULT_THREAD_POOL_WORKERS)
		
		# Start network check in thread pool (non-blocking)
		self._executor.submit(self._check_network_async)
		
		self.stateTooltip = None
		self.show()
		
		# Load config asynchronously
		self._executor.submit(self._load_config_async)
		
		# Load yiyan asynchronously
		self._executor.submit(self._load_yiyan_async)
		
		self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
		setThemeColor(FluentThemeColor.ORANGE_BRIGHT.color())
		self.windowEffect.setAeroEffect(MyWindow.winId(self))
		
		# 创建子界面
		self.home = MyWindow('主页', self)
		self.SETTING = SETTINGS('关于', self)
		
		# Initialize Plugin Manager
		self.plugin_manager = PluginManager('plugin', self)
		self.plugin_manager_ui = PluginManagerUI(self.plugin_manager, self)
		
		# Connect plugin manager signals
		self.plugin_manager.plugin_loaded.connect(self._on_plugin_loaded)
		self.plugin_manager.all_plugins_loaded.connect(self._on_all_plugins_loaded)
		self.plugin_manager.plugin_error.connect(self._on_plugin_error)
		self.plugin_manager.loading_progress.connect(self._on_plugin_loading_progress)
		
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

		# Load plugins asynchronously
		self.plugin_manager.load_plugins_async()
		
		self.createSubInterface()

		# close splash screen
		self.splashScreen.finish()
	
	def _check_network_async(self):
		"""Check network asynchronously."""
		global network
		try:
			response = requests.get("https://cn.bing.com", timeout=5)
			response.raise_for_status()
			network = "true"
		except (requests.exceptions.ConnectionError, requests.Timeout, requests.HTTPError):
			network = "false"
			# Show dialog on main thread
			QTimer.singleShot(0, lambda: self.showDialog('请检查网络连接，注意你的VPN哟~~', '注意'))
	
	def _load_config_async(self):
		"""Load config asynchronously."""
		# Delay config loading to not block UI
		QTimer.singleShot(100, self.load_config)
	
	def _load_yiyan_async(self):
		"""Load yiyan asynchronously."""
		try:
			yiyan('i')
		except Exception as e:
			logger.warning(f"Failed to load yiyan: {e}")
	
	def _on_plugin_loaded(self, plugin_info):
		"""Handle plugin loaded event."""
		if plugin_info.enabled:
			try:
				instance = self.plugin_manager.create_plugin_instance(plugin_info, self)
				if instance:
					self.addSubInterface(instance, plugin_info.icon, plugin_info.name, NavigationItemPosition.SCROLL)
			except Exception as e:
				logger.error(f"Failed to add plugin interface {plugin_info.name}: {e}")
	
	def _on_all_plugins_loaded(self):
		"""Handle all plugins loaded event."""
		logger.info("All plugins loaded")
		self.createInfoInfoBar("所有插件已加载完成", "插件加载", InfoBarIcon.SUCCESS, True, 3000)
	
	def _on_plugin_error(self, plugin_name, error):
		"""Handle plugin error."""
		logger.error(f"Plugin error {plugin_name}: {error}")
		self.createInfoInfoBar(f"插件 {plugin_name} 加载失败: {error}", "插件错误", InfoBarIcon.ERROR, True, 5000)
	
	def _on_plugin_loading_progress(self, current, total):
		"""Handle plugin loading progress."""
		logger.debug(f"Loading plugins: {current}/{total}")

	def createSubInterface(self):
		loop = QEventLoop(self)
		QTimer.singleShot(1000, loop.quit)
		loop.exec()

	def showyiyan(self):
		yiyan('i')
		self.createInfoInfoBar(yyinfo, yytitle, InfoBarIcon.INFORMATION, True, 5000)

	def initNavigation(self):
		self.addSubInterface(self.home, FluentIcon.HOME, '主页', NavigationItemPosition.TOP)
		self.addSubInterface(self.plugin_manager_ui, FluentIcon.APPLICATION, "插件管理", NavigationItemPosition.BOTTOM)
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
		"""
		Legacy plugin loading method. 
		Deprecated: Use plugin_manager.load_plugins_async() instead.
		Kept for backward compatibility.
		"""
		logger.warning("loadplugin() is deprecated. Use plugin_manager.load_plugins_async() instead.")
		# The plugin loading is now handled by PluginManager
		# This method is kept for backward compatibility
		pass

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

	def closeEvent(self, event):
		"""Clean up resources when closing the application."""
		# Cleanup plugin manager
		if hasattr(self, 'plugin_manager'):
			self.plugin_manager.cleanup()
		
		# Shutdown thread pool
		if hasattr(self, '_executor'):
			self._executor.shutdown(wait=False)
		
		super().closeEvent(event)


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
		self.worker = None

	def updataurl(self):
		webbrowser.open_new_tab("https://github.com/xin1201946/PythonChatGPT")

	def send_message(self):
		global API_KEY, API_URL
		user_question = self.ui.TextEdit_2.toPlainText()

		if not user_question:
			return
		try:
			if network == "true":
				# Cancel previous worker if still running
				if self.worker is not None and self.worker.isRunning():
					self.worker.cancel()
					self.worker.wait(WORKER_CANCEL_TIMEOUT_MS)  # Wait for graceful shutdown
					if self.worker.isRunning():
						self.worker.terminate()
				
				self.worker = Worker(self.ui, self.conversation, user_question, API_KEY, API_URL)
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



class Worker(QThread):
	"""
	Worker thread for AI chat requests.
	Uses QThread for seamless Qt integration with proper cancellation support.
	"""
	textRead = pyqtSignal(str)
	textReady = pyqtSignal(str)
	errorOccurred = pyqtSignal(str)
	finished_signal = pyqtSignal()

	def __init__(self, ui, conversation, user_question, api_key, api_url):
		super().__init__()
		self.ui = ui
		self.conversation = conversation
		self.user_question = user_question
		self.api_key = api_key
		self.api_url = api_url
		self._is_cancelled = False

	def cancel(self):
		"""Request cancellation of the worker."""
		self._is_cancelled = True

	@logger.catch
	def run(self):
		try:
			if self._is_cancelled:
				return
				
			if len(self.conversation) >= historyselected:
				self.conversation.pop(0)
			self.conversation.append({"role": "user", "content": self.user_question})
			
			if self._is_cancelled:
				return
				
			client = OpenAI(api_key=self.api_key, base_url=self.api_url)
			responses = client.chat.completions.create(
				model=modelselected,
				stream=True,
				messages=self.conversation,
				temperature=temperatureselected,
			)

			ai_response = ""
			for chunk in responses:
				if self._is_cancelled:
					break
				if len(chunk.choices) > 0 and chunk.choices[0].delta and chunk.choices[0].delta.content:
					new_content = chunk.choices[0].delta.content
					ai_response += new_content
					word = new_content
					self.textReady.emit(word)
			
			if not self._is_cancelled:
				self.conversation.append({"role": "assistant", "content": ai_response})
		except Exception as e:
			if not self._is_cancelled:
				self.errorOccurred.emit(str(e))
		finally:
			self.finished_signal.emit()


if __name__ == '__main__':
	app = QApplication(sys.argv)
	translator = FluentTranslator()
	app.installTranslator(translator)
	w = Window()
	w.show()
	sys.exit(app.exec())
