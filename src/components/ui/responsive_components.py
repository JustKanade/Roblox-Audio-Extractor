#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
响应式UI组件
提供自适应不同屏幕尺寸的UI组件
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt
from qfluentwidgets import IconWidget, CaptionLabel


class ResponsiveFeatureItem(QWidget):
    """响应式功能特色项目组件
    
    一个自适应不同屏幕尺寸的功能特色展示组件，
    包含图标和文本说明，可以根据窗口大小自动调整布局。
    
    Args:
        icon: FluentIcon图标
        text: 显示的文本
        parent: 父组件
    """

    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.icon = icon
        self.text = text
        self.setupUI()

    def setupUI(self):
        """设置UI"""
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumSize(140, 80)
        self.setMaximumSize(220, 80)

        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 图标
        self.icon_widget = IconWidget(self.icon)
        self.icon_widget.setFixedSize(30, 30)

        # 文本
        self.text_label = CaptionLabel(self.text)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setWordWrap(True)

        # 添加到布局
        layout.addWidget(self.icon_widget, 0, Qt.AlignCenter)
        layout.addWidget(self.text_label)
        
    def updateSize(self, min_width, min_height, max_width, max_height):
        """更新组件大小
        
        根据窗口大小动态调整组件尺寸
        
        Args:
            min_width: 最小宽度
            min_height: 最小高度
            max_width: 最大宽度
            max_height: 最大高度
        """
        self.setMinimumSize(min_width, min_height)
        self.setMaximumSize(max_width, max_height) 