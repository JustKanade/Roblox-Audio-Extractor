#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import (PrimaryPushButton, FluentIcon)

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


class ManualCheckUpdateCard(BaseUpdateCard):
    """手动检查更新设置卡片"""
    
    def __init__(self, config_manager, current_version, parent=None):
        self.config_manager = config_manager
        self.current_version = current_version
        
        # 获取翻译文本
        title = get_text("manual_check_settings") or "Manual Check Update"
        base_description = get_text("check_update_manually_desc") or "Manually check for application updates"
        # 在描述后添加当前版本号
        description = f"{base_description} (Current: v{current_version})"
        
        super().__init__(
            FluentIcon.SYNC,
            title,
            description,
            parent
        )
        
        self._setupContent()
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器 - 水平布局
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(12)
        
        # 手动检查按钮
        self.check_button = PrimaryPushButton(get_text("check_update_now"))
        self.check_button.setFixedSize(120, 32)
        self.check_button.clicked.connect(self._check_for_updates)
        
        content_layout.addStretch()  # 添加伸缩空间，让按钮靠右
        content_layout.addWidget(self.check_button)
        
        self.hBoxLayout.addWidget(content_widget)
    
    def _check_for_updates(self):
        """检查更新 - 重写基类方法以添加UI状态管理"""
        self.check_button.setEnabled(False)
        self.check_button.setText(get_text("checking_update"))
        # 调用基类的检查方法
        super()._check_for_updates()
    
    def _on_check_finished(self):
        """检查完成 - 重写基类方法以恢复UI状态"""
        self.check_button.setEnabled(True)
        self.check_button.setText(get_text("check_update_now")) 