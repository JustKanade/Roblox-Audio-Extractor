#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Roblox音频提取器 - 从Roblox缓存中提取音频文件并按音频长度或大小分类
Roblox Audio Extractor - Extract audio files from Roblox cache and classify by audio duration or size
作者/Author: JustKanade
版本/Version: 0.15
许可/License: GNU Affero General Public License v3.0 (AGPLv3)
"""

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import sys
from PyQt5.QtCore import QCoreApplication

if hasattr(sys, '_MEIPASS'):
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt', 'plugins')
import time
import json
import logging
import threading
import queue
import datetime
import traceback
import hashlib
import multiprocessing
from functools import lru_cache
from typing import Dict, List, Any, Tuple, Set, Optional
from enum import Enum, auto


from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,QButtonGroup,
    QFileDialog, QLabel, QFrame, QSizePolicy, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont


from qfluentwidgets import (
    MSFluentWindow, NavigationItemPosition, setTheme, Theme,
    InfoBar, FluentIcon, PushButton, PrimaryPushButton,
    ComboBox, BodyLabel, CardWidget, TitleLabel, CaptionLabel,
    ProgressBar, CheckBox, RadioButton, TextEdit,
    MessageBox, StateToolTip, InfoBarPosition,
    StrongBodyLabel, SubtitleLabel, DisplayLabel,
    HyperlinkButton, TransparentPushButton, ScrollArea,
    IconWidget, SpinBox, LineEdit, PillPushButton, FlowLayout,
    SplashScreen  
)

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# 延迟导入库列表
_LIBS_IMPORTED = False
gzip = shutil = random = string = getpass = subprocess = ThreadPoolExecutor = Fore = Style = init = None


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# 配置文件管理
class ConfigManager:
    """配置文件管理器"""

    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        self.config_file = os.path.join(self.config_dir, "config.json")
        os.makedirs(self.config_dir, exist_ok=True)
        self.config = self.load_config()

    def load_config(self):
        """加载配置文件"""
        default_config = {
            "language": "auto",  # auto, en, zh
            "theme": "dark",  # light, dark, auto
            "last_directory": "",
            "threads": min(32, multiprocessing.cpu_count() * 2),
            "convert_to_mp3": True,
            "classification_method": "duration"
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置，确保所有必需的键都存在
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                return default_config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return default_config

    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)

    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
        self.save_config()


# 分类方法枚举
class ClassificationMethod(Enum):
    """音频分类方法枚举"""
    DURATION = auto()  # 按时长分类
    SIZE = auto()  # 按大小分类


def import_libs():
    """按需导入库，减少启动时间和内存占用"""
    global gzip, shutil, random, string, hashlib, getpass, multiprocessing
    global subprocess, ThreadPoolExecutor, Fore, Style, init, _LIBS_IMPORTED

    if _LIBS_IMPORTED:
        return

    # 导入标准库
    import gzip
    import shutil
    import random
    import string
    import hashlib
    import getpass
    import multiprocessing
    import subprocess
    from concurrent.futures import ThreadPoolExecutor

    # 导入第三方库
    try:
        from colorama import Fore, Style, init
        init()
    except ImportError:
        # 创建假的colorama对象
        class DummyColorama:
            def __getattr__(self, name):
                return ""

        Fore = DummyColorama()
        Style = DummyColorama()

        def dummy_init():
            pass

        init = dummy_init
        logger.warning("未找到colorama库，将不显示彩色输出。请使用 pip install colorama 安装。")
        logger.warning(
            "Colorama library not found, colored output won't be displayed. Install with: pip install colorama.")

    _LIBS_IMPORTED = True


def get_roblox_default_dir():
    """获取Roblox缓存的默认目录"""
    try:
        username = os.getenv('USERNAME') or os.getenv('USER')

        # 根据操作系统选择合适的路径
        if os.name == 'nt':  # Windows
            return os.path.join("C:", os.sep, "Users", username, "AppData", "Local", "Temp", "Roblox", "sounds") # Roblox changed the http to the folder sounds.
        elif sys.platform == 'darwin':  # macOS
            return os.path.join("/Users", username, "Library", "Caches", "Roblox", "http") #i don't know if roblox added the folder on other platforms
        else:  # Linux 或其他
            return os.path.join(os.path.expanduser("~"), ".local", "share", "Roblox", "http")
    except:
        # 如果发生错误，回退到当前目录
        return os.path.join(os.getcwd(), "Roblox")


class Language(Enum):
    """支持的语言枚举类"""
    ENGLISH = auto()
    CHINESE = auto()


class LanguageManager:
    """语言管理器，处理翻译和语言切换"""

    def __init__(self, config_manager=None):
        """初始化语言管理器，设置支持的语言和翻译"""
        self.ENGLISH = Language.ENGLISH
        self.CHINESE = Language.CHINESE
        self.config_manager = config_manager

        # 翻译字典 - 使用嵌套字典结构更高效
        self._load_translations()

        # 设置当前语言
        if config_manager:
            lang_setting = config_manager.get("language", "auto")
            if lang_setting == "en":
                self.current_language = self.ENGLISH
            elif lang_setting == "zh":
                self.current_language = self.CHINESE
            else:
                self.current_language = self._detect_system_language()
        else:
            self.current_language = self._detect_system_language()

        self._cache = {}  # 添加缓存以提高性能

    def _load_translations(self):
        """加载翻译，分离为单独方法以提高可维护性"""
        self.TRANSLATIONS = {
            "title": {
                self.ENGLISH: "Roblox Audio Extractor v0.15",
                self.CHINESE: "Roblox Audio Extractor v0.15"
            },
            "welcome_message": {
                self.ENGLISH: "Welcome to Roblox Audio Extractor!",
                self.CHINESE: "欢迎使用 Roblox Audio Extractor！"
            },
            "extract_audio": {
                self.ENGLISH: "Extract",
                self.CHINESE: "提取音频"
            },
            "view_history": {
                self.ENGLISH: "History",
                self.CHINESE: "提取历史"
            },
            "clear_history": {
                self.ENGLISH: "Clear History",
                self.CHINESE: "清除历史"
            },
            "language_settings": {
                self.ENGLISH: "Settings",
                self.CHINESE: "设置"
            },
            "about": {
                self.ENGLISH: "About",
                self.CHINESE: "关于"
            },
            'clear_cache': {
                self.ENGLISH: "Cache",
                self.CHINESE: "清除缓存"
            },
            'cache_description': {
                self.ENGLISH: "Clear all audio cache files with 'oggs' in their names from the default cache directory.\n\nUse this when you want to extract audio from a specific game: clear the cache first, then run the game until it's fully loaded before extracting.",
                self.CHINESE: "清除默认缓存目录中所有带'oggs'字样的音频缓存文件。\n\n当你想要提取某一特定游戏的音频时使用：先清除缓存，然后运行游戏直至完全加载后再进行提取。"
            },
            'confirm_clear_cache': {
                self.ENGLISH: "Are you sure you want to clear all audio cache files?\n\nThis operation cannot be undone.",
                self.CHINESE: "确定要清除所有音频缓存文件吗？\n\n此操作无法撤销。"
            },
            'cache_cleared': {
                self.ENGLISH: "Successfully cleared {0} of {1} audio cache files.",
                self.CHINESE: "成功清除了 {1} 个缓存文件中的 {0} 个。"
            },
            'no_cache_found': {
                self.ENGLISH: "No audio cache files found.",
                self.CHINESE: "未找到音频缓存文件。"
            },
            'clear_cache_failed': {
                self.ENGLISH: "Failed to clear cache: {0}",
                self.CHINESE: "清除缓存失败：{0}"
            },
            'cache_location': {
                self.ENGLISH: "Cache Directory",
                self.CHINESE: "缓存目录"
            },
            'cache_dir_not_found': {
                self.ENGLISH: "Cache directory not found.",
                self.CHINESE: "未找到缓存目录。"
            },
            "error_occurred": {
                self.ENGLISH: "An error occurred: {}",
                self.CHINESE: "发生错误：{}"
            },
            "history_stats": {
                self.ENGLISH: "Extract History Statistics",
                self.CHINESE: "提取历史统计"
            },
            "files_recorded": {
                self.ENGLISH: "Files recorded: {}",
                self.CHINESE: "已记录文件：{}"
            },
            "history_file_location": {
                self.ENGLISH: "History file: {}",
                self.CHINESE: "历史文件：{}"
            },
            "confirm_clear_history": {
                self.ENGLISH: "Are you sure you want to clear all extraction history?\n\nThis operation cannot be undone.",
                self.CHINESE: "确定要清除所有提取历史吗？\n\n此操作无法撤销。"
            },
            "history_cleared": {
                self.ENGLISH: "Extraction history has been cleared.",
                self.CHINESE: "提取历史已清除。"
            },
            "operation_cancelled": {
                self.ENGLISH: "Operation cancelled.",
                self.CHINESE: "操作已取消。"
            },
            # 新增分类方法相关翻译
            "classification_method": {
                self.ENGLISH: "Classification Method",
                self.CHINESE: "分类方法"
            },
            "classify_by_duration": {
                self.ENGLISH: "By audio duration (requires FFmpeg)",
                self.CHINESE: "按音频时长分类（需要 FFmpeg）"
            },
            "classify_by_size": {
                self.ENGLISH: "By file size",
                self.CHINESE: "按文件大小分类"
            },
            "ffmpeg_not_found_warning": {
                self.ENGLISH: "⚠ FFmpeg not found. Duration classification may not work correctly.",
                self.CHINESE: "⚠ 未找到 FFmpeg。按时长分类可能无法正常工作。"
            },
            # 语言设置相关
            "restart_required": {
                self.ENGLISH: "Restart Required",
                self.CHINESE: "需要重启"
            },
            "restart_message": {
                self.ENGLISH: "The language change will take effect after restarting the application.\n\nWould you like to restart now?",
                self.CHINESE: "语言更改将在重启应用程序后生效。\n\n您想要现在重启吗？"
            },
            "language_saved": {
                self.ENGLISH: "Language setting saved. Please restart the application.",
                self.CHINESE: "语言设置已保存。请重启应用程序。"
            },
            "current_language": {
                self.ENGLISH: "Current language",
                self.CHINESE: "当前语言"
            },
            "select_language": {
                self.ENGLISH: "Select language",
                self.CHINESE: "选择语言"
            },
            # 主题设置
            "theme_settings": {
                self.ENGLISH: "Theme Settings",
                self.CHINESE: "主题设置"
            },
            "theme_light": {
                self.ENGLISH: "Light Theme",
                self.CHINESE: "浅色主题"
            },
            "theme_dark": {
                self.ENGLISH: "Dark Theme",
                self.CHINESE: "深色主题"
            },
            "theme_system": {
                self.ENGLISH: "Follow System",
                self.CHINESE: "跟随系统"
            },
            "theme_changed": {
                self.ENGLISH: "Theme changed to: {}",
                self.CHINESE: "主题已更改为：{}"
            },
            # 通用UI文本
            "browse": {
                self.ENGLISH: "Browse",
                self.CHINESE: "浏览"
            },
            "start_extraction": {
                self.ENGLISH: "Start Extraction",
                self.CHINESE: "开始提取"
            },
            "processing": {
                self.ENGLISH: "Processing...",
                self.CHINESE: "处理中..."
            },
            "apply": {
                self.ENGLISH: "Apply",
                self.CHINESE: "应用"
            },
            "save": {
                self.ENGLISH: "Save",
                self.CHINESE: "保存"
            },
            "cancel": {
                self.ENGLISH: "Cancel",
                self.CHINESE: "取消"
            },
            "confirm": {
                self.ENGLISH: "Confirm",
                self.CHINESE: "确认"
            },
            "settings": {
                self.ENGLISH: "Settings",
                self.CHINESE: "设置"
            },
            "home": {
                self.ENGLISH: "Home",
                self.CHINESE: "首页"
            },
            "directory": {
                self.ENGLISH: "Directory",
                self.CHINESE: "目录"
            },
            "task_running": {
                self.ENGLISH: "Task Running",
                self.CHINESE: "任务运行中"
            },
            "task_completed": {
                self.ENGLISH: "Task Completed",
                self.CHINESE: "任务完成"
            },
            "task_failed": {
                self.ENGLISH: "Task Failed",
                self.CHINESE: "任务失败"
            },
            "task_canceled": {
                self.ENGLISH: "Task Canceled",
                self.CHINESE: "任务已取消"
            },
            "ready": {
                self.ENGLISH: "Ready",
                self.CHINESE: "就绪"
            },
            "restart_now": {
                self.ENGLISH: "Restart Now",
                self.CHINESE: "立即重启"
            },
            "restart_later": {
                self.ENGLISH: "Restart Later",
                self.CHINESE: "稍后重启"
            },
            "about_description": {
                self.ENGLISH: "An open-source tool for extracting audio files from Roblox cache and converting them to MP3/OGG. Files can be classified by audio duration or file size.",
                self.CHINESE: "一个用于从 Roblox 缓存中提取音频文件并将其转换为 MP3/OGG 的开源工具。文件可以按音频时长或文件大小分类。"
            },
            "features": {
                self.ENGLISH: "Features",
                self.CHINESE: "功能特色"
            },
            "feature_1": {
                self.ENGLISH: "Fast multithreaded extraction",
                self.CHINESE: "快速多线程提取"
            },
            "feature_2": {
                self.ENGLISH: "Smart duplicate detection",
                self.CHINESE: "智能重复检测"
            },
            "feature_3": {
                self.ENGLISH: "Audio classification by duration or size",
                self.CHINESE: "按时长或大小分类音频"
            },
            "feature_4": {
                self.ENGLISH: "Automatic MP3 conversion",
                self.CHINESE: "自动 MP3 转换"
            },
            "default_dir": {
                self.ENGLISH: "Default directory",
                self.CHINESE: "默认目录"
            },
            "input_dir": {
                self.ENGLISH: "Enter directory (press Enter for default)",
                self.CHINESE: "输入目录（按回车使用默认值）"
            },
            "dir_not_exist": {
                self.ENGLISH: "Directory does not exist: {}",
                self.CHINESE: "目录不存在：{}"
            },
            "create_dir_prompt": {
                self.ENGLISH: "Create directory?",
                self.CHINESE: "创建目录吗？"
            },
            "dir_created": {
                self.ENGLISH: "Directory created: {}",
                self.CHINESE: "目录已创建：{}"
            },
            "dir_create_failed": {
                self.ENGLISH: "Failed to create directory: {}",
                self.CHINESE: "创建目录失败：{}"
            },
            "processing_info": {
                self.ENGLISH: "Processing Options",
                self.CHINESE: "处理选项"
            },
            "info_duration_categories": {
                self.ENGLISH: "Files will be organized by audio duration into different folders",
                self.CHINESE: "文件将按音频时长分类到不同文件夹中"
            },
            "info_size_categories": {
                self.ENGLISH: "Files will be organized by file size into different folders",
                self.CHINESE: "文件将按文件大小分类到不同文件夹中"
            },
            "info_mp3_conversion": {
                self.ENGLISH: "You can convert OGG files to MP3 after extraction",
                self.CHINESE: "提取后可以将 OGG 文件转换为 MP3"
            },
            "info_skip_downloaded": {
                self.ENGLISH: "Previously extracted files will be skipped automatically",
                self.CHINESE: "将自动跳过之前提取过的文件"
            },
            "threads_prompt": {
                self.ENGLISH: "Number of threads",
                self.CHINESE: "线程数"
            },
            "threads_min_error": {
                self.ENGLISH: "Number of threads must be at least 1",
                self.CHINESE: "线程数必须至少为 1"
            },
            "threads_high_warning": {
                self.ENGLISH: "Using a high number of threads may slow down your computer",
                self.CHINESE: "使用过多线程可能会降低计算机性能"
            },
            "confirm_high_threads": {
                self.ENGLISH: "Continue with high thread count anyway?",
                self.CHINESE: "是否仍使用这么多线程？"
            },
            "threads_adjusted": {
                self.ENGLISH: "Thread count adjusted to: {}",
                self.CHINESE: "线程数已调整为：{}"
            },
            "input_invalid": {
                self.ENGLISH: "Invalid input, using default value",
                self.CHINESE: "输入无效，使用默认值"
            },
            "extraction_complete": {
                self.ENGLISH: "Extraction completed successfully!",
                self.CHINESE: "提取成功完成！"
            },
            "processed": {
                self.ENGLISH: "Processed: {} files",
                self.CHINESE: "已处理：{} 个文件"
            },
            "skipped_duplicates": {
                self.ENGLISH: "Skipped duplicates: {} files",
                self.CHINESE: "跳过重复：{} 个文件"
            },
            "skipped_already_processed": {
                self.ENGLISH: "Skipped already processed: {} files",
                self.CHINESE: "跳过已处理：{} 个文件"
            },
            "errors": {
                self.ENGLISH: "Errors: {} files",
                self.CHINESE: "错误：{} 个文件"
            },
            "time_spent": {
                self.ENGLISH: "Time spent: {:.2f} seconds",
                self.CHINESE: "耗时：{:.2f} 秒"
            },
            "files_per_sec": {
                self.ENGLISH: "Processing speed: {:.2f} files/second",
                self.CHINESE: "处理速度：{:.2f} 文件/秒"
            },
            "output_dir": {
                self.ENGLISH: "Output directory: {}",
                self.CHINESE: "输出目录：{}"
            },
            "convert_to_mp3_prompt": {
                self.ENGLISH: "Convert to MP3 after extraction",
                self.CHINESE: "提取后转换为 MP3"
            },
            "mp3_conversion_complete": {
                self.ENGLISH: "MP3 conversion completed!",
                self.CHINESE: "MP3 转换完成！"
            },
            "converted": {
                self.ENGLISH: "Converted: {} of {} files",
                self.CHINESE: "已转换：{} / {} 个文件"
            },
            "mp3_conversion_failed": {
                self.ENGLISH: "MP3 conversion failed: {}",
                self.CHINESE: "MP3 转换失败：{}"
            },
            "opening_output_dir": {
                self.ENGLISH: "Opening {} output directory...",
                self.CHINESE: "正在打开 {} 输出目录..."
            },
            "manual_navigate": {
                self.ENGLISH: "Please navigate manually to: {}",
                self.CHINESE: "请手动导航到：{}"
            },
            "no_files_processed": {
                self.ENGLISH: "No files were processed",
                self.CHINESE: "没有处理任何文件"
            },
            "total_runtime": {
                self.ENGLISH: "Total runtime: {:.2f} seconds",
                self.CHINESE: "总运行时间：{:.2f} 秒"
            },
            "canceled_by_user": {
                self.ENGLISH: "Operation canceled by user",
                self.CHINESE: "操作被用户取消"
            },
            "scanning_files": {
                self.ENGLISH: "Scanning for files...",
                self.CHINESE: "正在扫描文件..."
            },
            "found_files": {
                self.ENGLISH: "Found {} files in {:.2f} seconds",
                self.CHINESE: "在 {:.2f} 秒内找到 {} 个文件"
            },
            "no_files_found": {
                self.ENGLISH: "No files found in the specified directory",
                self.CHINESE: "在指定目录中未找到文件"
            },
            "processing_with_threads": {
                self.ENGLISH: "Processing with {} threads...",
                self.CHINESE: "使用 {} 个线程处理..."
            },
            "mp3_category": {
                self.ENGLISH: "MP3",
                self.CHINESE: "MP3"
            },
            "ogg_category": {
                self.ENGLISH: "OGG",
                self.CHINESE: "OGG"
            },
            "readme_title": {
                self.ENGLISH: "Roblox Audio Files - Classification Information",
                self.CHINESE: "Roblox 音频文件 - 分类信息"
            },
            "ffmpeg_not_installed": {
                self.ENGLISH: "FFmpeg is not installed. Please install FFmpeg to convert files and get duration information.",
                self.CHINESE: "未安装 FFmpeg。请安装 FFmpeg 以转换文件并获取时长信息。"
            },
            "no_ogg_files": {
                self.ENGLISH: "No OGG files found to convert",
                self.CHINESE: "未找到要转换的 OGG 文件"
            },
            "mp3_conversion": {
                self.ENGLISH: "Converting {} OGG files to MP3...",
                self.CHINESE: "正在将 {} 个 OGG 文件转换为 MP3..."
            },
            "language_set": {
                self.ENGLISH: "Language set to: {}",
                self.CHINESE: "语言设置为：{}"
            },
            "about_title": {
                self.ENGLISH: "About Roblox Audio Extractor",
                self.CHINESE: "关于 Roblox 音频提取器"
            },
            "about_version": {
                self.ENGLISH: "Version 0.15",
                self.CHINESE: "版本 0.15"
            },
            "about_author": {
                self.ENGLISH: "Created by JustKanade",
                self.CHINESE: "由 JustKanade 制作"
            },
            "about_license": {
                self.ENGLISH: "License: GNU AGPLv3",
                self.CHINESE: "许可协议：GNU AGPLv3"
            },
            "github_link": {
                self.ENGLISH: "View on GitHub",
                self.CHINESE: "在 GitHub 上查看"
            },
            "mp3_conversion_info": {
                self.ENGLISH: "Starting MP3 conversion...",
                self.CHINESE: "开始 MP3 转换..."
            },
            "getting_duration": {
                self.ENGLISH: "Getting audio duration...",
                self.CHINESE: "正在获取音频时长..."
            },
            "duration_unknown": {
                self.ENGLISH: "Unknown duration",
                self.CHINESE: "未知时长"
            },
            "readme_duration_title": {
                self.ENGLISH: "Audio Duration Categories:",
                self.CHINESE: "音频时长分类："
            },
            "readme_size_title": {
                self.ENGLISH: "File Size Categories:",
                self.CHINESE: "文件大小分类："
            },
            "classification_method_used": {
                self.ENGLISH: "Classification method: {}",
                self.CHINESE: "分类方法：{}"
            },
            "classification_by_duration": {
                self.ENGLISH: "by audio duration",
                self.CHINESE: "按音频时长"
            },
            "classification_by_size": {
                self.ENGLISH: "by file size",
                self.CHINESE: "按文件大小"
            },
            "quick_start": {
                self.ENGLISH: "Quick Start",
                self.CHINESE: "快速开始"
            },
            "recent_activity": {
                self.ENGLISH: "Recent Activity",
                self.CHINESE: "最近活动"
            },
            "system_info": {
                self.ENGLISH: "System Information",
                self.CHINESE: "系统信息"
            },
            "cpu_cores": {
                self.ENGLISH: "CPU Cores",
                self.CHINESE: "CPU 核心"
            },
            "recommended_threads": {
                self.ENGLISH: "Recommended Threads",
                self.CHINESE: "推荐线程数"
            },
            "ffmpeg_status": {
                self.ENGLISH: "FFmpeg Status",
                self.CHINESE: "FFmpeg 状态"
            },
            "available": {
                self.ENGLISH: "Available",
                self.CHINESE: "可用"
            },
            "not_available": {
                self.ENGLISH: "Not Available",
                self.CHINESE: "不可用"
            },
            "open_directory": {
                self.ENGLISH: "Open Directory",
                self.CHINESE: "打开目录"
            },
            "copy_path": {
                self.ENGLISH: "Copy Path",
                self.CHINESE: "复制路径"
            },
            "app_settings": {
                self.ENGLISH: "Application Settings",
                self.CHINESE: "应用设置"
            },
            "language_region": {
                self.ENGLISH: "Language & Region",
                self.CHINESE: "语言和地区"
            },
            "appearance": {
                self.ENGLISH: "Appearance",
                self.CHINESE: "外观"
            },
            "performance": {
                self.ENGLISH: "Performance",
                self.CHINESE: "性能"
            },
            "about_section": {
                self.ENGLISH: "About",
                self.CHINESE: "关于"
            },
            "view_history_file": {
                self.ENGLISH: "View History File",
                self.CHINESE: "查看历史文件"
            },
            "history_overview": {
                self.ENGLISH: "History Overview",
                self.CHINESE: "历史记录概览"
            },
            "tech_stack": {
                self.ENGLISH: "Tech Stack",
                self.CHINESE: "技术栈"
            },
            "purpose": {
                self.ENGLISH: "Purpose",
                self.CHINESE: "用途"
            },
            "packaging": {
                self.ENGLISH: "Packaging",
                self.CHINESE: "打包"
            },
            "license": {
                self.ENGLISH: "License",
                self.CHINESE: "开源协议"
            },
            "operating_system": {
                self.ENGLISH: "Operating System",
                self.CHINESE: "操作系统"
            },
            "python_version": {
                self.ENGLISH: "Python Version",
                self.CHINESE: "Python 版本"
            },
            "ui_upgraded": {
                self.ENGLISH: "UI upgraded to PyQt-Fluent-Widget",
                self.CHINESE: "UI 已升级到 PyQt-Fluent-Widgets"
            },
            "config_file_location": {
                self.ENGLISH: "Config file location: {}",
                self.CHINESE: "配置文件位置: {}"
            },
            "total_files": {
                self.ENGLISH: "Total extraction files: {}",
                self.CHINESE: "总提取文件数: {}"
            },
            "avg_files_per_extraction": {
                self.ENGLISH: "Average per extraction: {} files",
                self.CHINESE: "平均每次提取: {} 文件"
            },
            "history_file_size": {
                self.ENGLISH: "History file size: {} KB",
                self.CHINESE: "历史记录大小: {} KB"
            },
            "links_and_support": {
                self.ENGLISH: "Links and Support",
                self.CHINESE: "链接和支持"
            },
            "default_threads": {
                self.ENGLISH: "Default thread count",
                self.CHINESE: "默认线程数"
            },
            "default_mp3_conversion": {
                self.ENGLISH: "Default MP3 conversion",
                self.CHINESE: "默认 MP3 转换"
            },
            "enabled": {
                self.ENGLISH: "Enabled",
                self.CHINESE: "启用"
            },
            "disabled": {
                self.ENGLISH: "Disabled",
                self.CHINESE: "禁用"
            },
            "saved": {
                self.ENGLISH: "Saved: {}",
                self.CHINESE: "已保存: {}"
            },
            "yes": {
                self.ENGLISH: "Yes",
                self.CHINESE: "是"
            },
            "no": {
                self.ENGLISH: "No",
                self.CHINESE: "否"
            }
        }

    @lru_cache(maxsize=128)
    def _detect_system_language(self) -> Language:
        """检测系统语言并返回相应的语言枚举"""
        try:
            import locale
            system_lang = locale.getdefaultlocale()[0]
            if system_lang and ('zh_' in system_lang.lower() or 'cn' in system_lang.lower()):
                return self.CHINESE
            return self.ENGLISH
        except:
            return self.ENGLISH

    def get(self, key: str, *args) -> str:
        """获取指定键的翻译并应用格式化参数"""
        # 检查缓存
        cache_key = (key, self.current_language, args)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 如果键不存在，返回键本身
        if key not in self.TRANSLATIONS:
            return key

        translations = self.TRANSLATIONS[key]
        if self.current_language not in translations:
            # 回退到英语
            if self.ENGLISH in translations:
                message = translations[self.ENGLISH]
            else:
                # 使用任何可用的翻译
                message = next(iter(translations.values()))
        else:
            message = translations[self.current_language]

        # 应用格式化参数
        if args:
            try:
                message = message.format(*args)
            except:
                pass

        # 更新缓存
        if len(self._cache) > 1000:  # 避免缓存无限增长
            self._cache.clear()
        self._cache[cache_key] = message
        return message

    def set_language(self, language: Language) -> None:
        """设置当前语言"""
        if self.current_language != language:
            self.current_language = language
            self._cache.clear()  # 清除缓存

    def get_language_name(self) -> str:
        """获取当前语言的名称"""
        return "中文" if self.current_language == self.CHINESE else "English"

    def save_language_setting(self, language_code: str):
        """保存语言设置到配置文件"""
        if self.config_manager:
            self.config_manager.set("language", language_code)


class ExtractedHistory:
    """管理提取历史，避免重复处理文件"""

    def __init__(self, history_file: str):
        """初始化提取历史"""
        import_libs()  # 确保已导入所需库
        self.history_file = history_file
        self.file_hashes: Set[str] = set()
        self.modified = False  # 跟踪是否修改过，避免不必要的保存
        self._lock = threading.Lock()  # 添加锁以保证线程安全
        self.load_history()

    def load_history(self) -> None:
        """从JSON文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                import json
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    with self._lock:
                        if isinstance(data, list):
                            self.file_hashes = set(data)
                        elif isinstance(data, dict) and 'hashes' in data:
                            self.file_hashes = set(data['hashes'])
        except Exception as e:
            logger.error(f"Error loading history: {str(e)}")
            with self._lock:
                self.file_hashes = set()

    def save_history(self) -> None:
        """将历史记录保存到JSON文件"""
        with self._lock:
            try:
                import json
                # 确保目录存在
                os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

                # 保存历史记录
                with open(self.history_file, 'w') as f:
                    json.dump(list(self.file_hashes), f)
                self.modified = False
                logger.info(f"History saved: {len(self.file_hashes)} files recorded")
            except Exception as e:
                logger.error(f"Error saving history: {str(e)}")

    def add_hash(self, file_hash: str) -> None:
        """添加文件哈希到历史记录"""
        with self._lock:
            if file_hash not in self.file_hashes:
                self.file_hashes.add(file_hash)
                self.modified = True

    def is_processed(self, file_hash: str) -> bool:
        """检查文件是否已处理"""
        with self._lock:
            return file_hash in self.file_hashes

    def clear_history(self) -> None:
        """清除所有提取历史"""
        with self._lock:
            try:
                # 清空内存中的历史记录
                self.file_hashes = set()
                self.modified = True

                # 确保目录存在
                os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

                # 写入空的历史记录文件
                with open(self.history_file, 'w') as f:
                    json.dump([], f)

                logger.info("History cleared successfully")
            except Exception as e:
                logger.error(f"Error clearing history: {str(e)}")
                raise

    def get_history_size(self) -> int:
        """获取历史记录中的文件数量"""
        with self._lock:
            return len(self.file_hashes)


class ContentHashCache:
    """缓存文件内容哈希以检测重复"""

    def __init__(self):
        """初始化哈希缓存"""
        self.hashes: Set[str] = set()
        self.lock = threading.Lock()

    def is_duplicate(self, content_hash: str) -> bool:
        """检查内容哈希是否重复"""
        with self.lock:
            if content_hash in self.hashes:
                return True
            self.hashes.add(content_hash)
            return False

    def clear(self) -> None:
        """清除缓存"""
        with self.lock:
            self.hashes.clear()


class ProcessingStats:
    """跟踪处理统计信息"""

    def __init__(self):
        """初始化统计对象"""
        self.stats = {}
        self.lock = threading.Lock()
        self.reset()
        self._last_update_time = 0
        self._update_interval = 0.1  # 限制更新频率，单位秒

    def reset(self) -> None:
        """重置所有统计数据"""
        with self.lock:
            self.stats = {
                'processed_files': 0,
                'duplicate_files': 0,
                'already_processed': 0,
                'error_files': 0,
                'mp3_converted': 0,
                'mp3_skipped': 0,
                'mp3_errors': 0,
                'last_update': time.time()
            }
            self._last_update_time = 0

    def increment(self, stat_key: str, amount: int = 1) -> None:
        """增加特定统计计数"""
        # 限制更新频率，减少锁争用
        current_time = time.time()
        if current_time - self._last_update_time < self._update_interval:
            return  # 如果距离上次更新时间太短，直接返回

        with self.lock:
            if stat_key in self.stats:
                self.stats[stat_key] += amount
                self.stats['last_update'] = current_time
            else:
                self.stats[stat_key] = amount
            self._last_update_time = current_time

    def get(self, stat_key: str) -> int:
        """获取特定统计计数"""
        with self.lock:
            return self.stats.get(stat_key, 0)

    def get_all(self) -> Dict[str, int]:
        """获取所有统计数据"""
        with self.lock:
            return self.stats.copy()


class RobloxAudioExtractor:
    """从Roblox临时文件中提取音频的主类"""

    def __init__(self, base_dir: str, num_threads: int = None, keyword: str = "oggs",
                 download_history: Optional['ExtractedHistory'] = None,
                 classification_method: ClassificationMethod = ClassificationMethod.DURATION):
        """初始化提取器"""
        import_libs()  # 确保已导入所需库

        self.base_dir = os.path.abspath(base_dir)
        self.num_threads = num_threads or min(32, multiprocessing.cpu_count() * 2)
        self.keyword = keyword
        self.download_history = download_history
        self.classification_method = classification_method

        # 输出目录
        self.output_dir = os.path.join(self.base_dir, "extracted_oggs")
        self.logs_dir = os.path.join(self.output_dir, "logs")

        # 创建日志和临时目录
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        # 初始化处理对象
        self.stats = ProcessingStats()
        self.hash_cache = ContentHashCache()
        self.file_lock = threading.Lock()

        # 文件计数器，使用原子操作而不是锁
        self.processed_count = 0
        self.cancelled = False

        # 按音频时长分类文件 (秒)
        self.duration_categories = {
            "ultra_short_0-5s": (0, 5),  # 0-5秒 (音效、提示音)
            "short_5-15s": (5, 15),  # 5-15秒 (短音效、通知音)
            "medium_15-60s": (15, 60),  # 15-60秒 (循环音乐、短背景音)
            "long_60-300s": (60, 300),  # 1-5分钟 (完整音乐、长背景音)
            "ultra_long_300s+": (300, float('inf'))  # 5分钟+ (长音乐、语音)
        }

        # 按文件大小分类 (字节)
        self.size_categories = {
            "ultra_small_0-50KB": (0, 50 * 1024),  # 0-50KB
            "small_50-200KB": (50 * 1024, 200 * 1024),  # 50KB-200KB
            "medium_200KB-1MB": (200 * 1024, 1024 * 1024),  # 200KB-1MB
            "large_1MB-5MB": (1024 * 1024, 5 * 1024 * 1024),  # 1MB-5MB
            "ultra_large_5MB+": (5 * 1024 * 1024, float('inf'))  # 5MB+
        }

        # 为每个类别创建目录
        self.category_dirs = {}

        # 根据分类方法选择要使用的类别
        if self.classification_method == ClassificationMethod.DURATION:
            categories = self.duration_categories
        else:
            categories = self.size_categories

        for category in categories:
            path = os.path.join(self.output_dir, category)
            os.makedirs(path, exist_ok=True)
            self.category_dirs[category] = path

    def find_files_to_process(self) -> List[str]:
        """查找需要处理的文件 - 使用os.scandir优化性能"""
        files_to_process = []
        output_path_norm = os.path.normpath(self.output_dir)

        def scan_directory(dir_path):
            """递归扫描目录"""
            try:
                with os.scandir(dir_path) as entries:
                    for entry in entries:
                        # 如果当前条目是目录
                        if entry.is_dir():
                            # 如果目录不是输出目录
                            entry_path_norm = os.path.normpath(entry.path)
                            if output_path_norm not in entry_path_norm:
                                scan_directory(entry.path)
                        elif entry.is_file():
                            # 如果文件名中不包含关键字且不以.ogg结尾
                            name = entry.name
                            if self.keyword not in name and not name.endswith('.ogg'):
                                # 使用stat获取文件大小而不是打开文件
                                try:
                                    stat_info = entry.stat()
                                    if stat_info.st_size >= 10:  # 如果文件大小至少为10字节
                                        files_to_process.append(entry.path)
                                except OSError:
                                    # 忽略无法访问的文件
                                    pass
            except (PermissionError, OSError):
                # 忽略无法访问的目录
                pass

        # 开始扫描
        scan_directory(self.base_dir)
        return files_to_process

    def process_files(self) -> Dict[str, Any]:
        """处理目录中的文件"""
        # 扫描文件并记录开始时间
        start_time = time.time()
        print(f"\n• {lang.get('scanning_files')}")

        # 查找要处理的文件
        files_to_process = self.find_files_to_process()

        scan_duration = time.time() - start_time
        print(f"✓ {lang.get('found_files', len(files_to_process), scan_duration)}")

        if not files_to_process:
            print(f"! {lang.get('no_files_found')}")
            return {
                "processed": 0,
                "duplicates": 0,
                "already_processed": 0,
                "errors": 0,
                "output_dir": self.output_dir,
                "duration": 0,
                "files_per_second": 0
            }

        # 创建README文件
        self.create_readme()

        # 重置统计信息
        self.stats.reset()
        self.hash_cache.clear()
        self.processed_count = 0
        self.cancelled = False

        # 处理文件
        processing_start = time.time()
        print(f"\n• {lang.get('processing_with_threads', self.num_threads)}")

        # 创建一个工作队列和一个结果队列
        work_queue = queue.Queue()

        # 填充工作队列
        for file_path in files_to_process:
            work_queue.put(file_path)

        # 创建工作线程
        def worker():
            while not self.cancelled:
                try:
                    # 从队列获取项目，如果队列为空5秒则退出
                    file_path = work_queue.get(timeout=5)
                    try:
                        self.process_file(file_path)
                    finally:
                        work_queue.task_done()
                        # 更新进度
                        self.processed_count += 1
                except queue.Empty:
                    break
                except Exception:
                    # 确保任何一个任务的失败不会中断整个处理
                    pass

        # 启动工作线程
        threads = []
        for _ in range(self.num_threads):
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # 等待所有工作完成
        try:
            # 主线程等待工作完成
            work_queue.join()
        except KeyboardInterrupt:
            # 允许用户中断处理
            self.cancelled = True
            print("\n操作被用户取消.")

        # 如果提取历史记录可用，保存它
        if self.download_history:
            self.download_history.save_history()

        # 计算结果统计
        total_time = time.time() - processing_start
        stats = self.stats.get_all()
        files_per_second = stats['processed_files'] / total_time if total_time > 0 else 0

        return {
            "processed": stats['processed_files'],
            "duplicates": stats['duplicate_files'],
            "already_processed": stats['already_processed'],
            "errors": stats['error_files'],
            "output_dir": self.output_dir,
            "duration": total_time,
            "files_per_second": files_per_second
        }

    def process_file(self, file_path: str) -> bool:
        """处理单个文件并提取音频"""
        if self.cancelled:
            return False

        try:
            # 计算文件哈希
            file_hash = self._get_file_hash(file_path)

            # 如果文件已经处理过了，则跳过
            if self.download_history and self.download_history.is_processed(file_hash):
                self.stats.increment('already_processed')
                return False

            # 尝试读取文件内容
            file_content = self._extract_ogg_content(file_path)
            if not file_content:
                return False

            # 确保是合法的OGG文件头
            if not self._is_valid_ogg(file_content):
                return False

            # 计算内容哈希以检测重复
            content_hash = hashlib.md5(file_content).hexdigest()
            if self.hash_cache.is_duplicate(content_hash):
                self.stats.increment('duplicate_files')
                return False

            # 保存文件
            output_path = self._save_ogg_file(file_path, file_content)
            if output_path:
                # 成功保存文件，增加处理计数
                self.stats.increment('processed_files')

                # 如果可用，将哈希添加到提取历史记录
                if self.download_history:
                    self.download_history.add_hash(file_hash)

                return True

            return False

        except Exception as e:
            # 增加错误计数
            self.stats.increment('error_files')
            # 将错误写入日志
            self._log_error(file_path, str(e))
            return False

    def _extract_ogg_content(self, file_path: str) -> Optional[bytes]:
        """提取文件中的OGG内容 - 使用更高效的文件读取"""
        try:
            # 使用二进制模式打开文件
            with open(file_path, 'rb') as f:
                # 读取前几个字节检查OGG头
                header = f.read(4)
                if header == b'OggS':
                    # 如果是OGG文件，重置文件指针并读取整个内容
                    f.seek(0)
                    return f.read()

                # 不是OGG头，检查是否是gzip压缩文件
                f.seek(0)
                content = f.read()

                # 查找OGG标记
                ogg_start = content.find(b'OggS')
                if ogg_start >= 0:
                    return content[ogg_start:]

                # 尝试gzip解压
                try:
                    if gzip is None:
                        import_libs()
                    # 尝试解压
                    decompressed = gzip.decompress(content)
                    ogg_start = decompressed.find(b'OggS')
                    if ogg_start >= 0:
                        return decompressed[ogg_start:]
                except Exception:
                    pass

            return None
        except Exception:
            return None

    def _is_valid_ogg(self, content: bytes) -> bool:
        """检查内容是否为有效的OGG文件"""
        # 检查OGG文件头
        return content[:4] == b'OggS'

    def _get_audio_duration(self, file_path: str) -> float:
        """获取音频文件的时长（秒）"""
        try:
            if subprocess is None:
                import_libs()

            subprocess_flags = 0
            if os.name == 'nt':  # Windows
                subprocess_flags = subprocess.CREATE_NO_WINDOW

            # 使用ffprobe获取音频时长
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess_flags,
                text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())

            return 0.0  # 默认时长为0，会被分类到最短的类别
        except Exception:
            return 0.0  # 如果获取失败，默认为0秒

    def _get_duration_category(self, file_path: str) -> str:
        """根据音频时长确定类别"""
        duration = self._get_audio_duration(file_path)

        for category, (min_duration, max_duration) in self.duration_categories.items():
            if min_duration <= duration < max_duration:
                return category

        # 默认类别：如果没有匹配项，分配到第一个类别
        return next(iter(self.duration_categories.keys()))

    def _get_size_category(self, file_size: int) -> str:
        """根据文件大小确定类别"""
        for category, (min_size, max_size) in self.size_categories.items():
            if min_size <= file_size < max_size:
                return category

        # 默认类别：如果没有匹配项，分配到第一个类别
        return next(iter(self.size_categories.keys()))

    def _save_ogg_file(self, source_path: str, content: bytes) -> Optional[str]:
        """保存提取的OGG文件 - 使用更高效的文件写入"""
        try:
            # 生成临时文件名
            base_name = os.path.basename(source_path)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            if random is None:
                import_libs()
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            temp_name = f"temp_{base_name}_{timestamp}_{random_suffix}.ogg"
            temp_path = os.path.join(self.output_dir, temp_name)

            # 保存临时文件
            with open(temp_path, 'wb', buffering=1024 * 8) as f:
                f.write(content)

            # 确定分类类别
            if self.classification_method == ClassificationMethod.DURATION:
                # 按时长分类
                category = self._get_duration_category(temp_path)
            else:
                # 按大小分类
                file_size = len(content)
                category = self._get_size_category(file_size)

            output_dir = self.category_dirs[category]

            # 生成最终文件名
            output_name = f"{base_name}_{timestamp}_{random_suffix}.ogg"
            output_path = os.path.join(output_dir, output_name)

            # 移动文件到正确的类别目录
            if shutil is None:
                import_libs()
            shutil.move(temp_path, output_path)

            return output_path

        except Exception as e:
            # 如果处理失败，删除临时文件
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            self._log_error(source_path, f"Failed to save file: {str(e)}")
            return None

    def _get_file_hash(self, file_path: str) -> str:
        """计算文件的哈希值"""
        # 使用文件路径和修改时间作为简单哈希，避免读取文件内容
        try:
            file_stat = os.stat(file_path)
            return hashlib.md5(f"{file_path}_{file_stat.st_size}_{file_stat.st_mtime}".encode()).hexdigest()
        except Exception:
            # 如果无法获取文件信息，使用文件路径
            return hashlib.md5(file_path.encode()).hexdigest()

    def _log_error(self, file_path: str, error_message: str) -> None:
        """记录处理错误 - 使用缓冲写入"""
        try:
            log_file = os.path.join(self.logs_dir, "extraction_errors.log")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.file_lock:
                with open(log_file, 'a', encoding='utf-8', buffering=8192) as f:
                    f.write(f"[{timestamp}] {file_path}: {error_message}\n")
        except Exception:
            pass  # 如果日志记录失败，则没有太大影响

    def create_readme(self) -> None:
        """创建README文件解释音频类别"""
        try:
            # 创建自述文件，解释不同的分类类别
            readme_path = os.path.join(self.output_dir, "README.txt")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"{lang.get('readme_title')}\n")
                f.write("=" * 60 + "\n\n")

                # 添加分类方法信息
                if self.classification_method == ClassificationMethod.DURATION:
                    f.write(f"{lang.get('classification_method_used', lang.get('classification_by_duration'))}\n\n")
                    f.write(f"{lang.get('readme_duration_title')}\n\n")
                    f.write(
                        "1. ultra_short_0-5s     (0-5 seconds / 0-5秒)      - Sound effects, notification sounds / 音效、提示音\n")
                    f.write(
                        "2. short_5-15s          (5-15 seconds / 5-15秒)     - Short effects, alerts / 短音效、通知音\n")
                    f.write(
                        "3. medium_15-60s        (15-60 seconds / 15-60秒)   - Loop music, short BGM / 循环音乐、短背景音\n")
                    f.write(
                        "4. long_60-300s         (1-5 minutes / 1-5分钟)     - Full music, long BGM / 完整音乐、长背景音\n")
                    f.write("5. ultra_long_300s+     (5+ minutes / 5分钟以上)    - Long music, voice / 长音乐、语音\n\n")
                    f.write(
                        f"Note: Duration classification requires FFmpeg to be installed. / 注意：时长分类需要安装FFmpeg。\n")
                else:
                    f.write(f"{lang.get('classification_method_used', lang.get('classification_by_size'))}\n\n")
                    f.write(f"{lang.get('readme_size_title')}\n\n")
                    f.write("1. ultra_small_0-50KB     (0-50KB)       - Very small audio clips / 极小音频片段\n")
                    f.write("2. small_50-200KB         (50KB-200KB)   - Small audio clips / 小型音频片段\n")
                    f.write("3. medium_200KB-1MB       (200KB-1MB)    - Medium size audio / 中等大小音频\n")
                    f.write("4. large_1MB-5MB          (1MB-5MB)      - Large audio files / 大型音频文件\n")
                    f.write("5. ultra_large_5MB+       (5MB+)         - Very large audio files / 极大音频文件\n\n")

                f.write(f"Extraction Time / 提取时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception:
            pass  # 非关键操作


class MP3Converter:
    """将OGG文件转换为MP3，保持时长分类结构"""

    def __init__(self, input_dir: str, output_dir: str, num_threads: int = None):
        """初始化MP3转换器"""
        import_libs()  # 确保已导入所需库

        self.input_dir = input_dir
        self.output_dir = output_dir
        self.num_threads = num_threads or min(16, multiprocessing.cpu_count())
        self.stats = ProcessingStats()
        self.file_lock = threading.Lock()
        self.cancelled = False
        self.processed_count = 0

        # 缓存已经转换过的文件哈希
        self.converted_hashes = set()

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

    def find_ogg_files(self) -> List[str]:
        """查找所有OGG文件 - 使用os.scandir优化"""
        ogg_files = []

        def scan_directory(dir_path):
            try:
                with os.scandir(dir_path) as entries:
                    for entry in entries:
                        if entry.is_dir():
                            scan_directory(entry.path)
                        elif entry.is_file() and entry.name.lower().endswith('.ogg'):
                            ogg_files.append(entry.path)
            except (PermissionError, OSError):
                pass

        scan_directory(self.input_dir)
        return ogg_files

    def convert_all(self) -> Dict[str, Any]:
        """转换所有找到的OGG文件"""
        # 检查ffmpeg是否可用
        if not self._is_ffmpeg_available():
            return {
                "success": False,
                "error": lang.get("ffmpeg_not_installed")
            }

        # 查找所有的OGG文件
        ogg_files = self.find_ogg_files()

        if not ogg_files:
            return {
                "success": False,
                "error": lang.get("no_ogg_files")
            }

        # 创建相应的输出目录结构
        self._create_output_structure()

        # 重置统计
        self.stats.reset()
        self.converted_hashes.clear()
        self.processed_count = 0
        self.cancelled = False

        # 显示转换进度
        print(f"\n• {lang.get('mp3_conversion', len(ogg_files))}")

        # 使用线程池处理文件
        start_time = time.time()

        # 创建工作队列
        work_queue = queue.Queue()

        # 填充工作队列
        for file_path in ogg_files:
            work_queue.put(file_path)

        # 创建工作线程
        def worker():
            while not self.cancelled:
                try:
                    # 从队列获取项目，如果队列为空5秒则退出
                    file_path = work_queue.get(timeout=5)
                    try:
                        self.convert_file(file_path)
                    finally:
                        work_queue.task_done()
                        # 更新进度
                        self.processed_count += 1
                except queue.Empty:
                    break
                except Exception:
                    # 确保任何一个任务的失败不会中断整个处理
                    pass

        # 启动工作线程
        threads = []
        for _ in range(self.num_threads):
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # 等待所有工作完成
        try:
            # 等待所有工作完成
            work_queue.join()
        except KeyboardInterrupt:
            # 允许用户中断处理
            self.cancelled = True
            print("\n操作被用户取消.")

        # 计算结果统计
        stats = self.stats.get_all()
        total_time = time.time() - start_time

        return {
            "success": True,
            "converted": stats['mp3_converted'],
            "skipped": stats['mp3_skipped'],
            "errors": stats['mp3_errors'],
            "total": len(ogg_files),
            "duration": total_time,
            "output_dir": self.output_dir
        }

    def convert_file(self, ogg_path: str) -> bool:
        """转换单个OGG文件为MP3，保持目录结构"""
        if self.cancelled:
            return False

        try:
            # 计算文件哈希以检测重复转换
            file_hash = self._get_file_hash(ogg_path)

            # 检查是否已转换
            with self.file_lock:
                if file_hash in self.converted_hashes:
                    self.stats.increment('mp3_skipped')
                    return False
                # 记录哈希
                self.converted_hashes.add(file_hash)

            # 获取相对输入路径以构建输出路径
            rel_path = os.path.relpath(ogg_path, self.input_dir)
            rel_dir = os.path.dirname(rel_path)
            basename = os.path.basename(ogg_path)
            basename_noext = os.path.splitext(basename)[0]

            # 为输出文件创建目录（保持时长分类结构）
            output_dir = os.path.join(self.output_dir, rel_dir)
            os.makedirs(output_dir, exist_ok=True)

            # 创建MP3文件名，保留原始格式
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            if random is None:
                import_libs()
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            mp3_filename = f"{basename_noext}_{timestamp}_{random_suffix}.mp3"
            mp3_path = os.path.join(output_dir, mp3_filename)

            # 使用ffmpeg转换文件 - 使用更高效的参数
            try:
                subprocess_flags = 0
                if os.name == 'nt':  # Windows
                    if subprocess is None:
                        import_libs()
                    subprocess_flags = subprocess.CREATE_NO_WINDOW

                # 使用更好的ffmpeg参数 - 增加转换速度
                result = subprocess.run(
                    ["ffmpeg", "-y", "-loglevel", "error", "-i", ogg_path,
                     "-codec:a", "libmp3lame", "-qscale:a", "2", "-threads", "2", mp3_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    creationflags=subprocess_flags
                )
                # 转换成功
                self.stats.increment('mp3_converted')
                return True
            except subprocess.CalledProcessError as e:
                self.stats.increment('mp3_errors')
                self._log_error(ogg_path, f"Conversion failed: {e.stderr.decode('utf-8', errors='ignore')}")
                return False
        except Exception as e:
            self.stats.increment('mp3_errors')
            self._log_error(ogg_path, f"Unexpected error: {str(e)}")
            return False

    def _get_file_hash(self, file_path: str) -> str:
        """计算文件的哈希值"""
        # 使用文件路径和修改时间作为简单哈希，避免读取文件内容
        try:
            file_stat = os.stat(file_path)
            return hashlib.md5(f"{file_path}_{file_stat.st_size}_{file_stat.st_mtime}".encode()).hexdigest()
        except Exception:
            # 如果无法获取文件信息，使用文件路径
            return hashlib.md5(file_path.encode()).hexdigest()

    def _is_ffmpeg_available(self) -> bool:
        """检查ffmpeg是否可用"""
        try:
            if subprocess is None:
                import_libs()

            subprocess_flags = 0
            if os.name == 'nt':  # Windows
                subprocess_flags = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess_flags
            )
            return result.returncode == 0
        except Exception:
            return False

    def _create_output_structure(self) -> None:
        """创建与输入目录相对应的输出目录结构"""

        # 使用os.scandir优化性能
        def create_dirs(base_path, relative_path=""):
            full_input_path = os.path.join(base_path, relative_path)
            full_output_path = os.path.join(self.output_dir, relative_path)

            if relative_path:  # 避免创建根目录
                os.makedirs(full_output_path, exist_ok=True)

            try:
                with os.scandir(full_input_path) as entries:
                    for entry in entries:
                        if entry.is_dir():
                            new_rel_path = os.path.join(relative_path, entry.name)
                            create_dirs(base_path, new_rel_path)
            except (PermissionError, OSError):
                pass

        create_dirs(self.input_dir)

    def _log_error(self, file_path: str, error_message: str) -> None:
        """记录转换错误 - 使用缓冲写入"""
        try:
            log_dir = os.path.join(self.output_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "conversion_errors.log")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.file_lock:
                with open(log_file, 'a', encoding='utf-8', buffering=8192) as f:
                    f.write(f"[{timestamp}] {file_path}: {error_message}\n")
        except Exception:
            pass  # 如果日志记录失败，则没有太大影响


def open_directory(path: str) -> bool:
    """在文件资源管理器/Finder中打开目录"""
    try:
        if os.name == 'nt':  # Windows
            os.startfile(path)
        elif os.name == 'posix':  # macOS, Linux
            if sys.platform == 'darwin':  # macOS
                subprocess.call(['open', path])
            else:  # Linux
                subprocess.call(['xdg-open', path])
        return True
    except Exception:
        return False


def is_ffmpeg_available() -> bool:
    """检查FFmpeg是否可用"""
    try:
        if subprocess is None:
            import_libs()

        subprocess_flags = 0
        if os.name == 'nt':  # Windows
            subprocess_flags = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess_flags
        )
        return result.returncode == 0
    except Exception:
        return False


class LogHandler:
    """日志处理类，用于记录消息到PyQt的TextEdit控件"""

    def __init__(self, text_edit: TextEdit):
        self.text_edit = text_edit

    def info(self, message: str):
        """记录信息消息"""
        self.text_edit.append(message)
        self.text_edit.ensureCursorVisible()

    def success(self, message: str):
        """记录成功消息"""
        self.text_edit.append(f"✓ {message}")
        self.text_edit.ensureCursorVisible()

    def warning(self, message: str):
        """记录警告消息"""
        self.text_edit.append(f"⚠ {message}")
        self.text_edit.ensureCursorVisible()

    def error(self, message: str):
        """记录错误消息"""
        self.text_edit.append(f"✗ {message}")
        self.text_edit.ensureCursorVisible()


# ====== PyQt5 实现部分 ======

class ExtractionWorker(QThread):
    """音频提取工作线程"""
    progressUpdated = pyqtSignal(int, int, float, float)  # 进度更新信号(当前进度, 总数, 已用时间, 速度)
    finished = pyqtSignal(dict)  # 完成信号(结果字典)
    logMessage = pyqtSignal(str, str)  # 日志消息信号(消息, 类型)

    def __init__(self, base_dir, num_threads, download_history, classification_method, convert_to_mp3=False):
        super().__init__()
        self.base_dir = base_dir
        self.num_threads = num_threads
        self.download_history = download_history
        self.classification_method = classification_method
        self.convert_to_mp3 = convert_to_mp3
        self.is_cancelled = False
        self.total_files = 0
        self.processed_count = 0

    def run(self):
        """运行线程：提取音频文件"""
        try:
            # 更新状态
            self.logMessage.emit(lang.get('scanning_files'), 'info')

            # 创建提取器
            start_time = time.time()
            extractor = RobloxAudioExtractor(
                self.base_dir,
                self.num_threads,
                "oggs",
                self.download_history,
                self.classification_method
            )

            # 设置取消检查函数
            extractor.cancelled = lambda: self.is_cancelled

            # 查找要处理的文件
            files_to_process = extractor.find_files_to_process()
            scan_duration = time.time() - start_time
            self.total_files = len(files_to_process)

            self.logMessage.emit(lang.get('found_files', self.total_files, scan_duration), 'info')

            if not files_to_process:
                self.logMessage.emit(lang.get('no_files_found'), 'warning')
                self.finished.emit({
                    "success": True,
                    "processed": 0,
                    "duplicates": 0,
                    "already_processed": 0,
                    "errors": 0,
                    "output_dir": extractor.output_dir,
                    "duration": 0,
                    "files_per_second": 0
                })
                return

            # 创建一个用于更新进度的函数
            original_process_file = extractor.process_file

            def process_file_with_progress(file_path):
                result = original_process_file(file_path)
                self.processed_count += 1
                elapsed = time.time() - start_time
                speed = self.processed_count / elapsed if elapsed > 0 else 0
                progress = min(100, int((self.processed_count / self.total_files) * 100))
                self.progressUpdated.emit(self.processed_count, self.total_files, elapsed, speed)
                return result

            # 替换原始方法
            extractor.process_file = process_file_with_progress

            # 处理文件
            self.logMessage.emit(lang.get('processing_with_threads', self.num_threads), 'info')

            # 进行处理
            extraction_result = extractor.process_files()

            # 确保历史记录被保存 - 修复：强制保存历史记录
            if self.download_history:
                try:
                    self.download_history.save_history()
                    self.logMessage.emit(f"History saved: {self.download_history.get_history_size()} files", 'info')
                except Exception as e:
                    self.logMessage.emit(f"Failed to save history: {str(e)}", 'error')

            # 如果需要，进行MP3转换
            mp3_result = None
            if self.convert_to_mp3 and not self.is_cancelled and extraction_result["processed"] > 0:
                self.logMessage.emit(lang.get('mp3_conversion_info'), 'info')
                mp3_dir = os.path.join(self.base_dir, "extracted_mp3")
                mp3_converter = MP3Converter(extraction_result["output_dir"], mp3_dir, self.num_threads)

                # 设置取消函数
                mp3_converter.cancelled = lambda: self.is_cancelled

                # 转换文件
                mp3_result = mp3_converter.convert_all()
                extraction_result["mp3_result"] = mp3_result

            # 设置结果
            extraction_result["success"] = True
            self.finished.emit(extraction_result)

        except Exception as e:
            self.logMessage.emit(lang.get('error_occurred', str(e)), 'error')
            traceback.print_exc()
            self.finished.emit({"success": False, "error": str(e)})

    def cancel(self):
        """取消操作"""
        self.is_cancelled = True


class CacheClearWorker(QThread):
    """缓存清理工作线程"""
    finished = pyqtSignal(bool, int, int, str)  # 完成信号(成功?, 清理数量, 总数, 错误信息)
    progressUpdated = pyqtSignal(int, int)  # 进度更新信号(当前, 总数)

    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        self.is_cancelled = False

    def run(self):
        """运行线程：清理缓存"""
        try:
            # 计数器
            total_files = 0
            cleared_files = 0
            processed_files = 0

            # 需要排除的文件夹
            exclude_dirs = {'extracted_mp3', 'extracted_oggs'}
            files_to_process = []

            # 首先扫描所有文件
            for root, dirs, files in os.walk(self.directory):
                # 跳过排除的目录
                if any(excluded in root for excluded in exclude_dirs):
                    continue

                for file in files:
                    file_path = os.path.join(root, file)
                    total_files += 1
                    files_to_process.append(file_path)

            # 处理文件
            for file_path in files_to_process:
                if self.is_cancelled:
                    break

                try:
                    # 读取文件的前8KB内容
                    with open(file_path, 'rb') as f:
                        content = f.read(8192)

                    # 检查OGG文件头或其他标识
                    if (b'OggS' in content or  # OGG标识
                            b'.ogg' in content.lower() or  # .ogg扩展名
                            b'audio' in content.lower() or  # 音频关键字
                            b'sound' in content.lower()):  # 声音关键字

                        # 删除文件
                        os.remove(file_path)
                        cleared_files += 1

                except (IOError, OSError, PermissionError):
                    pass

                # 更新进度
                processed_files += 1
                self.progressUpdated.emit(processed_files, total_files)

            # 返回结果
            self.finished.emit(True, cleared_files, total_files, "")

        except Exception as e:
            self.finished.emit(False, 0, 0, str(e))

    def cancel(self):
        """取消操作"""
        self.is_cancelled = True


# 响应式功能特色组件
class ResponsiveFeatureItem(QWidget):
    """响应式功能特色项目组件"""

    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.icon = icon
        self.text = text
        self.setupUI()

    def setupUI(self):
        """设置UI"""
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumSize(140, 80)
        self.setMaximumSize(220, 80)

        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 图标
        self.icon_widget = IconWidget(self.icon)
        self.icon_widget.setFixedSize(24, 24)

        # 文本
        self.text_label = CaptionLabel(self.text)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)

        # 添加到布局
        layout.addWidget(self.icon_widget, 0, Qt.AlignCenter)
        layout.addWidget(self.text_label)


class MainWindow(MSFluentWindow):
    """主窗口 - 使用MSFluentWindow而不是自定义标题栏，增强响应式布局"""

    def __init__(self):
        super().__init__()

        # 初始化配置管理器
        self.config_manager = ConfigManager()

        # 初始化语言管理器
        global lang
        lang = LanguageManager(self.config_manager)

        # 初始化窗口
        self.initWindow()

        # 初始化数据
        self.default_dir = get_roblox_default_dir()

        # 创建应用数据目录
        app_data_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        os.makedirs(app_data_dir, exist_ok=True)
        history_file = os.path.join(app_data_dir, "extracted_history.json")

        # 初始化提取历史
        self.download_history = ExtractedHistory(history_file)

        # 初始化工作线程
        self.extraction_worker = None
        self.cache_clear_worker = None

        # 初始化UI
        self.initUI()

        # 显示欢迎消息
        self.add_welcome_message()

        # 应用保存的主题设置
        self.applyThemeFromConfig()

    def initWindow(self):
        """初始化窗口设置"""
        # 设置窗口标题和大小
        self.setWindowTitle(lang.get("title"))
        self.resize(990, 700)

        # 设置最小窗口大小
        self.setMinimumSize(800, 600)

        # 设置深色主题
        setTheme(Theme.DARK)

        # 设置窗口图标
        try:
            icon_path = resource_path(os.path.join("icons", "Roblox-Audio-Extractor.ico"))
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"无法设置窗口图标: {e}")

        # 设置窗口特效和背景
        self.setWindowBackground()

    def setWindowBackground(self):
        """设置窗口背景，确保深色模式正确显示"""
        # 为主窗口设置深色背景
        self.setStyleSheet("""
            MSFluentWindow {
                background-color: rgb(32, 32, 32);
            }
            QWidget {
                background-color: transparent;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
        """)

    def applyThemeFromConfig(self):
        """从配置文件应用主题设置"""
        theme_setting = self.config_manager.get("theme", "dark")
        if theme_setting == "light":
            setTheme(Theme.LIGHT)
        elif theme_setting == "dark":
            setTheme(Theme.DARK)
        else:  # auto
            setTheme(Theme.AUTO)

        # 确保UI已初始化后再更新样式
        QTimer.singleShot(100, self.updateAllStyles)

    def initUI(self):
        """初始化UI组件"""
        # 创建主界面
        self.homeInterface = QWidget()
        self.homeInterface.setObjectName("homeInterface")

        self.extractInterface = QWidget()
        self.extractInterface.setObjectName("extractInterface")

        self.clearCacheInterface = QWidget()
        self.clearCacheInterface.setObjectName("clearCacheInterface")

        self.historyInterface = QWidget()
        self.historyInterface.setObjectName("historyInterface")

        self.settingsInterface = QWidget()
        self.settingsInterface.setObjectName("settingsInterface")

        self.aboutInterface = QWidget()
        self.aboutInterface.setObjectName("aboutInterface")

        # 设置导航 - 使用固定的路由键，而不是翻译后的文本
        self.addSubInterface(self.homeInterface, FluentIcon.HOME, lang.get("home"))
        self.addSubInterface(self.extractInterface, FluentIcon.DOWNLOAD, lang.get("extract_audio"))
        self.addSubInterface(self.clearCacheInterface, FluentIcon.DELETE, lang.get("clear_cache"))
        self.addSubInterface(self.historyInterface, FluentIcon.HISTORY, lang.get("view_history"))

        # 添加底部导航项
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, lang.get("settings"),
                             position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.aboutInterface, FluentIcon.INFO, lang.get("about"),
                             position=NavigationItemPosition.BOTTOM)

        # 初始化各个界面
        self.setupHomeInterface()
        self.setupExtractInterface()
        self.setupClearCacheInterface()
        self.setupHistoryInterface()
        self.setupSettingsInterface()
        self.setupAboutInterface()

        # 设置默认界面 - 使用界面对象而不是文本
        self.switchTo(self.homeInterface)

        # 监听界面切换事件
        self.stackedWidget.currentChanged.connect(self.onInterfaceChanged)

    def setupHomeInterface(self):
        """设置主页界面 - 响应式设计优化版本"""
        # 创建滚动区域
        scroll = ScrollArea(self.homeInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 创建主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)  # 减少边距以适应小屏幕
        content_layout.setSpacing(15)  # 减少间距

        # 欢迎横幅卡片 - 响应式设计
        welcome_card = CardWidget()
        welcome_card.setMinimumHeight(180)  # 设置最小高度而不是固定高度
        welcome_layout = QVBoxLayout(welcome_card)
        welcome_layout.setContentsMargins(20, 15, 20, 15)  # 减少内边距

        # 横幅内容 - 使用响应式布局
        banner_content = QHBoxLayout()
        banner_content.setSpacing(15)

        # 左侧：文本内容
        text_container = QWidget()
        text_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(8)

        welcome_title = DisplayLabel(lang.get("welcome_message"))
        welcome_title.setObjectName("welcomeTitle")
        welcome_title.setWordWrap(True)  # 允许文本换行

        welcome_subtitle = BodyLabel(lang.get("about_description"))
        welcome_subtitle.setWordWrap(True)
        welcome_subtitle.setObjectName("welcomeSubtitle")

        text_layout.addWidget(welcome_title)
        text_layout.addWidget(welcome_subtitle)

        # 右侧：图标（在小屏幕上隐藏）
        icon_container = QWidget()
        icon_container.setFixedSize(100, 100)
        icon_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        self.home_icon_label = QLabel()
        self.home_icon_label.setAlignment(Qt.AlignCenter)
        self.loadHomeIcon()
        icon_layout.addWidget(self.home_icon_label)

        # 添加到横幅布局
        banner_content.addWidget(text_container, 3)
        banner_content.addWidget(icon_container, 1)

        # 快速操作按钮 - 响应式排列
        action_container = QWidget()
        # 使用FlowLayout替代固定的水平布局
        action_layout = FlowLayout(action_container)
        action_layout.setContentsMargins(0, 10, 0, 0)
        action_layout.setSpacing(10)

        extract_btn = PrimaryPushButton(FluentIcon.DOWNLOAD, lang.get("extract_audio"))
        extract_btn.setFixedSize(140, 35)
        extract_btn.clicked.connect(lambda: self.switchTo(self.extractInterface))

        clear_cache_btn = PushButton(FluentIcon.DELETE, lang.get("clear_cache"))
        clear_cache_btn.setFixedSize(120, 35)
        clear_cache_btn.clicked.connect(lambda: self.switchTo(self.clearCacheInterface))

        settings_btn = TransparentPushButton(FluentIcon.SETTING, lang.get("settings"))
        settings_btn.setFixedSize(100, 35)
        settings_btn.clicked.connect(lambda: self.switchTo(self.settingsInterface))

        action_layout.addWidget(extract_btn)
        action_layout.addWidget(clear_cache_btn)
        action_layout.addWidget(settings_btn)

        # 组装欢迎卡片
        welcome_layout.addLayout(banner_content)
        welcome_layout.addWidget(action_container)
        content_layout.addWidget(welcome_card)

        # 功能特色卡片 - 使用响应式FlowLayout
        features_card = CardWidget()
        features_layout = QVBoxLayout(features_card)
        features_layout.setContentsMargins(20, 15, 20, 15)
        features_layout.setSpacing(12)

        features_title = SubtitleLabel(lang.get("features"))
        features_title.setObjectName("featuresTitle")
        features_layout.addWidget(features_title)

        # 创建响应式功能特色容器
        features_container = QWidget()
        self.features_flow_layout = FlowLayout(features_container)
        self.features_flow_layout.setSpacing(10)
        self.features_flow_layout.setContentsMargins(0, 0, 0, 0)

        # 功能特色项目
        feature_items = [
            (FluentIcon.SPEED_HIGH, lang.get("feature_1")),
            (FluentIcon.ACCEPT, lang.get("feature_2")),
            (FluentIcon.FOLDER, lang.get("feature_3")),
            (FluentIcon.MUSIC, lang.get("feature_4"))
        ]

        for icon, text in feature_items:
            feature_widget = ResponsiveFeatureItem(icon, text)
            self.features_flow_layout.addWidget(feature_widget)

        features_layout.addWidget(features_container)
        content_layout.addWidget(features_card)

        # 信息行 - 响应式网格布局
        info_container = QWidget()
        info_grid = QGridLayout(info_container)
        info_grid.setSpacing(15)
        info_grid.setContentsMargins(0, 0, 0, 0)

        # 系统信息卡片
        system_card = CardWidget()
        system_card.setMinimumWidth(250)  # 设置最小宽度
        system_layout = QVBoxLayout(system_card)
        system_layout.setContentsMargins(15, 12, 15, 12)

        system_title = StrongBodyLabel(lang.get("system_info"))
        system_layout.addWidget(system_title)

        # 系统信息项目
        cpu_info = f"{lang.get('cpu_cores')}: {multiprocessing.cpu_count()}"
        recommended_threads = f"{lang.get('recommended_threads')}: {min(32, multiprocessing.cpu_count() * 2)}"
        ffmpeg_status = f"{lang.get('ffmpeg_status')}: {lang.get('available') if is_ffmpeg_available() else lang.get('not_available')}"

        system_layout.addWidget(CaptionLabel(cpu_info))
        system_layout.addWidget(CaptionLabel(recommended_threads))
        system_layout.addWidget(CaptionLabel(ffmpeg_status))

        # 目录信息卡片
        dir_card = CardWidget()
        dir_card.setMinimumWidth(250)  # 设置最小宽度
        dir_layout = QVBoxLayout(dir_card)
        dir_layout.setContentsMargins(15, 12, 15, 12)

        dir_title = StrongBodyLabel(lang.get("default_dir"))
        dir_layout.addWidget(dir_title)

        dir_path_label = CaptionLabel(self.default_dir)
        dir_path_label.setWordWrap(True)
        dir_layout.addWidget(dir_path_label)

        dir_actions = QHBoxLayout()
        dir_actions.setContentsMargins(0, 8, 0, 0)
        dir_actions.setSpacing(8)

        open_dir_btn = PillPushButton(FluentIcon.FOLDER, lang.get("open_directory"))
        open_dir_btn.setFixedHeight(28)
        open_dir_btn.clicked.connect(lambda: open_directory(self.default_dir))

        copy_path_btn = TransparentPushButton(FluentIcon.COPY, lang.get("copy_path"))
        copy_path_btn.setFixedHeight(28)
        copy_path_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.default_dir))

        dir_actions.addWidget(open_dir_btn)
        dir_actions.addWidget(copy_path_btn)
        dir_actions.addStretch()

        dir_layout.addLayout(dir_actions)

        # 添加到网格布局（响应式排列）
        info_grid.addWidget(system_card, 0, 0)
        info_grid.addWidget(dir_card, 0, 1)

        # 设置列拉伸，使卡片能够平均分配空间
        info_grid.setColumnStretch(0, 1)
        info_grid.setColumnStretch(1, 1)

        content_layout.addWidget(info_container)

        # 最近活动日志卡片
        log_card = CardWidget()
        log_card.setMinimumHeight(200)  # 使用最小高度而不是固定高度
        log_card.setMaximumHeight(300)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(15, 10, 15, 12)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(lang.get("recent_activity"))
        log_layout.addWidget(log_title)

        self.homeLogText = TextEdit()
        self.homeLogText.setReadOnly(True)
        self.homeLogText.setMinimumHeight(120)
        log_layout.addWidget(self.homeLogText)

        content_layout.addWidget(log_card)

        # 添加伸缩空间
        content_layout.addStretch()

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self.homeInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 应用样式
        self.setHomeStyles()

        # 连接窗口大小改变事件来优化布局
        self.resizeEvent = self._create_responsive_resize_handler(self.resizeEvent)

    def _create_responsive_resize_handler(self, original_resize_event):
        """创建响应式调整大小处理程序"""

        def responsive_resize_event(event):
            # 调用原始的调整大小事件
            if original_resize_event:
                original_resize_event(event)

            # 响应式调整
            if hasattr(self, 'homeInterface'):
                self._adjust_responsive_layout(event.size().width())

        return responsive_resize_event

    def _adjust_responsive_layout(self, window_width):
        """根据窗口宽度调整响应式布局"""
        try:
            # 断点设置
            MOBILE_BREAKPOINT = 600
            TABLET_BREAKPOINT = 900

            # 调整功能特色项目的大小和排列
            if hasattr(self, 'features_flow_layout'):
                # 根据窗口宽度调整FlowLayout的项目大小
                for i in range(self.features_flow_layout.count()):
                    item = self.features_flow_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if isinstance(widget, ResponsiveFeatureItem):
                            if window_width < MOBILE_BREAKPOINT:
                                # 移动设备：更小的项目
                                widget.setMinimumSize(120, 70)
                                widget.setMaximumSize(180, 70)
                            elif window_width < TABLET_BREAKPOINT:
                                # 平板设备：中等大小
                                widget.setMinimumSize(140, 75)
                                widget.setMaximumSize(200, 75)
                            else:
                                # 桌面设备：正常大小
                                widget.setMinimumSize(160, 80)
                                widget.setMaximumSize(220, 80)

            # 在小屏幕上隐藏图标
            if hasattr(self, 'home_icon_label'):
                icon_container = self.home_icon_label.parent()
                if icon_container:
                    if window_width < MOBILE_BREAKPOINT:
                        icon_container.hide()
                    else:
                        icon_container.show()

        except Exception as e:
            # 静默处理异常，避免影响UI正常运行
            pass

    def loadHomeIcon(self):
        """加载主页图标"""
        try:
            icon_path = resource_path(os.path.join("icons", "Roblox-Audio-Extractor.png"))
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                scaled_pixmap = pixmap.scaled(
                    80, 80,  # 减小图标尺寸
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.home_icon_label.setPixmap(scaled_pixmap)
            else:
                # 使用默认文字
                self.home_icon_label.setText("♪")
                font = QFont()
                font.setPointSize(36)  # 减小字体
                self.home_icon_label.setFont(font)
                self.home_icon_label.setAlignment(Qt.AlignCenter)
        except Exception as e:
            print(f"无法加载主页图标: {e}")

    def setHomeStyles(self):
        """设置主页样式"""
        # 检查当前主题并设置相应样式
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            # 浅色模式样式
            self.homeInterface.setStyleSheet("""
                #welcomeTitle {
                    font-size: 26px;
                    font-weight: bold;
                    color: rgb(0, 0, 0);
                }
                #welcomeSubtitle {
                    font-size: 14px;
                    color: rgba(0, 0, 0, 0.7);
                }
                #featuresTitle {
                    font-size: 18px;
                    font-weight: 600;
                    color: rgb(0, 0, 0);
                }
            """)
        else:
            # 深色模式样式
            self.homeInterface.setStyleSheet("""
                #welcomeTitle {
                    font-size: 26px;
                    font-weight: bold;
                    color: rgb(255, 255, 255);
                }
                #welcomeSubtitle {
                    font-size: 14px;
                    color: rgba(255, 255, 255, 0.8);
                }
                #featuresTitle {
                    font-size: 18px;
                    font-weight: 600;
                    color: rgb(255, 255, 255);
                }
            """)

    def setupExtractInterface(self):
        """设置提取音频界面"""
        # 创建滚动区域
        scroll = ScrollArea(self.extractInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # 目录选择卡片
        dir_card = CardWidget()
        dir_card_layout = QVBoxLayout(dir_card)
        dir_card_layout.setContentsMargins(20, 15, 20, 15)
        dir_card_layout.setSpacing(15)

        dir_title = StrongBodyLabel(lang.get("directory"))
        dir_card_layout.addWidget(dir_title)

        # 目录输入行
        dir_input_layout = QHBoxLayout()
        dir_input_layout.setSpacing(10)

        self.dirInput = LineEdit()
        self.dirInput.setText(self.default_dir)
        self.dirInput.setPlaceholderText(lang.get("input_dir"))
        self.dirInput.setClearButtonEnabled(True)

        browse_btn = PushButton(FluentIcon.FOLDER_ADD, lang.get("browse"))
        browse_btn.setFixedSize(100, 33)
        browse_btn.clicked.connect(self.browseDirectory)

        dir_input_layout.addWidget(self.dirInput, 1)
        dir_input_layout.addWidget(browse_btn)

        dir_card_layout.addLayout(dir_input_layout)

        # 添加目录提示
        dir_hint = CaptionLabel(f"{lang.get('default_dir')}: {self.default_dir}")
        dir_hint.setWordWrap(True)
        dir_card_layout.addWidget(dir_hint)

        content_layout.addWidget(dir_card)

        # 分类方法卡片
        classification_card = CardWidget()
        class_card_layout = QVBoxLayout(classification_card)
        class_card_layout.setContentsMargins(20, 15, 20, 15)
        class_card_layout.setSpacing(15)

        class_title = StrongBodyLabel(lang.get("classification_method"))
        class_card_layout.addWidget(class_title)

        # 分类方法选择
        self.classification_group = QButtonGroup()

        duration_row = QHBoxLayout()
        self.durationRadio = RadioButton(lang.get("classify_by_duration"))
        self.durationRadio.setChecked(True)
        duration_icon = IconWidget(FluentIcon.CALENDAR)
        duration_icon.setFixedSize(16, 16)
        duration_row.addWidget(duration_icon)
        duration_row.addWidget(self.durationRadio)
        duration_row.addStretch()

        size_row = QHBoxLayout()
        self.sizeRadio = RadioButton(lang.get("classify_by_size"))
        size_icon = IconWidget(FluentIcon.DOCUMENT)
        size_icon.setFixedSize(16, 16)
        size_row.addWidget(size_icon)
        size_row.addWidget(self.sizeRadio)
        size_row.addStretch()

        self.classification_group.addButton(self.durationRadio)
        self.classification_group.addButton(self.sizeRadio)

        class_card_layout.addLayout(duration_row)
        class_card_layout.addLayout(size_row)

        # FFmpeg警告
        if not is_ffmpeg_available():
            ffmpeg_warning = InfoBar.warning(
                title="FFmpeg",
                content=lang.get("ffmpeg_not_found_warning"),
                orient=Qt.Horizontal,
                isClosable=False,
                duration=-1,
                parent=None
            )
            class_card_layout.addWidget(ffmpeg_warning)

        # 分类信息标签
        self.classInfoLabel = CaptionLabel(lang.get("info_duration_categories"))
        self.classInfoLabel.setWordWrap(True)
        class_card_layout.addWidget(self.classInfoLabel)

        # 连接分类方法选择事件
        self.durationRadio.toggled.connect(self.updateClassificationInfo)

        content_layout.addWidget(classification_card)

        # 处理选项卡片
        options_card = CardWidget()
        options_card_layout = QVBoxLayout(options_card)
        options_card_layout.setContentsMargins(20, 15, 20, 15)
        options_card_layout.setSpacing(15)

        options_title = StrongBodyLabel(lang.get("processing_info"))
        options_card_layout.addWidget(options_title)

        # 线程数设置
        threads_row = QHBoxLayout()
        threads_icon = IconWidget(FluentIcon.SPEED_HIGH)
        threads_icon.setFixedSize(16, 16)
        threads_label = BodyLabel(lang.get("threads_prompt"))

        self.threadsSpinBox = SpinBox()
        self.threadsSpinBox.setRange(1, 128)
        self.threadsSpinBox.setValue(min(32, multiprocessing.cpu_count() * 2))
        self.threadsSpinBox.setFixedWidth(120)
        self.threadsSpinBox.setFixedHeight(32)

        threads_row.addWidget(threads_icon)
        threads_row.addWidget(threads_label)
        threads_row.addStretch()
        threads_row.addWidget(self.threadsSpinBox)

        # MP3转换选项
        mp3_row = QHBoxLayout()
        mp3_icon = IconWidget(FluentIcon.MUSIC)
        mp3_icon.setFixedSize(16, 16)
        self.mp3CheckBox = CheckBox(lang.get("convert_to_mp3_prompt"))
        self.mp3CheckBox.setChecked(True)

        mp3_row.addWidget(mp3_icon)
        mp3_row.addWidget(self.mp3CheckBox)
        mp3_row.addStretch()

        options_card_layout.addLayout(threads_row)
        options_card_layout.addLayout(mp3_row)

        # 添加处理提示
        info_list = [
            lang.get("info_mp3_conversion"),
            lang.get("info_skip_downloaded")
        ]

        for info in info_list:
            info_label = CaptionLabel(f"• {info}")
            info_label.setWordWrap(True)
            options_card_layout.addWidget(info_label)

        content_layout.addWidget(options_card)

        # 操作控制卡片
        control_card = CardWidget()
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(25, 20, 25, 20)
        control_layout.setSpacing(15)

        # 进度显示
        progress_layout = QVBoxLayout()

        # 进度条
        self.progressBar = ProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        # 进度信息
        self.progressLabel = CaptionLabel(lang.get("ready"))
        self.progressLabel.setAlignment(Qt.AlignCenter)

        progress_layout.addWidget(self.progressBar)
        progress_layout.addWidget(self.progressLabel)

        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.extractButton = PrimaryPushButton(FluentIcon.DOWNLOAD, lang.get("start_extraction"))
        self.extractButton.setFixedHeight(40)
        self.extractButton.clicked.connect(self.startExtraction)

        self.cancelButton = PushButton(FluentIcon.CLOSE, lang.get("cancel"))
        self.cancelButton.setFixedHeight(40)
        self.cancelButton.clicked.connect(self.cancelExtraction)
        self.cancelButton.hide()  # 初始隐藏

        button_layout.addWidget(self.extractButton)
        button_layout.addWidget(self.cancelButton)
        button_layout.addStretch()

        control_layout.addLayout(progress_layout)
        control_layout.addLayout(button_layout)
        content_layout.addWidget(control_card)

        # 日志区域
        log_card = CardWidget()
        log_card.setFixedHeight(300)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(lang.get("recent_activity"))
        log_layout.addWidget(log_title)

        self.extractLogText = TextEdit()
        self.extractLogText.setReadOnly(True)
        self.extractLogText.setFixedHeight(220)
        log_layout.addWidget(self.extractLogText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self.extractInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.extractLogHandler = LogHandler(self.extractLogText)

    def setupClearCacheInterface(self):
        """设置清除缓存界面"""
        # 创建滚动区域
        scroll = ScrollArea(self.clearCacheInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # 缓存信息卡片
        info_card = CardWidget()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(25, 20, 25, 20)
        info_layout.setSpacing(15)

        # 标题
        info_title = TitleLabel(lang.get("clear_cache"))
        info_title.setObjectName("cacheTitle")
        info_layout.addWidget(info_title)

        # 描述
        desc_label = BodyLabel(lang.get("cache_description"))
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        # 缓存位置信息
        location_row = QHBoxLayout()
        location_icon = IconWidget(FluentIcon.FOLDER)
        location_icon.setFixedSize(20, 20)
        location_label = StrongBodyLabel(lang.get("cache_location"))
        location_row.addWidget(location_icon)
        location_row.addWidget(location_label)
        location_row.addStretch()

        info_layout.addLayout(location_row)

        # 缓存路径
        cache_path_label = CaptionLabel(self.default_dir)
        cache_path_label.setWordWrap(True)
        cache_path_label.setStyleSheet(
            "QLabel { background-color: rgba(255, 255, 255, 0.05); padding: 8px; border-radius: 4px; }")
        info_layout.addWidget(cache_path_label)

        # 快速操作按钮
        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(10)

        open_cache_btn = PushButton(FluentIcon.FOLDER, lang.get("open_directory"))
        open_cache_btn.clicked.connect(lambda: open_directory(self.default_dir))

        copy_cache_btn = TransparentPushButton(FluentIcon.COPY, lang.get("copy_path"))
        copy_cache_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.default_dir))

        quick_actions.addWidget(open_cache_btn)
        quick_actions.addWidget(copy_cache_btn)
        quick_actions.addStretch()

        info_layout.addLayout(quick_actions)
        content_layout.addWidget(info_card)

        # 操作控制卡片
        control_card = CardWidget()
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(25, 20, 25, 20)
        control_layout.setSpacing(15)

        # 进度显示
        progress_layout = QVBoxLayout()

        self.cacheProgressBar = ProgressBar()
        self.cacheProgressBar.setValue(0)
        self.cacheProgressBar.setTextVisible(True)

        self.cacheProgressLabel = CaptionLabel(lang.get("ready"))
        self.cacheProgressLabel.setAlignment(Qt.AlignCenter)

        progress_layout.addWidget(self.cacheProgressBar)
        progress_layout.addWidget(self.cacheProgressLabel)

        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.clearCacheButton = PrimaryPushButton(FluentIcon.DELETE, lang.get("clear_cache"))
        self.clearCacheButton.setFixedHeight(40)
        self.clearCacheButton.clicked.connect(self.clearAudioCache)

        self.cancelClearButton = PushButton(FluentIcon.CLOSE, lang.get("cancel"))
        self.cancelClearButton.setFixedHeight(40)
        self.cancelClearButton.clicked.connect(self.cancelClearCache)
        self.cancelClearButton.hide()

        button_layout.addWidget(self.clearCacheButton)
        button_layout.addWidget(self.cancelClearButton)
        button_layout.addStretch()

        control_layout.addLayout(progress_layout)
        control_layout.addLayout(button_layout)
        content_layout.addWidget(control_card)

        # 日志区域
        log_card = CardWidget()
        log_card.setFixedHeight(300)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(lang.get("recent_activity"))
        log_layout.addWidget(log_title)

        self.cacheLogText = TextEdit()
        self.cacheLogText.setReadOnly(True)
        self.cacheLogText.setFixedHeight(220)
        log_layout.addWidget(self.cacheLogText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self.clearCacheInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.cacheLogHandler = LogHandler(self.cacheLogText)

        # 应用样式
        self.setCacheStyles()

    def setCacheStyles(self):
        """设置缓存界面样式"""
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            self.clearCacheInterface.setStyleSheet("""
                #cacheTitle {
                    color: rgb(0, 0, 0);
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
        else:
            self.clearCacheInterface.setStyleSheet("""
                #cacheTitle {
                    color: rgb(255, 255, 255);
                    font-size: 24px;
                    font-weight: bold;
                }
            """)

    def setupHistoryInterface(self):
        """设置历史记录界面"""
        # 创建滚动区域
        scroll = ScrollArea(self.historyInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # 历史统计卡片
        stats_card = CardWidget()
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(25, 20, 25, 20)
        stats_layout.setSpacing(15)

        # 标题
        stats_title = TitleLabel(lang.get("history_stats"))
        stats_title.setObjectName("historyTitle")
        stats_layout.addWidget(stats_title)

        # 统计信息
        history_size = self.download_history.get_history_size()

        # 文件数量显示
        count_row = QHBoxLayout()
        count_icon = IconWidget(FluentIcon.DOCUMENT)
        count_icon.setFixedSize(24, 24)
        self.historyCountLabel = SubtitleLabel(lang.get("files_recorded", history_size))
        self.historyCountLabel.setObjectName("historyCount")

        count_row.addWidget(count_icon)
        count_row.addWidget(self.historyCountLabel)
        count_row.addStretch()

        stats_layout.addLayout(count_row)

        # 历史文件位置标签（固定显示）
        self.historyLocationLabel = CaptionLabel("")
        self.historyLocationLabel.setWordWrap(True)
        self.historyLocationLabel.setStyleSheet(
            "QLabel { background-color: rgba(255, 255, 255, 0.05); padding: 8px; border-radius: 4px; }")
        stats_layout.addWidget(self.historyLocationLabel)

        # 根据是否有历史记录来更新位置标签
        if history_size > 0:
            history_file = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor", "extracted_history.json")
            self.historyLocationLabel.setText(lang.get("history_file_location", history_file))
            self.historyLocationLabel.show()
        else:
            self.historyLocationLabel.hide()

        # 操作按钮行
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 10, 0, 0)

        # 清除历史按钮（始终显示）
        self.clearHistoryButton = PrimaryPushButton(FluentIcon.DELETE, lang.get("clear_history"))
        self.clearHistoryButton.setFixedHeight(40)
        self.clearHistoryButton.clicked.connect(self.clearHistory)
        button_layout.addWidget(self.clearHistoryButton)

        # 查看历史文件按钮（根据条件显示）
        self.viewHistoryButton = PushButton(FluentIcon.VIEW, lang.get("view_history_file"))
        self.viewHistoryButton.setFixedHeight(40)
        self.viewHistoryButton.clicked.connect(
            lambda: open_directory(os.path.dirname(self.download_history.history_file)))
        button_layout.addWidget(self.viewHistoryButton)

        # 根据是否有历史记录来显示/隐藏查看按钮
        if history_size > 0:
            self.viewHistoryButton.show()
        else:
            self.viewHistoryButton.hide()

        button_layout.addStretch()
        stats_layout.addLayout(button_layout)

        content_layout.addWidget(stats_card)

        # 历史记录概览卡片（固定结构）
        self.historyOverviewCard = CardWidget()
        overview_layout = QVBoxLayout(self.historyOverviewCard)
        overview_layout.setContentsMargins(20, 15, 20, 15)

        overview_title = StrongBodyLabel(lang.get("history_overview"))
        overview_layout.addWidget(overview_title)

        self.historyStatsLabel = CaptionLabel("")
        overview_layout.addWidget(self.historyStatsLabel)

        # 更新概览信息
        self.updateHistoryOverview(history_size)

        content_layout.addWidget(self.historyOverviewCard)

        # 日志区域
        log_card = CardWidget()
        log_card.setFixedHeight(300)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(lang.get("recent_activity"))
        log_layout.addWidget(log_title)

        self.historyLogText = TextEdit()
        self.historyLogText.setReadOnly(True)
        self.historyLogText.setFixedHeight(220)
        log_layout.addWidget(self.historyLogText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self.historyInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.historyLogHandler = LogHandler(self.historyLogText)

        # 应用样式
        self.setHistoryStyles()

    def updateHistoryOverview(self, history_size):
        """更新历史概览信息"""
        if history_size > 0:
            avg_files = history_size // max(1, history_size // 50)
            try:
                file_size = os.path.getsize(self.download_history.history_file) / 1024
            except:
                file_size = 0

            stats_info = f"""
• {lang.get('total_files', history_size)}
• {lang.get('avg_files_per_extraction', avg_files)}
• {lang.get('history_file_size', f"{file_size:.1f}")}
            """.strip()

            self.historyStatsLabel.setText(stats_info)
            self.historyOverviewCard.show()
        else:
            self.historyOverviewCard.hide()

    def onInterfaceChanged(self, index):
        """界面切换事件处理"""
        try:
            current_widget = self.stackedWidget.widget(index)
            # 如果切换到历史界面，刷新数据
            if current_widget == self.historyInterface:
                self.refreshHistoryInterface()
        except Exception as e:
            pass

    def setupHistoryButtons(self, history_size):
        """设置历史界面的按钮"""
        # 清除旧布局
        if self.historyButtonContainer.layout():
            while self.historyButtonContainer.layout().count():
                child = self.historyButtonContainer.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        # 创建新布局
        button_layout = QHBoxLayout(self.historyButtonContainer)
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # 清除历史按钮（始终显示）
        self.clearHistoryButton = PrimaryPushButton(FluentIcon.DELETE, lang.get("clear_history"))
        self.clearHistoryButton.setFixedHeight(40)
        self.clearHistoryButton.clicked.connect(self.clearHistory)
        button_layout.addWidget(self.clearHistoryButton)

        # 查看历史文件按钮（仅当有文件时显示）
        if history_size > 0:
            view_history_btn = PushButton(FluentIcon.VIEW, lang.get("view_history_file"))
            view_history_btn.setFixedHeight(40)
            view_history_btn.clicked.connect(
                lambda: open_directory(os.path.dirname(self.download_history.history_file)))
            button_layout.addWidget(view_history_btn)

        button_layout.addStretch()

    def refreshHistoryInterface(self):
        """刷新历史界面显示"""
        try:
            # 获取最新的历史记录数量
            history_size = self.download_history.get_history_size()

            # 更新计数显示
            if hasattr(self, 'historyCountLabel'):
                self.historyCountLabel.setText(lang.get("files_recorded", history_size))

            # 更新位置标签
            if hasattr(self, 'historyLocationLabel'):
                if history_size > 0:
                    history_file = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor",
                                                "extracted_history.json")
                    self.historyLocationLabel.setText(lang.get("history_file_location", history_file))
                    self.historyLocationLabel.show()
                else:
                    self.historyLocationLabel.hide()

            # 更新查看按钮的显示/隐藏
            if hasattr(self, 'viewHistoryButton'):
                if history_size > 0:
                    self.viewHistoryButton.show()
                else:
                    self.viewHistoryButton.hide()

            # 更新概览信息
            if hasattr(self, 'updateHistoryOverview'):
                self.updateHistoryOverview(history_size)

        except Exception as e:
            print(f"Error refreshing history interface: {e}")

    def setHistoryStyles(self):
        """设置历史界面样式"""
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            self.historyInterface.setStyleSheet("""
                #historyTitle {
                    color: rgb(0, 0, 0);
                    font-size: 24px;
                    font-weight: bold;
                }
                #historyCount {
                    color: rgb(0, 120, 215);
                    font-size: 20px;
                    font-weight: 600;
                }
            """)
        else:
            self.historyInterface.setStyleSheet("""
                #historyTitle {
                    color: rgb(255, 255, 255);
                    font-size: 24px;
                    font-weight: bold;
                }
                #historyCount {
                    color: rgb(0, 212, 255);
                    font-size: 20px;
                    font-weight: 600;
                }
            """)

    def setupSettingsInterface(self):
        """设置设置界面"""
        # 创建滚动区域
        scroll = ScrollArea(self.settingsInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # 应用设置组
        app_group = QWidget()
        app_group_layout = QVBoxLayout(app_group)
        group_title = TitleLabel(lang.get("app_settings"))
        app_group_layout.addWidget(group_title)

        # 语言设置卡片
        language_card = CardWidget()
        lang_card_layout = QVBoxLayout(language_card)
        lang_card_layout.setContentsMargins(20, 15, 20, 15)
        lang_card_layout.setSpacing(15)

        lang_title = StrongBodyLabel(lang.get('language_region'))
        lang_card_layout.addWidget(lang_title)

        # 当前语言显示
        current_lang_row = QHBoxLayout()
        current_lang_label = BodyLabel(lang.get("current_language"))
        current_lang_value = StrongBodyLabel(lang.get_language_name())
        current_lang_row.addWidget(current_lang_label)
        current_lang_row.addStretch()
        current_lang_row.addWidget(current_lang_value)

        lang_card_layout.addLayout(current_lang_row)

        # 语言选择
        lang_select_row = QHBoxLayout()
        lang_select_label = BodyLabel(lang.get("select_language"))
        self.languageCombo = ComboBox()
        self.languageCombo.addItems(["中文", "English"])
        self.languageCombo.setCurrentText(lang.get_language_name())
        self.languageCombo.setFixedWidth(150)

        lang_select_row.addWidget(lang_select_label)
        lang_select_row.addStretch()
        lang_select_row.addWidget(self.languageCombo)

        lang_card_layout.addLayout(lang_select_row)

        # 应用语言按钮
        apply_lang_layout = QHBoxLayout()
        self.applyLangButton = PrimaryPushButton(FluentIcon.SAVE, lang.get("save"))
        self.applyLangButton.clicked.connect(self.applyLanguage)
        apply_lang_layout.addStretch()
        apply_lang_layout.addWidget(self.applyLangButton)

        lang_card_layout.addLayout(apply_lang_layout)
        app_group_layout.addWidget(language_card)

        # 外观设置卡片
        appearance_card = CardWidget()
        appearance_card_layout = QVBoxLayout(appearance_card)
        appearance_card_layout.setContentsMargins(20, 15, 20, 15)
        appearance_card_layout.setSpacing(15)

        appearance_title = StrongBodyLabel(lang.get('appearance'))
        appearance_card_layout.addWidget(appearance_title)

        # 主题选择
        theme_row = QHBoxLayout()
        theme_label = BodyLabel(lang.get("theme_settings"))
        self.themeCombo = ComboBox()
        self.themeCombo.addItems([
            lang.get("theme_dark"),
            lang.get("theme_light"),
            lang.get("theme_system")
        ])

        # 设置当前主题
        current_theme = self.config_manager.get("theme", "dark")
        if current_theme == "dark":
            self.themeCombo.setCurrentIndex(0)
        elif current_theme == "light":
            self.themeCombo.setCurrentIndex(1)
        else:
            self.themeCombo.setCurrentIndex(2)

        self.themeCombo.currentTextChanged.connect(self.onThemeChanged)
        self.themeCombo.setFixedWidth(150)

        theme_row.addWidget(theme_label)
        theme_row.addStretch()
        theme_row.addWidget(self.themeCombo)

        appearance_card_layout.addLayout(theme_row)
        app_group_layout.addWidget(appearance_card)

        # 性能设置卡片
        performance_card = CardWidget()
        perf_card_layout = QVBoxLayout(performance_card)
        perf_card_layout.setContentsMargins(20, 15, 20, 15)
        perf_card_layout.setSpacing(15)

        perf_title = StrongBodyLabel(lang.get('performance'))
        perf_card_layout.addWidget(perf_title)

        # 默认线程数设置
        threads_row = QHBoxLayout()
        threads_label = BodyLabel(lang.get("default_threads"))
        self.defaultThreadsSpinBox = SpinBox()
        self.defaultThreadsSpinBox.setRange(1, 128)
        self.defaultThreadsSpinBox.setValue(
            self.config_manager.get("threads", min(32, multiprocessing.cpu_count() * 2)))
        self.defaultThreadsSpinBox.setFixedWidth(120)
        self.defaultThreadsSpinBox.valueChanged.connect(self.saveThreadsConfig)

        threads_row.addWidget(threads_label)
        threads_row.addStretch()
        threads_row.addWidget(self.defaultThreadsSpinBox)

        # 默认MP3转换设置
        mp3_row = QHBoxLayout()
        mp3_label = BodyLabel(lang.get("default_mp3_conversion"))
        self.defaultMp3CheckBox = CheckBox()
        self.defaultMp3CheckBox.setChecked(self.config_manager.get("convert_to_mp3", True))
        self.defaultMp3CheckBox.toggled.connect(self.saveMp3Config)

        mp3_row.addWidget(mp3_label)
        mp3_row.addStretch()
        mp3_row.addWidget(self.defaultMp3CheckBox)

        perf_card_layout.addLayout(threads_row)
        perf_card_layout.addLayout(mp3_row)
        app_group_layout.addWidget(performance_card)

        content_layout.addWidget(app_group)

        # 日志区域
        log_card = CardWidget()
        log_card.setFixedHeight(250)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(lang.get("recent_activity"))
        log_layout.addWidget(log_title)

        self.settingsLogText = TextEdit()
        self.settingsLogText.setReadOnly(True)
        self.settingsLogText.setFixedHeight(170)
        log_layout.addWidget(self.settingsLogText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self.settingsInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.settingsLogHandler = LogHandler(self.settingsLogText)

    def setupAboutInterface(self):
        """设置关于界面"""
        # 创建滚动区域
        scroll = ScrollArea(self.aboutInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # 关于应用卡片
        about_card = CardWidget()
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(30, 25, 30, 25)
        about_layout.setSpacing(20)

        # 应用头部
        header_layout = QHBoxLayout()

        # 左侧：图标和基本信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        app_title = DisplayLabel("Roblox Audio Extractor")
        app_title.setObjectName("aboutTitle")

        version_label = SubtitleLabel(lang.get("about_version"))
        version_label.setObjectName("aboutVersion")

        author_label = BodyLabel(lang.get("about_author"))
        license_label = CaptionLabel(lang.get("about_license"))

        info_layout.addWidget(app_title)
        info_layout.addWidget(version_label)
        info_layout.addSpacing(10)
        info_layout.addWidget(author_label)
        info_layout.addWidget(license_label)

        # 右侧：应用图标
        icon_widget = QWidget()
        icon_widget.setFixedSize(120, 120)
        icon_layout = QVBoxLayout(icon_widget)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        self.about_icon_label = QLabel()
        self.about_icon_label.setAlignment(Qt.AlignCenter)
        self.loadAboutIcon()
        icon_layout.addWidget(self.about_icon_label)

        header_layout.addLayout(info_layout, 2)
        header_layout.addWidget(icon_widget, 1)

        about_layout.addLayout(header_layout)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: rgba(255, 255, 255, 0.2); }")
        about_layout.addWidget(separator)

        # 应用描述
        desc_label = BodyLabel(lang.get("about_description"))
        desc_label.setWordWrap(True)
        about_layout.addWidget(desc_label)

        # 功能特色重复展示
        features_title = StrongBodyLabel(lang.get("features"))
        about_layout.addWidget(features_title)

        features_layout = QVBoxLayout()
        features_layout.setSpacing(8)

        feature_items = [
            lang.get("feature_1"),
            lang.get("feature_2"),
            lang.get("feature_3"),
            lang.get("feature_4")
        ]

        for i, feature in enumerate(feature_items, 1):
            feature_label = CaptionLabel(f"{i}. {feature}")
            features_layout.addWidget(feature_label)

        about_layout.addLayout(features_layout)

        content_layout.addWidget(about_card)

        # 链接和支持卡片
        links_card = CardWidget()
        links_layout = QVBoxLayout(links_card)
        links_layout.setContentsMargins(20, 15, 20, 15)
        links_layout.setSpacing(15)

        links_title = StrongBodyLabel(lang.get("links_and_support"))
        links_layout.addWidget(links_title)

        # GitHub链接
        github_layout = QHBoxLayout()
        github_btn = HyperlinkButton(
            "https://github.com/JustKanade/Roblox-Audio-Extractor",
            lang.get("github_link")
        )
        github_btn.setIcon(FluentIcon.GITHUB)
        github_layout.addWidget(github_btn)
        github_layout.addStretch()

        links_layout.addLayout(github_layout)

        # 技术信息
        tech_info = f"""
{lang.get('tech_stack')}: Python 3.x + PyQt5 + PyQt-Fluent-Widgets
{lang.get('purpose')}: Roblox {lang.get('extract_audio')}
{lang.get('license')}: GNU AGPLv3
        """.strip()

        tech_label = CaptionLabel(tech_info)
        links_layout.addWidget(tech_label)

        content_layout.addWidget(links_card)

        # 系统信息卡片
        system_card = CardWidget()
        system_layout = QVBoxLayout(system_card)
        system_layout.setContentsMargins(20, 15, 20, 15)
        system_layout.setSpacing(10)

        system_title = StrongBodyLabel(lang.get("system_info"))
        system_layout.addWidget(system_title)

        # 收集系统信息
        system_info = f"""
{lang.get('operating_system')}: {os.name} ({sys.platform})
{lang.get('python_version')}: {sys.version.split()[0]}
{lang.get('cpu_cores')}: {multiprocessing.cpu_count()}
{lang.get('ffmpeg_status')}: {lang.get('available') if is_ffmpeg_available() else lang.get('not_available')}
        """.strip()

        system_info_label = CaptionLabel(system_info)
        system_layout.addWidget(system_info_label)

        content_layout.addWidget(system_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self.aboutInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 应用样式
        self.setAboutStyles()

    def setAboutStyles(self):
        """设置关于页面样式"""
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            self.aboutInterface.setStyleSheet("""
                #aboutTitle {
                    color: rgb(0, 0, 0);
                    font-size: 32px;
                    font-weight: bold;
                }
                #aboutVersion {
                    color: rgb(0, 120, 215);
                    font-size: 18px;
                    font-weight: 600;
                }
            """)
        else:
            self.aboutInterface.setStyleSheet("""
                #aboutTitle {
                    color: rgb(255, 255, 255);
                    font-size: 32px;
                    font-weight: bold;
                }
                #aboutVersion {
                    color: rgb(0, 212, 255);
                    font-size: 18px;
                    font-weight: 600;
                }
            """)

    def loadAboutIcon(self):
        """加载关于页面图标"""
        try:
            icon_path = resource_path(os.path.join("icons", "Roblox-Audio-Extractor.png"))
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                scaled_pixmap = pixmap.scaled(
                    100, 100,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.about_icon_label.setPixmap(scaled_pixmap)
            else:
                # 使用默认图标
                self.about_icon_label.setText("♪")
                font = QFont()
                font.setPointSize(64)
                self.about_icon_label.setFont(font)
                self.about_icon_label.setAlignment(Qt.AlignCenter)
        except Exception as e:
            print(f"无法加载关于页面图标: {e}")

    def add_welcome_message(self):
        """添加欢迎消息到主页日志"""
        log = LogHandler(self.homeLogText)
        log.info(lang.get('welcome_message'))
        log.info(lang.get('about_version'))
        log.info(f"{lang.get('default_dir')}: {self.default_dir}")
        log.success(lang.get("ui_upgraded"))
        log.info(lang.get("config_file_location", self.config_manager.config_file))

    def browseDirectory(self):
        """浏览目录对话框"""
        directory = QFileDialog.getExistingDirectory(self, lang.get("directory"), self.dirInput.text())
        if directory:
            self.dirInput.setText(directory)
            self.config_manager.set("last_directory", directory)

    def updateClassificationInfo(self):
        """更新分类信息标签"""
        if self.durationRadio.isChecked():
            self.classInfoLabel.setText(lang.get("info_duration_categories"))
        else:
            self.classInfoLabel.setText(lang.get("info_size_categories"))

    def onThemeChanged(self, theme_name):
        """主题更改事件处理"""
        if theme_name == lang.get("theme_dark"):
            setTheme(Theme.DARK)
            self.config_manager.set("theme", "dark")
        elif theme_name == lang.get("theme_light"):
            setTheme(Theme.LIGHT)
            self.config_manager.set("theme", "light")
        else:
            setTheme(Theme.AUTO)
            self.config_manager.set("theme", "auto")

        # 重新应用所有界面样式
        self.updateAllStyles()

        # 记录主题更改
        if hasattr(self, 'settingsLogHandler'):
            self.settingsLogHandler.success(lang.get("theme_changed", theme_name))

    def updateAllStyles(self):
        """更新所有界面的样式以匹配当前主题"""
        try:
            theme = self.config_manager.get("theme", "dark")

            # 设置主窗口背景
            if theme == "light":
                main_bg = "rgb(243, 243, 243)"
                text_color = "rgb(0, 0, 0)"
                subtitle_color = "rgba(0, 0, 0, 0.7)"
                accent_color = "rgb(0, 120, 215)"
            else:
                main_bg = "rgb(32, 32, 32)"
                text_color = "rgb(255, 255, 255)"
                subtitle_color = "rgba(255, 255, 255, 0.8)"
                accent_color = "rgb(0, 212, 255)"

            # 应用主窗口样式
            self.setStyleSheet(f"""
                MSFluentWindow {{
                    background-color: {main_bg};
                }}
                QWidget {{
                    background-color: transparent;
                }}
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QScrollArea > QWidget > QWidget {{
                    background-color: transparent;
                }}
            """)

            # 更新主页样式
            if hasattr(self, 'homeInterface'):
                self.setHomeStyles()

            # 更新清除缓存界面样式
            if hasattr(self, 'clearCacheInterface'):
                self.setCacheStyles()

            # 更新历史界面样式
            if hasattr(self, 'historyInterface'):
                self.setHistoryStyles()

            # 更新关于界面样式
            if hasattr(self, 'aboutInterface'):
                self.setAboutStyles()

        except Exception as e:
            print(f"更新样式时出错: {e}")

    def saveThreadsConfig(self, value):
        """保存线程数配置"""
        self.config_manager.set("threads", value)
        if hasattr(self, 'settingsLogHandler'):
            self.settingsLogHandler.info(lang.get("saved", f"{lang.get('default_threads')}: {value}"))

    def saveMp3Config(self, checked):
        """保存MP3转换配置"""
        self.config_manager.set("convert_to_mp3", checked)
        if hasattr(self, 'settingsLogHandler'):
            status = lang.get('enabled') if checked else lang.get('disabled')
            self.settingsLogHandler.info(lang.get("saved", f"{lang.get('default_mp3_conversion')}: {status}"))

    def startExtraction(self):
        """开始提取音频"""
        # 获取用户选择的目录
        selected_dir = self.dirInput.text()

        # 检查目录是否存在
        if not os.path.exists(selected_dir):
            result = MessageBox(
                lang.get("create_dir_prompt"),
                lang.get("dir_not_exist", selected_dir),
                self
            )

            if result.exec():
                try:
                    os.makedirs(selected_dir, exist_ok=True)
                    self.extractLogHandler.success(lang.get("dir_created", selected_dir))
                except Exception as e:
                    self.extractLogHandler.error(lang.get("dir_create_failed", str(e)))
                    return
            else:
                self.extractLogHandler.warning(lang.get("operation_cancelled"))
                return

        # 获取线程数
        try:
            num_threads = self.threadsSpinBox.value()
            if num_threads < 1:
                self.extractLogHandler.warning(lang.get("threads_min_error"))
                num_threads = min(32, multiprocessing.cpu_count() * 2)
                self.threadsSpinBox.setValue(num_threads)

            if num_threads > 64:
                result = MessageBox(
                    lang.get("confirm_high_threads"),
                    lang.get("threads_high_warning"),
                    self
                )

                if not result.exec():
                    num_threads = min(32, multiprocessing.cpu_count() * 2)
                    self.threadsSpinBox.setValue(num_threads)
                    self.extractLogHandler.info(lang.get("threads_adjusted", num_threads))
        except ValueError:
            self.extractLogHandler.warning(lang.get("input_invalid"))
            num_threads = min(32, multiprocessing.cpu_count() * 2)
            self.threadsSpinBox.setValue(num_threads)

        # 获取分类方法
        classification_method = ClassificationMethod.DURATION if self.durationRadio.isChecked() else ClassificationMethod.SIZE

        # 如果选择时长分类但没有ffmpeg，显示警告
        if classification_method == ClassificationMethod.DURATION and not is_ffmpeg_available():
            result = MessageBox(
                lang.get("confirm"),
                lang.get("ffmpeg_not_installed"),
                self
            )

            if not result.exec():
                self.extractLogHandler.warning(lang.get("operation_cancelled"))
                return

        # 创建并启动提取线程
        self.extraction_worker = ExtractionWorker(
            selected_dir,
            num_threads,
            self.download_history,
            classification_method,
            self.mp3CheckBox.isChecked()
        )

        # 连接信号
        self.extraction_worker.progressUpdated.connect(self.updateExtractionProgress)
        self.extraction_worker.finished.connect(self.extractionFinished)
        self.extraction_worker.logMessage.connect(self.handleExtractionLog)

        # 更新UI状态
        self.extractButton.hide()
        self.cancelButton.show()
        self.progressBar.setValue(0)
        self.progressLabel.setText(lang.get("processing"))

        # 创建任务状态提示
        self.extractionStateTooltip = StateToolTip(
            lang.get("task_running"),
            lang.get("processing"),
            self
        )
        self.extractionStateTooltip.show()

        # 启动线程
        self.extraction_worker.start()

    def cancelExtraction(self):
        """取消提取操作"""
        if self.extraction_worker and self.extraction_worker.isRunning():
            self.extraction_worker.cancel()

            # 更新状态
            if hasattr(self, 'extractionStateTooltip'):
                self.extractionStateTooltip.setContent(lang.get("task_canceled"))
                self.extractionStateTooltip.setState(True)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.extractionStateTooltip.close)

            # 恢复UI
            self.cancelButton.hide()
            self.extractButton.show()

            # 重置进度条
            self.progressBar.setValue(0)
            self.progressLabel.setText(lang.get("ready"))

            self.handleExtractionLog(lang.get("canceled_by_user"), "warning")

    def updateExtractionProgress(self, current, total, elapsed, speed):
        """更新提取进度"""
        # 计算进度百分比
        progress = min(100, int((current / total) * 100)) if total > 0 else 0

        # 计算剩余时间
        remaining = (total - current) / speed if speed > 0 else 0
        remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"

        # 构建状态文本
        status_text = f"{progress}% - {current}/{total} | {speed:.1f} files/s | ETA: {remaining_str}"

        # 更新UI
        self.progressBar.setValue(progress)
        self.progressLabel.setText(status_text)

        # 更新状态提示
        if hasattr(self, 'extractionStateTooltip'):
            self.extractionStateTooltip.setContent(status_text)

    def extractionFinished(self, result):
        """提取完成处理"""
        # 恢复UI状态
        self.cancelButton.hide()
        self.extractButton.show()

        # 重置进度条为0而不是100
        self.progressBar.setValue(0)
        self.progressLabel.setText(lang.get("ready"))

        if result.get("success", False):
            # 显示提取结果
            if "processed" in result and result["processed"] > 0:
                self.extractLogHandler.success(lang.get("extraction_complete"))
                self.extractLogHandler.info(lang.get("processed", result['processed']))
                self.extractLogHandler.info(lang.get("skipped_duplicates", result.get('duplicates', 0)))
                self.extractLogHandler.info(lang.get("skipped_already_processed", result.get('already_processed', 0)))
                self.extractLogHandler.info(lang.get("errors", result.get('errors', 0)))
                self.extractLogHandler.info(lang.get("time_spent", result.get('duration', 0)))
                self.extractLogHandler.info(lang.get("files_per_sec", result.get('files_per_second', 0)))
                self.extractLogHandler.info(lang.get("output_dir", result.get('output_dir', '')))

                # 检查MP3转换结果
                if "mp3_result" in result and result["mp3_result"]:
                    mp3_result = result["mp3_result"]
                    if mp3_result.get("success", False):
                        self.extractLogHandler.success(lang.get("mp3_conversion_complete"))
                        self.extractLogHandler.info(
                            lang.get("converted", mp3_result.get('converted', 0), mp3_result.get('total', 0)))
                        self.extractLogHandler.info(f"跳过重复: {mp3_result.get('skipped', 0)} 文件")
                        self.extractLogHandler.info(f"转换错误: {mp3_result.get('errors', 0)} 文件")
                        self.extractLogHandler.info(f"总耗时: {mp3_result.get('duration', 0):.2f} 秒")
                    else:
                        self.extractLogHandler.info(
                            f"在 {mp3_result.get('duration', 0):.2f} 秒内找到 {mp3_result.get('total', 0)} 个文件")

                # 确定最终输出目录
                final_dir = ""
                if "mp3_result" in result and result["mp3_result"] and result["mp3_result"].get("success", False):
                    final_dir = result["mp3_result"].get("output_dir", "")
                    dir_type = lang.get("mp3_category")
                else:
                    final_dir = result.get("output_dir", "")
                    dir_type = lang.get("ogg_category")

                # 尝试打开目录
                if final_dir and os.path.exists(final_dir):
                    open_success = open_directory(final_dir)
                    if open_success:
                        self.extractLogHandler.info(lang.get("opening_output_dir", dir_type))
                    else:
                        self.extractLogHandler.info(lang.get("manual_navigate", final_dir))

                # 更新状态提示
                if hasattr(self, 'extractionStateTooltip'):
                    self.extractionStateTooltip.setContent(lang.get("extraction_complete"))
                    self.extractionStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.extractionStateTooltip.close)

                # 显示完成消息
                InfoBar.success(
                    title=lang.get("task_completed"),
                    content=lang.get("extraction_complete"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )

                # 刷新历史界面以显示最新的文件数量
                self.refreshHistoryInterface()
            else:
                self.extractLogHandler.warning(lang.get("no_files_processed"))

                # 更新状态提示
                if hasattr(self, 'extractionStateTooltip'):
                    self.extractionStateTooltip.setContent(lang.get("no_files_processed"))
                    self.extractionStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.extractionStateTooltip.close)
        else:
            # 显示错误
            self.extractLogHandler.error(lang.get("error_occurred", result.get('error', '')))

            # 更新状态提示
            if hasattr(self, 'extractionStateTooltip'):
                self.extractionStateTooltip.setContent(lang.get("task_failed"))
                self.extractionStateTooltip.setState(False)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.extractionStateTooltip.close)

            # 显示错误消息
            InfoBar.error(
                title=lang.get("task_failed"),
                content=result.get('error', lang.get('error_occurred', '')),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def handleExtractionLog(self, message, msg_type="info"):
        """处理提取过程中的日志消息"""
        if msg_type == "info":
            self.extractLogHandler.info(message)
        elif msg_type == "success":
            self.extractLogHandler.success(message)
        elif msg_type == "warning":
            self.extractLogHandler.warning(message)
        elif msg_type == "error":
            self.extractLogHandler.error(message)

    def clearAudioCache(self):
        """清除音频缓存"""
        # 确认对话框
        result = MessageBox(
            lang.get("clear_cache"),
            lang.get("confirm_clear_cache"),
            self
        )

        if not result.exec():
            self.cacheLogHandler.info(lang.get("operation_cancelled"))
            return

        # 创建并启动缓存清理线程
        self.cache_clear_worker = CacheClearWorker(self.default_dir)

        # 连接信号
        self.cache_clear_worker.progressUpdated.connect(self.updateCacheProgress)
        self.cache_clear_worker.finished.connect(self.cacheClearFinished)

        # 更新UI状态
        self.clearCacheButton.hide()
        self.cancelClearButton.show()
        self.cacheProgressBar.setValue(0)
        self.cacheProgressLabel.setText(lang.get("processing"))

        # 创建任务状态提示
        self.cacheStateTooltip = StateToolTip(
            lang.get("task_running"),
            lang.get("processing"),
            self
        )
        self.cacheStateTooltip.show()

        # 启动线程
        self.cache_clear_worker.start()

    def cancelClearCache(self):
        """取消缓存清理操作"""
        if self.cache_clear_worker and self.cache_clear_worker.isRunning():
            self.cache_clear_worker.cancel()

            # 更新状态
            if hasattr(self, 'cacheStateTooltip'):
                self.cacheStateTooltip.setContent(lang.get("task_canceled"))
                self.cacheStateTooltip.setState(True)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.cacheStateTooltip.close)

            # 恢复UI
            self.cancelClearButton.hide()
            self.clearCacheButton.show()

            # 重置进度条
            self.cacheProgressBar.setValue(0)
            self.cacheProgressLabel.setText(lang.get("ready"))

            self.cacheLogHandler.warning(lang.get("canceled_by_user"))

    def updateCacheProgress(self, current, total):
        """更新缓存清理进度"""
        # 计算进度百分比
        progress = min(100, int((current / total) * 100)) if total > 0 else 0

        # 构建状态文本
        status_text = f"{progress}% - {current}/{total}"

        # 更新UI
        self.cacheProgressBar.setValue(progress)
        self.cacheProgressLabel.setText(status_text)

        # 更新状态提示
        if hasattr(self, 'cacheStateTooltip'):
            self.cacheStateTooltip.setContent(status_text)

    def cacheClearFinished(self, success, cleared_files, total_files, error_msg):
        """缓存清理完成处理"""
        # 恢复UI状态
        self.cancelClearButton.hide()
        self.clearCacheButton.show()

        # 重置进度条为0而不是100
        self.cacheProgressBar.setValue(0)
        self.cacheProgressLabel.setText(lang.get("ready"))

        if success:
            if cleared_files > 0:
                self.cacheLogHandler.success(lang.get("cache_cleared", cleared_files, total_files))

                # 更新状态提示
                if hasattr(self, 'cacheStateTooltip'):
                    self.cacheStateTooltip.setContent(lang.get("cache_cleared", cleared_files, total_files))
                    self.cacheStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.cacheStateTooltip.close)

                # 显示完成消息
                InfoBar.success(
                    title=lang.get("task_completed"),
                    content=lang.get('cache_cleared', cleared_files, total_files),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            else:
                self.cacheLogHandler.warning(lang.get("no_cache_found"))

                # 更新状态提示
                if hasattr(self, 'cacheStateTooltip'):
                    self.cacheStateTooltip.setContent(lang.get("no_cache_found"))
                    self.cacheStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.cacheStateTooltip.close)
        else:
            # 显示错误
            self.cacheLogHandler.error(lang.get("clear_cache_failed", error_msg))

            # 更新状态提示
            if hasattr(self, 'cacheStateTooltip'):
                self.cacheStateTooltip.setContent(lang.get("task_failed"))
                self.cacheStateTooltip.setState(False)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.cacheStateTooltip.close)

            # 显示错误消息
            InfoBar.error(
                title=lang.get("task_failed"),
                content=lang.get('clear_cache_failed', error_msg),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def clearHistory(self):
        """清除提取历史"""
        try:
            # 直接清除历史记录，不显示确认对话框
            self.download_history.clear_history()

            # 延迟刷新界面，避免立即更新UI导致的问题
            QTimer.singleShot(100, self.refreshHistoryInterfaceAfterClear)

            # 显示成功消息
            if hasattr(self, 'historyLogHandler'):
                self.historyLogHandler.success(lang.get("history_cleared"))

            # 延迟显示通知，避免阻塞
            QTimer.singleShot(200, lambda: InfoBar.success(
                title=lang.get("task_completed"),
                content=lang.get('history_cleared'),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            ))
        except Exception as e:
            # 显示错误消息
            if hasattr(self, 'historyLogHandler'):
                self.historyLogHandler.error(lang.get("error_occurred", str(e)))
            traceback.print_exc()

            # 延迟显示错误通知
            QTimer.singleShot(200, lambda: InfoBar.error(
                title=lang.get("task_failed"),
                content=lang.get('error_occurred', str(e)),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            ))

    def refreshHistoryInterfaceAfterClear(self):
        """清除历史后刷新界面"""
        try:
            # 重新加载历史数据
            self.download_history.load_history()
            # 刷新界面
            self.refreshHistoryInterface()
        except Exception as e:
            print(f"Error refreshing after clear: {e}")

    def applyLanguage(self):
        """应用语言设置"""
        selected_language = self.languageCombo.currentText()

        # 保存语言设置到配置文件
        if selected_language == "English":
            lang.save_language_setting("en")
        else:
            lang.save_language_setting("zh")

        # 记录更改
        self.settingsLogHandler.success(lang.get("language_saved"))

        # 显示重启确认对话框
        restart_dialog = MessageBox(
            lang.get("restart_required"),
            lang.get("restart_message"),
            self
        )

        if restart_dialog.exec():
            # 用户选择立即重启
            QApplication.quit()
            # 尝试重启应用
            try:
                import subprocess
                subprocess.Popen([sys.executable] + sys.argv)
            except:
                pass
        else:
            # 用户选择稍后重启
            InfoBar.info(
                title=lang.get("restart_required"),
                content=lang.get("language_saved"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )


def main():
    """主函数 - 程序入口点，使用 GUI 界面"""
    try:
        # 设置高DPI缩放
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

        # 确保应用中的目录和资源存在
        os.makedirs(os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor"), exist_ok=True)
        icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
        os.makedirs(icon_dir, exist_ok=True)

        # 创建应用程序实例
        app = QApplication(sys.argv)

        # 设置应用信息
        app.setApplicationName("Roblox Audio Extractor")
        app.setApplicationDisplayName("Roblox Audio Extractor")
        app.setApplicationVersion("0.15")
        app.setOrganizationName("JustKanade")

        # 设置应用图标
        try:
            icon_path = resource_path(os.path.join("icons", "Roblox-Audio-Extractor.ico"))
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"无法设置应用图标: {e}")

        # 创建主窗口实例
        main_window = MainWindow()

        # 显示启动画面（可选）
        try:
            splash_icon = resource_path(os.path.join("icons", "Roblox-Audio-Extractor.png"))
            if os.path.exists(splash_icon):
                splash = SplashScreen(QIcon(splash_icon), main_window)
                splash.setIconSize(QSize(64, 64))
                splash.raise_()

                # 显示启动画面2秒后关闭
                QTimer.singleShot(2000, splash.finish)
        except Exception as e:
            print(f"无法显示启动画面: {e}")

        # 显示主窗口
        main_window.show()

        # 运行应用程序
        return app.exec_()
    except Exception as e:
        logger.error(f"程序出错: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # 在终端模式下记录错误
        logger.error(f"发生错误: {str(e)}")
        traceback.print_exc()

        # 尝试显示错误对话框
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            from PyQt5.QtWidgets import QMessageBox

            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle("错误")
            error_dialog.setText(f"发生错误: {str(e)}")
            error_dialog.setDetailedText(traceback.format_exc())
            error_dialog.exec_()
        except:
            pass

        sys.exit(1)
