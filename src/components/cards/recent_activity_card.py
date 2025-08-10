#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最近活动日志卡片组件 - 统一的日志显示卡片（支持可调整高度）
Recent Activity Card Component - Unified log display card (with resizable height)
"""

from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QCursor, QPainter, QPen, QColor

from qfluentwidgets import CardWidget, StrongBodyLabel, TextEdit, FluentIcon, IconWidget

from src.utils.log_utils import LogHandler


class ResizeHandle(QFrame):
    """可拖拽的调整手柄"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 增大手柄整体高度
        self.setFixedHeight(24)
        self.setCursor(QCursor(Qt.SizeVerCursor))
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        # 创建拖拽指示器布局
        layout = QHBoxLayout(self)
        # 增大上下边距以增大图标区域
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(0)
        
        # 添加伸缩项使指示器居中
        layout.addStretch()
        
        # 创建调整大小图标 - 使用可用的图标
        try:
            # 尝试使用展开收起图标
            self.resize_icon = IconWidget(FluentIcon.MORE, self)
            # 增大图标高度
            self.resize_icon.setFixedSize(20, 20)
            layout.addWidget(self.resize_icon)
        except:
            # 如果没有合适的图标，就不显示图标，只显示拖拽区域
            pass
        
        layout.addStretch()
        
        self.dragging = False
        self.start_pos = QPoint()
        self.start_height = 0
    

    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.start_pos = event.globalPos()
            self.start_height = self.parent().height()
            self.setCursor(QCursor(Qt.SizeVerCursor))
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            delta_y = event.globalPos().y() - self.start_pos.y()
            new_height = self.start_height + delta_y
            
            # 限制高度范围
            min_height = 150  # 最小高度
            max_height = 600  # 最大高度
            new_height = max(min_height, min(max_height, new_height))
            
            # 调整父组件高度
            self.parent().setFixedHeight(new_height)
            self.parent().updateTextEditHeight()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(QCursor(Qt.SizeVerCursor))
            # 保存高度设置
            self.parent().saveHeightSettings()


class RecentActivityCard(CardWidget):
    """
    最近活动日志卡片 - 统一的日志显示组件（支持可调整高度）
    Recent Activity Card - Unified log display component (with resizable height)
    """
    
    heightChanged = pyqtSignal(int)  # 高度改变信号
    
    def __init__(self, parent=None, lang=None, config_manager=None):
        """
        初始化最近活动日志卡片
        
        Args:
            parent: 父控件
            lang: 语言管理器
            config_manager: 配置管理器（用于保存高度设置）
        """
        super().__init__(parent)
        self.lang = lang
        self.config_manager = config_manager
        
        # 从配置中读取保存的高度，默认250px
        self.default_height = 250
        self.current_height = self.config_manager.get("log_card_height", self.default_height) if config_manager else self.default_height
        
        # 设置卡片属性
        self.setFixedHeight(self.current_height)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # 初始化UI
        self._setupUI()
        
        # 创建日志处理器
        self.log_handler = LogHandler(self.log_text_edit)
    
    def _setupUI(self):
        """设置UI布局"""
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 15, 20, 0)  # 底部margin设为0，为拖拽手柄留空间
        self.main_layout.setSpacing(10)
        
        # 标题
        title_text = "最近活动"
        if self.lang and hasattr(self.lang, 'get'):
            title_text = self.lang.get("recent_activity", "最近活动")
        
        self.title_label = StrongBodyLabel(title_text)
        self.main_layout.addWidget(self.title_label)
        
        # 日志文本编辑器
        self.log_text_edit = TextEdit()
        self.log_text_edit.setReadOnly(True)
        self.main_layout.addWidget(self.log_text_edit, 1)  # 设置拉伸因子为1
        
        # 添加可拖拽的调整手柄
        self.resize_handle = ResizeHandle(self)
        self.main_layout.addWidget(self.resize_handle)
        
        # 初始化TextEdit高度
        self.updateTextEditHeight()
    
    def updateTextEditHeight(self):
        """根据卡片总高度更新TextEdit的高度"""
        # 计算TextEdit应有的高度
        # 总高度 - 上边距(15) - 标题高度(约30) - 间距(10) - 拖拽手柄高度(8) - 底部间距(5)
        text_edit_height = self.height() - 15 - 30 - 10 - 8 - 5
        text_edit_height = max(50, text_edit_height)  # 最小高度50px
        
        # 不使用固定高度，让它根据布局自动调整
        self.log_text_edit.setMinimumHeight(text_edit_height)
        self.log_text_edit.setMaximumHeight(text_edit_height)
    
    def saveHeightSettings(self):
        """保存高度设置到配置文件"""
        if self.config_manager:
            self.config_manager.set("log_card_height", self.height())
            self.config_manager.save_config()
        
        # 发出高度改变信号
        self.heightChanged.emit(self.height())
    
    def resetHeight(self):
        """重置为默认高度"""
        self.setFixedHeight(self.default_height)
        self.updateTextEditHeight()
        self.saveHeightSettings()
    
    def setHeight(self, height):
        """设置指定高度"""
        height = max(150, min(600, height))  # 限制范围
        self.setFixedHeight(height)
        self.updateTextEditHeight()
        self.saveHeightSettings()
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.updateTextEditHeight()
    
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