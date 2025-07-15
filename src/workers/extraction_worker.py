#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频提取工作线程 - 负责在后台线程中处理音频提取任务
Audio Extraction Worker - Responsible for processing audio extraction tasks in a background thread
作者/Author: JustKanade
"""

import os
import time
import traceback

from PyQt5.QtCore import QThread, pyqtSignal

# 导入自定义提取器模块
from src.extractors.audio_extractor import RobloxAudioExtractor, ClassificationMethod


class ExtractionWorker(QThread):
    """音频提取工作线程"""
    progressUpdated = pyqtSignal(int, int, float, float)  # 进度更新信号(当前进度, 总数, 已用时间, 速度)
    finished = pyqtSignal(dict)  # 完成信号(结果字典)
    logMessage = pyqtSignal(str, str)  # 日志消息信号(消息, 类型)

    def __init__(self, base_dir, num_threads, download_history, classification_method, custom_output_dir=None, scan_db=True):
        super().__init__()
        self.base_dir = base_dir
        self.num_threads = num_threads
        self.download_history = download_history
        self.classification_method = classification_method
        self.custom_output_dir = custom_output_dir
        self.scan_db = scan_db
        self.is_cancelled = False
        self.total_files = 0
        self.processed_count = 0
        self.actual_extracted_count = 0  # 记录实际提取的文件数量
        self.extractor = None

    def run(self):
        """运行线程：提取音频文件"""
        try:
            # 更新状态
            self.logMessage.emit(self._get_lang('scanning_files'), 'info')

            # 创建提取器
            start_time = time.time()
            self.extractor = RobloxAudioExtractor(
                self.base_dir,
                self.num_threads,
                ["oggs", "ID3"],  # 同时搜索 "oggs" 和 "ID3"
                self.download_history,
                self.classification_method,
                self.custom_output_dir,  # 传入自定义输出路径
                self.scan_db  # 是否扫描数据库
            )

            # 设置取消检查函数
            def check_cancelled():
                return self.is_cancelled
                
            # 使用set_cancel_check方法
            self.extractor.set_cancel_check(check_cancelled)

            # 查找要处理的文件
            files_to_process = self.extractor.find_files_to_process()
            scan_duration = time.time() - start_time
            self.total_files = len(files_to_process)

            self.logMessage.emit(self._get_lang('found_files', self.total_files, scan_duration), 'info')

            if not files_to_process:
                self.logMessage.emit(self._get_lang('no_files_found'), 'warning')
                self.finished.emit({
                    "success": True,
                    "processed": 0,
                    "duplicates": 0,
                    "already_processed": 0,
                    "errors": 0,
                    "output_dir": self.extractor.output_dir,
                    "duration": 0,
                    "files_per_second": 0
                })
                return

            # 创建一个用于更新进度的函数
            original_process_file = self.extractor.process_file
            self.actual_extracted_count = 0  # 记录实际提取的文件数量

            def process_file_with_progress(file_path):
                # 调用原始处理方法，获取处理结果
                result = original_process_file(file_path)
                # 如果成功提取了文件，增加实际提取计数
                if result:
                    self.actual_extracted_count += 1
                
                # 更新总处理进度
                self.processed_count += 1
                elapsed = time.time() - start_time
                speed = self.processed_count / elapsed if elapsed > 0 else 0
                
                # 发送进度信号，不限制进度百分比为整数，让UI层处理
                self.progressUpdated.emit(self.processed_count, self.total_files, elapsed, speed)
                return result

            # 包装处理方法以提供进度更新
            self.extractor.process_file = process_file_with_progress

            # 处理文件
            self.logMessage.emit(self._get_lang('processing_with_threads', self.num_threads), 'info')

            # 进行处理
            extraction_result = self.extractor.process_files()
            
            # 使用实际提取的文件数量更新结果
            extraction_result["processed"] = self.actual_extracted_count

            # 确保历史记录被保存 - 修复：强制保存历史记录
            if self.download_history:
                try:
                    self.download_history.save_history()
                    self.logMessage.emit(f"History saved: {self.download_history.get_history_size()} files", 'info')
                except Exception as e:
                    self.logMessage.emit(f"Failed to save history: {str(e)}", 'error')

            # 设置结果
            extraction_result["success"] = True
            self.finished.emit(extraction_result)

        except Exception as e:
            self.logMessage.emit(self._get_lang('error_occurred', str(e)), 'error')
            traceback.print_exc()
            self.finished.emit({"success": False, "error": str(e)})

    def cancel(self):
        """取消操作"""
        self.is_cancelled = True
        
    def _get_lang(self, key, *args):
        """
        简单的语言字符串获取辅助函数。
        由于工作线程不应直接导入lang模块，所以用这个辅助函数发送固定的英文字符串，
        在主线程中会被正确转换为当前语言。
        """
        # 简单的英文键值映射，实际应用中应该使用主程序的语言系统
        english_strings = {
            'scanning_files': 'Scanning files...',
            'found_files': 'Found {} files to process (scan took {:.2f}s)',
            'no_files_found': 'No files found to process',
            'processing_with_threads': 'Processing with {} threads',
            'error_occurred': 'Error occurred: {}'
        }
        
        if key in english_strings:
            try:
                return english_strings[key].format(*args)
            except:
                return english_strings[key]
        return key  # 如果找不到键，返回键本身 