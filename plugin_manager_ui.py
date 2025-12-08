#  Copyright (c) 2024.
#  @Author  : Canfeng
#  @Email     : 1324435230@qq.com
#  About  plugin_manager_ui.py
#  @IDE        : PyCharm
#  注：本软件遵循 GPLv3协议，请在使用、修改或分发时遵守该协议条款。

"""
Plugin Manager UI module for ChatAI.
Provides a user interface for managing plugins.
"""

import os
import subprocess
import platform

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtGui import QIcon
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
    PushButton, PrimaryPushButton, ToggleButton,
    CardWidget, TableWidget, FluentIcon, InfoBar,
    InfoBarPosition, MessageBox, SwitchButton,
    CommandBar, Action, ScrollArea, ExpandLayout
)
from loguru import logger


class PluginCard(CardWidget):
    """Card widget for displaying a single plugin."""
    
    def __init__(self, plugin_info, parent=None, on_toggle=None, on_reload=None):
        super().__init__(parent)
        self.plugin_info = plugin_info
        self.on_toggle_callback = on_toggle
        self.on_reload_callback = on_reload
        self._init_ui()
        
    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        # Plugin info section
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        # Plugin name
        name_label = SubtitleLabel(self.plugin_info.name, self)
        info_layout.addWidget(name_label)
        
        # Plugin version and file
        version_label = CaptionLabel(f"版本: {self.plugin_info.version} | 文件: {self.plugin_info.module_name}.py", self)
        info_layout.addWidget(version_label)
        
        # Status
        status_text = "已加载" if self.plugin_info.loaded else "未加载"
        enabled_text = "已启用" if self.plugin_info.enabled else "已禁用"
        status_label = CaptionLabel(f"状态: {status_text} | {enabled_text}", self)
        info_layout.addWidget(status_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Controls section
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)
        
        # Enable/Disable switch
        self.switch = SwitchButton(self)
        self.switch.setChecked(self.plugin_info.enabled)
        self.switch.checkedChanged.connect(self._on_toggle)
        controls_layout.addWidget(self.switch)
        
        # Reload button
        reload_btn = PushButton("重新加载", self)
        reload_btn.setIcon(FluentIcon.SYNC)
        reload_btn.clicked.connect(self._on_reload)
        controls_layout.addWidget(reload_btn)
        
        layout.addLayout(controls_layout)
        
    def _on_toggle(self, checked):
        if self.on_toggle_callback:
            self.on_toggle_callback(self.plugin_info.name, checked)
            
    def _on_reload(self):
        if self.on_reload_callback:
            self.on_reload_callback(self.plugin_info.name)


class PluginManagerUI(QFrame):
    """Plugin Manager UI page."""
    
    def __init__(self, plugin_manager, main_window=None, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self.main_window = main_window
        self.plugin_cards = {}
        self.setObjectName("PluginManagerUI")
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)
        
        # Title section
        title_layout = QHBoxLayout()
        title = TitleLabel("插件管理器", self)
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # Refresh button
        refresh_btn = PrimaryPushButton("刷新插件列表", self)
        refresh_btn.setIcon(FluentIcon.SYNC)
        refresh_btn.clicked.connect(self._refresh_plugins)
        title_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(title_layout)
        
        # Description
        desc = BodyLabel("管理已安装的插件，可以启用、禁用或重新加载插件。", self)
        main_layout.addWidget(desc)
        
        # Command bar
        self.command_bar = CommandBar(self)
        self.command_bar.addAction(
            Action(FluentIcon.ADD, '启用全部', triggered=self._enable_all)
        )
        self.command_bar.addAction(
            Action(FluentIcon.REMOVE, '禁用全部', triggered=self._disable_all)
        )
        self.command_bar.addSeparator()
        self.command_bar.addAction(
            Action(FluentIcon.FOLDER, '打开插件目录', triggered=self._open_plugin_dir)
        )
        main_layout.addWidget(self.command_bar)
        
        # Plugin list scroll area
        self.scroll_area = ScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.scroll_content = QWidget()
        self.plugin_layout = ExpandLayout(self.scroll_content)
        self.plugin_layout.setContentsMargins(0, 0, 0, 0)
        self.plugin_layout.setSpacing(8)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
        # Statistics label
        self.stats_label = CaptionLabel("", self)
        main_layout.addWidget(self.stats_label)
        
        # Initial load
        self._load_plugin_cards()
        
    def _connect_signals(self):
        """Connect plugin manager signals."""
        self.plugin_manager.plugin_loaded.connect(self._on_plugin_loaded)
        self.plugin_manager.plugin_unloaded.connect(self._on_plugin_unloaded)
        self.plugin_manager.plugin_error.connect(self._on_plugin_error)
        
    def _load_plugin_cards(self):
        """Load plugin cards from plugin manager."""
        # Clear existing cards
        for name, card in self.plugin_cards.items():
            self.plugin_layout.removeWidget(card)
            card.deleteLater()
        self.plugin_cards.clear()
        
        # Add cards for each plugin
        for plugin_info in self.plugin_manager.plugins.values():
            self._add_plugin_card(plugin_info)
            
        self._update_stats()
        
    def _add_plugin_card(self, plugin_info):
        """Add a plugin card."""
        card = PluginCard(
            plugin_info, 
            self,
            on_toggle=self._on_toggle_plugin,
            on_reload=self._on_reload_plugin
        )
        self.plugin_cards[plugin_info.name] = card
        self.plugin_layout.addWidget(card)
        
    def _update_stats(self):
        """Update statistics label."""
        total = len(self.plugin_manager.plugins)
        enabled = len([p for p in self.plugin_manager.plugins.values() if p.enabled])
        loaded = len([p for p in self.plugin_manager.plugins.values() if p.loaded])
        self.stats_label.setText(f"共 {total} 个插件 | {enabled} 个已启用 | {loaded} 个已加载")
        
    def _on_plugin_loaded(self, plugin_info):
        """Handle plugin loaded signal."""
        if plugin_info.name not in self.plugin_cards:
            self._add_plugin_card(plugin_info)
        self._update_stats()
        
    def _on_plugin_unloaded(self, plugin_name):
        """Handle plugin unloaded signal."""
        self._update_stats()
        
    def _on_plugin_error(self, plugin_name, error):
        """Handle plugin error signal."""
        InfoBar.error(
            title=f"插件错误: {plugin_name}",
            content=error,
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=5000
        )
        
    def _on_toggle_plugin(self, plugin_name, enabled):
        """Handle plugin enable/disable toggle."""
        if enabled:
            self.plugin_manager.enable_plugin(plugin_name)
            InfoBar.success(
                title="插件已启用",
                content=f"{plugin_name} 将在下次启动时加载",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
        else:
            self.plugin_manager.disable_plugin(plugin_name)
            InfoBar.warning(
                title="插件已禁用",
                content=f"{plugin_name} 将在下次启动时不加载",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000
            )
        self._update_stats()
        
    def _on_reload_plugin(self, plugin_name):
        """Handle plugin reload."""
        if self.main_window:
            w = MessageBox(
                "重新加载插件",
                f"确定要重新加载插件 '{plugin_name}' 吗？\n这可能会影响正在使用该插件的功能。",
                self.main_window
            )
            if w.exec():
                try:
                    self.plugin_manager.reload_plugin(plugin_name, self.main_window)
                    InfoBar.success(
                        title="插件已重新加载",
                        content=f"{plugin_name} 重新加载成功",
                        parent=self,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=3000
                    )
                except Exception as e:
                    InfoBar.error(
                        title="重新加载失败",
                        content=str(e),
                        parent=self,
                        position=InfoBarPosition.TOP_RIGHT,
                        duration=5000
                    )
        self._load_plugin_cards()
        
    def _refresh_plugins(self):
        """Refresh plugin list."""
        self.plugin_manager.load_plugins_async(self._load_plugin_cards)
        InfoBar.info(
            title="刷新中",
            content="正在刷新插件列表...",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000
        )
        
    def _enable_all(self):
        """Enable all plugins."""
        for plugin_name in self.plugin_manager.plugins.keys():
            self.plugin_manager.enable_plugin(plugin_name)
        self._load_plugin_cards()
        InfoBar.success(
            title="已启用全部插件",
            content="所有插件将在下次启动时加载",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000
        )
        
    def _disable_all(self):
        """Disable all plugins."""
        for plugin_name in self.plugin_manager.plugins.keys():
            self.plugin_manager.disable_plugin(plugin_name)
        self._load_plugin_cards()
        InfoBar.warning(
            title="已禁用全部插件",
            content="所有插件将在下次启动时不加载",
            parent=self,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000
        )
        
    def _open_plugin_dir(self):
        """Open plugin directory in file explorer."""
        plugin_dir = self.plugin_manager.plugin_dir
        if platform.system() == 'Windows':
            os.startfile(plugin_dir)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', plugin_dir])
        else:  # Linux
            subprocess.run(['xdg-open', plugin_dir])
