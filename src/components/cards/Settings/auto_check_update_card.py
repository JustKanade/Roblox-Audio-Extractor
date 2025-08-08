#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import (
    SwitchButton, FluentIcon
)

# 导入更新工具
from src.utils.update_utils import BaseUpdateCard, set_language_manager as set_utils_lang

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None

def set_language_manager(language_manager):
    """设置语言管理器"""
    global lang
    lang = language_manager
    # 同时设置工具模块的语言管理器
    set_utils_lang(language_manager)

def get_text(key: str, *args) -> str:
    """获取翻译文本的便利函数"""
    if lang and hasattr(lang, 'get'):
        return lang.get(key, *args)
    return key


class AutoCheckUpdateCard(BaseUpdateCard):
    """自动检查更新设置卡片"""
    
    def __init__(self, config_manager, current_version, parent=None):
        self.config_manager = config_manager
        self.current_version = current_version
        
        # 从配置中读取设置 - 统一使用autoCheckUpdate
        self.auto_check = self.config_manager.get("autoCheckUpdate", True)
        
        # 获取翻译文本
        title = get_text("auto_check_settings") or "Auto Check Update Settings"
        description = get_text("auto_check_update") or "Auto-check for updates on startup"
        
        super().__init__(
            FluentIcon.UPDATE,
            title,
            description,
            parent
        )
        
        self._setupContent()
        
        # 如果设置了自动检查，则启动时检查更新
        if self.auto_check:
            QTimer.singleShot(1000, self._trigger_auto_check)
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器 - 水平布局
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(12)
        
        # 自动检查开关
        self.auto_check_switch = SwitchButton()
        self.auto_check_switch.setChecked(self.auto_check)
        self.auto_check_switch.checkedChanged.connect(self._on_auto_check_changed)
        
        content_layout.addStretch()  # 添加伸缩空间，让开关靠右
        content_layout.addWidget(self.auto_check_switch)
        
        self.hBoxLayout.addWidget(content_widget)
    
    def _on_auto_check_changed(self, checked: bool):
        """自动检查设置改变"""
        self.auto_check = checked
        self.config_manager.set("autoCheckUpdate", checked)
    
    def _trigger_auto_check(self):
        """触发自动检查更新"""
        try:
            # 直接调用基类的更新检查方法
            self._check_for_updates()
        except Exception as e:
            # 如果检查更新时发生错误，记录但不中断程序
            print(f"自动检查更新时出错: {e}")
            # 可以考虑在这里添加日志记录
            pass 