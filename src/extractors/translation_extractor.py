#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译文件提取器模块 
Translation Extractor Module 
"""

import os
import json
import hashlib
import logging
import threading
import queue
import time
import traceback
import multiprocessing
from typing import Dict, List, Any, Optional, Callable
from enum import Enum, auto
from dataclasses import dataclass

# 导入历史管理器
from src.utils.history_manager import ExtractedHistory, ContentHashCache

# 导入Roblox提取模块
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

class TranslationClassificationMethod(Enum):
    """翻译文件分类方法枚举"""
    LOCALE = auto()        # 按语言区域分类
    CONTENT_TYPE = auto()  # 按内容类型分类
    COMBINED = auto()      # 组合分类(语言+内容类型)
    NONE = auto()          # 无分类

class TranslationProcessingStats:
    """翻译文件处理统计类 - 线程安全"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.stats = {
            'translation_found': 0,
            'translation_saved': 0,
            'already_processed': 0,
            'processing_errors': 0,
            'duplicate_skipped': 0,
            'locales_discovered': set(),
            'content_types_discovered': set()
        }
    
    def increment(self, key: str, value: int = 1):
        """线程安全地增加统计值"""
        with self._lock:
            if key in self.stats:
                if isinstance(self.stats[key], set):
                    # 对于集合类型，value应该是要添加的元素
                    if isinstance(value, (str, int)):
                        self.stats[key].add(value)
                else:
                    self.stats[key] += value
    
    def add_locale(self, locale: str):
        """添加发现的语言区域"""
        with self._lock:
            self.stats['locales_discovered'].add(locale)
    
    def add_content_type(self, content_type: str):
        """添加发现的内容类型"""
        with self._lock:
            self.stats['content_types_discovered'].add(content_type)
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有统计信息的副本"""
        with self._lock:
            # 将集合转换为列表以便序列化
            stats_copy = self.stats.copy()
            stats_copy['locales_discovered'] = list(self.stats['locales_discovered'])
            stats_copy['content_types_discovered'] = list(self.stats['content_types_discovered'])
            return stats_copy

# 多进程工作函数
def _process_cache_item_worker(cache_item: CacheItem, config: 'TranslationProcessingConfig') -> Dict[str, Any]:
    """
    多进程工作函数 - 处理单个缓存项目
    
    Args:
        cache_item: 缓存项目
        config: 处理配置
        
    Returns:
        Dict: 处理结果
    """
    result = {
        'success': False,
        'translation_processed': 0,
        'translation_saved': 0,
        'processed_hashes': [],
        'errors': []
    }
    
    try:
        # 初始化组件
        rbxh_parser = RBXHParser()
        content_identifier = ContentIdentifier(config.block_avatar_images)
        
        # 初始化历史记录管理器
        download_history = None
        if config.history_file and os.path.exists(config.history_file):
            download_history = ExtractedHistory(config.history_file)
        
        # 解析缓存文件
        parsed_cache = rbxh_parser.parse_cache_file(cache_item.path)
        if not parsed_cache.success:
            return result
        
        # 识别内容类型
        identified = content_identifier.identify_content(parsed_cache.content)
        
        # 只处理翻译文件
        if identified.asset_type == AssetType.Translation:
            result['translation_processed'] = 1
            
            # 创建翻译处理器
            translation_processor = TranslationProcessor(
                config.translations_dir, 
                config.classification_method,
                download_history,
                collect_hashes=True  # 多进程模式下启用哈希收集
            )
            
            # 处理翻译文件
            process_result = translation_processor.process_translation(
                cache_item.hash_id, 
                parsed_cache.content
            )
            
            if process_result["success"]:
                result['translation_saved'] = process_result["saved_count"]
                result['processed_hashes'] = process_result.get("processed_hashes", [])
                result['success'] = True
            else:
                result['errors'].extend(process_result.get("errors", []))
        
    except Exception as e:
        result['errors'].append(f"处理缓存项 {cache_item.hash_id} 失败: {str(e)}")
    
    return result

@dataclass
class TranslationProcessingConfig:
    """翻译文件处理配置类"""
    translations_dir: str
    classification_method: TranslationClassificationMethod = TranslationClassificationMethod.LOCALE
    block_avatar_images: bool = True
    history_file: Optional[str] = None

class TranslationProcessor:
    """翻译文件处理器 - 处理Roblox翻译文件"""
    
    def __init__(self, output_dir: str, classification_method: TranslationClassificationMethod = TranslationClassificationMethod.LOCALE, download_history: Optional['ExtractedHistory'] = None, collect_hashes: bool = False):
        """
        初始化翻译文件处理器
        
        Args:
            output_dir: 输出目录
            classification_method: 分类方法
            download_history: 下载历史管理器，用于避免重复处理文件
            collect_hashes: 是否收集处理过的哈希
        """
        self.output_dir = output_dir
        self.classification_method = classification_method
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
    
    def _detect_content_type(self, translation_data: Dict[str, Any]) -> str:
        """
        检测翻译内容的类型
        
        Args:
            translation_data: 翻译数据
            
        Returns:
            str: 内容类型
        """
        entries = translation_data.get("entries", {})
        if not entries:
            return "Unknown"
        
        # 分析翻译键的模式来确定内容类型
        keys = list(entries.keys())
        
        # UI相关的键
        ui_patterns = ['ui.', 'button.', 'menu.', 'dialog.', 'window.', 'tab.', 'label.']
        # 错误相关的键
        error_patterns = ['error.', 'warning.', 'exception.', 'fail.', 'invalid.']
        # 游戏内容相关的键
        game_patterns = ['game.', 'player.', 'item.', 'action.', 'feature.', 'avatar.']
        
        ui_count = sum(1 for key in keys if any(pattern in key.lower() for pattern in ui_patterns))
        error_count = sum(1 for key in keys if any(pattern in key.lower() for pattern in error_patterns))
        game_count = sum(1 for key in keys if any(pattern in key.lower() for pattern in game_patterns))
        
        total = len(keys)
        if ui_count / total > 0.3:
            return "UI"
        elif error_count / total > 0.3:
            return "Errors"
        elif game_count / total > 0.3:
            return "GameContent"
        else:
            return "General"
    
    def _get_output_path(self, locale: str, content_type: str, filename: str) -> str:
        """
        根据分类方法获取输出路径
        
        Args:
            locale: 语言区域
            content_type: 内容类型
            filename: 文件名
            
        Returns:
            str: 输出路径
        """
        if self.classification_method == TranslationClassificationMethod.LOCALE:
            # 按语言分类：Translations/zh-cn/filename.json
            category_dir = os.path.join(self.output_dir, locale)
        elif self.classification_method == TranslationClassificationMethod.CONTENT_TYPE:
            # 按内容类型分类：Translations/UI/filename.json
            category_dir = os.path.join(self.output_dir, content_type)
        elif self.classification_method == TranslationClassificationMethod.COMBINED:
            # 组合分类：Translations/zh-cn/UI/filename.json
            category_dir = os.path.join(self.output_dir, locale, content_type)
        else:  # NONE
            # 无分类：Translations/filename.json
            category_dir = self.output_dir
        
        os.makedirs(category_dir, exist_ok=True)
        return os.path.join(category_dir, filename)
    
    def process_translation(self, dump_name: str, content: bytes) -> Dict[str, Any]:
        """
        处理翻译文件
        
        Args:
            dump_name: 转储文件名
            content: 文件内容
            
        Returns:
            Dict: 处理结果
        """
        result = {
            "success": False,
            "locale": "",
            "content_type": "",
            "saved_count": 0,
            "processed_hashes": [],  # 新增：已处理过的翻译计数
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
            translation_data = json.loads(content_str)
            
            locale = translation_data.get("locale", "unknown")
            result["locale"] = locale
            
            # 检测内容类型
            content_type = self._detect_content_type(translation_data)
            result["content_type"] = content_type
            
            logger.debug(f"处理翻译文件: {locale} ({content_type})")
            self.send_log("processing_translation", "info", locale, content_type)
            
            # 生成内容哈希用于去重
            content_hash = hashlib.sha256(content).hexdigest()
            
            # 检查内容是否已处理过（与音频提取器保持一致的双重检查）
            if self.download_history and self.download_history.is_content_processed(content_hash, 'translation'):
                logger.debug(f"翻译文件内容已处理过，跳过: {locale}")
                result["success"] = True
                result["saved_count"] = 0  # 已处理，不算新保存
                return result
            
            # 生成包含转储名称的文件哈希
            file_hash = f"{content_hash}_{dump_name}"
            
            # 检查完整文件哈希是否已处理过
            if self.download_history and self.download_history.is_processed(file_hash, 'translation'):
                logger.debug(f"翻译文件已处理过，跳过: {locale}")
                result["success"] = True
                result["saved_count"] = 0  # 已处理，不算新保存
                return result
            
            # 生成文件名
            filename = f"{locale}_{content_type}_{dump_name[:8]}.json"
            
            # 获取输出路径
            output_path = self._get_output_path(locale, content_type, filename)
            
            # 保存翻译文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(translation_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"成功保存翻译文件: {output_path}")
            self.send_log("translation_save_success", "info", output_path)
            
            # 添加历史记录
            self._add_translation_hash_to_history(file_hash)
            
            result["success"] = True
            result["saved_count"] = 1
                
        except Exception as e:
            error_msg = f"处理翻译文件时出错: {e}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
    
        return result
    
    def _add_translation_hash_to_history(self, file_hash: str):
        """添加翻译文件哈希到历史记录的统一方法
        
        Args:
            file_hash: 文件哈希值
        """
        if self.collect_hashes:
            # 多进程模式：收集哈希，不立即保存
            self.processed_hashes.append(file_hash)
        elif self.download_history:
            # 单线程/多线程模式：立即添加到历史记录
            self.download_history.add_hash(file_hash, 'translation')

class RobloxTranslationExtractor:
    """Roblox翻译文件提取器"""
    
    def __init__(self, 
                 output_dir: Optional[str] = None,
                 classification_method: TranslationClassificationMethod = TranslationClassificationMethod.LOCALE,
                 block_avatar_images: bool = True,
                 num_threads: int = 1,
                 use_multiprocessing: bool = False,
                 conservative_multiprocessing: bool = True,
                 log_callback: Optional[Callable[[str, str], None]] = None,
                 download_history: Optional[ExtractedHistory] = None):
        """
        初始化翻译文件提取器
        
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
        self.cache_scanner = RobloxCacheScanner(log_callback)
        
        # 配置
        self.classification_method = classification_method
        self.block_avatar_images = block_avatar_images
        
        # 输出目录
        if output_dir and os.path.isdir(output_dir):
            self.output_dir = os.path.abspath(output_dir)
        else:
            self.output_dir = os.path.join(os.getcwd(), "extracted")
        
        self.translations_dir = os.path.join(self.output_dir, "Translations")
        os.makedirs(self.translations_dir, exist_ok=True)
        
        # 翻译文件处理器
        self.translation_processor = TranslationProcessor(self.translations_dir, classification_method, download_history)
        # 传递日志回调到翻译处理器
        if self.log_callback:
            self.translation_processor.set_log_callback(self.log_callback)
        
        # 统计和状态
        self.stats = TranslationProcessingStats()
        self.processed_count = 0
        self.cancelled = False
        self._cancel_check_fn = None
        self._lock = threading.Lock()
        
        processing_mode = "多进程" if self.use_multiprocessing else "多线程"
        thread_count = self.num_processes if self.use_multiprocessing else self.num_threads
        logger.debug(f"Roblox翻译文件提取器已初始化，输出目录: {self.translations_dir}, 处理模式: {processing_mode}({thread_count})")
        
        # 发送初始化日志到界面
        self.send_log("initializing_translation_extractor", "info")
    
    def send_log(self, message_key: str, log_type: str, *args):
        """发送日志消息到界面"""
        if self.log_callback:
            # message_key将由界面层处理翻译
            self.log_callback(message_key, log_type, *args)
    
    def set_cancel_check(self, cancel_check_fn: Callable[[], bool]):
        """设置取消检查函数"""
        self._cancel_check_fn = cancel_check_fn
        if self.translation_processor:
            self.translation_processor.set_cancel_check(cancel_check_fn)
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        if self._cancel_check_fn:
            return self._cancel_check_fn()
        return self.cancelled
    
    def extract_translations(self, 
                           progress_callback: Optional[Callable[[int, int, str], None]] = None,
                           custom_cache_path: Optional[str] = None) -> Dict[str, Any]:
        """
        提取翻译文件
        
        Args:
            progress_callback: 进度回调函数
            custom_cache_path: 自定义缓存路径
            
        Returns:
            Dict[str, Any]: 提取结果
        """
        start_time = time.time()
        
        try:
            # 重置状态
            self.cancelled = False
            self.processed_count = 0
            self.stats = TranslationProcessingStats()
            
            self.send_log("starting_translation_extraction", "info")
            
            # 设置自定义缓存路径
            if custom_cache_path:
                is_database = custom_cache_path.endswith('.db')
                db_folder = ""
                if is_database:
                    db_folder = os.path.dirname(custom_cache_path).replace('-storage.db', '-storage')
                self.cache_scanner.set_custom_path(custom_cache_path, is_database, db_folder)
            
            # 获取缓存信息并检查路径
            cache_info = self.cache_scanner.get_cache_info()
            
            if not cache_info["path_exists"]:
                self.send_log("cache_path_not_found", "error")
                return {
                    "success": False,
                    "error": "Roblox缓存路径不存在或无法访问",
                    "processed_caches": 0,
                    "stats": self.stats.get_all(),
                    "cache_info": cache_info,
                    "duration": time.time() - start_time,
                    "output_dir": self.translations_dir
                }
            
            # 扫描缓存
            self.send_log("scanning_cache", "info")
            cache_items = self.cache_scanner.scan_cache()
            
            if not cache_items:
                self.send_log("no_cache_items_found", "warning")
                return {
                    "success": False,
                    "error": "未发现缓存项目",
                    "processed_caches": 0,
                    "stats": self.stats.get_all(),
                    "cache_info": cache_info,
                    "duration": time.time() - start_time,
                    "output_dir": self.translations_dir
                }
            
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
                    'translation_found': stats_dict.get('translation_found', 0),
                    'translation_saved': stats_dict.get('translation_saved', 0),
                    'already_processed': stats_dict.get('already_processed', 0),
                    'duplicate_skipped': stats_dict.get('duplicate_skipped', 0),
                    'processing_errors': stats_dict.get('processing_errors', 0),
                    'locales_discovered': stats_dict.get('locales_discovered', []),
                    'content_types_discovered': stats_dict.get('content_types_discovered', [])
                },
                "cache_info": cache_info,
                "duration": duration,
                "output_dir": self.translations_dir
            }
            
            logger.debug(f"翻译文件提取完成! 统计: {result['stats']}")
            
            # 保存历史记录 - 确保所有修改都已持久化
            if self.download_history:
                logger.debug("保存翻译文件提取历史记录...")
                self.send_log("saving_translation_history", "info")
                self.download_history.save_history()
                logger.debug("✓ 翻译文件提取历史记录已保存")
            
            # 发送完成日志
            stats = result['stats']
            self.send_log("translation_extraction_complete", "success",
                         stats['translation_found'], stats['translation_saved'], duration)
            
            return result
            
        except Exception as e:
            error_msg = f"翻译文件提取失败: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.send_log("translation_extraction_failed", "error", str(e))
            return {
                "success": False,
                "error": error_msg,
                "processed_caches": self.processed_count,
                "stats": self.stats.get_all(),
                "cache_info": self.cache_scanner.get_cache_info(),
                "duration": time.time() - start_time,
                "output_dir": self.translations_dir
            }
    
    def _process_cache_items_threading(self, cache_items: List[CacheItem], progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Dict[str, Any]:
        """使用多线程处理缓存项目"""
        total_items = len(cache_items)
        processed_count = 0
        
        def worker():
            nonlocal processed_count
            while True:
                try:
                    cache_item = item_queue.get(timeout=1)
                    if cache_item is None:
                        break
                    
                    if self.is_cancelled():
                        item_queue.task_done()
                        break
                    
                    # 处理单个项目
                    self._process_single_cache_item(cache_item)
                    
                    with self._lock:
                        processed_count += 1
                        if progress_callback:
                            progress_callback(processed_count, total_items, f"处理翻译文件 {processed_count}/{total_items}")
                    
                    item_queue.task_done()
                    
                except queue.Empty:
                    break
                except Exception as e:
                    logger.error(f"处理缓存项目时出错: {e}")
                    item_queue.task_done()
        
        # 创建队列和线程
        item_queue = queue.Queue()
        for item in cache_items:
            item_queue.put(item)
        
        # 启动工作线程
        threads = []
        for _ in range(self.num_threads):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)
        
        # 等待所有任务完成
        item_queue.join()
        
        # 停止工作线程
        for _ in threads:
            item_queue.put(None)
        
        for thread in threads:
            thread.join()
        
        return {'processed': processed_count}
    
    def _process_cache_items_multiprocessing(self, cache_items: List[CacheItem], progress_callback: Optional[Callable[[int, int, str], None]] = None) -> Dict[str, Any]:
        """使用多进程处理缓存项目"""
        if not cache_items:
            return {'processed': 0}
        
        # 创建配置对象
        config = TranslationProcessingConfig(
            translations_dir=self.translations_dir,
            classification_method=self.classification_method,
            block_avatar_images=self.block_avatar_images,
            history_file=self.download_history.history_file if self.download_history else None
        )
        
        # 创建多进程管理器
        mp_manager = MultiprocessingManager(
            worker_function=_process_cache_item_worker,
            num_processes=self.num_processes,
            config=config
        )
        
        processed_count = 0
        all_processed_hashes = []
        
        try:
            # 处理任务
            for i, result in enumerate(mp_manager.process_tasks(cache_items)):
                if self.is_cancelled():
                    break
                
                processed_count += 1
                
                # 更新统计
                if result.get('success'):
                    translation_processed = result.get('translation_processed', 0)
                    translation_saved = result.get('translation_saved', 0)
                    
                    if translation_processed > 0:
                        self.stats.increment('translation_found', translation_processed)
                        
                        if translation_saved > 0:
                            self.stats.increment('translation_saved', translation_saved)
                        else:
                            # 发现了翻译文件但没有保存（已处理过）
                            self.stats.increment('already_processed', translation_processed)
                    
                    # 收集处理过的哈希
                    processed_hashes = result.get('processed_hashes', [])
                    all_processed_hashes.extend(processed_hashes)
                
                # 处理错误
                errors = result.get('errors', [])
                if errors:
                    self.stats.increment('processing_errors', len(errors))
                    for error in errors:
                        logger.warning(f"多进程处理错误: {error}")
                
                # 更新进度
                if progress_callback:
                    progress_callback(processed_count, len(cache_items), f"处理翻译文件 {processed_count}/{len(cache_items)}")
        
        finally:
            mp_manager.cleanup()
        
        # 批量添加处理过的哈希到历史记录
        if all_processed_hashes and self.download_history:
            logger.debug(f"批量添加 {len(all_processed_hashes)} 个翻译文件哈希到历史记录")
            for file_hash in all_processed_hashes:
                self.download_history.add_hash(file_hash, 'translation')
        
        return {'processed': processed_count}
    
    def _process_single_cache_item(self, cache_item: CacheItem):
        """处理单个缓存项目"""
        try:
            # 解析缓存文件
            parsed_cache = self.rbxh_parser.parse_cache_file(cache_item.path)
            if not parsed_cache.success:
                return
            
            # 识别内容类型
            identified = self.content_identifier.identify_content(parsed_cache.content)
            
            # 只处理翻译文件
            if identified.asset_type == AssetType.Translation:
                self.stats.increment('translation_found')
                
                # 处理翻译文件
                process_result = self.translation_processor.process_translation(
                    cache_item.hash_id, 
                    parsed_cache.content
                )
                
                if process_result["success"]:
                    if process_result["saved_count"] > 0:
                        self.stats.increment('translation_saved', process_result["saved_count"])
                        # 记录发现的语言和内容类型
                        if process_result["locale"]:
                            self.stats.add_locale(process_result["locale"])
                        if process_result["content_type"]:
                            self.stats.add_content_type(process_result["content_type"])
                    else:
                        self.stats.increment('already_processed')
                else:
                    self.stats.increment('processing_errors')
                    for error in process_result.get("errors", []):
                        logger.warning(f"翻译文件处理错误: {error}")
        
        except Exception as e:
            self.stats.increment('processing_errors')
            logger.error(f"处理缓存项目 {cache_item.hash_id} 时出错: {e}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return self.cache_scanner.get_cache_info()


# 便捷函数
def extract_roblox_translations(output_dir: Optional[str] = None,
                               cache_path: Optional[str] = None,
                               progress_callback: Optional[Callable[[int, int, str], None]] = None,
                               num_threads: int = 1,
                               use_multiprocessing: bool = False,
                               conservative_multiprocessing: bool = True,
                               log_callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, Any]:
    """
    Roblox翻译文件提取的便捷函数
    
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
    extractor = RobloxTranslationExtractor(
        output_dir=output_dir,
        num_threads=num_threads,
        use_multiprocessing=use_multiprocessing,
        conservative_multiprocessing=conservative_multiprocessing,
        log_callback=log_callback
    )    
    return extractor.extract_translations(progress_callback, cache_path) 