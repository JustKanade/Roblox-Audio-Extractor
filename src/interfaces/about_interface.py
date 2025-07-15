#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

from qfluentwidgets import (
    CardWidget, TitleLabel, SubtitleLabel,
    StrongBodyLabel, BodyLabel, CaptionLabel, 
    HyperlinkButton, FluentIcon, IconWidget,
    DisplayLabel, ScrollArea
)

from src.utils.file_utils import resource_path
import os
import sys


class AboutInterface(QWidget):
    """关于界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None):
        super().__init__(parent)
        self.setObjectName("aboutInterface")
        self.config_manager = config_manager
        self.lang = lang
        
        # 确保语言对象存在，否则创建空的语言处理函数
        if self.lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = self.lang.get
        
        # 初始化界面
        self.initUI()
        # 应用样式
        self.setAboutStyles()
        
    def initUI(self):
        """初始化界面"""
        # 创建滚动区域
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # 关于应用卡片
        about_card = CardWidget()
        about_card.setMaximumHeight(200)  # 添加最大高度值
        about_layout = QVBoxLayout(about_card)
        # 应用头部
        header_layout = QHBoxLayout()

        # 左侧：图标和基本信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        app_title = DisplayLabel("Roblox Audio Extractor")
        app_title.setObjectName("aboutTitle")

        version_label = SubtitleLabel(self.get_text("about_version", "Version: 0.16.1"))
        version_label.setObjectName("aboutVersion")

        author_label = BodyLabel(self.get_text("about_author", "By JustKanade"))
        license_label = CaptionLabel(self.get_text("about_license", "Licensed under GNU AGPLv3"))

        info_layout.addWidget(app_title)
        info_layout.addWidget(version_label)
        info_layout.addSpacing(10)
        info_layout.addWidget(author_label)
        info_layout.addWidget(license_label)

        # 右侧：应用图标
        icon_widget = QWidget()
        icon_widget.setFixedSize(120, 120)
        icon_layout = QVBoxLayout(icon_widget)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        self.about_icon_label = QLabel()
        self.about_icon_label.setAlignment(Qt.AlignCenter)
        self.loadAboutIcon()
        icon_layout.addWidget(self.about_icon_label)

        header_layout.addLayout(info_layout, 2)
        header_layout.addWidget(icon_widget, 1)

        about_layout.addLayout(header_layout)

        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: rgba(255, 255, 255, 0.2); }")
        about_layout.addWidget(separator)

        # 应用描述
        desc_label = BodyLabel(self.get_text("about_description", "A tool to extract audio files from Roblox cache."))
        desc_label.setWordWrap(True)
        about_layout.addWidget(desc_label)

        content_layout.addWidget(about_card)

        # 链接和支持卡片
        links_card = CardWidget()
        links_card.setMaximumHeight(180)  # 限制最大高度，防止异常放大
        links_layout = QVBoxLayout(links_card)
        links_layout.setContentsMargins(20, 15, 20, 15)
        links_layout.setSpacing(15)

        links_title = StrongBodyLabel(self.get_text("links_and_support", "Links & Support"))
        links_layout.addWidget(links_title)

        # GitHub链接
        github_layout = QHBoxLayout()
        github_btn = HyperlinkButton(
            "https://github.com/JustKanade/Roblox-Audio-Extractor",
            self.get_text("github_link", "GitHub Repository")
        )
        github_btn.setIcon(FluentIcon.GITHUB)
        github_layout.addWidget(github_btn)
        github_layout.addStretch()

        links_layout.addLayout(github_layout)

        # 技术信息
        tech_info = f"""
{self.get_text('tech_stack', 'Tech Stack')}: Python 3.x + PyQt5 + PyQt-Fluent-Widgets
{self.get_text('purpose', 'Purpose')}: Roblox {self.get_text('extract_audio', 'Audio Extraction')}
{self.get_text('license', 'License')}: GNU AGPLv3
        """.strip()

        tech_label = CaptionLabel(tech_info)
        links_layout.addWidget(tech_label)

        content_layout.addWidget(links_card)

        # 系统信息卡片
        system_card = CardWidget()
        system_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)  # 关键：防止高度异常拉伸

        system_layout = QVBoxLayout(system_card)
        system_layout.setContentsMargins(20, 15, 20, 15)
        system_layout.setSpacing(10)

        system_title = StrongBodyLabel(self.get_text("system_info", "System Information"))
        system_layout.addWidget(system_title)

        # 导入必要的模块
        import multiprocessing
        from src.extractors.audio_extractor import is_ffmpeg_available
        
        # 收集系统信息
        system_info = f"""
{self.get_text('operating_system', 'OS')}: {os.name} ({sys.platform})
{self.get_text('python_version', 'Python')}: {sys.version.split()[0]}
{self.get_text('cpu_cores', 'CPU Cores')}: {multiprocessing.cpu_count()}
{self.get_text('ffmpeg_status', 'FFmpeg')}: {self.get_text('available', 'Available') if is_ffmpeg_available() else self.get_text('not_available', 'Not Available')}
        """.strip()

        system_info_label = CaptionLabel(system_info)
        system_layout.addWidget(system_info_label)

        content_layout.addWidget(system_card)
        
        # 添加伸缩空间，确保内容顶部对齐
        content_layout.addStretch()

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
    def loadAboutIcon(self):
        """加载关于页面图标"""
        try:
            icon_path = resource_path(os.path.join("res", "icons", "logo.png"))
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                scaled_pixmap = pixmap.scaled(
                    100, 100,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.about_icon_label.setPixmap(scaled_pixmap)
            else:
                # 使用默认图标
                self.about_icon_label.setText("♪")
                font = QFont()
                font.setPointSize(64)
                self.about_icon_label.setFont(font)
                self.about_icon_label.setAlignment(Qt.AlignCenter)
        except Exception as e:
            print(f"无法加载关于页面图标: {e}")
            
    def setAboutStyles(self):
        """设置关于页面样式"""
        if self.config_manager:
            theme = self.config_manager.get("theme", "dark")
        else:
            theme = "dark"

        if theme == "light":
            self.setStyleSheet("""
                #aboutTitle {
                    color: rgb(0, 0, 0);
                    font-size: 32px;
                    font-weight: bold;
                }
                #aboutVersion {
                    color: rgb(0, 120, 215);
                    font-size: 18px;
                    font-weight: 600;
                }
            """)
        else:
            self.setStyleSheet("""
                #aboutTitle {
                    color: rgb(255, 255, 255);
                    font-size: 32px;
                    font-weight: bold;
                }
                #aboutVersion {
                    color: rgb(0, 212, 255);
                    font-size: 18px;
                    font-weight: 600;
                }
            """) 