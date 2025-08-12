#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史管理模块 - 管理提取历史，避免重复处理文件
History Manager Module - Manages extraction history to avoid duplicate processing
"""

import os
import json
import hashlib
import logging
import threading
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)


class ExtractedHistory:
    """管理提取历史，避免重复处理文件"""

    def __init__(self, history_file: str):
        """初始化提取历史"""
        self.history_file = history_file
        # 不同类型资源的哈希集合
        self.history_records = {
            'audio': {'file_hashes': set(), 'content_hashes': set()},
            'font': {'file_hashes': set(), 'content_hashes': set()},  # 新增字体类型
            'image': {'file_hashes': set(), 'content_hashes': set()},
            'texture': {'file_hashes': set(), 'content_hashes': set()},
            'model': {'file_hashes': set(), 'content_hashes': set()},
            'other': {'file_hashes': set(), 'content_hashes': set()}
        }
        # 向后兼容的属性
        self.file_hashes = set()  
        self.content_hashes = set() 
        
        self.modified = False  # 跟踪是否修改过，避免不必要的保存
        self._lock = threading.Lock()  # 添加锁以保证线程安全
        self.load_history()

    def load_history(self) -> None:
        """从JSON文件加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    with self._lock:
                        # 尝试加载新格式的历史记录
                        if 'records' in data:
                            for record_type, record_data in data['records'].items():
                                if record_type in self.history_records:
                                    self.history_records[record_type]['file_hashes'] = set(record_data.get('file_hashes', []))
                                    self.history_records[record_type]['content_hashes'] = set(record_data.get('content_hashes', []))
                            
                            # 更新向后兼容的属性
                            self._update_legacy_attributes()
                            
                        # 尝试加载旧格式的历史记录并转换为新格式
                        else:
                            # 处理旧版格式
                            file_hashes = set(data.get('hashes', []))
                            content_hashes = set(data.get('content_hashes', []))
                            
                            # 将旧数据迁移到音频类别
                            self.history_records['audio']['file_hashes'] = file_hashes
                            self.history_records['audio']['content_hashes'] = content_hashes
                            
                            # 更新向后兼容的属性
                            self.file_hashes = file_hashes
                            self.content_hashes = content_hashes
                            
                            # 标记为已修改，以便保存为新格式
                            self.modified = True
                            
                logger.info(f"History loaded successfully with {self.get_history_size()} total records")
        except Exception as e:
            logger.error(f"Error loading history: {str(e)}")
            # 初始化空历史记录
            with self._lock:
                for record_type in self.history_records:
                    self.history_records[record_type]['file_hashes'] = set()
                    self.history_records[record_type]['content_hashes'] = set()
                self.file_hashes = set()
                self.content_hashes = set()

    def _update_legacy_attributes(self):
        """更新向后兼容的属性"""
        # 主要从音频记录更新兼容属性
        self.file_hashes = self.history_records['audio']['file_hashes'].copy()
        self.content_hashes = self.history_records['audio']['content_hashes'].copy()

    def save_history(self) -> None:
        """将历史记录保存到JSON文件"""
        with self._lock:
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

                # 准备新格式的数据
                records_data = {}
                total_files = 0
                total_contents = 0
                
                for record_type, record_data in self.history_records.items():
                    file_hashes = list(record_data['file_hashes'])
                    content_hashes = list(record_data['content_hashes'])
                    
                    if file_hashes or content_hashes:
                        records_data[record_type] = {
                            'file_hashes': file_hashes,
                            'content_hashes': content_hashes
                        }
                        total_files += len(file_hashes)
                        total_contents += len(content_hashes)

                # 保存历史记录，使用新格式
                with open(self.history_file, 'w') as f:
                    json.dump({
                        'records': records_data,
                        # 兼容旧版，保留原字段
                        'hashes': list(self.file_hashes),
                        'content_hashes': list(self.content_hashes)
                    }, f)
                    
                self.modified = False
                logger.info(f"History saved: {total_files} files recorded, {total_contents} unique content hashes")
            except Exception as e:
                logger.error(f"Error saving history: {str(e)}")

    def add_hash(self, file_hash: str, record_type: str = 'audio') -> None:
        """添加文件哈希到历史记录
        
        Args:
            file_hash: 文件哈希值
            record_type: 记录类型，默认为'audio'
        """
        with self._lock:
            record_type = record_type.lower()
            if record_type not in self.history_records:
                record_type = 'other'
                
            if file_hash not in self.history_records[record_type]['file_hashes']:
                self.history_records[record_type]['file_hashes'].add(file_hash)
                
                # 提取内容哈希部分
                parts = file_hash.split('_')
                if len(parts) > 1:
                    self.history_records[record_type]['content_hashes'].add(parts[0])
                    
                self.modified = True
                
                # 如果是音频类型，更新兼容属性
                if record_type == 'audio':
                    self.file_hashes.add(file_hash)
                    if len(parts) > 1:
                        self.content_hashes.add(parts[0])

    def is_processed(self, file_hash: str, record_type: str = 'audio') -> bool:
        """检查文件是否已处理
        
        Args:
            file_hash: 文件哈希值
            record_type: 记录类型，默认为'audio'
        """
        with self._lock:
            record_type = record_type.lower()
            if record_type not in self.history_records:
                record_type = 'other'
                
            return file_hash in self.history_records[record_type]['file_hashes']

    def is_content_processed(self, content_hash: str, record_type: str = 'audio') -> bool:
        """检查内容哈希是否已处理
        
        Args:
            content_hash: 内容哈希值
            record_type: 记录类型，默认为'audio'
        """
        with self._lock:
            record_type = record_type.lower()
            if record_type not in self.history_records:
                record_type = 'other'
                
            return content_hash in self.history_records[record_type]['content_hashes']

    def clear_history(self, record_type: Optional[str] = None) -> None:
        """清除提取历史
        
        Args:
            record_type: 要清除的记录类型，如果为None则清除所有记录
        """
        with self._lock:
            try:
                if record_type is None or record_type == "all":
                    # 清空所有记录
                    for rec_type in self.history_records:
                        self.history_records[rec_type]['file_hashes'] = set()
                        self.history_records[rec_type]['content_hashes'] = set()
                        
                    # 更新兼容属性
                    self.file_hashes = set()
                    self.content_hashes = set()
                    # 记录日志
                    logger.info("History cleared: all")
                else:
                    # 确保 record_type 是字符串
                    record_type_str = str(record_type).lower()
                    if record_type_str in self.history_records:
                        # 清空特定类型的记录
                        self.history_records[record_type_str]['file_hashes'] = set()
                        self.history_records[record_type_str]['content_hashes'] = set()
                        
                        # 如果清除的是音频，也更新兼容属性
                        if record_type_str == 'audio':
                            self.file_hashes = set()
                            self.content_hashes = set()
                    
                    # 记录日志
                    logger.info(f"History cleared: {record_type_str}")
                
                self.modified = True
                
                # 确保目录存在
                os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

                # 准备保存的数据
                records_data = {}
                for rec_type, rec_data in self.history_records.items():
                    if rec_data['file_hashes'] or rec_data['content_hashes']:
                        records_data[rec_type] = {
                            'file_hashes': list(rec_data['file_hashes']),
                            'content_hashes': list(rec_data['content_hashes'])
                        }

                # 写入历史记录文件
                with open(self.history_file, 'w') as f:
                    json.dump({
                        'records': records_data,
                        'hashes': list(self.file_hashes),
                        'content_hashes': list(self.content_hashes)
                    }, f)
            except Exception as e:
                logger.error(f"Error clearing history: {str(e)}")
                raise

    def get_history_size(self, record_type: Optional[str] = None) -> int:
        """获取历史记录中的文件数量
        
        Args:
            record_type: 记录类型，如果为None则返回所有记录数量
        """
        with self._lock:
            if record_type is None:
                # 返回所有记录的总数
                total = 0
                for rec_type in self.history_records:
                    total += len(self.history_records[rec_type]['file_hashes'])
                return total
            else:
                record_type = record_type.lower()
                if record_type in self.history_records:
                    return len(self.history_records[record_type]['file_hashes'])
                return 0
                
    def get_content_hash_count(self, record_type: Optional[str] = None) -> int:
        """获取内容哈希的数量
        
        Args:
            record_type: 记录类型，如果为None则返回所有内容哈希数量
        """
        with self._lock:
            if record_type is None:
                # 返回所有内容哈希的总数
                total = 0
                for rec_type in self.history_records:
                    total += len(self.history_records[rec_type]['content_hashes'])
                return total
            else:
                record_type = record_type.lower()
                if record_type in self.history_records:
                    return len(self.history_records[record_type]['content_hashes'])
                return 0
                
    def get_record_types(self) -> list:
        """获取所有记录类型"""
        return list(self.history_records.keys())


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