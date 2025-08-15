#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体提取器模块 
Font Extractor Module 
"""

import os
import json
import hashlib
import logging
import threading
import queue
import time
import requests
import traceback
import multiprocessing
from typing import Dict, List, Any, Optional, Callable
from enum import Enum, auto
from dataclasses import dataclass

# 导入历史管理器
from src.utils.history_manager import ExtractedHistory, ContentHashCache

# 导入Roblox字体提取模块
from .rbxh_parser import RBXHParser, ParsedCache, parse_cache_file, parse_cache_data
from .content_identifier import ContentIdentifier, AssetType, IdentifiedContent, identify_content
from .cache_scanner import RobloxCacheScanner, CacheItem, CacheType, scan_roblox_cache

# 导入多进程工具
from src.utils.multiprocessing_utils import (
    MultiprocessingManager, 
    ProcessingConfig,
    get_optimal_process_count,
    create_worker_function
)

logger = logging.getLogger(__name__)

class FontClassificationMethod(Enum):
    """字体分类方法枚举"""
    FAMILY = auto()     # 按字体家族分类
    STYLE = auto()      # 按字体样式分类  
    SIZE = auto()       # 按文件大小分类
    NONE = auto()       # 无分类

class FontProcessingStats:
    """字体处理统计类 - 线程安全"""
    
    def __init__(self):
        self.stats = {
            'processed_caches': 0,
            'fontlist_found': 0,
            'fonts_downloaded': 0,
            'already_processed': 0,  # 新增：已处理过的字体计数
            'duplicate_skipped': 0,
            'download_failed': 0,
            'processing_errors': 0
        }
        self._lock = threading.Lock()
    
    def increment(self, key: str, amount: int = 1):
        """线程安全地增加统计值"""
        with self._lock:
            if key in self.stats:
                self.stats[key] += amount
    
    def get_all(self) -> Dict[str, int]:
        """获取所有统计数据的副本"""
        with self._lock:
            return self.stats.copy()

# 多进程工作函数
def _process_cache_item_worker(cache_item: CacheItem, config: 'FontProcessingConfig') -> Dict[str, Any]:
    """
    多进程字体缓存项处理工作函数
    
    Args:
        cache_item: 缓存项
        config: 处理配置
        
    Returns:
        Dict[str, Any]: 处理结果
    """
    result = {
        'success': False,
        'fontlist_processed': 0,
        'fonts_downloaded': 0,
        'errors': [],
        'processed_hashes': [] # 新增：收集成功处理的哈希
    }
    
    try:
        # 创建处理器实例
        rbxh_parser = RBXHParser()
        content_identifier = ContentIdentifier(config.block_avatar_images)
        
        # 解析缓存内容
        if cache_item.data:
            parsed_cache = rbxh_parser.parse_cache_data(cache_item.data)
        else:
            parsed_cache = rbxh_parser.parse_cache_file(cache_item.path)
        
        if not parsed_cache.success:
            return result
        
        # 识别内容类型
        identified = content_identifier.identify_content(parsed_cache.content)
        
        # 只处理字体列表
        if identified.asset_type == AssetType.FontList:
            result['fontlist_processed'] = 1
            
            # 创建字体处理器 - 多进程模式下每个进程使用少量下载线程
            download_threads = min(2, max(1, multiprocessing.cpu_count() // 4))
            font_processor = FontListProcessor(
                config.fonts_dir, 
                config.classification_method,
                download_threads,
                download_history,
                collect_hashes=True  # 多进程模式下启用哈希收集
            )
            
            # 处理字体列表
            process_result = font_processor.process_fontlist(
                cache_item.hash_id, 
                parsed_cache.content
            )
            
            if process_result["success"]:
                result['fonts_downloaded'] = process_result["downloaded_count"]
                result['processed_hashes'] = process_result.get("processed_hashes", [])
                result['success'] = True
            else:
                result['errors'].extend(process_result.get("errors", []))
        
    except Exception as e:
        result['errors'].append(f"处理缓存项 {cache_item.hash_id} 失败: {str(e)}")
    
    return result

@dataclass
class FontProcessingConfig:
    """字体处理配置类"""
    fonts_dir: str
    classification_method: FontClassificationMethod
    block_avatar_images: bool = True
    history_file: Optional[str] = None # 新增历史文件路径参数

class FontListProcessor:
    """字体列表处理器 - 处理Roblox字体列表"""
    
    def __init__(self, output_dir: str, classification_method: FontClassificationMethod = FontClassificationMethod.FAMILY, max_download_threads: int = 4, download_history: Optional['ExtractedHistory'] = None, collect_hashes: bool = False):
        """
        初始化字体列表处理器
        
        Args:
            output_dir: 输出目录
            classification_method: 分类方法
            max_download_threads: 最大下载线程数
            download_history: 下载历史管理器，用于避免重复处理文件
            collect_hashes: 是否收集处理过的哈希
        """
        self.output_dir = output_dir
        self.classification_method = classification_method
        self.max_download_threads = max_download_threads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RobloxAudioExtractor/1.0'
        })
        self._cancel_check_fn = None  # 取消检查函数
        self._log_callback = None  # 日志回调函数
        self.download_history = download_history
        self.collect_hashes = collect_hashes
        self.processed_hashes = []  # 成功处理的哈希列表（用于多进程模式）
    
    def set_cancel_check(self, cancel_check_fn: Callable[[], bool]):
        """设置取消检查函数"""
        self._cancel_check_fn = cancel_check_fn
    
    def set_log_callback(self, log_callback: Callable[[str, str], None]):
        """设置日志回调函数"""
        self._log_callback = log_callback
    
    def send_log(self, message_key: str, log_type: str, *args):
        """发送日志消息到界面"""
        if self._log_callback:
            self._log_callback(message_key, log_type, *args)
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        if self._cancel_check_fn:
            return self._cancel_check_fn()
        return False
    
    def _get_file_hash(self, file_path_or_url: str) -> str:
        """计算文件或URL的哈希值
        
        Args:
            file_path_or_url: 文件路径或下载URL
            
        Returns:
            str: 哈希值
        """
        try:
            # 对于URL，使用URL本身作为哈希依据
            if file_path_or_url.startswith(('http://', 'https://')):
                return hashlib.md5(file_path_or_url.encode()).hexdigest()
            
            # 对于文件路径，读取文件内容的前8KB用于哈希计算
            # 对于字体文件，开头部分通常包含足够的唯一特征
            with open(file_path_or_url, 'rb') as f:
                content_head = f.read(8192)  # 读取前8KB
            
            if content_head:
                # 将文件内容的哈希与文件路径结合，确保唯一性
                # 使用内容作为主要哈希依据，但仍然包含路径信息
                content_hash = hashlib.md5(content_head).hexdigest()
                path_hash = hashlib.md5(file_path_or_url.encode()).hexdigest()[:8]
                return f"{content_hash}_{path_hash}"
            else:
                # 如果无法读取内容，退回到使用文件信息
                file_stat = os.stat(file_path_or_url)
                return hashlib.md5(f"{file_path_or_url}_{file_stat.st_size}_{file_stat.st_mtime}".encode()).hexdigest()
        except Exception:
            # 如果无法获取文件信息，使用文件路径/URL
            return hashlib.md5(file_path_or_url.encode()).hexdigest()
    
    def _get_content_hash(self, content: bytes) -> str:
        """计算内容的哈希值
        
        Args:
            content: 字体文件内容（字节数据）
            
        Returns:
            str: 内容哈希值
        """
        return hashlib.md5(content).hexdigest()
    
    def process_fontlist(self, dump_name: str, content: bytes) -> Dict[str, Any]:
        """
        处理字体列表
        
        Args:
            dump_name: 缓存文件名
            content: 字体列表内容
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        result = {
            "success": False,
            "font_family": "",
            "faces_count": 0,
            "downloaded_count": 0,
            "already_processed_count": 0,  # 新增：已处理过的字体计数
            "errors": []
        }
        
        try:
            # 检查是否已取消
            if self.is_cancelled():
                result["errors"].append("操作已取消")
                return result
            
            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)
            
            # 解析JSON
            content_str = content.decode('utf-8', errors='ignore')
            font_data = json.loads(content_str)
            
            font_name = font_data.get("name", "Unknown")
            faces = font_data.get("faces", [])
            
            result["font_family"] = font_name
            result["faces_count"] = len(faces)
            
            logger.debug(f"处理字体列表: {font_name}, 包含 {len(faces)} 个字体")
            self.send_log("processing_font_list", "info", font_name, len(faces))
            
            # 保存JSON文件
            json_path = os.path.join(self.output_dir, f"{font_name}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(font_data, f, indent=2, ensure_ascii=False)
            
            # 下载字体文件 - 支持多线程
            if len(faces) > 1 and self.max_download_threads > 1:
                # 使用多线程下载
                downloaded_count, already_processed_count = self._download_fonts_multithreaded(font_name, faces, result["errors"])
            else:
                # 串行下载（单个字体或线程数为1）
                downloaded_count = 0
                already_processed_count = 0
                for face in faces:
                    # 检查是否已取消
                    if self.is_cancelled():
                        logger.debug("字体下载被用户取消")
                        self.send_log("font_download_cancelled", "warning")
                        break
                    
                    try:
                        download_result = self._download_font_face(font_name, face)
                        if download_result == "downloaded":
                            downloaded_count += 1
                        elif download_result == "already_processed":
                            already_processed_count += 1
                    except Exception as e:
                        error_msg = f"下载字体 {font_name}-{face.get('name', 'Unknown')} 失败: {e}"
                        logger.error(error_msg)
                        result["errors"].append(error_msg)
            
            result["downloaded_count"] = downloaded_count
            result["already_processed_count"] = already_processed_count
            result["success"] = True
            
            logger.debug(f"字体列表处理完成: {font_name}, 成功下载 {downloaded_count}/{len(faces)} 个字体")
            self.send_log("font_list_complete", "success", font_name, downloaded_count, len(faces))
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON解析失败: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        except Exception as e:
            error_msg = f"处理字体列表失败: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
        
        return result
    
    def _download_fonts_multithreaded(self, font_name: str, faces: List[Dict[str, Any]], errors: List[str]) -> tuple[int, int]:
        """
        多线程下载字体文件
        
        Args:
            font_name: 字体家族名称
            faces: 字体面列表
            errors: 错误列表
            
        Returns:
            tuple[int, int]: (成功下载的字体数量, 已处理过的字体数量)
        """
        downloaded_count = 0
        already_processed_count = 0
        download_lock = threading.Lock()
        
        # 创建工作队列
        work_queue = queue.Queue()
        for face in faces:
            work_queue.put(face)
        
        def download_worker():
            nonlocal downloaded_count, already_processed_count
            while not self.is_cancelled():
                try:
                    face = work_queue.get(timeout=2)
                    try:
                        result = self._download_font_face(font_name, face)
                        with download_lock:
                            if result == "downloaded":
                                downloaded_count += 1
                            elif result == "already_processed":
                                already_processed_count += 1
                    except Exception as e:
                        error_msg = f"下载字体 {font_name}-{face.get('name', 'Unknown')} 失败: {e}"
                        logger.error(error_msg)
                        with download_lock:
                            errors.append(error_msg)
                    finally:
                        work_queue.task_done()
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"字体下载工作线程出错: {e}")
        
        # 启动下载线程
        threads = []
        thread_count = min(self.max_download_threads, len(faces))
        for _ in range(thread_count):
            thread = threading.Thread(target=download_worker)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # 等待所有下载完成
        try:
            work_queue.join()
        except KeyboardInterrupt:
            logger.debug("多线程字体下载被用户取消")
            self.send_log("multithread_download_cancelled", "warning")
        
        # 等待所有线程结束
        for thread in threads:
            thread.join(timeout=1)
        
        return downloaded_count, already_processed_count
    
    def _get_font_category(self, font_name: str, face_name: str, file_size: int) -> str:
        """
        根据分类方法确定字体文件的分类目录
        
        Args:
            font_name: 字体家族名称
            face_name: 字体面名称
            file_size: 文件大小（字节）
            
        Returns:
            str: 分类目录名称
        """
        if self.classification_method == FontClassificationMethod.FAMILY:
            # 按字体家族分类 - 清理文件夹名称中的特殊字符
            safe_name = font_name.replace(" ", "_").replace("-", "_")
            # 移除其他可能的特殊字符
            safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
            return safe_name
            
        elif self.classification_method == FontClassificationMethod.STYLE:
            # 按字体样式分类 - 提取样式信息
            face_lower = face_name.lower()
            
            # 定义样式优先级（从具体到一般）
            if "black" in face_lower:
                return "Black"
            elif "extra bold" in face_lower or "extrabold" in face_lower:
                return "Extra_Bold"  
            elif "semi bold" in face_lower or "semibold" in face_lower:
                return "Semi_Bold"
            elif "bold" in face_lower:
                return "Bold"
            elif "extra light" in face_lower or "extralight" in face_lower:
                return "Extra_Light"
            elif "thin" in face_lower:
                return "Thin"
            elif "light" in face_lower:
                return "Light"
            elif "medium" in face_lower:
                return "Medium"
            elif "regular" in face_lower or face_lower == "normal":
                return "Regular"
            else:
                # 处理斜体变体
                if "italic" in face_lower:
                    base_style = "Italic"
                    # 检查是否有其他样式与斜体组合
                    if "bold" in face_lower:
                        return "Bold_Italic"
                    elif "light" in face_lower:
                        return "Light_Italic"
                    elif "medium" in face_lower:
                        return "Medium_Italic"
                    else:
                        return base_style
                else:
                    # 未知样式，使用原始名称
                    safe_name = face_name.replace(" ", "_").replace("-", "_")
                    safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
                    return safe_name or "Other"
                    
        elif self.classification_method == FontClassificationMethod.SIZE:
            # 按文件大小分类 - 使用与音频相同的阈值
            if file_size < 50 * 1024:
                return "ultra_small_0-50KB"
            elif file_size < 200 * 1024:
                return "small_50-200KB"
            elif file_size < 1024 * 1024:
                return "medium_200KB-1MB"
            elif file_size < 5 * 1024 * 1024:
                return "large_1MB-5MB"
            else:
                return "ultra_large_5MB+"
        else:
            # 无分类 - 直接输出到根目录
            return ""

    def _download_font_face(self, font_name: str, face: Dict[str, Any]) -> str:
        """
        下载单个字体文件
        
        Args:
            font_name: 字体家族名称
            face: 字体面信息
            
        Returns:
            str: 下载结果 ("downloaded", "already_processed", "failed")
        """
        try:
            face_name = face.get("name", "Regular")
            asset_id = face.get("assetId", "")
            
            # 检查asset ID格式
            if not asset_id.startswith("rbxassetid://"):
                if asset_id.startswith("rbxasset://"):
                    logger.debug(f"跳过本地资源: {font_name}-{face_name}")
                else:
                    logger.debug(f"跳过无效资源ID: {font_name}-{face_name}")
                return "failed"
            
            # 提取asset ID
            split_result = asset_id.split("rbxassetid://")
            if len(split_result) < 2 or not split_result[1].strip():
                logger.debug(f"无效的资源ID格式: {asset_id} (字体: {font_name}-{face_name})")
                return "failed"
            
            asset_id_num = split_result[1]
            download_url = f"https://assetdelivery.roblox.com/v1/asset?id={asset_id_num}"
            
            # 使用asset_id作为唯一标识符进行历史记录检查
            asset_id_hash = f"font_asset_{asset_id_num}"
            
            # 检查是否已经处理过这个资源
            if self.download_history and self.download_history.is_processed(asset_id_hash, 'font'):
                logger.debug(f"跳过已处理的字体资源 (Asset ID: {asset_id_num}): {font_name}-{face_name}.ttf")
                self.send_log("font_already_processed", "info", f"{font_name}-{face_name}.ttf")
                return "already_processed"
            
            logger.debug(f"正在下载字体: {font_name}-{face_name}.ttf...")
            self.send_log("downloading_font", "info", f"{font_name}-{face_name}.ttf")
            
            # 下载字体文件，支持重试
            font_data = None
            max_retries = 3
            
            for attempt in range(max_retries):
                # 检查是否已取消
                if self.is_cancelled():
                    logger.debug("字体下载被用户取消")
                    self.send_log("font_download_cancelled", "warning")
                    return "failed"
                
                try:
                    response = self.session.get(download_url, timeout=30)
                    if response.status_code == 200:
                        font_data = response.content
                        break
                    else:
                        logger.warning(f"下载失败 (状态码: {response.status_code}), 重试中...")
                except Exception as e:
                    logger.warning(f"下载失败 (错误: {e}), 重试中...")
                
                if attempt < max_retries - 1:
                    time.sleep(1)  # 等待1秒后重试
            
            if font_data:
                # 计算内容哈希
                content_hash = self._get_content_hash(font_data)
                
                # 检查内容是否已处理过
                if self.download_history and self.download_history.is_content_processed(content_hash, 'font'):
                    logger.debug(f"跳过已处理的字体内容 (内容重复): {font_name}-{face_name}.ttf")
                    self.send_log("font_content_duplicate", "info", f"{font_name}-{face_name}.ttf")
                    # 仍然需要添加历史记录确保一致性
                    self._add_font_hash_to_history(asset_id_hash)
                    return "already_processed"
                
                # 确定分类目录
                category = self._get_font_category(font_name, face_name, len(font_data))
                category_dir = os.path.join(self.output_dir, category)
                
                # 确保分类目录存在
                try:
                    os.makedirs(category_dir, exist_ok=True)
                except Exception as e:
                    logger.error(f"无法创建目录 {category_dir}: {e}")
                    return "failed"
                
                # 生成字体文件名和路径
                font_filename = f"{font_name}-{face_name}.ttf"
                font_path = os.path.join(category_dir, font_filename)
                
                # 检查文件是否已存在
                file_already_exists = os.path.exists(font_path)
                if file_already_exists:
                    logger.debug(f"文件已存在，跳过保存但添加历史记录: {font_filename}")
                    self.send_log("font_file_exists", "info", f"{category}/{font_filename}")
                    # 即使文件存在，也要添加历史记录确保一致性
                    self._add_font_hash_to_history(asset_id_hash)
                    return "already_processed"
                
                # 保存字体文件
                try:
                    with open(font_path, 'wb') as f:
                        f.write(font_data)
                    logger.debug(f"成功下载字体: {category}/{font_filename}")
                    self.send_log("font_download_success", "info", f"{category}/{font_filename}")
                    
                    # 添加历史记录
                    self._add_font_hash_to_history(asset_id_hash)
                    
                    return "downloaded"
                except Exception as e:
                    logger.error(f"无法写入字体文件 {font_path}: {e}")
                    return "failed"
            else:
                logger.error(f"字体下载失败 ({max_retries}次重试后): {font_name}-{face_name}")
                return "failed"
                
        except Exception as e:
            logger.error(f"下载字体文件时出错: {e}")
            return "failed"
    
    def _add_font_hash_to_history(self, file_hash: str):
        """添加字体哈希到历史记录的统一方法
        
        Args:
            file_hash: 文件哈希值
        """
        if self.collect_hashes:
            # 多进程模式：收集哈希，不立即保存
            self.processed_hashes.append(file_hash)
        elif self.download_history:
            # 单线程/多线程模式：立即添加到历史记录
            self.download_history.add_hash(file_hash, 'font')
    
class RobloxFontExtractor:
    """Roblox字体提取器"""
    
    def __init__(self, 
                 output_dir: Optional[str] = None,
                 classification_method: FontClassificationMethod = FontClassificationMethod.FAMILY,
                 block_avatar_images: bool = True,
                 num_threads: int = 1,
                 use_multiprocessing: bool = False,
                 conservative_multiprocessing: bool = True,
                 log_callback: Optional[Callable[[str, str], None]] = None,
                 download_history: Optional[ExtractedHistory] = None):
        """
        初始化字体提取器
        
        Args:
            output_dir: 输出目录
            classification_method: 分类方法
            block_avatar_images: 是否阻止头像图片
            num_threads: 线程数量
            use_multiprocessing: 是否使用多进程
            conservative_multiprocessing: 是否使用保守的多进程策略
            log_callback: 日志回调函数(message, log_type)
            download_history: 下载历史管理器，用于避免重复处理文件
        """
        # 多线程/多进程配置
        self.use_multiprocessing = use_multiprocessing
        self.conservative_multiprocessing = conservative_multiprocessing
        self.log_callback = log_callback
        self.download_history = download_history
        
        # 根据多进程配置调整线程/进程数量
        if self.use_multiprocessing:
            self.num_processes = get_optimal_process_count(
                max_processes=num_threads if num_threads > 1 else None,
                conservative=conservative_multiprocessing
            )
        else:
            self.num_threads = num_threads or min(32, multiprocessing.cpu_count() * 2)
        
        # 初始化组件
        self.rbxh_parser = RBXHParser()
        self.content_identifier = ContentIdentifier(block_avatar_images)
        from .cache_scanner import get_scanner
        self.cache_scanner = get_scanner(log_callback)
        
        # 配置
        self.classification_method = classification_method
        self.block_avatar_images = block_avatar_images
        
        # 输出目录
        if output_dir and os.path.isdir(output_dir):
            self.output_dir = os.path.abspath(output_dir)
        else:
            self.output_dir = os.path.join(os.getcwd(), "extracted")
        
        self.fonts_dir = os.path.join(self.output_dir, "Fonts")
        os.makedirs(self.fonts_dir, exist_ok=True)
        
        # 字体处理器 - 每个字体家族使用少量线程进行下载
        download_threads = min(4, max(1, (self.num_threads if not self.use_multiprocessing else self.num_processes) // 2))
        self.font_processor = FontListProcessor(self.fonts_dir, classification_method, download_threads, download_history)
        # 传递日志回调到字体处理器
        if self.log_callback:
            self.font_processor.set_log_callback(self.log_callback)
        
        # 统计和状态
        self.stats = FontProcessingStats()
        self.processed_count = 0
        self.cancelled = False
        self._cancel_check_fn = None
        self._lock = threading.Lock()
        
        processing_mode = "多进程" if self.use_multiprocessing else "多线程"
        thread_count = self.num_processes if self.use_multiprocessing else self.num_threads
        logger.debug(f"Roblox字体提取器已初始化，输出目录: {self.fonts_dir}, 处理模式: {processing_mode}({thread_count})")
        
        # 发送初始化日志到界面
        self.send_log("initializing_font_extractor", "info")
    
    def send_log(self, message_key: str, log_type: str, *args):
        """发送日志消息到界面"""
        if self.log_callback:
            # message_key将由界面层处理翻译
            self.log_callback(message_key, log_type, *args)
    
    def set_cancel_check(self, cancel_check_fn: Callable[[], bool]):
        """设置取消检查函数"""
        self._cancel_check_fn = cancel_check_fn
        # 同时传递给字体处理器
        if hasattr(self, 'font_processor'):
            self.font_processor.set_cancel_check(cancel_check_fn)
    
    def cancel(self):
        """取消提取操作"""
        self.cancelled = True
        logger.debug("字体提取操作已取消")
        self.send_log("font_extraction_cancelled", "warning")
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        if self._cancel_check_fn and self._cancel_check_fn():
            return True
        return self.cancelled
    
    def extract_fonts(self, 
                     progress_callback: Optional[Callable[[int, int, str], None]] = None,
                     custom_cache_path: Optional[str] = None) -> Dict[str, Any]:
        """
        提取字体文件
        
        Args:
            progress_callback: 进度回调函数 (当前, 总数, 消息)
            custom_cache_path: 自定义缓存路径
            
        Returns:
            Dict[str, Any]: 提取结果
        """
        logger.debug("开始字体提取...")
        start_time = time.time()
        
        # 发送开始提取日志
        self.send_log("starting_font_extraction", "info")
        
        # 重置统计
        self.stats = FontProcessingStats()
        self.cancelled = False
        
        # 确保字体处理器也有取消检查函数
        if self._cancel_check_fn:
            self.font_processor.set_cancel_check(self._cancel_check_fn)
        
        try:
            # 设置自定义缓存路径
            if custom_cache_path:
                is_database = custom_cache_path.endswith('.db')
                db_folder = ""
                if is_database:
                    db_folder = os.path.dirname(custom_cache_path).replace('-storage.db', '-storage')
                self.cache_scanner.set_custom_path(custom_cache_path, is_database, db_folder)
            
            # 获取缓存信息
            cache_info = self.cache_scanner.get_cache_info()
            logger.debug(f"缓存信息: {cache_info}")
            
            if not cache_info["path_exists"]:
                self.send_log("cache_path_not_found", "error")
                return {
                    "success": False,
                    "error": "Roblox缓存路径不存在或无法访问",
                    "cache_info": cache_info
                }
            
            # 扫描缓存
            cache_items = []
            
            def cache_callback(item: CacheItem):
                cache_items.append(item)
                if progress_callback:
                    progress_callback(len(cache_items), 0, f"扫描缓存: 发现 {len(cache_items)} 项...")
            
            logger.debug("开始扫描Roblox缓存...")
            self.send_log("scanning_cache", "info")
            cache_items = self.cache_scanner.scan_cache(cache_callback)
            
            if not cache_items:
                self.send_log("no_cache_items_found", "warning")
                return {
                    "success": True,
                    "message": "未发现新的缓存项目",
                    "stats": {},
                    "cache_info": cache_info
                }
            
            logger.debug(f"缓存扫描完成，发现 {len(cache_items)} 个项目")
            self.send_log("cache_scan_complete", "info", len(cache_items))
            
            # 处理缓存项目 - 支持多线程/多进程
            logger.debug(f"开始处理缓存项目，总数: {len(cache_items)}")
            processing_start = time.time()
            
            if self.use_multiprocessing:
                result = self._process_cache_items_multiprocessing(cache_items, progress_callback)
            else:
                result = self._process_cache_items_threading(cache_items, progress_callback)
            
            processed = result.get('processed', 0)
            
            # 计算结果
            duration = time.time() - start_time
            stats_dict = self.stats.get_all()
            
            result = {
                "success": True,
                "processed_caches": processed,
                "stats": {
                    'fontlist_found': stats_dict.get('fontlist_found', 0),
                    'fonts_downloaded': stats_dict.get('fonts_downloaded', 0),
                    'already_processed': stats_dict.get('already_processed', 0),
                    'duplicate_skipped': stats_dict.get('duplicate_skipped', 0),
                    'download_failed': stats_dict.get('download_failed', 0),
                    'processing_errors': stats_dict.get('processing_errors', 0)
                },
                "cache_info": cache_info,
                "duration": duration,
                "output_dir": self.fonts_dir
            }
            
            logger.debug(f"字体提取完成! 统计: {result['stats']}")
            
            # 保存历史记录 - 确保所有修改都已持久化
            if self.download_history:
                logger.debug("保存字体提取历史记录...")
                self.send_log("saving_font_history", "info")
                self.download_history.save_history()
                logger.debug("✓ 字体提取历史记录已保存")
            
            # 发送完成日志
            stats = result['stats']
            self.send_log("font_extraction_complete", "success", 
                         stats.get('fontlist_found', 0), 
                         stats.get('fonts_downloaded', 0), 
                         duration)
            
            return result
            
        except Exception as e:
            logger.error(f"字体提取失败: {e}")
            logger.error(traceback.format_exc())
            
            # 发送失败日志
            self.send_log("font_extraction_failed", "error", str(e))
            
            return {
                "success": False,
                "error": str(e),
                "stats": self.stats.get_all() if hasattr(self.stats, 'get_all') else {}
            }

    def _process_cache_items_multiprocessing(self, cache_items: List[CacheItem], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """使用多进程处理缓存项目"""
        logger.debug(f"使用 {self.num_processes} 个进程处理缓存项目...")
        self.send_log("processing_caches_multiprocess", "info", self.num_processes)
        
        # 创建配置对象用于多进程处理
        config = FontProcessingConfig(
            fonts_dir=self.fonts_dir,
            classification_method=self.classification_method,
            block_avatar_images=self.block_avatar_images,
            history_file=self.download_history.history_file if self.download_history else None  # 传递历史文件路径
        )
        
        # 创建多进程管理器
        def progress_callback_wrapper(current, total, elapsed, progress):
            self.processed_count = current
            if progress_callback:
                progress_callback(current, total, f"多进程处理缓存项 {current}/{total}...")
        
        manager = MultiprocessingManager(
            num_processes=self.num_processes,
            conservative=self.conservative_multiprocessing,
            progress_callback=progress_callback_wrapper,
            cancel_check=lambda: self.is_cancelled()
        )
        
        # 创建工作函数
        worker_func = create_worker_function(_process_cache_item_worker)
        
        try:
            # 执行多进程处理
            result = manager.process_items(
                items=cache_items,
                worker_func=worker_func,
                config=config
            )
            
            # 统计结果
            processed_results = result.get('results', [])
            processed = len([r for r in processed_results if r.get('success', False)])
            
            total_fontlist = sum(r.get('fontlist_processed', 0) for r in processed_results)
            total_downloaded = sum(r.get('fonts_downloaded', 0) for r in processed_results)
            
            # 收集所有成功处理的哈希
            all_processed_hashes = []
            for result_item in processed_results:
                if result_item.get('success', False):
                    hashes = result_item.get('processed_hashes', [])
                    all_processed_hashes.extend(hashes)
            
            # 批量添加哈希到主进程的历史记录
            if self.download_history and all_processed_hashes:
                logger.debug(f"批量添加 {len(all_processed_hashes)} 个字体哈希到历史记录...")
                for file_hash in all_processed_hashes:
                    self.download_history.add_hash(file_hash, 'font')
                
                # 强制保存历史记录 - 修复：确保多进程模式下历史记录能够保存
                logger.debug("强制保存字体提取历史记录...")
                self.download_history.save_history()
                logger.debug("✓ 多进程模式下字体提取历史记录已保存")
            
            # 更新统计
            self.stats.increment('processed_caches', processed)
            self.stats.increment('fontlist_found', total_fontlist)
            self.stats.increment('fonts_downloaded', total_downloaded)
            
            return {
                'processed': processed,
                'fontlist_found': total_fontlist,
                'fonts_downloaded': total_downloaded
            }
            
        except Exception as e:
            logger.error(f"多进程处理出错: {e}")
            return {
                'processed': 0,
                'fontlist_found': 0,
                'fonts_downloaded': 0,
                'error': str(e)
            }
    
    def _process_cache_items_threading(self, cache_items: List[CacheItem], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """使用多线程处理缓存项目"""
        logger.debug(f"使用 {self.num_threads} 个线程处理缓存项目...")
        self.send_log("processing_caches_multithread", "info", self.num_threads)
        
        # 创建工作队列
        work_queue = queue.Queue()
        
        # 填充工作队列
        for cache_item in cache_items:
            work_queue.put(cache_item)
        
        # 定义工作线程函数
        def worker():
            while not self.is_cancelled():
                try:
                    # 从队列获取项目，如果队列为空5秒则退出
                    cache_item = work_queue.get(timeout=5)
                    try:
                        self._process_cache_item_threadsafe(cache_item)
                    finally:
                        work_queue.task_done()
                        # 更新进度
                        self.processed_count += 1
                        if progress_callback:
                            progress_callback(
                                self.processed_count, 
                                len(cache_items), 
                                f"多线程处理缓存项 {self.processed_count}/{len(cache_items)}..."
                            )
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"工作线程出错: {e}")
                    self.stats.increment('processing_errors')
        
        # 启动工作线程
        threads = []
        for _ in range(self.num_threads):
            thread = threading.Thread(target=worker)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # 等待所有工作完成
        try:
            work_queue.join()
        except KeyboardInterrupt:
            self.cancelled = True
            logger.debug("线程处理被用户取消")
            self.send_log("thread_processing_cancelled", "warning")
        
        # 等待所有线程结束
        for thread in threads:
            thread.join(timeout=1)
        
        stats_dict = self.stats.get_all()
        return {
            'processed': stats_dict.get('processed_caches', 0),
            'fontlist_found': stats_dict.get('fontlist_found', 0),
            'fonts_downloaded': stats_dict.get('fonts_downloaded', 0)
        }
    
    def _process_cache_item_threadsafe(self, cache_item: CacheItem):
        """线程安全的缓存项处理方法"""
        try:
            # 解析缓存内容
            if cache_item.data:
                parsed_cache = self.rbxh_parser.parse_cache_data(cache_item.data)
            else:
                parsed_cache = self.rbxh_parser.parse_cache_file(cache_item.path)
            
            if not parsed_cache.success:
                return
            
            # 识别内容类型
            identified = self.content_identifier.identify_content(parsed_cache.content)
            
            # 更新统计
            self.stats.increment('processed_caches')
            
            # 只处理字体列表
            if identified.asset_type == AssetType.FontList:
                self.stats.increment('fontlist_found')
                
                # 处理字体列表
                result = self.font_processor.process_fontlist(cache_item.hash_id, parsed_cache.content)
                
                if result["success"]:
                    self.stats.increment('fonts_downloaded', result["downloaded_count"])
                    self.stats.increment('already_processed', result.get("already_processed_count", 0))
                else:
                    self.stats.increment('download_failed')
                    
        except Exception as e:
            logger.error(f"处理缓存项失败: {e}")
            self.stats.increment('processing_errors')
    
    def _process_cache_item(self, cache_item: CacheItem):
        """
        处理单个缓存项目
        
        Args:
            cache_item: 缓存项目
        """
        try:
            # 获取缓存内容
            if cache_item.data:
                # 直接从数据库获取的内容
                parsed_cache = self.rbxh_parser.parse_cache_data(cache_item.data)
            else:
                # 从文件读取的内容
                parsed_cache = self.rbxh_parser.parse_cache_file(cache_item.path)
            
            if not parsed_cache.success:
                return
            
            # 识别内容类型
            identified = self.content_identifier.identify_content(parsed_cache.content)
            
            # 只处理字体列表
            if identified.asset_type == AssetType.FontList:
                self.stats.increment('fontlist_found')
                
                # 处理字体列表
                result = self.font_processor.process_fontlist(cache_item.hash_id, parsed_cache.content)
                
                if result["success"]:
                    self.stats.increment('fonts_downloaded', result["downloaded_count"])
                    self.stats.increment('already_processed', result.get("already_processed_count", 0))
                else:
                    self.stats.increment('download_failed')
                    
            elif identified.asset_type == AssetType.Unknown:
                logger.debug(f"未知内容类型: {identified.type_name}")
            else:
                logger.debug(f"跳过非字体内容: {identified.asset_type.name}")
            
        except Exception as e:
            logger.error(f"处理缓存项失败: {e}")
            self.stats.processing_errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取提取统计"""
        return self.stats.get_all()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return self.cache_scanner.get_cache_info()



# 便捷函数
def extract_roblox_fonts(output_dir: Optional[str] = None,
                                cache_path: Optional[str] = None,
                                progress_callback: Optional[Callable[[int, int, str], None]] = None,
                                num_threads: int = 1,
                                use_multiprocessing: bool = False,
                                conservative_multiprocessing: bool = True,
                                log_callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, Any]:
    """
    Roblox字体提取的便捷函数
    
    Args:
        output_dir: 输出目录
        cache_path: 自定义缓存路径
        progress_callback: 进度回调函数
        num_threads: 线程数量
        use_multiprocessing: 是否使用多进程
        conservative_multiprocessing: 是否使用保守的多进程策略
        log_callback: 日志回调函数
        
    Returns:
        Dict[str, Any]: 提取结果
    """
    extractor = RobloxFontExtractor(
        output_dir=output_dir,
        num_threads=num_threads,
        use_multiprocessing=use_multiprocessing,
        conservative_multiprocessing=conservative_multiprocessing,
        log_callback=log_callback
    )    
    return extractor.extract_fonts(progress_callback, cache_path)

