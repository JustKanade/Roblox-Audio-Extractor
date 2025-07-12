#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Roblox图像提取器 - 从Roblox缓存中提取图片文件
Roblox Image Extractor - Extract image files from Roblox cache
"""

import os
import time
import queue
import threading
import datetime
import hashlib
import random
import string
import shutil
import multiprocessing
from enum import Enum, auto
from typing import Dict, List, Any, Set, Optional, Tuple, Callable, Union

# 用于图像处理的库
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None  # 如果导入失败，设为None


class ImageClassificationMethod(Enum):
    """图像分类方法枚举"""
    TYPE = auto()  # 按类型分类 (PNG, WEBP, KTX)
    SIZE = auto()  # 按大小分类


class ContentHashCache:
    """内容哈希缓存，用于防止重复提取相同的文件"""

    def __init__(self):
        self.hash_set = set()

    def is_duplicate(self, content_hash: str) -> bool:
        if content_hash in self.hash_set:
            return True
        self.hash_set.add(content_hash)
        return False

    def clear(self) -> None:
        self.hash_set.clear()


class ProcessingStats:
    """处理统计信息"""

    def __init__(self):
        self.stats = {}
        self.reset()

    def reset(self) -> None:
        """重置所有统计信息"""
        self.stats = {
            'processed_files': 0,  # 成功处理的文件数
            'duplicate_files': 0,  # 重复文件数
            'already_processed': 0,  # 已经处理过的文件数（基于历史记录）
            'error_files': 0,  # 处理出错的文件数
            'png_files': 0,    # PNG格式文件数
            'webp_files': 0,   # WEBP格式文件数
            'ktx_files': 0,    # KTX格式文件数
            'unknown_files': 0  # 未知格式文件数
        }

    def increment(self, stat_key: str, amount: int = 1) -> None:
        """增加指定统计项的计数"""
        if stat_key in self.stats:
            self.stats[stat_key] += amount
        else:
            # 如果是新的统计项，初始化为指定值
            self.stats[stat_key] = amount

    def get(self, stat_key: str) -> int:
        """获取指定统计项的值"""
        return self.stats.get(stat_key, 0)

    def get_all(self) -> Dict[str, int]:
        """获取所有统计信息"""
        return self.stats.copy()


class RobloxImageExtractor:
    """从Roblox临时文件中提取图片的主类"""

    def __init__(self, base_dir: str, num_threads: Optional[int] = None,
                 download_history: Optional[Any] = None,
                 classification_method: ImageClassificationMethod = ImageClassificationMethod.TYPE,
                 custom_output_dir: Optional[str] = None):
        """初始化提取器"""
        self.base_dir = os.path.abspath(base_dir)
        # 确保num_threads始终是整数
        self.num_threads = int(num_threads) if num_threads is not None else min(32, multiprocessing.cpu_count() * 2)
        self.download_history = download_history
        self.classification_method = classification_method

        # 输出目录
        if custom_output_dir and os.path.isdir(custom_output_dir):
            # 使用自定义输出路径
            self.output_dir = os.path.abspath(custom_output_dir)
        else:
            # 使用默认输出路径
            self.output_dir = os.path.join(self.base_dir, "extracted_images")
        
        # 创建Images总文件夹
        self.images_dir = os.path.join(self.output_dir, "Images")
        self.logs_dir = os.path.join(self.output_dir, "logs")

        # 创建日志和图片总文件夹
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        # 初始化处理对象
        self.stats = ProcessingStats()
        self.hash_cache = ContentHashCache()
        self.file_lock = threading.Lock()

        # 文件计数器，使用原子操作而不是锁
        self.processed_count = 0
        
        # 定义取消操作的回调函数，默认为始终返回False
        self._cancelled = False
        
        # 按图片类型分类
        self.type_categories = {
            "png": "PNG图片",
            "webp": "WEBP图片",
            "ktx": "KTX纹理",
            "unknown": "未知格式"
        }

        # 按文件大小分类 (字节)
        self.size_categories = {
            "ultra_small_0-10KB": (0, 10 * 1024),  # 0-10KB
            "small_10-50KB": (10 * 1024, 50 * 1024),  # 10KB-50KB
            "medium_50-200KB": (50 * 1024, 200 * 1024),  # 50KB-200KB
            "large_200KB-1MB": (200 * 1024, 1024 * 1024),  # 200KB-1MB
            "ultra_large_1MB+": (1024 * 1024, float('inf'))  # 1MB+
        }

        # 为每个类别创建目录
        self.category_dirs = {}

        # 根据分类方法选择要使用的类别
        if self.classification_method == ImageClassificationMethod.TYPE:
            categories = self.type_categories
            for category in categories:
                path = os.path.join(self.images_dir, category)
                os.makedirs(path, exist_ok=True)
                self.category_dirs[category] = path
        else:
            categories = self.size_categories
            for category in categories:
                path = os.path.join(self.images_dir, category)
                os.makedirs(path, exist_ok=True)
                self.category_dirs[category] = path

    # 将cancelled实现为属性，允许外部设置为函数或布尔值
    @property
    def cancelled(self) -> bool:
        """检查是否已取消处理"""
        if callable(self._cancelled):
            return bool(self._cancelled())
        return bool(self._cancelled)
        
    @cancelled.setter
    def cancelled(self, value: Union[bool, Callable[[], bool]]):
        """设置取消状态，可以是布尔值或回调函数"""
        self._cancelled = value

    def find_files_to_process(self) -> List[str]:
        """查找需要处理的文件 - 专注于http缓存目录中的无扩展名文件"""
        files_to_process = []
        output_path_norm = os.path.normpath(self.output_dir)
        images_path_norm = os.path.normpath(self.images_dir)
        
        # 特别关注http缓存目录
        http_cache_dir = os.path.join(self.base_dir, "http")
        
        def scan_directory(dir_path):
            """递归扫描目录"""
            try:
                with os.scandir(dir_path) as entries:
                    for entry in entries:
                        # 如果当前条目是目录
                        if entry.is_dir():
                            # 如果目录不是输出目录和Images目录
                            entry_path_norm = os.path.normpath(entry.path)
                            if (output_path_norm not in entry_path_norm and 
                                images_path_norm not in entry_path_norm):
                                scan_directory(entry.path)
                        elif entry.is_file():
                            # 图像文件通常没有扩展名或有特定扩展名
                            name = entry.name
                            _, ext = os.path.splitext(name)
                            # 如果文件没有扩展名或有特定扩展名
                            if ext == '' or ext.lower() in ['.webp', '.png']:
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

        # 如果http缓存目录存在，优先扫描
        if os.path.exists(http_cache_dir) and os.path.isdir(http_cache_dir):
            scan_directory(http_cache_dir)
        
        # 扫描其他可能包含图片的目录
        scan_directory(self.base_dir)
        return files_to_process

    def process_files(self) -> Dict[str, Any]:
        """处理目录中的文件"""
        # 扫描文件并记录开始时间
        start_time = time.time()
        # 使用语言管理器获取翻译文本，如果不可用则使用默认文本
        scanning_msg = lang.get("scanning_files", "正在扫描文件...") if lang else "正在扫描文件..."
        print(f"\n• {scanning_msg}")

        # 查找要处理的文件
        files_to_process = self.find_files_to_process()

        scan_duration = time.time() - start_time
        # 使用语言管理器获取翻译文本，如果不可用则使用默认文本
        found_files_msg = lang.get("found_files", "找到 {0} 个文件，用时 {1:.2f} 秒").format(
            len(files_to_process), scan_duration
        ) if lang else f"找到 {len(files_to_process)} 个文件，用时 {scan_duration:.2f} 秒"
        print(f"✓ {found_files_msg}")

        if not files_to_process:
            # 使用语言管理器获取翻译文本，如果不可用则使用默认文本
            no_files_msg = lang.get("no_files_found", "未找到任何文件") if lang else "未找到任何文件"
            print(f"! {no_files_msg}")
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
        
        # 处理文件
        processing_start = time.time()
        # 使用语言管理器获取翻译文本，如果不可用则使用默认文本
        processing_msg = lang.get("processing_with_threads", "使用 {0} 个线程处理文件").format(
            self.num_threads
        ) if lang else f"使用 {self.num_threads} 个线程进行处理"
        print(f"\n• {processing_msg}")

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
            self._cancelled = True
            # 使用语言管理器获取翻译文本，如果不可用则使用默认文本
            canceled_msg = lang.get("operation_cancelled", "操作被用户取消") if lang else "操作被用户取消"
            print(f"\n{canceled_msg}.")

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
            "png_files": stats['png_files'],
            "webp_files": stats['webp_files'],
            "ktx_files": stats['ktx_files'],
            "unknown_files": stats['unknown_files'],
            "output_dir": self.output_dir,
            "duration": total_time,
            "files_per_second": files_per_second
        }

    def process_file(self, file_path: str) -> bool:
        """处理单个文件并提取图片"""
        if self.cancelled:
            return False

        try:
            # 计算文件哈希
            file_hash = self._get_file_hash(file_path)

            # 如果文件已经处理过了，则跳过
            if self.download_history and self.download_history.is_processed(file_hash):
                self.stats.increment('already_processed')
                return False

            # 尝试读取文件内容并识别图片类型
            file_content, image_type = self._extract_image_content(file_path)
            if not file_content or image_type == "unknown":
                return False

            # 统计不同类型的图片
            if image_type == "png":
                self.stats.increment('png_files')
            elif image_type == "webp":
                self.stats.increment('webp_files')
            elif image_type == "ktx":
                self.stats.increment('ktx_files')
            else:
                self.stats.increment('unknown_files')

            # 计算内容哈希以检测重复
            content_hash = hashlib.md5(file_content).hexdigest()
            if self.hash_cache.is_duplicate(content_hash):
                self.stats.increment('duplicate_files')
                return False

            # 保存文件
            output_path = self._save_image_file(file_path, file_content, image_type)
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

    def _extract_image_content(self, file_path: str) -> Tuple[Optional[bytes], str]:
        """提取文件中的图片内容并识别类型
        
        提取流程:
        1. 定位原始文件：从Roblox缓存目录中读取文件
        2. 文件识别：检查特征标识以确定文件类型（PNG、WEBP或KTX）
        3. 提取图片数据：根据不同类型处理不同的偏移量
          - PNG格式：偏移量为1字节
          - WEBP格式：偏移量为8字节
          - KTX格式：偏移量为1字节
        4. 保存文件：将提取的数据保存为带有适当扩展名的新文件
        """
        try:
            # 使用二进制模式打开文件
            with open(file_path, 'rb') as f:
                content = f.read()
                
                # 查找PNG标识
                png_start = content.find(b'\x89PNG')
                if png_start >= 0:
                    # PNG通常偏移1字节
                    return content[png_start:], "png"
                
                # 查找WEBP标识
                webp_start = content.find(b'WEBP')
                if webp_start >= 0:
                    # 根据文档，WEBP偏移8字节
                    # 实际查找RIFF标头，通常WEBP文件以RIFF开头
                    riff_start = content.find(b'RIFF', max(0, webp_start - 8))
                    if riff_start >= 0:
                        return content[riff_start:], "webp"
                    else:
                        # 如果找不到RIFF，尝试从WEBP标识的8字节前开始
                        start = max(0, webp_start - 8)
                        return content[start:], "webp"
                
                # 查找KTX标识
                ktx_start = content.find(b'KTX')
                if ktx_start >= 0:
                    # KTX通常偏移1字节
                    return content[max(0, ktx_start - 1):], "ktx"

            # 如果没有找到任何已知格式
            return None, "unknown"
        except Exception:
            return None, "unknown"

    def _get_size_category(self, file_size: int) -> str:
        """根据文件大小确定类别"""
        for category, (min_size, max_size) in self.size_categories.items():
            if min_size <= file_size < max_size:
                return category

        # 默认类别：如果没有匹配项，分配到第一个类别
        return next(iter(self.size_categories.keys()))

    def _save_image_file(self, source_path: str, content: bytes, image_type: str) -> Optional[str]:
        """保存提取的图片文件"""
        try:
            # 生成临时文件名
            base_name = os.path.basename(source_path)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
            
            # 根据图片类型决定扩展名
            if image_type == "png":
                ext = ".png"
            elif image_type == "webp":
                ext = ".webp"
            elif image_type == "ktx":
                ext = ".ktx"
            else:
                ext = ".bin"  # 未知类型使用通用扩展名
                
            temp_name = f"temp_{base_name}_{timestamp}_{random_suffix}{ext}"
            temp_path = os.path.join(self.output_dir, temp_name)

            # 保存临时文件
            with open(temp_path, 'wb', buffering=1024 * 8) as f:
                f.write(content)

            # 确定分类类别
            if self.classification_method == ImageClassificationMethod.TYPE:
                # 按类型分类
                category = image_type if image_type in self.type_categories else "unknown"
            else:
                # 按大小分类
                file_size = len(content)
                category = self._get_size_category(file_size)

            output_dir = self.category_dirs[category]

            # 生成最终文件名
            output_name = f"{base_name}_{timestamp}_{random_suffix}{ext}"
            output_path = os.path.join(output_dir, output_name)

            # 移动文件到正确的类别目录
            shutil.move(temp_path, output_path)

            return output_path

        except Exception as e:
            # 如果处理失败，删除临时文件
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            self._log_error(source_path, f"无法保存文件: {str(e)}")
            return None

    def _get_file_hash(self, file_path: str) -> str:
        """获取文件路径的哈希值，用于历史记录"""
        return hashlib.md5(file_path.encode('utf-8')).hexdigest()

    def _log_error(self, file_path: str, error_message: str) -> None:
        """将错误记录到日志文件"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_message = f"[{timestamp}] 错误处理 {file_path}: {error_message}\n"
            
            log_file = os.path.join(self.logs_dir, "extraction_errors.log")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_message)
        except:
            # 如果日志记录失败，不应影响主程序
            pass

    def create_readme(self) -> None:
        """在输出目录创建自述文件"""
        readme_path = os.path.join(self.output_dir, "README.txt")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(f"Roblox图像提取器 - 提取时间: {timestamp}\n")
            f.write("=" * 50 + "\n\n")
            f.write("此文件夹包含从Roblox缓存中提取的图像文件。\n")
            f.write("文件按照以下类别分类存放：\n\n")
            
            if self.classification_method == ImageClassificationMethod.TYPE:
                for category, desc in self.type_categories.items():
                    f.write(f"- {category}: {desc}\n")
            else:
                for category, (min_size, max_size) in self.size_categories.items():
                    min_kb = min_size / 1024
                    max_kb = "无限" if max_size == float('inf') else f"{max_size/1024:.1f}KB"
                    f.write(f"- {category}: {min_kb:.1f}KB 到 {max_kb}\n") 