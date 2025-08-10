#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import (
    SwitchSettingCard, FluentIcon, InfoBar, InfoBarPosition
)

# 导入更新工具
from src.utils.update_utils import UpdateWorker, UpdateDialog, get_text as utils_get_text

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
        return lang.get(key, key)
    return key


class AutoCheckUpdateCard(SwitchSettingCard):
    """自动检查更新设置卡片"""
    
    def __init__(self, config_manager, current_version, parent=None):
        self.config_manager = config_manager
        self.current_version = current_version
        self.update_worker = None
        
        # 从配置中读取设置 - 统一使用autoCheckUpdate
        auto_check = self.config_manager.get("autoCheckUpdate", True)
        
        # 获取翻译文本
        title = get_text("auto_check_settings") or "Auto Check Update Settings"
        description = get_text("auto_check_update") or "Auto-check for updates on startup"
        
        super().__init__(
            FluentIcon.UPDATE,
            title,
            description,
            parent
        )
        
        # 设置当前值
        self.setChecked(auto_check)
        
        # 连接事件处理
        self.checkedChanged.connect(self._on_auto_check_changed)
        
        # 如果设置了自动检查，则启动时检查更新
        if auto_check:
            QTimer.singleShot(1000, self._trigger_auto_check)
    
    def _on_auto_check_changed(self, checked: bool):
        """自动检查设置改变"""
        self.config_manager.set("autoCheckUpdate", checked)
    
    def _trigger_auto_check(self):
        """触发自动检查更新"""
        if self.isChecked():
            self._check_for_updates()
    
    def _check_for_updates(self):
        """执行更新检查"""
        if not hasattr(self, 'current_version') or not self.current_version:
            self._on_error(utils_get_text("version_not_available") or "Version not available")
            return
            
        # 启动更新检查线程
        self.update_worker = UpdateWorker(self.current_version)
        self.update_worker.update_found.connect(self._on_update_found)
        self.update_worker.no_update.connect(self._on_no_update)
        self.update_worker.error_occurred.connect(self._on_error)
        self.update_worker.finished.connect(self._on_check_finished)
        self.update_worker.start()
    
    def _on_update_found(self, release_info: dict):
        """发现更新"""
        InfoBar.success(
            title=utils_get_text("update_available") or "Update Available",
            content=f"v{release_info['tag_name'].lstrip('v')}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )
        
        # 显示更新对话框
        dialog = UpdateDialog(release_info, self.window())
        dialog.show()
    
    def _on_no_update(self, current_version: str):
        """已是最新版本"""
        InfoBar.success(
            title=utils_get_text("already_latest") or "Already Latest Version",
            content=f"v{current_version}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )
    
    def _on_error(self, error_message: str):
        """检查失败"""
        # 使用格式化的错误标题
        title = utils_get_text("check_failed", error_message) or f"Check Failed: {error_message}"
        InfoBar.error(
            title=title[:50] + "..." if len(title) > 50 else title,  # 限制标题长度
            content=error_message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=5000,
            parent=self.window()
        )
    
    def _on_check_finished(self):
        """检查完成"""
        # 清理工作线程
        if self.update_worker:
            self.update_worker = None 