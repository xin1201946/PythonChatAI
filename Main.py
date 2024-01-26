import json
import logging
import pickle
import os
import platform
import subprocess
import sys
import logging
import pyperclip
import requests
from PyQt5 import QtGui
from PyQt5.QtCore import QPoint, Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QStackedWidget, QFrame, QVBoxLayout, QComboBox, QListWidget, QTextEdit, \
    QWidget, QFileDialog, QPushButton, QLineEdit, QLabel, QListWidgetItem, QHBoxLayout
from PyQt5.QtWidgets import QMainWindow
from openai import OpenAI
from qfluentwidgets import InfoBarIcon, InfoBar, InfoBarPosition, \
    InfoBarManager, FluentIcon, FluentTranslator, Action, TransparentDropDownPushButton, setFont, RoundMenu, ComboBox, \
    TextEdit, PushButton
from qfluentwidgets import setTheme, Theme
import form
import datetime

global z, tt

APPname = 'ChatAI For Mac'
APPversion = '1.4.5'
AppComplieTime = '2024/1/26_19:40'
AppFirstComplieTime = '2024/1/10_10:00'

conversation = []
tuxiang = '''                                     

          ---------------------------------------------
             By canf...                    欢迎使用
'''
DEFAULT_API_URL = ""  ##默认的
DEFAULT_API_KEY = ""
API_URL = ""  ##用户自己写的或者从文件读取的
API_KEY = ""
systemrole = ""
module = ""
current_time = datetime.datetime.now().strftime("%Y-%m-%d")

user_dir = os.path.expanduser('~')
target_dir = os.path.join(user_dir, 'Canfeng')
if not os.path.exists(target_dir):
    os.makedirs(target_dir)

# 更改程序的工作目录
os.chdir(target_dir)

work_dir = os.getcwd()

# 创建日志文件的完整路径
log_file = os.path.join(work_dir, current_time + '.log')
logging.basicConfig(
    filename=log_file,
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s')


def is_dark_mode_enabled():  ## 对MAC的暗黑模式进行检测
    if platform.system() != 'Darwin':
        return False

    try:
        result = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'], capture_output=True, text=True)
        output = result.stdout.strip()
        return output == 'Dark'
    except subprocess.CalledProcessError:
        return False


def check_network():
    try:
        requests.get("https://www.bing.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False


class LogWindow(QWidget):
    def __init__(self):
        super(LogWindow, self).__init__()
        self.setObjectName("LogViewer")
        self.setMinimumSize(713, 600)  # 设置窗口最小尺寸为400 x 300
        # 创建日志记录器
        self.logger = logging.getLogger()

        # 创建 UI 组件
        self.combo = ComboBox()
        self.combo.addItems(["ALL", "INFO", "DEBUG"])
        self.log_view = TextEdit()

        layout = QVBoxLayout()
        layout.addWidget(self.combo)
        layout.addWidget(self.log_view)

        self.setLayout(layout)

        # 创建自定义日志处理器并添加到日志记录器
        log_handler = TextEditLogger(self.log_view)
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(log_handler)

        # 设置日志过滤器并添加到处理器
        self.log_view.append(tuxiang)
        self.log_view.append("============================================================\n")
        self.log_view.append("当您的程序崩溃时，请将 Debug 改为 ALL，这非常有助于开发人员诊断错误.\n")
        self.log_view.append("==============================================================")
        self.log_view.append("  时间  [日志级别]  >>                               信息")

        # 连接信号
        self.combo.currentTextChanged.connect(self.update_log_level)

    def update_log_level(self, text):
        if text == "DEBUG":
            self.filter.level = logging.DEBUG
        elif text == "INFO":
            self.filter.level = logging.INFO
        else:
            self.filter.level = logging.NOTSET


class TextEditLogger(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        # 确保跨线程安全调用
        self.widget.append(msg)  # 这里将日志消息附加到文本框


class LogFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno >= self.level


class Worker(QThread):  ##使用另一个线程获取AI返回的信息，让用户即使网络环境差，也不会应用卡死
    textRead = pyqtSignal(str)
    textReady = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)

    def __init__(self, ui, conversation, systemrole, user_question, api_key, api_url):
        logging.info('启动线程>')
        QThread.__init__(self)
        self.ui = ui
        self.conversation = conversation
        self.systemrole = systemrole
        self.user_question = user_question
        self.api_key = api_key
        logging.info('key = sk-****')
        self.api_url = api_url
        logging.info('url = ' + self.api_url)

    def run(self):
        global  conversation
        try:
            self.conversation.append({"role": "system", "content": self.systemrole})
            self.conversation.append({"role": "user", "content": self.user_question})
            client = OpenAI(api_key=self.api_key, base_url=self.api_url)
            responses = client.chat.completions.create(
                model=self.ui.ComboBox.text(),
                stream=True,
                messages=self.conversation,
                temperature=0.5,
            )

            ai_response = ""
            for chunk in responses:
                if len(chunk.choices) > 0 and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    new_content = chunk.choices[0].delta.content
                    ai_response += new_content
                    word = new_content
                    self.textReady.emit(word)
            conversation.append({"role": self.ui.ComboBox.text(), "content": ai_response})
        except Exception as e:
            self.errorOccurred.emit(str(e))


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


class DictEditor(QWidget):
    def __init__(self):
        super(DictEditor, self).__init__()
        global conversation
        self.dict_value = conversation

        # 创建 QVBoxLayout 实例
        self.layout = QVBoxLayout(self)

        # 创建 QHBoxLayout 实例
        self.sub_layout = QHBoxLayout()

        # 创建 QListWidget 实例
        self.list_widget = QListWidget(self)

        # 将字典的键值对添加到 QListWidget
        for item in conversation:
            listWidgetItem = QListWidgetItem(str(item))
            self.list_widget.addItem(listWidgetItem)

        # 连接 QListWidget 的 itemClicked 事件
        self.list_widget.itemClicked.connect(self.itemClicked)

        # 创建 QLabel 和 QLineEdit 实例
        self.label = QLabel('选中的键值对：')
        self.line_edit = QLineEdit(self)

        # 将 QListWidget，QLabel 和 QLineEdit 添加到布局中
        self.sub_layout.addWidget(self.list_widget)
        self.sub_layout.addWidget(self.label)
        self.sub_layout.addWidget(self.line_edit)
        self.layout.addLayout(self.sub_layout)

        # 创建 '保存' 按钮，并将其添加到布局中
        self.save_button = QPushButton('保存', self)
        self.layout.addWidget(self.save_button)
        # 连接 '保存' 按钮的点击事件
        self.save_button.clicked.connect(self.save)

        # 创建 '取消' 按钮，并将其添加到布局中
        self.cancel_button = QPushButton('取消', self)
        self.layout.addWidget(self.cancel_button)
        # 连接 '取消' 按钮的点击事件
        self.cancel_button.clicked.connect(self.cancel)

        # 设置窗口的布局
        self.setLayout(self.layout)

    def itemClicked(self, item):
        # 当 QListWidget 的一个列表项被点击时，将该项的值显示在 QLineEdit 中
        self.label.setText(f'选中的键值对：{item.text().split(":")[0]}')
        self.line_edit.setText(item.text().split(": ")[1])

    def save(self):
        # 获取 QLineEdit 中的文本内容，并更新字典
        key = self.label.text().split("：")[1]
        value = self.line_edit.text()
        self.dict_value[key] = value

    def cancel(self):
        self.close()


class Window(QMainWindow):
    def __init__(self):
        global conversation
        super().__init__()
        self.ui = form.Ui_MainWindow()

        self.ui.setupUi(self)
        self.setWindowTitle("ChatAI For MacOS")
        self.setWindowIcon(FluentIcon.CHAT.icon())
        logging.info('程序启动成功')
        self.setObjectName("HOME")

        ##         变量配置
        conversation = []
        self.api_key = self.ui.PasswordLineEdit.text()
        self.api_url = self.ui.EditableComboBox.text()
        self.load_config()
        self.stateTooltip = None
        self.setWindowIcon(FluentIcon.CHAT.icon())
        ##普通按钮配置
        self.ui.pushButton.clicked.connect(self.send_message)
        self.ui.pushButton_2.clicked.connect(self.save_config)
        ##Combo 的配置
        items = ['OpenAI', 'Google', 'Anthropic']
        self.ui.ComboBox_2.addItems(items)
        self.ui.ComboBox_2.currentTextChanged.connect(self.commboxchange)
        self.ui.ComboBox.clear()
        item = ['gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-4', 'gpt-4-all', 'gpt-4-plus']
        self.ui.ComboBox.addItems(item)
        self.ui.EditableComboBox.addItem("https://api.openai.com/v1/chat/completions",
                                         icon=FluentIcon.HOME_FILL)
        ## Timer

        # 创建一个计时器，并设置每3秒触发一次
        self.timer = QTimer()
        self.timer.timeout.connect(self.darkmode)
        self.timer.start(500)

        ## CommandBar的配置
        self.ui.CommandBar.addAction(Action(FluentIcon.MESSAGE, '刷新一言', triggered=self.showyiyanTip))
        self.ui.CommandBar.addAction(Action(FluentIcon.SHARE, '分享内容', triggered=self.sharetext))
        self.ui.CommandBar.addAction(Action(FluentIcon.FOLDER, '加载对话', triggered=self.load_anytalk))
        self.ui.CommandBar.addAction(Action(FluentIcon.SAVE, '保存对话', triggered=self.save_talk))
        self.ui.CommandBar.addAction(Action(FluentIcon.DELETE, '清空内容', triggered=self.deletetext))
        self.ui.CommandBar.addAction(Action(FluentIcon.SEND, '发送', triggered=self.send_message))
        self.ui.CommandBar.addAction(Action(FluentIcon.CLEAR_SELECTION, '清空记忆', triggered=self.clearmemory))
        self.ui.CommandBar.addSeparator()
        self.ui.TextEdit_4.setText(
            'Name >' + APPname + '\nVersion>' + APPversion + '\n应用初次编译时间>' + AppFirstComplieTime + '\n应用编译时间>' + AppComplieTime)

        ##检查用户网络连接是否正常，及时阻止程序崩溃
        if check_network():
            self.createseccess("您已连接网络", "网络管理程序")
        else:
            self.createWarningInfoBar("请检查您的网络连接!", "网络管理程序", 2000)

        # 从这里开始，程序已经初始化完毕
        self.CustomInfoBar("",
                           "欢迎体验ChatAI For MacOS.😎", 4000)

        self.showyiyanTip()
        self.load_talk()

    def load_anytalk(self):
        global conversation
        file_path = QFileDialog.getOpenFileName(None, "选择文件")
        self.ui.TextEdit.clear()
        with open(file_path[0], 'r', encoding='utf-8') as file:
            data = json.load(file)
            for item in data:
                if 'role' in item:
                    self.ui.TextEdit.append(item['role'] + ': \n' + item['content'])
                    conversation.append(item)
                elif 'command' in item:
                    # 这是一个命令
                    command = item['command']
                    if command == 'clear':
                        self.ui.TextEdit.clear()
                    elif command == 'msgbox':
                        # 弹出指定信息
                        self.CustomInfoBar(message=item['message'], title='TalkCacheLoader', ShowTime=3000)
                        # 实现你的代码

    def load_talk(self):
        global conversation
        path = os.getcwd()
        try:
            with open(path+"/TalkCache.tlk", 'r', encoding='utf-8') as file:
                data = json.load(file)
                for item in data:
                    if 'role' in item:
                        self.ui.TextEdit.append(item['role'] + ': \n' + item['content'])
                        conversation.append(item)
                    elif 'command' in item:
                        # 这是一个命令
                        command = item['command']
                        if command=='model':
                            self.ui.ComboBox.setText(item['Model'])
                            self.ui.ComboBox_2.setText('自定义')
                        elif command=='clear':
                            self.ui.TextEdit.clear()
        except FileNotFoundError:
            logging.error('File Not Found,'+path+"/TalkCache.tlk")
            conversation = []
        except Exception as e:
            logging.error(e)
            conversation = []

    def save_talk(self):
        global conversation
        cloneConversation=conversation
        cloneConversation.append({"command": "model", "Model": self.ui.ComboBox.text()})
        with open("TalkCache.tlk", 'w', encoding='utf-8') as file:
            json.dump(conversation, file, ensure_ascii=False, indent=4)

    def clearmemory(self):
        global conversation
        self.ui.TextEdit.append('\n-------------新对话--------------\n')
        conversation = []

    def darkmode(self):
        if is_dark_mode_enabled():
            setTheme(Theme.DARK)
        else:
            setTheme(Theme.LIGHT)


    def createDropDownButton(self):
        button = TransparentDropDownPushButton('其他', self, FluentIcon.MENU)
        button.setFixedHeight(34)
        setFont(button, 12)
        menu = RoundMenu(parent=self)
        menu.addActions([
            Action(FluentIcon.MESSAGE, '关于', triggered=self.about),
        ])
        button.setMenu(menu)
        return button

    def sharetext(self):
        pyperclip.copy("内容>\n" + self.ui.TextEdit.toPlainText() + "\n By " + os.getlogin())
        self.createseccess("复制成功", "System")

    def deletetext(self):
        self.ui.TextEdit.clear()
        self.createseccess("清除成功", "System")

    def addButton(self, icon, text):
        action = Action(icon, text, self)
        self.ui.CommandBar.addAction(action)

    def commboxchange(self):
        if self.ui.ComboBox_2.text() == "Google":
            item = ['gemini-pro', 'gemini-pro-v', 'gemini-Ultra', 'gemini-Nano']
            self.ui.ComboBox.clear()
            self.ui.ComboBox.addItems(item)
        elif self.ui.ComboBox_2.text() == "Anthropic":
            item = ['claude-2', 'claude-instant-1']
            self.ui.ComboBox.clear()
            self.ui.ComboBox.addItems(item)
        elif self.ui.ComboBox_2.text() == 'OpenAI':
            self.ui.ComboBox.clear()
            item = ['gpt-3.5-turbo', 'gpt-3.5-turbo-16k', 'gpt-4', 'gpt-4-all', 'gpt-4-plus']
            self.ui.ComboBox.addItems(item)

    def save_config(self):
        global API_URL, API_KEY
        API_URL = self.ui.EditableComboBox.text()
        API_KEY = self.ui.PasswordLineEdit.text()

        # 获取用户的家目录和配置文件的路径
        user_dir = os.path.expanduser('~')
        target_dir = os.path.join(user_dir, 'Canfeng')
        config_file_path = os.path.join(target_dir, 'config.json')

        config = {
            "api_url": API_URL,
            "api_key": API_KEY,
        }
        try:
            with open(config_file_path, "w") as config_file:
                json.dump(config, config_file)
        except Exception as e:
            self.createWarningInfoBar("在保存文件时发生错误：\n\t" + str(e), "Error", -1)

    def load_config(self):
        global API_URL, API_KEY

        # 检查和创建目录
        user_dir = os.path.expanduser('~')
        target_dir = os.path.join(user_dir, 'Canfeng')
        check_and_create_dir(target_dir)

        # 检查和创建文件
        config_file_path = os.path.join(target_dir, 'config.json')
        check_and_create_file(config_file_path)

        try:
            with open(config_file_path, "r") as config_file:
                config = json.load(config_file)
                API_URL = config.get("api_url", self.api_url)
                API_KEY = config.get("api_key", self.api_key)

                # 使用加载的值更新UI
                self.ui.EditableComboBox.setText(API_URL)
                self.ui.EditableComboBox.addItem(API_URL, icon=FluentIcon.ADD)
                self.ui.PasswordLineEdit.setText(API_KEY)
        except FileNotFoundError:
            pass

    def createWarningInfoBar(self, message, title, value):
        InfoBar.warning(
            title=title,
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,  # disable close button
            position=InfoBarPosition.TOP,
            duration=value,
            parent=self
        )

    def createseccess(self, message, title):
        content = message
        w = InfoBar(
            icon=InfoBarIcon.SUCCESS,
            title=title,
            content=content,
            orient=Qt.Vertical,  # vertical layout
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=4000,
            parent=self
        )
        w.show()

    def CustomInfoBar(self, title, message, ShowTime):
        w = InfoBar.new(
            icon=FluentIcon.MESSAGE,
            # icon=FluentIcon.GITHUB,
            title=title,
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=ShowTime,
            parent=self
        )
        w.setCustomBackgroundColor('white', '#202020')

    def send_message(self):
        user_question = self.ui.TextEdit_2.toPlainText()
        if self.ui.PasswordLineEdit.text() == "" or self.ui.EditableComboBox.text() == "":
            self.api_url = DEFAULT_API_URL
            self.api_key = DEFAULT_API_KEY
        else:
            self.api_key = self.ui.PasswordLineEdit.text()
            self.api_url = self.ui.EditableComboBox.text()
        systemrole = "在任何时候，请您用中文回复. 然后在加上 表情符号。" + self.ui.TextEdit_3.toPlainText()
        if not user_question:
            self.createWarningInfoBar("你还没输入问题", "System", 4000)
            return
        try:
            if check_network():
                self.worker = Worker(self.ui, conversation, systemrole, user_question, self.api_key, self.api_url)
                if self.worker is not None and self.worker.isRunning():
                    self.worker.terminate()  # Terminate the old worker thread if it's still running
                self.ui.TextEdit.append("\n" + os.getlogin() + ": " + self.ui.TextEdit_2.toPlainText())
                self.ui.TextEdit_2.clear()
                self.ui.TextEdit.moveCursor(QtGui.QTextCursor.End)
                self.ui.TextEdit.setEnabled(False)  # 禁止用户交互
                self.ui.TextEdit.append("\n" + self.ui.ComboBox.text() + ": ")
                self.worker.textReady.connect(self.ui.TextEdit.insertPlainText)
                self.ui.TextEdit.verticalScrollBar().setValue(self.ui.TextEdit.verticalScrollBar().maximum())
                self.ui.TextEdit.setEnabled(True)  # 重新允许用户交互
                self.worker.errorOccurred.connect(self.handleWorkerError)
                self.worker.start()
            else:
                self.createWarningInfoBar("请检查您的网络连接!", "网络管理程序", 4000)
        except Exception as e:
            self.ui.TextEdit.append(f"错误: {e}")
            self.createWarningInfoBar(f"错误: {e}", "System", -1)

    def handleTextReady(self, text):
        pass  # Handle the textReady signal

    def handleWorkerError(self, error):
        self.ui.TextEdit.append(f"错误: {error}")
        self.createWarningInfoBar(f"错误: {error}", "System", -1)
        logging.exception('错误：' + error)

    def clear(self):
        self.ui.TextEdit.clear()

    def about(self):
        self.createaboutInfoBar()

    # setTheme(Theme.DARK)
    # self.setStyleSheet("Demo{background: rgb(32, 32, 32)}")

    def showyiyanTip(self):
        if check_network():
            yiyan("a")
            self.createWarningInfoBar(z, tt, 3000)
            self.ui.label_3.setText(z)
        else:
            self.createWarningInfoBar("请检查您的网络连接!", "网络管理程序", 4000)


def Main():
    app = QApplication(sys.argv)

    translator = FluentTranslator()
    app.installTranslator(translator)

    # 创建 MyWindow 对象
    my_window = Window()
    # 显示 MyWindow
    my_window.show()
    sys.exit(app.exec())


def check_and_create_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def check_and_create_file(filepath):
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump({"api_url": "your default url", "api_key": "your default key"}, f)


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
    Main()
