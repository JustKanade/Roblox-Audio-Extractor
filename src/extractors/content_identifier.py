#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容识别器 - 实现Roblox内容识别功能
Content Identifier - Implements Roblox content identification functionality
"""

import struct
import logging
from enum import Enum, auto
from typing import Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class AssetType(Enum):
    """资源类型枚举"""
    Unknown = auto()
    Ignored = auto()
    NoConvert = auto()
    Mesh = auto()
    Khronos = auto()
    EXTM3U = auto()
    Translation = auto()
    FontList = auto()
    WebP = auto()

@dataclass
class IdentifiedContent:
    """识别的内容信息"""
    asset_type: AssetType
    extension: str
    type_name: str
    category: str
    
    def __init__(self, asset_type: AssetType, extension: str = "", type_name: str = "", category: str = ""):
        self.asset_type = asset_type
        self.extension = extension
        self.type_name = type_name
        self.category = category

class ContentIdentifier:
    """内容识别器 - 识别Roblox内容类型"""
    
    def __init__(self, block_avatar_images: bool = True):
        """
        初始化内容识别器
        
        Args:
            block_avatar_images: 是否阻止头像图片
        """
        self.block_avatar_images = block_avatar_images
    
    def identify_content(self, content: bytes) -> IdentifiedContent:
        """
        识别内容类型
        
        Args:
            content: 内容字节数据
            
        Returns:
            IdentifiedContent: 识别结果
        """
        if len(content) == 0:
            return IdentifiedContent(AssetType.Unknown, "", "empty content", "")
        
        # 获取内容开头部分用于匹配
        begin_size = min(48, len(content) - 1) if len(content) > 1 else len(content)
        begin = content[:begin_size].decode('utf-8', errors='ignore')
        
        # 获取魔术字节
        magic = struct.unpack('<I', content[:4])[0] if len(content) >= 4 else 0
        
        # 按照Roblox内容格式进行识别
        return self._match_content_type(begin, content, magic)
    
    def _match_content_type(self, begin: str, content: bytes, magic: int) -> IdentifiedContent:
        """
        匹配内容类型
        
        Args:
            begin: 内容开头字符串
            content: 完整内容字节
            magic: 魔术字节
            
        Returns:
            IdentifiedContent: 识别结果
        """
        # Roblox模型文件
        if "<roblox!" in begin:
            return IdentifiedContent(AssetType.NoConvert, "rbxm", "RBXM", "RBXM")
        
        # 不支持的XML格式
        if "<roblox xml" in begin:
            return IdentifiedContent(AssetType.Ignored, "", "unsupported XML", "")
        
        # 网格文件
        if not begin.startswith("\"version") and begin.startswith("version"):
            return IdentifiedContent(AssetType.Mesh, "", "", "")
        
        # 翻译列表JSON（忽略）
        if begin.startswith("{\"translations"):
            return IdentifiedContent(AssetType.Ignored, "", "translation list JSON", "")
        
        # 翻译文件
        if "{\"locale\":\"" in begin:
            return IdentifiedContent(AssetType.Translation, "", "", "")
        
        # PNG图片
        if "PNG\r\n" in begin:
            return IdentifiedContent(AssetType.NoConvert, "png", "PNG", "Textures")
        
        # GIF图片
        if begin.startswith("GIF87a") or begin.startswith("GIF89a"):
            return IdentifiedContent(AssetType.NoConvert, "gif", "GIF", "Textures")
        
        # JPEG图片
        if "JFIF" in begin or "Exif" in begin:
            return IdentifiedContent(AssetType.NoConvert, "jfif", "JFIF", "Textures")
        
        # WebP图片
        if begin.startswith("RIFF") and "WEBP" in begin:
            if self.block_avatar_images:
                return IdentifiedContent(AssetType.WebP, "webp", "WebP", "Textures")
            else:
                return IdentifiedContent(AssetType.NoConvert, "webp", "WebP", "Textures")
        
        # OGG音频
        if begin.startswith("OggS"):
            return IdentifiedContent(AssetType.NoConvert, "ogg", "OGG", "Sounds")
        
        # MP3音频
        if (begin.startswith("ID3") or 
            (len(content) > 2 and (content[0] & 0xFF) == 0xFF and (content[1] & 0xE0) == 0xE0)):
            return IdentifiedContent(AssetType.NoConvert, "mp3", "MP3", "Sounds")
        
        # KTX纹理
        if "KTX 11" in begin:
            return IdentifiedContent(AssetType.Khronos, "", "", "")
        
        # M3U播放列表
        if begin.startswith("#EXTM3U"):
            return IdentifiedContent(AssetType.EXTM3U, "", "", "")
        
        # 字体列表 - 这是我们主要关注的类型
        if "\"name\": \"" in begin:
            return IdentifiedContent(AssetType.FontList, "", "", "")
        
        # 应用程序设置JSON（忽略）
        if "{\"applicationSettings" in begin:
            return IdentifiedContent(AssetType.Ignored, "", "FFlags JSON", "")
        
        # 客户端版本JSON（忽略）
        if "{\"version" in begin:
            return IdentifiedContent(AssetType.Ignored, "", "client version JSON", "")
        
        # OpenType/TrueType字体（忽略）
        if "GDEF" in begin or "GPOS" in begin or "GSUB" in begin:
            return IdentifiedContent(AssetType.Ignored, "", "OpenType/TrueType font", "")
        
        # Zstandard压缩数据（可能是FFlags）
        if magic == 0xFD2FB528:
            return IdentifiedContent(AssetType.Ignored, "", "Zstandard compressed data (likely FFlags)", "")
        
        # VideoFrame段
        if (len(content) >= 4 and content[0] == 0x1A and content[1] == 0x45 and 
            content[2] == 0xDF and content[3] == 0xA3):
            return IdentifiedContent(AssetType.Ignored, "", "VideoFrame segment", "")
        
        # 未知类型
        return IdentifiedContent(AssetType.Unknown, begin, "", "")
    
    def is_fontlist(self, content: bytes) -> bool:
        """
        快速检查是否为字体列表
        
        Args:
            content: 内容字节数据
            
        Returns:
            bool: 是否为字体列表
        """
        try:
            # 检查是否包含字体列表的关键标识
            text_content = content.decode('utf-8', errors='ignore')
            return ('"name": "' in text_content and 
                    '"faces":' in text_content)
        except Exception:
            return False
    
    def get_texture_format(self, internal_format: int) -> str:
        """
        检测纹理格式
        
        Args:
            internal_format: 内部格式代码
            
        Returns:
            str: 纹理格式名称
        """
        if ((internal_format >= 0x1900 and internal_format <= 0x1908) or
            (internal_format & 0xFF00) == 0x8200):
            return "Uncompressed"
        elif ((internal_format & 0xFF00) == 0x8300 or
              (internal_format & 0xFF00) == 0x8D00 or
              (internal_format & 0xFF00) == 0x8E00):
            return "BCn"
        elif ((internal_format & 0xFF00) == 0x9200 or
              (internal_format & 0xFF00) == 0x9300):
            return "ASTC"
        else:
            return "Unknown"

# 全局识别器实例
_identifier_instance = None

def get_identifier(block_avatar_images: bool = True) -> ContentIdentifier:
    """获取全局识别器实例"""
    global _identifier_instance
    if _identifier_instance is None:
        _identifier_instance = ContentIdentifier(block_avatar_images)
    return _identifier_instance

def identify_content(content: bytes, block_avatar_images: bool = True) -> IdentifiedContent:
    """
    识别内容类型的便捷函数
    
    Args:
        content: 内容字节数据
        block_avatar_images: 是否阻止头像图片
        
    Returns:
        IdentifiedContent: 识别结果
    """
    return get_identifier(block_avatar_images).identify_content(content) 