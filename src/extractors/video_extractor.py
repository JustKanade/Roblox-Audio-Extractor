#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频提取器模块 - 提供从Roblox缓存中提取视频的功能
Video Extractor Module - Provides functionality for extracting videos from Roblox cache
"""

import os
import re
import json
import requests
import hashlib
import logging
import threading
import queue
import time
import traceback
import multiprocessing
import subprocess
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum, auto
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

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

class VideoClassificationMethod(Enum):
    """视频分类方法枚举"""
    RESOLUTION = auto()    # 按分辨率分类
    SIZE = auto()         # 按文件大小分类  
    DURATION = auto()     # 按时长分类
    NONE = auto()         # 无分类

class VideoQualityPreference(Enum):
    """视频质量偏好枚举"""
    AUTO = auto()         # 自动选择最佳质量
    P1080 = auto()        # 1080p优先
    P720 = auto()         # 720p优先
    P480 = auto()         # 480p优先
    LOWEST = auto()       # 最低质量

class VideoProcessingStats:
    """视频处理统计类 - 线程安全"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.stats = {
            'processed_videos': 0,
            'downloaded_segments': 0,
            'merged_videos': 0,
            'duplicate_videos': 0,
            'already_processed': 0,
            'error_videos': 0,
            'download_failures': 0,
            'merge_failures': 0
        }
    
    def increment(self, stat_name: str, count: int = 1):
        """线程安全地增加统计计数"""
        with self._lock:
            if stat_name in self.stats:
                self.stats[stat_name] += count
    
    def get(self, stat_name: str) -> int:
        """获取统计值"""
        with self._lock:
            return self.stats.get(stat_name, 0)
    
    def get_all(self) -> Dict[str, int]:
        """获取所有统计信息的副本"""
        with self._lock:
            return self.stats.copy()

class VideoProcessor:
    """视频处理器 - 处理Roblox视频文件"""
    
    def __init__(self, output_dir: str, classification_method: VideoClassificationMethod = VideoClassificationMethod.RESOLUTION,
                 ffmpeg_path: str = None, max_retries: int = 3, segment_timeout: int = 30,
                 quality_preference: VideoQualityPreference = VideoQualityPreference.AUTO,
                 timestamp_repair: bool = True):
        """
        初始化视频处理器
        
        Args:
            output_dir: 输出目录
            classification_method: 分类方法
            ffmpeg_path: FFmpeg可执行文件路径
            max_retries: 最大重试次数
            segment_timeout: 片段下载超时时间（秒）
        """
        self.output_dir = output_dir
        self.classification_method = classification_method
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()
        self.max_retries = max_retries
        self.segment_timeout = segment_timeout
        self.quality_preference = quality_preference
        self.timestamp_repair = timestamp_repair
        self.session = requests.Session()
        self._cancel_check_fn = None
        
        # 设置请求会话
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def _find_ffmpeg(self) -> Optional[str]:
        """查找FFmpeg可执行文件"""
        import shutil
        return shutil.which('ffmpeg')
    
    def set_cancel_check_function(self, cancel_check_fn: Callable[[], bool]):
        """设置取消检查函数"""
        self._cancel_check_fn = cancel_check_fn
    
    def is_cancelled(self) -> bool:
        """检查是否被取消"""
        if self._cancel_check_fn:
            return self._cancel_check_fn()
        return False
    
    def _parse_m3u8_playlist(self, content: str) -> Tuple[str, str, str]:
        """
        解析M3U8播放列表，根据质量偏好选择合适的流
        
        Args:
            content: M3U8内容
            
        Returns:
            Tuple[stream_url, resolution, base_uri]: 选择的流URL，分辨率，基础URI
        """
        lines = content.strip().split('\n')
        base_uri = ""
        streams = []  # 存储所有可用流: (bandwidth, resolution, stream_url)
        pending_stream = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('#EXT-X-DEFINE:'):
                # 解析基础URI定义
                if 'NAME="RBX-BASE-URI"' in line:
                    match = re.search(r'VALUE="([^"]*)"', line)
                    if match:
                        base_uri = match.group(1)
            elif line.startswith('#EXT-X-STREAM-INF:'):
                # 解析流信息
                bandwidth_match = re.search(r'BANDWIDTH=(\d+)', line)
                resolution_match = re.search(r'RESOLUTION=([^,\s]+)', line)
                
                if bandwidth_match:
                    bandwidth = int(bandwidth_match.group(1))
                    resolution = resolution_match.group(1) if resolution_match else "Unknown"
                    pending_stream = (bandwidth, resolution)
            elif pending_stream and not line.startswith('#'):
                stream_url = line.replace('{$RBX-BASE-URI}', base_uri)
                streams.append((pending_stream[0], pending_stream[1], stream_url))
                pending_stream = None
        
        if not streams:
            return "", "", base_uri
        
        # 根据质量偏好选择流
        selected_stream = self._select_stream_by_quality(streams)
        
        return selected_stream[2], selected_stream[1], base_uri
    
    def _select_stream_by_quality(self, streams: List[Tuple[int, str, str]]) -> Tuple[int, str, str]:
        """
        根据质量偏好选择流
        
        Args:
            streams: 可用流列表 [(bandwidth, resolution, url), ...]
            
        Returns:
            Tuple[bandwidth, resolution, url]: 选择的流
        """
        if not streams:
            return (0, "Unknown", "")
        
        # 按带宽排序（高到低）
        streams_sorted = sorted(streams, key=lambda x: x[0], reverse=True)
        
        if self.quality_preference == VideoQualityPreference.AUTO:
            # 自动选择最高质量
            return streams_sorted[0]
        elif self.quality_preference == VideoQualityPreference.LOWEST:
            # 选择最低质量
            return streams_sorted[-1]
        else:
            # 根据指定分辨率选择
            target_heights = {
                VideoQualityPreference.P1080: 1080,
                VideoQualityPreference.P720: 720,
                VideoQualityPreference.P480: 480
            }
            
            target_height = target_heights.get(self.quality_preference, 1080)
            
            # 寻找最接近目标分辨率的流
            best_stream = streams_sorted[0]  # 默认选择最高质量
            min_diff = float('inf')
            
            for bandwidth, resolution, url in streams:
                # 尝试从分辨率字符串中提取高度（如"1920x1080"）
                height_match = re.search(r'x(\d+)', resolution)
                if height_match:
                    height = int(height_match.group(1))
                    diff = abs(height - target_height)
                    
                    # 如果找到完全匹配或更接近的分辨率
                    if diff < min_diff or (height <= target_height and diff <= min_diff):
                        min_diff = diff
                        best_stream = (bandwidth, resolution, url)
            
            return best_stream
    
    def _download_segment_playlist(self, stream_url: str) -> List[str]:
        """
        下载片段播放列表
        
        Args:
            stream_url: 流URL
            
        Returns:
            List[str]: 片段文件名列表
        """
        try:
            response = self.session.get(stream_url, timeout=self.segment_timeout)
            response.raise_for_status()
            
            content = response.text
            segments = []
            next_is_segment = False
            
            for line in content.split('\n'):
                line = line.strip()
                if next_is_segment and line and not line.startswith('#'):
                    segments.append(line)
                    next_is_segment = False
                elif line.startswith('#EXTINF:'):
                    next_is_segment = True
            
            return segments
            
        except Exception as e:
            logger.error(f"下载片段播放列表失败: {e}")
            return []
    
    def _download_video_segment(self, segment_url: str, output_path: str) -> bool:
        """
        下载视频片段
        
        Args:
            segment_url: 片段URL
            output_path: 输出路径
            
        Returns:
            bool: 是否下载成功
        """
        for attempt in range(self.max_retries):
            if self.is_cancelled():
                return False
                
            try:
                response = self.session.get(segment_url, timeout=self.segment_timeout, stream=True)
                response.raise_for_status()
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.is_cancelled():
                            return False
                        if chunk:
                            f.write(chunk)
                
                return True
                
            except Exception as e:
                logger.warning(f"片段下载失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)  # 重试前等待
        
        return False
    
    def _repair_video_segment(self, input_path: str, output_path: str) -> bool:
        """
        修复视频片段时间戳
        
        Args:
            input_path: 输入路径
            output_path: 输出路径
            
        Returns:
            bool: 是否修复成功
        """
        if not self.ffmpeg_path:
            logger.error("FFmpeg未找到，无法修复视频片段")
            return False
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-c', 'copy',
                '-bsf:v', 'setts=ts=PTS-STARTPTS',
                output_path,
                '-y'  # 覆盖输出文件
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return True
            else:
                logger.error(f"FFmpeg修复失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg修复超时")
            return False
        except Exception as e:
            logger.error(f"FFmpeg修复出错: {e}")
            return False
    
    def _merge_video_segments(self, segment_list_file: str, output_path: str) -> bool:
        """
        合并视频片段
        
        Args:
            segment_list_file: 片段列表文件路径
            output_path: 输出视频路径
            
        Returns:
            bool: 是否合并成功
        """
        if not self.ffmpeg_path:
            logger.error("FFmpeg未找到，无法合并视频片段")
            return False
        
        try:
            cmd = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', segment_list_file,
                '-c', 'copy',
                output_path,
                '-y'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return True
            else:
                logger.error(f"视频合并失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("视频合并超时")
            return False
        except Exception as e:
            logger.error(f"视频合并出错: {e}")
            return False
    
    def _get_output_directory(self, resolution: str) -> str:
        """
        根据分类方法获取输出目录
        
        Args:
            resolution: 视频分辨率
            
        Returns:
            str: 输出目录路径
        """
        base_dir = os.path.join(self.output_dir, "Videos")
        
        if self.classification_method == VideoClassificationMethod.RESOLUTION:
            if resolution and resolution != "Unknown":
                # 提取分辨率高度部分，如 "1920x1080" -> "1080p"
                match = re.search(r'x(\d+)', resolution)
                if match:
                    height = match.group(1)
                    return os.path.join(base_dir, f"{height}p")
                else:
                    return os.path.join(base_dir, resolution)
            else:
                return os.path.join(base_dir, "Unknown_Resolution")
        elif self.classification_method == VideoClassificationMethod.NONE:
            return base_dir
        else:
            # 其他分类方法暂时使用默认目录
            return base_dir
    
    def process_m3u8_content(self, content: str, video_hash: str, stats: VideoProcessingStats) -> bool:
        """
        处理M3U8播放列表内容
        
        Args:
            content: M3U8内容
            video_hash: 视频哈希
            stats: 统计对象
            
        Returns:
            bool: 是否处理成功
        """
        try:
            # 检查是否包含RBX-BASE-URI标识
            if "RBX-BASE-URI" not in content:
                logger.debug("忽略非Roblox视频播放列表")
                return False
            
            # 解析播放列表
            stream_url, resolution, base_uri = self._parse_m3u8_playlist(content)
            
            if not stream_url:
                logger.error("未找到有效的视频流URL")
                return False
            
            logger.info(f"处理视频: {video_hash}, 分辨率: {resolution}")
            
            # 获取输出目录
            output_dir = self._get_output_directory(resolution)
            os.makedirs(output_dir, exist_ok=True)
            
            final_video_path = os.path.join(output_dir, f"{video_hash}.webm")
            
            # 检查文件是否已存在
            if os.path.exists(final_video_path):
                logger.debug(f"视频已存在，跳过: {final_video_path}")
                stats.increment('duplicate_videos')
                return True
            
            # 下载片段播放列表
            segments = self._download_segment_playlist(stream_url)
            if not segments:
                logger.error("无法获取视频片段列表")
                stats.increment('download_failures')
                return False
            
            # 创建临时目录
            temp_dir = os.path.join(self.output_dir, "temp", f"VideoFrame-{video_hash}")
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # 下载和修复所有片段
                segment_base_url = stream_url.rsplit('/', 1)[0] + '/'
                repaired_segments = []
                
                for i, segment in enumerate(segments):
                    if self.is_cancelled():
                        return False
                    
                    segment_url = urljoin(segment_base_url, segment)
                    segment_path = os.path.join(temp_dir, segment)
                    repaired_path = os.path.join(temp_dir, segment.replace('.webm', '-repaired.webm'))
                    
                    logger.info(f"下载片段 {i+1}/{len(segments)}: {segment}")
                    
                    # 下载片段
                    if self._download_video_segment(segment_url, segment_path):
                        stats.increment('downloaded_segments')
                        
                        # 根据设置决定是否修复片段
                        if self.timestamp_repair and self.ffmpeg_path:
                            # 修复片段时间戳
                            logger.info(f"修复视频片段: {segment}")
                            if self._repair_video_segment(segment_path, repaired_path):
                                repaired_segments.append(f"file '{os.path.basename(repaired_path)}'")
                                # 删除原始片段
                                try:
                                    os.remove(segment_path)
                                except:
                                    pass
                            else:
                                logger.error(f"片段修复失败: {segment}")
                                stats.increment('error_videos')
                                return False
                        else:
                            # 不修复，直接使用原始片段
                            repaired_segments.append(f"file '{os.path.basename(segment_path)}'")
                            # 重命名为repaired_path以保持一致性
                            try:
                                os.rename(segment_path, repaired_path)
                            except:
                                pass
                    else:
                        logger.error(f"片段下载失败: {segment}")
                        stats.increment('download_failures')
                        return False
                
                if self.is_cancelled():
                    return False
                
                # 创建片段列表文件
                segment_list_file = os.path.join(temp_dir, "videos.txt")
                with open(segment_list_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(repaired_segments))
                
                # 合并视频片段
                logger.info(f"合并视频片段: {video_hash}")
                if self._merge_video_segments(segment_list_file, final_video_path):
                    stats.increment('merged_videos')
                    stats.increment('processed_videos')
                    logger.info(f"视频处理成功: {final_video_path}")
                    return True
                else:
                    stats.increment('merge_failures')
                    return False
                    
            finally:
                # 清理临时目录
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"清理临时目录失败: {e}")
            
        except Exception as e:
            logger.error(f"处理M3U8内容时出错: {e}")
            stats.increment('error_videos')
            return False

class RobloxVideoExtractor:
    """从Roblox缓存中提取视频的主类"""
    
    def __init__(self, base_dir: str, num_threads: int = 1,
                 download_history: Optional[ExtractedHistory] = None,
                 classification_method: VideoClassificationMethod = VideoClassificationMethod.RESOLUTION,
                 custom_output_dir: Optional[str] = None,
                 scan_db: bool = True,
                 use_multiprocessing: bool = False,
                 conservative_multiprocessing: bool = True,
                 ffmpeg_path: str = None,
                 quality_preference: VideoQualityPreference = VideoQualityPreference.AUTO,
                 timestamp_repair: bool = True):
        """初始化视频提取器"""
        self.base_dir = os.path.abspath(base_dir)
        self.use_multiprocessing = use_multiprocessing
        self.conservative_multiprocessing = conservative_multiprocessing
        
        # 根据多进程配置调整线程/进程数量
        if self.use_multiprocessing:
            self.num_processes = get_optimal_process_count(
                max_processes=num_threads if num_threads > 1 else None,
                conservative=conservative_multiprocessing
            )
        else:
            self.num_threads = num_threads or min(8, multiprocessing.cpu_count())
        
        self.download_history = download_history
        self.classification_method = classification_method
        self.cancelled = False
        self._cancel_check_fn = None
        self.scan_db = scan_db
        self.ffmpeg_path = ffmpeg_path
        self.quality_preference = quality_preference
        self.timestamp_repair = timestamp_repair
        
        # 输出目录
        if custom_output_dir and os.path.isabs(custom_output_dir):
            self.output_dir = custom_output_dir
        else:
            self.output_dir = os.path.join(self.base_dir, custom_output_dir or "extracted")
        
        # 初始化组件
        from .cache_scanner import get_scanner
        self.cache_scanner = get_scanner()
        
        # 设置自定义缓存路径（如果提供了base_dir）
        if self.base_dir:
            # 检测是否为数据库文件
            if self.base_dir.endswith('.db') and os.path.isfile(self.base_dir):
                is_database = self.scan_db  # 只有启用数据库扫描才作为数据库处理
                db_folder = os.path.splitext(self.base_dir)[0] if is_database else ""
                target_path = self.base_dir if is_database else os.path.dirname(self.base_dir)
                self.cache_scanner.set_custom_path(target_path, is_database, db_folder)
            # 检查是否为Roblox标准数据库文件夹
            elif os.path.basename(self.base_dir) == 'rbx-storage' and os.path.isdir(self.base_dir):
                potential_db = self.base_dir + '.db'
                if os.path.isfile(potential_db) and self.scan_db:
                    # 存在数据库文件且启用数据库扫描
                    self.cache_scanner.set_custom_path(potential_db, True, self.base_dir)
                else:
                    # 直接扫描文件夹
                    self.cache_scanner.set_custom_path(self.base_dir, False, "")
            # 其他情况，直接作为文件系统路径处理
            else:
                self.cache_scanner.set_custom_path(self.base_dir, False, "")
        
        self.content_identifier = ContentIdentifier(block_avatar_images=True)
        self.stats = VideoProcessingStats()
        self.hash_cache = ContentHashCache()
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
    
    def set_cancel_check_function(self, cancel_check_fn: Callable[[], bool]):
        """设置取消检查函数"""
        self._cancel_check_fn = cancel_check_fn
    
    def cancel(self):
        """取消提取操作"""
        self.cancelled = True
    
    def is_cancelled(self):
        """检查是否被取消"""
        if self._cancel_check_fn:
            return self._cancel_check_fn()
        return self.cancelled
    
    def extract_videos(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict[str, Any]:
        """
        提取视频文件
        
        Args:
            progress_callback: 进度回调函数(current, total)
            
        Returns:
            Dict[str, Any]: 提取结果统计
        """
        start_time = time.time()
        
        try:
            # 扫描缓存
            logger.info("Starting video cache scan...")
            cache_items = self.cache_scanner.scan_cache()
            
            if not cache_items:
                logger.info("No cache items found")
                return self._create_result_dict(start_time)
            
            logger.info(f"Found {len(cache_items)} cache items")
            
            # 筛选M3U8/视频相关项
            video_items = []
            for item in cache_items:
                if self.is_cancelled():
                    break
                    
                try:
                    # 解析缓存内容
                    if item.cache_type == CacheType.DATABASE:
                        parsed = parse_cache_data(item.data)
                    else:
                        parsed = parse_cache_file(item.path)
                    
                    if parsed and parsed.success:
                        # 识别内容类型
                        identified = self.content_identifier.identify_content(parsed.content)
                        
                        # 检查是否为M3U8播放列表
                        if identified.asset_type == AssetType.EXTM3U:
                            content_str = parsed.content.decode('utf-8', errors='ignore')
                            if "RBX-BASE-URI" in content_str:
                                video_items.append((item, parsed.content, content_str))
                
                except Exception as e:
                    logger.warning(f"解析缓存项失败: {e}")
                    continue
            
            logger.info(f"Found {len(video_items)} video playlists")
            
            if not video_items:
                logger.info("No video content found")
                return self._create_result_dict(start_time)
            
            # 处理视频
            processor = VideoProcessor(
                output_dir=self.output_dir,
                classification_method=self.classification_method,
                ffmpeg_path=self.ffmpeg_path,
                quality_preference=self.quality_preference,
                timestamp_repair=self.timestamp_repair
            )
            processor.set_cancel_check_function(self.is_cancelled)
            
            total_videos = len(video_items)
            processed_count = 0
            
            for i, (cache_item, content_bytes, content_str) in enumerate(video_items):
                if self.is_cancelled():
                    break
                
                try:
                    # 生成视频哈希
                    video_hash = hashlib.md5(content_bytes).hexdigest()
                    
                    # 检查是否已处理
                    if self.download_history and self.download_history.is_processed(video_hash):
                        self.stats.increment('already_processed')
                        continue
                    
                    # 处理视频
                    if processor.process_m3u8_content(content_str, video_hash, self.stats):
                        # 添加到历史记录
                        if self.download_history:
                            self.download_history.add_hash(video_hash, 'video')
                    
                    processed_count += 1
                    
                    # 更新进度
                    if progress_callback:
                        progress_callback(processed_count, total_videos)
                        
                except Exception as e:
                    logger.error(f"处理视频时出错: {e}")
                    self.stats.increment('error_videos')
            
            return self._create_result_dict(start_time)
            
        except Exception as e:
            logger.error(f"视频提取过程中发生错误: {e}")
            raise
    
    def _create_result_dict(self, start_time: float) -> Dict[str, Any]:
        """创建结果字典"""
        end_time = time.time()
        duration = end_time - start_time
        
        stats = self.stats.get_all()
        
        return {
            'success': True,
            'duration': duration,
            'stats': stats,
            'output_dir': self.output_dir,
            'cancelled': self.is_cancelled()
        }

# 导出函数
def extract_roblox_videos(base_dir: str, output_dir: str = None, 
                         classification_method: VideoClassificationMethod = VideoClassificationMethod.RESOLUTION,
                         num_threads: int = 1, scan_db: bool = True,
                         ffmpeg_path: str = None,
                         progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict[str, Any]:
    """
    提取Roblox视频的便捷函数
    
    Args:
        base_dir: Roblox缓存目录
        output_dir: 输出目录
        classification_method: 分类方法
        num_threads: 线程数
        scan_db: 是否扫描数据库
        ffmpeg_path: FFmpeg路径
        progress_callback: 进度回调
        
    Returns:
        Dict[str, Any]: 提取结果
    """
    extractor = RobloxVideoExtractor(
        base_dir=base_dir,
        custom_output_dir=output_dir,
        classification_method=classification_method,
        num_threads=num_threads,
        scan_db=scan_db,
        ffmpeg_path=ffmpeg_path
    )
    
    return extractor.extract_videos(progress_callback=progress_callback) 