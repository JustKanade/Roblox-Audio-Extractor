#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关于页面卡片组件
About Page Card Components
"""

import os
import sys
import multiprocessing
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget

from qfluentwidgets import (
    SettingCard, HyperlinkCard, CardWidget, 
    StrongBodyLabel, BodyLabel, CaptionLabel,
    FluentIcon, IconWidget, HyperlinkButton, PrimaryPushSettingCard
)

# 导入必要的模块用于系统信息
from src.extractors.audio_extractor import is_ffmpeg_available


class GitHubLinkCard(SettingCard):
    """GitHub链接卡片"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        super().__init__(
            FluentIcon.GITHUB,
            self.get_text("github_repository", "GitHub Repository"),
            self.get_text("github_description", "View source code, report issues, and contribute to the project"),
            parent
        )
        
        self._setupContent()
    
    def _setupContent(self):
        """设置内容"""
        
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 创建带图标的GitHub按钮
        self.github_button = HyperlinkButton(
            url="https://github.com/JustKanade/Roblox-Audio-Extractor",
            text=self.get_text("github_link", "View on GitHub"),
            parent=content_widget
        )
        self.github_button.setIcon(FluentIcon.LINK)
        self.github_button.setFixedSize(160, 35)
        
        content_layout.addWidget(self.github_button)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)


class FeedbackCard(PrimaryPushSettingCard):
    """提供反馈卡片"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        super().__init__(
            self.get_text("provide_feedback", "Provide feedback"),
            FluentIcon.FEEDBACK,
            self.get_text("provide_feedback", "Provide feedback"),
            self.get_text("feedback_description", "Help us improve Roblox Audio Extractor by providing feedback"),
            parent
        )
        
        # 连接点击事件
        self.clicked.connect(self._open_feedback_url)
    
    def _open_feedback_url(self):
        """打开反馈页面"""
        from PyQt5.QtCore import QUrl
        from PyQt5.QtGui import QDesktopServices
        
        # 打开GitHub Issues页面进行反馈
        feedback_url = "https://github.com/JustKanade/Roblox-Audio-Extractor/issues"
        QDesktopServices.openUrl(QUrl(feedback_url))


class SystemInfoCard(SettingCard):
    """系统信息卡片"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        # 收集系统信息
        system_info = f"{os.name} ({sys.platform}) | Python {sys.version.split()[0]} | {multiprocessing.cpu_count()} {self.get_text('cpu_cores', 'CPU Cores')}"
        
        super().__init__(
            FluentIcon.APPLICATION,
            self.get_text("system_info", "System Information"),
            system_info,
            parent
        )


class TechStackCard(SettingCard):
    """技术栈信息卡片"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        tech_info = f"Python 3.x + PyQt5 + PyQt-Fluent-Widgets"
        
        super().__init__(
            FluentIcon.CODE,
            self.get_text('tech_stack', 'Tech Stack'),
            tech_info,
            parent
        )
        
        self._setupContent()
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 创建跳转到PyQt-Fluent-Widgets官网的按钮
        self.fluent_button = HyperlinkButton(
            url="https://qfluentwidgets.com/",
            text=self.get_text("visit_fluent_widgets", "View on GitHub"),
            parent=content_widget
        )
        self.fluent_button.setIcon(FluentIcon.LINK)
        self.fluent_button.setFixedSize(160, 35)
        
        content_layout.addWidget(self.fluent_button)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)


class VersionInfoCard(SettingCard):
    """版本信息卡片"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        version_info = f" {self.get_text('license', 'License')}: GNU AGPLv3 | {self.get_text('about_author', 'By JustKanade')}"
        
        super().__init__(
            FluentIcon.INFO,
            self.get_text("about_version", "Version & License"),
            version_info,
            parent
        ) 