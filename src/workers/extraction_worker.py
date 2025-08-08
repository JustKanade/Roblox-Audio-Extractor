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

    def __init__(self, base_dir, num_threads, download_history, classification_method, custom_output_dir=None, scan_db=True, convert_enabled=False, convert_format="MP3"):
        super().__init__()
        self.base_dir = base_dir
        self.num_threads = num_threads
        self.download_history = download_history
        self.classification_method = classification_method
        self.custom_output_dir = custom_output_dir
        self.scan_db = scan_db
        self.convert_enabled = convert_enabled
        self.convert_format = convert_format
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

            # 如果启用了音频转换且提取了文件，进行格式转换
            if self.convert_enabled and self.actual_extracted_count > 0:
                self.logMessage.emit(f'Converting audio files to {self.convert_format}...', 'info')
                try:
                    conversion_result = self._convert_audio_files(extraction_result.get("output_dir", ""))
                    extraction_result["conversion_result"] = conversion_result
                    # 添加转换输出目录信息
                    conversion_result["converted_dir"] = os.path.join(extraction_result.get("output_dir", ""), f"Audio_{self.convert_format.upper()}")
                    if conversion_result["converted"] > 0:
                        self.logMessage.emit(f'Successfully converted {conversion_result["converted"]} files to {self.convert_format}', 'success')
                    else:
                        self.logMessage.emit('No files were converted', 'warning')
                except Exception as e:
                    self.logMessage.emit(f'Audio conversion failed: {str(e)}', 'error')
                    extraction_result["conversion_error"] = str(e)

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
    
    def _convert_audio_files(self, output_dir):
        """转换音频文件格式"""
        import subprocess
        import glob
        
        result = {
            "converted": 0,
            "failed": 0,
            "errors": []
        }
        
        if not output_dir or not os.path.exists(output_dir):
            raise Exception("Output directory not found")
        
        # 查找所有OGG文件
        audio_dir = os.path.join(output_dir, "Audio")
        if not os.path.exists(audio_dir):
            raise Exception("Audio directory not found")
        
        # 为转换后的格式创建专门的文件夹
        convert_format_upper = self.convert_format.upper()
        converted_dir = os.path.join(output_dir, f"Audio_{convert_format_upper}")
        
        # 递归查找所有.ogg文件
        ogg_files = []
        for root, dirs, files in os.walk(audio_dir):
            for file in files:
                if file.lower().endswith('.ogg'):
                    ogg_files.append(os.path.join(root, file))
        
        if not ogg_files:
            return result
        
        # 检查ffmpeg是否可用
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("FFmpeg is not installed or not found in PATH")
        
        self.logMessage.emit(f'Found {len(ogg_files)} OGG files to convert', 'info')
        self.logMessage.emit(f'Converting to format: {convert_format_upper}', 'info')
        self.logMessage.emit(f'Output directory: {converted_dir}', 'info')
        
        for i, ogg_file in enumerate(ogg_files):
            if self.is_cancelled:
                break
                
            try:
                # 获取OGG文件相对于Audio目录的路径
                rel_path = os.path.relpath(ogg_file, audio_dir)
                
                # 生成对应的转换后文件路径，保持相同的文件夹结构
                output_file_name = os.path.splitext(os.path.basename(rel_path))[0] + f'.{self.convert_format.lower()}'
                output_file_dir = os.path.join(converted_dir, os.path.dirname(rel_path))
                output_file = os.path.join(output_file_dir, output_file_name)
                
                # 确保输出目录存在
                os.makedirs(output_file_dir, exist_ok=True)
                
                # 构建ffmpeg命令
                cmd = [
                    'ffmpeg', '-i', ogg_file, 
                    '-y',  # 覆盖输出文件
                    '-loglevel', 'error',  # 只显示错误
                ]
                
                # 根据格式添加特定参数
                if self.convert_format.upper() == 'MP3':
                    cmd.extend(['-codec:a', 'libmp3lame', '-b:a', '192k'])
                elif self.convert_format.upper() == 'WAV':
                    cmd.extend(['-codec:a', 'pcm_s16le'])
                elif self.convert_format.upper() == 'FLAC':
                    cmd.extend(['-codec:a', 'flac'])
                elif self.convert_format.upper() == 'AAC':
                    cmd.extend(['-codec:a', 'aac', '-b:a', '128k'])
                elif self.convert_format.upper() == 'M4A':
                    cmd.extend(['-codec:a', 'aac', '-b:a', '128k'])
                    
                cmd.append(output_file)
                
                # 执行转换
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                if process.returncode == 0:
                    result["converted"] += 1
                    # 转换成功后可以选择删除原文件
                    # os.remove(ogg_file)  # 取消注释以删除原OGG文件
                else:
                    result["failed"] += 1
                    error_msg = f"Failed to convert {os.path.basename(ogg_file)}: {process.stderr}"
                    result["errors"].append(error_msg)
                    self.logMessage.emit(error_msg, 'warning')
                    
            except Exception as e:
                result["failed"] += 1
                error_msg = f"Error converting {os.path.basename(ogg_file)}: {str(e)}"
                result["errors"].append(error_msg)
                self.logMessage.emit(error_msg, 'warning')
            
            # 更新进度 (可选)
            if i % 10 == 0:  # 每转换10个文件更新一次进度
                self.logMessage.emit(f'Converted {i+1}/{len(ogg_files)} files...', 'info')
        
        return result 