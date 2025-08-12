#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体提取工作线程 

"""

import os
import time
import traceback
from PyQt5.QtCore import QThread, pyqtSignal

# 导入Roblox字体提取器
from src.extractors.font_extractor import RobloxFontExtractor, FontClassificationMethod
from src.locale import lang

class FontExtractionWorker(QThread):
    """字体提取工作线程"""
    progressUpdated = pyqtSignal(int, int, float, float)  # 进度更新信号(当前进度, 总数, 已用时间, 速度)
    finished = pyqtSignal(dict)  # 完成信号(结果字典)
    logMessage = pyqtSignal(str, str)  # 日志消息信号(消息, 类型)
    statusMessage = pyqtSignal(str)  # 状态消息信号

    def __init__(self, base_dir, num_threads, download_history, classification_method, custom_output_dir=None, scan_db=True, convert_enabled=True, convert_format="TTF", use_multiprocessing=False, conservative_multiprocessing=True):
        """
        初始化字体提取工作线程
        
        Args:
            base_dir: 基础目录路径(Roblox缓存路径)
            num_threads: 线程数量
            download_history: 下载历史管理器
            classification_method: 分类方法
            custom_output_dir: 自定义输出目录
            scan_db: 是否扫描数据库
            convert_enabled: 是否启用字体下载(与音频的convert_enabled对应)
            convert_format: 字体格式(保留以兼容接口)
            use_multiprocessing: 是否使用多进程
            conservative_multiprocessing: 是否使用保守的多进程策略
        """
        super().__init__()
        self.base_dir = base_dir
        self.num_threads = num_threads
        self.download_history = download_history
        self.classification_method = classification_method
        self.custom_output_dir = custom_output_dir
        self.scan_db = scan_db
        self.convert_enabled = convert_enabled
        self.convert_format = convert_format
        self.use_multiprocessing = use_multiprocessing
        self.conservative_multiprocessing = conservative_multiprocessing
        self.is_cancelled = False
        self.extractor = None
        
        # 进度追踪
        self.start_time = 0
        self.processed_count = 0
        self.total_count = 0

    def run(self):
        """运行线程：提取字体文件"""
        try:
            self.start_time = time.time()
            
            # 发送开始消息
            self.logMessage.emit(self._get_lang('starting_font_extraction'), 'info')
            self.statusMessage.emit(self._get_lang('initializing_extractor'))
            
            # 创建日志回调函数
            def log_callback(message_key: str, log_type: str, *args):
                """处理从提取器发送的日志消息"""
                # 将翻译键和参数以特殊格式发送，让界面层处理翻译和格式化
                if args:
                    # 使用分隔符将翻译键和参数分开
                    message_with_args = f"{message_key}|{chr(31)}|" + chr(31).join(str(arg) for arg in args)
                    self.logMessage.emit(message_with_args, log_type)
                else:
                    self.logMessage.emit(message_key, log_type)
            
            # 创建Roblox字体提取器
            self.extractor = RobloxFontExtractor(
                output_dir=self.custom_output_dir,
                classification_method=self.classification_method,
                block_avatar_images=True,  # 默认阻止头像图片
                num_threads=self.num_threads,
                use_multiprocessing=self.use_multiprocessing,
                conservative_multiprocessing=self.conservative_multiprocessing,
                log_callback=log_callback,
                download_history=self.download_history
            )
            
            # 设置取消检查函数
            self.extractor.set_cancel_check(lambda: self.is_cancelled)
            
            # 获取缓存信息
            cache_info = self.extractor.get_cache_info()
            cache_path = cache_info.get('target_path', self._get_lang('unknown'))
            cache_type = self._get_lang('database') if cache_info.get('target_is_database', False) else self._get_lang('filesystem')
            self.logMessage.emit(
                self._get_lang('cache_info', cache_path, cache_type),
                'info'
            )
            
            # 检查缓存路径
            if not cache_info.get('path_exists', False):
                error_msg = self._get_lang('cache_path_not_found')
                self.logMessage.emit(error_msg, 'error')
                self.finished.emit({
                    "success": False,
                    "error": error_msg,
                    "stats": {},
                    "cache_info": cache_info
                })
                return
            
            # 开始提取字体
            self.statusMessage.emit(self._get_lang('extracting_fonts'))
            result = self.extractor.extract_fonts(
                progress_callback=self._on_progress,
                custom_cache_path=None  # 字体提取始终使用自动检测的Roblox缓存路径
            )
            
            # 计算最终统计
            duration = time.time() - self.start_time
            result['duration'] = duration
            
            if result.get('success', False):
                stats = result.get('stats', {})
                fontlist_found = stats.get('fontlist_found', 0)
                fonts_downloaded = stats.get('fonts_downloaded', 0)
                self.logMessage.emit(
                    self._get_lang('extraction_completed', fontlist_found, fonts_downloaded, duration),
                    'success'
                )
            else:
                error_msg = result.get('error', self._get_lang('unknown_error'))
                self.logMessage.emit(
                    self._get_lang('extraction_failed', error_msg),
                    'error'
                )
            
            # 发送完成信号
            self.finished.emit(result)
            
        except Exception as e:
            error_msg = self._get_lang('extraction_error', str(e))
            self.logMessage.emit(error_msg, 'error')
            self.logMessage.emit(self._get_lang('error_details', traceback.format_exc()), 'debug')
            
            self.finished.emit({
                "success": False,
                "error": str(e),
                "stats": {},
                "duration": time.time() - self.start_time if self.start_time > 0 else 0
            })
        
        finally:
            # 确保历史记录被保存 - 修复：强制保存历史记录
            if self.download_history:
                try:
                    self.download_history.save_history()
                    history_size = self.download_history.get_history_size('font')
                    self.logMessage.emit(f"History saved: {history_size} font files", 'info')
                except Exception as e:
                    self.logMessage.emit(f"Failed to save font history: {str(e)}", 'error')

    def _on_progress(self, current: int, total: int, message: str):
        """
        进度回调函数
        
        Args:
            current: 当前进度
            total: 总数
            message: 状态消息
        """
        if self.is_cancelled:
            return
            
        self.processed_count = current
        self.total_count = total
        
        # 计算时间和速度
        elapsed_time = time.time() - self.start_time
        if current > 0 and elapsed_time > 0:
            speed = current / elapsed_time
        else:
            speed = 0.0
        
        # 发送进度信号
        self.progressUpdated.emit(current, total, elapsed_time, speed)
        
        # 发送状态消息
        self.statusMessage.emit(message)
        
        # 记录重要进度
        if total > 0 and current % max(1, total // 10) == 0:  # 每10%记录一次
            progress_percent = (current / total) * 100
            self.logMessage.emit(
                self._get_lang('progress_update', progress_percent, current, total),
                'info'
            )

    def cancel(self):
        """取消字体提取操作"""
        self.is_cancelled = True
        if self.extractor:
            self.extractor.cancel()
        self.logMessage.emit(self._get_lang('extraction_cancelled'), 'warning')

    def _get_lang(self, key, *args):
        """
        简单的语言字符串获取辅助函数。
        由于工作线程不应直接导入lang模块，所以用这个辅助函数发送固定的英文字符串，
        在主线程中会被正确转换为当前语言。
        """
        # 简单的英文键值映射，实际应用中应该使用主程序的语言系统
        english_strings = {
            'starting_font_extraction': 'Starting font extraction...',
            'initializing_extractor': 'Initializing font extractor...',
            'cache_info': 'Cache info: Path={}, Type={}',
            'cache_path_not_found': 'Roblox cache path not found or inaccessible',
            'extracting_fonts': 'Extracting font files...',
            'extraction_completed': 'Font extraction completed! Found {} font lists, successfully downloaded {} font files (took {:.1f} seconds)',
            'extraction_failed': 'Font extraction failed: {}',
            'extraction_error': 'Error occurred during font extraction: {}',
            'error_details': 'Error details: {}',
            'progress_update': 'Progress update: {:.1f}% ({}/{})',
            'extraction_cancelled': 'Font extraction cancelled',
            'unknown_error': 'Unknown error',
            'unknown': 'Unknown',
            'database': 'Database',
            'filesystem': 'File system'
        }
        
        if key in english_strings:
            try:
                return english_strings[key].format(*args)
            except:
                return english_strings[key]
        return key  # 如果找不到键，返回键本身

    def get_extraction_stats(self) -> dict:
        """
        获取提取统计信息
        
        Returns:
            dict: 统计信息
        """
        if self.extractor:
            return self.extractor.get_stats()
        return {} 