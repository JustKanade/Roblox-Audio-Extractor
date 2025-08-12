#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取器模块 - 包含音频和字体提取功能
Extractors Module - Contains audio and font extraction functionality
"""

# 导出音频提取器
from .audio_extractor import (
    RobloxAudioExtractor,
    ClassificationMethod as AudioClassificationMethod,
    ProcessingStats as AudioProcessingStats,
    ContentHashCache as AudioContentHashCache,
    ExtractedHistory as AudioExtractedHistory
)

# 导出Roblox字体提取器及相关组件
from .font_extractor import (
    RobloxFontExtractor,
    FontClassificationMethod,
    FontProcessingStats,
    FontListProcessor,
    extract_roblox_fonts
)

# 导出RBXH解析器
from .rbxh_parser import (
    RBXHParser,
    ParsedCache,
    parse_cache_file,
    parse_cache_data,
    get_parser
)

# 导出内容识别器
from .content_identifier import (
    ContentIdentifier,
    AssetType,
    IdentifiedContent,
    identify_content,
    get_identifier
)

# 导出缓存扫描器
from .cache_scanner import (
    RobloxCacheScanner,
    CacheItem,
    CacheType,
    scan_roblox_cache,
    get_scanner
)

# 为了兼容性，保持原有的导出
__all__ = [
    # 音频提取器
    'RobloxAudioExtractor',
    'AudioClassificationMethod',
    'AudioProcessingStats', 
    'AudioContentHashCache',
    'AudioExtractedHistory',
    
    # Roblox字体提取器
    'RobloxFontExtractor',
    'FontClassificationMethod',
    'FontProcessingStats',
    'FontListProcessor',
    'extract_roblox_fonts',
    
    # RBXH解析器
    'RBXHParser',
    'ParsedCache',
    'parse_cache_file',
    'parse_cache_data',
    'get_parser',
    
    # 内容识别器
    'ContentIdentifier',
    'AssetType',
    'IdentifiedContent', 
    'identify_content',
    'get_identifier',
    
    # 缓存扫描器
    'RobloxCacheScanner',
    'CacheItem',
    'CacheType',
    'scan_roblox_cache',
    'get_scanner'
] 