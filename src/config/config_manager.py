    #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件管理器 - 处理应用程序配置的加载、保存和访问
"""

import os
import json
import logging
import multiprocessing
import sys
from PyQt5.QtGui import QColor
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator, ColorConfigItem,
                            Theme, FolderValidator, ConfigSerializer)

# 设置日志记录
logger = logging.getLogger(__name__)

# 默认主题色常量
DEFAULT_THEME_COLOR = "#009faa"

def isWin11():
    """检查是否为 Windows 11"""
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000

class ThemeSerializer(ConfigSerializer):
    """主题序列化器"""
    
    def serialize(self, theme):
        if theme == Theme.DARK:
            return "dark"
        elif theme == Theme.LIGHT:
            return "light"
        else:
            return "auto"
    
    def deserialize(self, value: str):
        if value == "dark":
            return Theme.DARK
        elif value == "light":
            return Theme.LIGHT
        else:
            return Theme.AUTO

class AppConfig(QConfig):
    """应用程序配置类 - 使用官方qconfig系统"""
    
    # 基本配置
    language = OptionsConfigItem(
        "General", "Language", "auto", OptionsValidator(["auto", "en", "zh"]), restart=True)
    theme = OptionsConfigItem(
        "General", "Theme", Theme.AUTO, OptionsValidator([Theme.LIGHT, Theme.DARK, Theme.AUTO]), ThemeSerializer())
    
    # 界面缩放配置
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    
    # 主题色配置 - 使用官方ColorConfigItem
    themeColor = ColorConfigItem("Appearance", "ThemeColor", QColor(DEFAULT_THEME_COLOR))
    
    # 窗口效果配置
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    acrylicEnabled = ConfigItem("MainWindow", "AcrylicEnabled", True, BoolValidator())
    
    # 路径配置
    lastDirectory = ConfigItem("Paths", "LastDirectory", "", FolderValidator())
    customOutputDir = ConfigItem("Paths", "CustomOutputDir", "", FolderValidator())
    globalInputPath = ConfigItem("Paths", "GlobalInputPath", "", FolderValidator())  # 将在运行时设置为Roblox默认路径
    lastInputDir = ConfigItem("Paths", "LastInputDir", "", FolderValidator())
    lastAudioInputDir = ConfigItem("Paths", "LastAudioInputDir", "", FolderValidator())
    lastFontInputDir = ConfigItem("Paths", "LastFontInputDir", "", FolderValidator())
    launchFile = ConfigItem("Paths", "LaunchFile", "")
    
    # 性能配置
    threads = RangeConfigItem(
        "Performance", "Threads", min(32, multiprocessing.cpu_count() * 2), 
        RangeValidator(1, 64))
    useMultiprocessing = ConfigItem("Performance", "UseMultiprocessing", False, BoolValidator())
    conservativeMultiprocessing = ConfigItem("Performance", "ConservativeMultiprocessing", True, BoolValidator())
    
    # 功能配置
    classificationMethod = OptionsConfigItem(
        "Features", "ClassificationMethod", "duration", 
        OptionsValidator(["duration", "size", "name"]))
    saveLogs = ConfigItem("Features", "SaveLogs", False, BoolValidator())
    autoOpenOutputDir = ConfigItem("Features", "AutoOpenOutputDir", True, BoolValidator())
    
    # 字体配置
    fontClassificationMethod = OptionsConfigItem(
        "Fonts", "FontClassificationMethod", "family",
        OptionsValidator(["family", "style", "size"]))
    fontThreads = RangeConfigItem(
        "Fonts", "FontThreads", min(4, multiprocessing.cpu_count()), 
        RangeValidator(1, 16))
    
    # 音频转换配置
    convertAudioEnabled = ConfigItem("Features", "ConvertAudioEnabled", False, BoolValidator())
    convertAudioFormat = OptionsConfigItem(
        "Features", "ConvertAudioFormat", "MP3", 
        OptionsValidator(["MP3", "WAV", "FLAC", "AAC", "M4A"]))
    
    # 缓存管理配置
    autoClearCacheEnabled = ConfigItem("Features", "AutoClearCacheEnabled", False, BoolValidator())
    
    # 窗口配置
    alwaysOnTop = ConfigItem("Window", "AlwaysOnTop", False, BoolValidator())
    debugMode = ConfigItem("Debug", "Enabled", False, BoolValidator())
    autoCheckUpdate = ConfigItem("Update", "AutoCheck", True, BoolValidator())

    # UI配置
    disableAvatarAutoUpdate = ConfigItem("UI", "DisableAvatarAutoUpdate", False, BoolValidator())
    greetingEnabled = ConfigItem("UI", "GreetingEnabled", True, BoolValidator())
    logCardHeight = RangeConfigItem("UI", "LogCardHeight", 250, RangeValidator(150, 600))
    


class ConfigManager:
    """配置文件管理器 - 结合官方qconfig和传统配置管理"""

    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        self.config_file = os.path.join(self.config_dir, "config.json")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # PyQt-Fluent-Widgets配置文件路径
        self.qfluent_config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config")
        self.qfluent_config_file = os.path.join(self.qfluent_config_dir, "config.json")
        os.makedirs(self.qfluent_config_dir, exist_ok=True)
        
        # 创建配置实例
        self.cfg = AppConfig()
        
        # 加载现有配置（向后兼容）
        self.load_existing_config()
        
        # 使用qconfig加载配置
        qconfig.load(self.config_file, self.cfg)
        
        # 初始化路径管理器
        self.path_manager = None
        self._init_path_manager()
        
        # 连接配置变更信号
        self._connect_config_signals()
        
    def _init_path_manager(self):
        """初始化路径管理器"""
        try:
            from src.management.path_management import PathManager
            self.path_manager = PathManager(self)
            
            # 如果全局输入路径为空，自动设置为Roblox默认路径
            current_path = self.get("global_input_path", "")
            if not current_path:
                default_roblox_path = self.path_manager.get_roblox_default_dir()
                if default_roblox_path:
                    self.set("global_input_path", default_roblox_path)
                    self.save_config()
                    logger.info(f"自动设置全局输入路径为Roblox默认路径: {default_roblox_path}")
                    
        except Exception as e:
            logger.error(f"初始化路径管理器失败: {e}")
            self.path_manager = None

    def load_existing_config(self):
        """加载现有配置文件以保持向后兼容"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    old_config = json.load(f)
                    
                # 迁移旧配置到新系统
                self._migrate_old_config(old_config)
                    
            except Exception as e:
                logger.error(f"加载现有配置失败: {e}")

    def _migrate_old_config(self, old_config):
        """迁移旧配置到新的qconfig系统"""
        try:
            # 语言配置
            if "language" in old_config:
                self.cfg.set(self.cfg.language, old_config["language"])
            
            # 主题配置
            if "theme" in old_config:
                theme_value = old_config["theme"]
                if theme_value == "dark":
                    self.cfg.set(self.cfg.theme, Theme.DARK)
                elif theme_value == "light":
                    self.cfg.set(self.cfg.theme, Theme.LIGHT)
                else:
                    self.cfg.set(self.cfg.theme, Theme.AUTO)
            
            # 界面缩放配置
            if "dpi_scale" in old_config:
                self.cfg.set(self.cfg.dpiScale, old_config["dpi_scale"])
            
            # 主题色配置 - 关键迁移！
            if "theme_color" in old_config and "use_custom_theme_color" in old_config:
                if old_config.get("use_custom_theme_color", False):
                    color_str = old_config["theme_color"]
                    if isinstance(color_str, str) and color_str.startswith('#'):
                        try:
                            color = QColor(color_str)
                            if color.isValid():
                                self.cfg.set(self.cfg.themeColor, color)
                                logger.info(f"迁移主题色配置: {color_str}")
                        except Exception as e:
                            logger.error(f"迁移主题色失败: {e}")
            
            # 其他配置项迁移
            config_mapping = {
                "last_directory": self.cfg.lastDirectory,
                "custom_output_dir": self.cfg.customOutputDir,
                "global_input_path": self.cfg.globalInputPath,
                "last_input_dir": self.cfg.lastInputDir,
                "last_audio_input_dir": self.cfg.lastAudioInputDir,
                "last_font_input_dir": self.cfg.lastFontInputDir,
                "launch_file": self.cfg.launchFile, # 新增迁移
                "dpi_scale": self.cfg.dpiScale,  # 添加DPI缩放配置迁移
                "threads": self.cfg.threads,
                "classification_method": self.cfg.classificationMethod,
                "save_logs": self.cfg.saveLogs,
                "auto_open_output_dir": self.cfg.autoOpenOutputDir,
                "always_on_top": self.cfg.alwaysOnTop,
                "debug_mode": self.cfg.debugMode,
                "auto_check_update": self.cfg.autoCheckUpdate,
                "greeting_enabled": self.cfg.greetingEnabled,
                "disable_avatar_auto_update": self.cfg.disableAvatarAutoUpdate,
            }
            
            for old_key, config_item in config_mapping.items():
                if old_key in old_config:
                    self.cfg.set(config_item, old_config[old_key])
                    
        except Exception as e:
            logger.error(f"配置迁移失败: {e}")

    def _connect_config_signals(self):
        """连接配置变更信号"""
        # 主题变更时同步到PyQt-Fluent-Widgets配置
        self.cfg.themeChanged.connect(self.sync_theme_to_qfluent)
        # 监听主题色配置项的变更
        self.cfg.themeColor.valueChanged.connect(self.sync_theme_to_qfluent)

    def sync_theme_to_qfluent(self):
        """同步主题设置到PyQt-Fluent-Widgets配置文件"""
        try:
            # 默认配置
            qfluent_config = {
                "QFluentWidgets": {
                    "ThemeMode": "Auto",
                    "ThemeColor": "#ffe8b3ff"
                }
            }
            
            # 读取现有配置（如果存在）
            if os.path.exists(self.qfluent_config_file):
                try:
                    with open(self.qfluent_config_file, 'r', encoding='utf-8') as f:
                        qfluent_config = json.load(f)
                except Exception as e:
                    logger.warning(f"读取QFluentWidgets配置失败: {e}")
            
            # 确保QFluentWidgets键存在
            if "QFluentWidgets" not in qfluent_config:
                qfluent_config["QFluentWidgets"] = {}
                
            # 同步主题模式
            theme_mode = self.cfg.get(self.cfg.theme)
            if theme_mode == Theme.DARK:
                qfluent_config["QFluentWidgets"]["ThemeMode"] = "Dark"
            elif theme_mode == Theme.LIGHT:
                qfluent_config["QFluentWidgets"]["ThemeMode"] = "Light"
            else:
                qfluent_config["QFluentWidgets"]["ThemeMode"] = "Auto"
                
            # 同步主题色
            theme_color = self.cfg.get(self.cfg.themeColor)
            if isinstance(theme_color, QColor) and theme_color.isValid():
                # 转换为ARGB格式
                color_name = theme_color.name()  # #RRGGBB
                if len(color_name) == 7:  # #RRGGBB 格式
                    argb_color = f"#ff{color_name[1:]}"  # 添加透明度前缀
                else:
                    argb_color = "#ffe8b3ff"  # 回退到默认色
                qfluent_config["QFluentWidgets"]["ThemeColor"] = argb_color
            else:
                qfluent_config["QFluentWidgets"]["ThemeColor"] = "#ffe8b3ff"
            
            # 保存到PyQt-Fluent-Widgets配置文件
            os.makedirs(os.path.dirname(self.qfluent_config_file), exist_ok=True)
            with open(self.qfluent_config_file, 'w', encoding='utf-8') as f:
                json.dump(qfluent_config, f, indent=4, ensure_ascii=False)
                
            logger.debug("已同步配置到PyQt-Fluent-Widgets")
                
        except Exception as e:
            logger.error(f"同步主题到PyQt-Fluent-Widgets失败: {e}")

    def get(self, key, default=None):
        """获取配置值 - 向后兼容接口"""
        try:
            # 映射旧的配置键到新的配置项
            key_mapping = {
                "language": self.cfg.language,
                "theme": self.cfg.theme,
                "theme_color": self.cfg.themeColor,
                "use_custom_theme_color": None,  # 新系统中不需要这个标志
                "dpi_scale": self.cfg.dpiScale,  # 添加DPI缩放配置映射
                "last_directory": self.cfg.lastDirectory,
                "custom_output_dir": self.cfg.customOutputDir,
                "global_input_path": self.cfg.globalInputPath,
                "last_input_dir": self.cfg.lastInputDir,
                "last_audio_input_dir": self.cfg.lastAudioInputDir,
                "last_font_input_dir": self.cfg.lastFontInputDir,
                "launch_file": self.cfg.launchFile,
                "threads": self.cfg.threads,
                "useMultiprocessing": self.cfg.useMultiprocessing,
                "conservativeMultiprocessing": self.cfg.conservativeMultiprocessing,
                "classification_method": self.cfg.classificationMethod,
                "save_logs": self.cfg.saveLogs,
                "auto_open_output_dir": self.cfg.autoOpenOutputDir,
                "always_on_top": self.cfg.alwaysOnTop,
                "debug_mode": self.cfg.debugMode,
                "debug_mode_enabled": self.cfg.debugMode,  # 别名
                "auto_check_update": self.cfg.autoCheckUpdate,
                "autoCheckUpdate": self.cfg.autoCheckUpdate,  # 添加键名映射
                "greeting_enabled": self.cfg.greetingEnabled,
                "disable_avatar_auto_update": self.cfg.disableAvatarAutoUpdate,
                "log_card_height": self.cfg.logCardHeight,
                # 音频转换配置
                "convert_audio_enabled": self.cfg.convertAudioEnabled,
                "convert_audio_format": self.cfg.convertAudioFormat,
                # 兼容旧的音频转换配置键名
                "convert_enabled": self.cfg.convertAudioEnabled,
                "convert_format": self.cfg.convertAudioFormat,
                # 字体配置
                "font_classification_method": self.cfg.fontClassificationMethod,
                "font_threads": self.cfg.fontThreads,
            }
            
            if key in key_mapping:
                config_item = key_mapping[key]
                if config_item is None:
                    # 特殊处理
                    if key == "use_custom_theme_color":
                        # 新系统中，只要主题色不是默认色就算自定义
                        current_color = self.cfg.get(self.cfg.themeColor)
                        default_color = QColor(DEFAULT_THEME_COLOR)
                        return current_color != default_color
                    return default
                    
                value = self.cfg.get(config_item)
                
                # 特殊处理主题色返回值
                if key == "theme_color" and isinstance(value, QColor):
                    return value.name()  # 返回 #RRGGBB 格式
                elif key == "theme" and isinstance(value, Theme):
                    # 将Theme枚举转换为字符串
                    if value == Theme.DARK:
                        return "dark"
                    elif value == Theme.LIGHT:
                        return "light"
                    else:
                        return "auto"
                elif key == "dpi_scale":
                    return value
                        
                return value
            else:
                logger.warning(f"未知配置键: {key}")
                return default
                
        except Exception as e:
            logger.error(f"获取配置值失败 {key}: {e}")
            return default

    def set(self, key, value):
        """设置配置值 - 向后兼容接口"""
        try:
            # 映射旧的配置键到新的配置项
            key_mapping = {
                "language": self.cfg.language,
                "theme": self.cfg.theme,
                "theme_color": self.cfg.themeColor,
                "use_custom_theme_color": None,  # 新系统中不需要这个标志
                "dpi_scale": self.cfg.dpiScale,  # 添加DPI缩放配置映射
                "last_directory": self.cfg.lastDirectory,
                "custom_output_dir": self.cfg.customOutputDir,
                "global_input_path": self.cfg.globalInputPath,
                "last_input_dir": self.cfg.lastInputDir,
                "last_audio_input_dir": self.cfg.lastAudioInputDir,
                "last_font_input_dir": self.cfg.lastFontInputDir,
                "launch_file": self.cfg.launchFile,
                "threads": self.cfg.threads,
                "useMultiprocessing": self.cfg.useMultiprocessing,
                "conservativeMultiprocessing": self.cfg.conservativeMultiprocessing,
                "classification_method": self.cfg.classificationMethod,
                "save_logs": self.cfg.saveLogs,
                "auto_open_output_dir": self.cfg.autoOpenOutputDir,
                "always_on_top": self.cfg.alwaysOnTop,
                "debug_mode": self.cfg.debugMode,
                "debug_mode_enabled": self.cfg.debugMode,  # 别名
                "auto_check_update": self.cfg.autoCheckUpdate,
                "autoCheckUpdate": self.cfg.autoCheckUpdate,  # 添加键名映射
                "greeting_enabled": self.cfg.greetingEnabled,
                "disable_avatar_auto_update": self.cfg.disableAvatarAutoUpdate,
                "log_card_height": self.cfg.logCardHeight,
                # 音频转换配置
                "convert_audio_enabled": self.cfg.convertAudioEnabled,
                "convert_audio_format": self.cfg.convertAudioFormat,
                # 兼容旧的音频转换配置键名
                "convert_enabled": self.cfg.convertAudioEnabled,
                "convert_format": self.cfg.convertAudioFormat,
                # 字体配置
                "font_classification_method": self.cfg.fontClassificationMethod,
                "font_threads": self.cfg.fontThreads,
            }
            
            if key in key_mapping:
                config_item = key_mapping[key]
                if config_item is None:
                    # 特殊处理
                    if key == "use_custom_theme_color":
                        # 在新系统中这个标志被忽略，因为直接设置颜色即可
                        logger.debug(f"忽略 use_custom_theme_color 设置: {value}")
                    return
                    
                # 特殊处理值转换
                if key == "theme_color":
                    if isinstance(value, str) and value.startswith('#'):
                        color = QColor(value)
                        if color.isValid():
                            value = color
                        else:
                            logger.error(f"无效的颜色值: {value}")
                            return
                elif key == "theme":
                    if isinstance(value, str):
                        if value == "dark":
                            value = Theme.DARK
                        elif value == "light":
                            value = Theme.LIGHT
                        else:
                            value = Theme.AUTO
                elif key == "dpi_scale":
                    if isinstance(value, str):
                        if value == "Auto":
                            value = "Auto"
                        else:
                            try:
                                float_value = float(value)
                                if float_value in [1, 1.25, 1.5, 1.75, 2]:
                                    value = float_value
                                else:
                                    logger.error(f"无效的DPI缩放值: {value}")
                                    return
                            except ValueError:
                                logger.error(f"无效的DPI缩放值: {value}")
                                return
                    elif isinstance(value, (int, float)):
                        if value in [1, 1.25, 1.5, 1.75, 2]:
                            value = float(value)
                        else:
                            logger.error(f"无效的DPI缩放值: {value}")
                            return
                            
                self.cfg.set(config_item, value)
                logger.debug(f"设置配置: {key} = {value}")
                
                # 立即保存配置确保持久化
                qconfig.save()
                
            else:
                logger.warning(f"未知配置键: {key}")
                
        except Exception as e:
            logger.error(f"设置配置值失败 {key}={value}: {e}")
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # qconfig会自动保存，这里主要是为了兼容性
            qconfig.save()
            logger.debug("配置已保存")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
        
    def get_qfluent_config(self):
        """获取QFluentWidgets配置文件内容"""
        try:
            if os.path.exists(self.qfluent_config_file):
                with open(self.qfluent_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"QFluentWidgets": {"ThemeMode": "Auto", "ThemeColor": "#ffe8b3ff"}}
        except Exception as e:
            logger.error(f"读取QFluentWidgets配置失败: {e}")
            return {"QFluentWidgets": {"ThemeMode": "Auto", "ThemeColor": "#ffe8b3ff"}} 