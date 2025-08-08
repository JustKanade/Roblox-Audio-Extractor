#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import multiprocessing
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import (
    SimpleCardWidget, StrongBodyLabel, BodyLabel, CaptionLabel,
    HyperlinkButton, FluentIcon
)

# 导入必要的模块用于系统信息
from src.extractors.audio_extractor import is_ffmpeg_available


class LinksAndSupportCard(SimpleCardWidget):
    """链接和支持信息卡片"""
    
    def __init__(self, parent=None, lang=None):
        super().__init__(parent)
        self.lang = lang
        
        # 确保语言对象存在，否则创建空的语言处理函数
        if self.lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = self.lang.get
        
        self.setMaximumHeight(180)
        self._setupUI()
    
    def _setupUI(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # 标题
        title = StrongBodyLabel(self.get_text("links_and_support", "Links & Support"))
        layout.addWidget(title)
        
        # GitHub链接
        github_layout = QHBoxLayout()
        github_btn = HyperlinkButton(
            "https://github.com/JustKanade/Roblox-Audio-Extractor",
            self.get_text("github_link", "GitHub Repository")
        )
        github_btn.setIcon(FluentIcon.GITHUB)
        github_layout.addWidget(github_btn)
        github_layout.addStretch()
        
        layout.addLayout(github_layout)
        
        # 技术信息
        tech_info = f"""
{self.get_text('tech_stack', 'Tech Stack')}: Python 3.x + PyQt5 + PyQt-Fluent-Widgets
{self.get_text('purpose', 'Purpose')}: Roblox {self.get_text('extract_audio', 'Audio Extraction')}
{self.get_text('license', 'License')}: GNU AGPLv3
        """.strip()
        
        tech_label = CaptionLabel(tech_info)
        layout.addWidget(tech_label)


class SystemInfoCard(SimpleCardWidget):
    """系统信息卡片"""
    
    def __init__(self, parent=None, lang=None):
        super().__init__(parent)
        self.lang = lang
        
        # 确保语言对象存在，否则创建空的语言处理函数
        if self.lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = self.lang.get
        
        self._setupUI()
    
    def _setupUI(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # 标题
        title = StrongBodyLabel(self.get_text("system_info", "System Information"))
        layout.addWidget(title)
        
        # 收集系统信息
        system_info = f"""
{self.get_text('operating_system', 'OS')}: {os.name} ({sys.platform})
{self.get_text('python_version', 'Python')}: {sys.version.split()[0]}
{self.get_text('cpu_cores', 'CPU Cores')}: {multiprocessing.cpu_count()}
{self.get_text('ffmpeg_status', 'FFmpeg')}: {self.get_text('available', 'Available') if is_ffmpeg_available() else self.get_text('not_available', 'Not Available')}
        """.strip()
        
        system_info_label = CaptionLabel(system_info)
        layout.addWidget(system_info_label) 