#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QTimer
from qfluentwidgets import SwitchSettingCard, FluentIcon, ConfigItem, BoolValidator

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None

def set_language_manager(language_manager):
    """设置语言管理器"""
    global lang
    lang = language_manager

def get_text(key: str, *args) -> str:
    """获取翻译文本的便利函数"""
    if lang and hasattr(lang, 'get'):
        return lang.get(key, *args)
    return key


class AutoCheckUpdateCard(SwitchSettingCard):
    """自动检查更新设置卡片"""
    
    def __init__(self, config_manager, current_version, parent=None):
        self.config_manager = config_manager
        self.current_version = current_version
        
        # 从配置中读取设置 - 统一使用autoCheckUpdate
        self.auto_check = self.config_manager.get("autoCheckUpdate", True)
        
        # 获取翻译文本
        title = get_text("auto_check_settings") or "Auto Check Update Settings"
        description = get_text("auto_check_update") or "Auto-check for updates on startup"
        
        # 直接使用配置管理器的配置项，避免创建重复的ConfigItem
        super().__init__(
            FluentIcon.UPDATE,
            title,
            description,
            config_manager.cfg.autoCheckUpdate,
            parent
        )
        
        # 设置初始状态
        self.setChecked(self.auto_check)
        
        # 连接信号
        self.checkedChanged.connect(self._on_auto_check_changed)
        
        # 如果设置了自动检查，则启动时检查更新
        if self.auto_check:
            QTimer.singleShot(1000, self._trigger_auto_check)
    
    def _on_auto_check_changed(self, checked: bool):
        """自动检查设置改变"""
        self.auto_check = checked
        self.config_manager.set("autoCheckUpdate", checked)
    
    def _trigger_auto_check(self):
        """触发自动检查更新"""
        # 改进的父窗口查找逻辑，寻找手动检查卡片
        try:
            # 从当前卡片开始，向上遍历寻找设置界面
            parent_widget = self.parent()
            while parent_widget:
                # 检查是否是设置界面，并且有手动检查卡片
                if hasattr(parent_widget, 'manualCheckUpdateCard') and parent_widget.manualCheckUpdateCard:
                    # 调用正确的方法名
                    parent_widget.manualCheckUpdateCard._check_for_updates()
                    break
                # 继续向上查找
                parent_widget = parent_widget.parent()
                
        except Exception as e:
            # 如果找不到手动检查卡片或发生任何错误，记录但不中断程序
            print(f"自动检查更新时出错: {e}")
            # 可以考虑在这里添加日志记录
            pass 