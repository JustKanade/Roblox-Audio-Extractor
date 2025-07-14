#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt

from qfluentwidgets import (
    CardWidget, BodyLabel, TitleLabel, StrongBodyLabel,
    ScrollArea, PushButton, TransparentPushButton, 
    FluentIcon, CaptionLabel, ProgressBar, PrimaryPushButton,
    TextEdit, IconWidget
)

from src.utils.file_utils import open_directory
from src.utils.log_utils import LogHandler


class ClearCacheInterface(QWidget):
    """缓存清理界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None, default_dir=None):
        super().__init__(parent)
        self.setObjectName("clearCacheInterface")
        self.config_manager = config_manager
        self.lang = lang
        self.default_dir = default_dir
        self._parent_window = parent  # 使用不同的名字避免混淆
        
        # 确保语言对象存在，否则创建空的语言处理函数
        if self.lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = self.lang.get
        
        # 初始化界面
        self.initUI()
        # 应用样式
        self.setCacheStyles()
        
    def initUI(self):
        """初始化界面"""
        # 创建滚动区域
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
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
        info_title = TitleLabel(self.get_text("clear_cache", "清除缓存"))
        info_title.setObjectName("cacheTitle")
        info_layout.addWidget(info_title)

        # 描述
        desc_label = BodyLabel(self.get_text("cache_description", "清除Roblox音频缓存文件，释放磁盘空间。"))
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        # 缓存位置信息
        location_row = QHBoxLayout()
        location_icon = IconWidget(FluentIcon.FOLDER)
        location_icon.setFixedSize(20, 20)
        location_label = StrongBodyLabel(self.get_text("cache_location", "缓存位置"))
        
        location_row.addWidget(location_icon)
        location_row.addWidget(location_label)
        location_row.addStretch()

        info_layout.addLayout(location_row)

        # 缓存路径
        cache_path_label = CaptionLabel(self.default_dir if self.default_dir else "")
        cache_path_label.setWordWrap(True)
        cache_path_label.setStyleSheet(
            "QLabel { background-color: rgba(255, 255, 255, 0.05); padding: 8px; border-radius: 4px; }")
        info_layout.addWidget(cache_path_label)

        # 快速操作按钮
        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(10)

        open_cache_btn = PushButton(FluentIcon.FOLDER, self.get_text("open_directory", "打开目录"))
        # 使用安全的方法连接事件
        open_cache_btn.clicked.connect(lambda: self._openDirectory())

        copy_cache_btn = TransparentPushButton(FluentIcon.COPY, self.get_text("copy_path", "复制路径"))
        # 使用安全的方法连接事件
        copy_cache_btn.clicked.connect(lambda: self._copyPathToClipboard())

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
        self.progressBar = ProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        self.progressLabel = CaptionLabel(self.get_text("ready", "就绪"))
        self.progressLabel.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progressBar)
        progress_layout.addWidget(self.progressLabel)

        control_layout.addLayout(progress_layout)

        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.clearCacheButton = PrimaryPushButton(FluentIcon.DELETE, self.get_text("clear_cache", "清除缓存"))
        self.clearCacheButton.setFixedHeight(40)
        # 使用安全的方法连接事件
        self.clearCacheButton.clicked.connect(lambda: self._clearCache())

        self.cancelClearButton = PushButton(FluentIcon.CLOSE, self.get_text("cancel", "取消"))
        self.cancelClearButton.setFixedHeight(40)
        # 使用安全的方法连接事件
        self.cancelClearButton.clicked.connect(lambda: self._cancelClearCache())
        self.cancelClearButton.hide()

        button_layout.addWidget(self.clearCacheButton)
        button_layout.addWidget(self.cancelClearButton)
        button_layout.addStretch()

        control_layout.addLayout(button_layout)
        content_layout.addWidget(control_card)

        # 日志区域
        log_card = CardWidget()
        log_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(self.get_text("recent_activity", "最近活动"))
        log_layout.addWidget(log_title)

        self.logText = TextEdit()
        self.logText.setReadOnly(True)
        self.logText.setFixedHeight(220)
        log_layout.addWidget(self.logText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.logHandler = LogHandler(self.logText)
    
    def _openDirectory(self):
        """安全地打开缓存目录"""
        if self.default_dir:
            open_directory(self.default_dir)
            
    def _copyPathToClipboard(self):
        """安全地复制路径到剪贴板"""
        if self._parent_window and hasattr(self._parent_window, 'copyPathToClipboard') and self.default_dir:
            self._parent_window.copyPathToClipboard(self.default_dir)
            
    def _clearCache(self):
        """安全地调用清除缓存方法"""
        if self._parent_window and hasattr(self._parent_window, 'clearAudioCache'):
            self._parent_window.clearAudioCache()
            
    def _cancelClearCache(self):
        """安全地调用取消清除缓存方法"""
        if self._parent_window and hasattr(self._parent_window, 'cancelClearCache'):
            self._parent_window.cancelClearCache()
        
    def setCacheStyles(self):
        """设置缓存界面样式"""
        if not self.config_manager:
            return
            
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            self.setStyleSheet("""
                #cacheTitle {
                    color: rgb(0, 0, 0);
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                #cacheTitle {
                    color: rgb(255, 255, 255);
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
            
    def updateProgressBar(self, value):
        """更新进度条"""
        if hasattr(self, 'progressBar'):
            self.progressBar.setValue(value)
            
    def updateProgressLabel(self, text):
        """更新进度标签"""
        if hasattr(self, 'progressLabel'):
            self.progressLabel.setText(text)
            
    def showCancelButton(self, show=True):
        """显示/隐藏取消按钮"""
        if hasattr(self, 'cancelClearButton'):
            if show:
                self.cancelClearButton.show()
            else:
                self.cancelClearButton.hide()
                
    def showClearButton(self, show=True):
        """显示/隐藏清除按钮"""
        if hasattr(self, 'clearCacheButton'):
            if show:
                self.clearCacheButton.show()
            else:
                self.clearCacheButton.hide() 