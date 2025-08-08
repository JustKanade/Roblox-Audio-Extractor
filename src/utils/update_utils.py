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

from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt, QSize, QUrl
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, 
                             QLabel, QDialog, QDialogButtonBox, QSizePolicy)
from PyQt5.QtGui import QColor, QDesktopServices
from qfluentwidgets import (BodyLabel, CaptionLabel, StrongBodyLabel, TitleLabel,
                          PrimaryPushButton, InfoBar, InfoBarPosition, 
                          FluentIcon, MaskDialogBase, setFont, SettingCard,
                          IconWidget, SubtitleLabel, SimpleCardWidget, 
                          TransparentToolButton, TextEdit, PushButton, 
                          isDarkTheme)

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
                "https://api.github.com/repos/JustKanade/Roblox-Audio-Extractor/releases/latest",
                "https://api.github.com/repos/JustKanade/roblox-audio-extractor/releases/latest"
            ]
            
            response = None
            last_error = None
            
            for url in possible_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 403:
                        # GitHub API限制
                        last_error = get_text("api_rate_limit") or "GitHub API rate limit exceeded. Please try again later."
                    elif response.status_code == 404:
                        # 仓库不存在
                        last_error = get_text("repository_not_found") or "Repository not found."
                    else:
                        # 其他HTTP错误
                        last_error = f"HTTP {response.status_code}"
                except requests.exceptions.Timeout:
                    last_error = get_text("connection_timeout") or "Connection timeout"
                except requests.exceptions.ConnectionError:
                    last_error = get_text("connection_error") or "Network connection error"
                except Exception as e:
                    last_error = str(e)
                    continue
            
            # 检查API调用是否成功
            if response is None or response.status_code != 200:
                # API调用失败，发送错误信号
                error_msg = last_error or (get_text("network_error") or "Network error occurred")
                self.error_occurred.emit(error_msg)
                return
            
            # 解析响应数据
            try:
                release_data = response.json()
                latest_version = release_data["tag_name"].lstrip("v")
            except (KeyError, ValueError) as e:
                # JSON解析失败
                self.error_occurred.emit(get_text("invalid_response") or "Invalid response from server")
                return
            
            # 版本比较
            if compare_versions(latest_version, self.current_version) > 0:
                self.update_found.emit(release_data)
            else:
                # 真正的"已是最新版本"
                self.no_update.emit(latest_version)
                
        except Exception as e:
            # 捕获所有其他异常，发送错误信号
            error_msg = get_text("unexpected_error") or f"Unexpected error: {str(e)}"
            self.error_occurred.emit(error_msg)


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
        # 使用格式化的错误标题
        title = get_text("check_failed", error_message) or f"Check Failed: {error_message}"
        InfoBar.error(
            title=title[:50] + "..." if len(title) > 50 else title,  # 限制标题长度
            content=error_message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,  # 增加显示时间，让用户有足够时间阅读错误信息
            parent=self.window()
        )
    
    def _on_check_finished(self):
        """检查完成的回调，子类可以重写"""
        pass


class UpdateDialog(MaskDialogBase):
    """更新对话框"""
    
    def __init__(self, release_info: dict, parent=None):
        """初始化更新对话框
        
        Args:
            release_info: GitHub发布信息字典
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 保存必要的数据
        self.release_info = release_info
        self.release_url = release_info.get('html_url', '')
        self.release_notes = release_info.get('body', '')
        self.version = release_info.get('tag_name', '').lstrip('v')
        self.title = get_text("update_available") or "Update Available!"
        
        # 设置窗口属性
        self.setWindowTitle(self.title)
        self.setMaskColor(QColor(0, 0, 0, 120))  # 半透明黑色蒙版
        
        # 创建对话框内容
        self.setupUI()
        
        # 添加漂亮的阴影效果
        self.setShadowEffect(blurRadius=40, offset=(0, 6), color=QColor(0, 0, 0, 60))
    
    def setupUI(self):
        """设置对话框UI"""
        # 获取对话框的内容区域
        self.widget.setFixedWidth(520)
        self.widget.setMinimumHeight(480)
        
        # 设置边框圆角和样式
        if isDarkTheme():
            self.widget.setStyleSheet("""
                background-color: #2b2b2b;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            """)
            text_color = "#ffffff"
            secondary_color = "rgba(255, 255, 255, 0.65)"
            card_bg = "#363636"
            separator_color = "rgba(255, 255, 255, 0.1)"
        else:
            self.widget.setStyleSheet("""
                background-color: white;
                border-radius: 10px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            """)
            text_color = "#202020"
            secondary_color = "rgba(0, 0, 0, 0.65)"
            card_bg = "#f5f5f5"
            separator_color = "rgba(0, 0, 0, 0.08)"
        
        # 创建主布局
        self.mainLayout = QVBoxLayout(self.widget)
        self.mainLayout.setContentsMargins(24, 20, 24, 24)
        self.mainLayout.setSpacing(16)
        
        # === 标题栏区域 ===
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)
        
        # 添加标题图标
        icon = IconWidget(FluentIcon.UPDATE, self.widget)
        icon.setFixedSize(28, 28)
        
        # 标题文本
        titleLabel = TitleLabel(self.title, self.widget)
        titleLabel.setStyleSheet(f"color: {text_color}; font-weight: bold; border: none;")
        
        # 关闭按钮
        closeBtn = TransparentToolButton(FluentIcon.CLOSE, self.widget)
        closeBtn.setFixedSize(32, 32)
        closeBtn.setIconSize(QSize(16, 16))
        closeBtn.clicked.connect(self.reject)
        
        header.addWidget(icon)
        header.addWidget(titleLabel, 1)
        header.addWidget(closeBtn)
        
        self.mainLayout.addLayout(header)
        
        # === 版本信息区域 ===
        versionInfo = QHBoxLayout()
        versionInfo.setContentsMargins(0, 4, 0, 4)
        
        # 获取主题色
        themeColor = self._getThemeColor()
        
        # 最新版本标签
        versionLabel = StrongBodyLabel(get_text("latest_version", self.version) or f"Latest Version: {self.version}")
        versionLabel.setStyleSheet(f"color: {themeColor.name()}; border: none;")
        
        versionInfo.addWidget(versionLabel)
        versionInfo.addStretch()
        
        self.mainLayout.addLayout(versionInfo)
        
        # === 更新内容标题区域 ===
        notesHeader = QHBoxLayout()
        notesHeader.setContentsMargins(0, 12, 0, 8)  # 增加上边距，替代分隔线的视觉效果
        notesHeader.setSpacing(8)
        
        # 添加图标
        noteIcon = IconWidget(FluentIcon.DOCUMENT, self.widget)
        noteIcon.setFixedSize(16, 16)
        
        # 更新内容标题
        notesTitle = SubtitleLabel(get_text("release_notes") or "Release Notes")
        notesTitle.setStyleSheet(f"color: {text_color}; font-weight: bold; border: none;")

        notesHeader.addWidget(noteIcon)
        notesHeader.addWidget(notesTitle)
        notesHeader.addStretch()
        
        self.mainLayout.addLayout(notesHeader)
        
        # === 更新内容卡片 ===
        contentCard = SimpleCardWidget(self.widget)
        contentCard.setBorderRadius(8)
        contentCard.setStyleSheet(f"""
            background-color: {card_bg};
            border-radius: 8px;
            border: none;
        """)
        
        contentLayout = QVBoxLayout(contentCard)
        contentLayout.setContentsMargins(16, 16, 16, 16)
        
        # 格式化并显示更新内容
        self.notesEdit = TextEdit(contentCard)
        self.notesEdit.setReadOnly(True)
        self.notesEdit.setText(self._formatReleaseNotes(self.release_notes))
        self.notesEdit.setStyleSheet(f"""
            border: none;
            background-color: transparent;
            color: {text_color};
            selection-background-color: {themeColor.name()};
        """)
        self.notesEdit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.notesEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.notesEdit.setMinimumHeight(200)
        
        # 设置文档边距为0
        try:
            document = self.notesEdit.document()
            if document:
                document.setDocumentMargin(0)
        except:
            pass
        
        contentLayout.addWidget(self.notesEdit)
        
        self.mainLayout.addWidget(contentCard, 1)  # 添加伸展因子，使内容区域可伸缩
        
        # === 按钮区域 ===
        buttonLayout = QHBoxLayout()
        buttonLayout.setContentsMargins(0, 8, 0, 0)
        buttonLayout.setSpacing(12)
        
        # 取消按钮
        self.cancelButton = PushButton(get_text("close") or "Close")
        self.cancelButton.clicked.connect(self.reject)
        
        # 更新按钮
        self.updateButton = PrimaryPushButton(get_text("download_update") or "Download Update")
        self.updateButton.setIcon(FluentIcon.LINK)
        self.updateButton.clicked.connect(self.download_update)
        
        # 调整按钮大小
        self.cancelButton.setMinimumWidth(100)
        self.updateButton.setMinimumWidth(140)
        
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.updateButton)
        
        self.mainLayout.addLayout(buttonLayout)
    
    def _getThemeColor(self):
        """获取主题颜色"""
        try:
            # 尝试使用qfluentwidgets的主题色
            try:
                from qfluentwidgets import themeColor
                return themeColor()
            except (ImportError, AttributeError):
                pass
                
            # 默认蓝色
            return QColor(0, 120, 212)
        except:
            return QColor(0, 120, 212)
    
    def _formatReleaseNotes(self, notes):
        """格式化发布说明内容，使其更美观"""
        if not notes:
            return ""
            
        # 替换Markdown标题为大写粗体文本
        formatted = notes
        
        # 确保每个项目符号前后有足够的空间
        formatted = formatted.replace("\n- ", "\n\n- ")
        
        # 确保段落之间有足够的空间
        formatted = formatted.replace("\n\n\n", "\n\n")
        
        # 处理Markdown标题
        lines = formatted.split("\n")
        result = []
        
        for line in lines:
            if line.startswith("## "):
                result.append("\n" + line.replace("## ", "").upper() + "\n")
            elif line.startswith("# "):
                result.append("\n" + line.replace("# ", "").upper() + "\n")
            else:
                result.append(line)
                
        return "\n".join(result)
    
    def download_update(self):
        """下载更新"""
        if self.release_url:
            QDesktopServices.openUrl(QUrl(self.release_url))
        self.accept() 