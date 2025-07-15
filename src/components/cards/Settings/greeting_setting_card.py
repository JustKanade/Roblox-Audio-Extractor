#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问候语设置卡片组件
Greeting Setting Card Component
"""

import os
import sys
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal

from qfluentwidgets import (
    CardWidget, SwitchButton, FluentIcon, InfoBar,
    InfoBarPosition, StrongBodyLabel, BodyLabel, IconWidget
)

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None  # 如果导入失败，设为None


class GreetingSettingCard(CardWidget):
    """
    问候语设置卡片，提供启用/禁用问候通知的功能
    Greeting setting card, provides enabling/disabling greeting notifications
    """
    
    def __init__(self, parent=None, config_manager=None):
        """
        初始化问候语设置卡片
        
        Args:
            parent: 父控件
            config_manager: 配置管理器实例
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.greeting_enabled = self.config_manager.get("greeting_enabled", True) if config_manager else True
        self.setupUI()
    
    def setupUI(self):
        """设置UI布局"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # 标题行布局
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # 添加图标
        title_icon = IconWidget(FluentIcon.HEART, self)
        title_icon.setFixedSize(16, 16)
        
        # 标题
        title_label = StrongBodyLabel(self._get_text("greeting_setting"))
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # 问候语启用选项
        greeting_row = QHBoxLayout()
        
        greeting_label = BodyLabel(self._get_text("greeting_setting_description"))
        self.greeting_switch = SwitchButton()
        self.greeting_switch.setChecked(self.greeting_enabled)
        self.greeting_switch.checkedChanged.connect(self.on_greeting_enabled_changed)
        
        greeting_row.addWidget(greeting_label)
        greeting_row.addStretch()
        greeting_row.addWidget(self.greeting_switch)
        
        main_layout.addLayout(greeting_row)
    
    def on_greeting_enabled_changed(self, is_checked):
        """问候语设置改变的响应函数"""
        self.greeting_enabled = is_checked
        if self.config_manager:
            self.config_manager.set("greeting_enabled", is_checked)
            
        # 显示提示消息
        self.showMessage(
            "success" if is_checked else "info",
            self._get_text("greeting_enabled" if is_checked else "greeting_disabled"),
            self._get_text("greeting_enabled_description" if is_checked else "greeting_disabled_description")
        )
    
    def _get_text(self, key, default=""):
        """获取翻译文本"""
        global lang
        if lang and hasattr(lang, 'get'):
            return lang.get(key, default)
        
        # 默认文本（中文）
        texts = {
            "greeting_setting": "问候语设置",
            "greeting_setting_description": "启用或禁用程序启动时的问候通知",
            "greeting_enabled": "问候语已启用",
            "greeting_disabled": "问候语已禁用",
            "greeting_enabled_description": "程序启动时将显示问候通知",
            "greeting_disabled_description": "程序启动时将不再显示问候通知"
        }
        return texts.get(key, default)
    
    def showMessage(self, msg_type, title, content):
        """显示消息通知"""
        if msg_type == "success":
            InfoBar.success(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
        elif msg_type == "info":
            InfoBar.info(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
        elif msg_type == "warning":
            InfoBar.warning(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
        elif msg_type == "error":
            InfoBar.error(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            ) 
            
    def setLanguageManager(self, lang_manager):
        """设置语言管理器"""
        global lang
        lang = lang_manager 