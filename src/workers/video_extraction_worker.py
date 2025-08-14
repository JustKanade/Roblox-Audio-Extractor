#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频提取工作线程
Video Extraction Worker Thread
"""

import os
import time
import traceback
from PyQt5.QtCore import QThread, pyqtSignal

from src.extractors.video_extractor import RobloxVideoExtractor, VideoClassificationMethod
from src.utils.history_manager import ExtractedHistory

class VideoExtractionWorker(QThread):
    """视频提取工作线程"""
    
    # 信号定义
    progressUpdated = pyqtSignal(int, int, float, float)  # current, total, elapsed_time, speed
    finished = pyqtSignal(dict)  # 提取完成信号，传递结果字典
    logMessage = pyqtSignal(str, str)  # 日志消息，message, type
    
    def __init__(self, base_dir, num_threads, download_history, classification_method, 
                 custom_output_dir=None, scan_db=True, use_multiprocessing=False, 
                 conservative_multiprocessing=True, concurrent_downloads=True, 
                 auto_cleanup=True, ffmpeg_path=None, quality_preference=None, 
                 timestamp_repair=True):
        """
        初始化视频提取工作线程
        
        Args:
            base_dir: 输入目录
            num_threads: 线程数
            download_history: 下载历史
            classification_method: 分类方法
            custom_output_dir: 自定义输出目录
            scan_db: 是否扫描数据库
            use_multiprocessing: 是否使用多进程
            conservative_multiprocessing: 保守的多进程策略
            concurrent_downloads: 并发下载
            auto_cleanup: 自动清理
            ffmpeg_path: FFmpeg路径
        """
        super().__init__()
        self.base_dir = base_dir
        self.num_threads = num_threads
        self.download_history = download_history
        self.classification_method = classification_method
        self.custom_output_dir = custom_output_dir
        self.scan_db = scan_db
        self.use_multiprocessing = use_multiprocessing
        self.conservative_multiprocessing = conservative_multiprocessing
        self.concurrent_downloads = concurrent_downloads
        self.auto_cleanup = auto_cleanup
        self.ffmpeg_path = ffmpeg_path
        self.quality_preference = quality_preference
        self.timestamp_repair = timestamp_repair
        self.extractor = None
        self._stop_requested = False
    
    def _get_lang(self, key, *args):
        """
        简单的语言字符串获取辅助函数。
        由于工作线程不应直接导入lang模块，所以用这个辅助函数发送固定的英文字符串，
        在主线程中会被正确转换为当前语言。
        """
        # 简单的英文键值映射，实际应用中应该使用主程序的语言系统
        english_strings = {
            'video_initializing_extractor': 'Initializing video extractor...',
            'video_scanning_cache': 'Scanning video cache...',
            'video_extraction_cancelled': 'Video extraction cancelled',
            'video_processing_complete': 'Video processing complete!',
            'video_extraction_failed': 'Video extraction failed',
            'video_extraction_error': 'Error occurred during video extraction: {}',
            'video_error_details': 'Error details: {}',
            'video_cancelling': 'Cancelling video extraction...',
            'video_total_duration': 'Total duration: {:.2f} seconds',
            'video_output_directory': 'Output directory: {}',
            'video_processed_count': 'Videos processed: {} items',
            'video_segments_downloaded': 'Segments downloaded: {} items',
            'video_merged_count': 'Videos merged: {} items',
            'video_duplicates_skipped': 'Duplicates skipped: {} items',
            'video_download_failures': 'Download failures: {} items',
            'video_progress_update': 'Processing progress: {}/{} ({}%)',
            'video_repairing_segment': 'Repairing video segment: {}',
            'video_repair_failed': 'Video segment repair failed: {}',
            'video_selected_quality': 'Selected video quality: {}',
            'video_quality_not_available': 'Requested quality {} not available, using: {}'
        }
        
        text = english_strings.get(key, key)
        if args:
            try:
                text = text.format(*args)
            except:
                pass
        return text
        
    def run(self):
        """运行视频提取"""
        try:
            self.start_time = time.time()
            self.logMessage.emit(self._get_lang("video_initializing_extractor"), 'info')
            
            # 创建视频提取器
            self.extractor = RobloxVideoExtractor(
                base_dir=self.base_dir,
                num_threads=self.num_threads,
                download_history=self.download_history,
                classification_method=self.classification_method,
                custom_output_dir=self.custom_output_dir,
                scan_db=self.scan_db,
                use_multiprocessing=self.use_multiprocessing,
                conservative_multiprocessing=self.conservative_multiprocessing,
                ffmpeg_path=self.ffmpeg_path,
                quality_preference=self.quality_preference,
                timestamp_repair=self.timestamp_repair
            )
            
            # 设置取消检查函数
            self.extractor.set_cancel_check_function(lambda: self._stop_requested)
            
            self.logMessage.emit(self._get_lang("video_scanning_cache"), 'info')
            
            # 执行视频提取，传递进度回调
            result = self.extractor.extract_videos(
                progress_callback=self.progress_callback
            )
            
            if self._stop_requested:
                self.logMessage.emit(self._get_lang("video_extraction_cancelled"), 'warning')
                result['cancelled'] = True
            elif result.get('success', False):
                # 输出统计信息
                stats = result.get('stats', {})
                self.logMessage.emit(self._get_lang("video_processing_complete"), 'success')
                self.logMessage.emit(self._get_lang("video_processed_count", stats.get('processed_videos', 0)), 'info')
                self.logMessage.emit(self._get_lang("video_segments_downloaded", stats.get('downloaded_segments', 0)), 'info')
                self.logMessage.emit(self._get_lang("video_merged_count", stats.get('merged_videos', 0)), 'info')
                
                if stats.get('duplicate_videos', 0) > 0:
                    self.logMessage.emit(self._get_lang("video_duplicates_skipped", stats.get('duplicate_videos', 0)), 'info')
                
                if stats.get('download_failures', 0) > 0:
                    self.logMessage.emit(self._get_lang("video_download_failures", stats.get('download_failures', 0)), 'warning')
                
                duration = result.get('duration', 0)
                self.logMessage.emit(self._get_lang("video_total_duration", duration), 'info')
                
                # 输出目录信息
                output_dir = result.get('output_dir', '')
                if output_dir:
                    self.logMessage.emit(self._get_lang("video_output_directory", output_dir), 'info')
            else:
                self.logMessage.emit(self._get_lang("video_extraction_failed"), 'error')
            
            # 发送完成信号
            self.finished.emit(result)
            
        except Exception as e:
            error_msg = self._get_lang("video_extraction_error", str(e))
            self.logMessage.emit(error_msg, 'error')
            self.logMessage.emit(self._get_lang("video_error_details", traceback.format_exc()), 'error')
            
            # 发送失败结果
            self.finished.emit({
                'success': False,
                'error': str(e),
                'cancelled': self._stop_requested
            })
    
    def progress_callback(self, current, total):
        """进度回调函数"""
        if not self._stop_requested:
            # 计算已用时间和处理速度
            current_time = time.time()
            if not hasattr(self, 'start_time'):
                self.start_time = current_time
            
            elapsed_time = current_time - self.start_time
            speed = current / elapsed_time if elapsed_time > 0 else 0
            
            self.progressUpdated.emit(current, total, elapsed_time, speed)
            
            if total > 0:
                percentage = (current / total) * 100
                # 使用特殊分隔符格式来与翻译系统兼容
                separator = chr(31)
                message = f"video_progress_update|{separator}|{percentage:.1f}{separator}{current}{separator}{total}"
                self.logMessage.emit(message, 'info')
    
    def stop(self):
        """停止提取操作"""
        self._stop_requested = True
        if self.extractor:
            self.extractor.cancel()
        
        self.logMessage.emit(self._get_lang("video_cancelling"), 'warning')
    
    def is_running_extraction(self):
        """检查是否正在运行提取"""
        return self.isRunning() and not self._stop_requested 