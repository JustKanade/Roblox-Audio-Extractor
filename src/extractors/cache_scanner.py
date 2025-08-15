#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存扫描器 - 实现Roblox缓存扫描功能
Cache Scanner - Implements Roblox cache scanning functionality
"""

import os
import sys
import sqlite3
import logging
import threading
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum, auto

# 尝试导入语言管理器
try:
    from src.locale.language_manager import lang
except ImportError:
    lang = None

logger = logging.getLogger(__name__)

def get_text(key, default=""):
    """获取翻译文本"""
    if lang and hasattr(lang, 'get'):
        return lang.get(key, default)
    return default

class CacheType(Enum):
    """缓存类型"""
    FILE_SYSTEM = auto()  # 文件系统缓存
    DATABASE = auto()     # 数据库缓存

@dataclass
class CacheItem:
    """缓存项目"""
    path: str = ""
    data: Optional[bytes] = None
    hash_id: str = ""
    cache_type: CacheType = CacheType.FILE_SYSTEM

class RobloxCacheScanner:
    """Roblox缓存扫描器 - 扫描Roblox缓存文件"""
    
    def __init__(self, log_callback: Optional[Callable[[str, str], None]] = None):
        """
        初始化缓存扫描器
        
        Args:
            log_callback: 可选的日志回调函数，用于向UI发送消息
        """
        self.target_path = ""
        self.target_is_database = False
        self.db_folder = ""
        self.known_items = set()  # 已知项目，避免重复处理
        self._lock = threading.Lock()
        self._has_fallback_warned = False  # 避免重复警告
        self.log_callback = log_callback  # 日志回调函数
        
        # 自动检测Roblox缓存路径
        self._detect_roblox_paths()
    
    def set_log_callback(self, log_callback: Callable[[str, str], None]):
        """设置日志回调函数"""
        self.log_callback = log_callback
    
    def send_log(self, message_key: str, log_type: str, *args):
        """发送日志消息到界面"""
        if self.log_callback:
            self.log_callback(message_key, log_type, *args)
    
    def _detect_roblox_paths(self):
        """自动检测Roblox缓存路径"""
        if sys.platform == 'win32':  # Windows
            local_app_data = os.environ.get('LOCALAPPDATA', '')
            
            # 标准版路径
            web_path = os.path.join(local_app_data, 'Roblox', 'rbx-storage.db')
            web_db_folder = os.path.join(local_app_data, 'Roblox', 'rbx-storage')
            
            # UWP版路径
            uwp_path = os.path.join(local_app_data, 'Packages', 
                                  'ROBLOXCORPORATION.ROBLOX_55nm5eh3cm0pr', 
                                  'LocalState', 'http')
            
            # 检查标准版
            web_exists = os.path.exists(web_path)
            uwp_exists = os.path.exists(uwp_path)
            
            if web_exists and not uwp_exists:
                # 只有标准版
                self.target_path = web_path
                self.target_is_database = True
                self.db_folder = web_db_folder
                logger.info("检测到Roblox标准版缓存")
            elif uwp_exists and not web_exists:
                # 只有UWP版
                self.target_path = uwp_path
                self.target_is_database = False
                self.db_folder = ""
                logger.info("检测到Roblox UWP版缓存")
            elif web_exists and uwp_exists:
                # 两个都存在，默认使用标准版
                self.target_path = web_path
                self.target_is_database = True
                self.db_folder = web_db_folder
                logger.info("检测到多个Roblox版本，默认使用标准版缓存")
            else:
                # 都不存在，使用临时文件夹作为备用
                temp_path = os.path.join(os.environ.get('TEMP', ''), 'Roblox', 'http')
                self.target_path = temp_path
                self.target_is_database = False
                self.db_folder = ""
                logger.warning("未检测到Roblox缓存，使用临时目录作为备用")
                
        else:
            # 非Windows系统，使用默认路径
            logger.warning("非Windows系统，缓存扫描功能可能不可用")
    
    def set_custom_path(self, path: str, is_database: bool = True, db_folder: str = ""):
        """
        设置自定义缓存路径
        
        Args:
            path: 缓存路径
            is_database: 是否为数据库格式
            db_folder: 数据库文件夹路径
        """
        # 检查路径是否实际发生了变化
        path_changed = (self.target_path != path or 
                       self.target_is_database != is_database or 
                       self.db_folder != db_folder)
        
        self.target_path = path
        self.target_is_database = is_database
        self.db_folder = db_folder
        
        # 只有在路径实际发生变化时才重置警告标志
        if path_changed:
            self._has_fallback_warned = False
            logger.info(f"设置自定义缓存路径: {path}, 数据库模式: {is_database}")
        else:
            logger.debug(f"缓存路径未变化，保持现有设置: {path}")
    

    
    def scan_cache(self, callback: Optional[Callable[[CacheItem], None]] = None) -> List[CacheItem]:
        """
        扫描缓存并返回新发现的项目
        
        Args:
            callback: 可选的回调函数，每发现一个新项目时调用
            
        Returns:
            List[CacheItem]: 新发现的缓存项目列表
        """
        new_items = []
        
        try:
            # 首先验证基本路径
            if not self._validate_target_path():
                logger.warning("目标缓存路径无效或不存在")
                return new_items
            
            # 根据当前模式进行扫描
            if self.target_is_database:
                new_items = self._scan_database(callback)
            else:
                new_items = self._scan_file_system(callback)
                
            logger.info(f"缓存扫描完成，发现 {len(new_items)} 个新项目")
            
        except Exception as e:
            logger.error(f"缓存扫描失败: {e}")
            
        return new_items
    
    def _validate_target_path(self) -> bool:
        """验证目标路径是否有效"""
        if not self.target_path:
            return False
            
        if self.target_is_database:
            return os.path.isfile(self.target_path)
        else:
            return os.path.isdir(self.target_path)
    
    def _validate_database_integrity(self, conn: sqlite3.Connection) -> bool:
        """
        检测数据库完整性，确保必要的表存在
        
        Args:
            conn: SQLite连接对象
            
        Returns:
            bool: 数据库是否完整
        """
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            logger.debug(f"数据库完整性检测失败: {e}")
            return False
    
    def _fallback_to_temp_directory(self):
        """
        当数据库损坏或无法访问时回退到临时目录
        增强版本 - 更智能的路径检测和选择
        """
        if self._has_fallback_warned:
            return  # 避免重复处理
            
        # 记录原始路径
        original_path = self.target_path
        original_is_db = self.target_is_database
        
        # 候选临时路径列表（按优先级排序）
        temp_candidates = []
        
        if sys.platform == 'win32':
            temp_dir = os.environ.get('TEMP', '')
            localappdata = os.environ.get('LOCALAPPDATA', '')
            
            # 优先级1: 标准临时Roblox http目录
            if temp_dir:
                temp_candidates.append(os.path.join(temp_dir, 'Roblox', 'http'))
            
            # 优先级2: LocalAppData中的Roblox rbx-storage目录
            if localappdata:
                rbx_storage = os.path.join(localappdata, 'Roblox', 'rbx-storage')
                if os.path.exists(rbx_storage):
                    temp_candidates.append(rbx_storage)
            
            # 优先级3: UWP路径作为备用
            if localappdata:
                uwp_path = os.path.join(localappdata, 'Packages', 
                                      'ROBLOXCORPORATION.ROBLOX_55nm5eh3cm0pr', 
                                      'LocalState', 'http')
                if os.path.exists(uwp_path):
                    temp_candidates.append(uwp_path)
        
        # 尝试使用候选路径
        fallback_path = None
        for candidate in temp_candidates:
            if os.path.exists(candidate) and os.path.isdir(candidate):
                # 检查目录是否有文件
                try:
                    files = os.listdir(candidate)
                    if files:  # 如果目录不为空
                        fallback_path = candidate
                        break
                except (PermissionError, OSError):
                    continue
        
        if not fallback_path and temp_candidates:
            # 如果没有找到非空目录，使用第一个存在的目录
            for candidate in temp_candidates:
                if os.path.exists(candidate):
                    fallback_path = candidate
                    break
        
        # 应用回滚
        if fallback_path:
            self.target_path = fallback_path
            self.target_is_database = False
            self.db_folder = ""
            self._has_fallback_warned = True
            
            logger.warning(f"数据库损坏或无法访问，已自动回退到临时目录模式")
            logger.info(f"原始路径: {original_path} -> 回退路径: {fallback_path}")
            
            # 如果原本不是数据库模式，额外说明
            if not original_is_db:
                logger.info("已优化缓存路径选择")
        else:
            # 最后的备用方案
            if sys.platform == 'win32':
                temp_dir = os.environ.get('TEMP', '')
                if temp_dir:
                    backup_path = os.path.join(temp_dir, 'Roblox', 'http')
                    self.target_path = backup_path
                    self.target_is_database = False
                    self.db_folder = ""
                    self._has_fallback_warned = True
                    
                    logger.warning(f"无法找到有效的临时目录，使用默认备用路径: {backup_path}")
                    logger.info("注意: 此路径可能不存在文件，需要运行Roblox后重新尝试")
    
    def _scan_database(self, callback: Optional[Callable[[CacheItem], None]] = None) -> List[CacheItem]:
        """
        扫描SQLite数据库缓存
        
        Args:
            callback: 可选的回调函数
            
        Returns:
            List[CacheItem]: 新发现的缓存项目
        """
        new_items = []
        
        try:
            with sqlite3.connect(self.target_path, timeout=10.0) as conn:

                
                cursor = conn.cursor()
                cursor.execute("SELECT id, content FROM files")
                
                for row in cursor.fetchall():
                    try:
                        # 处理ID字段
                        if row[0] is not None:
                            if isinstance(row[0], bytes):
                                hash_id = row[0].hex().lower()
                            else:
                                hash_id = str(row[0]).lower()
                            

                            
                            cache_item = None
                            
                            # 检查是否有直接内容
                            if row[1] is not None:
                                # 有内容，直接使用
                                cache_item = CacheItem(
                                    path=hash_id,
                                    data=row[1],
                                    hash_id=hash_id,
                                    cache_type=CacheType.DATABASE
                                )
                            else:
                                # 没有内容，从文件夹获取
                                byte1 = hash_id[:2]
                                file_path = os.path.join(self.db_folder, byte1, hash_id)
                                
                                if os.path.exists(file_path):
                                    cache_item = CacheItem(
                                        path=file_path,
                                        data=None,
                                        hash_id=hash_id,
                                        cache_type=CacheType.FILE_SYSTEM
                                    )
                                else:
                                    logger.debug(f"无法找到哈希文件: {hash_id}")
                                    continue
                            
                            if cache_item:
                                new_items.append(cache_item)
                                if callback:
                                    callback(cache_item)
                                    
                    except Exception as e:
                        logger.error(f"处理数据库行时出错: {e}")
                        continue
                        
        except sqlite3.Error as e:
            logger.error(f"SQLite数据库访问失败: {e}")
                
        except Exception as e:
            logger.error(f"数据库扫描出错: {e}")
            
        return new_items
    
    def _scan_file_system(self, callback: Optional[Callable[[CacheItem], None]] = None) -> List[CacheItem]:
        """
        扫描文件系统缓存
        
        Args:
            callback: 可选的回调函数
            
        Returns:
            List[CacheItem]: 新发现的缓存项目
        """
        new_items = []
        
        try:
            if not os.path.isdir(self.target_path):
                logger.warning(f"目标目录不存在: {self.target_path}")
                return new_items
                
            for file_name in os.listdir(self.target_path):
                file_path = os.path.join(self.target_path, file_name)
                
                # 只处理文件，跳过目录
                if not os.path.isfile(file_path):
                    continue
                

                
                cache_item = CacheItem(
                    path=file_path,
                    data=None,
                    hash_id=file_name,
                    cache_type=CacheType.FILE_SYSTEM
                )
                
                new_items.append(cache_item)
                if callback:
                    callback(cache_item)
                    
        except Exception as e:
            logger.error(f"文件系统扫描出错: {e}")
            
        return new_items
    
    def clear_known_items(self):
        """清空已知项目缓存"""
        with self._lock:
            self.known_items.clear()
        logger.info("已清空已知项目缓存")
    
    def get_known_items_count(self) -> int:
        """获取已知项目数量"""
        with self._lock:
            return len(self.known_items)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存信息
        """
        return {
            "target_path": self.target_path,
            "target_is_database": self.target_is_database,
            "db_folder": self.db_folder,
            "path_exists": self._validate_target_path()
        }

# 全局扫描器实例
_scanner_instance = None

def get_scanner(log_callback: Optional[Callable[[str, str], None]] = None) -> RobloxCacheScanner:
    """获取全局扫描器实例"""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = RobloxCacheScanner(log_callback)
    return _scanner_instance

def scan_roblox_cache(callback: Optional[Callable[[CacheItem], None]] = None) -> List[CacheItem]:
    """
    扫描Roblox缓存的便捷函数
    
    Args:
        callback: 可选的回调函数
        
    Returns:
        List[CacheItem]: 新发现的缓存项目
    """
    return get_scanner().scan_cache(callback)

 