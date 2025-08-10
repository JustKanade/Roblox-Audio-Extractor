#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最近活动日志卡片组件 - 统一的日志显示卡片
Recent Activity Card Component - Unified log display card
"""

from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt

from qfluentwidgets import CardWidget, StrongBodyLabel, TextEdit

from src.utils.log_utils import LogHandler


class RecentActivityCard(CardWidget):
    """
    最近活动日志卡片 - 统一的日志显示组件
    Recent Activity Card - Unified log display component
    """
    
    def __init__(self, parent=None, lang=None):
        """
        初始化最近活动日志卡片
        
        Args:
            parent: 父控件
            lang: 语言管理器
        """
        super().__init__(parent)
        self.lang = lang
        
        # 设置卡片属性
        self.setFixedHeight(250)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        
        # 初始化UI
        self._setupUI()
        
        # 创建日志处理器
        self.log_handler = LogHandler(self.log_text_edit)
    
    def _setupUI(self):
        """设置UI布局"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        # 标题
        title_text = "最近活动"
        if self.lang and hasattr(self.lang, 'get'):
            title_text = self.lang.get("recent_activity", "最近活动")
        
        self.title_label = StrongBodyLabel(title_text)
        layout.addWidget(self.title_label)
        
        # 日志文本编辑器
        self.log_text_edit = TextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFixedHeight(180)  # 250-15-15-10-30(标题高度) ≈ 180
        layout.addWidget(self.log_text_edit)
    
    def get_log_handler(self):
        """
        获取日志处理器实例
        
        Returns:
            LogHandler: 日志处理器实例
        """
        return self.log_handler
    
    def get_text_edit(self):
        """
        获取TextEdit组件实例（用于向后兼容）
        
        Returns:
            TextEdit: TextEdit组件实例
        """
        return self.log_text_edit 