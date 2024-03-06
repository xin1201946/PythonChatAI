# 程序功能

这是一个使用PyQt框架开发的ChatGPT桌面端应用程序.



## 使用方式

- 下载源码编译 
- 或者 从Release 下载旧版本的 Main.7z 压缩包

  - 解压到任意位置
  - 运行/main/main.exe
  - enjoy！ 😂

## 屏幕截图

主页：

![HomePage](ScreenShort\HomePage.png)

设置页：

![settingsPage](ScreenShort\settingsPage.png)

## 相关项目地址



1. [UI-PyQt-Fluent](https://github.com/zhiyiYo/PyQt-Fluent-Widgets/tree/master)

   [PyQt6](https://www.qt.io/download-open-source)



# **二次开发指南**



## 检查

当你下载所有的源代码文件后，应当包含以下文件：

- image 文件夹
  - image.jpg （在Log子界面上方显示的文字画）和 MAIN.png（个性化头像）
- plugin文件夹
  - 你的拓展插件
- setting.py  和 setting.ui （PyQT的界面文件）
- ChatForm.py 和ChatForm.ui（PyQT的界面文件）
- ico.ico（应用图标）
- main.py（应用的主要代码区）


## 简介

本程序的类及相关介绍：

| 类（Class）                           | 说明                 |
| ------------------------------------- | -------------------- |
| class ProfileCard(QWidget)            | 在程序空白处右击菜单 |
| class NetworkCheckerThread(QThread)   | 网络检查工具         |
| class SystemTrayIcon(QSystemTrayIcon) | 应用托盘图标         |
| class Window(FluentWindow)            | 程序主页面           |
| class MyWindow(QFrame)                | 程序主子页面         |
| class SETTINGS(QFrame)                | 程序“设置”子页面     |
| class Worker(QThread)                 | 跨线程实现访问OpenAI |

| 函数（Function） | 说明                                       |
| ---------------- | ------------------------------------------ |
| yiyan(type)      | 随机一言。结果返回到变量 yytitle, yyinfo中 |

本程序涉及的变量：

| 变量                | 说明                                                         |
| ------------------- | ------------------------------------------------------------ |
| yytitle             | yiyan函数将获取的信息放入此变量> str : title                 |
| yyinfo              | yiyan函数将获取的信息放入此变量> str: info                   |
| temperatureselected | OpenAI的 Temperature 值，介于 0-1之间                        |
| modelselected       | 用户选择的模型名                                             |
| API_URL             | 用户设置或者程序读取的API_URL                                |
| API_KEY             | 用户设置或者程序读取的API_KEY                                |
| historyselected     | 最大保存多少历史记录。较大的值会让AI回答更连贯，但是占用内存很大 |
| model               | OpenAI的模型名 集合，你的更改反映到 设置 中的Model列表框中   |
| network             | 是否存在网络（你需要请求检查完网络连接）                     |

### Window类

本类是整个程序的主类，也是程序启动后负责多页面显示的类。下面是本类的特殊函数：

| 函数                                     | 说明                                 |
| ---------------------------------------- | ------------------------------------ |
| showyiyan                                | 显示一言Tip                          |
| initNavigation                           | 添加子页面                           |
| createInfoInfoBar                        | 所有子页面的信息均通过本函数进行显示 |
| copyyiyan                                | 复制一言的信息到剪贴板               |
| showDialog(self, title, message)         | 显示对话框                           |
| contextMenuEvent                         | 右击菜单在这里进行定制               |
| loadplugin                               | 负责整个插件系统的加载               |
| loadtip(self, title, message, donetitle) | 自定义 加载  对话框                  |
| load_config                              | 加载用户配置                         |

### MyWindow 类

本类主要实现OpenAI交互界面。以下是本类特殊函数：

| 函数              | 说明                                         |
| ----------------- | -------------------------------------------- |
| updataurl         | 当用户点击更新链接时跳转浏览器打开指定页面   |
| send_message      | 核心函数，发送信息到OpenAI，并获取返回信息。 |
| handleTextReady   | （无使用该函数的语句）                       |
| handleWorkerError | 当向OpenAI服务器获取返回信息出错时激活       |

### SETTINGS类

本类主要用于 修改设置，以下是本类的特殊函数：

| 函数        | 说明            |
| ----------- | --------------- |
| initcombo   | 初始化combo控件 |
| load_config | 加载配置        |
| save_config | 保存配置        |



### Worker类

本类并不是子界面，本类用于实现与Open AI交互信息。

## 插件加载

本节重点解释插件加载。位于： Class Window > Function LoadPlugin。

这里贴上实现代码：

```python
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
```

插件要求：

- 插件必须在 APPPATH / Plugin 文件夹下

- 插件不要求名称，但是插件的拓展名必须为.py

- 插件必须包含全局变量：

  - \_APPNAME :应用名

  - \_APPICON：QICON类型

  - \_APPVERSION：str>应用版本

  - 实例：

  - ```python
    global _APPNAME,_APPVERSION,_APPICON,geturl
    _APPNAME = "短视频下载"
    _APPVERSION = "1.0"
    _APPICON = FluentIcon.CLOUD_DOWNLOAD.icon()
    ```

- 插件由MAIN类开始，继承QFrame

- 插件可使用以下库：

  ​	fake_useragent 

  ​	Crypto.Cipher (AES) 

  ​	binascii (b2a_hex, a2b_hex) 

  ​	pyperclip cv2 (OpenCV) 

  ​	json 

  ​	logging 

  ​	os

  ​	sys 

  ​	threading 

  ​	webbrowser 

  ​	glob 

  ​	PIL.Image 

  ​	requests 

  ​	PyQt5及其相关组件 

  ​	openai 

  ​	rsa 

  ​	qfluentwidgets和qframelesswindow中的组件

  > **警告⚠：如果您尝试使用WebView时，请使用 [FramelessWebEngineView](https://github.com/zhiyiYo/PyQt-Fluent-Widgets/blob/master/examples/window/web_engine/demo.py)**

  
  
  

## 其他

​	About  二次开发指南.md

​	修改来自《插件制作指南》

------



> Copyright (c) 2024. 
>
> ​	@Author : Canfeng 
>
> ​	@Email : 1324435230@qq.com 
>
> About ChatAI 
>
> ​	@IDE : PyCharm 
>
> ​	注：本软件遵循 GPLv3协议，请在使用、修改或分发时遵守该协议条款。
