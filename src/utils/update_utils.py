#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import sys
import subprocess
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any
import webbrowser
import time
from urllib.parse import urlparse
from urllib.request import urlopen, urlretrieve

from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, 
                             QLabel, QDialog, QDialogButtonBox)
from qfluentwidgets import (BodyLabel, CaptionLabel, StrongBodyLabel, TitleLabel,
                          PrimaryPushButton, InfoBar, InfoBarPosition, 
                          FluentIcon, MaskDialogBase, setFont, SettingCard)

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None

def set_language_manager(language_manager):
    """设置语言管理器"""
    global lang
    lang = language_manager

def get_text(key: str, *args) -> str:
    """获取翻译文本的便利函数"""
    if lang and hasattr(lang, 'get'):
        return lang.get(key, *args)
    return key

def compare_versions(version1: str, version2: str) -> int:
    """比较版本号
    
    Args:
        version1: 第一个版本号
        version2: 第二个版本号
        
    Returns:
        int: 1 if version1 > version2, -1 if version1 < version2, 0 if equal
    """
    def normalize_version(v):
        # 移除 'v' 前缀并分割版本号
        v = v.lstrip('v')
        parts = []
        for part in v.split('.'):
            # 提取数字部分
            num_part = ''
            for char in part:
                if char.isdigit():
                    num_part += char
                else:
                    break
            if num_part:
                parts.append(int(num_part))
            else:
                parts.append(0)
        return parts
    
    v1_parts = normalize_version(version1)
    v2_parts = normalize_version(version2)
    
    # 补齐长度
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))
    
    # 比较
    for i in range(max_len):
        if v1_parts[i] > v2_parts[i]:
            return 1
        elif v1_parts[i] < v2_parts[i]:
            return -1
    
    return 0


class UpdateWorker(QThread):
    """更新检查工作线程"""
    update_found = pyqtSignal(dict)
    no_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
    
    def run(self):
        try:
            # 尝试不同的可能仓库URL
            possible_urls = [
                "https://api.github.com/repos/DiaoDaiaChan/Roblox-Audio-Extractor/releases/latest",
                "https://api.github.com/repos/diodaiachan/Roblox-Audio-Extractor/releases/latest",
                "https://api.github.com/repos/DiaoDaiaChan/roblox-audio-extractor/releases/latest"
            ]
            
            response = None
            for url in possible_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        break
                except:
                    continue
            
            if response is None or response.status_code != 200:
                # 如果所有URL都失败，创建模拟数据表示当前版本就是最新的
                self.no_update.emit(self.current_version)
                return
            
            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip("v")
            
            # 版本比较
            if compare_versions(latest_version, self.current_version) > 0:
                self.update_found.emit(release_data)
            else:
                self.no_update.emit(latest_version)
                
        except Exception as e:
            # 如果检查失败，默认认为当前版本是最新的
            self.no_update.emit(self.current_version)


class BaseUpdateCard(SettingCard):
    """更新检查卡片基类，包含公共的更新检查逻辑"""
    
    def __init__(self, icon, title, description, parent=None):
        super().__init__(icon, title, description, parent)
        self.update_worker = None
        
    def _check_for_updates(self):
        """执行更新检查的公共方法"""
        if not hasattr(self, 'current_version'):
            self._on_error(get_text("version_not_available") or "Version not available")
            return
            
        # 启动更新检查线程
        self.update_worker = UpdateWorker(self.current_version)
        self.update_worker.update_found.connect(self._on_update_found)
        self.update_worker.no_update.connect(self._on_no_update)
        self.update_worker.error_occurred.connect(self._on_error)
        self.update_worker.finished.connect(self._on_check_finished)
        self.update_worker.start()
    
    def _on_update_found(self, release_info: dict):
        """发现更新"""
        InfoBar.success(
            title=get_text("update_available") or "Update Available",
            content=f"v{release_info['tag_name'].lstrip('v')}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )
        
        # 显示更新对话框
        dialog = UpdateDialog(release_info, self.window())
        dialog.show()
    
    def _on_no_update(self, current_version: str):
        """已是最新版本"""
        InfoBar.success(
            title=get_text("already_latest") or "Already Latest Version",
            content=f"v{current_version}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )
    
    def _on_error(self, error_message: str):
        """检查失败"""
        InfoBar.error(
            title=get_text("check_failed") or "Check Failed",
            content=error_message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )
    
    def _on_check_finished(self):
        """检查完成的回调，子类可以重写"""
        pass


class UpdateDialog(MaskDialogBase):
    """更新对话框"""
    
    def __init__(self, release_info: dict, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self.setupUI()
    
    def setupUI(self):
        self.setFixedSize(600, 400)
        
        # 主布局
        layout = QVBoxLayout()
        
        # 标题
        title_label = TitleLabel(get_text("latest_version") or "Latest Version")
        layout.addWidget(title_label)
        
        # 版本号
        version_label = StrongBodyLabel(f"v{self.release_info['tag_name'].lstrip('v')}")
        layout.addWidget(version_label)
        
        # 更新说明标题
        notes_title = BodyLabel(get_text("release_notes") or "Release Notes:")
        setFont(notes_title, 13)
        layout.addWidget(notes_title)
        
        # 更新内容
        content_edit = QTextEdit()
        content_edit.setReadOnly(True)
        content_edit.setPlainText(self.release_info.get('body', ''))
        content_edit.setMaximumHeight(200)
        layout.addWidget(content_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.download_button = PrimaryPushButton(get_text("download_update") or "Download Update")
        self.download_button.clicked.connect(self.download_update)
        
        self.cancel_button = PrimaryPushButton(get_text("cancel") or "Cancel")
        self.cancel_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # 设置布局
        widget = QWidget()
        widget.setLayout(layout)
        self.widget.setLayout(QVBoxLayout())
        self.widget.layout().addWidget(widget)
    
    def download_update(self):
        """下载更新"""
        download_url = self.release_info.get('html_url')

        if download_url:
            webbrowser.open(download_url)
        self.close() 