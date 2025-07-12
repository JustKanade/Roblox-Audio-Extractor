#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Roblox图像提取工作线程
Roblox Image Extraction Worker Thread
"""

import os
import time
import traceback
from typing import Dict, Any, Optional

from PyQt5.QtCore import QThread, pyqtSignal

from src.components.RobloxImageExtractor import RobloxImageExtractor, ImageClassificationMethod

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None  # 如果导入失败，设为None

class ImageExtractionWorker(QThread):
    """图片提取工作线程"""
    progressUpdated = pyqtSignal(int, int, float, float)  # 进度更新信号(当前进度, 总数, 已用时间, 速度)
    finished = pyqtSignal(dict)  # 完成信号(结果字典)
    logMessage = pyqtSignal(str, str)  # 日志消息信号(消息, 类型)

    def __init__(self, base_dir, num_threads, download_history, classification_method, custom_output_dir=None):
        """初始化图片提取工作线程
        
        Args:
            base_dir: 基础目录路径
            num_threads: 线程数
            download_history: 下载历史记录对象
            classification_method: 分类方法
            custom_output_dir: 自定义输出目录
        """
        super().__init__()
        self.base_dir = base_dir
        self.num_threads = num_threads
        self.download_history = download_history
        self.classification_method = classification_method
        self.custom_output_dir = custom_output_dir
        self.is_cancelled = False
        self.total_files = 0
        self.processed_count = 0

    def run(self):
        """运行线程：提取图片文件"""
        try:
            # 更新状态
            self.logMessage.emit(
                lang.get("scanning_files", "正在扫描文件...") if lang else "正在扫描文件...", 
                'info'
            )

            # 创建提取器
            start_time = time.time()
            extractor = RobloxImageExtractor(
                self.base_dir,
                self.num_threads,
                self.download_history,
                self.classification_method,
                self.custom_output_dir
            )

            # 设置取消检查函数
            extractor.cancelled = lambda: self.is_cancelled

            # 查找要处理的文件
            files_to_process = extractor.find_files_to_process()
            scan_duration = time.time() - start_time
            self.total_files = len(files_to_process)

            # 发送日志消息
            found_files_msg = lang.get("found_files", "找到 {0} 个文件，用时 {1:.2f} 秒").format(
                self.total_files, scan_duration
            ) if lang else f"找到 {self.total_files} 个文件，用时 {scan_duration:.2f} 秒"
            
            self.logMessage.emit(found_files_msg, 'info')

            if not files_to_process:
                no_files_msg = lang.get("no_files_found", "未找到任何文件") if lang else "未找到任何文件"
                self.logMessage.emit(no_files_msg, 'warning')
                self.finished.emit({
                    "success": True,
                    "processed": 0,
                    "duplicates": 0,
                    "already_processed": 0,
                    "errors": 0,
                    "output_dir": extractor.output_dir,
                    "duration": 0,
                    "files_per_second": 0
                })
                return

            # 创建一个用于更新进度的函数
            original_process_file = extractor.process_file

            def process_file_with_progress(file_path):
                result = original_process_file(file_path)
                self.processed_count += 1
                elapsed = time.time() - start_time
                speed = self.processed_count / elapsed if elapsed > 0 else 0
                progress = min(100, int((self.processed_count / self.total_files) * 100))
                self.progressUpdated.emit(self.processed_count, self.total_files, elapsed, speed)
                return result

            # 替换原始方法
            extractor.process_file = process_file_with_progress

            # 处理文件
            processing_msg = lang.get("processing_with_threads", "使用 {0} 个线程处理文件").format(
                self.num_threads
            ) if lang else f"使用 {self.num_threads} 个线程处理文件"
            self.logMessage.emit(processing_msg, 'info')

            # 进行处理
            extraction_result = extractor.process_files()

            # 确保历史记录被保存
            if self.download_history:
                try:
                    self.download_history.save_history()
                    history_saved_msg = lang.get("history_saved", "历史记录已保存: {0} 个文件").format(
                        self.download_history.get_history_size()
                    ) if lang else f"历史记录已保存: {self.download_history.get_history_size()} 个文件"
                    self.logMessage.emit(history_saved_msg, 'info')
                except Exception as e:
                    save_failed_msg = lang.get("failed_to_save_history", "保存历史记录失败: {0}").format(
                        str(e)
                    ) if lang else f"保存历史记录失败: {str(e)}"
                    self.logMessage.emit(save_failed_msg, 'error')

            # 设置结果
            extraction_result["success"] = True
            self.finished.emit(extraction_result)

        except Exception as e:
            error_msg = lang.get("error_occurred", "发生错误: {0}").format(str(e)) if lang else f"发生错误: {str(e)}"
            self.logMessage.emit(error_msg, 'error')
            traceback.print_exc()
            self.finished.emit({"success": False, "error": str(e)})

    def cancel(self):
        """取消操作"""
        self.is_cancelled = True 