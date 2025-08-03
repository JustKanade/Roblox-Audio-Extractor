#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QGridLayout,
    QLabel, QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont

from qfluentwidgets import (
    ScrollArea, CardWidget, DisplayLabel, BodyLabel, CaptionLabel,
    StrongBodyLabel, SubtitleLabel, PrimaryPushButton, PushButton,
    TransparentPushButton, FluentIcon, TextEdit, PillPushButton,
    FlowLayout
)

from src.components.ui.responsive_components import ResponsiveFeatureItem
from src.utils.file_utils import resource_path, open_directory
from src.utils.log_utils import LogHandler

import os
import multiprocessing
from typing import Any, Optional

class HomeInterface(QWidget):
    """首页界面类"""
    
    def __init__(self, parent=None, default_dir: str = "", config_manager: Any = None, lang: Any = None):
        super().__init__(parent=parent)
        self.setObjectName("homeInterface")
        self.default_dir = default_dir
        self.config_manager = config_manager
        self.lang = lang
        
        # 初始化UI
        self.initUI()
        
    def initUI(self):
        """初始化首页界面"""
        # 创建滚动区域
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 创建主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)  # 减少边距以适应小屏幕
        content_layout.setSpacing(15)  # 减少间距

        # 欢迎横幅卡片 - 响应式设计
        welcome_card = CardWidget()
        welcome_card.setMinimumHeight(180)  # 设置最小高度而不是固定高度
        welcome_layout = QVBoxLayout(welcome_card)
        welcome_layout.setContentsMargins(20, 15, 20, 15)  # 减少内边距

        # 横幅内容 - 使用响应式布局
        banner_content = QHBoxLayout()
        banner_content.setSpacing(15)

        # 左侧：文本内容
        text_container = QWidget()
        text_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(8)

        welcome_title = DisplayLabel(self.lang.get("welcome_message"))
        welcome_title.setObjectName("welcomeTitle")
        welcome_title.setWordWrap(True)  # 允许文本换行

        welcome_subtitle = BodyLabel(self.lang.get("about_description"))
        welcome_subtitle.setWordWrap(True)
        welcome_subtitle.setObjectName("welcomeSubtitle")

        text_layout.addWidget(welcome_title)
        text_layout.addWidget(welcome_subtitle)

        # 右侧：图标（在小屏幕上隐藏）
        icon_container = QWidget()
        icon_container.setFixedSize(100, 100)
        icon_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        self.home_icon_label = QLabel()
        self.home_icon_label.setAlignment(Qt.AlignCenter)
        self.loadHomeIcon()
        icon_layout.addWidget(self.home_icon_label)

        # 添加到横幅布局
        banner_content.addWidget(text_container, 3)
        banner_content.addWidget(icon_container, 1)

        # 快速操作按钮 - 响应式排列
        action_container = QWidget()
        # 使用FlowLayout替代固定的水平布局
        action_layout = FlowLayout(action_container)
        action_layout.setContentsMargins(0, 10, 0, 0)
        action_layout.setSpacing(10)

        extract_btn = PrimaryPushButton(FluentIcon.DOWNLOAD, self.lang.get("extract_audio"))
        extract_btn.setFixedSize(140, 35)
        extract_btn.clicked.connect(lambda: self.switchToInterface("extractInterface"))

        clear_cache_btn = PushButton(FluentIcon.DELETE, self.lang.get("clear_cache"))
        clear_cache_btn.setFixedSize(120, 35)
        clear_cache_btn.clicked.connect(lambda: self.switchToInterface("clearCacheInterface"))

        settings_btn = TransparentPushButton(FluentIcon.SETTING, self.lang.get("settings"))
        settings_btn.setFixedSize(100, 35)
        settings_btn.clicked.connect(lambda: self.switchToInterface("settingsInterface"))

        action_layout.addWidget(extract_btn)
        action_layout.addWidget(clear_cache_btn)
        action_layout.addWidget(settings_btn)

        # 组装欢迎卡片
        welcome_layout.addLayout(banner_content)
        welcome_layout.addWidget(action_container)
        content_layout.addWidget(welcome_card)

        # 功能特色卡片 - 使用响应式FlowLayout
        features_card = CardWidget()
        features_layout = QVBoxLayout(features_card)
        features_layout.setContentsMargins(20, 15, 20, 15)
        features_layout.setSpacing(12)

        features_title = SubtitleLabel(self.lang.get("features"))
        features_title.setObjectName("featuresTitle")
        features_layout.addWidget(features_title)

        # 创建响应式功能特色容器
        features_container = QWidget()
        self.features_flow_layout = FlowLayout(features_container)
        self.features_flow_layout.setSpacing(10)
        self.features_flow_layout.setContentsMargins(0, 0, 0, 0)

        # 功能特色项目
        feature_items = [
            (FluentIcon.SPEED_HIGH, self.lang.get("feature_1")),
            (FluentIcon.ACCEPT, self.lang.get("feature_2")),
            (FluentIcon.FOLDER, self.lang.get("feature_3")),
            (FluentIcon.MUSIC, self.lang.get("feature_4"))
        ]

        for icon, text in feature_items:
            feature_widget = ResponsiveFeatureItem(icon, text)
            self.features_flow_layout.addWidget(feature_widget)

        features_layout.addWidget(features_container)
        content_layout.addWidget(features_card)

        # 信息行 - 响应式网格布局
        info_container = QWidget()
        info_grid = QGridLayout(info_container)
        info_grid.setSpacing(15)
        info_grid.setContentsMargins(0, 0, 0, 0)

        # 系统信息卡片
        system_card = CardWidget()
        system_card.setMinimumWidth(250)  # 设置最小宽度
        system_layout = QVBoxLayout(system_card)
        system_layout.setContentsMargins(20, 15, 20, 15)

        system_title = StrongBodyLabel(self.lang.get("system_info"))
        system_layout.addWidget(system_title)

        # 系统信息项目
        cpu_info = f"{self.lang.get('cpu_cores')}: {multiprocessing.cpu_count()}"
        recommended_threads = f"{self.lang.get('recommended_threads')}: {min(32, multiprocessing.cpu_count() * 2)}"
        
        # 检查是否可以导入ffmpeg状态检查功能
        try:
            from src.extractors.audio_extractor import is_ffmpeg_available
            ffmpeg_status = f"{self.lang.get('ffmpeg_status')}: {self.lang.get('available') if is_ffmpeg_available() else self.lang.get('not_available')}"
        except ImportError:
            ffmpeg_status = f"{self.lang.get('ffmpeg_status')}: {self.lang.get('unknown')}"

        system_layout.addWidget(CaptionLabel(cpu_info))
        system_layout.addWidget(CaptionLabel(recommended_threads))
        system_layout.addWidget(CaptionLabel(ffmpeg_status))

        # 目录信息卡片
        dir_card = CardWidget()
        dir_card.setMinimumWidth(250)  # 设置最小宽度
        dir_layout = QVBoxLayout(dir_card)
        dir_layout.setContentsMargins(15, 12, 15, 12)

        dir_title = StrongBodyLabel(self.lang.get("default_dir"))
        dir_layout.addWidget(dir_title)

        dir_path_label = CaptionLabel(self.default_dir)
        dir_path_label.setWordWrap(True)
        dir_layout.addWidget(dir_path_label)

        dir_actions = QHBoxLayout()
        dir_actions.setContentsMargins(0, 8, 0, 0)
        dir_actions.setSpacing(8)

        open_dir_btn = PillPushButton(FluentIcon.FOLDER, self.lang.get("open_directory"))
        open_dir_btn.setFixedHeight(28)
        open_dir_btn.setCheckable(False)  # 设置为非checkable，避免点击后保持选中状态
        open_dir_btn.clicked.connect(lambda: open_directory(self.default_dir))

        copy_path_btn = TransparentPushButton(FluentIcon.COPY, self.lang.get("copy_path"))
        copy_path_btn.setFixedHeight(28)
        copy_path_btn.clicked.connect(lambda: self.copyPathToClipboard(self.default_dir))

        dir_actions.addWidget(open_dir_btn)
        dir_actions.addWidget(copy_path_btn)
        dir_actions.addStretch()

        dir_layout.addLayout(dir_actions)

        # 添加到网格布局（响应式排列）
        info_grid.addWidget(system_card, 0, 0)
        info_grid.addWidget(dir_card, 0, 1)

        # 设置列拉伸，使卡片能够平均分配空间
        info_grid.setColumnStretch(0, 1)
        info_grid.setColumnStretch(1, 1)

        content_layout.addWidget(info_container)

        # 最近活动日志卡片
        log_card = CardWidget()
        log_card.setMinimumHeight(200)  # 使用最小高度而不是固定高度
        log_card.setMaximumHeight(300)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(15, 10, 15, 12)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(self.lang.get("recent_activity"))
        log_layout.addWidget(log_title)

        self.homeLogText = TextEdit()
        self.homeLogText.setReadOnly(True)
        self.homeLogText.setMinimumHeight(120)
        log_layout.addWidget(self.homeLogText)

        content_layout.addWidget(log_card)

        # 添加伸缩空间
        content_layout.addStretch()

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 应用样式
        self.setHomeStyles()
        
    def switchToInterface(self, interface_name):
        """通过发送信号切换界面（由主窗口实现具体切换逻辑）"""
        # 这个方法会在主窗口中被重写覆盖，这里只是一个占位
        pass
        
    def loadHomeIcon(self):
        """加载主页图标"""
        try:
            icon_path = resource_path(os.path.join("res", "icons", "logo.png"))
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                scaled_pixmap = pixmap.scaled(
                    80, 80,  # 减小图标尺寸
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.home_icon_label.setPixmap(scaled_pixmap)
            else:
                # 使用默认文字
                self.home_icon_label.setText("♪")
                font = QFont()
                font.setPointSize(36)  # 减小字体
                self.home_icon_label.setFont(font)
                self.home_icon_label.setAlignment(Qt.AlignCenter)
        except Exception as e:
            print(f"无法加载主页图标: {e}")

    def setHomeStyles(self):
        """设置主页样式"""
        # 检查当前主题并设置相应样式
        if not self.config_manager:
            return
            
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            # 浅色模式样式
            self.setStyleSheet("""
                #welcomeTitle {
                    font-size: 26px;
                    font-weight: bold;
                    color: rgb(0, 0, 0);
                }
                #welcomeSubtitle {
                    font-size: 14px;
                    color: rgba(0, 0, 0, 0.7);
                }
                #featuresTitle {
                    font-size: 18px;
                    font-weight: 600;
                    color: rgb(0, 0, 0);
                }
            """)
        else:
            # 深色模式样式
            self.setStyleSheet("""
                #welcomeTitle {
                    font-size: 26px;
                    font-weight: bold;
                    color: rgb(255, 255, 255);
                }
                #welcomeSubtitle {
                    font-size: 14px;
                    color: rgba(255, 255, 255, 0.8);
                }
                #featuresTitle {
                    font-size: 18px;
                    font-weight: 600;
                    color: rgb(255, 255, 255);
                }
            """)
            
    def adjust_responsive_layout(self, window_width: int):
        """根据窗口宽度调整响应式布局"""
        try:
            # 断点设置
            MOBILE_BREAKPOINT = 600
            TABLET_BREAKPOINT = 900
            DESKTOP_BREAKPOINT = 1200
            LARGE_DESKTOP_BREAKPOINT = 1600

            # 调整功能特色项目的大小和排列
            if hasattr(self, 'features_flow_layout'):
                # 根据窗口宽度调整FlowLayout的项目大小
                for i in range(self.features_flow_layout.count()):
                    item = self.features_flow_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if isinstance(widget, ResponsiveFeatureItem):
                            if window_width < MOBILE_BREAKPOINT:
                                # 移动设备：更小的项目
                                widget.updateSize(120, 70, 180, 70)
                            elif window_width < TABLET_BREAKPOINT:
                                # 平板设备：中等大小
                                widget.updateSize(140, 75, 200, 75)
                            elif window_width < DESKTOP_BREAKPOINT:
                                # 桌面设备：正常大小
                                widget.updateSize(160, 80, 220, 80)
                            elif window_width < LARGE_DESKTOP_BREAKPOINT:
                                # 大型桌面：更大的项目
                                widget.updateSize(180, 85, 240, 85)
                            else:
                                # 超大屏幕（最大化）：最大项目
                                widget.updateSize(200, 90, 260, 90)

            # 在小屏幕上隐藏图标
            if hasattr(self, 'home_icon_label'):
                icon_container = self.home_icon_label.parent()
                if icon_container and isinstance(icon_container, QWidget):
                    if window_width < MOBILE_BREAKPOINT:
                        icon_container.setVisible(False)
                    else:
                        icon_container.setVisible(True)
                        # 在大屏幕上增大图标尺寸
                        if window_width >= LARGE_DESKTOP_BREAKPOINT:
                            if hasattr(self, 'home_icon_label') and self.home_icon_label:
                                try:
                                    # 更新图标尺寸
                                    icon_path = resource_path(os.path.join("res", "icons", "logo.png"))
                                    if os.path.exists(icon_path):
                                        pixmap = QPixmap(icon_path)
                                        scaled_size = 100 if window_width >= LARGE_DESKTOP_BREAKPOINT else 80
                                        scaled_pixmap = pixmap.scaled(
                                            scaled_size, scaled_size,
                                            Qt.KeepAspectRatio,
                                            Qt.SmoothTransformation
                                        )
                                        self.home_icon_label.setPixmap(scaled_pixmap)
                                        # 调整容器大小
                                        icon_container.setFixedSize(scaled_size + 20, scaled_size + 20)
                                except Exception:
                                    pass

            # 调整信息卡片的布局
            # 在大屏幕上找到网格布局并调整列数
            try:
                info_container = None
                for i in range(self.layout().count()):
                    widget = self.layout().itemAt(i).widget()
                    if isinstance(widget, ScrollArea):
                        scroll_content = widget.widget()
                        if scroll_content and scroll_content.layout():
                            for j in range(scroll_content.layout().count()):
                                item = scroll_content.layout().itemAt(j)
                                if item and item.widget():
                                    if isinstance(item.widget().layout(), QGridLayout):
                                        info_container = item.widget()
                                        break
                
                # 如果找到了网格布局容器
                if info_container and info_container.layout():
                    grid_layout = info_container.layout()
                    
                    # 根据窗口宽度调整卡片的最小宽度
                    system_card = None
                    dir_card = None
                    
                    # 寻找系统和目录卡片
                    for i in range(grid_layout.count()):
                        item = grid_layout.itemAt(i)
                        if item and item.widget() and isinstance(item.widget(), CardWidget):
                            widget = item.widget()
                            if i == 0:  # 系统卡片通常是第一个
                                system_card = widget
                            elif i == 1:  # 目录卡片通常是第二个
                                dir_card = widget
                    
                    # 调整卡片最小宽度
                    if system_card:
                        if window_width < TABLET_BREAKPOINT:
                            system_card.setMinimumWidth(200)
                        elif window_width < DESKTOP_BREAKPOINT:
                            system_card.setMinimumWidth(250)
                        elif window_width < LARGE_DESKTOP_BREAKPOINT:
                            system_card.setMinimumWidth(300)
                        else:
                            system_card.setMinimumWidth(350)
                    
                    if dir_card:
                        if window_width < TABLET_BREAKPOINT:
                            dir_card.setMinimumWidth(200)
                        elif window_width < DESKTOP_BREAKPOINT:
                            dir_card.setMinimumWidth(250)
                        elif window_width < LARGE_DESKTOP_BREAKPOINT:
                            dir_card.setMinimumWidth(300)
                        else:
                            dir_card.setMinimumWidth(350)
            except Exception:
                pass

        except Exception as e:
            # 静默处理异常，避免影响UI正常运行
            pass
            
    def copyPathToClipboard(self, path: str):
        """复制路径到剪贴板"""
        # 这个方法会在主窗口中被重写覆盖，这里只是一个占位
        pass
    
    def add_welcome_message(self):
        """添加欢迎消息到主页日志"""
        try:
            # 导入并显示时间问候
            from src.components.Greetings import TimeGreetings
            
            # 获取当前语言设置
            current_language = self.lang.get_language_name()
            language_code = 'en' if current_language == 'English' else 'zh'
            
            # 检查问候语是否启用
            greeting_enabled = self.config_manager.get("greeting_enabled", True)
            if greeting_enabled:
                # 使用固定样式和当前语言显示问候
                TimeGreetings.show_greeting(language_code)
            
            # 日志信息
            log = LogHandler(self.homeLogText)
            log.info(self.lang.get('welcome_message'))
            log.info(self.lang.get('about_version'))
            log.info(f"{self.lang.get('default_dir')}: {self.default_dir}")
            log.info(self.lang.get("config_file_location", self.config_manager.config_file))
        except Exception as e:
            print(f"添加欢迎信息时出错: {e}") 