#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QFont, QPainter, QBrush, QPainterPath, QLinearGradient, QColor

from qfluentwidgets import (
    CardWidget, TitleLabel, SubtitleLabel,
    StrongBodyLabel, BodyLabel, CaptionLabel, 
    HyperlinkButton, FluentIcon, IconWidget,
    DisplayLabel, ScrollArea, isDarkTheme, setTheme, Theme
)

# 导入FluentTheme以获取当前主题色
try:
    from qfluentwidgets import FluentTheme
except ImportError:
    # 如果导入失败，创建一个模拟的FluentTheme类
    class FluentTheme:
        @staticmethod
        def primaryColor():
            return QColor("#e8b3ff")  # 默认蓝色

from src.utils.file_utils import resource_path
import os
import sys


class BannerWidget(QWidget):
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
        
        self.version_label = SubtitleLabel(self.get_text("about_version", "Version: 0.16.1"))
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

    def paintEvent(self, e):
        """绘制事件，绘制渐变背景"""
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(
            QPainter.SmoothPixmapTransform | QPainter.Antialiasing
        )
        painter.setPen(Qt.NoPen)

        # 创建圆角矩形路径
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        w, h = self.width(), self.height()
        path.addRoundedRect(QRectF(0, 0, w, h), 10, 10)
        
        # 获取自定义主题色
        theme_color = None
        if self.config_manager:
            if self.config_manager.get("use_custom_theme_color", False):
                theme_color_str = self.config_manager.get("theme_color", "#e8b3ff")
                theme_color = QColor(theme_color_str)
            else:
                # 如果没有启用自定义主题色，从QFluentWidgets获取当前主题色
                theme_color = FluentTheme.primaryColor()
        else:
            # 如果没有config_manager，从QFluentWidgets获取当前主题色
            theme_color = FluentTheme.primaryColor()
            
        # 如果没有自定义主题色或无效，使用默认主题色
        if not theme_color or not theme_color.isValid():
            theme_color = QColor("#e8b3ff")  

        # 初始化线性渐变
        gradient = QLinearGradient(0, 0, w, h)
        
        # 根据主题设置渐变颜色
        if not isDarkTheme():
            # 浅色主题：使用主题色的浅色变体
            gradient.setColorAt(0, QColor(theme_color.red(), theme_color.green(), theme_color.blue(), 80))
            gradient.setColorAt(1, QColor(theme_color.red(), theme_color.green(), theme_color.blue(), 10))
        else:
            # 深色主题：使用主题色的深色变体
            gradient.setColorAt(0, QColor(theme_color.red()//2, theme_color.green()//2, theme_color.blue()//2, 120))
            gradient.setColorAt(1, QColor(theme_color.red()//3, theme_color.green()//3, theme_color.blue()//3, 20))
            
        # 使用渐变填充路径
        painter.fillPath(path, QBrush(gradient))


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

        # 关于应用横幅
        about_banner = BannerWidget(parent=self, config_manager=self.config_manager, lang=self.lang)
        content_layout.addWidget(about_banner)

        # 链接和支持卡片
        links_card = CardWidget()
        links_card.setMaximumHeight(180)  
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