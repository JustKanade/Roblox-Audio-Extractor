from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QSizePolicy)
from PyQt5.QtGui import QColor
from qfluentwidgets import (ExpandSettingCard, BodyLabel, CaptionLabel, 
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

class FFmpegStatusCard(ExpandSettingCard):
    """FFmpeg状态检测卡片"""

    ffmpegPathChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        # 获取翻译文本
        title = ""
        description = ""
        if lang:
            title = lang.get("ffmpeg_status_title") or ""
            description = lang.get("ffmpeg_description") or ""
        
        super().__init__(
            FluentIcon.MEDIA,
            title or "FFmpeg状态",
            description or "检测和管理FFmpeg安装状态",
            parent
        )
        
        self.ffmpeg_path = ""
        self._setupContent()
        
        # 延迟检查FFmpeg状态
        QTimer.singleShot(100, self.check_ffmpeg_silent)
    
    def _setupContent(self):
        """设置内容"""
        # 创建内容控件
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
        
        # 状态显示区域
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(12)
        
        # 状态图标
        self.status_icon = IconWidget(FluentIcon.QUESTION)
        self.status_icon.setFixedSize(16, 16)
        
        # 状态文本
        self.status_label = BodyLabel("检测中...")
        setFont(self.status_label, 13)
        
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        content_layout.addWidget(status_container)
        
        # 按钮行
        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        
        # 检测按钮
        self.detect_button = PushButton(FluentIcon.SYNC, self.get_text("detect_ffmpeg") or "检测FFmpeg")
        self.detect_button.clicked.connect(self.check_ffmpeg)
        
        # 浏览按钮  
        self.browse_button = PushButton(FluentIcon.FOLDER, self.get_text("browse_ffmpeg") or "浏览FFmpeg")
        self.browse_button.clicked.connect(self.browse_ffmpeg)
        
        button_row.addWidget(self.detect_button)
        button_row.addWidget(self.browse_button)
        button_row.addStretch()
        
        content_layout.addLayout(button_row)
        
        # 使用正确的API添加内容
        self.addWidget(content_widget)
    
    def get_text(self, key):
        """获取翻译文本"""
        if lang is None:
            return ""
        return lang.get(key)
    
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
                self._update_status(True, self.get_text("ffmpeg_available") or "可用",
                                  self.get_text("ffmpeg_found_in_path") or f"在系统PATH中找到FFmpeg")
                if show_messages:
                    InfoBar.success(
                        title=self.get_text("ffmpeg_available") or "FFmpeg可用",
                        content=self.get_text("ffmpeg_ready") or "FFmpeg已准备就绪，时长分类功能可正常工作",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                return True
            
            # 2. 检查配置中的自定义路径
            if hasattr(self, 'parent') and hasattr(self.parent(), 'config_manager'):
                config_manager = self.parent().config_manager
                custom_path = config_manager.get("ffmpeg_path", "")
                if custom_path and os.path.isfile(custom_path):
                    if self._test_ffmpeg_executable(custom_path):
                        self.ffmpeg_path = custom_path
                        self._update_status(True, self.get_text("ffmpeg_available") or "可用",
                                          f"{self.get_text('ffmpeg_found_at') or '找到FFmpeg'}: {custom_path}")
                        if show_messages:
                            InfoBar.success(
                                title=self.get_text("ffmpeg_available") or "FFmpeg可用",
                                content=self.get_text("ffmpeg_ready") or "FFmpeg已准备就绪，时长分类功能可正常工作",
                                orient=Qt.Horizontal,
                                isClosable=True,
                                position=InfoBarPosition.TOP,
                                duration=3000,
                                parent=self
                            )
                        return True
            
            # 3. 未找到FFmpeg
            self.ffmpeg_path = ""
            self._update_status(False, self.get_text("ffmpeg_not_found") or "未找到",
                              self.get_text("ffmpeg_install_hint") or "请安装FFmpeg以启用音频时长分类功能")
            
            if show_messages:
                InfoBar.warning(
                    title=self.get_text("ffmpeg_not_available") or "FFmpeg不可用",
                    content=self.get_text("ffmpeg_install_instruction") or "请安装FFmpeg以启用音频时长分类功能。您可以手动指定FFmpeg路径",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=4000,
                    parent=self
                )
            
            return False
        
        except Exception as e:
            self.ffmpeg_path = ""
            self._update_status(False, self.get_text("ffmpeg_not_found") or "未找到", f"检测出错: {str(e)}")
            return False
    
    def _update_status(self, available, status_text, detail_text):
        """更新状态显示"""
        if available:
            self.status_icon.setIcon(FluentIcon.ACCEPT)
            self.status_label.setText(f"✓ {status_text}")
            self.status_label.setStyleSheet("color: #10b981;")  # 绿色
        else:
            self.status_icon.setIcon(FluentIcon.CLOSE)
            self.status_label.setText(f"✗ {status_text}")
            self.status_label.setStyleSheet("color: #ef4444;")  # 红色
    
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
            self.get_text("select_ffmpeg_file") or "选择FFmpeg文件",
            "",
            file_filter
        )
        
        if not file_path:
            return
        
        if not self._test_ffmpeg_executable(file_path):
            InfoBar.error(
                title=self.get_text("invalid_ffmpeg") or "无效的FFmpeg文件",
                content=self.get_text("invalid_ffmpeg_hint") or "选择的文件不是有效的FFmpeg可执行文件",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
        
        # 保存FFmpeg路径
        if hasattr(self, 'parent') and hasattr(self.parent(), 'config_manager'):
            config_manager = self.parent().config_manager
            config_manager.set("ffmpeg_path", file_path)
        
        self.ffmpeg_path = file_path
        self._update_status(True, self.get_text("ffmpeg_available") or "可用",
                          f"{self.get_text('ffmpeg_custom_path') or '自定义路径'}: {file_path}")
        
        InfoBar.success(
            title=self.get_text("ffmpeg_set_success") or "FFmpeg设置成功",
            content=self.get_text("ffmpeg_path_updated") or "FFmpeg路径已更新",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
        
        self.ffmpegPathChanged.emit(file_path) 