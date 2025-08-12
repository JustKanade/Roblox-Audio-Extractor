#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RBXH缓存格式解析器 - 实现Roblox缓存文件解析功能
RBXH Cache Format Parser - Implements Roblox cache file parsing functionality
"""

import os
import struct
import logging
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParsedCache:
    """解析后的缓存数据结构"""
    success: bool = False
    link: str = ""
    content: bytes = b""
    error_message: str = ""

class RBXHParser:
    """RBXH格式解析器"""
    
    def __init__(self):
        self.known_links = set()  # 用于跟踪已知链接，避免重复处理
    
    def parse_cache_file(self, file_path: str) -> ParsedCache:
        """
        解析RBXH缓存文件
        
        Args:
            file_path: 缓存文件路径
            
        Returns:
            ParsedCache: 解析结果
        """
        try:
            if not os.path.exists(file_path):
                return ParsedCache(success=False, error_message=f"文件不存在: {file_path}")
            
            with open(file_path, 'rb') as f:
                return self._parse_rbxh_stream(f)
                
        except Exception as e:
            logger.error(f"解析缓存文件失败 {file_path}: {e}")
            return ParsedCache(success=False, error_message=str(e))
    
    def parse_cache_data(self, data: bytes) -> ParsedCache:
        """
        解析RBXH缓存数据
        
        Args:
            data: 缓存数据字节
            
        Returns:
            ParsedCache: 解析结果
        """
        try:
            import io
            stream = io.BytesIO(data)
            return self._parse_rbxh_stream(stream)
            
        except Exception as e:
            logger.error(f"解析缓存数据失败: {e}")
            return ParsedCache(success=False, error_message=str(e))
    
    def _parse_rbxh_stream(self, stream) -> ParsedCache:
        """
        解析RBXH数据流
        
        Args:
            stream: 二进制数据流
            
        Returns:
            ParsedCache: 解析结果
        """
        try:
            # 读取魔术头 (4字节)
            magic = stream.read(4)
            if magic != b'RBXH':
                logger.debug(f"非RBXH格式，魔术头: {magic}")
                return ParsedCache(success=False, error_message=f"非RBXH格式，魔术头: {magic}")
            
            # 跳过头部大小 (4字节)
            stream.read(4)
            
            # 读取链接长度 (4字节)
            link_len_bytes = stream.read(4)
            if len(link_len_bytes) != 4:
                return ParsedCache(success=False, error_message="文件截断：无法读取链接长度")
            
            link_len = struct.unpack('<I', link_len_bytes)[0]  # 小端序
            
            # 读取链接
            if link_len > 0:
                link_bytes = stream.read(link_len)
                if len(link_bytes) != link_len:
                    return ParsedCache(success=False, error_message="文件截断：无法读取完整链接")
                
                try:
                    link = link_bytes.decode('utf-8')
                except UnicodeDecodeError:
                    link = link_bytes.decode('utf-8', errors='ignore')
            else:
                link = ""
            
            # 检查重复链接
            if link in self.known_links:
                logger.debug(f"跳过重复链接: {link}")
                return ParsedCache(success=False, error_message="重复链接")
            
            # 跳过流氓字节 (1字节)
            stream.read(1)
            
            # 读取状态码 (4字节)
            status_bytes = stream.read(4)
            if len(status_bytes) != 4:
                return ParsedCache(success=False, error_message="文件截断：无法读取状态码")
            
            status = struct.unpack('<I', status_bytes)[0]
            
            # 检查状态码
            if status >= 300:
                logger.debug(f"非成功状态码: {status}")
                return ParsedCache(success=False, error_message=f"非成功状态码: {status}")
            
            # 读取头部长度 (4字节)
            header_len_bytes = stream.read(4)
            if len(header_len_bytes) != 4:
                return ParsedCache(success=False, error_message="文件截断：无法读取头部长度")
            
            header_len = struct.unpack('<I', header_len_bytes)[0]
            
            # 跳过XXHash摘要 (4字节)
            stream.read(4)
            
            # 读取内容长度 (4字节)
            content_len_bytes = stream.read(4)
            if len(content_len_bytes) != 4:
                return ParsedCache(success=False, error_message="文件截断：无法读取内容长度")
            
            content_len = struct.unpack('<I', content_len_bytes)[0]
            
            # 跳过XXHash摘要、保留字节和头部 (8 + header_len字节)
            skip_bytes = 8 + header_len
            stream.read(skip_bytes)
            
            # 读取内容
            if content_len > 0:
                content = stream.read(content_len)
                if len(content) != content_len:
                    return ParsedCache(success=False, error_message="文件截断：无法读取完整内容")
            else:
                content = b""
            
            # 记录已知链接
            if link:
                self.known_links.add(link)
            
            logger.debug(f"成功解析RBXH缓存，链接: {link}, 内容长度: {len(content)}")
            
            return ParsedCache(
                success=True,
                link=link,
                content=content
            )
            
        except Exception as e:
            logger.error(f"解析RBXH流失败: {e}")
            return ParsedCache(success=False, error_message=str(e))
    
    def clear_known_links(self):
        """清空已知链接缓存"""
        self.known_links.clear()
    
    def get_known_links_count(self) -> int:
        """获取已知链接数量"""
        return len(self.known_links)

# 全局解析器实例
_parser_instance = None

def get_parser() -> RBXHParser:
    """获取全局解析器实例"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = RBXHParser()
    return _parser_instance

def parse_cache_file(file_path: str) -> ParsedCache:
    """
    解析RBXH缓存文件的便捷函数
    
    Args:
        file_path: 缓存文件路径
        
    Returns:
        ParsedCache: 解析结果
    """
    return get_parser().parse_cache_file(file_path)

def parse_cache_data(data: bytes) -> ParsedCache:
    """
    解析RBXH缓存数据的便捷函数
    
    Args:
        data: 缓存数据字节
        
    Returns:
        ParsedCache: 解析结果
    """
    return get_parser().parse_cache_data(data) 