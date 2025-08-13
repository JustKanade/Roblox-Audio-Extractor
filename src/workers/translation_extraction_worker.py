#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译文件提取工作线程 
Translation Extraction Worker
"""

import os
import time
import traceback
from PyQt5.QtCore import QThread, pyqtSignal

# 导入Roblox翻译文件提取器
from src.extractors.translation_extractor import RobloxTranslationExtractor, TranslationClassificationMethod


class TranslationExtractionWorker(QThread):
    """翻译文件提取工作线程"""
    progressUpdated = pyqtSignal(int, int, float, float)  # 进度更新信号(当前进度, 总数, 已用时间, 速度)
    finished = pyqtSignal(dict)  # 完成信号(结果字典)
    logMessage = pyqtSignal(str, str)  # 日志消息信号(消息, 类型)

    def __init__(self, base_dir, num_threads, download_history, classification_method, custom_output_dir=None, scan_db=True, convert_enabled=True, convert_format="JSON", use_multiprocessing=False, conservative_multiprocessing=True):
        """
        初始化翻译文件提取工作线程
        
        Args:
            base_dir: 基础目录路径(Roblox缓存路径)
            num_threads: 线程数量
            download_history: 下载历史管理器
            classification_method: 分类方法
            custom_output_dir: 自定义输出目录
            scan_db: 是否扫描数据库
            convert_enabled: 是否启用翻译文件处理(与音频的convert_enabled对应)
            convert_format: 翻译文件格式(保留以兼容接口)
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
        """运行线程：提取翻译文件"""
        try:
            self.start_time = time.time()
            
            # 发送开始消息
            self.logMessage.emit(self._get_lang('starting_translation_extraction'), 'info')
            
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
            
            # 创建Roblox翻译文件提取器
            self.extractor = RobloxTranslationExtractor(
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
            
            # 创建进度回调函数
            def progress_callback(current: int, total: int, status: str):
                """进度回调函数"""
                self.processed_count = current
                self.total_count = total
                
                # 计算统计信息
                elapsed_time = time.time() - self.start_time
                speed = current / elapsed_time if elapsed_time > 0 else 0
                
                # 发送进度更新信号
                self.progressUpdated.emit(current, total, elapsed_time, speed)
            
            # 开始提取
            # 如果启用数据库扫描，使用自动检测的Roblox缓存路径（传递None）
            # 如果禁用数据库扫描，使用用户指定的自定义路径
            cache_path = None if self.scan_db else self.base_dir
            result = self.extractor.extract_translations(progress_callback, cache_path)
            
            # 发送完成信号
            self.finished.emit(result)
            
        except Exception as e:
            error_msg = f"翻译文件提取过程中发生错误: {str(e)}"
            self.logMessage.emit(error_msg, 'error')
            
            # 发送失败结果
            result = {
                "success": False,
                "error": error_msg,
                "processed_caches": self.processed_count,
                "stats": {},
                "duration": time.time() - self.start_time if self.start_time > 0 else 0,
                "output_dir": ""
            }
            self.finished.emit(result)

    def cancel(self):
        """取消提取操作"""
        self.is_cancelled = True
        if self.extractor:
            self.extractor.cancelled = True

    def _get_lang(self, key, default=""):
        """获取翻译文本的占位符方法"""
        # 这里直接返回key，让界面层处理翻译
        return key 