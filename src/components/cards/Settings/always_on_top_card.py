#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
总是置顶窗口设置卡片组件
Always On Top Card Component
"""

import os
import sys
import ctypes
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal

try:
    from qfluentwidgets import (
        CardWidget, SwitchButton, FluentIcon, InfoBar,
        InfoBarPosition, StrongBodyLabel, BodyLabel, IconWidget
    )
    HAS_FLUENT_WIDGETS = True
except ImportError:
    print("无法导入qfluentwidgets组件，将使用基本的控件替代")
    from PyQt5.QtWidgets import QLabel, QFrame, QCheckBox
    HAS_FLUENT_WIDGETS = False
    
    # 创建替代类
    class CardWidget(QFrame):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setStyleSheet("background-color: #f5f5f5; border-radius: 8px; padding: 8px;")
    
    class SwitchButton(QCheckBox):
        checkedChanged = pyqtSignal(bool)
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.toggled.connect(self.checkedChanged)
            
        def setChecked(self, checked):
            super().setChecked(checked)
            
        def isChecked(self):
            return super().isChecked()
    
    class FluentIcon:
        PIN = None
    
    class InfoBar:
        @staticmethod
        def success(title, content, orient=1, isClosable=True, position=None, duration=3000, parent=None):
            pass
        
        @staticmethod
        def warning(title, content, orient=1, isClosable=True, position=None, duration=3000, parent=None):
            pass
        
        @staticmethod
        def error(title, content, orient=1, isClosable=True, position=None, duration=3000, parent=None):
            pass
        
        @staticmethod
        def info(title, content, orient=1, isClosable=True, position=None, duration=3000, parent=None):
            pass
    
    class InfoBarPosition:
        TOP = None
    
    class StrongBodyLabel(QLabel):
        def __init__(self, text, parent=None):
            super().__init__(text, parent)
            self.setStyleSheet("font-weight: bold; font-size: 14px;")
            
    class BodyLabel(QLabel):
        def __init__(self, text, parent=None):
            super().__init__(text, parent)
    
    class IconWidget(QWidget):
        def __init__(self, icon, parent=None):
            super().__init__(parent)
            self.setFixedSize(16, 16)

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None  # 如果导入失败，设为None


class AlwaysOnTopCard(CardWidget):
    """
    总是置顶窗口设置卡片，提供窗口置顶功能
    Always on top window card, provides window pin to top functionality
    """
    
    def __init__(self, parent=None, config_manager=None):
        """
        初始化总是置顶窗口设置卡片
        
        Args:
            parent: 父控件
            config_manager: 配置管理器实例
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.always_on_top = self.config_manager.get("always_on_top", False) if config_manager else False
        self.setupUI()
    
    def setupUI(self):
        """设置UI布局"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # 标题行布局
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # 添加图标
        title_icon = IconWidget(FluentIcon.PIN, self)
        title_icon.setFixedSize(16, 16)
        
        # 标题
        title_label = StrongBodyLabel(self._get_text("always_on_top"))
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # 总是置顶选项
        always_on_top_row = QHBoxLayout()
        
        always_on_top_label = BodyLabel(self._get_text("always_on_top_description"))
        self.always_on_top_switch = SwitchButton()
        self.always_on_top_switch.setChecked(self.always_on_top)
        self.always_on_top_switch.checkedChanged.connect(self.on_always_on_top_changed)
        
        always_on_top_row.addWidget(always_on_top_label)
        always_on_top_row.addStretch()
        always_on_top_row.addWidget(self.always_on_top_switch)
        
        main_layout.addLayout(always_on_top_row)
    
    def on_always_on_top_changed(self, is_checked):
        """总是置顶设置改变的响应函数"""
        self.always_on_top = is_checked
        if self.config_manager:
            self.config_manager.set("always_on_top", is_checked)
            
        # 设置窗口置顶属性
        main_window = self.window()
        if main_window:
            print(f"正在设置窗口置顶: {is_checked}")
            # 使用平台特定的API设置窗口置顶
            if sys.platform == 'win32':
                # Windows平台使用SetWindowPos API
                try:
                    # 先确保窗口显示并处理事件
                    main_window.show()
                    QApplication.processEvents()
                    
                    # 获取窗口标题
                    window_title = main_window.windowTitle()
                    print(f"窗口标题: {window_title}")
                    
                    # 使用FindWindow API获取窗口句柄
                    # 将窗口标题转换为C类型字符串
                    title = ctypes.c_wchar_p(window_title)
                    hwnd = ctypes.windll.user32.FindWindowW(None, title)
                    print(f"通过FindWindow获取的窗口句柄: {hwnd}")
                    
                    if hwnd == 0:
                        # 如果FindWindow失败，尝试使用Qt的winId
                        hwnd = ctypes.c_int(main_window.winId().__int__())
                        print(f"回退到Qt的窗口句柄: {hwnd.value}")
                    
                    # Windows API常量
                    HWND_TOPMOST = -1  # 置于所有非顶层窗口之上
                    HWND_NOTOPMOST = -2  # 置于所有顶层窗口之下
                    
                    # 设置窗口位置标志
                    SWP_NOMOVE = 0x0002  # 保持当前位置
                    SWP_NOSIZE = 0x0001  # 保持当前大小
                    SWP_NOACTIVATE = 0x0010  # 不激活窗口
                    SWP_SHOWWINDOW = 0x0040  # 显示窗口
                    
                    # 组合标志 - 不改变大小和位置，不激活窗口
                    flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
                    
                    # 调用Windows API设置窗口位置
                    if is_checked:
                        # 设置为置顶
                        print("尝试设置窗口为置顶")
                        result = ctypes.windll.user32.SetWindowPos(
                            hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
                        print(f"SetWindowPos结果: {result}")
                        if not result:
                            # 获取错误码
                            error_code = ctypes.windll.kernel32.GetLastError()
                            print(f"SetWindowPos失败，错误码: {error_code}")
                            # 回退到Qt方法
                            self._set_window_top_with_qt(main_window, is_checked)
                    else:
                        # 取消置顶
                        print("尝试取消窗口置顶")
                        result = ctypes.windll.user32.SetWindowPos(
                            hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, flags)
                        print(f"SetWindowPos结果: {result}")
                        if not result:
                            # 获取错误码
                            error_code = ctypes.windll.kernel32.GetLastError()
                            print(f"SetWindowPos失败，错误码: {error_code}")
                            # 回退到Qt方法
                            self._set_window_top_with_qt(main_window, is_checked)
                except Exception as e:
                    print(f"设置窗口置顶时出错: {e}")
                    # 回退到Qt方法
                    self._set_window_top_with_qt(main_window, is_checked)
            else:
                # 其他平台使用Qt方法
                self._set_window_top_with_qt(main_window, is_checked)
            
        # 显示提示消息
        self.showMessage(
            "success" if is_checked else "info",
            self._get_text("always_on_top_enabled" if is_checked else "always_on_top_disabled"),
            self._get_text("always_on_top_enabled_tip" if is_checked else "always_on_top_disabled_tip")
        )
    
    def _set_window_top_with_qt(self, window, is_top):
        """使用Qt方法设置窗口置顶"""
        # 保存窗口状态
        was_visible = window.isVisible()
        was_maximized = window.isMaximized()
        geometry = window.geometry()
        
        # 获取当前窗口标志
        flags = window.windowFlags()
        
        # 修改窗口标志
        if is_top:
            # 添加置顶标志
            flags |= Qt.WindowStaysOnTopHint
        else:
            # 移除置顶标志
            flags &= ~Qt.WindowStaysOnTopHint
        
        # 应用新标志 - 这会导致窗口重建
        window.setWindowFlags(flags)
        
        # 恢复窗口状态
        if was_maximized:
            window.showMaximized()
        else:
            window.setGeometry(geometry)
            if was_visible:
                window.show()
    
    def _get_text(self, key, default=""):
        """获取本地化文本"""
        if lang:
            return lang.get(key, default)
        return default
    
    def showMessage(self, msg_type, title, content):
        """显示消息通知
        
        Args:
            msg_type: 消息类型 (success, warning, error, info)
            title: 标题
            content: 内容
        """
        # 创建orient参数，避免直接使用Qt.Horizontal
        orient = 1  # Qt.Horizontal的值是1
        
        # 获取主窗口作为父控件，确保消息显示在最上方
        main_window = self.window()
        parent = main_window if main_window else self
        
        if msg_type == "success":
            InfoBar.success(title, content, orient=orient, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
        elif msg_type == "warning":
            InfoBar.warning(title, content, orient=orient, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
        elif msg_type == "error":
            InfoBar.error(title, content, orient=orient, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent)
        else:
            InfoBar.info(title, content, orient=orient, isClosable=True, position=InfoBarPosition.TOP, duration=3000, parent=parent) 