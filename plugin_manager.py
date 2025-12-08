#  Copyright (c) 2024.
#  @Author  : Canfeng
#  @Email     : 1324435230@qq.com
#  About  plugin_manager.py
#  @IDE        : PyCharm
#  注：本软件遵循 GPLv3协议，请在使用、修改或分发时遵守该协议条款。

"""
Plugin Manager module for ChatAI.
Provides async plugin loading, unloading, and management capabilities.
"""

import importlib
import importlib.util
import glob
import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any
from loguru import logger
from PyQt6.QtCore import QThread, pyqtSignal, QObject


@dataclass
class PluginInfo:
    """Data class to hold plugin information."""
    name: str
    version: str
    icon: Any
    module_name: str
    file_path: str
    enabled: bool = True
    loaded: bool = False
    instance: Any = None


class PluginLoaderThread(QThread):
    """Thread for loading a single plugin asynchronously."""
    plugin_loaded = pyqtSignal(object, object)  # (PluginInfo, error)
    
    def __init__(self, plugin_path: str, parent=None):
        super().__init__(parent)
        self.plugin_path = plugin_path
        
    def run(self):
        try:
            plugin_info = self._load_plugin(self.plugin_path)
            self.plugin_loaded.emit(plugin_info, None)
        except Exception as e:
            logger.error(f"Failed to load plugin {self.plugin_path}: {e}")
            self.plugin_loaded.emit(None, str(e))
    
    def _load_plugin(self, py_file: str) -> Optional[PluginInfo]:
        """Load a single plugin from file."""
        module_name = os.path.splitext(os.path.basename(py_file))[0]
        
        # Skip __init__.py
        if module_name == "__init__":
            return None
            
        try:
            module = importlib.import_module('.' + module_name, package='plugin')
            
            if hasattr(module, 'MAIN') and isinstance(getattr(module, 'MAIN'), type):
                app_name = getattr(module, '_APPNAME', module_name)
                app_version = getattr(module, '_APPVERSION', '1.0')
                app_icon = getattr(module, '_APPICON', None)
                
                return PluginInfo(
                    name=app_name,
                    version=app_version,
                    icon=app_icon,
                    module_name=module_name,
                    file_path=py_file,
                    enabled=True,
                    loaded=True
                )
        except Exception as e:
            logger.error(f"Error loading plugin module {module_name}: {e}")
            raise
        return None


class PluginManager(QObject):
    """
    Plugin Manager class for managing plugin lifecycle.
    Supports async loading, unloading, enabling/disabling plugins.
    """
    
    # Signals
    plugin_loaded = pyqtSignal(object)  # PluginInfo
    plugin_unloaded = pyqtSignal(str)   # plugin name
    plugin_error = pyqtSignal(str, str)  # plugin name, error message
    all_plugins_loaded = pyqtSignal()
    loading_progress = pyqtSignal(int, int)  # current, total
    
    CONFIG_FILE = './plugin_config.json'
    DEFAULT_MAX_WORKERS = 4  # Default number of worker threads for plugin loading
    
    def __init__(self, plugin_dir: str = 'plugin', max_workers: int = None, parent=None):
        super().__init__(parent)
        self.plugin_dir = os.path.abspath(plugin_dir)
        self.plugins: Dict[str, PluginInfo] = {}
        self.plugin_instances: Dict[str, Any] = {}
        self._max_workers = max_workers or self.DEFAULT_MAX_WORKERS
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._loader_threads: List[PluginLoaderThread] = []
        self._pending_loads = 0
        self._load_config()
        
    def _load_config(self):
        """Load plugin configuration from file."""
        self._plugin_config: Dict[str, bool] = {}
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self._plugin_config = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load plugin config: {e}")
            self._plugin_config = {}
    
    def _save_config(self):
        """Save plugin configuration to file."""
        try:
            config = {name: info.enabled for name, info in self.plugins.items()}
            with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save plugin config: {e}")
    
    def _ensure_plugin_dirs(self):
        """Ensure plugin directories exist."""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
        download_dir = os.path.join(self.plugin_dir, 'download')
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        # Add plugin dir to sys.path
        if self.plugin_dir not in sys.path:
            sys.path.append(self.plugin_dir)
    
    def get_plugin_files(self) -> List[str]:
        """Get list of plugin Python files."""
        self._ensure_plugin_dirs()
        return glob.glob(os.path.join(self.plugin_dir, '*.py'))
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins without loading them."""
        py_files = self.get_plugin_files()
        plugin_names = []
        for py_file in py_files:
            module_name = os.path.splitext(os.path.basename(py_file))[0]
            if module_name != "__init__":
                plugin_names.append(module_name)
        return plugin_names
    
    def load_plugins_async(self, callback: Optional[Callable] = None):
        """Load all plugins asynchronously."""
        py_files = self.get_plugin_files()
        self._pending_loads = len([f for f in py_files 
                                   if not os.path.basename(f).startswith('__')])
        
        if self._pending_loads == 0:
            self.all_plugins_loaded.emit()
            return
            
        loaded_count = [0]  # Using list to allow modification in nested function
        
        for py_file in py_files:
            if os.path.basename(py_file).startswith('__'):
                continue
                
            loader = PluginLoaderThread(py_file, self)
            
            def on_loaded(plugin_info, error, file=py_file):
                loaded_count[0] += 1
                self.loading_progress.emit(loaded_count[0], self._pending_loads)
                
                if error:
                    module_name = os.path.splitext(os.path.basename(file))[0]
                    self.plugin_error.emit(module_name, error)
                elif plugin_info:
                    # Check if plugin was disabled in config
                    if plugin_info.name in self._plugin_config:
                        plugin_info.enabled = self._plugin_config[plugin_info.name]
                    self.plugins[plugin_info.name] = plugin_info
                    self.plugin_loaded.emit(plugin_info)
                
                if loaded_count[0] >= self._pending_loads:
                    self.all_plugins_loaded.emit()
                    if callback:
                        callback()
            
            loader.plugin_loaded.connect(on_loaded)
            loader.start()
            self._loader_threads.append(loader)
    
    def load_plugin_sync(self, plugin_name: str) -> Optional[PluginInfo]:
        """Load a single plugin synchronously."""
        py_file = os.path.join(self.plugin_dir, f"{plugin_name}.py")
        if not os.path.exists(py_file):
            logger.error(f"Plugin file not found: {py_file}")
            return None
            
        try:
            module = importlib.import_module('.' + plugin_name, package='plugin')
            
            if hasattr(module, 'MAIN') and isinstance(getattr(module, 'MAIN'), type):
                app_name = getattr(module, '_APPNAME', plugin_name)
                app_version = getattr(module, '_APPVERSION', '1.0')
                app_icon = getattr(module, '_APPICON', None)
                
                plugin_info = PluginInfo(
                    name=app_name,
                    version=app_version,
                    icon=app_icon,
                    module_name=plugin_name,
                    file_path=py_file,
                    enabled=True,
                    loaded=True
                )
                
                if plugin_info.name in self._plugin_config:
                    plugin_info.enabled = self._plugin_config[plugin_info.name]
                    
                self.plugins[plugin_info.name] = plugin_info
                return plugin_info
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            self.plugin_error.emit(plugin_name, str(e))
        return None
    
    def create_plugin_instance(self, plugin_info: PluginInfo, parent=None) -> Any:
        """Create an instance of a loaded plugin."""
        if not plugin_info.loaded:
            logger.error(f"Plugin {plugin_info.name} is not loaded")
            return None
            
        try:
            module = importlib.import_module('.' + plugin_info.module_name, package='plugin')
            instance = module.MAIN(plugin_info.name, parent)
            plugin_info.instance = instance
            self.plugin_instances[plugin_info.name] = instance
            return instance
        except Exception as e:
            logger.error(f"Error creating instance for plugin {plugin_info.name}: {e}")
            self.plugin_error.emit(plugin_info.name, str(e))
        return None
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        if plugin_name not in self.plugins:
            return False
            
        plugin_info = self.plugins[plugin_name]
        
        # Remove instance
        if plugin_name in self.plugin_instances:
            instance = self.plugin_instances.pop(plugin_name)
            if hasattr(instance, 'close'):
                instance.close()
            if hasattr(instance, 'deleteLater'):
                instance.deleteLater()
        
        # Remove from modules
        module_full_name = f'plugin.{plugin_info.module_name}'
        if module_full_name in sys.modules:
            del sys.modules[module_full_name]
        
        plugin_info.loaded = False
        plugin_info.instance = None
        self.plugin_unloaded.emit(plugin_name)
        return True
    
    def reload_plugin(self, plugin_name: str, parent=None) -> Optional[Any]:
        """Reload a plugin."""
        if plugin_name in self.plugins:
            plugin_info = self.plugins[plugin_name]
            self.unload_plugin(plugin_name)
            
            # Reimport
            module_full_name = f'plugin.{plugin_info.module_name}'
            if module_full_name in sys.modules:
                del sys.modules[module_full_name]
                
            new_info = self.load_plugin_sync(plugin_info.module_name)
            if new_info:
                return self.create_plugin_instance(new_info, parent)
        return None
    
    def enable_plugin(self, plugin_name: str):
        """Enable a plugin."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = True
            self._save_config()
    
    def disable_plugin(self, plugin_name: str):
        """Disable a plugin."""
        if plugin_name in self.plugins:
            self.plugins[plugin_name].enabled = False
            self._save_config()
    
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """Check if a plugin is enabled."""
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].enabled
        return True  # Default to enabled for new plugins
    
    def get_loaded_plugins(self) -> List[PluginInfo]:
        """Get list of loaded plugins."""
        return [p for p in self.plugins.values() if p.loaded]
    
    def get_enabled_plugins(self) -> List[PluginInfo]:
        """Get list of enabled plugins."""
        return [p for p in self.plugins.values() if p.enabled]
    
    def cleanup(self):
        """Cleanup resources."""
        # Wait for all loader threads
        for thread in self._loader_threads:
            if thread.isRunning():
                thread.wait()
        self._loader_threads.clear()
        
        # Shutdown executor
        self._executor.shutdown(wait=False)
        
        # Unload all plugins
        for plugin_name in list(self.plugins.keys()):
            self.unload_plugin(plugin_name)
