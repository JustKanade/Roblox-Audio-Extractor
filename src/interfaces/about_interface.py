#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QRectF, QEvent
from PyQt5.QtGui import QPixmap, QFont, QImage, QPainter, QBrush, QPainterPath

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
from src.components.cards.contributors_table_card import ContributorsTableCard
from src.components.avatar.avatar_widget import AvatarDownloader
import os
import sys

# 导入事件相关定义
AVATAR_SETTING_CHANGED_EVENT_TYPE = QEvent.Type(1001)  # 与avatar_setting_card.py保持一致


class BannerWidget(CardWidget):
    """ 横幅小部件 """

    def __init__(self, parent=None, config_manager=None, lang=None, qq_number="2824333590", use_logo_only=False):
        super().__init__(parent=parent)
        self.setFixedHeight(200)  # 设置固定高度
        self.config_manager = config_manager
        self.lang = lang
        self.qq_number = qq_number
        self.use_logo_only = use_logo_only  # 是否只使用程序logo
        
        # 头像相关属性
        self.avatar_pixmap = None
        self.use_avatar = False
        self.downloader = None
        
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
    
    def should_load_avatar(self):
        """检查是否应该加载头像"""
        if not self.config_manager:
            return True  # 没有配置管理器时默认加载
        return not self.config_manager.get("disable_avatar_auto_update", False)
    
    def loadAboutIcon(self):
        """加载关于页面图标 - 优先尝试QQ头像，失败时回退到应用logo"""
        try:
            # 如果设置为只使用logo，直接显示程序logo
            if self.use_logo_only:
                self.loadFallbackIcon()
                return
            
            # 检查是否应该加载头像
            if not self.should_load_avatar():
                # 禁用头像下载，直接显示应用logo
                self.loadFallbackIcon()
                return
                
            # 首先尝试下载QQ头像
            if self.qq_number:
                self.downloader = AvatarDownloader(self.qq_number)
                self.downloader.downloadFinished.connect(self._on_avatar_downloaded)
                self.downloader.downloadError.connect(self._on_download_error)
                self.downloader.start()
            else:
                # 如果没有QQ号，直接加载回退图标
                self.loadFallbackIcon()
        except Exception as e:
            print(f"无法启动头像下载: {e}")
            self.loadFallbackIcon()
    
    def _on_avatar_downloaded(self, content):
        """头像下载成功的回调处理"""
        try:
            image = QImage()
            if image.loadFromData(content):
                # 将QImage转换为QPixmap并缩放
                pixmap = QPixmap.fromImage(image)
                scaled_pixmap = pixmap.scaled(
                    100, 100,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                # 制作圆形头像
                circular_pixmap = self.makeCircularPixmap(scaled_pixmap)
                self.about_icon_label.setPixmap(circular_pixmap)
                self.avatar_pixmap = circular_pixmap
                self.use_avatar = True
                print("成功加载QQ头像到关于界面")
            else:
                # 头像数据加载失败，回退到应用logo
                print("头像数据加载失败，回退到应用logo")
                self.loadFallbackIcon()
        except Exception as e:
            print(f"处理头像下载结果时出错: {e}")
            self.loadFallbackIcon()
    
    def _on_download_error(self, error_msg):
        """头像下载失败的回调处理"""
        print(f"头像下载失败: {error_msg}，回退到应用logo")
        self.loadFallbackIcon()
    
    def makeCircularPixmap(self, pixmap):
        """将头像制作成圆形"""
        try:
            size = min(pixmap.width(), pixmap.height())
            # 创建正方形的pixmap
            square_pixmap = QPixmap(size, size)
            square_pixmap.fill(Qt.transparent)
            
            # 绘制圆形头像
            painter = QPainter(square_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 创建圆形路径
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            
            # 绘制头像
            painter.drawPixmap(0, 0, pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            painter.end()
            
            return square_pixmap
        except Exception as e:
            print(f"制作圆形头像时出错: {e}")
            return pixmap  # 返回原始头像
    
    def loadFallbackIcon(self):
        """加载回退图标（应用logo或默认文本）"""
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
                self.use_avatar = False
                print("已加载应用logo到关于界面")
            else:
                # 使用默认文本图标
                self.about_icon_label.clear()
                self.about_icon_label.setText("♪")
                font = QFont()
                font.setPointSize(64)
                self.about_icon_label.setFont(font)
                self.about_icon_label.setAlignment(Qt.AlignCenter)
                self.use_avatar = False
                print("使用默认文本图标")
        except Exception as e:
            print(f"加载回退图标时出错: {e}")
            # 最终回退：使用默认文本
            try:
                self.about_icon_label.clear()
                self.about_icon_label.setText("♪")
                font = QFont()
                font.setPointSize(64)
                self.about_icon_label.setFont(font)
                self.about_icon_label.setAlignment(Qt.AlignCenter)
                self.use_avatar = False
            except Exception as final_e:
                print(f"设置默认文本图标也失败: {final_e}")
    
    def event(self, event):
        """处理自定义事件"""
        if event.type() == AVATAR_SETTING_CHANGED_EVENT_TYPE:
            # 如果设置为只使用logo，忽略头像设置更改事件
            if self.use_logo_only:
                return True
                
            # 头像设置更改事件
            if event.disable_update:
                # 禁用头像下载
                # 停止正在进行的下载
                if hasattr(self, 'downloader') and self.downloader:
                    self.downloader.terminate()
                    self.downloader = None
                # 显示回退图标
                self.loadFallbackIcon()
            else:
                # 启用头像下载，重新加载头像
                self.loadAboutIcon()
            
            return True
        return super().event(event)


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
        self.expandLayout.setContentsMargins(20, 20, 20, 20)
        self.expandLayout.setSpacing(28)

        # 关于应用横幅 - 跟随滚动
        self.about_banner = BannerWidget(parent=content_widget, config_manager=self.config_manager, lang=self.lang)
        self.expandLayout.addWidget(self.about_banner)

        # 贡献者卡片组
        self.contributorsGroup = SettingCardGroup(
            self.get_text("contributors_section", "Contributors"),
            content_widget
        )
        
        # 贡献者表格卡片
        self.contributorsTableCard = ContributorsTableCard(parent=self.contributorsGroup, lang=self.lang)
        self.contributorsGroup.addSettingCard(self.contributorsTableCard)
        
        self.expandLayout.addWidget(self.contributorsGroup)

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
        
        # 设置为响应式
        self.setResponsiveContentWidget(scroll)
    
    def setResponsiveContentWidget(self, scroll_area):
        """为滚动区域内的内容容器应用响应式布局设置，防止卡片间距异常"""
        if not scroll_area:
            return
            
        content_widget = scroll_area.widget()
        if not content_widget:
            return
            
        # 设置垂直大小策略为最小值，防止垂直方向上不必要的扩展
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        # 确保布局设置了顶部对齐
        if content_widget.layout():
            content_widget.layout().setAlignment(Qt.AlignTop)
            
            # 确保布局末尾有伸缩项
            if isinstance(content_widget.layout(), QVBoxLayout):
                has_stretch = False
                for i in range(content_widget.layout().count()):
                    item = content_widget.layout().itemAt(i)
                    if item and item.spacerItem():
                        has_stretch = True
                        break
                        
                if not has_stretch:
                    content_widget.layout().addStretch()
            
    def setAboutStyles(self):
        """设置关于页面样式"""
        if self.config_manager:
            theme = self.config_manager.get("theme")
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