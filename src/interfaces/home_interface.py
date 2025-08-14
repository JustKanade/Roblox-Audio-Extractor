#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QGridLayout,
    QLabel, QFrame
)
from PyQt5.QtCore import Qt, QSize

from qfluentwidgets import (
    ScrollArea, CardWidget, DisplayLabel, BodyLabel, CaptionLabel,
    StrongBodyLabel, SubtitleLabel, PrimaryPushButton, PushButton,
    TransparentPushButton, FluentIcon, TextEdit, PillPushButton,
    FlowLayout, SettingCardGroup, ExpandLayout
)

from src.utils.file_utils import resource_path, open_directory
from src.utils.log_utils import LogHandler
from src.interfaces.about_interface import BannerWidget
from src.components.cards.home_cards import (
    QuickActionsCard, SystemInfoHomeCard, DirectoryInfoCard,
    ExtractMenuCard, ClearCacheCard, SettingsCard
)
from src.components.cards.recent_activity_card import RecentActivityCard
from src.management.theme_management.interface_theme_mixin import InterfaceThemeMixin
from typing import Any, Optional

class HomeInterface(QWidget, InterfaceThemeMixin):
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
        scroll.setObjectName('homeScrollArea')

        # 主内容容器
        content_widget = QWidget()
        content_widget.setObjectName('homeScrollWidget')
        self.expandLayout = ExpandLayout(content_widget)
        self.expandLayout.setContentsMargins(20, 20, 20, 20)
        self.expandLayout.setSpacing(28)

        # 欢迎横幅 - 复用BannerWidget，只显示程序logo
        self.welcome_banner = BannerWidget(parent=content_widget, config_manager=self.config_manager, lang=self.lang, use_logo_only=True)
        self.expandLayout.addWidget(self.welcome_banner)

        # 快速操作卡片组
        self.quickActionsGroup = SettingCardGroup(
            self.lang.get("quick_actions", "Quick Actions"), 
            content_widget
        )
        
        # 快速操作卡片
        self.quickActionsCard = QuickActionsCard(parent=self.quickActionsGroup, lang=self.lang)
        # 连接按钮事件

        self.quickActionsGroup.addSettingCard(self.quickActionsCard)
        
        # 内容提取下拉菜单卡片
        self.extractMenuCard = ExtractMenuCard(parent=self.quickActionsGroup, lang=self.lang)
        # 连接菜单项事件
        self.extractMenuCard.get_audio_action().triggered.connect(lambda: self.switchToInterface("extractInterface"))
        self.extractMenuCard.get_fonts_action().triggered.connect(lambda: self.switchToInterface("extractFontsInterface"))
        self.extractMenuCard.get_translations_action().triggered.connect(lambda: self.switchToInterface("extractTranslationsInterface"))
        self.extractMenuCard.get_videos_action().triggered.connect(lambda: self.switchToInterface("extractVideosInterface"))
        self.quickActionsGroup.addSettingCard(self.extractMenuCard)
        
        # 清理缓存独立卡片
        self.clearCacheCard = ClearCacheCard(parent=self.quickActionsGroup, lang=self.lang)
        self.clearCacheCard.clear_btn.clicked.connect(lambda: self.switchToInterface("clearCacheInterface"))
        self.quickActionsGroup.addSettingCard(self.clearCacheCard)
        
        # 设置独立卡片
        self.settingsCard = SettingsCard(parent=self.quickActionsGroup, lang=self.lang)
        self.settingsCard.settings_btn.clicked.connect(lambda: self.switchToInterface("settingsInterface"))
        self.quickActionsGroup.addSettingCard(self.settingsCard)
        
        self.expandLayout.addWidget(self.quickActionsGroup)

        # 系统信息卡片组  
        self.systemGroup = SettingCardGroup(
            self.lang.get("system_info", "System Information"),
            content_widget
        )
        
        # 系统信息卡片
        self.systemInfoCard = SystemInfoHomeCard(parent=self.systemGroup, lang=self.lang)
        self.systemGroup.addSettingCard(self.systemInfoCard)
        
        # 目录信息卡片
        self.directoryCard = DirectoryInfoCard(parent=self.systemGroup, lang=self.lang, default_dir=self.default_dir)
        # 连接按钮事件
        self.directoryCard.open_dir_btn.clicked.connect(lambda: open_directory(self.default_dir))
        self.directoryCard.copy_path_btn.clicked.connect(lambda: self.copyPathToClipboard(self.default_dir))
        self.systemGroup.addSettingCard(self.directoryCard)
        
        self.expandLayout.addWidget(self.systemGroup)

        # 最近活动日志卡片组
        self.activityGroup = SettingCardGroup(
            self.lang.get("recent_activity", "Recent Activity"),
            content_widget
        )
        
        # 最近活动日志卡片
        self.recent_activity_card = RecentActivityCard(parent=self.activityGroup, lang=self.lang, config_manager=self.config_manager)
        # 保持向后兼容性
        self.homeLogText = self.recent_activity_card.get_text_edit()
        self.logHandler = self.recent_activity_card.get_log_handler()

        self.activityGroup.addSettingCard(self.recent_activity_card)
        self.expandLayout.addWidget(self.activityGroup)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 应用样式
        self.setInterfaceStyles()
        
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
        
    def switchToInterface(self, interface_name):
        """通过发送信号切换界面（由主窗口实现具体切换逻辑）"""
        # 这个方法会在主窗口中被重写覆盖，这里只是一个占位
        pass
        


    def setInterfaceStyles(self):
        """设置主页样式"""
        # 调用父类的通用样式设置
        super().setInterfaceStyles()
        
        # 获取文本样式
        text_styles = self.get_text_styles()
        
        # 应用特定的主页样式
        specific_styles = f"""
            #homeInterface {{
                background-color: transparent;
            }}
            #homeScrollArea {{
                background-color: transparent;
                border: none;
            }}
            #homeScrollWidget {{
                background-color: transparent;
            }}
            #aboutTitle {{
                {text_styles['title']}
            }}
            #aboutVersion {{
                {text_styles['version']}
            }}
        """
        
        # 合并通用样式和特定样式
        combined_styles = self.get_common_interface_styles() + specific_styles
        self.setStyleSheet(combined_styles)
            

            
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
            self.logHandler.info(self.lang.get('welcome_message'))
            self.logHandler.info(self.lang.get('about_version'))
            self.logHandler.info(f"{self.lang.get('default_dir')}: {self.default_dir}")
            self.logHandler.info(self.lang.get("config_file_location", self.config_manager.config_file))
        except Exception as e:
            print(f"添加欢迎信息时出错: {e}") 