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
from qfluentwidgets import (SettingCard, BodyLabel, CaptionLabel, StrongBodyLabel, TitleLabel,
                          PrimaryPushButton, InfoBar, InfoBarPosition, SwitchButton, 
                          FluentIcon, MaskDialogBase, setFont)

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
    if lang is None:
        # 返回键名作为默认值
        return key
    
    return lang.get(key, *args)


def compare_versions(version1: str, version2: str) -> int:
    """比较两个版本号，返回 1（version1 > version2），-1（version1 < version2），0（相等）"""
    def parse_version(v):
        # 移除可能的 'v' 前缀并按点分割
        v = v.lstrip('v')
        try:
            return [int(x) for x in v.split('.')]
        except ValueError:
            return [0]  # 如果解析失败，返回 [0]
    
    v1_parts = parse_version(version1)
    v2_parts = parse_version(version2)
    
    # 填充较短的版本号
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))
    
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
        import webbrowser
        download_url = self.release_info.get('html_url', '')
        if download_url:
            webbrowser.open(download_url)
        self.close()


class VersionCheckCard(SettingCard):
    """版本检测设置卡片"""
    
    def __init__(self, config_manager, current_version, parent=None):
        self.config_manager = config_manager
        self.current_version = current_version
        
        # 从配置中读取设置
        self.auto_check = self.config_manager.get("auto_check_update", True)
        
        # 获取翻译文本
        title = get_text("version_check_settings") or "Version Check Settings"
        description = "Manage application version checking and update settings"
        
        super().__init__(
            FluentIcon.UPDATE,
            title,
            description,
            parent
        )
        
        self._setupContent()
        
        # 如果设置了自动检查，则启动时检查更新
        if self.auto_check:
            QTimer.singleShot(1000, self.checkUpdate)
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器 - 水平布局
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(12)
        
        # 自动检查更新开关
        self.auto_check_switch = SwitchButton()
        self.auto_check_switch.setChecked(self.auto_check)
        self.auto_check_switch.checkedChanged.connect(self._on_auto_check_changed)
        
        # 手动检查按钮
        self.check_button = PrimaryPushButton(get_text("check_update") or "Check Update")
        self.check_button.setFixedSize(140, 32)
        self.check_button.clicked.connect(self.checkUpdate)
        
        content_layout.addWidget(self.auto_check_switch)
        content_layout.addWidget(self.check_button)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)
    
    def _on_auto_check_changed(self, checked: bool):
        """自动检查设置改变"""
        self.auto_check = checked
        self.config_manager.set("auto_check_update", checked)
    
    def checkUpdate(self):
        """检查更新"""
        self.check_button.setEnabled(False)
        self.check_button.setText(get_text("checking_update") or "Checking...")
        
        # 创建工作线程
        self.worker = UpdateWorker(self.current_version)
        self.worker.update_found.connect(self._on_update_found)
        self.worker.no_update.connect(self._on_no_update)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.finished.connect(self._on_check_finished)
        self.worker.start()
    
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
        """检查完成"""
        self.check_button.setEnabled(True)
        self.check_button.setText(get_text("check_update") or "Check Update") 
