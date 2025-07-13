#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频提取器模块 - 提供从Roblox缓存中提取音频的功能
Audio Extractor Module - Provides functionality for extracting audio from Roblox cache
"""

import os
import sys
import time
import json
import hashlib
import logging
import threading
import queue
import datetime
import traceback
import multiprocessing
from typing import Dict, List, Any, Set, Optional
from enum import Enum, auto

# 统一的日志设置
logger = logging.getLogger(__name__)

# 分类方法枚举
class ClassificationMethod(Enum):
    """音频分类方法枚举"""
    DURATION = auto()  # 按时长分类
    SIZE = auto()  # 按大小分类


class ExtractedHistory:
    """管理提取历史，避免重复处理文件"""

    def __init__(self, history_file: str):
        """初始化提取历史"""
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

    def __init__(self, base_dir: str, num_threads: int = 1, keywords: Optional[List[str]] = None,
                 download_history: Optional[ExtractedHistory] = None,
                 classification_method: ClassificationMethod = ClassificationMethod.DURATION,
                 custom_output_dir: Optional[str] = None):
        """初始化提取器"""
        self.base_dir = os.path.abspath(base_dir)
        self.num_threads = num_threads or min(32, multiprocessing.cpu_count() * 2)
        self.keywords = keywords or ["oggs", "ID3"]  # 默认同时搜索"oggs"和"ID3"
        self.download_history = download_history
        self.classification_method = classification_method
        self.cancelled = False
        self._cancel_check_fn = None  # 用于存储外部取消检查函数

        # 初始化库相关属性
        self.gzip = None
        self.shutil = None
        self.random = None
        self.string = None
        self.subprocess = None
        self._libs_imported = False
        
        # 导入所需库
        self._import_libs()

        # 输出目录
        if custom_output_dir and os.path.isdir(custom_output_dir):
            # 使用自定义输出路径
            self.output_dir = os.path.abspath(custom_output_dir)
        else:
            # 使用默认输出路径
            self.output_dir = os.path.join(self.base_dir, "extracted")
        
        # 创建Audio总文件夹
        self.audio_dir = os.path.join(self.output_dir, "Audio")
        self.logs_dir = os.path.join(self.output_dir, "logs")

        # 创建日志和音频总文件夹
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        # 初始化处理对象
        self.stats = ProcessingStats()
        self.hash_cache = ContentHashCache()
        self.file_lock = threading.Lock()

        # 文件计数器，使用原子操作而不是锁
        self.processed_count = 0

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
            path = os.path.join(self.audio_dir, category)
            os.makedirs(path, exist_ok=True)
            self.category_dirs[category] = path
            

    def _import_libs(self):
        """按需导入库，减少启动时间和内存占用"""
        if self._libs_imported:
            return

        # 导入标准库
        import gzip
        import shutil
        import random
        import string
        import subprocess

        # 保存引用
        self.gzip = gzip
        self.shutil = shutil
        self.random = random
        self.string = string
        self.subprocess = subprocess

        self._libs_imported = True

    def find_files_to_process(self) -> List[str]:
        """查找需要处理的文件 - 使用os.scandir优化性能"""
        files_to_process = []
        output_path_norm = os.path.normpath(self.output_dir)
        audio_path_norm = os.path.normpath(self.audio_dir)

        def scan_directory(dir_path):
            """递归扫描目录"""
            try:
                with os.scandir(dir_path) as entries:
                    for entry in entries:
                        # 如果当前条目是目录
                        if entry.is_dir():
                            # 如果目录不是输出目录和Audio目录
                            entry_path_norm = os.path.normpath(entry.path)
                            if (output_path_norm not in entry_path_norm and 
                                audio_path_norm not in entry_path_norm):
                                scan_directory(entry.path)
                        elif entry.is_file():
                            # 如果文件名中不包含关键字且不以.ogg结尾
                            name = entry.name
                            # 检查是否已经是.ogg文件
                            if name.endswith('.ogg'):
                                continue
                                
                            # 检查是否包含任何关键字
                            should_skip = False
                            for keyword in self.keywords:
                                if keyword in name:
                                    should_skip = True
                                    break
                                    
                            if not should_skip:
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
        print(f"\n• 正在扫描文件...")

        # 查找要处理的文件
        files_to_process = self.find_files_to_process()

        scan_duration = time.time() - start_time
        print(f"✓ 找到 {len(files_to_process)} 个文件 (耗时 {scan_duration:.2f} 秒)")

        if not files_to_process:
            print(f"! 未找到符合条件的文件")
            return {
                "processed": 0,
                "duplicates": 0,
                "already_processed": 0,
                "errors": 0,
                "output_dir": self.output_dir,
                "duration": 0,
                "files_per_second": 0
            }

        # 重置统计信息
        self.stats.reset()
        self.hash_cache.clear()
        self.processed_count = 0
        self.cancelled = False

        # 处理文件
        processing_start = time.time()
        print(f"\n• 使用 {self.num_threads} 个线程处理文件...")

        # 创建一个工作队列和一个结果队列
        work_queue = queue.Queue()

        # 填充工作队列
        for file_path in files_to_process:
            work_queue.put(file_path)

        # 创建工作线程
        def worker():
            while not self.is_cancelled():
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

    def set_cancel_check(self, check_fn):
        """设置取消检查函数"""
        self._cancel_check_fn = check_fn
        
    def is_cancelled(self):
        """检查是否应该取消处理"""
        if self._cancel_check_fn:
            return self._cancel_check_fn()
        return self.cancelled
        
    def process_file(self, file_path: str) -> bool:
        """处理单个文件并提取音频"""
        if self.is_cancelled():
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
        """提取文件中的OGG内容
        
        提取流程:
        1. 定位原始文件：从Roblox缓存目录中读取文件
        2. 文件识别：通过读取前2048字节检查是否包含OggS或ID3头部标识
        3. 提取音频数据：找到OggS或ID3头部在文件中的位置，从该位置开始截取剩余所有数据
        4. 保存文件：将提取的数据保存为带有.ogg扩展名的新文件
        """
        try:
            # 使用二进制模式打开文件
            with open(file_path, 'rb') as f:
                # 读取前2048字节检查OGG头或ID3头
                header_chunk = f.read(2048)
                
                # 查找OggS头部标识
                ogg_start = header_chunk.find(b'OggS')
                
                if ogg_start >= 0:
                    # 如果在前2048字节中找到了OggS头部，重置文件指针到头部位置
                    f.seek(ogg_start)
                    # 从该位置开始截取剩余所有数据
                    return f.read()
                
                # 查找ID3头部标识
                id3_start = header_chunk.find(b'ID3')
                
                if id3_start >= 0:
                    # 在ID3后寻找OggS头部
                    f.seek(0)
                    content = f.read()
                    
                    # 在ID3标记之后查找OggS
                    post_id3_content = content[id3_start:]
                    ogg_in_id3 = post_id3_content.find(b'OggS')
                    
                    if ogg_in_id3 >= 0:
                        # 找到了嵌入在ID3之后的OggS
                        return post_id3_content[ogg_in_id3:]
                
                # 如果前2048字节中没有找到OggS头部，检查整个文件
                f.seek(0)
                content = f.read()
                
                # 查找OggS标记
                ogg_start = content.find(b'OggS')
                if ogg_start >= 0:
                    # 从OggS头部位置开始截取剩余所有数据
                    return content[ogg_start:]
                
                # 尝试作为gzip解压
                try:
                    if not self._libs_imported:
                        self._import_libs()
                    # 尝试解压
                    decompressed = self.gzip.decompress(content)
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
            if not self._libs_imported:
                self._import_libs()

            subprocess_flags = 0
            if os.name == 'nt':  # Windows
                subprocess_flags = self.subprocess.CREATE_NO_WINDOW

            # 使用ffprobe获取音频时长
            result = self.subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", file_path],
                stdout=self.subprocess.PIPE,
                stderr=self.subprocess.PIPE,
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
            if not self._libs_imported:
                self._import_libs()
            random_suffix = ''.join(self.random.choices(self.string.ascii_lowercase + self.string.digits, k=4))
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
            if not self._libs_imported:
                self._import_libs()
            self.shutil.move(temp_path, output_path)

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


def is_ffmpeg_available() -> bool:
    """检查FFmpeg是否可用"""
    try:
        import subprocess
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


def open_directory(path: str) -> bool:
    """在文件资源管理器/Finder中打开目录"""
    try:
        if os.name == 'nt':  # Windows
            os.startfile(path)
        elif os.name == 'posix':  # macOS, Linux
            import subprocess
            if sys.platform == 'darwin':  # macOS
                subprocess.call(['open', path])
            else:  # Linux
                subprocess.call(['xdg-open', path])
        return True
    except Exception:
        return False 