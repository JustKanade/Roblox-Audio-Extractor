#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JustKanade Avatar Setting Card - 头像设置卡片
"""

from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import CardWidget, StrongBodyLabel, BodyLabel, SwitchButton, FluentIcon, IconWidget

# 全局语言管理器变量
lang = None

# 定义AvatarSettingChangedEvent，与avatar_widget.py中保持一致
AVATAR_SETTING_CHANGED_EVENT_TYPE = QEvent.Type(1001)  # 使用一个固定值，避免冲突

# 自定义事件类，用于传递设置更改
class AvatarSettingChangedEvent(QEvent):
    """头像设置更改事件"""
    
    def __init__(self, disable_update):
        """初始化事件
        
        Args:
            disable_update: 是否禁用自动更新
        """
        super().__init__(AVATAR_SETTING_CHANGED_EVENT_TYPE)
        self.disable_update = disable_update


class AvatarSettingCard(CardWidget):
    """头像设置卡片，提供禁用自动更新头像的选项"""

    def __init__(self, config_manager, parent=None):
        """初始化头像设置卡片
        
        Args:
            config_manager: 配置管理器实例
            parent: 父控件
        """
        super().__init__(parent)
        self.config_manager = config_manager
        
        # 从配置中读取设置
        self.disable_auto_update = self.config_manager.get("disable_avatar_auto_update", False)
        
        self.setupUI()
    
    def setupUI(self):
        """设置UI界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # 标题行布局
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # 添加图标
        title_icon = IconWidget(FluentIcon.GLOBE, self)
        title_icon.setFixedSize(16, 16)
        
        # 标题
        title_label = StrongBodyLabel(self._get_text("avatar_settings") or "头像设置")
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # 禁用自动更新选项
        disable_auto_update_row = QHBoxLayout()
        
        disable_auto_update_label = BodyLabel(self._get_text("disable_avatar_auto_update") or "禁用侧边栏头像自动更新")
        self.disable_auto_update_switch = SwitchButton()
        self.disable_auto_update_switch.setChecked(self.disable_auto_update)
        self.disable_auto_update_switch.checkedChanged.connect(self.on_disable_auto_update_changed)
        
        disable_auto_update_row.addWidget(disable_auto_update_label)
        disable_auto_update_row.addStretch()
        disable_auto_update_row.addWidget(self.disable_auto_update_switch)
        
        main_layout.addLayout(disable_auto_update_row)
        
        # 说明文本 - 加快启动速度的提示
        tip_text = self._get_text("avatar_auto_update_tip") or "禁用侧边栏头像自动更新可以加快程序启动速度"
        tip_label = BodyLabel(tip_text)
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet("color: rgba(150, 150, 150, 0.8); font-size: 12px; margin-left: 20px;")
        
        main_layout.addWidget(tip_label)
    
    def on_disable_auto_update_changed(self, is_checked):
        """禁用自动更新设置改变的响应函数"""
        self.disable_auto_update = is_checked
        self.config_manager.set("disable_avatar_auto_update", is_checked)
        
        # 通知所有窗口（包括AvatarWidget）设置已更改
        self._notify_setting_changed(is_checked)
    
    def _notify_setting_changed(self, disable_update):
        """通知头像组件设置已更改"""
        try:
            # 创建自定义事件
            event = AvatarSettingChangedEvent(disable_update)
            
            # 向所有窗口发送事件
            for widget in QApplication.topLevelWidgets():
                QApplication.sendEvent(widget, event)
                
                # 递归向所有子控件发送事件
                self._send_event_recursively(widget, event)
        except Exception as e:
            print(f"通知设置更改时出错: {str(e)}")
    
    def _send_event_recursively(self, widget, event):
        """递归向所有子控件发送事件"""
        if not widget:
            return
            
        # 向子控件发送事件
        for child in widget.children():
            if isinstance(child, QWidget):
                QApplication.sendEvent(child, event)
                self._send_event_recursively(child, event)
    
    def _get_text(self, key):
        """获取翻译文本"""
        if lang is None:
            return None
        return lang.get(key)


# 修复缺失的 QApplication 导入
from PyQt5.QtWidgets import QApplication 