#!/usr/bin/env python3
# -*- coding: utf-8 -*-

VERSION = "0.16.1"

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import sys
import time
import json
import logging
import threading
import queue
import datetime
import traceback
import multiprocessing
from functools import lru_cache
from typing import Dict, List, Any, Set, Optional
from enum import Enum, auto

# 导入自定义提取器模块
from src.extractors.audio_extractor import RobloxAudioExtractor, ExtractedHistory, ContentHashCache, ProcessingStats, ClassificationMethod, is_ffmpeg_available

# 导入工具函数
from src.utils.file_utils import resource_path, get_roblox_default_dir, open_directory
from src.utils.log_utils import LogHandler, setup_basic_logging, save_log_to_file
from src.utils.import_utils import import_libs

# 导入语言管理
from src.locale import Language, initialize_lang
from src.locale import lang
# 导入语言管理功能
from src.management.language_management.language_manager import apply_language, get_language_code

# 导入自定义工作线程
from src.workers.extraction_worker import ExtractionWorker
# 导入缓存管理模块
from src.management.cache_management.cache_cleaner import CacheClearWorker
# 导入响应式UI组件
from src.components.ui.responsive_components import ResponsiveFeatureItem
# 导入窗口管理功能
from src.management.window_management.responsive_handler import apply_responsive_handler
from src.management.window_management.window_utils import apply_always_on_top
# 导入主题管理功能
from src.management.theme_management.theme_manager import apply_theme_from_config, apply_theme_change
# 导入自定义主题颜色卡片
from src.components.cards.Settings.custom_theme_color_card import CustomThemeColorCard
# 导入中央日志处理系统
from src.logging.central_log_handler import CentralLogHandler
# 导入版本检测卡片
from src.components.cards.Settings.version_check_card import VersionCheckCard
# 导入日志控制卡片
from src.components.cards.Settings.log_control_card import LogControlCard
# 导入FFmpeg状态卡片
from src.components.cards.Settings.ffmpeg_status_card import FFmpegStatusCard
# 导入头像设置卡片
from src.components.cards.Settings.avatar_setting_card import AvatarSettingCard
# 导入Debug模式卡片
from src.components.cards.Settings.debug_mode_card import DebugModeCard
# 导入总是置顶窗口设置卡片
from src.components.cards.Settings.always_on_top_card import AlwaysOnTopCard
# 导入问候语设置卡片
from src.components.cards.Settings.greeting_setting_card import GreetingSettingCard
# 导入配置管理器
from src.config import ConfigManager


if hasattr(sys, '_MEIPASS'):
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt', 'plugins')

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,QButtonGroup,
    QFileDialog, QLabel, QFrame, QSizePolicy, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor


from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, setTheme, Theme,
    InfoBar, FluentIcon, PushButton, PrimaryPushButton,
    ComboBox, BodyLabel, CardWidget, TitleLabel, CaptionLabel,
    ProgressBar, CheckBox, RadioButton, TextEdit,
    MessageBox, StateToolTip, InfoBarPosition,
    StrongBodyLabel, SubtitleLabel, DisplayLabel,
    HyperlinkButton, TransparentPushButton, ScrollArea,
    IconWidget, SpinBox, LineEdit, PillPushButton, FlowLayout,
    SplashScreen, setThemeColor, SwitchButton  
)

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class MainWindow(FluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 确保在启动时同步配置到PyQt-Fluent-Widgets
        self.config_manager.sync_theme_to_qfluent()
        
        # 打印配置文件内容，用于调试
        print(f"QFluentWidgets配置文件路径: {self.config_manager.qfluent_config_file}")
        if os.path.exists(self.config_manager.qfluent_config_file):
            try:
                with open(self.config_manager.qfluent_config_file, 'r', encoding='utf-8') as f:
                    qfluent_config = json.load(f)
                    print(f"QFluentWidgets配置内容: {qfluent_config}")
            except Exception as e:
                print(f"读取QFluentWidgets配置失败: {e}")

        # 初始化语言管理器
        global lang
        lang = initialize_lang(self.config_manager)

        # 初始化中央日志处理器
        CentralLogHandler.getInstance().init_with_config(self.config_manager)

        # 初始化窗口
        self.initWindow()

        # 初始化数据
        self.default_dir = get_roblox_default_dir()
        
        # 创建应用数据目录
        app_data_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        os.makedirs(app_data_dir, exist_ok=True)
        history_file = os.path.join(app_data_dir, "extracted_history.json")
        
        # 初始化提取历史
        self.download_history = ExtractedHistory(history_file)
        
        # 初始化工作线程
        self.extraction_worker = None
        self.cache_clear_worker = None
        
        # 初始化UI
        self.initUI()
        
        # 显示欢迎消息
        self.add_welcome_message()
        
        # 再次确保同步配置到PyQt-Fluent-Widgets，然后应用主题设置
        self.config_manager.sync_theme_to_qfluent()
        
        # 应用保存的主题设置
        self.applyThemeFromConfig()
        
        # 应用响应式布局到所有界面
        self.applyResponsiveLayoutToAllInterfaces()
        
        # 应用响应式窗口调整处理器
        apply_responsive_handler(self, self._adjust_responsive_layout)

    def initWindow(self):
        """初始化窗口设置"""
        # 设置窗口标题和大小
        self.setWindowTitle(lang.get("title"))
        self.resize(750, 570)

        # 设置最小窗口大小
        self.setMinimumSize(750, 570)

        # 设置自动主题
        setTheme(Theme.AUTO)

        # 设置窗口图标
        try:
            icon_path = resource_path(os.path.join("res", "icons", "Roblox-Audio-Extractor.png"))
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"无法设置窗口图标: {e}")

        
        # 应用窗口置顶设置
        always_on_top = self.config_manager.get("always_on_top", False)
        if always_on_top:
            # 使用更长的延迟，确保窗口已完全初始化
            print("窗口初始化时设置置顶")
            # 使用两段式延迟，先显示窗口，再设置置顶
            QTimer.singleShot(500, lambda: self.show())
            QTimer.singleShot(1500, lambda: apply_always_on_top(self, True))



    def applyThemeFromConfig(self):
        """从配置文件应用主题设置"""
        # 使用主题管理器应用主题
        apply_theme_from_config(self, self.config_manager, CentralLogHandler.getInstance())

    def initUI(self):
        """初始化UI组件"""
        # 创建主界面
        self.homeInterface = QWidget()
        self.homeInterface.setObjectName("homeInterface")

        self.extractInterface = QWidget()
        self.extractInterface.setObjectName("extractInterface")

        # 添加新的图像和纹理提取界面
        self.extractImagesInterface = QWidget()
        self.extractImagesInterface.setObjectName("extractImagesInterface")

        self.extractTexturesInterface = QWidget()
        self.extractTexturesInterface.setObjectName("extractTexturesInterface")

        self.clearCacheInterface = QWidget()
        self.clearCacheInterface.setObjectName("clearCacheInterface")

        self.historyInterface = QWidget()
        self.historyInterface.setObjectName("historyInterface")

        self.settingsInterface = QWidget()
        self.settingsInterface.setObjectName("settingsInterface")

        self.aboutInterface = QWidget()
        self.aboutInterface.setObjectName("aboutInterface")

        # 设置导航 - 
        self.addSubInterface(self.homeInterface, FluentIcon.HOME, lang.get("home"))
        
        # 添加Extract树形菜单
        extract_tree = self.navigationInterface.addItem(
            routeKey="extract",
            icon=FluentIcon.DOWNLOAD,
            text=lang.get("extract"),
            onClick=None,
            selectable=False,
            position=NavigationItemPosition.TOP
        )
        
        # 先确保接口被添加到堆叠窗口小部件
        self.stackedWidget.addWidget(self.extractInterface)
        
        # 添加子菜单项
        self.navigationInterface.addItem(
            routeKey=self.extractInterface.objectName(),
            icon=FluentIcon.MUSIC,
            text=lang.get("extract_audio"),
            onClick=lambda: self.switchTo(self.extractInterface),
            selectable=True,
            position=NavigationItemPosition.TOP,
            parentRouteKey="extract"
        )
        
        # 同样确保其他接口被添加到堆叠窗口小部件
        self.stackedWidget.addWidget(self.extractImagesInterface)
        self.stackedWidget.addWidget(self.extractTexturesInterface)
        
        self.navigationInterface.addItem(
            routeKey=self.extractImagesInterface.objectName(),
            icon=FluentIcon.PHOTO,
            text=lang.get("extract_images"),
            onClick=lambda: self.switchTo(self.extractImagesInterface),
            selectable=True,
            position=NavigationItemPosition.TOP,
            parentRouteKey="extract"
        )
        
        self.navigationInterface.addItem(
            routeKey=self.extractTexturesInterface.objectName(),
            icon=FluentIcon.PALETTE,
            text=lang.get("extract_textures"),
            onClick=lambda: self.switchTo(self.extractTexturesInterface),
            selectable=True,
            position=NavigationItemPosition.TOP,
            parentRouteKey="extract"
        )
        
        # 默认收起Extract树形菜单
        extract_tree.setExpanded(False)
        
        self.addSubInterface(self.clearCacheInterface, FluentIcon.DELETE, lang.get("clear_cache"))
        self.addSubInterface(self.historyInterface, FluentIcon.HISTORY, lang.get("view_history"))

        # 在提取历史导航下方添加分隔线
        self.navigationInterface.addSeparator()

        # 添加底部导航项 - 顺序很重要
        # 先添加JustKanade头像按钮，确保它在设置按钮上方
        try:
            from src.components.avatar import AvatarWidget
            # 设置avatar_widget模块的lang变量
            import src.components.avatar.avatar_widget as avatar_widget_module
            avatar_widget_module.lang = lang
            
            avatar_widget = AvatarWidget(parent=self)
            self.navigationInterface.addWidget(
                routeKey="avatar_widget",
                widget=avatar_widget,
                position=NavigationItemPosition.BOTTOM,
                tooltip="JustKanade"
            )
        except Exception as e:
            print(f"添加头像组件时出错: {e}")

        # 然后添加设置和关于按钮
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, lang.get("settings"),
                             position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.aboutInterface, FluentIcon.INFO, lang.get("about"),
                             position=NavigationItemPosition.BOTTOM)

        # 初始化各个界面
        self.setupHomeInterface()
        self.setupExtractInterface()
        self.setupExtractImagesInterface()
        self.setupExtractTexturesInterface()
        self.setupClearCacheInterface()
        self.setupHistoryInterface()
        self.setupSettingsInterface()
        self.setupAboutInterface()

        # 设置默认界面 - 使用界面对象而不是文本
        self.switchTo(self.homeInterface)

        # 监听界面切换事件
        self.stackedWidget.currentChanged.connect(self.onInterfaceChanged)

    def setupHomeInterface(self):
        """设置主页界面 - 响应式设计优化版本"""
        # 创建滚动区域
        scroll = ScrollArea(self.homeInterface)
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

        welcome_title = DisplayLabel(lang.get("welcome_message"))
        welcome_title.setObjectName("welcomeTitle")
        welcome_title.setWordWrap(True)  # 允许文本换行

        welcome_subtitle = BodyLabel(lang.get("about_description"))
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

        extract_btn = PrimaryPushButton(FluentIcon.DOWNLOAD, lang.get("extract_audio"))
        extract_btn.setFixedSize(140, 35)
        extract_btn.clicked.connect(lambda: self.switchTo(self.extractInterface))

        clear_cache_btn = PushButton(FluentIcon.DELETE, lang.get("clear_cache"))
        clear_cache_btn.setFixedSize(120, 35)
        clear_cache_btn.clicked.connect(lambda: self.switchTo(self.clearCacheInterface))

        settings_btn = TransparentPushButton(FluentIcon.SETTING, lang.get("settings"))
        settings_btn.setFixedSize(100, 35)
        settings_btn.clicked.connect(lambda: self.switchTo(self.settingsInterface))

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

        features_title = SubtitleLabel(lang.get("features"))
        features_title.setObjectName("featuresTitle")
        features_layout.addWidget(features_title)

        # 创建响应式功能特色容器
        features_container = QWidget()
        self.features_flow_layout = FlowLayout(features_container)
        self.features_flow_layout.setSpacing(10)
        self.features_flow_layout.setContentsMargins(0, 0, 0, 0)

        # 功能特色项目
        feature_items = [
            (FluentIcon.SPEED_HIGH, lang.get("feature_1")),
            (FluentIcon.ACCEPT, lang.get("feature_2")),
            (FluentIcon.FOLDER, lang.get("feature_3")),
            (FluentIcon.MUSIC, lang.get("feature_4"))
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

        system_title = StrongBodyLabel(lang.get("system_info"))
        system_layout.addWidget(system_title)

        # 系统信息项目
        cpu_info = f"{lang.get('cpu_cores')}: {multiprocessing.cpu_count()}"
        recommended_threads = f"{lang.get('recommended_threads')}: {min(32, multiprocessing.cpu_count() * 2)}"
        ffmpeg_status = f"{lang.get('ffmpeg_status')}: {lang.get('available') if is_ffmpeg_available() else lang.get('not_available')}"

        system_layout.addWidget(CaptionLabel(cpu_info))
        system_layout.addWidget(CaptionLabel(recommended_threads))
        system_layout.addWidget(CaptionLabel(ffmpeg_status))

        # 目录信息卡片
        dir_card = CardWidget()
        dir_card.setMinimumWidth(250)  # 设置最小宽度
        dir_layout = QVBoxLayout(dir_card)
        dir_layout.setContentsMargins(15, 12, 15, 12)

        dir_title = StrongBodyLabel(lang.get("default_dir"))
        dir_layout.addWidget(dir_title)

        dir_path_label = CaptionLabel(self.default_dir)
        dir_path_label.setWordWrap(True)
        dir_layout.addWidget(dir_path_label)

        dir_actions = QHBoxLayout()
        dir_actions.setContentsMargins(0, 8, 0, 0)
        dir_actions.setSpacing(8)

        open_dir_btn = PillPushButton(FluentIcon.FOLDER, lang.get("open_directory"))
        open_dir_btn.setFixedHeight(28)
        open_dir_btn.setCheckable(False)  # 设置为非checkable，避免点击后保持选中状态
        open_dir_btn.clicked.connect(lambda: open_directory(self.default_dir))

        copy_path_btn = TransparentPushButton(FluentIcon.COPY, lang.get("copy_path"))
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

        log_title = StrongBodyLabel(lang.get("recent_activity"))
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
        main_layout = QVBoxLayout(self.homeInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 应用样式
        self.setHomeStyles()

        # 不再需要手动连接窗口大小改变事件，因为我们使用了apply_responsive_handler

    def _adjust_responsive_layout(self, window_width):
        """根据窗口宽度调整响应式布局"""
        try:
            # 断点设置
            MOBILE_BREAKPOINT = 600
            TABLET_BREAKPOINT = 900

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
                            else:
                                # 桌面设备：正常大小
                                widget.updateSize(160, 80, 220, 80)

            # 在小屏幕上隐藏图标
            if hasattr(self, 'home_icon_label'):
                icon_container = self.home_icon_label.parent()
                if icon_container:
                    if window_width < MOBILE_BREAKPOINT:
                        icon_container.setVisible(False)
                    else:
                        icon_container.setVisible(True)

        except Exception as e:
            # 静默处理异常，避免影响UI正常运行
            pass

    def loadHomeIcon(self):
        """加载主页图标"""
        try:
            icon_path = resource_path(os.path.join("res", "icons", "Roblox-Audio-Extractor.png"))
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
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            # 浅色模式样式
            self.homeInterface.setStyleSheet("""
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
            self.homeInterface.setStyleSheet("""
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

    def setupExtractInterface(self):
        """设置提取音频界面"""
        # 创建滚动区域
        scroll = ScrollArea(self.extractInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        
        # 添加页面标题
        page_title = TitleLabel(lang.get("extract_audio"))
        page_title.setObjectName("extractAudioTitle")
        content_layout.addWidget(page_title)

        # 目录选择卡片
        dir_card = CardWidget()
        dir_card_layout = QVBoxLayout(dir_card)
        dir_card_layout.setContentsMargins(20, 15, 20, 15)
        dir_card_layout.setSpacing(15)

        dir_title = StrongBodyLabel(lang.get("directory"))
        dir_card_layout.addWidget(dir_title)

        # 目录输入行
        dir_input_layout = QHBoxLayout()
        dir_input_layout.setSpacing(10)

        self.dirInput = LineEdit()
        self.dirInput.setText(self.default_dir)
        self.dirInput.setPlaceholderText(lang.get("input_dir"))
        self.dirInput.setClearButtonEnabled(True)

        browse_btn = PushButton(FluentIcon.FOLDER_ADD, lang.get("browse"))
        browse_btn.setFixedSize(100, 33)
        browse_btn.clicked.connect(self.browseDirectory)

        dir_input_layout.addWidget(self.dirInput, 1)
        dir_input_layout.addWidget(browse_btn)

        dir_card_layout.addLayout(dir_input_layout)

        # 添加目录提示
        dir_hint = CaptionLabel(f"{lang.get('default_dir')}: {self.default_dir}")
        dir_hint.setWordWrap(True)
        dir_card_layout.addWidget(dir_hint)

        content_layout.addWidget(dir_card)

        # 分类方法卡片
        classification_card = CardWidget()
        class_card_layout = QVBoxLayout(classification_card)
        class_card_layout.setContentsMargins(20, 15, 20, 15)
        class_card_layout.setSpacing(15)

        class_title = StrongBodyLabel(lang.get("classification_method"))
        class_card_layout.addWidget(class_title)

        # 分类方法选择
        self.classification_group = QButtonGroup()

        duration_row = QHBoxLayout()
        self.durationRadio = RadioButton(lang.get("classify_by_duration"))
        self.durationRadio.setChecked(True)
        duration_icon = IconWidget(FluentIcon.CALENDAR)
        duration_icon.setFixedSize(16, 16)
        duration_row.addWidget(duration_icon)
        duration_row.addWidget(self.durationRadio)
        duration_row.addStretch()

        size_row = QHBoxLayout()
        self.sizeRadio = RadioButton(lang.get("classify_by_size"))
        size_icon = IconWidget(FluentIcon.DOCUMENT)
        size_icon.setFixedSize(16, 16)
        size_row.addWidget(size_icon)
        size_row.addWidget(self.sizeRadio)
        size_row.addStretch()

        self.classification_group.addButton(self.durationRadio)
        self.classification_group.addButton(self.sizeRadio)

        class_card_layout.addLayout(duration_row)
        class_card_layout.addLayout(size_row)

        # FFmpeg警告
        if not is_ffmpeg_available():
            ffmpeg_warning = InfoBar.warning(
                title="FFmpeg",
                content=lang.get("ffmpeg_not_found_warning"),
                orient=Qt.Horizontal,
                isClosable=False,
                duration=-1,
                parent=None
            )
            class_card_layout.addWidget(ffmpeg_warning)

        # 分类信息标签
        self.classInfoLabel = CaptionLabel(lang.get("info_duration_categories"))
        self.classInfoLabel.setWordWrap(True)
        class_card_layout.addWidget(self.classInfoLabel)

        # 连接分类方法选择事件
        self.durationRadio.toggled.connect(self.updateClassificationInfo)

        content_layout.addWidget(classification_card)

        # 处理选项卡片
        options_card = CardWidget()
        options_card_layout = QVBoxLayout(options_card)
        options_card_layout.setContentsMargins(20, 15, 20, 15)
        options_card_layout.setSpacing(15)

        options_title = StrongBodyLabel(lang.get("processing_info"))
        options_card_layout.addWidget(options_title)

        # 线程数设置
        threads_row = QHBoxLayout()
        threads_icon = IconWidget(FluentIcon.SPEED_HIGH)
        threads_icon.setFixedSize(16, 16)
        threads_label = BodyLabel(lang.get("threads_prompt"))

        self.threadsSpinBox = SpinBox()
        self.threadsSpinBox.setRange(1, 128)
        self.threadsSpinBox.setValue(min(32, multiprocessing.cpu_count() * 2))
        self.threadsSpinBox.setFixedWidth(120)
        self.threadsSpinBox.setFixedHeight(32)

        threads_row.addWidget(threads_icon)
        threads_row.addWidget(threads_label)
        threads_row.addStretch()
        threads_row.addWidget(self.threadsSpinBox)

        options_card_layout.addLayout(threads_row)

        # 添加处理提示
        info_list = [
            lang.get("info_skip_downloaded")
        ]

        for info in info_list:
            info_label = CaptionLabel(f"• {info}")
            info_label.setWordWrap(True)
            options_card_layout.addWidget(info_label)

        content_layout.addWidget(options_card)

        # 操作控制卡片
        control_card = CardWidget()
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(25, 20, 25, 20)
        control_layout.setSpacing(15)

        # 进度显示
        progress_layout = QVBoxLayout()

        # 进度条
        self.progressBar = ProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        # 进度信息
        self.progressLabel = CaptionLabel(lang.get("ready"))
        self.progressLabel.setAlignment(Qt.AlignCenter)

        progress_layout.addWidget(self.progressBar)
        progress_layout.addWidget(self.progressLabel)

        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.extractButton = PrimaryPushButton(FluentIcon.DOWNLOAD, lang.get("start_extraction"))
        self.extractButton.setFixedHeight(40)
        self.extractButton.clicked.connect(self.startExtraction)

        self.cancelButton = PushButton(FluentIcon.CLOSE, lang.get("cancel"))
        self.cancelButton.setFixedHeight(40)
        self.cancelButton.clicked.connect(self.cancelExtraction)
        self.cancelButton.hide()  # 初始隐藏

        button_layout.addWidget(self.extractButton)
        button_layout.addWidget(self.cancelButton)
        button_layout.addStretch()

        control_layout.addLayout(progress_layout)
        control_layout.addLayout(button_layout)
        content_layout.addWidget(control_card)

        # 日志区域
        log_card = CardWidget()
        log_card.setFixedHeight(300)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(lang.get("recent_activity"))
        log_layout.addWidget(log_title)

        self.extractLogText = TextEdit()
        self.extractLogText.setReadOnly(True)
        self.extractLogText.setFixedHeight(220)
        log_layout.addWidget(self.extractLogText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self.extractInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.extractLogHandler = LogHandler(self.extractLogText)

    def setupExtractImagesInterface(self):
        """设置图像提取界面"""
        # 创建滚动区域
        scroll = ScrollArea(self.extractImagesInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # 添加占位内容
        placeholder = CardWidget()
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.setContentsMargins(20, 20, 20, 20)
        
        title = SubtitleLabel("提取图像")
        title.setObjectName("extractImagesTitle")
        placeholder_layout.addWidget(title)
        
        desc = BodyLabel("这是提取图像的功能界面占位符，将在后续版本中实现。")
        desc.setWordWrap(True)
        placeholder_layout.addWidget(desc)
        
        content_layout.addWidget(placeholder)
        scroll.setWidget(content_widget)
        
        # 创建布局
        layout = QVBoxLayout(self.extractImagesInterface)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        
        # 设置为响应式
        self.setResponsiveContentWidget(scroll)

    def setupExtractTexturesInterface(self):
        """设置纹理提取界面"""
        # 创建滚动区域
        scroll = ScrollArea(self.extractTexturesInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # 添加占位内容
        placeholder = CardWidget()
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.setContentsMargins(20, 20, 20, 20)
        
        title = SubtitleLabel("提取纹理")
        title.setObjectName("extractTexturesTitle")
        placeholder_layout.addWidget(title)
        
        desc = BodyLabel("这是提取纹理的功能界面占位符，将在后续版本中实现。")
        desc.setWordWrap(True)
        placeholder_layout.addWidget(desc)
        
        content_layout.addWidget(placeholder)
        scroll.setWidget(content_widget)
        
        # 创建布局
        layout = QVBoxLayout(self.extractTexturesInterface)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        
        # 设置为响应式
        self.setResponsiveContentWidget(scroll)

    def setupClearCacheInterface(self):
        scroll = ScrollArea(self.clearCacheInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        # 与Extract界面保持一致的边距和间隔
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # 缓存信息卡片
        info_card = CardWidget()
        info_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(20, 15, 20, 15)
        info_layout.setSpacing(12)
        content_layout.addWidget(info_card)

        # 标题
        info_title = TitleLabel(lang.get("clear_cache"))
        info_layout.addWidget(info_title)

        # 描述
        desc_label = BodyLabel(lang.get("cache_description"))
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        # 缓存位置信息
        location_row = QHBoxLayout()
        location_icon = IconWidget(FluentIcon.FOLDER)
        location_icon.setFixedSize(20, 20)
        location_label = StrongBodyLabel(lang.get("cache_location"))
        location_row.addWidget(location_icon)
        location_row.addWidget(location_label)
        location_row.addStretch()

        info_layout.addLayout(location_row)

        # 缓存路径
        cache_path_label = CaptionLabel(self.default_dir)
        cache_path_label.setWordWrap(True)
        cache_path_label.setStyleSheet(
            "QLabel { background-color: rgba(255, 255, 255, 0.05); padding: 8px; border-radius: 4px; }")
        info_layout.addWidget(cache_path_label)

        # 快速操作按钮
        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(10)

        open_cache_btn = PushButton(FluentIcon.FOLDER, lang.get("open_directory"))
        open_cache_btn.clicked.connect(lambda: open_directory(self.default_dir))

        copy_cache_btn = TransparentPushButton(FluentIcon.COPY, lang.get("copy_path"))
        copy_cache_btn.clicked.connect(lambda: self.copyPathToClipboard(self.default_dir))

        quick_actions.addWidget(open_cache_btn)
        quick_actions.addWidget(copy_cache_btn)
        quick_actions.addStretch()

        info_layout.addLayout(quick_actions)
        content_layout.addWidget(info_card)


        # 操作控制卡片
        control_card = CardWidget()
        control_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(25, 20, 25, 20)
        control_layout.setSpacing(15)
        content_layout.addWidget(control_card)

        # 进度显示
        progress_layout = QVBoxLayout()
        self.cacheProgressBar = ProgressBar()
        self.cacheProgressBar.setValue(0)
        self.cacheProgressBar.setTextVisible(True)
        self.cacheProgressLabel = CaptionLabel(lang.get("ready"))
        self.cacheProgressLabel.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.cacheProgressBar)
        progress_layout.addWidget(self.cacheProgressLabel)

        control_layout.addLayout(progress_layout)

        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.clearCacheButton = PrimaryPushButton(FluentIcon.DELETE, lang.get("clear_cache"))
        self.clearCacheButton.setFixedHeight(40)
        self.clearCacheButton.clicked.connect(self.clearAudioCache)

        self.cancelClearButton = PushButton(FluentIcon.CLOSE, lang.get("cancel"))
        self.cancelClearButton.setFixedHeight(40)
        self.cancelClearButton.clicked.connect(self.cancelClearCache)
        self.cancelClearButton.hide()

        button_layout.addWidget(self.clearCacheButton)
        button_layout.addWidget(self.cancelClearButton)
        button_layout.addStretch()

        control_layout.addLayout(progress_layout)
        control_layout.addLayout(button_layout)
        content_layout.addWidget(control_card)

        # 日志区域
        log_card = CardWidget()
        log_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(lang.get("recent_activity"))
        log_layout.addWidget(log_title)

        self.cacheLogText = TextEdit()
        self.cacheLogText.setReadOnly(True)
        self.cacheLogText.setFixedHeight(220)
        log_layout.addWidget(self.cacheLogText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self.clearCacheInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.cacheLogHandler = LogHandler(self.cacheLogText)

        # 应用样式
        self.setCacheStyles()

    def setCacheStyles(self):
        """设置缓存界面样式"""
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            self.clearCacheInterface.setStyleSheet("""
                #cacheTitle {
                    color: rgb(0, 0, 0);
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
        else:
            self.clearCacheInterface.setStyleSheet("""
                #cacheTitle {
                    color: rgb(255, 255, 255);
                    font-size: 24px;
                    font-weight: bold;
                }
            """)

    def setupHistoryInterface(self):
        """设置历史记录界面"""
        # 创建滚动区域
        scroll = ScrollArea(self.historyInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # 历史统计卡片
        stats_card = CardWidget()
        stats_card.setMaximumHeight(220)  # 限制最大高度，防止异常放大
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(25, 20, 25, 20)
        stats_layout.setSpacing(15)

        # 标题
        stats_title = TitleLabel(lang.get("history_stats"))
        stats_title.setObjectName("historyTitle")
        stats_layout.addWidget(stats_title)

        # 统计信息
        history_size = self.download_history.get_history_size()

        # 文件数量显示
        count_row = QHBoxLayout()
        count_icon = IconWidget(FluentIcon.DOCUMENT)
        count_icon.setFixedSize(24, 24)
        self.historyCountLabel = SubtitleLabel(lang.get("files_recorded", history_size))
        self.historyCountLabel.setObjectName("historyCount")

        count_row.addWidget(count_icon)
        count_row.addWidget(self.historyCountLabel)
        count_row.addStretch()

        stats_layout.addLayout(count_row)

        # 历史文件位置标签（固定显示）
        self.historyLocationLabel = CaptionLabel("")
        self.historyLocationLabel.setWordWrap(True)
        self.historyLocationLabel.setStyleSheet(
            "QLabel { background-color: rgba(255, 255, 255, 0.05); padding: 8px; border-radius: 4px; }")
        stats_layout.addWidget(self.historyLocationLabel)

        # 根据是否有历史记录来更新位置标签
        if history_size > 0:
            history_file = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor", "extracted_history.json")
            self.historyLocationLabel.setText(lang.get("history_file_location", history_file))
            self.historyLocationLabel.show()
        else:
            self.historyLocationLabel.hide()

        # 操作按钮行
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 10, 0, 0)

        # 清除历史按钮（始终显示）
        self.clearHistoryButton = PrimaryPushButton(FluentIcon.DELETE, lang.get("clear_history"))
        self.clearHistoryButton.setFixedHeight(40)
        self.clearHistoryButton.clicked.connect(self.clearHistory)
        button_layout.addWidget(self.clearHistoryButton)

        # 查看历史文件按钮（根据条件显示）
        self.viewHistoryButton = PushButton(FluentIcon.VIEW, lang.get("view_history_file"))
        self.viewHistoryButton.setFixedHeight(40)
        self.viewHistoryButton.clicked.connect(
            lambda: open_directory(os.path.dirname(self.download_history.history_file)))
        button_layout.addWidget(self.viewHistoryButton)

        # 根据是否有历史记录来显示/隐藏查看按钮
        if history_size > 0:
            self.viewHistoryButton.show()
        else:
            self.viewHistoryButton.hide()

        button_layout.addStretch()
        stats_layout.addLayout(button_layout)

        content_layout.addWidget(stats_card)

        # 历史记录概览卡片（固定结构）
        self.historyOverviewCard = CardWidget()
        self.historyOverviewCard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 关键：自适应宽度
        self.historyOverviewCard.setMaximumHeight(120)
        overview_layout = QVBoxLayout(self.historyOverviewCard)
        overview_layout.setContentsMargins(20, 15, 20, 15)

        overview_title = StrongBodyLabel(lang.get("history_overview"))
        overview_layout.addWidget(overview_title)

        self.historyStatsLabel = CaptionLabel("")
        overview_layout.addWidget(self.historyStatsLabel)

        # 添加弹性空间
        overview_layout.addStretch()

        content_layout.addWidget(self.historyOverviewCard)

        # 日志区域
        log_card = CardWidget()
        log_card.setFixedHeight(300)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(lang.get("recent_activity"))
        log_layout.addWidget(log_title)

        self.historyLogText = TextEdit()
        self.historyLogText.setReadOnly(True)
        self.historyLogText.setFixedHeight(220)
        log_layout.addWidget(self.historyLogText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self.historyInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.historyLogHandler = LogHandler(self.historyLogText)

        # 应用样式
        self.setHistoryStyles()

    def updateHistoryOverview(self, history_size):
        """更新历史概览信息"""
        if history_size > 0:
            avg_files = history_size // max(1, history_size // 50)
            try:
                file_size = os.path.getsize(self.download_history.history_file) / 1024
            except:
                file_size = 0

            stats_info = f"""
• {lang.get('total_files', history_size)}
• {lang.get('avg_files_per_extraction', avg_files)}
• {lang.get('history_file_size', f"{file_size:.1f}")}
            """.strip()

            self.historyStatsLabel.setText(stats_info)
            self.historyOverviewCard.show()
        else:
            self.historyOverviewCard.hide()

    def onInterfaceChanged(self, index):
        """界面切换事件处理"""
        try:
            current_widget = self.stackedWidget.widget(index)
            # 如果切换到历史界面，刷新数据
            if current_widget == self.historyInterface:
                self.refreshHistoryInterface()
            # 如果切换到提取界面，更新线程数设置
            elif current_widget == self.extractInterface:
                # 从配置中读取默认线程数并更新界面
                default_threads = self.config_manager.get("threads", min(32, multiprocessing.cpu_count() * 2))
                if hasattr(self, 'threadsSpinBox'):
                    self.threadsSpinBox.setValue(default_threads)
        except Exception as e:
            pass

    def setupHistoryButtons(self, history_size):
        """设置历史界面的按钮"""
        # 清除旧布局
        if self.historyButtonContainer.layout():
            while self.historyButtonContainer.layout().count():
                child = self.historyButtonContainer.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        # 创建新布局
        button_layout = QHBoxLayout(self.historyButtonContainer)
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 0, 0, 0)

        # 清除历史按钮（始终显示）
        self.clearHistoryButton = PrimaryPushButton(FluentIcon.DELETE, lang.get("clear_history"))
        self.clearHistoryButton.setFixedHeight(40)
        self.clearHistoryButton.clicked.connect(self.clearHistory)
        button_layout.addWidget(self.clearHistoryButton)

        # 查看历史文件按钮（仅当有文件时显示）
        if history_size > 0:
            view_history_btn = PushButton(FluentIcon.VIEW, lang.get("view_history_file"))
            view_history_btn.setFixedHeight(40)
            view_history_btn.clicked.connect(
                lambda: open_directory(os.path.dirname(self.download_history.history_file)))
            button_layout.addWidget(view_history_btn)

        button_layout.addStretch()

    def refreshHistoryInterface(self):
        """刷新历史界面显示"""
        try:
            # 获取最新的历史记录数量
            history_size = self.download_history.get_history_size()

            # 更新计数显示
            if hasattr(self, 'historyCountLabel'):
                self.historyCountLabel.setText(lang.get("files_recorded", history_size))

            # 更新位置标签
            if hasattr(self, 'historyLocationLabel'):
                if history_size > 0:
                    history_file = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor",
                                                "extracted_history.json")
                    self.historyLocationLabel.setText(lang.get("history_file_location", history_file))
                    self.historyLocationLabel.show()
                else:
                    self.historyLocationLabel.hide()

            # 更新查看按钮的显示/隐藏
            if hasattr(self, 'viewHistoryButton'):
                if history_size > 0:
                    self.viewHistoryButton.show()
                else:
                    self.viewHistoryButton.hide()

            # 更新概览信息
            if hasattr(self, 'updateHistoryOverview'):
                self.updateHistoryOverview(history_size)

        except Exception as e:
            print(f"Error refreshing history interface: {e}")

    def setHistoryStyles(self):
        """设置历史界面样式"""
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            self.historyInterface.setStyleSheet("""
                #historyTitle {
                    color: rgb(0, 0, 0);
                    font-size: 24px;
                    font-weight: bold;
                }
                #historyCount {
                    color: rgb(0, 120, 215);
                    font-size: 20px;
                    font-weight: 600;
                }
            """)
        else:
            self.historyInterface.setStyleSheet("""
                #historyTitle {
                    color: rgb(255, 255, 255);
                    font-size: 24px;
                    font-weight: bold;
                }
                #historyCount {
                    color: rgb(0, 212, 255);
                    font-size: 20px;
                    font-weight: 600;
                }
            """)

    def setupSettingsInterface(self):
        """设置设置界面"""
        # 如果导入了CustomThemeColorCard，设置全局lang变量
        if CustomThemeColorCard is not None:
            try:
                import src.components.cards.Settings.custom_theme_color_card as custom_theme_color_card
            except ImportError:
                try:
                    import src.components.cards.custom_theme_color_card as custom_theme_color_card
                except ImportError:
                    try:
                        import custom_theme_color_card
                    except ImportError:
                        pass
            if 'custom_theme_color_card' in globals() or 'custom_theme_color_card' in locals():
                custom_theme_color_card.lang = lang
            
        # 如果导入了VersionCheckCard，设置全局lang变量
        if VersionCheckCard is not None:
            try:
                import src.components.cards.Settings.version_check_card as version_check_card
            except ImportError:
                try:
                    import src.components.cards.version_check_card as version_check_card
                except ImportError:
                    try:
                        import version_check_card
                    except ImportError:
                        pass
            if 'version_check_card' in globals() or 'version_check_card' in locals():
                version_check_card.lang = lang

        # 如果导入了AlwaysOnTopCard，设置全局lang变量
        if AlwaysOnTopCard is not None:
            try:
                import src.components.cards.Settings.always_on_top_card as always_on_top_card
                always_on_top_card.lang = lang
            except ImportError:
                pass

        # 创建滚动区域
        scroll = ScrollArea(self.settingsInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # 应用设置组
        app_group = QWidget()
        app_group_layout = QVBoxLayout(app_group)
        
        # 将标题移动到这里，在Debug模式卡片之前
        group_title = TitleLabel(lang.get("app_settings"))
        app_group_layout.addWidget(group_title)
        
        # Debug模式卡片
        if DebugModeCard is not None:
            try:
                # 设置全局语言变量
                import src.components.cards.Settings.debug_mode_card as debug_mode_card
                debug_mode_card.lang = lang
                
                debug_mode_card = DebugModeCard(
                    parent=self.settingsInterface,
                    lang=lang,
                    config_manager=self.config_manager
                )
                app_group_layout.addWidget(debug_mode_card)
            except Exception as e:
                print(f"添加Debug模式卡片时出错: {e}")
                if hasattr(self, 'settingsLogHandler'):
                    self.settingsLogHandler.error(f"添加Debug模式卡片时出错: {e}")

        # 添加总是置顶窗口设置卡片
        if AlwaysOnTopCard is not None:
            try:
                always_on_top_card = AlwaysOnTopCard(
                    parent=self.settingsInterface,
                    config_manager=self.config_manager
                )
                app_group_layout.addWidget(always_on_top_card)
            except Exception as e:
                print(f"添加总是置顶窗口卡片时出错: {e}")
                if hasattr(self, 'settingsLogHandler'):
                    self.settingsLogHandler.error(f"添加总是置顶窗口卡片时出错: {e}")

        # 添加问候语设置卡片
        if GreetingSettingCard is not None:
            try:
                # 设置全局语言变量
                import src.components.cards.Settings.greeting_setting_card as greeting_setting_card
                greeting_setting_card.lang = lang
                
                greeting_card = GreetingSettingCard(
                    parent=self.settingsInterface,
                    config_manager=self.config_manager
                )
                app_group_layout.addWidget(greeting_card)
            except Exception as e:
                print(f"添加问候语设置卡片时出错: {e}")
                if hasattr(self, 'settingsLogHandler'):
                    self.settingsLogHandler.error(f"添加问候语设置卡片时出错: {e}")

        # 语言设置卡片
        language_card = CardWidget()
        lang_card_widget = QWidget()
        lang_card_layout = QVBoxLayout(lang_card_widget)
        lang_card_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        lang_card_layout.setContentsMargins(20, 15, 20, 15)
        lang_card_layout.setSpacing(15)

        # 然后将 lang_card_widget 添加到 language_card
        language_card_layout = QVBoxLayout(language_card)
        language_card_layout.addWidget(lang_card_widget)

        # 当前语言显示
        current_lang_row = QHBoxLayout()
 
        # 添加语言图标
        current_lang_icon = IconWidget(FluentIcon.LANGUAGE)
        current_lang_icon.setFixedSize(16, 16)
        current_lang_label = BodyLabel(lang.get("current_language"))
        current_lang_value = StrongBodyLabel(lang.get_language_name())
        current_lang_row.addWidget(current_lang_icon)

        current_lang_label = BodyLabel(lang.get("current_language"))
        current_lang_value = StrongBodyLabel(lang.get_language_name())
   
        current_lang_row.addWidget(current_lang_label)
        current_lang_row.addStretch()
        current_lang_row.addWidget(current_lang_value)

        lang_card_layout.addLayout(current_lang_row)

        # 语言选择
        lang_select_row = QHBoxLayout()
        lang_select_label = BodyLabel(lang.get("select_language"))
        self.languageCombo = ComboBox()
        self.languageCombo.addItems(["中文", "English"])
        self.languageCombo.setCurrentText(lang.get_language_name())
        self.languageCombo.setFixedWidth(150)

        lang_select_row.addWidget(lang_select_label)
        lang_select_row.addStretch()
        lang_select_row.addWidget(self.languageCombo)

        lang_card_layout.addLayout(lang_select_row)

        # 应用语言按钮
        apply_lang_layout = QHBoxLayout()
        self.applyLangButton = PrimaryPushButton(FluentIcon.SAVE, lang.get("save"))
        self.applyLangButton.clicked.connect(self.applyLanguage)
        apply_lang_layout.addStretch()
        apply_lang_layout.addWidget(self.applyLangButton)

        lang_card_layout.addLayout(apply_lang_layout)
        app_group_layout.addWidget(language_card)

        # 外观设置卡片
        appearance_card = CardWidget()
        appearance_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)  # 正确
        appearance_card_layout = QVBoxLayout(appearance_card)
        appearance_card_layout.setContentsMargins(20, 15, 20, 15)
        appearance_card_layout.setSpacing(15)

        # 主题选择
        theme_row = QHBoxLayout()
        theme_label = BodyLabel(lang.get("theme_settings"))
        self.themeCombo = ComboBox()
        self.themeCombo.addItems([
            lang.get("theme_dark"),
            lang.get("theme_light"),
            lang.get("theme_system")
        ])

        # 设置当前主题
        current_theme = self.config_manager.get("theme", "dark")
        if current_theme == "dark":
            self.themeCombo.setCurrentIndex(0)
        elif current_theme == "light":
            self.themeCombo.setCurrentIndex(1)
        else:
            self.themeCombo.setCurrentIndex(2)

        self.themeCombo.currentTextChanged.connect(self.onThemeChanged)
        self.themeCombo.setFixedWidth(150)

        theme_row.addWidget(theme_label)
        theme_row.addStretch()
        theme_row.addWidget(self.themeCombo)

        appearance_card_layout.addLayout(theme_row)
        
        # 添加自定义主题颜色卡片
        if CustomThemeColorCard is not None:
            self.themeColorCard = CustomThemeColorCard(self.config_manager)
            appearance_card_layout.addWidget(self.themeColorCard)
        
        app_group_layout.addWidget(appearance_card)

        # 性能设置卡片
        performance_card = CardWidget()
        performance_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        perf_card_layout = QVBoxLayout(performance_card)  # 正确：定义 perf_card_layout
        perf_card_layout.setContentsMargins(20, 15, 20, 15)
        perf_card_layout.setSpacing(15)

        # 默认线程数设置
        threads_row = QHBoxLayout()
 
        # 添加线程图标
        threads_icon = IconWidget(FluentIcon.SPEED_OFF)
        threads_icon.setFixedSize(16, 16)

   
        threads_label = BodyLabel(lang.get("default_threads"))
        self.defaultThreadsSpinBox = SpinBox()
        self.defaultThreadsSpinBox.setRange(1, 128)
        self.defaultThreadsSpinBox.setValue(
            self.config_manager.get("threads", min(32, multiprocessing.cpu_count() * 2)))
        self.defaultThreadsSpinBox.setFixedWidth(120)
        self.defaultThreadsSpinBox.valueChanged.connect(self.saveThreadsConfig)

 
        threads_row.addWidget(threads_icon)

   
        threads_row.addWidget(threads_label)
        threads_row.addStretch()
        threads_row.addWidget(self.defaultThreadsSpinBox)

        perf_card_layout.addLayout(threads_row)
        app_group_layout.addWidget(performance_card)
        
        # 输出目录设置卡片
        output_card = CardWidget()
        output_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(20, 15, 20, 15)
        output_layout.setSpacing(15)
        
        output_title = StrongBodyLabel(lang.get("output_settings"))
        output_layout.addWidget(output_title)
        
        # 全局输入路径设置
        try:
            # 设置全局语言变量
            import src.components.cards.Settings.global_input_path_card as global_input_path_card
            global_input_path_card.lang = lang
            
            # 直接导入GlobalInputPathCard类
            from src.components.cards.Settings.global_input_path_card import GlobalInputPathCard
            
            # 如果没有设置全局输入路径，则使用默认的Roblox路径
            if not self.config_manager.get("global_input_path", ""):
                default_roblox_dir = get_roblox_default_dir()
                if default_roblox_dir:
                    self.config_manager.set("global_input_path", default_roblox_dir)
                    self.config_manager.save_config()
                    if hasattr(self, 'settingsLogHandler'):
                        self.settingsLogHandler.info(lang.get("default_roblox_path_set", "已设置默认Roblox路径") + f": {default_roblox_dir}")
            
            self.globalInputPathCard = GlobalInputPathCard(self.config_manager)
            # 连接输入路径改变信号到更新路径函数
            self.globalInputPathCard.inputPathChanged.connect(self.updateGlobalInputPath)
            # 连接恢复默认路径信号
            self.globalInputPathCard.restoreDefaultPath.connect(self.restoreDefaultInputPath)
            output_layout.addWidget(self.globalInputPathCard)
        except Exception as e:
            print(f"添加全局输入路径卡片时出错: {e}")
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.error(f"添加全局输入路径卡片时出错: {e}")
        
        # 自定义输出路径设置
        custom_output_row = QHBoxLayout()
        custom_output_label = BodyLabel(lang.get("custom_output_dir"))
        custom_output_row.addWidget(custom_output_label)
        custom_output_row.addStretch()
        
        output_layout.addLayout(custom_output_row)
        
        # 输出路径输入框和浏览按钮
        output_path_layout = QHBoxLayout()
        self.customOutputPath = LineEdit()
        self.customOutputPath.setText(self.config_manager.get("custom_output_dir", ""))
        self.customOutputPath.setPlaceholderText(lang.get("output_dir_placeholder"))
        
        browse_output_btn = PushButton(FluentIcon.FOLDER_ADD, lang.get("browse"))
        browse_output_btn.setFixedSize(80, 33)
        browse_output_btn.clicked.connect(self.browseOutputDirectory)
        
        output_path_layout.addWidget(self.customOutputPath)
        output_path_layout.addWidget(browse_output_btn)
        
        output_layout.addLayout(output_path_layout)
        
        # 保存日志选项
        save_logs_row = QHBoxLayout()
        save_logs_label = BodyLabel(lang.get("save_logs"))
        self.saveLogsSwitch = SwitchButton()
        self.saveLogsSwitch.setChecked(self.config_manager.get("save_logs", False))
        self.saveLogsSwitch.checkedChanged.connect(self.toggleSaveLogs)
        
        save_logs_row.addWidget(save_logs_label)
        save_logs_row.addStretch()
        save_logs_row.addWidget(self.saveLogsSwitch)
        
        output_layout.addLayout(save_logs_row)
        
        # 自动打开输出目录选项
        auto_open_row = QHBoxLayout()
        auto_open_label = BodyLabel(lang.get("auto_open_output_dir"))
        self.autoOpenSwitch = SwitchButton()
        self.autoOpenSwitch.setChecked(self.config_manager.get("auto_open_output_dir", True))
        self.autoOpenSwitch.checkedChanged.connect(self.toggleAutoOpenOutputDir)
        
        auto_open_row.addWidget(auto_open_label)
        auto_open_row.addStretch()
        auto_open_row.addWidget(self.autoOpenSwitch)
        
        output_layout.addLayout(auto_open_row)
        
        # 添加输出设置卡片
        app_group_layout.addWidget(output_card)
        
        # 添加版本检测卡片
        if VersionCheckCard is not None:
            version_card = CardWidget()
            version_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            version_card_layout = QVBoxLayout(version_card)
            version_card_layout.setContentsMargins(0, 0, 0, 0)  # 让VersionCheckCard处理内边距
            
            # 获取当前版本号（从注释中提取）
            current_version = VERSION  # 使用统一的版本常量
            
            # 创建版本检测卡片
            self.versionCheckCard = VersionCheckCard(self.config_manager, current_version)
            version_card_layout.addWidget(self.versionCheckCard)
            
            # 添加版本检测卡片
            app_group_layout.addWidget(version_card)

        # 添加FFmpeg状态检测卡片
        if FFmpegStatusCard is not None:
            # 设置全局语言变量
            try:
                import src.components.cards.Settings.ffmpeg_status_card as ffmpeg_status_card
                ffmpeg_status_card.lang = lang
            except ImportError:
                try:
                    import src.components.cards.ffmpeg_status_card as ffmpeg_status_card
                    ffmpeg_status_card.lang = lang
                except ImportError:
                    try:
                        import ffmpeg_status_card
                        ffmpeg_status_card.lang = lang
                    except ImportError:
                        pass
            
            ffmpeg_card = CardWidget()
            ffmpeg_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            ffmpeg_card_layout = QVBoxLayout(ffmpeg_card)
            ffmpeg_card_layout.setContentsMargins(0, 0, 0, 0)  # 让FFmpegStatusCard处理内边距
            
            # 创建FFmpeg状态卡片
            self.ffmpegStatusCard = FFmpegStatusCard()
            ffmpeg_card_layout.addWidget(self.ffmpegStatusCard)
            
            # 添加FFmpeg状态卡片
            app_group_layout.addWidget(ffmpeg_card)
            
        # 添加头像设置卡片
        try:
            from src.components.cards.Settings.avatar_setting_card import AvatarSettingCard
            # 设置全局语言变量
            import src.components.cards.Settings.avatar_setting_card as avatar_setting_card
            avatar_setting_card.lang = lang
            
            avatar_card = CardWidget()
            avatar_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            avatar_card_layout = QVBoxLayout(avatar_card)
            avatar_card_layout.setContentsMargins(0, 0, 0, 0)  # 让AvatarSettingCard处理内边距
            
            # 创建头像设置卡片
            self.avatarSettingCard = AvatarSettingCard(self.config_manager)
            avatar_card_layout.addWidget(self.avatarSettingCard)
            
            # 添加头像设置卡片
            app_group_layout.addWidget(avatar_card)
        except Exception as e:
            print(f"添加头像设置卡片时出错: {e}")

        # 日志管理卡片
        if LogControlCard is not None:
            log_control_card = LogControlCard(
                parent=self.settingsInterface,
                lang=lang,
                central_log_handler=CentralLogHandler.getInstance()
            )
            app_group_layout.addWidget(log_control_card)

        content_layout.addWidget(app_group)

        # 日志区域
        log_card = CardWidget()
        log_card.setFixedHeight(250)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(lang.get("recent_activity"))
        log_layout.addWidget(log_title)

        self.settingsLogText = TextEdit()
        self.settingsLogText.setReadOnly(True)
        self.settingsLogText.setFixedHeight(170)
        log_layout.addWidget(self.settingsLogText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self.settingsInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.settingsLogHandler = LogHandler(self.settingsLogText)

    def setupAboutInterface(self):
        """设置关于界面"""
        # 创建滚动区域
        scroll = ScrollArea(self.aboutInterface)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

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

        version_label = SubtitleLabel(lang.get("about_version"))
        version_label.setObjectName("aboutVersion")

        author_label = BodyLabel(lang.get("about_author"))
        license_label = CaptionLabel(lang.get("about_license"))

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
        desc_label = BodyLabel(lang.get("about_description"))
        desc_label.setWordWrap(True)
        about_layout.addWidget(desc_label)






        content_layout.addWidget(about_card)

        # 链接和支持卡片
        links_card = CardWidget()
        links_card.setMaximumHeight(180)  # 限制最大高度，防止异常放大
        links_layout = QVBoxLayout(links_card)
        links_layout.setContentsMargins(20, 15, 20, 15)
        links_layout.setSpacing(15)

        links_title = StrongBodyLabel(lang.get("links_and_support"))
        links_layout.addWidget(links_title)

        # GitHub链接
        github_layout = QHBoxLayout()
        github_btn = HyperlinkButton(
            "https://github.com/JustKanade/Roblox-Audio-Extractor",
            lang.get("github_link")
        )
        github_btn.setIcon(FluentIcon.GITHUB)
        github_layout.addWidget(github_btn)
        github_layout.addStretch()

        links_layout.addLayout(github_layout)

        # 技术信息
        tech_info = f"""
{lang.get('tech_stack')}: Python 3.x + PyQt5 + PyQt-Fluent-Widgets
{lang.get('purpose')}: Roblox {lang.get('extract_audio')}
{lang.get('license')}: GNU AGPLv3
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

        system_title = StrongBodyLabel(lang.get("system_info"))
        system_layout.addWidget(system_title)

        # 收集系统信息
        system_info = f"""
{lang.get('operating_system')}: {os.name} ({sys.platform})
{lang.get('python_version')}: {sys.version.split()[0]}
{lang.get('cpu_cores')}: {multiprocessing.cpu_count()}
{lang.get('ffmpeg_status')}: {lang.get('available') if is_ffmpeg_available() else lang.get('not_available')}
        """.strip()

        system_info_label = CaptionLabel(system_info)
        system_layout.addWidget(system_info_label)

        content_layout.addWidget(system_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self.aboutInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 应用样式
        self.setAboutStyles()

    def setAboutStyles(self):
        """设置关于页面样式"""
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            self.aboutInterface.setStyleSheet("""
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
            self.aboutInterface.setStyleSheet("""
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

    def loadAboutIcon(self):
        """加载关于页面图标"""
        try:
            icon_path = resource_path(os.path.join("res", "icons", "Roblox-Audio-Extractor.png"))
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

    def add_welcome_message(self):
        """添加欢迎消息到主页日志"""
        # 导入并显示时间问候
        from src.components.Greetings import TimeGreetings
        
        # 获取当前语言设置
        current_language = lang.get_language_name()
        language_code = 'en' if current_language == 'English' else 'zh'
        
        # 检查问候语是否启用
        greeting_enabled = self.config_manager.get("greeting_enabled", True)
        if greeting_enabled:
            # 使用固定样式和当前语言显示问候
            TimeGreetings.show_greeting(language_code)
        
        # 原有的日志信息
        log = LogHandler(self.homeLogText)
        log.info(lang.get('welcome_message'))
        log.info(lang.get('about_version'))
        log.info(f"{lang.get('default_dir')}: {self.default_dir}")

        log.info(lang.get("config_file_location", self.config_manager.config_file))
    def browseDirectory(self):
        """浏览目录对话框"""
        directory = QFileDialog.getExistingDirectory(self, lang.get("directory"), self.dirInput.text())
        if directory:
            self.dirInput.setText(directory)
            self.config_manager.set("last_directory", directory)
            
    def updateClassificationInfo(self):
        """更新分类信息标签"""
        if self.durationRadio.isChecked():
            self.classInfoLabel.setText(lang.get("info_duration_categories"))
        else:
            self.classInfoLabel.setText(lang.get("info_size_categories"))

    def onThemeChanged(self, theme_name):
        """主题更改事件处理"""
        # 使用主题管理器应用主题变更
        apply_theme_change(
            self, 
            theme_name, 
            self.config_manager, 
            CentralLogHandler.getInstance(), 
            self.settingsLogHandler if hasattr(self, 'settingsLogHandler') else None,
            lang
        )

    def setExtractStyles(self):
        """设置提取音频界面的样式"""
        try:
            theme = self.config_manager.get("theme", "dark")
            
            # 设置标题样式
            title_label = self.extractInterface.findChild(TitleLabel, "extractAudioTitle")
            if title_label:
                if theme == "light":
                    title_label.setStyleSheet("""
                        font-size: 28px;
                        font-weight: bold;
                        color: rgb(0, 0, 0);
                        margin-bottom: 3px;
                    """)
                else:
                    title_label.setStyleSheet("""
                        font-size: 28px;
                        font-weight: bold;
                        color: rgb(255, 255, 255);
                        margin-bottom: 3px;
                    """)
                    
        except Exception as e:
            print(f"设置提取音频界面样式时出错: {e}")

    def saveThreadsConfig(self, value):
        """保存线程数配置"""
        self.config_manager.set("threads", value)
        if hasattr(self, 'settingsLogHandler'):
            self.settingsLogHandler.info(lang.get("saved", f"{lang.get('default_threads')}: {value}"))

    def startExtraction(self):
        """开始提取音频"""
        # 获取全局输入路径（如果已设置）
        global_input_path = self.config_manager.get("global_input_path", "")
        
        # 获取用户选择的目录
        selected_dir = global_input_path if global_input_path else self.dirInput.text()
        
        # 如果使用了全局输入路径，更新输入框的显示
        if global_input_path and self.dirInput.text() != global_input_path:
            self.dirInput.setText(global_input_path)
            self.extractLogHandler.info(lang.get("using_global_input_path", "使用全局输入路径") + f": {global_input_path}")

        # 检查目录是否存在
        if not os.path.exists(selected_dir):
            result = MessageBox(
                lang.get("create_dir_prompt"),
                lang.get("dir_not_exist", selected_dir),
                self
            )

            if result.exec():
                try:
                    os.makedirs(selected_dir, exist_ok=True)
                    self.extractLogHandler.success(lang.get("dir_created", selected_dir))
                except Exception as e:
                    self.extractLogHandler.error(lang.get("dir_create_failed", str(e)))
                    return
            else:
                self.extractLogHandler.warning(lang.get("operation_cancelled"))
                return

        # 获取线程数
        try:
            num_threads = self.threadsSpinBox.value()
            if num_threads < 1:
                self.extractLogHandler.warning(lang.get("threads_min_error"))
                num_threads = min(32, multiprocessing.cpu_count() * 2)
                self.threadsSpinBox.setValue(num_threads)

            if num_threads > 64:
                result = MessageBox(
                    lang.get("confirm_high_threads"),
                    lang.get("threads_high_warning"),
                    self
                )

                if not result.exec():
                    num_threads = min(32, multiprocessing.cpu_count() * 2)
                    self.threadsSpinBox.setValue(num_threads)
                    self.extractLogHandler.info(lang.get("threads_adjusted", num_threads))
        except ValueError:
            self.extractLogHandler.warning(lang.get("input_invalid"))
            num_threads = min(32, multiprocessing.cpu_count() * 2)
            self.threadsSpinBox.setValue(num_threads)

        # 获取分类方法
        classification_method = ClassificationMethod.DURATION if self.durationRadio.isChecked() else ClassificationMethod.SIZE

        # 如果选择时长分类但没有ffmpeg，显示警告
        if classification_method == ClassificationMethod.DURATION and not is_ffmpeg_available():
            result = MessageBox(
                lang.get("confirm"),
                lang.get("ffmpeg_not_installed"),
                self
            )

            if not result.exec():
                self.extractLogHandler.warning(lang.get("operation_cancelled"))
                return

        # 获取自定义输出目录
        custom_output_dir = self.config_manager.get("custom_output_dir", "")
        
        # 创建并启动提取线程
        self.extraction_worker = ExtractionWorker(
            selected_dir,
            num_threads,
            self.download_history,
            classification_method,
            custom_output_dir  # 传递自定义输出目录参数
        )

        # 连接信号
        self.extraction_worker.progressUpdated.connect(self.updateExtractionProgress)
        self.extraction_worker.finished.connect(self.extractionFinished)
        self.extraction_worker.logMessage.connect(self.handleExtractionLog)

        # 更新UI状态
        self.extractButton.hide()
        self.cancelButton.show()
        self.progressBar.setValue(0)
        self.progressLabel.setText(lang.get("processing"))

        # 创建任务状态提示
        self.extractionStateTooltip = StateToolTip(
            lang.get("task_running"),
            lang.get("processing"),
            self
        )
        self.extractionStateTooltip.show()

        # 启动线程
        self.extraction_worker.start()
    def cancelExtraction(self):
        """取消提取操作"""
        if self.extraction_worker and self.extraction_worker.isRunning():
            self.extraction_worker.cancel()

            # 更新状态
            if hasattr(self, 'extractionStateTooltip'):
                self.extractionStateTooltip.setContent(lang.get("task_canceled"))
                self.extractionStateTooltip.setState(True)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.extractionStateTooltip.close)

            # 恢复UI
            self.cancelButton.hide()
            self.extractButton.show()

            # 重置进度条
            self.progressBar.setValue(0)
            self.progressLabel.setText(lang.get("ready"))

            self.handleExtractionLog(lang.get("canceled_by_user"), "warning")

    def updateExtractionProgress(self, current, total, elapsed, speed):
        """更新提取进度"""
        # 计算进度百分比
        progress = min(100, int((current / total) * 100)) if total > 0 else 0

        # 计算剩余时间
        remaining = (total - current) / speed if speed > 0 else 0
        remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"

        # 构建状态文本
        status_text = f"{progress}% - {current}/{total} | {speed:.1f} files/s"

        # 更新UI
        self.progressBar.setValue(progress)
        self.progressLabel.setText(status_text)
        # 更新状态提示
        if hasattr(self, 'extractionStateTooltip'):
            self.extractionStateTooltip.setContent(status_text)

    def extractionFinished(self, result):
        """提取完成处理"""
        # 恢复UI状态
        self.cancelButton.hide()
        self.extractButton.show()

        # 重置进度条为0而不是100
        self.progressBar.setValue(0)
        self.progressLabel.setText(lang.get("ready"))

        if result.get("success", False):
            # 显示提取结果
            if "processed" in result and result["processed"] > 0:
                self.extractLogHandler.success(lang.get("extraction_complete"))
                self.extractLogHandler.info(lang.get("processed", result['processed']))
                self.extractLogHandler.info(lang.get("skipped_duplicates", result.get('duplicates', 0)))
                self.extractLogHandler.info(lang.get("skipped_already_processed", result.get('already_processed', 0)))
                self.extractLogHandler.info(lang.get("errors", result.get('errors', 0)))
                self.extractLogHandler.info(lang.get("time_spent", result.get('duration', 0)))
                self.extractLogHandler.info(lang.get("files_per_sec", result.get('files_per_second', 0)))
                self.extractLogHandler.info(lang.get("output_dir", result.get('output_dir', '')))

                # 输出目录
                final_dir = result.get("output_dir", "")
                # 音频输出文件夹路径
                audio_dir = os.path.join(final_dir, "Audio")

                # 根据设置决定是否自动打开目录
                if final_dir and os.path.exists(final_dir) and self.config_manager.get("auto_open_output_dir", True):
                    # 优先打开Audio文件夹，如果存在
                    if os.path.exists(audio_dir):
                        open_success = open_directory(audio_dir)
                        if open_success:
                            self.extractLogHandler.info(lang.get("opening_output_dir", "音频总文件夹"))
                        else:
                            self.extractLogHandler.info(lang.get("manual_navigate", audio_dir))
                    else:
                        # 如果Audio文件夹不存在，打开根输出目录
                        open_success = open_directory(final_dir)
                        if open_success:
                            self.extractLogHandler.info(lang.get("opening_output_dir", lang.get("ogg_category")))
                        else:
                            self.extractLogHandler.info(lang.get("manual_navigate", final_dir))

                # 更新状态提示
                if hasattr(self, 'extractionStateTooltip'):
                    self.extractionStateTooltip.setContent(lang.get("extraction_complete"))
                    self.extractionStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.extractionStateTooltip.close)

                # 显示完成消息
                InfoBar.success(
                    title=lang.get("task_completed"),
                    content=lang.get("extraction_complete"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )

                # 刷新历史界面以显示最新的文件数量
                self.refreshHistoryInterface()
            else:
                self.extractLogHandler.warning(lang.get("no_files_processed"))

                # 更新状态提示
                if hasattr(self, 'extractionStateTooltip'):
                    self.extractionStateTooltip.setContent(lang.get("no_files_processed"))
                    self.extractionStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.extractionStateTooltip.close)
        else:
            # 显示错误
            self.extractLogHandler.error(lang.get("error_occurred", result.get('error', '')))

            # 更新状态提示
            if hasattr(self, 'extractionStateTooltip'):
                self.extractionStateTooltip.setContent(lang.get("task_failed"))
                self.extractionStateTooltip.setState(False)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.extractionStateTooltip.close)

            # 显示错误消息
            InfoBar.error(
                title=lang.get("task_failed"),
                content=result.get('error', lang.get('error_occurred', '')),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def handleExtractionLog(self, message, msg_type="info"):
        """处理提取过程中的日志消息"""
        if msg_type == "info":
            self.extractLogHandler.info(message)
        elif msg_type == "success":
            self.extractLogHandler.success(message)
        elif msg_type == "warning":
            self.extractLogHandler.warning(message)
        elif msg_type == "error":
            self.extractLogHandler.error(message)

    def clearAudioCache(self):
        """清除音频缓存"""
        # 确认对话框
        result = MessageBox(
            lang.get("clear_cache"),
            lang.get("confirm_clear_cache"),
            self
        )

        if not result.exec():
            self.cacheLogHandler.info(lang.get("operation_cancelled"))
            return

        # 创建并启动缓存清理线程
        self.cache_clear_worker = CacheClearWorker(self.default_dir)

        # 连接信号
        self.cache_clear_worker.progressUpdated.connect(self.updateCacheProgress)
        self.cache_clear_worker.finished.connect(self.cacheClearFinished)

        # 更新UI状态
        self.clearCacheButton.hide()
        self.cancelClearButton.show()
        self.cacheProgressBar.setValue(0)
        self.cacheProgressLabel.setText(lang.get("processing"))

        # 创建任务状态提示
        self.cacheStateTooltip = StateToolTip(
            lang.get("task_running"),
            lang.get("processing"),
            self
        )
        self.cacheStateTooltip.show()

        # 启动线程
        self.cache_clear_worker.start()

    def cancelClearCache(self):
        """取消缓存清理操作"""
        if self.cache_clear_worker and self.cache_clear_worker.isRunning():
            self.cache_clear_worker.cancel()

            # 更新状态
            if hasattr(self, 'cacheStateTooltip'):
                self.cacheStateTooltip.setContent(lang.get("task_canceled"))
                self.cacheStateTooltip.setState(True)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.cacheStateTooltip.close)

            # 恢复UI
            self.cancelClearButton.hide()
            self.clearCacheButton.show()

            # 重置进度条
            self.cacheProgressBar.setValue(0)
            self.cacheProgressLabel.setText(lang.get("ready"))

            self.cacheLogHandler.warning(lang.get("canceled_by_user"))

    def updateCacheProgress(self, current, total):
        """更新缓存清理进度"""
        # 计算进度百分比
        progress = min(100, int((current / total) * 100)) if total > 0 else 0

        # 构建状态文本
        status_text = f"{progress}% - {current}/{total}"

        # 更新UI
        self.cacheProgressBar.setValue(progress)
        self.cacheProgressLabel.setText(status_text)

        # 更新状态提示
        if hasattr(self, 'cacheStateTooltip'):
            self.cacheStateTooltip.setContent(status_text)

    def cacheClearFinished(self, success, cleared_files, total_files, error_msg):
        """缓存清理完成处理"""
        # 恢复UI状态
        self.cancelClearButton.hide()
        self.clearCacheButton.show()

        # 重置进度条为0而不是100
        self.cacheProgressBar.setValue(0)
        self.cacheProgressLabel.setText(lang.get("ready"))

        if success:
            if cleared_files > 0:
                self.cacheLogHandler.success(lang.get("cache_cleared", cleared_files, total_files))

                # 更新状态提示
                if hasattr(self, 'cacheStateTooltip'):
                    self.cacheStateTooltip.setContent(lang.get("cache_cleared", cleared_files, total_files))
                    self.cacheStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.cacheStateTooltip.close)
                # 显示完成消息
                InfoBar.success(
                    title=lang.get("task_completed"),
                    content=lang.get('cache_cleared', cleared_files, total_files),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            else:
                self.cacheLogHandler.warning(lang.get("no_cache_found"))

                # 更新状态提示
                if hasattr(self, 'cacheStateTooltip'):
                    self.cacheStateTooltip.setContent(lang.get("no_cache_found"))
                    self.cacheStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.cacheStateTooltip.close)
        else:
            # 显示错误
            self.cacheLogHandler.error(lang.get("clear_cache_failed", error_msg))

            # 更新状态提示
            if hasattr(self, 'cacheStateTooltip'):
                self.cacheStateTooltip.setContent(lang.get("task_failed"))
                self.cacheStateTooltip.setState(False)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.cacheStateTooltip.close)

            # 显示错误消息
            InfoBar.error(
                title=lang.get("task_failed"),
                content=lang.get('clear_cache_failed', error_msg),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def clearHistory(self):
        """清除提取历史"""
        # 确认对话框
        result = MessageBox(
            lang.get("clear_history"),
            lang.get("confirm_clear_history"),
            self
        )

        if not result.exec():
            self.historyLogHandler.info(lang.get("operation_cancelled"))
            return
            
        try:
            # 清除历史记录
            self.download_history.clear_history()

            # 延迟刷新界面，避免立即更新UI导致的问题
            QTimer.singleShot(100, self.refreshHistoryInterfaceAfterClear)

            # 显示成功消息
            if hasattr(self, 'historyLogHandler'):
                self.historyLogHandler.success(lang.get("history_cleared"))

            # 延迟显示通知，避免阻塞
            QTimer.singleShot(200, lambda: InfoBar.success(
                title=lang.get("task_completed"),
                content=lang.get('history_cleared'),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            ))
        except Exception as e:
            # 显示错误消息
            if hasattr(self, 'historyLogHandler'):
                self.historyLogHandler.error(lang.get("error_occurred", str(e)))
            traceback.print_exc()

            # 延迟显示错误通知
            QTimer.singleShot(200, lambda: InfoBar.error(
                title=lang.get("task_failed"),
                content=lang.get('error_occurred', str(e)),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            ))

    def refreshHistoryInterfaceAfterClear(self):
        """清除历史后刷新界面"""
        try:
            # 重新加载历史数据
            self.download_history.load_history()
            # 刷新界面
            self.refreshHistoryInterface()
        except Exception as e:
            print(f"Error refreshing after clear: {e}")

    def applyLanguage(self):
        """应用语言设置"""
        selected_language = self.languageCombo.currentText()
        current_language = lang.get_language_name()
        
        # 使用语言管理模块应用语言设置
        apply_language(
            self, 
            selected_language, 
            current_language, 
            lang, 
            self.settingsLogHandler if hasattr(self, 'settingsLogHandler') else None
        )

    def setResponsiveContentWidget(self, scroll_area):
        """为滚动区域内的内容容器应用响应式布局设置，防止卡片间距异常"""
        if not scroll_area or not isinstance(scroll_area, ScrollArea):
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

    def applyResponsiveLayoutToAllInterfaces(self):
        """为所有接口页面应用响应式布局"""
        # 处理每个界面
        for interface in [self.homeInterface, self.extractInterface, self.clearCacheInterface, 
                        self.historyInterface, self.settingsInterface, self.aboutInterface]:
            if not interface or not interface.layout():
                continue
                
            # 查找每个界面中的ScrollArea
            for i in range(interface.layout().count()):
                item = interface.layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), ScrollArea):
                    # 应用响应式布局
                    self.setResponsiveContentWidget(item.widget())

    def browseOutputDirectory(self):
        """浏览输出目录对话框"""
        directory = QFileDialog.getExistingDirectory(self, lang.get("directory"), self.customOutputPath.text())
        if directory:
            self.customOutputPath.setText(directory)
            self.config_manager.set("custom_output_dir", directory)

    def toggleSaveLogs(self):
        """切换保存日志选项"""
        self.config_manager.set("save_logs", self.saveLogsSwitch.isChecked())
        if hasattr(self, 'settingsLogHandler'):
            self.settingsLogHandler.info(lang.get("log_save_option_toggled"))

    def toggleAutoOpenOutputDir(self):
        """切换自动打开输出目录选项"""
        self.config_manager.set("auto_open_output_dir", self.autoOpenSwitch.isChecked())
        if hasattr(self, 'settingsLogHandler'):
            self.settingsLogHandler.info(lang.get("auto_open_toggled"))

    def updateGlobalInputPath(self, path):
        """更新全局输入路径"""
        self.config_manager.set("global_input_path", path)
        
        # 更新所有需要使用这个路径的地方
        
        # 更新提取界面的输入路径框
        if hasattr(self, 'dirInput') and self.dirInput:
            self.dirInput.setText(path)
            
        # 显示成功消息
        if hasattr(self, 'settingsLogHandler') and self.settingsLogHandler:
            self.settingsLogHandler.success(f"全局输入路径已更新: {path}")
            
        # 保存配置
        self.config_manager.save_config()

    def restoreDefaultInputPath(self):
        """恢复默认输入路径"""
        # 获取默认的Roblox路径
        default_roblox_dir = get_roblox_default_dir()
        if default_roblox_dir:
            # 更新全局输入路径
            self.config_manager.set("global_input_path", default_roblox_dir)
            self.config_manager.save_config()
            
            # 更新输入框显示
            if hasattr(self, 'globalInputPathCard') and hasattr(self.globalInputPathCard, 'inputPathEdit'):
                self.globalInputPathCard.inputPathEdit.setText(default_roblox_dir)
            
            # 调用更新路径函数
            self.updateGlobalInputPath(default_roblox_dir)
            
            # 显示成功消息
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.success(lang.get("default_path_restored") + f": {default_roblox_dir}")

    def applyAlwaysOnTop(self, is_top):
        """应用总是置顶设置"""
        apply_always_on_top(self, is_top)

    def copyPathToClipboard(self, path):
        """复制路径到剪贴板并显示提示"""
        QApplication.clipboard().setText(path)
        
        # 显示复制成功的通知
        InfoBar.success(
            title=lang.get("copied"),
            content=lang.get("path_copied_to_clipboard", path),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )


def main():
    """主函数 - 程序入口点，使用 GUI 界面"""
    try:
        # 设置高DPI缩放
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

        # 确保应用中的目录和资源存在
        app_data_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        os.makedirs(app_data_dir, exist_ok=True)
        

        
        icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "res", "icons")
        os.makedirs(icon_dir, exist_ok=True)

        # 创建应用程序实例
        app = QApplication(sys.argv)

        # 设置应用信息
        app.setApplicationName("Roblox Audio Extractor")
        app.setApplicationDisplayName("Roblox Audio Extractor")
        app.setApplicationVersion(VERSION)
        app.setOrganizationName("JustKanade")

        # 设置应用图标
        try:
            icon_path = resource_path(os.path.join("res", "icons", "Roblox-Audio-Extractor.png"))
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"无法设置应用图标: {e}")

        # 创建主窗口实例
        main_window = MainWindow()

        # 显示启动画面（可选）
        try:
            splash_icon = resource_path(os.path.join("res", "icons", "Roblox-Audio-Extractor.png"))
            if os.path.exists(splash_icon):
                splash = SplashScreen(QIcon(splash_icon), main_window)
                splash.setIconSize(QSize(150, 150))
                splash.raise_()

                # 显示启动画面2秒后关闭
                QTimer.singleShot(2000, splash.finish)
        except Exception as e:
            print(f"无法显示启动画面: {e}")

        # 显示主窗口
        main_window.show()

        # 运行应用程序
        return app.exec_()
    except Exception as e:
        logger.error(f"程序出错: {e}")
        traceback.print_exc()
        
        # 保存崩溃日志
        try:
            CentralLogHandler.getInstance().save_crash_log(str(e), traceback.format_exc())
        except Exception as log_e:
            print(f"保存崩溃日志失败: {str(log_e)}")
            
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # 在终端模式下记录错误
        logger.error(f"发生错误: {str(e)}")
        traceback.print_exc()
        
        # 保存崩溃日志
        crash_log_path = None
        try:
            crash_log_path = CentralLogHandler.getInstance().save_crash_log(str(e), traceback.format_exc())
        except Exception as log_e:
            print(f"保存崩溃日志失败: {str(log_e)}")

        # 尝试显示错误对话框
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            from PyQt5.QtWidgets import QMessageBox

            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle("错误")
            error_dialog.setText(f"发生错误: {str(e)}")
            
            # 添加详细信息
            detailed_text = traceback.format_exc()
            if crash_log_path:
                detailed_text += f"\n\n崩溃日志已保存至: {crash_log_path}"
            error_dialog.setDetailedText(detailed_text)
            
            error_dialog.exec_()
        except:
            pass

        sys.exit(1)