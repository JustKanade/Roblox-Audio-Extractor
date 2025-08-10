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
    TextEdit, IconWidget, SettingCardGroup, SettingCard, LineEdit, SwitchSettingCard
)

import os
import sys

from src.utils.file_utils import open_directory
from src.utils.log_utils import LogHandler
from src.components.cards.recent_activity_card import RecentActivityCard

# 尝试导入LogControlCard
try:
    from src.components.cards.Settings.log_control_card import LogControlCard
except ImportError:
    LogControlCard = None

# 导入中央日志处理器
from src.logging.central_log_handler import CentralLogHandler


class ClearCacheInterface(QWidget):
    """缓存清理界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None, default_dir=None):
        super().__init__(parent)
        self.setObjectName("clearCacheInterface")
        self.config_manager = config_manager
        self.lang = lang
        self.default_dir = default_dir
        self._parent_window = parent  # 使用不同的名字避免混淆
        
        # 获取路径管理器
        self.path_manager = getattr(config_manager, 'path_manager', None) if config_manager else None
        
        # 确保语言对象存在，否则创建空的语言处理函数
        if self.lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = self.lang.get
        
        # 初始化界面
        self.initUI()
        # 应用样式
        self.setCacheStyles()
        
        # 连接路径管理器信号实现实时同步
        if self.path_manager:
            self.path_manager.globalInputPathChanged.connect(self.onGlobalInputPathChanged)
        
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
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # 创建缓存信息设置卡片组
        cache_info_group = SettingCardGroup(self.get_text("cache_info", "缓存信息"))
        
        # 缓存位置信息卡片
        self.cache_location_card = SettingCard(
            FluentIcon.FOLDER,
            self.get_text("cache_location", "缓存位置"),
            self.get_text("cache_description", "清除Roblox数据库和存储缓存，释放磁盘空间。提取的文件将被保留。")
        )
        
        # 获取有效的缓存路径
        effective_cache_path = self._getEffectiveCachePath()
        
        # 创建路径显示控件容器
        path_widget = QWidget()
        path_layout = QVBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 20, 0)
        path_layout.setSpacing(8)
        
        # 缓存路径显示
        self.cache_path_edit = LineEdit()
        self.cache_path_edit.setText(effective_cache_path)
        self.cache_path_edit.setReadOnly(True)  # 设置为只读
        self.cache_path_edit.setClearButtonEnabled(False)  # 禁用清除按钮
        self.cache_path_edit.setPlaceholderText(self.get_text("cache_path_placeholder", "Roblox缓存目录路径"))
        self.cache_path_edit.setMinimumWidth(370)  # 延长缓存路径显示
        self.cache_path_edit.setMaximumWidth(400)  # 可根据界面自适应调整
        path_layout.addWidget(self.cache_path_edit)

        # 将路径控件添加到卡片
        self.cache_location_card.hBoxLayout.addWidget(path_widget)
        cache_info_group.addSettingCard(self.cache_location_card)

        # 清理详情1：数据库文件卡片
        self.db_file_card = SettingCard(
            FluentIcon.DOCUMENT,
            self.get_text("cache_db_file", "rbx-storage.db 数据库文件"),
            self.get_text("cache_db_file_desc", "Roblox客户端的数据库文件，包含缓存索引信息")
        )
        cache_info_group.addSettingCard(self.db_file_card)

        # 清理详情2：文件夹内容卡片  
        self.folder_content_card = SettingCard(
            FluentIcon.FOLDER,
            self.get_text("cache_folder_content", "rbx-storage 文件夹中的内容（除了extracted文件夹）"),
            self.get_text("cache_folder_content_desc", "Roblox缓存文件夹中的临时文件和资源缓存")
        )
        cache_info_group.addSettingCard(self.folder_content_card)
        
        # 快速操作卡片
        self.quick_actions_card = SettingCard(
            FluentIcon.COMMAND_PROMPT,
            self.get_text("quick_actions", "快速操作"),
            self.get_text("quick_actions_info", "快速访问和管理缓存目录")
        )
        
        # 创建快速操作控件容器
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 20, 0)
        actions_layout.setSpacing(10)
        
        open_cache_btn = PushButton(FluentIcon.FOLDER, self.get_text("open_directory", "打开目录"))
        open_cache_btn.setFixedSize(150, 32)
        # 使用安全的方法连接事件
        open_cache_btn.clicked.connect(lambda: self._openDirectory())

        copy_cache_btn = TransparentPushButton(FluentIcon.COPY, self.get_text("copy_path", "复制路径"))
        copy_cache_btn.setFixedSize(120, 32)
        # 使用安全的方法连接事件
        copy_cache_btn.clicked.connect(lambda: self._copyPathToClipboard())

        actions_layout.addStretch()
        actions_layout.addWidget(open_cache_btn)
        actions_layout.addWidget(copy_cache_btn)
        
        # 将快速操作控件添加到卡片
        self.quick_actions_card.hBoxLayout.addWidget(actions_widget)
        cache_info_group.addSettingCard(self.quick_actions_card)
        
        # 自动清除缓存设置卡片
        self.auto_clear_cache_card = SwitchSettingCard(
            FluentIcon.BROOM,
            self.get_text("auto_clear_cache", "自动清除缓存"),
            self.get_text("auto_clear_cache_desc", "在音频提取完成后自动清除Roblox缓存，节省磁盘空间")
        )
        
        # 设置默认值和状态
        if self.config_manager:
            auto_clear_enabled = self.config_manager.cfg.get(self.config_manager.cfg.autoClearCacheEnabled)
            self.auto_clear_cache_card.setChecked(auto_clear_enabled)
        else:
            self.auto_clear_cache_card.setChecked(False)
        
        # 连接开关变化信号
        self.auto_clear_cache_card.checkedChanged.connect(self.onAutoClearCacheChanged)
        cache_info_group.addSettingCard(self.auto_clear_cache_card)
        
        # 日志管理卡片
        if LogControlCard:
            self.log_management_card = LogControlCard(
                parent=self,
                lang=self.lang,
                central_log_handler=CentralLogHandler.getInstance()
            )
            cache_info_group.addSettingCard(self.log_management_card)
        
        content_layout.addWidget(cache_info_group)

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

        # 添加弹性空间，将按钮推至右侧
        button_layout.addStretch()

        self.cancelClearButton = PushButton(FluentIcon.CLOSE, self.get_text("cancel", "取消"))
        self.cancelClearButton.setFixedHeight(40)
        # 使用安全的方法连接事件
        self.cancelClearButton.clicked.connect(lambda: self._cancelClearCache())
        self.cancelClearButton.hide()
        button_layout.addWidget(self.cancelClearButton)

        self.clearCacheButton = PrimaryPushButton(FluentIcon.DELETE, self.get_text("clear_cache", "清除缓存"))
        self.clearCacheButton.setFixedHeight(40)
        # 使用安全的方法连接事件
        self.clearCacheButton.clicked.connect(lambda: self._clearCache())
        button_layout.addWidget(self.clearCacheButton)

        control_layout.addLayout(button_layout)

        # 日志区域
        self.recent_activity_card = RecentActivityCard(parent=content_widget, lang=self.lang, config_manager=self.config_manager)
        # 保持向后兼容性
        self.logText = self.recent_activity_card.get_text_edit()

        content_layout.addWidget(self.recent_activity_card)
        
        # 确保布局末尾有伸缩项，防止界面被拉伸
        content_layout.addStretch(1)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.logHandler = self.recent_activity_card.get_log_handler()
    
    def _getEffectiveCachePath(self) -> str:
        """获取有效的缓存路径"""
        # 优先使用路径管理器的有效路径
        if self.path_manager:
            effective_path = self.path_manager.get_effective_input_path()
            if effective_path and os.path.exists(effective_path):
                return effective_path
        
        # 备用方案：使用路径管理器的默认Roblox路径
        if self.path_manager:
            roblox_path = self.path_manager.get_roblox_default_dir()
            if roblox_path and os.path.exists(roblox_path):
                return roblox_path
        
        # 最后备用方案：手动获取Roblox本地数据目录
        if sys.platform == 'win32':  # Windows
            roblox_local_dir = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Roblox')
        elif sys.platform == 'darwin':  # macOS
            roblox_local_dir = os.path.expanduser('~/Library/Application Support/Roblox')
        else:  # Linux或其他系统
            roblox_local_dir = os.path.expanduser('~/.local/share/Roblox')
        
        return roblox_local_dir if os.path.exists(roblox_local_dir) else self.get_text("path_not_found", "未找到缓存目录")
    
    def _openDirectory(self):
        """安全地打开缓存目录"""
        effective_path = self._getEffectiveCachePath()
        if effective_path and os.path.exists(effective_path):
            open_directory(effective_path)
            if hasattr(self, 'logHandler'):
                self.logHandler.info(f"{self.get_text('opened_directory', '已打开目录')}: {effective_path}")
        else:
            if hasattr(self, 'logHandler'):
                self.logHandler.warning(self.get_text("directory_not_found", "目录不存在"))
            
    def _copyPathToClipboard(self):
        """安全地复制路径到剪贴板"""
        effective_path = self._getEffectiveCachePath()
        if self._parent_window and hasattr(self._parent_window, 'copyPathToClipboard'):
            self._parent_window.copyPathToClipboard(effective_path)
            if hasattr(self, 'logHandler'):
                self.logHandler.info(f"{self.get_text('copied_path', '已复制路径')}: {effective_path}")
    
    def onGlobalInputPathChanged(self, new_path: str):
        """全局输入路径变更处理"""
        if hasattr(self, 'cache_path_edit'):
            # 获取新的有效缓存路径
            effective_path = self._getEffectiveCachePath()
            
            # 更新界面显示
            current_text = self.cache_path_edit.text().strip()
            if current_text != effective_path:
                self.cache_path_edit.setText(effective_path)
                # 记录路径变更
                if hasattr(self, 'logHandler'):
                    self.logHandler.info(f"{self.get_text('cache_path_synced', '缓存路径已同步')}: {effective_path}")
    
    def onAutoClearCacheChanged(self, checked: bool):
        """自动清除缓存开关状态变化处理"""
        if self.config_manager:
            # 保存开关状态到配置
            self.config_manager.cfg.set(self.config_manager.cfg.autoClearCacheEnabled, checked)
            # 记录开关状态变更
            if hasattr(self, 'logHandler'):
                status_text = self.get_text('enabled') if checked else self.get_text('disabled')
                self.logHandler.info(f"{self.get_text('auto_clear_cache_status_changed', '自动清除缓存状态已更改')}: {status_text}")
    
    def isAutoClearCacheEnabled(self) -> bool:
        """获取自动清除缓存开关状态"""
        if hasattr(self, 'auto_clear_cache_card'):
            return self.auto_clear_cache_card.isChecked()
        elif self.config_manager:
            return self.config_manager.cfg.get(self.config_manager.cfg.autoClearCacheEnabled)
        return False
            
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
            
        theme = self.config_manager.get("theme")

        if theme == "light":
            # 浅色模式样式
            text_color = "rgb(0, 0, 0)"
        else:
            # 深色模式样式
            text_color = "rgb(255, 255, 255)"
        
        # 设置日志文本编辑器样式
        if hasattr(self, 'logText'):
            self.logText.setStyleSheet(f"""
                TextEdit {{
                    font-family: Consolas, Courier, monospace;
                    color: {text_color};
                }}
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