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
from qfluentwidgets import (ExpandSettingCard, BodyLabel, CaptionLabel, StrongBodyLabel, TitleLabel,
                          PrimaryPushButton, InfoBar, InfoBarPosition, SwitchButton, 
                          FluentIcon, MaskDialogBase, setFont)
import requests
import json

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
            # GitHub API获取最新发布信息
            url = "https://api.github.com/repos/DiaoDaiaChan/Roblox-Audio-Extractor/releases/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data["tag_name"].lstrip("v")
            
            # 版本比较
            if compare_versions(latest_version, self.current_version) > 0:
                self.update_found.emit(release_data)
            else:
                self.no_update.emit(latest_version)
                
        except Exception as e:
            self.error_occurred.emit(str(e))


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
        title_label = TitleLabel(get_text("latest_version") or "最新版本")
        layout.addWidget(title_label)
        
        # 版本号
        version_label = StrongBodyLabel(f"v{self.release_info['tag_name'].lstrip('v')}")
        layout.addWidget(version_label)
        
        # 更新说明标题
        notes_title = BodyLabel(get_text("release_notes") or "更新说明:")
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
        
        self.download_button = PrimaryPushButton(get_text("download_update") or "下载更新")
        self.download_button.clicked.connect(self.download_update)
        
        self.cancel_button = PrimaryPushButton(get_text("cancel") or "取消")
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


class VersionCheckCard(ExpandSettingCard):
    """版本检测设置卡片"""
    
    def __init__(self, config_manager, current_version, parent=None):
        self.config_manager = config_manager
        self.current_version = current_version
        
        # 从配置中读取设置
        self.auto_check = self.config_manager.get("auto_check_update", True)
        
        # 获取翻译文本
        title = ""
        description = ""
        if lang:
            title = lang.get("version_check_settings") or ""
            description = lang.get("version_check_description") or ""
        
        super().__init__(
            FluentIcon.UPDATE,
            title or "版本检测设置",
            description or "管理应用程序版本检查和更新设置",
            parent
        )
        
        self._setupContent()
        
        # 如果设置了自动检查，则启动时检查更新
        if self.auto_check:
            QTimer.singleShot(1000, self.checkUpdate)
    
    def _setupContent(self):
        """设置内容"""
        # 创建内容控件
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        # 自动检查更新开关
        auto_check_layout = QHBoxLayout()
        auto_check_label = BodyLabel(get_text("auto_check_update") or "启动时自动检查更新")
        setFont(auto_check_label, 13)
        
        self.auto_check_switch = SwitchButton()
        self.auto_check_switch.setChecked(self.auto_check)
        self.auto_check_switch.checkedChanged.connect(self._on_auto_check_changed)
        
        auto_check_layout.addWidget(auto_check_label)
        auto_check_layout.addStretch()
        auto_check_layout.addWidget(self.auto_check_switch)
        
        content_layout.addLayout(auto_check_layout)
        
        # 当前版本显示
        version_layout = QHBoxLayout()
        version_label = BodyLabel(get_text("current_version") or "当前版本:")
        self.version_value = BodyLabel(f"v{self.current_version}")
        setFont(version_label, 13)
        setFont(self.version_value, 13)
        
        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_value)
        version_layout.addStretch()
        
        content_layout.addLayout(version_layout)
        
        # 检查更新按钮
        self.check_button = PrimaryPushButton(get_text("check_update") or "检查更新")
        self.check_button.clicked.connect(self.checkUpdate)
        content_layout.addWidget(self.check_button)
        
        # 状态标签
        self.status_label = CaptionLabel("")
        self.status_label.setStyleSheet("color: gray;")
        content_layout.addWidget(self.status_label)
        
        # 使用正确的API添加内容
        self.addWidget(content_widget)
    
    def _on_auto_check_changed(self, checked: bool):
        """自动检查设置改变"""
        self.auto_check = checked
        self.config_manager.set("auto_check_update", checked)
    
    def checkUpdate(self):
        """检查更新"""
        self.check_button.setEnabled(False)
        self.check_button.setText(get_text("checking_update") or "正在检查更新...")
        self.status_label.setText("")
        
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
            title=get_text("update_available") or "发现新版本",
            content=f"v{release_info['tag_name'].lstrip('v')}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
        # 显示更新对话框
        dialog = UpdateDialog(release_info, self)
        dialog.show()
        
        self.status_label.setText(f"发现新版本: v{release_info['tag_name'].lstrip('v')}")
    
    def _on_no_update(self, current_version: str):
        """已是最新版本"""
        InfoBar.success(
            title=get_text("already_latest") or "已是最新版本",
            content=f"v{current_version}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
        self.status_label.setText("已是最新版本")
    
    def _on_error(self, error_message: str):
        """检查失败"""
        InfoBar.error(
            title=get_text("check_failed") or "检查失败",
            content=error_message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
        self.status_label.setText(f"检查失败: {error_message}")
    
    def _on_check_finished(self):
        """检查完成"""
        self.check_button.setEnabled(True)
        self.check_button.setText(get_text("check_update") or "检查更新") 
