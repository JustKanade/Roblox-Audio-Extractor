#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt

from qfluentwidgets import (
    CardWidget, BodyLabel, SubtitleLabel, 
    ScrollArea
)


class ExtractImagesInterface(QWidget):
    """图像提取界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None):
        super().__init__(parent)
        self.setObjectName("extractImagesInterface")
        self.config_manager = config_manager
        self.lang = lang
        
        # 确保语言对象存在，否则创建空的语言处理函数
        if self.lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = self.lang.get
        
        # 初始化界面
        self.initUI()
        
    def initUI(self):
        """初始化界面"""
        # 创建滚动区域
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # 添加占位内容
        placeholder = CardWidget()
        placeholder_layout = QVBoxLayout(placeholder)
        placeholder_layout.setContentsMargins(20, 20, 20, 20)
        
        title = SubtitleLabel(self.get_text("extract_images", "提取图像"))
        title.setObjectName("extractImagesTitle")
        placeholder_layout.addWidget(title)
        
        desc = BodyLabel(self.get_text("extract_images_placeholder", "这是提取图像的功能界面占位符，将在后续版本中实现。"))
        desc.setWordWrap(True)
        placeholder_layout.addWidget(desc)
        
        content_layout.addWidget(placeholder)
        
        # 添加伸缩空间，确保内容顶部对齐
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        
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