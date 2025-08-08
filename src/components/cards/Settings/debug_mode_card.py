#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug模式卡片组件 - 提供崩溃时日志保存功能
Debug Mode Card Component - Provides crash log saving functionality
"""

import os
import sys
import traceback
import subprocess
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal

from qfluentwidgets import (
    CardWidget, SwitchButton, FluentIcon, InfoBar,
    InfoBarPosition, StrongBodyLabel, BodyLabel, IconWidget,
    PrimaryPushButton
)


class DebugModeCard(CardWidget):
    """
    Debug模式卡片，提供崩溃时日志保存功能
    Debug Mode Card, provides crash log saving functionality
    """
    
    def __init__(self, parent=None, lang=None, config_manager=None):
        """
        初始化Debug模式卡片
        
        Args:
            parent: 父控件
            lang: 语言管理器
            config_manager: 配置管理器实例
        """
        super().__init__(parent)
        self.lang = lang
        self.config_manager = config_manager
        self.debug_mode_enabled = self.config_manager.get("debug_mode_enabled", True) if config_manager else True
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
        title_icon = IconWidget(FluentIcon.COMMAND_PROMPT, self)
        title_icon.setFixedSize(16, 16)
        
        # 标题
        title_text = "Debug模式"
        if self.lang and hasattr(self.lang, 'get'):
            title_text = self.lang.get("debug_mode") or title_text
        title_label = StrongBodyLabel(title_text)
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # Debug模式选项
        debug_mode_row = QHBoxLayout()
        
        description_text = "在程序崩溃时生成错误日志"
        if self.lang and hasattr(self.lang, 'get'):
            description_text = self.lang.get("debug_mode_description") or description_text
        debug_mode_label = BodyLabel(description_text)
        
        self.debug_mode_switch = SwitchButton()
        self.debug_mode_switch.setChecked(self.debug_mode_enabled)
        self.debug_mode_switch.checkedChanged.connect(self.on_debug_mode_changed)
        
        debug_mode_row.addWidget(debug_mode_label)
        debug_mode_row.addStretch()
        debug_mode_row.addWidget(self.debug_mode_switch)
        
        main_layout.addLayout(debug_mode_row)
        
        # 添加打开错误日志文件夹按钮到开关下方
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 5, 0, 0)  # 添加一点上边距
        
        button_text = "打开错误日志文件夹"
        if self.lang and hasattr(self.lang, 'get'):
            button_text = self.lang.get("open_error_logs_folder") or button_text
        open_logs_button = PrimaryPushButton(button_text)
        open_logs_button.clicked.connect(self.open_error_logs_folder)
        
        button_row.addStretch()
        button_row.addWidget(open_logs_button)
        
        main_layout.addLayout(button_row)
    
    def on_debug_mode_changed(self, is_checked):
        """Debug模式设置改变的响应函数"""
        self.debug_mode_enabled = is_checked
        if self.config_manager:
            self.config_manager.set("debug_mode_enabled", is_checked)
            
        # 获取标题和内容
        if is_checked:
            title = "Debug模式已启用"
            content = "程序将在崩溃时生成详细的错误日志"
            
            if self.lang and hasattr(self.lang, 'get'):
                title = self.lang.get("debug_mode_enabled") or title
                content = self.lang.get("debug_mode_enabled_tip") or content
        else:
            title = "Debug模式已禁用"
            content = "程序崩溃时不会生成错误日志"
            
            if self.lang and hasattr(self.lang, 'get'):
                title = self.lang.get("debug_mode_disabled") or title
                content = self.lang.get("debug_mode_disabled_tip") or content
                
        # 显示提示消息
        self.showMessage(
            "success" if is_checked else "info",
            title,
            content
        )
    
    def open_error_logs_folder(self):
        """打开错误日志文件夹"""
        try:
            # 使用统一的崩溃日志路径工具
            from src.utils.log_utils import get_crash_log_dir
            crash_log_dir = get_crash_log_dir()
            
            # 根据操作系统打开文件夹
            if sys.platform == 'win32':
                os.startfile(crash_log_dir)
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', crash_log_dir])
            else:  # Linux
                subprocess.Popen(['xdg-open', crash_log_dir])
            
            # 获取成功消息
            title = "打开文件夹成功"
            content = "已打开错误日志文件夹"
            
            if self.lang and hasattr(self.lang, 'get'):
                title = self.lang.get("open_folder_success") or title
                content = self.lang.get("error_logs_folder_opened") or content
                
            # 显示成功消息
            self.showMessage("success", title, content)
        except Exception as e:
            # 获取错误消息
            title = "打开文件夹失败"
            content = f"打开文件夹时出错: {str(e)}"
            
            if self.lang and hasattr(self.lang, 'get'):
                title = self.lang.get("open_folder_failed") or title
                content = self.lang.get("error_opening_folder", str(e)) or content
            
            # 显示错误消息
            self.showMessage("error", title, content)
    
    def showMessage(self, msg_type, title, content):
        """显示消息通知
        
        Args:
            msg_type: 消息类型 (success, warning, error, info)
            title: 标题
            content: 内容
        """
        # 获取主窗口作为父控件，确保消息显示在最上方
        main_window = self.window()
        parent = main_window if main_window else self
        
        if msg_type == "success":
            InfoBar.success(title, content, orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
        elif msg_type == "warning":
            InfoBar.warning(title, content, orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
        elif msg_type == "error":
            InfoBar.error(title, content, orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
        else:
            InfoBar.info(title, content, orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent) 