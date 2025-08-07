from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets import (
    SettingCard, SpinBox, BodyLabel, 
    FluentIcon, setFont
)

import multiprocessing

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None


class ThreadCountCard(SettingCard):
    """线程数设置卡片 - 使用SpinBox选择器"""
    
    valueChanged = pyqtSignal(int)
    
    def __init__(self, config_manager, parent=None):
        self.config_manager = config_manager
        
        # 获取翻译文本
        title = self._get_text("default_threads") or "Default thread count"
        content = self._get_text("threads_description") or "Set the default number of threads for extraction tasks"
        
        super().__init__(
            FluentIcon.SPEED_OFF,
            title,
            content,
            parent
        )
        
        self._setupContent()
    
    def _get_text(self, key):
        """获取翻译文本"""
        if lang is None:
            return ""
        return lang.get(key)
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器 - 水平布局
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)  # 添加右边距避免超出边框
        content_layout.setSpacing(8)
        
        # 线程数SpinBox
        self.threadSpinBox = SpinBox()
        self.threadSpinBox.setRange(1, 128)  # 设置范围从1到128
        
        # 设置默认值为CPU核心数的2倍，但不超过32
        default_threads = min(32, multiprocessing.cpu_count() * 2)
        saved_threads = self.config_manager.get("threads", default_threads) if self.config_manager else default_threads
        self.threadSpinBox.setValue(saved_threads)
        
        self.threadSpinBox.setFixedWidth(120)  # 固定宽度，与音频提取界面保持一致
        self.threadSpinBox.valueChanged.connect(self._onValueChanged)
        

        
        content_layout.addWidget(self.threadSpinBox)

        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)
    
    def _onValueChanged(self, value):
        """处理值变化"""
        if self.config_manager:
            self.config_manager.set("threads", value)
        self.valueChanged.emit(value)
    
    def setValue(self, value):
        """设置值"""
        if hasattr(self, 'threadSpinBox'):
            self.threadSpinBox.setValue(value)
    
    def getValue(self):
        """获取当前值"""
        if hasattr(self, 'threadSpinBox'):
            return self.threadSpinBox.value()
        return 1 