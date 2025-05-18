#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Roblox音频提取器 - 从Roblox缓存中提取音频文件并按音频长度或大小分类
Roblox Audio Extractor - Extract audio files from Roblox cache and classify by audio duration or size
作者/Author: JustKanade
修改/Modified by: User
版本/Version: 0.14.1 (Multiple Classification Methods)
许可/License: GNU Affero General Public License v3.0 (AGPLv3)
"""

import os
import sys
import time
import json
import logging
import threading
import concurrent.futures
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Dict, List, Any, Tuple, Set, Optional
from enum import Enum, auto
import datetime
import queue
import traceback
import hashlib
import multiprocessing
from functools import lru_cache


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# 延迟导入库列表
_LIBS_IMPORTED = False
gzip = shutil = random = string = getpass = subprocess = ThreadPoolExecutor = Fore = Style = init = None


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
            return os.path.join("C:", os.sep, "Users", username, "AppData", "Local", "Temp", "Roblox", "http")
        elif sys.platform == 'darwin':  # macOS
            return os.path.join("/Users", username, "Library", "Caches", "Roblox", "http")
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

    def __init__(self):
        """初始化语言管理器，设置支持的语言和翻译"""
        self.ENGLISH = Language.ENGLISH
        self.CHINESE = Language.CHINESE

        # 翻译字典 - 使用嵌套字典结构更高效
        self._load_translations()

        # 设置当前语言
        self.current_language = self._detect_system_language()
        self._cache = {}  # 添加缓存以提高性能

    def _load_translations(self):
        """加载翻译，分离为单独方法以提高可维护性"""
        self.TRANSLATIONS = {
            "title": {
                self.ENGLISH: "    Roblox-Audio-Extractor Version-0.14.1 ",
                self.CHINESE: "    Roblox-Audio-Extractor Version-0.14.1 "
            },

            "welcome_message": {
                self.ENGLISH: "Welcome to Roblox Audio Extractor!",
                self.CHINESE: "欢迎使用 Roblox-Audio-Extractor "
            },
            "extract_audio": {
                self.ENGLISH: "1. Extract Audio Files",
                self.CHINESE: "1. 提取音频文件"
            },
            "view_history": {
                self.ENGLISH: "3. View Extracted History",
                self.CHINESE: "3. 查看提取历史"
            },
            "clear_history": {
                self.ENGLISH: " Clear Extracted History",
                self.CHINESE: " 清除提取历史"
            },
            "language_settings": {
                self.ENGLISH: "4. Language Settings",
                self.CHINESE: "4. 语言设置"
            },
            "about": {
                self.ENGLISH: "5. About",
                self.CHINESE: "5. 关于"
            },

            'clear_cache': {
                Language.ENGLISH: "2. Clear Audio Cache",
                Language.CHINESE: "2. 清除音频缓存"
            },
            'cache_description': {
                Language.ENGLISH: "Clear all audio cache files with 'oggs' in their names from the default cache directory.\n\nUse this when you want to extract audio from a specific game: clear the cache first, then run the game until it's fully loaded before extracting.",
                Language.CHINESE: "清除默认缓存目录中所有带'oggs'字样的音频缓存文件。\n\n当你想要提取某一特定游戏的音频时使用:先清除缓存,然后运行游戏直至完全加载后再进行提取。"
            },
            'confirm_clear_cache': {
                Language.ENGLISH: "Are you sure you want to clear all audio cache files? This cannot be undone.",
                Language.CHINESE: "确定要清除所有音频缓存文件吗？此操作无法撤销。"
            },
            'cache_cleared': {
                Language.ENGLISH: "Successfully cleared {0} of {1} audio cache files.",
                Language.CHINESE: "成功清除了{1}个缓存文件中的{0}个。"
            },
            'no_cache_found': {
                Language.ENGLISH: "No audio cache files found.",
                Language.CHINESE: "未找到音频缓存文件。"
            },
            'clear_cache_failed': {
                Language.ENGLISH: "Failed to clear cache: {0}",
                Language.CHINESE: "清除缓存失败: {0}"
            },
            'cache_location': {
                Language.ENGLISH: "Cache Directory Location",
                Language.CHINESE: "缓存目录位置"
            },
            'cache_dir_not_found': {
                Language.ENGLISH: "Cache directory not found.",
                Language.CHINESE: "未找到缓存目录。"
            },
            "error_occurred": {
                self.ENGLISH: "An error occurred: {}",
                self.CHINESE: "发生错误：{}"
            },
            "history_stats": {
                self.ENGLISH: "=== Extracted History Statistics ===",
                self.CHINESE: "=== 提取历史统计 ==="
            },
            "files_recorded": {
                self.ENGLISH: "Files recorded in history: {}",
                self.CHINESE: "历史记录中的文件数：{}"
            },
            "history_file_location": {
                self.ENGLISH: "History file location: {}",
                self.CHINESE: "历史记录文件位置：{}"
            },
            "confirm_clear_history": {
                self.ENGLISH: "Are you sure you want to clear all download history?  ",
                self.CHINESE: "您确定要清除所有提取历史吗？"
            },
            "history_cleared": {
                self.ENGLISH: "Extracted history has been cleared.",
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
                self.ENGLISH: "1. Classify by audio duration (requires FFmpeg)",
                self.CHINESE: "1. 按音频时长分类 (需要安装FFmpeg)"
            },
            "classify_by_size": {
                self.ENGLISH: "2. Classify by file size",
                self.CHINESE: "2. 按文件大小分类"
            },
            "ffmpeg_not_found_warning": {
                self.ENGLISH: "Warning: FFmpeg not found. Duration classification may not work correctly.",
                self.CHINESE: "警告：未找到FFmpeg。按时长分类可能无法正常工作。"
            },
            "ultra_small": {
                self.ENGLISH: "Ultra Small (0-50KB)",
                self.CHINESE: "极小文件 (0-50KB)"
            },
            "small": {
                self.ENGLISH: "Small (50KB-200KB)",
                self.CHINESE: "小文件 (50KB-200KB)"
            },
            "medium": {
                self.ENGLISH: "Medium (200KB-1MB)",
                self.CHINESE: "中等文件 (200KB-1MB)"
            },
            "large": {
                self.ENGLISH: "Large (1MB-5MB)",
                self.CHINESE: "大文件 (1MB-5MB)"
            },
            "ultra_large": {
                self.ENGLISH: "Ultra Large (5MB+)",
                self.CHINESE: "极大文件 (5MB以上)"
            },
            "size_classification_info": {
                self.ENGLISH: "• Files will be organized by file size in different folders",
                self.CHINESE: "• 文件将按文件大小分类到不同文件夹中"
            },
            "duration_classification_info": {
                self.ENGLISH: "• Files will be organized by audio duration in different folders",
                self.CHINESE: "• 文件将按音频时长分类到不同文件夹中"
            },
            # ... [其余翻译保持不变]
        }
        # 添加剩余的翻译
        self._add_remaining_translations()

    def _add_remaining_translations(self):
        """添加剩余的翻译项"""
        remaining = {

            "Creators & Contributors": {
                self.ENGLISH: "Creators & Contributor：JustKanade",
                self.CHINESE: "创作&贡献者：JustKanade："
            },

            "about_info": {
                self.ENGLISH: "This is an open-source tool for extracting audio files from Roblox cache and converting them to MP3. Files can be classified by audio duration or file size.",
                self.CHINESE: "这是一个开源工具，旨在用于从 Roblox 缓存中提取音频文件并将其转换为 Ogg/Mp3。文件可以按音频时长或文件大小分类。"
            },

            "default_dir": {
                self.ENGLISH: "Default directory: ",
                self.CHINESE: "默认目录："
            },
            "input_dir": {
                self.ENGLISH: "Enter directory (press Enter for default): ",
                self.CHINESE: "输入目录（按回车使用默认值）："
            },
            "dir_not_exist": {
                self.ENGLISH: "Directory does not exist: {}",
                self.CHINESE: "目录不存在：{}"
            },
            "create_dir_prompt": {
                self.ENGLISH: "Create directory? (y/n): ",
                self.CHINESE: "创建目录？(y/n)："
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
                self.ENGLISH: "=== Processing Information ===",
                self.CHINESE: "=== 处理信息 ==="
            },
            "info_duration_categories": {
                self.ENGLISH: "• Files will be organized by audio duration in different folders",
                self.CHINESE: "• 文件将按音频时长分类到不同文件夹中"
            },
            "info_mp3_conversion": {
                self.ENGLISH: "• You can convert OGG files to MP3 after extraction",
                self.CHINESE: "• 提取后可以将OGG文件转换为MP3"
            },
            "info_skip_downloaded": {
                self.ENGLISH: "• Previously downloaded files will be skipped",
                self.CHINESE: "• 将跳过之前提取过的文件"
            },
            "threads_prompt": {
                self.ENGLISH: "Enter number of threads (default: {}): ",
                self.CHINESE: "输入线程数（默认：{}）："
            },
            "threads_min_error": {
                self.ENGLISH: "Number of threads must be at least 1",
                self.CHINESE: "线程数必须至少为1"
            },
            "threads_high_warning": {
                self.ENGLISH: "Warning: Using a high number of threads may slow down your computer",
                self.CHINESE: "警告：使用过多线程可能会降低计算机性能"
            },
            "confirm_high_threads": {
                self.ENGLISH: "Continue with high thread count anyway? (y/n): ",
                self.CHINESE: "是否仍使用这么多线程？(y/n)："
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
                self.ENGLISH: "Do you want to convert extracted OGG files to MP3? (y/n): ",
                self.CHINESE: "是否将提取的OGG文件转换为MP3？(y/n)："
            },
            "mp3_conversion_complete": {
                self.ENGLISH: "MP3 conversion completed!",
                self.CHINESE: "MP3转换完成！"
            },
            "converted": {
                self.ENGLISH: "Converted: {} of {} files",
                self.CHINESE: "已转换：{} / {} 个文件"
            },
            "mp3_conversion_failed": {
                self.ENGLISH: "MP3 conversion failed: {}",
                self.CHINESE: "MP3转换失败：{}"
            },
            "opening_output_dir": {
                self.ENGLISH: "Opening {} output directory...",
                self.CHINESE: "正在打开{}输出目录..."
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
                self.CHINESE: "未安装FFmpeg。请安装FFmpeg以转换文件并获取时长信息。"
            },
            "no_ogg_files": {
                self.ENGLISH: "No OGG files found to convert",
                self.CHINESE: "未找到要转换的OGG文件"
            },
            "mp3_conversion": {
                self.ENGLISH: "Converting {} OGG files to MP3...",
                self.CHINESE: "正在将 {} 个OGG文件转换为MP3..."
            },
            "current_language": {
                self.ENGLISH: "Current language: {}",
                self.CHINESE: "当前语言：{}"
            },
            "select_language": {
                self.ENGLISH: "Select language (1. Chinese, 2. English): ",
                self.CHINESE: "选择语言 (1. 中文, 2. 英文): "
            },
            "language_set": {
                self.ENGLISH: "Language set to: {}",
                self.CHINESE: "语言设置为：{}"
            },
            "about_title": {
                self.ENGLISH: "About Roblox Audio Extractor",
                self.CHINESE: "关于 Roblox Audio Extractor"
            },
            "about_version": {
                self.ENGLISH: "Current Version: 0.14.1 ",
                self.CHINESE: "当前版本: 0.14.1"
            },
            "mp3_conversion_info": {
                self.ENGLISH: "Starting MP3 conversion...",
                self.CHINESE: "开始MP3转换..."
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
                self.CHINESE: "音频时长分类:"
            },
            "readme_size_title": {
                self.ENGLISH: "File Size Categories:",
                self.CHINESE: "文件大小分类:"
            },
            "classification_method_used": {
                self.ENGLISH: "Classification method: {}",
                self.CHINESE: "分类方法: {}"
            },
            "classification_by_duration": {
                self.ENGLISH: "by audio duration",
                self.CHINESE: "按音频时长"
            },
            "classification_by_size": {
                self.ENGLISH: "by file size",
                self.CHINESE: "按文件大小"
            },
        }
        # 合并词典
        self.TRANSLATIONS.update(remaining)

    @lru_cache(maxsize=128)
    def _detect_system_language(self) -> Language:
        """检测系统语言并返回相应的语言枚举"""
        try:
            import locale
            system_lang = locale.getdefaultlocale()[0].lower()
            if system_lang and ('zh_' in system_lang or 'cn' in system_lang):
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
            if not self.modified:
                return  # 如果没有修改，不需要保存

            try:
                import json
                with open(self.history_file, 'w') as f:
                    json.dump(list(self.file_hashes), f)
                self.modified = False
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
            if self.file_hashes:
                self.file_hashes = set()
                self.modified = True
                self.save_history()

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


class ProgressBar:
    """可视化进度条，提供更直观的进度显示"""

    def __init__(self, total, width=40, title="", fill_char="█", empty_char="░"):
        """初始化进度条"""
        self.total = max(1, total)  # 避免除以零
        self.width = width
        self.title = title
        self.fill_char = fill_char
        self.empty_char = empty_char
        self.last_progress = -1
        self.last_update_time = 0
        self.update_interval = 0.2  # 限制更新频率，单位秒

    def update(self, current, extra_info=""):
        """更新进度条显示"""
        # 限制更新频率
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return

        progress = min(100, int((current / self.total) * 100))

        # 只有在进度变化时才更新显示
        if progress != self.last_progress:
            self.last_progress = progress
            self.last_update_time = current_time

            filled_width = int(self.width * progress / 100)
            bar = self.fill_char * filled_width + self.empty_char * (self.width - filled_width)

            # 构建显示文本
            if self.title:
                display = f"{self.title} [{bar}] {progress}% ({current}/{self.total}) {extra_info}"
            else:
                display = f"[{bar}] {progress}% ({current}/{self.total}) {extra_info}"

            # 显示进度
            sys.stdout.write(f"\r{display}")
            sys.stdout.flush()

            # 如果完成则换行
            if progress >= 100:
                print()

    def complete(self):
        """完成进度条，确保最后状态正确"""
        if self.last_progress < 100:
            self.update(self.total)
            print()  # 确保换行


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

        # 启动进度条
        total_files = len(files_to_process)
        progress_bar = ProgressBar(total_files, title="Processing:", width=40)

        # 使用线程池处理文件
        batch_size = min(5000, total_files)  # 增加批次大小

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
                        # 更新显示，无需频繁更新
                        if self.processed_count % 10 == 0:
                            stats = self.stats.get_all()
                            elapsed = time.time() - processing_start
                            speed = self.processed_count / elapsed if elapsed > 0 else 0
                            remaining = (total_files - self.processed_count) / speed if speed > 0 else 0
                            remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"
                            extra_info = f"| {speed:.1f} files/s | ETA: {remaining_str}"
                            progress_bar.update(self.processed_count, extra_info)
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
            # 主线程监控进度并更新进度条
            while not work_queue.empty() and not self.cancelled:
                stats = self.stats.get_all()
                elapsed = time.time() - processing_start
                speed = self.processed_count / elapsed if elapsed > 0 else 0
                remaining = (total_files - self.processed_count) / speed if speed > 0 else 0
                remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"
                extra_info = f"| {speed:.1f} files/s | ETA: {remaining_str}"
                progress_bar.update(self.processed_count, extra_info)
                time.sleep(0.5)  # 减少CPU使用

            # 等待所有工作完成
            work_queue.join()
        except KeyboardInterrupt:
            # 允许用户中断处理
            self.cancelled = True
            print("\n操作被用户取消.")

        # 完成进度条
        progress_bar.complete()

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

        # 创建进度条
        progress_bar = ProgressBar(len(ogg_files), title="Converting:", width=40)

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
                        # 更新显示，无需频繁更新
                        if self.processed_count % 10 == 0:
                            stats = self.stats.get_all()
                            elapsed = time.time() - start_time
                            speed = self.processed_count / elapsed if elapsed > 0 else 0
                            remaining = (len(ogg_files) - self.processed_count) / speed if speed > 0 else 0
                            remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"
                            extra_info = f"| {speed:.1f} files/s | ETA: {remaining_str}"
                            progress_bar.update(self.processed_count, extra_info)
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
            # 主线程监控进度并更新进度条
            while not work_queue.empty() and not self.cancelled:
                elapsed = time.time() - start_time
                speed = self.processed_count / elapsed if elapsed > 0 else 0
                remaining = (len(ogg_files) - self.processed_count) / speed if speed > 0 else 0
                remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"
                extra_info = f"| {speed:.1f} files/s | ETA: {remaining_str}"
                progress_bar.update(self.processed_count, extra_info)
                time.sleep(0.5)  # 减少CPU使用

            # 等待所有工作完成
            work_queue.join()
        except KeyboardInterrupt:
            # 允许用户中断处理
            self.cancelled = True
            print("\n操作被用户取消.")

        # 完成进度条
        progress_bar.complete()

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


class ConsoleRedirector:
    """控制台输出重定向器，将控制台输出重定向到 GUI 文本控件"""

    def __init__(self, text_widget, tag=None):
        """初始化重定向器"""
        self.text_widget = text_widget
        self.tag = tag
        self.buffer = ""
        self.buffer_size = 1024  # 缓冲区大小
        self.last_update = 0
        self.update_interval = 0.1  # 更新间隔时间(秒)

    def write(self, message):
        """写入消息到文本控件 - 使用缓冲和节流优化"""
        # 防止空消息
        if not message or message.isspace():
            return

        # 将消息添加到缓冲区
        self.buffer += message

        # 检查是否应该刷新缓冲区
        current_time = time.time()
        should_flush = (
                len(self.buffer) >= self.buffer_size or
                "\n" in self.buffer or
                (current_time - self.last_update) >= self.update_interval
        )

        if should_flush:
            # 更新界面必须在主线程中进行
            self.text_widget.insert(tk.END, self.buffer, self.tag)
            self.text_widget.see(tk.END)  # 自动滚动到最新内容
            self.text_widget.update_idletasks()  # 更轻量级的更新
            self.buffer = ""
            self.last_update = current_time

    def flush(self):
        """刷新输出（为兼容sys.stdout而需要）"""
        if self.buffer:
            self.text_widget.insert(tk.END, self.buffer, self.tag)
            self.text_widget.see(tk.END)
            self.text_widget.update_idletasks()
            self.buffer = ""


class GUILogger:
    """GUI 日志记录器，在 GUI 中显示日志消息并保持不同类型消息的格式"""

    def __init__(self, text_widget):
        """初始化日志记录器"""
        self.text_widget = text_widget
        self.queue = queue.Queue()
        self.running = True
        self.buffer = []  # 消息缓冲
        self.buffer_size = 10  # 批处理大小
        self.last_update = 0
        self.update_interval = 0.1  # 更新间隔(秒)

        # 配置文本标签
        self.text_widget.tag_configure("info", foreground="black")
        self.text_widget.tag_configure("success", foreground="green")
        self.text_widget.tag_configure("warning", foreground="orange")
        self.text_widget.tag_configure("error", foreground="red")

        # 启动处理线程
        self.thread = threading.Thread(target=self._process_queue)
        self.thread.daemon = True
        self.thread.start()

    def _process_queue(self):
        """处理消息队列 - 使用批处理减少UI更新"""
        batch = []
        while self.running:
            try:
                # 获取消息，有短暂超时以便可以退出循环
                message, tag = self.queue.get(timeout=0.1)
                batch.append((message, tag))

                # 尝试获取更多消息直到达到批处理大小或队列为空
                while len(batch) < self.buffer_size:
                    try:
                        message, tag = self.queue.get_nowait()
                        batch.append((message, tag))
                    except queue.Empty:
                        break

                # 处理批次
                if batch:
                    # 在主线程中更新 UI
                    self.text_widget.after(0, self._update_text_batch, batch)
                    batch = []

            except queue.Empty:
                # 如果队列为空但有待处理的消息，处理它们
                if batch:
                    self.text_widget.after(0, self._update_text_batch, batch)
                    batch = []
                continue

    def _update_text_batch(self, messages):
        """在主线程中批量更新文本控件"""
        for message, tag in messages:
            if not message.endswith('\n'):
                message += '\n'
            self.text_widget.insert(tk.END, message, tag)
        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()  # 更轻量级的更新

    def info(self, message):
        """记录信息消息"""
        self.queue.put((message, "info"))

    def success(self, message):
        """记录成功消息"""
        self.queue.put((message, "success"))

    def warning(self, message):
        """记录警告消息"""
        self.queue.put((message, "warning"))

    def error(self, message):
        """记录错误消息"""
        self.queue.put((message, "error"))

    def stop(self):
        """停止日志记录器"""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=2)


class RobloxAudioExtractorGUI:
    """Roblox 音频提取器 GUI 界面"""

    def __init__(self, root):
        """初始化 GUI 界面"""
        # 延迟导入所需库，加快启动速度
        import_libs()

        # 全局引用
        self.root = root

        # 初始化语言管理器
        global lang
        lang = LanguageManager()

        # 获取默认目录
        self.default_dir = get_roblox_default_dir()

        # 设置提取历史记录文件
        app_data_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        os.makedirs(app_data_dir, exist_ok=True)
        history_file = os.path.join(app_data_dir, "extracted_history.json")

        # 初始化提取历史
        self.download_history = ExtractedHistory(history_file)

        # 设置主窗口属性
        self.root.title("Roblox Audio Extractor (Multiple Classification Methods)")
        self.root.geometry("901x552")  # 初始窗口大小
        self.root.minsize(900, 300)  # 最小窗口大小

        # 创建样式
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Arial', 11))
        self.style.configure('TButton', font=('Arial', 11))
        self.style.configure('TFrame', background='#f5f5f5')
        self.style.configure('Header.TLabel', font=('Arial', 14, 'bold'))

        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建顶部标题
        self.header = ttk.Label(self.main_frame, text="Roblox Audio Extractor (Multiple Classification Methods)",
                                style='Header.TLabel')
        self.header.pack(pady=(0, 10))

        # 创建主布局为左侧菜单和右侧内容
        self.content_frame = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

        # 创建左侧菜单框架
        self.menu_frame = ttk.Frame(self.content_frame, padding="5 5 5 5", width=200)
        self.content_frame.add(self.menu_frame, weight=1)

        # 创建右侧内容框架
        self.right_frame = ttk.Frame(self.content_frame, padding="5 5 5 5")
        self.content_frame.add(self.right_frame, weight=4)

        # 设置菜单按钮
        self.setup_menu()

        # 创建状态栏
        self.status_bar = ttk.Label(self.main_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 初始化日志区域
        self.log_frame = ttk.LabelFrame(self.right_frame, text="Log")
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 初始化日志记录器
        self.gui_logger = GUILogger(self.log_text)

        # 设置重定向控制台输出
        self.original_stdout = sys.stdout
        sys.stdout = ConsoleRedirector(self.log_text, "info")

        # 设置本地化界面
        self.update_language()

        # 当前活动任务
        self.active_task = None
        self.task_cancelled = False

        # 分类方法
        self.classification_method = ClassificationMethod.DURATION

        # 显示欢迎消息
        self.gui_logger.info(lang.get('welcome_message'))
        self.gui_logger.info((lang.get('about_version')).strip())
        self.gui_logger.info((lang.get('default_dir') + ": " + self.default_dir).strip())

        # 当窗口关闭时恢复标准输出和停止所有任务
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_scrollable_frame(self, parent):
        """创建可滚动的框架，支持鼠标滚轮"""
        # 创建带滚动条的画布
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # 配置滚动
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # 在画布中创建窗口
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 打包元素
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 添加鼠标滚轮绑定
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        # 不同操作系统的不同绑定
        if sys.platform.startswith("win"):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        elif sys.platform.startswith("darwin"):  # macOS
            canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * event.delta), "units"))
        else:  # Linux
            canvas.bind_all("<Button-4>", lambda event: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda event: canvas.yview_scroll(1, "units"))

        return scrollable_frame

    def on_closing(self):
        """窗口关闭处理函数"""
        # 取消任何正在运行的任务
        self.cancel_active_task()

        # 恢复标准输出
        sys.stdout = self.original_stdout

        # 停止日志记录器
        self.gui_logger.stop()

        # 保存可能的历史更改
        if self.download_history and hasattr(self.download_history, 'modified') and self.download_history.modified:
            self.download_history.save_history()

        # 销毁窗口
        self.root.destroy()

    def setup_menu(self):
        """设置左侧菜单按钮"""
        # 菜单容器，使用垂直方向布局
        self.menu_buttons_frame = ttk.Frame(self.menu_frame)
        self.menu_buttons_frame.pack(fill=tk.Y, expand=False)

        # 创建菜单按钮
        self.btn_extract = ttk.Button(
            self.menu_buttons_frame,
            text="1. Extract Audio",
            command=self.show_extract_frame,
            width=25
        )
        self.btn_extract.pack(fill=tk.X, padx=5, pady=5)

        self.btn_clear_cache = ttk.Button(
            self.menu_buttons_frame,
            text=lang.get('clear_cache'),
            command=self.show_clear_cache_frame,
            width=25
        )
        self.btn_clear_cache.pack(fill=tk.X, padx=5, pady=5)

        self.btn_history = ttk.Button(
            self.menu_buttons_frame,
            text="2. View History",
            command=self.show_history_frame,
            width=25
        )
        self.btn_history.pack(fill=tk.X, padx=5, pady=5)

        self.btn_language = ttk.Button(
            self.menu_buttons_frame,
            text="4. Language Settings",
            command=self.show_language_frame,
            width=25
        )
        self.btn_language.pack(fill=tk.X, padx=5, pady=5)

        self.btn_about = ttk.Button(
            self.menu_buttons_frame,
            text="5. About",
            command=self.show_about_frame,
            width=25
        )
        self.btn_about.pack(fill=tk.X, padx=5, pady=5)

    def show_clear_cache_frame(self):
        """显示清除缓存界面"""
        # 清除右侧框架
        self.clear_right_frame()

        # 创建清除缓存框架
        cache_frame = ttk.LabelFrame(self.right_frame, text=lang.get('clear_cache'))
        cache_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

        # 创建可滚动内容
        content_frame = self.create_scrollable_frame(cache_frame)

        # 添加说明文本
        ttk.Label(content_frame, text=lang.get('cache_description'),
                  wraplength=400).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Label(content_frame, text=lang.get('cache_location') + f":\n{self.default_dir}",
                  wraplength=400).pack(anchor=tk.W, padx=10, pady=5)

        # 添加操作按钮
        clear_btn = ttk.Button(content_frame, text=lang.get('clear_cache'),
                               command=self.clear_audio_cache)
        clear_btn.pack(anchor=tk.CENTER, pady=10)

        # 显示日志框架
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def cancel_active_task(self):
        """取消活动任务"""
        if self.active_task is not None and self.active_task.is_alive():
            # 设置取消标志
            self.task_cancelled = True
            # 等待最多2秒让任务终止
            self.active_task.join(timeout=2)
            # 更新状态
            self.task_cancelled = False
            self.active_task = None
            self.gui_logger.warning(lang.get('canceled_by_user'))
            self.status_bar.config(text="Ready / 就绪")

    def update_language(self):
        """更新界面语言"""
        # 更新标题
        self.header.config(text=lang.get('title').strip())

        # 更新菜单按钮文本
        self.btn_extract.config(text=lang.get('extract_audio'))
        self.btn_history.config(text=lang.get('view_history'))

        self.btn_language.config(text=lang.get('language_settings'))
        self.btn_about.config(text=lang.get('about'))
        self.btn_clear_cache.config(text=lang.get('clear_cache'))

        # 如果当前显示的是清除缓存界面，更新其内容
        if hasattr(self, 'cache_frame') and self.cache_frame.winfo_exists():
            self.show_clear_cache_frame()

        # 更新状态栏
        self.status_bar.config(text="Ready / 就绪")

    def change_language(self, event=None):
        """切换界面语言"""
        selected = self.language_var.get()

        if selected == "English":
            lang.set_language(Language.ENGLISH)
        else:
            lang.set_language(Language.CHINESE)

        # 更新界面语言
        self.update_language()

        # 显示语言已更改消息
        self.gui_logger.success(lang.get('language_set', lang.get_language_name()))

    def clear_right_frame(self):
        """清除右侧内容框架中的所有小部件"""
        # 取消任何正在运行的任务
        self.cancel_active_task()

        for widget in self.right_frame.winfo_children():
            widget.destroy()

        # 重新创建日志区域
        self.log_frame = ttk.LabelFrame(self.right_frame, text="Log")
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, height=5)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 重新初始化日志记录器
        self.gui_logger = GUILogger(self.log_text)

        # 重设重定向控制台输出
        sys.stdout = ConsoleRedirector(self.log_text, "info")

    def show_extract_frame(self):
        """显示提取音频界面"""
        # 清除右侧框架
        self.clear_right_frame()

        # 创建提取音频框架
        extract_frame = ttk.LabelFrame(self.right_frame, text=lang.get('extract_audio'))
        extract_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

        # 创建可滚动内容
        content_frame = self.create_scrollable_frame(extract_frame)

        # 目录选择
        dir_frame = ttk.Frame(content_frame)
        dir_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(dir_frame, text=lang.get('default_dir', '')).pack(side=tk.LEFT, padx=5)

        self.dir_var = tk.StringVar(value=self.default_dir)
        dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=50)
        dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_btn = ttk.Button(dir_frame, text="Browse...", command=self.browse_directory)
        browse_btn.pack(side=tk.LEFT, padx=5)

        # 分类方法选择
        classification_frame = ttk.LabelFrame(content_frame, text=lang.get('classification_method'))
        classification_frame.pack(fill=tk.X, padx=5, pady=5)

        self.classification_var = tk.StringVar(value="duration")

        # 创建单选按钮
        ttk.Radiobutton(
            classification_frame,
            text=lang.get('classify_by_duration'),
            variable=self.classification_var,
            value="duration",
            command=self.update_classification_info
        ).pack(anchor=tk.W, padx=10, pady=2)

        ttk.Radiobutton(
            classification_frame,
            text=lang.get('classify_by_size'),
            variable=self.classification_var,
            value="size",
            command=self.update_classification_info
        ).pack(anchor=tk.W, padx=10, pady=2)

        # 检查FFmpeg是否可用
        if not self._is_ffmpeg_available():
            ttk.Label(
                classification_frame,
                text=lang.get('ffmpeg_not_found_warning'),
                foreground="red"
            ).pack(anchor=tk.W, padx=10, pady=2)

        # 处理选项
        self.options_frame = ttk.LabelFrame(content_frame, text=lang.get('processing_info'))
        self.options_frame.pack(fill=tk.X, padx=5, pady=5)

        # 动态显示分类信息
        self.classification_info_label = ttk.Label(self.options_frame, text=lang.get('info_duration_categories'))
        self.classification_info_label.pack(anchor=tk.W, padx=5, pady=2)

        ttk.Label(self.options_frame, text=lang.get('info_mp3_conversion')).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Label(self.options_frame, text=lang.get('info_skip_downloaded')).pack(anchor=tk.W, padx=5, pady=2)

        # 线程设置
        threads_frame = ttk.Frame(content_frame)
        threads_frame.pack(fill=tk.X, padx=5, pady=5)

        default_threads = min(32, multiprocessing.cpu_count() * 2)
        ttk.Label(threads_frame, text=lang.get('threads_prompt', default_threads).split(':')[0] + ':').pack(
            side=tk.LEFT, padx=5)

        self.threads_var = tk.StringVar(value=str(default_threads))
        threads_spinbox = ttk.Spinbox(threads_frame, from_=1, to=64, textvariable=self.threads_var, width=5)
        threads_spinbox.pack(side=tk.LEFT, padx=5)

        # MP3 转换选项
        convert_frame = ttk.Frame(content_frame)
        convert_frame.pack(fill=tk.X, padx=5, pady=5)

        self.convert_mp3_var = tk.BooleanVar(value=True)
        convert_check = ttk.Checkbutton(convert_frame, text=lang.get('convert_to_mp3_prompt').replace("?", ""),
                                        variable=self.convert_mp3_var)
        convert_check.pack(anchor=tk.W, padx=5)

        # 操作按钮
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)

        self.extract_btn = ttk.Button(buttons_frame, text=lang.get('extract_audio'), command=self.start_extraction)
        self.extract_btn.pack(side=tk.RIGHT, padx=5)

        # 进度条
        self.progress_frame = ttk.Frame(content_frame)
        self.progress_frame.pack(fill=tk.X, padx=5, pady=5)

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, mode='determinate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack(anchor=tk.W, padx=5)

        # 显示日志框架
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def update_classification_info(self):
        """根据所选分类方法更新显示信息"""
        selected = self.classification_var.get()

        if selected == "duration":
            self.classification_method = ClassificationMethod.DURATION
            self.classification_info_label.config(text=lang.get('duration_classification_info'))
        else:
            self.classification_method = ClassificationMethod.SIZE
            self.classification_info_label.config(text=lang.get('size_classification_info'))

    def _is_ffmpeg_available(self) -> bool:
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

    def clear_audio_cache(self):
        """清除音频缓存文件"""
        try:
            # 确认对话框
            if not messagebox.askyesno(
                    lang.get('clear_cache'),
                    lang.get('confirm_clear_cache')
            ):
                self.gui_logger.info(lang.get('operation_cancelled'))
                return

            # 计数器
            total_files = 0
            cleared_files = 0

            # 需要排除的文件夹
            exclude_dirs = {'extracted_mp3', 'extracted_oggs'}

            # 递归搜索所有文件
            for root, dirs, files in os.walk(self.default_dir):
                # 跳过排除的目录
                if any(excluded in root for excluded in exclude_dirs):
                    continue

                for file in files:
                    file_path = os.path.join(root, file)
                    total_files += 1

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
                        continue

            # 显示结果
            self.gui_logger.success(lang.get('cache_cleared', cleared_files, total_files))
        except Exception as e:
            self.gui_logger.error(lang.get('clear_cache_failed', str(e)))

    def browse_directory(self):
        """浏览并选择目录"""
        directory = filedialog.askdirectory(initialdir=self.dir_var.get())
        if directory:
            self.dir_var.set(directory)

    def start_extraction(self):
        """开始提取音频文件"""
        # 获取用户选择的目录
        selected_dir = self.dir_var.get()

        # 检查目录是否存在
        if not os.path.exists(selected_dir):
            result = messagebox.askquestion(
                "Directory not found",
                lang.get('dir_not_exist', selected_dir) + "\n" + lang.get('create_dir_prompt'),
                icon='warning'
            )

            if result == 'yes':
                try:
                    os.makedirs(selected_dir, exist_ok=True)
                    self.gui_logger.success(lang.get('dir_created', selected_dir))
                except Exception as e:
                    self.gui_logger.error(lang.get('dir_create_failed', str(e)))
                    return
            else:
                self.gui_logger.warning(lang.get('operation_cancelled'))
                return

        # 获取线程数
        try:
            num_threads = int(self.threads_var.get())
            if num_threads < 1:
                self.gui_logger.warning(lang.get('threads_min_error'))
                num_threads = min(32, multiprocessing.cpu_count() * 2)
                self.threads_var.set(str(num_threads))

            if num_threads > 64:
                result = messagebox.askquestion(
                    "Warning",
                    lang.get('threads_high_warning') + "\n" + lang.get('confirm_high_threads'),
                    icon='warning'
                )

                if result != 'yes':
                    num_threads = min(32, multiprocessing.cpu_count() * 2)
                    self.threads_var.set(str(num_threads))
                    self.gui_logger.info(lang.get('threads_adjusted', num_threads))
        except ValueError:
            self.gui_logger.warning(lang.get('input_invalid'))
            num_threads = min(32, multiprocessing.cpu_count() * 2)
            self.threads_var.set(str(num_threads))

        # 获取分类方法
        classification_method = ClassificationMethod.DURATION if self.classification_var.get() == "duration" else ClassificationMethod.SIZE

        # 如果选择时长分类但没有ffmpeg，显示警告
        if classification_method == ClassificationMethod.DURATION and not self._is_ffmpeg_available():
            result = messagebox.askquestion(
                "Warning",
                lang.get('ffmpeg_not_installed') + "\n" + lang.get('operation_cancelled'),
                icon='warning'
            )
            if result != 'yes':
                self.gui_logger.warning(lang.get('operation_cancelled'))
                return

        # 创建并启动提取线程
        self.task_cancelled = False
        self.active_task = threading.Thread(target=self.run_extraction_process,
                                            args=(selected_dir, num_threads, classification_method))
        self.active_task.daemon = True
        self.active_task.start()

    def run_extraction_process(self, selected_dir, num_threads, classification_method):
        """运行提取过程"""
        try:
            # 更新状态栏
            self.status_bar.config(text=lang.get('scanning_files'))

            # 初始化并运行提取器
            start_time = time.time()
            extractor = RobloxAudioExtractor(selected_dir, num_threads, "oggs",
                                             self.download_history, classification_method)

            # 覆盖extractor的cancelled属性，使其检查self.task_cancelled的当前值
            def is_cancelled():
                return self.task_cancelled

            extractor.cancelled = is_cancelled

            # 显示正在扫描文件的消息
            self.gui_logger.info(lang.get('scanning_files'))

            # 查找要处理的文件
            files_to_process = extractor.find_files_to_process()
            total_files = len(files_to_process)

            scan_duration = time.time() - start_time
            self.gui_logger.info(lang.get('found_files', total_files, scan_duration))

            if not files_to_process:
                self.gui_logger.warning(lang.get('no_files_found'))
                self.status_bar.config(text="Ready / 就绪")
                self.extract_btn.configure(state='normal')
                self.active_task = None
                return

            # 设置进度更新
            self.processed_count = 0

            # 创建一个周期性的进度更新函数
            def update_progress():
                if self.task_cancelled:
                    return

                # 计算进度百分比
                progress = min(100, int((self.processed_count / total_files) * 100)) if total_files > 0 else 0

                # 计算剩余时间
                elapsed = time.time() - start_time
                speed = self.processed_count / elapsed if elapsed > 0 else 0
                remaining = (total_files - self.processed_count) / speed if speed > 0 else 0
                remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"

                # 构建状态文本
                status_text = f"{progress}% - {self.processed_count}/{total_files} | {speed:.1f} files/s | ETA: {remaining_str}"

                # 更新UI
                self.progress_var.set(progress)
                self.progress_label.config(text=status_text)

                # 如果仍在处理，继续更新
                if self.processed_count < total_files and not self.task_cancelled and self.active_task and self.active_task.is_alive():
                    self.root.after(100, update_progress)

            # 替换extractor的process_file方法来跟踪进度
            original_process_file = extractor.process_file

            def process_file_with_progress(file_path):
                result = original_process_file(file_path)
                self.processed_count += 1
                return result

            extractor.process_file = process_file_with_progress

            # 启动进度更新
            self.root.after(100, update_progress)

            # 更新状态栏
            self.status_bar.config(text=lang.get('processing_with_threads', num_threads))

            # 处理文件
            extraction_result = extractor.process_files()

            # 显示提取结果
            output_dir = extraction_result["output_dir"]
            if extraction_result["processed"] > 0:
                self.gui_logger.success(lang.get('extraction_complete'))
                self.gui_logger.info(lang.get('processed', extraction_result['processed']))
                self.gui_logger.info(lang.get('skipped_duplicates', extraction_result['duplicates']))
                self.gui_logger.info(lang.get('skipped_already_processed', extraction_result['already_processed']))
                self.gui_logger.info(lang.get('errors', extraction_result['errors']))
                self.gui_logger.info(lang.get('time_spent', extraction_result['duration']))
                self.gui_logger.info(lang.get('files_per_sec', extraction_result['files_per_second']))
                self.gui_logger.info(lang.get('output_dir', output_dir))

                # 询问用户是否要转换为MP3
                convert_to_mp3 = self.convert_mp3_var.get()

                mp3_dir = None
                if convert_to_mp3 and not self.task_cancelled:
                    self.gui_logger.info(lang.get('mp3_conversion_info'))
                    mp3_dir = os.path.join(selected_dir, "extracted_mp3")
                    mp3_converter = MP3Converter(output_dir, mp3_dir, num_threads)

                    # 设置MP3转换器的取消参数
                    def mp3_is_cancelled():
                        return self.task_cancelled

                    mp3_converter.cancelled = mp3_is_cancelled

                    # 运行MP3转换
                    self.run_mp3_conversion(mp3_converter)

                # 打开输出目录
                final_dir = mp3_dir if convert_to_mp3 and mp3_dir and hasattr(self,
                                                                              'mp3_result') and self.mp3_result.get(
                    "success") else output_dir

                # 使用基于平台的方法打开目录
                if not self.task_cancelled:
                    try:
                        if os.name == 'nt':
                            os.startfile(final_dir)
                        elif sys.platform == 'darwin':
                            subprocess.call(['open', final_dir])
                        else:
                            subprocess.call(['xdg-open', final_dir])

                        self.gui_logger.info(lang.get('opening_output_dir',
                                                      lang.get('mp3') if convert_to_mp3 and mp3_dir and hasattr(self,
                                                                                                                'mp3_result') and self.mp3_result.get(
                                                          "success") else lang.get('ogg')))
                    except Exception as e:
                        self.gui_logger.error(f"Failed to open directory: {str(e)}")
            else:
                self.gui_logger.warning(lang.get('no_files_processed'))

            # 更新状态栏
            self.status_bar.config(text="Ready / 就绪")
        except Exception as e:
            self.gui_logger.error(lang.get('error_occurred', str(e)))
            self.gui_logger.error(traceback.format_exc())
            self.status_bar.config(text="Error / 错误")
        finally:
            # 确保提取按钮重新启用
            self.extract_btn.configure(state='normal')
            self.active_task = None

    def run_mp3_conversion(self, mp3_converter):
        """运行MP3转换"""
        try:
            # 转换所有找到的OGG文件
            mp3_result = mp3_converter.convert_all()
            self.mp3_result = mp3_result

            # 显示转换结果
            if mp3_result["success"]:
                self.gui_logger.success(lang.get('mp3_conversion_complete'))
                self.gui_logger.info(lang.get('converted', mp3_result['converted'], mp3_result['total']))
                self.gui_logger.info(f"Skipped duplicates: {mp3_result['skipped']} files")
                self.gui_logger.info(f"Errors: {mp3_result['errors']} files")
                self.gui_logger.info(f"Total time: {mp3_result['duration']:.2f} seconds")
            else:
                self.gui_logger.error(mp3_result['error'])
        except Exception as e:
            self.gui_logger.error(lang.get('mp3_conversion_failed', str(e)))

    def show_history_frame(self):
        """显示提取历史界面"""
        # 清除右侧框架
        self.clear_right_frame()

        # 创建历史框架
        history_frame = ttk.LabelFrame(self.right_frame, text=lang.get('history_stats'))
        history_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

        # 创建可滚动内容
        content_frame = self.create_scrollable_frame(history_frame)

        # 获取历史数据
        history_size = self.download_history.get_history_size()

        # 显示历史统计信息
        ttk.Label(content_frame, text=lang.get('files_recorded', history_size)).pack(anchor=tk.W, padx=10, pady=5)

        if history_size > 0:
            history_file = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor", "extracted_history.json")
            ttk.Label(content_frame, text=lang.get('history_file_location', history_file)).pack(anchor=tk.W, padx=10,
                                                                                                pady=5)

        # 操作按钮
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)

        clear_btn = ttk.Button(buttons_frame, text=lang.get('clear_history'), command=self.clear_history)
        clear_btn.pack(side=tk.RIGHT, padx=5)

        # 显示日志框架
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 显示历史信息
        self.gui_logger.info(lang.get('history_stats'))
        self.gui_logger.info(lang.get('files_recorded', history_size))

        if history_size > 0:
            self.gui_logger.info(lang.get('history_file_location', history_file))

    def clear_history(self):
        """清除提取历史"""
        # 显示确认对话框
        result = messagebox.askquestion(
            lang.get('clear_history'),
            lang.get('confirm_clear_history'),
            icon='warning'
        )

        if result == 'yes':
            try:
                # 获取历史文件路径并创建空历史文件
                history_file = self.download_history.history_file
                with open(history_file, 'w') as f:
                    f.write("[]")

                # 显示成功消息（使用messagebox避免使用可能被销毁的日志控件）
                messagebox.showinfo("", lang.get('history_cleared'))

                # 完全重新启动UI
                self.root.after(100, lambda: self._restart_history_view(history_file))

            except Exception as e:
                messagebox.showerror("Error", f"Error clearing history: {str(e)}")
                traceback.print_exc()
        else:
            messagebox.showinfo("Cancelled", lang.get('operation_cancelled'))

    def _restart_history_view(self, history_file):
        """完全重启历史视图"""
        # 停止当前日志记录器
        if hasattr(self, 'gui_logger') and self.gui_logger:
            try:
                self.gui_logger.running = False
            except:
                pass

        # 恢复原始stdout
        sys.stdout = self.original_stdout

        # 重新创建历史对象
        self.download_history = ExtractedHistory(history_file)

        # 清除右侧内容并重新显示历史界面
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        self.show_history_frame()

    def show_language_frame(self):
        """显示语言设置界面"""
        # 清除右侧框架
        self.clear_right_frame()

        # 创建语言设置框架
        language_frame = ttk.LabelFrame(self.right_frame, text=lang.get('language_settings'))
        language_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

        # 创建可滚动内容
        content_frame = self.create_scrollable_frame(language_frame)

        # 显示当前语言
        ttk.Label(content_frame, text=lang.get('current_language', lang.get_language_name())).pack(anchor=tk.W,
                                                                                                   padx=10, pady=10)

        # 语言选择
        select_frame = ttk.Frame(content_frame)
        select_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(select_frame, text=lang.get('select_language').split(':')[0] + ':').pack(side=tk.LEFT, padx=5)

        self.lang_var = tk.StringVar()
        self.lang_var.set("2" if lang.current_language == Language.ENGLISH else "1")

        chinese_radio = ttk.Radiobutton(select_frame, text="中文", variable=self.lang_var, value="1")
        chinese_radio.pack(side=tk.LEFT, padx=20)

        english_radio = ttk.Radiobutton(select_frame, text="English", variable=self.lang_var, value="2")
        english_radio.pack(side=tk.LEFT, padx=20)

        # 操作按钮
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)

        apply_btn = ttk.Button(buttons_frame, text="Apply / 应用", command=self.apply_language)
        apply_btn.pack(side=tk.RIGHT, padx=5)

        # 显示日志框架
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def apply_language(self):
        """应用语言设置"""
        choice = self.lang_var.get()

        if choice == "1":
            lang.set_language(Language.CHINESE)

        elif choice == "2":
            lang.set_language(Language.ENGLISH)

        # 更新界面语言
        self.update_language()

        # 刷新当前界面
        self.show_language_frame()

        # 显示语言已更改消息
        self.gui_logger.success(lang.get('language_set', lang.get_language_name()))

    def show_about_frame(self):
        """显示关于界面"""
        # 清除右侧框架
        self.clear_right_frame()

        # 创建关于框架
        about_frame = ttk.LabelFrame(self.right_frame, text=lang.get('about_title'))
        about_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)

        # 创建可滚动内容
        content_frame = self.create_scrollable_frame(about_frame)

        # 创建顶部框架来显示图标和标题
        top_frame = ttk.Frame(content_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        # 加载并显示图标
        try:
            if sys.platform.startswith("win"):
                # Windows: 使用PhotoImage加载ico文件
                from PIL import Image, ImageTk
                icon = Image.open(resource_path(os.path.join(".readme", "ui-images", "Roblox-Audio-Extractor.ico")))
                app_icon = ImageTk.PhotoImage(icon)

            # 创建标签显示图标
            icon_label = ttk.Label(top_frame, image=app_icon)
            icon_label.image = app_icon  # 保持引用以防止被垃圾回收
            icon_label.pack(side=tk.LEFT, padx=10)

            # 创建标题标签
            title_label = ttk.Label(top_frame, text="Roblox Audio Extractor (Multiple Classification Methods)",
                                    font=("Arial", 16, "bold"))
            title_label.pack(side=tk.LEFT, padx=10)

        except Exception as e:
            # 如果无法加载图标，只显示标题
            title_label = ttk.Label(top_frame, text="Roblox Audio Extractor (Multiple Classification Methods)",
                                    font=("Arial", 16, "bold"))
            title_label.pack(side=tk.LEFT, padx=10)

        # 关于信息
        ttk.Label(content_frame,
                  text=lang.get('about_info'),
                  wraplength=600).pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(content_frame, text=lang.get('about_version')).pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(content_frame, text=lang.get('Creators & Contributors')).pack(anchor=tk.W, padx=10, pady=5)

        # 分隔线
        ttk.Separator(content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)


        # # 显示分类信息
        # classification_info_frame = ttk.LabelFrame(content_frame, text="Classification Methods / 分类方法")
        # classification_info_frame.pack(fill=tk.X, padx=10, pady=10)
        #
        # # 先显示按时长分类信息
        # ttk.Label(classification_info_frame, text="Duration Classification / 按时长分类:",
        #           font=("Arial", 11, "bold")).pack(anchor=tk.W, padx=5, pady=2)
        # ttk.Label(classification_info_frame,
        #           text="Ultra Short (0-5s): Sound effects, notifications / 超短 (0-5秒): 音效、通知",
        #           wraplength=600).pack(anchor=tk.W, padx=10, pady=2)
        # ttk.Label(classification_info_frame, text="Short (5-15s): Short effects, alerts / 短 (5-15秒): 短音效、通知音",
        #           wraplength=600).pack(anchor=tk.W, padx=10, pady=2)
        # ttk.Label(classification_info_frame,
        #           text="Medium (15-60s): Loop music, short BGM / 中等 (15-60秒): 循环音乐、短背景音",
        #           wraplength=600).pack(anchor=tk.W, padx=10, pady=2)
        # ttk.Label(classification_info_frame,
        #           text="Long (1-5min): Full music, long BGM / 长 (1-5分钟): 完整音乐、长背景音",
        #           wraplength=600).pack(anchor=tk.W, padx=10, pady=2)
        # ttk.Label(classification_info_frame, text="Ultra Long (5min+): Long music, voices / 超长 (5分钟+): 长音乐、语音",
        #           wraplength=600).pack(anchor=tk.W, padx=10, pady=2)
        #
        # # 再显示按大小分类信息
        # ttk.Label(classification_info_frame, text="Size Classification / 按大小分类:",
        #           font=("Arial", 11, "bold")).pack(anchor=tk.W, padx=5, pady=(10, 2))
        # ttk.Label(classification_info_frame, text="Ultra Small (0-50KB): Very small audio clips / 极小音频片段",
        #           wraplength=600).pack(anchor=tk.W, padx=10, pady=2)
        # ttk.Label(classification_info_frame, text="Small (50KB-200KB): Small audio clips / 小型音频片段",
        #           wraplength=600).pack(anchor=tk.W, padx=10, pady=2)
        # ttk.Label(classification_info_frame, text="Medium (200KB-1MB): Medium size audio / 中等大小音频",
        #           wraplength=600).pack(anchor=tk.W, padx=10, pady=2)
        # ttk.Label(classification_info_frame, text="Large (1MB-5MB): Large audio files / 大型音频文件",
        #           wraplength=600).pack(anchor=tk.W, padx=10, pady=2)
        # ttk.Label(classification_info_frame, text="Ultra Large (5MB+): Very large audio files / 极大音频文件",
        #           wraplength=600).pack(anchor=tk.W, padx=10, pady=2)


        # 分隔线
        ttk.Separator(content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)

        # 链接和许可信息
        ttk.Label(content_frame, text="GitHub: https://github.com/JustKanade/Roblox-Audio-Extractor").pack(anchor=tk.W,
                                                                                                           padx=10,
                                                                                                           pady=5)
        ttk.Label(content_frame, text="License: GNU Affero General Public License v3.0 (AGPLv3)").pack(anchor=tk.W,
                                                                                                       padx=10, pady=5)


        # 显示内存使用情况
        try:
            # 动态导入psutil (如果可用)
            try:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB

                ttk.Separator(content_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)
                ttk.Label(content_frame, text=f"Current memory usage: {memory_mb:.2f} MB").pack(anchor=tk.W, padx=10,
                                                                                                pady=5)
            except ImportError:
                pass
        except:
            pass

        # 显示日志框架
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)





def main():
    """主函数 - 程序入口点，使用 GUI 界面"""
    try:
        # 创建并运行 GUI 应用程序
        root = tk.Tk()
        # 根据操作系统设置应用程序图标
        try:
            if sys.platform.startswith("win"):  # Windows
                root.iconbitmap(resource_path(os.path.join(".readme", "ui-images", "Roblox-Audio-Extractor.ico")))
            elif sys.platform == "darwin":  # macOS
                # macOS 不支持 .ico 格式，可以使用 .icns 或其他支持的格式
                root.tk.call('wm', 'iconphoto', root._w, tk.PhotoImage(
                    file=resource_path(os.path.join(".readme", "ui-images", "Roblox-Audio-Extractor.png"))))
            else:  # Linux 或其他
                root.tk.call('wm', 'iconphoto', root._w, tk.PhotoImage(
                    file=resource_path(os.path.join(".readme", "ui-images", "Roblox-Audio-Extractor.png"))))
        except Exception as e:
            print(f"无法设置图标: {e}")

        app = RobloxAudioExtractorGUI(root)
        root.mainloop()

        return 0
    except Exception as e:
        print(f"程序出错: {e}")
        return 1
    except Exception as e:
        # 显示错误消息
        traceback.print_exc()
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        return 1


if __name__ == "__main__":
    # 初始化语言管理器
    lang = LanguageManager()

    try:
        sys.exit(main())
    except Exception as e:
        # 在终端模式下记录错误
        logger.error(f"An error occurred: {str(e)}")
        traceback.print_exc()

        # 在 GUI 模式下显示错误对话框
        try:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        except:
            pass

        input("\n> Press Enter to continue...")
        sys.exit(1)
