from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFileDialog, QWidget
from PyQt5.QtGui import QKeyEvent
import os
import platform

from qfluentwidgets import (
    SettingCard, LineEdit, PushButton, BodyLabel, 
    FluentIcon, setFont
)

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None

class CustomLineEdit(LineEdit):
    """自定义LineEdit，添加Enter键信号"""
    
    enterPressed = pyqtSignal()
    
    def keyPressEvent(self, event: QKeyEvent):
        """重写按键事件，捕获Enter键"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.enterPressed.emit()
        else:
            super().keyPressEvent(event)


class LaunchFileCard(SettingCard):
    """启动文件设置卡片"""
    
    launchFileChanged = pyqtSignal(str)
    clearLaunchFile = pyqtSignal()
    
    def __init__(self, config_manager, parent=None):
        self.config_manager = config_manager
        
        # 获取翻译文本
        title = self._get_text("launch_file_title") or "Launch File"
        content = self._get_text("launch_file_description") or "Select a file to be executed when clicking the Launch button"
        
        super().__init__(
            FluentIcon.PLAY,
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
        
        # 启动文件路径编辑框
        self.launchFileEdit = CustomLineEdit()
        self.launchFileEdit.setPlaceholderText(
            self._get_text("launch_file_placeholder") or "Select an executable file to launch"
        )
        self.launchFileEdit.setClearButtonEnabled(True)
        self.launchFileEdit.setText(self.config_manager.get("launch_file", ""))
        self.launchFileEdit.editingFinished.connect(self._saveLaunchFile)
        self.launchFileEdit.enterPressed.connect(self._clearLaunchFile)

        
        # 浏览按钮
        self.browseButton = PushButton(FluentIcon.FOLDER_ADD, self._get_text("browse"))
        self.browseButton.setFixedSize(100, 32)
        self.browseButton.clicked.connect(self._browseFile)
        
        content_layout.addWidget(self.launchFileEdit, 1)
        content_layout.addWidget(self.browseButton)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)
    
    def _saveLaunchFile(self):
        """保存启动文件路径"""
        path = self.launchFileEdit.text().strip()
        self.config_manager.set("launch_file", path)
        self.launchFileChanged.emit(path)
    
    def _clearLaunchFile(self):
        """清除启动文件路径"""
        self.launchFileEdit.clear()
        self.config_manager.set("launch_file", "")
        self.clearLaunchFile.emit()
    
    def _browseFile(self):
        """浏览文件"""
        current_path = self.launchFileEdit.text() or ""
        
        # 根据操作系统设置文件过滤器
        if platform.system() == "Windows":
            file_filter = "Executable Files (*.exe *.bat *.cmd *.com *.scr *.msi);;All Files (*.*)"
        elif platform.system() == "Darwin":  # macOS
            file_filter = "Applications (*.app);;Executable Files (*.sh *.command);;All Files (*.*)"
        else:  # Linux and others
            file_filter = "Executable Files (*.sh *.run *.AppImage);;All Files (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            self._get_text("select_executable") or "Select Executable File",
            os.path.dirname(current_path) if current_path else "",
            file_filter
        )
        
        if file_path:
            self.launchFileEdit.setText(file_path)
            self._saveLaunchFile()
    
    def updatePath(self, path):
        """更新路径显示"""
        self.launchFileEdit.setText(path) 