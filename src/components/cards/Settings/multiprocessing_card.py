from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from qfluentwidgets import (
    SwitchSettingCard, SettingCard, BodyLabel, 
    FluentIcon, setFont, ComboBox, MessageBox
)

import multiprocessing

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None



class MultiprocessingCard(SwitchSettingCard):
    """多进程设置卡片 - 启用/禁用多进程"""
    
    valueChanged = pyqtSignal(bool)
    
    def __init__(self, config_manager, lang=None, parent=None):
        self.config_manager = config_manager
        self.lang = lang
        
        # 获取翻译文本
        title = self._get_text("use_multiprocessing")
        content = self._get_text("multiprocessing_description")
        
        # 从配置中获取当前值（默认值改为False）
        current_value = self.config_manager.get("useMultiprocessing", False) if self.config_manager else False
        
        super().__init__(
            FluentIcon.SPEED_HIGH,
            title,
            content,
            parent
        )
        
        # 设置当前值
        self.setChecked(current_value)
        
        # 连接事件处理
        self.checkedChanged.connect(self._onValueChanged)
    
    def _get_text(self, key):
        """获取翻译文本"""
        if self.lang and hasattr(self.lang, 'get'):
            return self.lang.get(key, key)
        
        # 如果没有lang对象，返回默认翻译
        translations = {
            "use_multiprocessing": "Use Multiprocessing",
            "multiprocessing_description": "Enable multiprocessing for faster audio extraction",
            "multiprocessing_warning_title": "Multiprocessing Warning",
            "multiprocessing_warning_message": "Multiprocessing may consume more system resources. Continue?",
            "enable_multiprocessing": "Enable",
            "cancel_multiprocessing": "Cancel"
        }

        return translations.get(key, key)
    
    def _onValueChanged(self, checked):
        """处理值变化"""
        if checked:
            # 用户尝试启用多进程，显示警告对话框
            self._showMultiprocessingWarning()
        else:
            # 用户禁用多进程，直接应用
            self._applyMultiprocessingSetting(False)
    
    def _showMultiprocessingWarning(self):
        """显示多进程警告对话框"""
        title = self._get_text("multiprocessing_warning_title")
        message = self._get_text("multiprocessing_warning_message")
        
        w = MessageBox(title, message, self.window())
        w.yesButton.setText(self._get_text("enable_multiprocessing"))
        w.cancelButton.setText(self._get_text("cancel_multiprocessing"))
        
        if w.exec():
            # 用户确认启用
            self._applyMultiprocessingSetting(True)
        else:
            # 用户取消，恢复开关状态
            self.checkedChanged.disconnect()
            self.setChecked(False)
            self.checkedChanged.connect(self._onValueChanged)
    
    def _applyMultiprocessingSetting(self, enabled):
        """应用多进程设置"""
        if self.config_manager:
            self.config_manager.set("useMultiprocessing", enabled)
        
        # 发出值变化信号
        self.valueChanged.emit(enabled)
        
        # 显示状态消息（可选）
        # status_message = self._get_text("multiprocessing_enabled" if enabled else "multiprocessing_disabled")
        # print(status_message)  # 或者使用其他通知方式


class MultiprocessingStrategyCard(SettingCard):
    """多进程策略设置卡片 - 选择保守或激进策略"""
    
    valueChanged = pyqtSignal(bool)
    
    def __init__(self, config_manager, lang=None, parent=None):
        self.config_manager = config_manager
        self.lang = lang
        
        # 获取翻译文本
        title = self._get_text("multiprocessing_strategy")
        content = self._get_text("multiprocessing_strategy_description")
        
        super().__init__(
            FluentIcon.SETTING,
            title,
            content,
            parent
        )
        
        self._setupContent()
    
    def _get_text(self, key):
        """获取翻译文本"""
        if self.lang and hasattr(self.lang, 'get'):
            return self.lang.get(key, key)
        
        # 如果没有lang对象，返回默认翻译
        translations = {
            "multiprocessing_strategy": "Multiprocessing Strategy",
            "multiprocessing_strategy_description": "Choose between conservative or aggressive multiprocessing",
            "conservative_strategy": "Conservative",
            "aggressive_strategy": "Aggressive",
            "processes": " processes"
        }

        return translations.get(key, key)
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 策略选择下拉框
        self.strategy_combo = ComboBox()
        
        # 添加选项
        cpu_count = multiprocessing.cpu_count()
        conservative_count = cpu_count + 1 if cpu_count <= 4 else cpu_count
        aggressive_count = min(32, cpu_count * 2)
        
        self.strategy_combo.addItem(
            f"{self._get_text('conservative_strategy')} ({conservative_count}{self._get_text('processes')})"
        )
        self.strategy_combo.addItem(
            f"{self._get_text('aggressive_strategy')} ({aggressive_count}{self._get_text('processes')})"
        )
        
        # 从配置中获取当前值
        current_conservative = self.config_manager.get("conservativeMultiprocessing", True) if self.config_manager else True
        self.strategy_combo.setCurrentIndex(0 if current_conservative else 1)
        
        self.strategy_combo.currentIndexChanged.connect(self._onValueChanged)
        self.strategy_combo.setFixedWidth(280)
        
        content_layout.addStretch()  # 添加伸缩空间，让下拉框靠右
        content_layout.addWidget(self.strategy_combo)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)
    
    def _onValueChanged(self, index):
        """处理值变化"""
        conservative = (index == 0)
        if self.config_manager:
            self.config_manager.set("conservativeMultiprocessing", conservative)
        self.valueChanged.emit(conservative)
    
    def setConservative(self, conservative):
        """设置策略"""
        if hasattr(self, 'strategy_combo'):
            self.strategy_combo.setCurrentIndex(0 if conservative else 1)
    
    def isConservative(self):
        """获取当前是否为保守策略"""
        if hasattr(self, 'strategy_combo'):
            return self.strategy_combo.currentIndex() == 0
        return True 