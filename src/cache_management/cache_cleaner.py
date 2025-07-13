#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
缓存清理工具
提供用于清理Roblox音频缓存文件的功能
"""

import os
from PyQt5.QtCore import QThread, pyqtSignal


class CacheClearWorker(QThread):
    """缓存清理工作线程"""
    finished = pyqtSignal(bool, int, int, str)  # 完成信号(成功?, 清理数量, 总数, 错误信息)
    progressUpdated = pyqtSignal(int, int)  # 进度更新信号(当前, 总数)

    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        self.is_cancelled = False

    def run(self):
        """运行线程：清理缓存"""
        try:
            # 计数器
            total_files = 0
            cleared_files = 0
            processed_files = 0

            # 需要排除的文件夹
            exclude_dirs = {'extracted'}
            files_to_process = []

            # 首先扫描所有文件
            for root, dirs, files in os.walk(self.directory):
                # 跳过排除的目录
                if any(excluded in root for excluded in exclude_dirs):
                    continue

                for file in files:
                    file_path = os.path.join(root, file)
                    total_files += 1
                    files_to_process.append(file_path)

            # 处理文件
            for file_path in files_to_process:
                if self.is_cancelled:
                    break

                try:
                    # 读取文件的前8KB内容
                    with open(file_path, 'rb') as f:
                        content = f.read(8192)

                    # 检查OGG文件头或其他标识
                    if (b'OggS' in content or  # OGG标识
                            b'.ogg' in content.lower() or  # .ogg扩展名
                            b'audio' in content.lower() or  # 音频关键字
                            b'sound' in content.lower()):  # 声音关键字

                        # 删除文件
                        os.remove(file_path)
                        cleared_files += 1

                except (IOError, OSError, PermissionError):
                    pass

                # 更新进度
                processed_files += 1
                self.progressUpdated.emit(processed_files, total_files)

            # 返回结果
            self.finished.emit(True, cleared_files, total_files, "")

        except Exception as e:
            self.finished.emit(False, 0, 0, str(e))
    
    def cancel(self):
        """取消操作"""
        self.is_cancelled = True 