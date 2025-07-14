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

try:
    from qfluentwidgets import (
        CardWidget, SwitchButton, FluentIcon, InfoBar,
        InfoBarPosition, StrongBodyLabel, BodyLabel, IconWidget,
        PrimaryPushButton
    )
    HAS_FLUENT_WIDGETS = True
except ImportError:
    print("无法导入qfluentwidgets组件，将使用基本的控件替代")
    from PyQt5.QtWidgets import QLabel, QFrame, QCheckBox, QPushButton
    HAS_FLUENT_WIDGETS = False
    
    # 创建替代类
    class CardWidget(QFrame):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; padding: 8px;")
    
    class SwitchButton(QCheckBox):
        checkedChanged = pyqtSignal(bool)
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.toggled.connect(self.checkedChanged)
            
        def setChecked(self, checked):
            super().setChecked(checked)
            
        def isChecked(self):
            return super().isChecked()
    
    class FluentIcon:
        COMMAND_PROMPT = None
    
    class InfoBar:
        @staticmethod
        def success(title, content, orient=1, isClosable=True, position=None, duration=3000, parent=None):
            pass
        
        @staticmethod
        def warning(title, content, orient=1, isClosable=True, position=None, duration=3000, parent=None):
            pass
        
        @staticmethod
        def error(title, content, orient=1, isClosable=True, position=None, duration=3000, parent=None):
            pass
        
        @staticmethod
        def info(title, content, orient=1, isClosable=True, position=None, duration=3000, parent=None):
            pass
    
    class InfoBarPosition:
        TOP = None
    
    class StrongBodyLabel(QLabel):
        def __init__(self, text, parent=None):
            super().__init__(text, parent)
            self.setStyleSheet("font-weight: bold; font-size: 14px;")
            
    class BodyLabel(QLabel):
        def __init__(self, text, parent=None):
            super().__init__(text, parent)
    
    class IconWidget(QWidget):
        def __init__(self, icon, parent=None):
            super().__init__(parent)
            self.setFixedSize(16, 16)
            
    class PrimaryPushButton(QPushButton):
        def __init__(self, text, parent=None):
            super().__init__(text, parent)


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
        title_label = StrongBodyLabel(self.lang.get("debug_mode") if self.lang else "Debug模式")
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # Debug模式选项
        debug_mode_row = QHBoxLayout()
        
        debug_mode_label = BodyLabel(self.lang.get("debug_mode_description") if self.lang else "在程序崩溃时生成错误日志")
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
        
        open_logs_button = PrimaryPushButton(self.lang.get("open_error_logs_folder") if self.lang else "打开错误日志文件夹")
        open_logs_button.clicked.connect(self.open_error_logs_folder)
        
        button_row.addStretch()
        button_row.addWidget(open_logs_button)
        
        main_layout.addLayout(button_row)
    
    def on_debug_mode_changed(self, is_checked):
        """Debug模式设置改变的响应函数"""
        self.debug_mode_enabled = is_checked
        if self.config_manager:
            self.config_manager.set("debug_mode_enabled", is_checked)
            
        # 显示提示消息
        self.showMessage(
            "success" if is_checked else "info",
            self.lang.get("debug_mode_enabled" if is_checked else "debug_mode_disabled") if self.lang else "Debug模式已启用" if is_checked else "Debug模式已禁用",
            self.lang.get("debug_mode_enabled_tip" if is_checked else "debug_mode_disabled_tip") if self.lang else 
            "程序将在崩溃时生成详细的错误日志" if is_checked else "程序崩溃时不会生成错误日志"
        )
    
    def open_error_logs_folder(self):
        """打开错误日志文件夹"""
        try:
            # 获取日志文件夹路径
            custom_output_dir = self.config_manager.get("custom_output_dir", "") if self.config_manager else ""
            if custom_output_dir and os.path.isdir(custom_output_dir):
                # 使用自定义路径
                crash_log_dir = os.path.join(custom_output_dir, "logs", "crash_logs")
            else:
                # 使用默认路径
                crash_log_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor", "logs", "crash_logs")
            
            # 确保目录存在
            os.makedirs(crash_log_dir, exist_ok=True)
            
            # 根据操作系统打开文件夹
            if sys.platform == 'win32':
                os.startfile(crash_log_dir)
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', crash_log_dir])
            else:  # Linux
                subprocess.Popen(['xdg-open', crash_log_dir])
                
            # 显示成功消息
            self.showMessage(
                "success",
                self.lang.get("open_folder_success") if self.lang else "打开文件夹成功",
                self.lang.get("error_logs_folder_opened") if self.lang else "已打开错误日志文件夹"
            )
        except Exception as e:
            # 显示错误消息
            self.showMessage(
                "error",
                self.lang.get("open_folder_failed") if self.lang else "打开文件夹失败",
                self.lang.get("error_opening_folder", str(e)) if self.lang else f"打开文件夹时出错: {str(e)}"
            )
    
    def showMessage(self, msg_type, title, content):
        """显示消息通知
        
        Args:
            msg_type: 消息类型 (success, warning, error, info)
            title: 标题
            content: 内容
        """
        # 创建orient参数，避免直接使用Qt.Horizontal
        orient = 1  # Qt.Horizontal的值是1
        
        # 获取主窗口作为父控件，确保消息显示在最上方
        main_window = self.window()
        parent = main_window if main_window else self
        
        if msg_type == "success":
            InfoBar.success(title, content, orient=orient, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
        elif msg_type == "warning":
            InfoBar.warning(title, content, orient=orient, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
        elif msg_type == "error":
            InfoBar.error(title, content, orient=orient, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
        else:
            InfoBar.info(title, content, orient=orient, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent) 