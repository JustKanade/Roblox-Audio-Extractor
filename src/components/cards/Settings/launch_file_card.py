from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFileDialog, QSizePolicy)
from PyQt5.QtGui import QColor
from qfluentwidgets import (SettingCard, BodyLabel, CaptionLabel, 
                          PrimaryPushButton, InfoBar, InfoBarPosition,
                          FluentIcon, IconWidget, PushButton, TransparentPushButton)
import os
import sys

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None

class LaunchFileCard(SettingCard):
    """启动文件设置卡片"""

    launchFileChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        self.launch_file_path = ""
        
        # 获取翻译文本
        title = self.get_text("launch_file_settings") or "Launch File Settings"
        description = self.get_text("launch_file_description") or "Configure the file to launch when clicking the Launch button."
        
        super().__init__(
            FluentIcon.PLAY,
            title,
            description,
            parent
        )
        
        self._setupContent()
        self._loadCurrentFile()
    
    def get_text(self, key):
        """获取翻译文本"""
        if lang is None:
            return ""
        return lang.get(key)
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 选择文件按钮
        self.select_button = PushButton(FluentIcon.FOLDER, self.get_text("select_launch_file") or "Select File")
        self.select_button.setFixedSize(130, 32)
        self.select_button.clicked.connect(self.select_launch_file)
        
        content_layout.addWidget(self.select_button)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)
    
    def _loadCurrentFile(self):
        """加载当前设置的启动文件"""
        try:
            if hasattr(self, 'parent') and hasattr(self.parent(), 'config_manager'):
                config_manager = self.parent().config_manager
                file_path = config_manager.cfg.get(config_manager.cfg.launchFilePath)
                if file_path and os.path.isfile(file_path):
                    self.launch_file_path = file_path
                else:
                    self.launch_file_path = ""
        except Exception as e:
            self.launch_file_path = ""
    

    
    def select_launch_file(self):
        """选择启动文件"""
        # Windows可执行文件过滤器
        if sys.platform == "win32":
            file_filter = "Executable Files (*.exe *.bat *.cmd);;All Files (*.*)"
        else:
            file_filter = "All Files (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.get_text("select_launch_file") or "Select Launch File",
            "",
            file_filter
        )
        
        if not file_path:
            return
        
        if not os.path.isfile(file_path):
            InfoBar.error(
                title="Invalid File",
                content="The selected file does not exist or is not accessible.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
            return
        
        # 保存启动文件路径
        if hasattr(self, 'parent') and hasattr(self.parent(), 'config_manager'):
            config_manager = self.parent().config_manager
            config_manager.cfg.set(config_manager.cfg.launchFilePath, file_path)
        
        self.launch_file_path = file_path
        
        InfoBar.success(
            title="File Selected",
            content=f"Launch file has been set to: {os.path.basename(file_path)}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )
        
        self.launchFileChanged.emit(file_path)
    

    
    def get_launch_file_path(self):
        """获取当前启动文件路径"""
        return self.launch_file_path
    
    def get_launch_file_display_name(self):
        """获取启动文件显示名称（无扩展名）"""
        if self.launch_file_path:
            filename = os.path.basename(self.launch_file_path)
            return os.path.splitext(filename)[0]
        return "" 