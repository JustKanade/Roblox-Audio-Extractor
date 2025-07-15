#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
缓存清理工具
提供用于清理Roblox数据库和存储缓存的功能
"""

import os
import sys
import shutil
import time
from PyQt5.QtCore import QThread, pyqtSignal


class CacheClearWorker(QThread):
    """缓存清理工作线程"""
    finished = pyqtSignal(bool, int, int, str)  # 完成信号(成功?, 清理数量, 总数, 错误信息)
    progressUpdated = pyqtSignal(int, int)  # 进度更新信号(当前, 总数)

    def __init__(self, directory=None):
        super().__init__()
        self.directory = directory
        self.is_cancelled = False
        self.roblox_local_dir = self._get_roblox_local_dir()
        
    def _get_roblox_local_dir(self):
        """获取Roblox本地数据目录，确保多系统兼容"""
        if sys.platform == 'win32':  # Windows
            return os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Roblox')
        elif sys.platform == 'darwin':  # macOS
            return os.path.expanduser('~/Library/Application Support/Roblox')
        else:  # Linux或其他系统
            return os.path.expanduser('~/.local/share/Roblox')

    def run(self):
        """运行线程：清理缓存"""
        try:
            if not self.roblox_local_dir or not os.path.exists(self.roblox_local_dir):
                self.finished.emit(False, 0, 0, f"Roblox目录不存在: {self.roblox_local_dir}")
                return
                
            # 计数器
            total_items = 0
            cleared_items = 0
            processed_items = 0
            
            # 要清理的项目列表
            items_to_process = []
            
            # 数据库文件路径
            db_file = os.path.join(self.roblox_local_dir, "rbx-storage.db")
            if os.path.exists(db_file):
                items_to_process.append(("file", db_file))
                total_items += 1
                
            # 数据库临时文件路径
            db_journal_file = os.path.join(self.roblox_local_dir, "rbx-storage.db-journal")
            if os.path.exists(db_journal_file):
                items_to_process.append(("file", db_journal_file))
                total_items += 1
                
            # 存储文件夹路径
            storage_dir = os.path.join(self.roblox_local_dir, "rbx-storage")
            if os.path.exists(storage_dir):
                # 获取存储文件夹中的所有子目录和文件
                for root, dirs, files in os.walk(storage_dir):
                    # 检查当前目录是否是extracted或其子目录
                    rel_path = os.path.relpath(root, storage_dir)
                    if rel_path == "." or not rel_path.startswith("extracted"):
                        # 处理文件
                        for file in files:
                            file_path = os.path.join(root, file)
                            items_to_process.append(("file", file_path))
                            total_items += 1
                            
                        # 处理目录（非extracted目录）
                        for dir_name in dirs[:]:  # 创建副本以避免修改迭代中的列表
                            if dir_name != "extracted":
                                dir_path = os.path.join(root, dir_name)
                                items_to_process.append(("dir", dir_path))
                                total_items += 1
                                dirs.remove(dir_name)  # 避免递归进入这个目录
            
            # 如果没有找到任何项目
            if total_items == 0:
                self.finished.emit(True, 0, 0, "")
                return
                
            # 处理项目
            for item_type, item_path in items_to_process:
                if self.is_cancelled:
                    break
                    
                try:
                    if item_type == "file":
                        # 如果是文件，尝试删除
                        if os.path.exists(item_path):
                            os.remove(item_path)
                            cleared_items += 1
                    elif item_type == "dir":
                        # 如果是目录，尝试删除整个目录
                        if os.path.exists(item_path):
                            shutil.rmtree(item_path)
                            cleared_items += 1
                except (IOError, OSError, PermissionError) as e:
                    print(f"无法删除 {item_path}: {str(e)}")
                
                # 更新进度
                processed_items += 1
                self.progressUpdated.emit(processed_items, total_items)
                
                # 短暂暂停，避免系统过载
                time.sleep(0.01)
            
            # 创建新的空数据库文件，确保Roblox可以正常工作
            if os.path.exists(db_file):
                try:
                    with open(db_file, 'w') as f:
                        pass  # 创建空文件
                except Exception as e:
                    print(f"无法创建新数据库文件: {str(e)}")
            
            # 确保存储目录存在
            if not os.path.exists(storage_dir):
                try:
                    os.makedirs(storage_dir)
                except Exception as e:
                    print(f"无法创建存储目录: {str(e)}")
            
            # 确保extracted目录存在
            extracted_dir = os.path.join(storage_dir, "extracted")
            if not os.path.exists(extracted_dir):
                try:
                    os.makedirs(extracted_dir)
                except Exception as e:
                    print(f"无法创建extracted目录: {str(e)}")
            
            # 返回结果
            self.finished.emit(True, cleared_items, total_items, "")
            
        except Exception as e:
            self.finished.emit(False, 0, 0, str(e))
    
    def cancel(self):
        """取消操作"""
        self.is_cancelled = True 