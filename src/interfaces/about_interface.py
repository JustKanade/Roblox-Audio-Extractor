#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QFont

from qfluentwidgets import (
    CardWidget, TitleLabel, SubtitleLabel,
    StrongBodyLabel, BodyLabel, CaptionLabel, 
    HyperlinkButton, FluentIcon, IconWidget,
    DisplayLabel, ScrollArea, isDarkTheme, setTheme, Theme,
    SettingCardGroup, ExpandLayout
)

from src.utils.file_utils import resource_path
from src.components.cards.about_cards import (
    GitHubLinkCard, SystemInfoCard, TechStackCard, VersionInfoCard, FeedbackCard
)
from src.components.cards.Settings.ffmpeg_status_card import FFmpegStatusCard
import os
import sys


class BannerWidget(CardWidget):
    """ 横幅小部件 """

    def __init__(self, parent=None, config_manager=None, lang=None):
        super().__init__(parent=parent)
        self.setFixedHeight(200)  # 设置固定高度
        self.config_manager = config_manager
        self.lang = lang
        
        # 确保语言对象存在，否则创建空的语言处理函数
        if self.lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = self.lang.get
        
        # 初始化UI
        self.initUI()

    def initUI(self):
        """初始化UI"""
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(8)
        self.vBoxLayout.setContentsMargins(20, 20, 20, 15)
        
        # 创建水平布局，左侧文本，右侧图标
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        
        # 左侧：文本内容
        text_container = QWidget()
        text_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(8)
        
        # 应用标题与版本信息
        self.app_title = DisplayLabel("Roblox Audio Extractor")
        self.app_title.setObjectName("aboutTitle")
        
        self.version_label = SubtitleLabel(self.get_text("about_version"))
        self.version_label.setObjectName("aboutVersion")
        
        # 作者和许可证信息
        self.author_label = BodyLabel(self.get_text("about_author", "By JustKanade"))
        self.license_label = CaptionLabel(self.get_text("about_license", "Licensed under GNU AGPLv3"))
        
        # 应用描述
        self.desc_label = BodyLabel(self.get_text("about_description", "A tool to extract audio files from Roblox cache."))
        self.desc_label.setWordWrap(True)
        
        # 添加到文本布局
        text_layout.addWidget(self.app_title)
        text_layout.addWidget(self.version_label)
        text_layout.addSpacing(10)
        text_layout.addWidget(self.author_label)
        text_layout.addWidget(self.license_label)
        text_layout.addSpacing(10)
        text_layout.addWidget(self.desc_label)
        text_layout.addStretch(1)
        
        # 右侧：图标
        self.icon_container = QWidget()
        self.icon_container.setFixedSize(120, 120)
        self.icon_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        icon_layout = QVBoxLayout(self.icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        self.about_icon_label = QLabel()
        self.about_icon_label.setAlignment(Qt.AlignCenter)
        self.loadAboutIcon()
        icon_layout.addWidget(self.about_icon_label)
        
        # 添加到主布局
        main_layout.addWidget(text_container, 3)
        main_layout.addWidget(self.icon_container, 1, Qt.AlignTop)
        
        self.vBoxLayout.addLayout(main_layout)
    
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
        scroll.setObjectName('aboutScrollArea')

        # 主内容容器
        content_widget = QWidget()
        content_widget.setObjectName('aboutScrollWidget')
        self.expandLayout = ExpandLayout(content_widget)
        self.expandLayout.setContentsMargins(36, 20, 36, 20)
        self.expandLayout.setSpacing(28)

        # 关于应用横幅 - 跟随滚动
        self.about_banner = BannerWidget(parent=content_widget, config_manager=self.config_manager, lang=self.lang)
        self.expandLayout.addWidget(self.about_banner)

        # 链接和支持卡片组
        self.linksGroup = SettingCardGroup(
            self.get_text("links_and_support", "Links & Support"), 
            content_widget
        )

        # GitHub链接卡片
        self.githubCard = GitHubLinkCard(parent=self.linksGroup, lang=self.lang)
        self.linksGroup.addSettingCard(self.githubCard)
        
        # 提供反馈卡片
        self.feedbackCard = FeedbackCard(parent=self.linksGroup, lang=self.lang)
        self.linksGroup.addSettingCard(self.feedbackCard)
        
        self.expandLayout.addWidget(self.linksGroup)

        # 系统信息卡片组  
        self.systemGroup = SettingCardGroup(
            self.get_text("system_info", "System Information"),
            content_widget
        )

        # 系统信息卡片
        self.systemInfoCard = SystemInfoCard(parent=self.systemGroup, lang=self.lang)
        self.systemGroup.addSettingCard(self.systemInfoCard)
        
        # FFmpeg状态卡片
        self.ffmpegCard = FFmpegStatusCard(parent=self.systemGroup)
        self.systemGroup.addSettingCard(self.ffmpegCard)
        
        self.expandLayout.addWidget(self.systemGroup)

        # 关于应用卡片组
        self.aboutGroup = SettingCardGroup(
            self.get_text("about_application", "About Application"),
            content_widget
        )
        
        # 技术栈卡片
        self.techStackCard = TechStackCard(parent=self.aboutGroup, lang=self.lang)
        self.aboutGroup.addSettingCard(self.techStackCard)
        
        # 版本信息卡片
        self.versionInfoCard = VersionInfoCard(parent=self.aboutGroup, lang=self.lang)
        self.aboutGroup.addSettingCard(self.versionInfoCard)
        
        self.expandLayout.addWidget(self.aboutGroup)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
            
    def setAboutStyles(self):
        """设置关于页面样式"""
        if self.config_manager:
            theme = self.config_manager.get("theme", "dark")
        else:
            theme = "dark"

        if theme == "light":
            self.setStyleSheet("""
                #aboutInterface {
                    background-color: transparent;
                }
                #aboutScrollArea {
                    background-color: transparent;
                    border: none;
                }
                #aboutScrollWidget {
                    background-color: transparent;
                }
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
                #aboutInterface {
                    background-color: transparent;
                }
                #aboutScrollArea {
                    background-color: transparent;
                    border: none;
                }
                #aboutScrollWidget {
                    background-color: transparent;
                }
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