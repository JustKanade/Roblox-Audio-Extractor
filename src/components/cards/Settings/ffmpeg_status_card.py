from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QSizePolicy)
from PyQt5.QtGui import QColor
from qfluentwidgets import (SettingCard, BodyLabel, CaptionLabel, 
                          PrimaryPushButton, InfoBar, InfoBarPosition,
                          FluentIcon, IconWidget, StateToolTip, PushButton,
                          setFont)
import os
import subprocess
import sys
import shutil

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None

class FFmpegStatusCard(SettingCard):
    """FFmpeg状态检测卡片"""

    ffmpegPathChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        self.ffmpeg_path = ""
        
        # 获取翻译文本
        title = self.get_text("ffmpeg_status_title") or "FFmpeg Status"
        description = "Detect and manage FFmpeg installation status"
        
        super().__init__(
            FluentIcon.MEDIA,
            title,
            description,
            parent
        )
        
        self._setupContent()
        
        # 延迟检查FFmpeg状态
        QTimer.singleShot(100, self.check_ffmpeg_silent)
    
    def get_text(self, key):
        """获取翻译文本"""
        if lang is None:
            return ""
        return lang.get(key)
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器 - 水平布局
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 检测按钮
        self.detect_button = PushButton(FluentIcon.SYNC, self.get_text("detect_ffmpeg") or "Detect FFmpeg")
        self.detect_button.setFixedSize(100, 32)  # 增加宽度确保文字显示完整
        self.detect_button.clicked.connect(self.check_ffmpeg)
        
        # 浏览按钮  
        self.browse_button = PushButton(FluentIcon.FOLDER, self.get_text("browse_ffmpeg") or "Browse FFmpeg")
        self.browse_button.setFixedSize(100, 32)  # 增加宽度确保文字显示完整
        self.browse_button.clicked.connect(self.browse_ffmpeg)
        
        content_layout.addWidget(self.detect_button)
        content_layout.addWidget(self.browse_button)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)
    
    def check_ffmpeg_silent(self):
        """静默检查FFmpeg（不显示消息提示）"""
        self.check_ffmpeg_internal(show_messages=False)
    
    def check_ffmpeg(self):
        """检查FFmpeg（显示消息提示）"""
        self.check_ffmpeg_internal(show_messages=True)
    
    def check_ffmpeg_internal(self, show_messages=True):
        """内部FFmpeg检查逻辑"""
        try:
            # 1. 尝试在系统PATH中查找
            if shutil.which("ffmpeg"):
                self.ffmpeg_path = "ffmpeg"
                self._update_status(True, self.get_text("ffmpeg_available") or "Available")
                if show_messages:
                    InfoBar.success(
                        title=self.get_text("ffmpeg_available") or "FFmpeg Available",
                        content=self.get_text("ffmpeg_ready") or "FFmpeg is ready, duration classification feature will work normally",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self.window()
                    )
                return True
            
            # 2. 检查配置中的自定义路径
            if hasattr(self, 'parent') and hasattr(self.parent(), 'config_manager'):
                config_manager = self.parent().config_manager
                custom_path = config_manager.get("ffmpeg_path", "")
                if custom_path and os.path.isfile(custom_path):
                    if self._test_ffmpeg_executable(custom_path):
                        self.ffmpeg_path = custom_path
                        self._update_status(True, self.get_text("ffmpeg_available") or "Available")
                        if show_messages:
                            InfoBar.success(
                                title=self.get_text("ffmpeg_available") or "FFmpeg Available",
                                content=self.get_text("ffmpeg_ready") or "FFmpeg is ready, duration classification feature will work normally",
                                orient=Qt.Horizontal,
                                isClosable=True,
                                position=InfoBarPosition.TOP,
                                duration=3000,
                                parent=self.window()
                            )
                        return True
            
            # 3. 未找到FFmpeg
            self.ffmpeg_path = ""
            self._update_status(False, self.get_text("ffmpeg_not_found") or "Not Found")
            
            if show_messages:
                InfoBar.warning(
                    title=self.get_text("ffmpeg_not_available") or "FFmpeg Not Available",
                    content=self.get_text("ffmpeg_install_instruction") or "Please install FFmpeg to enable audio duration classification feature. You can manually specify FFmpeg path",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=4000,
                    parent=self.window()
                )
            
            return False
        
        except Exception as e:
            self.ffmpeg_path = ""
            self._update_status(False, f"Error: {str(e)}")
            return False
    
    def _update_status(self, available, status_text):
        """更新状态显示（现在只保存状态，不显示）"""
        # 状态显示组件已移除，只保存状态用于内部逻辑
        pass
    
    def _test_ffmpeg_executable(self, path):
        """测试FFmpeg可执行文件"""
        try:
            result = subprocess.run([path, "-version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0 and "ffmpeg version" in result.stdout.lower()
        except:
            return False
    
    def browse_ffmpeg(self):
        """浏览FFmpeg文件"""
        file_filter = "FFmpeg (ffmpeg.exe);;All Files (*.*)" if sys.platform == "win32" else "FFmpeg (ffmpeg);;All Files (*.*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.get_text("select_ffmpeg_file") or "Select FFmpeg File",
            "",
            file_filter
        )
        
        if not file_path:
            return
        
        if not self._test_ffmpeg_executable(file_path):
            InfoBar.error(
                title=self.get_text("invalid_ffmpeg") or "Invalid FFmpeg File",
                content=self.get_text("invalid_ffmpeg_hint") or "The selected file is not a valid FFmpeg executable",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
            return
        
        # 保存FFmpeg路径
        if hasattr(self, 'parent') and hasattr(self.parent(), 'config_manager'):
            config_manager = self.parent().config_manager
            config_manager.set("ffmpeg_path", file_path)
        
        self.ffmpeg_path = file_path
        self._update_status(True, self.get_text("ffmpeg_available") or "Available")
        
        InfoBar.success(
            title=self.get_text("ffmpeg_set_success") or "FFmpeg Setup Successful",
            content=self.get_text("ffmpeg_path_updated") or "FFmpeg path has been updated",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window()
        )
        
        self.ffmpegPathChanged.emit(file_path) 