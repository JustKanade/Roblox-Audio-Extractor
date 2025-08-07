#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志控制卡片组件 - 提供导出和清空日志功能
Log Control Card Component - Provides export and clear log functions
"""

import os
from datetime import datetime
import traceback
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFileDialog, QWidget
)
from PyQt5.QtCore import Qt

from qfluentwidgets import (
    SettingCard, PushButton, FluentIcon, MessageBox,
    InfoBar, InfoBarPosition
)
    
class LogControlCard(SettingCard):
    """日志控制卡片，提供导出和清空日志功能"""
    
    def __init__(self, parent=None, lang=None, central_log_handler=None):
        """
        初始化日志控制卡片
        
        Args:
            parent: 父控件
            lang: 语言管理器
            central_log_handler: 中央日志处理器实例
        """
        self.lang = lang
        self.central_log_handler = central_log_handler
        
        # 获取翻译文本
        title = self.lang.get("log_management") if self.lang else "Log Management"
        description = self.lang.get("log_management_description") if self.lang else "Export logs to file or clear all log entries"
        
        super().__init__(
            FluentIcon.SAVE,
            title,
            description,
            parent
        )
        
        self._setupButtons()
    
    def _setupButtons(self):
        """设置按钮"""
        # 创建按钮容器
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 20, 0)  # 设置右边距为20px
        button_layout.setSpacing(8)
        
        # 导出日志按钮
        self.export_btn = PushButton(FluentIcon.SAVE, self.lang.get("export_logs") if self.lang else "Export Logs")
        self.export_btn.setFixedHeight(32)
        self.export_btn.setMinimumWidth(120)  # 确保按钮有足够宽度显示文字
        self.export_btn.clicked.connect(self.exportLogs)
        
        # 清空日志按钮
        self.clear_btn = PushButton(FluentIcon.DELETE, self.lang.get("clear_logs") if self.lang else "Clear Logs")
        self.clear_btn.setFixedHeight(32)
        self.clear_btn.setMinimumWidth(120)  # 确保按钮有足够宽度显示文字
        self.clear_btn.clicked.connect(self.confirmClearLogs)
        
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.clear_btn)
        
        # 将按钮添加到SettingCard的hBoxLayout中
        self.hBoxLayout.addWidget(button_widget)
    
    def exportLogs(self):
        """导出日志到文件"""
        if not self.central_log_handler or not hasattr(self.central_log_handler, '_log_entries') or not self.central_log_handler._log_entries:
            self.showMessage("warning", self.lang.get("export_failed") if self.lang else "Export Failed", 
                            self.lang.get("error_exporting_logs", "No logs to export") if self.lang else "No logs to export")
            return
        
        # 获取主窗口作为父控件
        main_window = self.window()
        parent = main_window if main_window else self
        
        # 打开文件对话框
        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            self.lang.get("save_log_file") if self.lang else "Save Log File",
            os.path.join(os.path.expanduser("~"), "roblox_audio_extractor_logs.txt"),
            "Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return  # 用户取消了操作
        
        try:
            # 将日志写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                for entry in self.central_log_handler._log_entries:
                    f.write(f"{entry}\n")
                    
            # 显示成功消息
            self.showMessage(
                "success",
                self.lang.get("export_successful") if self.lang else "Export Successful",
                self.lang.get("logs_exported_to", file_path) if self.lang else f"Logs exported to: {file_path}"
            )
        except Exception as e:
            # 显示错误消息
            self.showMessage(
                "error",
                self.lang.get("export_failed") if self.lang else "Export Failed",
                self.lang.get("error_exporting_logs", str(e)) if self.lang else f"Error exporting logs: {str(e)}"
            )
    
    def confirmClearLogs(self):
        """显示确认对话框，确认是否清空日志"""
        if not self.central_log_handler:
            self.showMessage("error", "Error", "Central log handler not available")
            return
            
        # 获取主窗口作为父控件，确保对话框正确显示
        main_window = self.window()
        parent = main_window if main_window else self
        
        # 创建确认对话框
        title = self.lang.get("confirm_clear_logs") if self.lang else "Clear Logs"
        content = self.lang.get("confirm_clear_logs_message") if self.lang else "Are you sure you want to clear all logs? This operation cannot be undone."
        
        # 显示确认对话框
        confirm_box = MessageBox(title, content, parent)
        if confirm_box.exec():
            self.clearLogs()
    
    def clearLogs(self):
        """清空所有日志"""
        if not self.central_log_handler:
            self.showMessage("error", self.lang.get("clear_failed") if self.lang else "Clear Failed", 
                            self.lang.get("error_clearing_logs", "Central log handler not available") if self.lang else "Central log handler not available")
            return
        
        try:
            # 检查是否有clear_logs方法
            if hasattr(self.central_log_handler, 'clear_logs'):
                self.central_log_handler.clear_logs()
            elif hasattr(self.central_log_handler, '_log_entries'):
                # 手动清空日志
                self.central_log_handler._log_entries.clear()
                # 清空所有文本编辑控件
                if hasattr(self.central_log_handler, '_text_edits'):
                    for text_edit in self.central_log_handler._text_edits:
                        if text_edit:
                            text_edit.clear()
            else:
                self.showMessage("error", self.lang.get("clear_failed") if self.lang else "Clear Failed", 
                               self.lang.get("error_clearing_logs", "Cannot clear logs") if self.lang else "Cannot clear logs")
                return
            
            # 显示成功消息
            self.showMessage("success", 
                           self.lang.get("clear_successful") if self.lang else "Clear Successful", 
                           self.lang.get("logs_cleared") if self.lang else "All logs have been cleared")
        except Exception as e:
            # 显示错误消息
            self.showMessage("error", 
                           self.lang.get("clear_failed") if self.lang else "Clear Failed", 
                           self.lang.get("error_clearing_logs", str(e)) if self.lang else f"Error clearing logs: {str(e)}")
    
    def showMessage(self, msg_type, title, content):
        """显示消息通知
        
        Args:
            msg_type: 消息类型 (success, warning, error)
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