import os
import sys
import time
import gzip
import shutil
import random
import string
import hashlib
import getpass
import logging
import datetime
import threading
import multiprocessing
import subprocess
from typing import Dict, List, Any, Tuple, Set, Optional
from concurrent.futures import ThreadPoolExecutor
from enum import Enum, auto
from colorama import Fore, Style, init

# 初始化colorama
init()

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class Language(Enum):
    """支持的语言枚举"""
    ENGLISH = auto()
    CHINESE = auto()


class LanguageManager:
    """语言管理器，处理翻译和语言切换"""

    def __init__(self):
        # 设置可用的语言常量
        self.ENGLISH = Language.ENGLISH
        self.CHINESE = Language.CHINESE

        # 翻译字典
        self.TRANSLATIONS = {
            "title": {
                self.ENGLISH: "    Roblox-Audio-Extractor ",
                self.CHINESE: "    Roblox-Audio-Extractor "
            },
            "extract_audio": {
                self.ENGLISH: "1. Extract Audio Files",
                self.CHINESE: "1. 提取音频文件"
            },
            "view_history": {
                self.ENGLISH: "2. View Download History",
                self.CHINESE: "2. 查看下载历史"
            },
            "clear_history": {
                self.ENGLISH: "3. Clear Download History",
                self.CHINESE: "3. 清除下载历史"
            },
            "language_settings": {
                self.ENGLISH: "4. Language Settings",
                self.CHINESE: "4. 语言设置 (Language Settings)"
            },
            "about": {
                self.ENGLISH: "5. About",
                self.CHINESE: "5. 关于本项目"
            },
            "exit": {
                self.ENGLISH: "6. Exit",
                self.CHINESE: "6. 退出"
            },
            "select_operation": {
                self.ENGLISH: "Please select an operation (1-6): ",
                self.CHINESE: "请选择操作 (1-6): "
            },
            "invalid_choice": {
                self.ENGLISH: "Invalid choice, please enter a number between 1-6.",
                self.CHINESE: "无效选择，请输入1-6之间的数字。"
            },
            "thanks_bye": {
                self.ENGLISH: "Thank you for using Roblox-Audio-Extractor. Goodbye!",
                self.CHINESE: "感谢使用 Roblox-Audio-Extractor 再见！"
            },
            "press_enter": {
                self.ENGLISH: "Press Enter to continue...",
                self.CHINESE: "按回车键继续..."
            },
            "error_occurred": {
                self.ENGLISH: "An error occurred: {}",
                self.CHINESE: "发生错误：{}"
            },
            "history_stats": {
                self.ENGLISH: "=== Download History Statistics ===",
                self.CHINESE: "=== 下载历史统计 ==="
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
                self.ENGLISH: "Are you sure you want to clear all download history? (y/n): ",
                self.CHINESE: "您确定要清除所有下载历史吗？(y/n)："
            },
            "history_cleared": {
                self.ENGLISH: "Download history has been cleared.",
                self.CHINESE: "下载历史已清除。"
            },
            "operation_cancelled": {
                self.ENGLISH: "Operation cancelled.",
                self.CHINESE: "操作已取消。"
            },
            "default_dir": {
                self.ENGLISH: "Default directory: {}",
                self.CHINESE: "默认目录：{}"
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
            "info_size_categories": {
                self.ENGLISH: "• Files will be organized by size in different folders",
                self.CHINESE: "• 文件将按大小分类到不同文件夹中"
            },
            "info_mp3_conversion": {
                self.ENGLISH: "• You can convert OGG files to MP3 after extraction",
                self.CHINESE: "• 提取后可以将OGG文件转换为MP3"
            },
            "info_skip_downloaded": {
                self.ENGLISH: "• Previously downloaded files will be skipped",
                self.CHINESE: "• 将跳过之前下载过的文件"
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
            "categorizing_files": {
                self.ENGLISH: "Categorizing {} files by size...",
                self.CHINESE: "正在按大小对 {} 个文件进行分类..."
            },
            "category_dir_info": {
                self.ENGLISH: "{} files ({}): {}",
                self.CHINESE: "{} 文件 ({}): {}"
            },
            "readme_title": {
                self.ENGLISH: "Roblox Audio Files - Category Information",
                self.CHINESE: "Roblox 音频文件 - 类别信息"
            },
            "readme_category_tiny": {
                self.ENGLISH: "- tiny: Very short sounds (0-10KB), likely sound effects",
                self.CHINESE: "- tiny: 非常短的声音 (0-10KB)，可能是音效"
            },
            "readme_category_small": {
                self.ENGLISH: "- small: Short sounds (10-100KB), brief audio clips",
                self.CHINESE: "- small: 短声音 (10-100KB)，简短的音频片段"
            },
            "readme_category_medium": {
                self.ENGLISH: "- medium: Medium-length sounds (100KB-1MB), longer clips",
                self.CHINESE: "- medium: 中等长度声音 (100KB-1MB)，较长的片段"
            },
            "readme_category_large": {
                self.ENGLISH: "- large: Long audio (1-5MB), full music tracks",
                self.CHINESE: "- large: 较长音频 (1-5MB)，完整音乐曲目"
            },
            "readme_category_huge": {
                self.ENGLISH: "- huge: Very long audio (5MB+), high-quality music or long tracks",
                self.CHINESE: "- huge: 非常长的音频 (5MB+)，高质量音乐或长曲目"
            },
            "readme_note": {
                self.ENGLISH: "\nNote: Files in these folders are all OGG format. You can use any media player that supports OGG format to play them.",
                self.CHINESE: "\n注意：这些文件夹中的文件都是OGG格式。您可以使用任何支持OGG格式的媒体播放器来播放它们。"
            },
            "readme_date": {
                self.ENGLISH: "\nExtracted on:",
                self.CHINESE: "\n提取日期："
            },
            "ffmpeg_not_installed": {
                self.ENGLISH: "FFmpeg is not installed. Please install FFmpeg to convert files.",
                self.CHINESE: "未安装FFmpeg。请安装FFmpeg以转换文件。"
            },
            "no_ogg_files": {
                self.ENGLISH: "No OGG files found to convert",
                self.CHINESE: "未找到要转换的OGG文件"
            },
            "mp3_conversion": {
                self.ENGLISH: "Converting {} OGG files to MP3...",
                self.CHINESE: "正在将 {} 个OGG文件转换为MP3..."
            },
            "mp3_conversion_info": {
                self.ENGLISH: "MP3 Conversion Information -",
                self.CHINESE: "MP3转换信息 -"
            },
            "mp3_converted_count": {
                self.ENGLISH: "Successfully converted: {} of {} files",
                self.CHINESE: "成功转换：{} / {} 个文件"
            },
            "mp3_skipped_count": {
                self.ENGLISH: "Skipped duplicates: {} files",
                self.CHINESE: "跳过重复：{} 个文件"
            },
            "mp3_failed_count": {
                self.ENGLISH: "Failed to convert: {} files",
                self.CHINESE: "转换失败：{} 个文件"
            },
            "mp3_total_time": {
                self.ENGLISH: "Total conversion time: {:.2f} seconds",
                self.CHINESE: "总转换时间：{:.2f} 秒"
            },
            "mp3_directory_note": {
                self.ENGLISH: "MP3 files are organized in the same structure as the original OGG files",
                self.CHINESE: "MP3文件按照与原始OGG文件相同的结构组织"
            },
            "mp3_rename_note": {
                self.ENGLISH: "Files are named with a timestamp to avoid conflicts",
                self.CHINESE: "文件使用时间戳命名以避免冲突"
            },
            "mp3_filename_format": {
                self.ENGLISH: "File format: original_name_YYYYMMDD_HHMMSS_xxxx.mp3",
                self.CHINESE: "文件格式：原文件名_YYYYMMDD_HHMMSS_xxxx.mp3"
            },
            "ogg": {
                self.ENGLISH: "OGG",
                self.CHINESE: "OGG"
            },
            "mp3": {
                self.ENGLISH: "MP3",
                self.CHINESE: "MP3"
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
                self.CHINESE: "关于 Roblox 音频提取器"
            },
            "about_description": {
                self.ENGLISH: "This is an open-source tool for extracting audio files from Roblox cache and converting them to MP3.",
                self.CHINESE: "这是一个用于从Roblox缓存中提取音频文件并转换为MP3的开源工具。"
            },
            "about_version": {
                self.ENGLISH: "Version: 0.13",
                self.CHINESE: "版本: 0.13"
            },
            "about_author": {
                self.ENGLISH: "Author: JustKanade",
                self.CHINESE: "作者: JustKanade"
            },
            "about_github": {
                self.ENGLISH: "GitHub: https://github.com/JustKanade/Roblox-Audio-Extractor",
                self.CHINESE: "GitHub: https://github.com/JustKanade/Roblox-Audio-Extractor"
            },
            "about_license": {
                self.ENGLISH: "License: GNU Affero General Public License v3.0 (AGPLv3)",
                self.CHINESE: "许可: GNU Affero General Public License v3.0 (AGPLv3)"
            },
            "about_contribution": {
                self.ENGLISH: "Feel free to submit issues and contribute on GitHub!",
                self.CHINESE: "欢迎在GitHub上提交问题和贡献代码！"
            },
        }

        # 设置当前语言
        self.current_language = self.detect_system_language()

    def detect_system_language(self) -> Language:
        """
        检测系统语言并返回相应的语言枚举

        返回:
            Language: 检测到的语言枚举
        """
        try:
            import locale
            system_lang = locale.getdefaultlocale()[0].lower()
            if system_lang and ('zh_' in system_lang or 'cn' in system_lang):
                return self.CHINESE
            return self.ENGLISH
        except:
            return self.ENGLISH

    def get(self, key: str, *args) -> str:
        """
        获取指定键的翻译

        参数:
            key: 翻译键
            *args: 格式化参数

        返回:
            str: 翻译后的字符串
        """
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

        return message

    def set_language(self, language: Language) -> None:
        """
        设置当前语言

        参数:
            language: 要设置的语言枚举
        """
        self.current_language = language

    def get_language_name(self) -> str:
        """
        获取当前语言的名称

        返回:
            str: 语言名称
        """
        if self.current_language == self.CHINESE:
            return "中文"
        else:
            return "English"


# 初始化语言管理器
lang = LanguageManager()


class DownloadHistory:
    """管理下载历史，避免重复处理文件"""

    def __init__(self, history_file: str):
        """
        初始化下载历史

        参数:
            history_file: JSON历史文件的路径
        """
        self.history_file = history_file
        self.file_hashes: Set[str] = set()
        self.load_history()

    def load_history(self) -> None:
        """从JSON文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                import json
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.file_hashes = set(data)
                    elif isinstance(data, dict) and 'hashes' in data:
                        self.file_hashes = set(data['hashes'])
        except Exception as e:
            logger.error(f"Error loading history: {str(e)}")
            self.file_hashes = set()

    def save_history(self) -> None:
        """将历史记录保存到JSON文件"""
        try:
            import json
            with open(self.history_file, 'w') as f:
                json.dump(list(self.file_hashes), f)
        except Exception as e:
            logger.error(f"Error saving history: {str(e)}")

    def add_hash(self, file_hash: str) -> None:
        """添加文件哈希到历史记录"""
        self.file_hashes.add(file_hash)

    def is_processed(self, file_hash: str) -> bool:
        """检查文件是否已处理"""
        return file_hash in self.file_hashes

    def clear_history(self) -> None:
        """清除所有下载历史"""
        self.file_hashes = set()
        self.save_history()

    def get_history_size(self) -> int:
        """获取历史记录中的文件数量"""
        return len(self.file_hashes)


class ContentHashCache:
    """缓存文件内容哈希以检测重复"""

    def __init__(self):
        """初始化哈希缓存"""
        self.hashes: Set[str] = set()
        self.lock = threading.Lock()

    def is_duplicate(self, content_hash: str) -> bool:
        """
        检查内容哈希是否重复

        参数:
            content_hash: 文件内容的MD5哈希

        返回:
            bool: 如果文件是重复的则为True，否则为False
        """
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

    def increment(self, stat_key: str, amount: int = 1) -> None:
        """
        增加特定统计计数

        参数:
            stat_key: 要增加的统计键
            amount: 要增加的数量
        """
        with self.lock:
            if stat_key in self.stats:
                self.stats[stat_key] += amount
                self.stats['last_update'] = time.time()
            else:
                self.stats[stat_key] = amount

    def get(self, stat_key: str) -> int:
        """
        获取特定统计计数

        参数:
            stat_key: 获取的统计键

        返回:
            int: 当前计数
        """
        with self.lock:
            return self.stats.get(stat_key, 0)

    def get_all(self) -> Dict[str, int]:
        """
        获取所有统计数据

        返回:
            Dict[str, int]: 包含所有统计数据的字典
        """
        with self.lock:
            return self.stats.copy()


class ProgressTracker:
    """跟踪和显示处理进度"""

    def __init__(self, total_items: int, stats: ProcessingStats, stat_keys: List[str]):
        """
        初始化进度跟踪器

        参数:
            total_items: 要处理的项目总数
            stats: 用于跟踪统计信息的对象
            stat_keys: 要考虑的统计键列表
        """
        self.total_items = total_items
        self.stats = stats
        self.stat_keys = stat_keys
        self.running = False
        self.thread = None

    def start(self) -> None:
        """启动进度跟踪线程"""
        self.running = True
        self.thread = threading.Thread(target=self._progress_thread)
        self.thread.daemon = True
        self.thread.start()

    def stop(self) -> None:
        """停止进度跟踪线程"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        sys.stdout.write("\n")
        sys.stdout.flush()

    def _progress_thread(self) -> None:
        """线程函数以更新进度显示"""
        last_count = 0
        last_time = time.time()

        while self.running:
            time.sleep(0.5)  # 更新频率

            # 汇总已处理项目
            current_time = time.time()
            stats_dict = self.stats.get_all()
            total_processed = sum(stats_dict.get(key, 0) for key in self.stat_keys)

            # 计算速度（每秒项目数）
            elapsed = current_time - last_time
            if elapsed >= 0.5:  # 至少0.5秒以避免大幅度波动
                processed_since_last = total_processed - last_count
                items_per_sec = processed_since_last / elapsed
            else:
                items_per_sec = 0

            # 计算进度百分比
            progress_percent = (total_processed / self.total_items) * 100 if self.total_items > 0 else 0
            progress_percent = min(100, progress_percent)  # 最大100%

            # 估计剩余时间
            if items_per_sec > 0 and total_processed < self.total_items:
                remaining_items = self.total_items - total_processed
                remaining_time = remaining_items / items_per_sec
                remaining_str = f"{int(remaining_time // 60)}m {int(remaining_time % 60)}s"
            else:
                remaining_str = "..."

            # 显示进度
            sys.stdout.write(
                f"\r{progress_percent:.1f}% ({total_processed}/{self.total_items}) | "
                f"{items_per_sec:.1f} files/s | ETA: {remaining_str}"
            )
            sys.stdout.flush()

            # 更新上一次的计数和时间
            last_count = total_processed
            last_time = current_time

            # 如果所有项目都已处理完毕，则退出
            if total_processed >= self.total_items:
                break


class RobloxAudioExtractor:
    """从Roblox临时文件中提取音频的主类"""

    def __init__(self, base_dir: str, num_threads: int = None, keyword: str = "oggs",
                 download_history: DownloadHistory = None):
        """
        初始化提取器

        参数:
            base_dir: 要处理的目录
            num_threads: 要使用的线程数（默认：CPU数量 * 2）
            keyword: 用于识别音频文件的关键字
            download_history: 下载历史记录对象
        """
        self.base_dir = os.path.abspath(base_dir)
        self.num_threads = num_threads or min(32, multiprocessing.cpu_count() * 2)
        self.keyword = keyword
        self.download_history = download_history

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

        # 按大小分类文件
        self.size_categories = {
            "tiny_0-10KB_very_short": (0, 10 * 1024),  # 0-10KB
            "small_10-100KB_short": (10 * 1024, 100 * 1024),  # 10-100KB
            "medium_100KB-1MB_medium": (100 * 1024, 1024 * 1024),  # 100KB-1MB
            "large_1-5MB_long": (1024 * 1024, 5 * 1024 * 1024),  # 1-5MB
            "huge_5MB+_very_long": (5 * 1024 * 1024, float('inf'))  # 5MB+
        }

        # 为每个类别创建目录
        self.category_dirs = {}
        for category in self.size_categories:
            path = os.path.join(self.output_dir, category)
            os.makedirs(path, exist_ok=True)
            self.category_dirs[category] = path

    def process_files(self) -> Dict[str, Any]:
        """
        处理目录中的文件

        返回:
            Dict[str, Any]: 包含处理结果的字典
        """
        # 扫描文件并记录开始时间
        start_time = time.time()
        logger.info(f"{Fore.CYAN}{lang.get('scanning_files')}{Fore.RESET}")

        files_to_process = []
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if self.keyword not in file and not file.endswith('.ogg'):
                    # 获取完整路径
                    file_path = os.path.join(root, file)

                    # 跳过输出目录中的文件
                    if self.output_dir in file_path:
                        continue

                    # 文件至少有10字节
                    if os.path.getsize(file_path) >= 10:
                        files_to_process.append(file_path)

        scan_duration = time.time() - start_time
        logger.info(f"{Fore.GREEN}{lang.get('found_files', len(files_to_process), scan_duration)}{Fore.RESET}")

        if not files_to_process:
            logger.warning(f"{Fore.YELLOW}{lang.get('no_files_found')}{Fore.RESET}")
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

        # 处理文件
        processing_start = time.time()
        logger.info(f"{Fore.CYAN}{lang.get('processing_with_threads', self.num_threads)}{Fore.RESET}")

        # 启动进度跟踪
        progress_tracker = ProgressTracker(
            len(files_to_process),
            self.stats,
            ['processed_files', 'duplicate_files', 'already_processed', 'error_files']
        )
        progress_tracker.start()

        # 处理文件
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            results = list(executor.map(self.process_file, files_to_process))

        # 停止进度跟踪
        progress_tracker.stop()

        # 如果下载历史记录可用，保存它
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
        """
        处理单个文件并提取音频

        参数:
            file_path: 要处理的文件路径

        返回:
            bool: 如果处理成功则为True，否则为False
        """
        try:
            # 计算文件哈希
            file_hash = self.get_file_hash(file_path)

            # 如果文件已经处理过了，则跳过
            if self.download_history and self.download_history.is_processed(file_hash):
                self.stats.increment('already_processed')
                return False

            # 尝试读取文件内容
            file_content = self.extract_ogg_content(file_path)
            if not file_content:
                return False

            # 确保是合法的OGG文件头
            if not self.is_valid_ogg(file_content):
                return False

            # 计算内容哈希以检测重复
            content_hash = hashlib.md5(file_content).hexdigest()
            if self.hash_cache.is_duplicate(content_hash):
                self.stats.increment('duplicate_files')
                return False

            # 保存文件
            output_path = self.save_ogg_file(file_path, file_content)
            if output_path:
                # 成功保存文件，增加处理计数
                self.stats.increment('processed_files')

                # 如果可用，将哈希添加到下载历史记录
                if self.download_history:
                    self.download_history.add_hash(file_hash)

                return True

            return False

        except Exception as e:
            # 增加错误计数
            self.stats.increment('error_files')
            # 将错误写入日志
            self.log_error(file_path, str(e))
            return False

    def extract_ogg_content(self, file_path: str) -> Optional[bytes]:
        """
        提取文件中的OGG内容

        参数:
            file_path: 要处理的文件路径

        返回:
            Optional[bytes]: 如果找到则为OGG文件内容，否则为None
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            # 寻找OGG标头
            ogg_start = content.find(b'OggS')
            if ogg_start >= 0:
                return content[ogg_start:]
            else:
                # 尝试以gzip解压，有时候Roblox会压缩文件
                try:
                    decompressed = gzip.decompress(content)
                    ogg_start = decompressed.find(b'OggS')
                    if ogg_start >= 0:
                        return decompressed[ogg_start:]
                except Exception:
                    pass
            return None
        except Exception:
            return None

    def is_valid_ogg(self, content: bytes) -> bool:
        """
        检查内容是否为有效的OGG文件

        参数:
            content: 要检查的文件内容

        返回:
            bool: 如果内容是有效的OGG文件则为True，否则为False
        """
        return content[:4] == b'OggS'

    def get_size_category(self, file_size: int) -> str:
        """
        根据文件大小确定类别

        参数:
            file_size: 文件大小（字节）

        返回:
            str: 大小类别名称
        """
        for category, (min_size, max_size) in self.size_categories.items():
            if min_size <= file_size < max_size:
                return category
        # 默认类别：如果没有匹配项
        return next(iter(self.size_categories.keys()))

    def save_ogg_file(self, source_path: str, content: bytes) -> Optional[str]:
        """
        保存提取的OGG文件

        参数:
            source_path: 源文件路径
            content: 文件内容

        返回:
            Optional[str]: 成功时保存的文件路径，否则为None
        """
        try:
            # 获取文件大小并确定类别
            file_size = len(content)
            category = self.get_size_category(file_size)
            output_dir = self.category_dirs[category]

            # 生成唯一的文件名
            base_name = os.path.basename(source_path)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            output_name = f"{base_name}_{timestamp}_{random_suffix}.ogg"
            output_path = os.path.join(output_dir, output_name)

            # 保存文件
            with open(output_path, 'wb') as f:
                f.write(content)

            return output_path
        except Exception as e:
            self.log_error(source_path, f"Failed to save file: {str(e)}")
            return None

    def get_file_hash(self, file_path: str) -> str:
        """
        计算文件的哈希值

        参数:
            file_path: 文件路径

        返回:
            str: 文件的MD5哈希
        """
        file_hash = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    file_hash.update(chunk)
            return file_hash.hexdigest()
        except Exception:
            # 如果无法读取文件，使用文件路径和大小
            try:
                file_size = os.path.getsize(file_path)
                file_hash.update(f"{file_path}_{file_size}".encode())
                return file_hash.hexdigest()
            except Exception:
                # 最后的选择：只使用文件路径
                file_hash.update(file_path.encode())
                return file_hash.hexdigest()

    def log_error(self, file_path: str, error_message: str) -> None:
        """
        记录处理错误

        参数:
            file_path: 导致错误的文件
            error_message: 错误消息
        """
        try:
            log_file = os.path.join(self.logs_dir, "extraction_errors.log")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.file_lock:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp}] {file_path}: {error_message}\n")
        except Exception:
            pass  # 如果日志记录失败，则没有太大影响

    def create_readme(self) -> None:
        """创建README文件解释音频类别"""
        try:
            # 创建自述文件，解释不同的文件大小类别
            readme_path = os.path.join(self.output_dir, "README.txt")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"{lang.get('readme_title')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"{lang.get('readme_category_tiny')}\n")
                f.write(f"{lang.get('readme_category_small')}\n")
                f.write(f"{lang.get('readme_category_medium')}\n")
                f.write(f"{lang.get('readme_category_large')}\n")
                f.write(f"{lang.get('readme_category_huge')}\n")
                f.write(f"{lang.get('readme_note')}\n")
                f.write(f"{lang.get('readme_date')} {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception:
            pass  # 非关键操作


class MP3Converter:
    """将OGG文件转换为MP3"""

    def __init__(self, input_dir: str, output_dir: str, num_threads: int = None):
        """
        初始化MP3转换器

        参数:
            input_dir: 包含OGG文件的输入目录
            output_dir: 输出目录
            num_threads: 转换线程数
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.num_threads = num_threads or min(16, multiprocessing.cpu_count())
        self.stats = ProcessingStats()
        self.file_lock = threading.Lock()

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

    def convert_all(self) -> Dict[str, Any]:
        """
        转换所有找到的OGG文件

        返回:
            Dict[str, Any]: 转换结果字典
        """
        # 检查ffmpeg是否可用
        if not self._is_ffmpeg_available():
            return {
                "success": False,
                "error": lang.get("ffmpeg_not_installed")
            }

        # 查找所有的OGG文件
        ogg_files = []
        for root, _, files in os.walk(self.input_dir):
            for file in files:
                if file.endswith('.ogg'):
                    ogg_files.append(os.path.join(root, file))

        if not ogg_files:
            return {
                "success": False,
                "error": lang.get("no_ogg_files")
            }

        # 创建相应的输出目录结构
        self._create_output_structure()

        # 重置统计
        self.stats.reset()

        # 启动进度跟踪
        logger.info(f"{Fore.CYAN}{lang.get('mp3_conversion', len(ogg_files))}{Fore.RESET}")
        progress_tracker = ProgressTracker(
            len(ogg_files),
            self.stats,
            ['mp3_converted', 'mp3_skipped', 'mp3_errors']
        )
        progress_tracker.start()

        # 开始转换
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            results = list(executor.map(self.convert_file, ogg_files))

        # 停止进度跟踪
        progress_tracker.stop()

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
        """
        转换单个OGG文件为MP3

        参数:
            ogg_path: OGG文件的路径

        返回:
            bool: 成功时为True，否则为False
        """
        try:
            # 获取相对输入路径以构建输出路径
            rel_path = os.path.relpath(ogg_path, self.input_dir)
            rel_dir = os.path.dirname(rel_path)
            basename = os.path.basename(ogg_path)
            basename_noext = os.path.splitext(basename)[0]

            # 为输出文件创建目录
            output_dir = os.path.join(self.output_dir, rel_dir)
            os.makedirs(output_dir, exist_ok=True)

            # 创建MP3文件名，保留原始格式
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            mp3_filename = f"{basename_noext}_{timestamp}_{random_suffix}.mp3"
            mp3_path = os.path.join(output_dir, mp3_filename)

            # 使用ffmpeg转换文件
            try:
                result = subprocess.run(
                    ["ffmpeg", "-i", ogg_path, "-codec:a", "libmp3lame", "-qscale:a", "1", mp3_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
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

    def _is_ffmpeg_available(self) -> bool:
        """
        检查ffmpeg是否可用

        返回:
            bool: 如果ffmpeg可用则为True，否则为False
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except Exception:
            return False

    def _create_output_structure(self) -> None:
        """创建与输入目录相对应的输出目录结构"""
        for root, dirs, _ in os.walk(self.input_dir):
            rel_path = os.path.relpath(root, self.input_dir)
            if rel_path != '.':
                os.makedirs(os.path.join(self.output_dir, rel_path), exist_ok=True)

    def _log_error(self, file_path: str, error_message: str) -> None:
        """
        记录转换错误

        参数:
            file_path: 导致错误的文件
            error_message: 错误消息
        """
        try:
            log_dir = os.path.join(self.output_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "conversion_errors.log")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.file_lock:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp}] {file_path}: {error_message}\n")
        except Exception:
            pass  # 如果日志记录失败，则没有太大影响


def open_directory(path: str) -> bool:
    """
    在文件资源管理器/Finder中打开目录

    参数:
        path: 要打开的目录路径

    返回:
        bool: 如果成功则为True，否则为False
    """
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


def language_settings():
    """显示语言设置菜单并处理语言更改"""
    global lang

    print(f"\n{Style.BRIGHT}{Fore.CYAN}{lang.get('current_language', lang.get_language_name())}{Style.RESET_ALL}")
    choice = input(f"{Style.BRIGHT}{lang.get('select_language')}{Style.RESET_ALL}")

    if choice == '1':
        lang.set_language(Language.CHINESE)
        print(f"{Fore.GREEN}{lang.get('language_set', lang.get_language_name())}{Fore.RESET}")
    elif choice == '2':
        lang.set_language(Language.ENGLISH)
        print(f"{Fore.GREEN}{lang.get('language_set', lang.get_language_name())}{Fore.RESET}")
    else:
        print(f"{Fore.RED}{lang.get('invalid_choice')}{Fore.RESET}")

    input(f"\n{Fore.CYAN}{lang.get('press_enter')}{Fore.RESET}")


def show_about_info():
    """显示关于信息"""
    print(f"\n{Style.BRIGHT}{Fore.CYAN}{lang.get('about_title')}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{lang.get('about_description')}{Fore.RESET}")
    print(f"{Fore.YELLOW}{lang.get('about_version')}{Fore.RESET}")
    print(f"{Fore.CYAN}{lang.get('about_author')}{Fore.RESET}")
    print(f"{Fore.MAGENTA}{lang.get('about_github')}{Fore.RESET}")
    print(f"{Fore.BLUE}{lang.get('about_license')}{Fore.RESET}")
    print(f"{Fore.GREEN}{lang.get('about_contribution')}{Fore.RESET}")
    input(f"\n{Fore.CYAN}{lang.get('press_enter')}{Fore.RESET}")


def main():
    try:
        # 获取默认目录
        current_username = getpass.getuser()
        default_dir = os.path.join("C:", os.sep, "Users", current_username, "AppData", "Local", "Temp", "Roblox",
                                   "http")

        # 设置下载历史记录文件
        app_data_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        os.makedirs(app_data_dir, exist_ok=True)
        history_file = os.path.join(app_data_dir, "download_history.json")

        # 初始化下载历史
        download_history = DownloadHistory(history_file)

        # 显示主菜单
        while True:
            print(f"\n{Style.BRIGHT}{Fore.CYAN}{lang.get('title')}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{lang.get('extract_audio')}{Fore.RESET}")
            print(f"{Fore.YELLOW}{lang.get('view_history')}{Fore.RESET}")
            print(f"{Fore.RED}{lang.get('clear_history')}{Fore.RESET}")
            print(f"{Fore.BLUE}{lang.get('language_settings')}{Fore.RESET}")
            print(f"{Fore.CYAN}{lang.get('about')}{Fore.RESET}")
            print(f"{Fore.MAGENTA}{lang.get('exit')}{Fore.RESET}")

            choice = input(f"\n{Style.BRIGHT}{lang.get('select_operation')}{Style.RESET_ALL}").strip()

            if choice == '6':
                print(f"{Fore.CYAN}{lang.get('thanks_bye')}{Fore.RESET}")
                break

            elif choice == '5':
                # 显示关于信息
                show_about_info()
                continue

            elif choice == '4':
                # 语言设置
                language_settings()
                continue

            elif choice == '2':
                # 显示下载历史统计
                history_size = download_history.get_history_size()
                print(f"\n{Style.BRIGHT}{Fore.CYAN}{lang.get('history_stats')}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}{lang.get('files_recorded', history_size)}{Fore.RESET}")
                if history_size > 0:
                    print(f"{Fore.YELLOW}{lang.get('history_file_location', history_file)}{Fore.RESET}")
                input(f"\n{Fore.CYAN}{lang.get('press_enter')}{Fore.RESET}")
                continue

            elif choice == '3':
                # 清除下载历史
                confirm = input(f"\n{Fore.RED}{lang.get('confirm_clear_history')}{Fore.RESET}").strip().lower()
                if confirm == 'y':
                    download_history.clear_history()
                    print(f"{Fore.GREEN}{lang.get('history_cleared')}{Fore.RESET}")
                else:
                    print(f"{Fore.YELLOW}{lang.get('operation_cancelled')}{Fore.RESET}")
                input(f"\n{Fore.CYAN}{lang.get('press_enter')}{Fore.RESET}")
                continue

            elif choice == '1':
                # 从用户获取目录
                print(f"\n{Fore.CYAN}{lang.get('default_dir', default_dir)}{Fore.RESET}")
                custom_dir = input(f"{Fore.YELLOW}{lang.get('input_dir')}{Fore.RESET}")
                roblox_http_dir = custom_dir.strip() if custom_dir.strip() else default_dir

                # 如果目录不存在，则创建
                if not os.path.exists(roblox_http_dir):
                    logger.warning(lang.get("dir_not_exist", roblox_http_dir))
                    create_dir = input(f"{Fore.YELLOW}{lang.get('create_dir_prompt')}{Fore.RESET}")
                    if create_dir.lower() == 'y':
                        try:
                            os.makedirs(roblox_http_dir, exist_ok=True)
                            logger.info(lang.get("dir_created", roblox_http_dir))
                        except Exception as e:
                            logger.error(lang.get("dir_create_failed", str(e)))
                            input(f"\n{Fore.CYAN}{lang.get('press_enter')}{Fore.RESET}")
                            continue
                    else:
                        logger.info(lang.get("operation_cancelled"))
                        input(f"\n{Fore.CYAN}{lang.get('press_enter')}{Fore.RESET}")
                        continue

                # 打印处理信息
                print(f"\n{Style.BRIGHT}{Fore.CYAN}{lang.get('processing_info')}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}{lang.get('info_size_categories')}{Fore.RESET}")
                print(f"{Fore.GREEN}{lang.get('info_mp3_conversion')}{Fore.RESET}")
                print(f"{Fore.GREEN}{lang.get('info_skip_downloaded')}{Fore.RESET}")

                # 获取线程数
                try:
                    default_threads = min(32, multiprocessing.cpu_count() * 2)
                    thread_input = input(f"\n{Fore.YELLOW}{lang.get('threads_prompt', default_threads)}{Fore.RESET}")

                    if thread_input.strip():
                        num_threads = int(thread_input)
                        if num_threads < 1:
                            raise ValueError(lang.get("threads_min_error"))
                        if num_threads > 64:
                            logger.warning(lang.get("threads_high_warning"))
                            confirm = input(f"{Fore.RED}{lang.get('confirm_high_threads')}{Fore.RESET}")
                            if confirm.lower() != 'y':
                                num_threads = default_threads
                                logger.info(lang.get("threads_adjusted", num_threads))
                    else:
                        num_threads = default_threads
                except ValueError:
                    logger.warning(lang.get("input_invalid"))
                    num_threads = default_threads

                # 初始化并运行提取器
                start_time = time.time()
                extractor = RobloxAudioExtractor(roblox_http_dir, num_threads, "oggs", download_history)
                extraction_result = extractor.process_files()

                # 打印提取结果
                output_dir = extraction_result["output_dir"]
                if extraction_result["processed"] > 0:
                    logger.info(f"\n{Fore.GREEN}{lang.get('extraction_complete')}{Fore.RESET}")
                    logger.info(f"{Fore.CYAN}{lang.get('processed', extraction_result['processed'])}{Fore.RESET}")
                    logger.info(f"{Fore.YELLOW}{lang.get('skipped_duplicates', extraction_result['duplicates'])}{Fore.RESET}")
                    logger.info(f"{Fore.YELLOW}{lang.get('skipped_already_processed', extraction_result['already_processed'])}{Fore.RESET}")
                    logger.info(f"{Fore.RED}{lang.get('errors', extraction_result['errors'])}{Fore.RESET}")
                    logger.info(f"{Fore.CYAN}{lang.get('time_spent', extraction_result['duration'])}{Fore.RESET}")
                    logger.info(f"{Fore.CYAN}{lang.get('files_per_sec', extraction_result['files_per_second'])}{Fore.RESET}")
                    logger.info(f"{Fore.GREEN}{lang.get('output_dir', output_dir)}{Fore.RESET}")

                    # 询问用户是否要转换为MP3
                    mp3_dir = None
                    convert_to_mp3 = input(f"\n{Style.BRIGHT}{Fore.YELLOW}{lang.get('convert_to_mp3_prompt')}{Style.RESET_ALL}").strip().lower()

                    if convert_to_mp3 == 'y':
                        mp3_dir = os.path.join(roblox_http_dir, "extracted_mp3")
                        mp3_converter = MP3Converter(output_dir, mp3_dir, num_threads)
                        mp3_result = mp3_converter.convert_all()

                        if mp3_result["success"]:
                            logger.info(f"\n{Fore.GREEN}{lang.get('mp3_conversion_complete')}{Fore.RESET}")
                            logger.info(f"{Fore.CYAN}{lang.get('mp3_conversion_info')}{Fore.RESET}")
                            logger.info(f"{Fore.GREEN}{lang.get('converted', mp3_result['converted'], mp3_result['total'])}{Fore.RESET}")
                            logger.info(f"{Fore.YELLOW}{lang.get('mp3_skipped_count', mp3_result['skipped'])}{Fore.RESET}")
                            logger.info(f"{Fore.RED}{lang.get('mp3_failed_count', mp3_result['errors'])}{Fore.RESET}")
                            logger.info(f"{Fore.CYAN}{lang.get('mp3_total_time', mp3_result['duration'])}{Fore.RESET}")
                            logger.info(f"\n{Fore.MAGENTA}{lang.get('mp3_directory_note')}{Fore.RESET}")
                            logger.info(f"{Fore.MAGENTA}{lang.get('mp3_rename_note')}{Fore.RESET}")
                            logger.info(f"{Fore.MAGENTA}{lang.get('mp3_filename_format')}{Fore.RESET}")
                        else:
                            logger.error(f"\n{Fore.RED}{mp3_result['error']}{Fore.RESET}")

                    # 打开输出目录
                    output_type = lang.get('mp3') if convert_to_mp3 == 'y' and mp3_dir and mp3_result.get("success") else lang.get('ogg')
                    final_dir = mp3_dir if convert_to_mp3 == 'y' and mp3_dir and mp3_result.get("success") else output_dir
                    logger.info(f"\n{Fore.CYAN}{lang.get('opening_output_dir', output_type)}{Fore.RESET}")
                    if not open_directory(final_dir):
                        logger.warning(f"{Fore.YELLOW}{lang.get('manual_navigate', final_dir)}{Fore.RESET}")

                else:
                    logger.warning(f"\n{Fore.YELLOW}{lang.get('no_files_processed')}{Fore.RESET}")

                # 打印总耗时
                total_time = time.time() - start_time
                logger.info(f"\n{Fore.CYAN}{lang.get('total_runtime', total_time)}{Fore.RESET}")
                input(f"\n{Fore.CYAN}{lang.get('press_enter')}{Fore.RESET}")

            else:
                print(f"{Fore.RED}{lang.get('invalid_choice')}{Fore.RESET}")

        return 0

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}{lang.get('canceled_by_user')}{Fore.RESET}")
        return 1
    except Exception as e:
        print(f"\n{Fore.RED}{lang.get('error_occurred', str(e))}{Fore.RESET}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        logger.error(f"{Fore.RED}{lang.get('error_occurred', str(e))}{Fore.RESET}")
        input(f"\n{Fore.CYAN}{lang.get('press_enter')}{Fore.RESET}")
        sys.exit(1)