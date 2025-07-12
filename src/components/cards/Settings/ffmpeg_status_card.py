from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QSizePolicy)
from PyQt5.QtGui import QColor
from qfluentwidgets import (CardWidget, StrongBodyLabel, CaptionLabel, 
                          BodyLabel, PrimaryPushButton, InfoBar, InfoBarPosition,
                          FluentIcon, IconWidget, StateToolTip, PushButton)
import os
import subprocess
import sys
import shutil

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None  # 如果导入失败，设为None

class FFmpegStatusCard(CardWidget):
    """FFmpeg状态检测卡片"""

    # 信号：FFmpeg路径更新
    ffmpegPathChanged = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.ffmpeg_path = ""
        self.setup_ui()
        
        # 使用定时器延迟检查，确保UI已完全加载，但使用静默检查
        QTimer.singleShot(100, self.check_ffmpeg_silent)
    
    def setup_ui(self):
        """设置UI组件"""
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.setObjectName("ffmpegStatusCard")
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # 标题行 - 带图标
        title_row = QHBoxLayout()
        title_icon = IconWidget(FluentIcon.MEDIA)
        title_icon.setFixedSize(20, 20)
        title = StrongBodyLabel(self.get_text("ffmpeg_status_title") or "FFmpeg状态")
        title.setObjectName("ffmpegCardTitle")
        
        title_row.addWidget(title_icon)
        title_row.addSpacing(8)
        title_row.addWidget(title)
        title_row.addStretch()
        layout.addLayout(title_row)
        
        # 状态行 - 改进视觉效果
        status_container = QWidget()
        status_container.setObjectName("statusContainer")
        status_container.setStyleSheet("""
            #statusContainer {
                background-color: rgba(200, 200, 200, 0.15);
                border-radius: 4px;
                border: 1px solid rgba(0, 0, 0, 0.08);
                padding: 2px;
            }
        """)
        
        status_row = QHBoxLayout(status_container)
        status_row.setContentsMargins(10, 8, 10, 8)
        status_row.setSpacing(10)
        
        status_label = BodyLabel(self.get_text("ffmpeg_status") or "FFmpeg状态:")
        self.status_icon = IconWidget()
        self.status_icon.setFixedSize(16, 16)
        self.status_value = BodyLabel("")
        self.status_value.setObjectName("statusValue")
        
        status_row.addWidget(status_label)
        status_row.addWidget(self.status_icon)
        status_row.addWidget(self.status_value)
        status_row.addStretch()
        layout.addWidget(status_container)
        
        # 提示信息
        self.info_label = CaptionLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setObjectName("infoLabel")
        layout.addWidget(self.info_label)
        
        # 按钮行 - 添加两个按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # 检测按钮
        self.detect_btn = PushButton(
            FluentIcon.SYNC,
            self.get_text("detect_ffmpeg") or "检测FFmpeg"
        )
        # 连接到带消息框的检测方法
        self.detect_btn.clicked.connect(self.check_ffmpeg)
        
        # 浏览按钮
        self.browse_btn = PrimaryPushButton(
            FluentIcon.FOLDER_ADD,
            self.get_text("browse_ffmpeg") or "浏览FFmpeg"
        )
        self.browse_btn.clicked.connect(self.browse_ffmpeg)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.detect_btn)
        btn_layout.addWidget(self.browse_btn)
        layout.addLayout(btn_layout)
    
    def check_ffmpeg_silent(self):
        """静默检查FFmpeg是否可用并更新UI（不显示消息框）"""
        # 直接执行检查，不显示状态提示和消息框
        self._perform_check(None, show_infobar=False)
    
    def check_ffmpeg(self):
        """检查FFmpeg是否可用并更新UI（显示消息框）"""
        # 创建状态提示
        state_tooltip = StateToolTip(
            self.get_text("detecting") or "正在检测",
            self.get_text("detecting_ffmpeg") or "正在检测FFmpeg...",
            self.window()
        )
        state_tooltip.show()
        
        # 使用QTimer确保UI更新
        QTimer.singleShot(300, lambda: self._perform_check(state_tooltip, show_infobar=True))
    
    def _perform_check(self, state_tooltip=None, show_infobar=True):
        """执行实际的FFmpeg检查
        
        Args:
            state_tooltip: 状态提示对象，如果为None则不显示状态
            show_infobar: 是否显示顶部消息条
        """
        is_available = self.is_ffmpeg_available()
        path_found = self._find_ffmpeg_path() if is_available else ""
        
        if is_available:
            # 更新UI为可用状态
            self.status_icon.setIcon(FluentIcon.ACCEPT)
            self.status_value.setText(self.get_text("available") or "可用")
            self.status_value.setStyleSheet("color: #2ECC71;")  # 绿色
            
            # 更新信息文本
            if path_found:
                self.info_label.setText(
                    (self.get_text("ffmpeg_available_info_path") or 
                    f"FFmpeg可用，路径：{path_found}。按时长分类功能可以正常工作。")
                )
            else:
                self.info_label.setText(
                    self.get_text("ffmpeg_available_info") or 
                    "FFmpeg可用，按时长分类功能可以正常工作。"
                )
            
            # 更新状态提示
            if state_tooltip:
                state_tooltip.setContent(self.get_text("ffmpeg_detected") or "FFmpeg检测完成")
                state_tooltip.setState(True)
                QTimer.singleShot(2000, state_tooltip.close)
            
            # 显示顶部消息条（仅当需要时）
            if show_infobar:
                self._show_top_info_bar(
                    "success", 
                    self.get_text("ffmpeg_available") or "FFmpeg可用", 
                    self.get_text("ffmpeg_available_message") or "FFmpeg已安装，按时长分类功能可以正常工作。"
                )
        else:
            # 更新UI为不可用状态
            self.status_icon.setIcon(FluentIcon.CANCEL)
            self.status_value.setText(self.get_text("not_available") or "不可用")
            self.status_value.setStyleSheet("color: #E74C3C;")  # 红色
            
            self.info_label.setText(
                self.get_text("ffmpeg_not_available_info") or 
                "FFmpeg未安装或不在系统PATH中。按时长分类功能将无法正常工作。"
            )
            
            # 更新状态提示
            if state_tooltip:
                state_tooltip.setContent(self.get_text("ffmpeg_not_detected") or "未检测到FFmpeg")
                state_tooltip.setState(False)
                QTimer.singleShot(2000, state_tooltip.close)
            
            # 显示顶部警告消息条（仅当需要时）
            if show_infobar:
                self._show_top_info_bar(
                    "warning", 
                    self.get_text("ffmpeg_not_available") or "FFmpeg不可用", 
                    self.get_text("ffmpeg_not_available_message") or 
                    "未检测到FFmpeg，按时长分类功能可能无法正常工作。请点击'浏览FFmpeg'手动设置。"
                )
    
    def _find_ffmpeg_path(self) -> str:
        """查找FFmpeg路径"""
        # 如果已有自定义路径，优先返回
        if self.ffmpeg_path and os.path.exists(self.ffmpeg_path):
            return self.ffmpeg_path
            
        # 在系统PATH中查找
        ffmpeg_cmd = "ffmpeg.exe" if os.name == 'nt' else "ffmpeg"
        
        try:
            # 使用which/where命令查找
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    ["where", ffmpeg_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:  # Unix/Linux/Mac
                result = subprocess.run(
                    ["which", ffmpeg_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')[0]
                
            # 如果上面的方法失败，尝试使用shutil
            path = shutil.which(ffmpeg_cmd)
            if path:
                return path
                
        except Exception:
            pass
            
        return ""
    
    def is_ffmpeg_available(self) -> bool:
        """检查FFmpeg是否可用"""
        try:
            subprocess_flags = 0
            if os.name == 'nt':  # Windows
                subprocess_flags = subprocess.CREATE_NO_WINDOW

            # 先检查PATH中是否有ffmpeg
            result = subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess_flags
            )
            if result.returncode == 0:
                return True
            
            # 如果有自定义路径，检查该路径
            if self.ffmpeg_path and os.path.exists(self.ffmpeg_path):
                result = subprocess.run(
                    [self.ffmpeg_path, "-version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess_flags
                )
                return result.returncode == 0
                
            return False
        except Exception:
            return False
    
    def browse_ffmpeg(self):
        """浏览选择FFmpeg可执行文件"""
        file_filter = ""
        if os.name == 'nt':  # Windows
            file_filter = "可执行文件 (*.exe)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            self.get_text("select_ffmpeg") or "选择FFmpeg可执行文件", 
            "", 
            file_filter
        )
        
        if file_path:
            # 显示状态提示
            state_tooltip = StateToolTip(
                self.get_text("verifying") or "正在验证",
                self.get_text("verifying_ffmpeg") or "正在验证FFmpeg...",
                self.window()
            )
            state_tooltip.show()
            
            # 验证选择的文件是否真的是FFmpeg
            try:
                subprocess_flags = 0
                if os.name == 'nt':  # Windows
                    subprocess_flags = subprocess.CREATE_NO_WINDOW
                
                result = subprocess.run(
                    [file_path, "-version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess_flags
                )
                
                if result.returncode == 0 and b"ffmpeg" in result.stdout.lower():
                    self.ffmpeg_path = file_path
                    self.ffmpegPathChanged.emit(file_path)
                    
                    # 更新状态提示
                    state_tooltip.setContent(self.get_text("ffmpeg_set_success") or "FFmpeg路径设置成功")
                    state_tooltip.setState(True)
                    QTimer.singleShot(2000, state_tooltip.close)
                    
                    # 显示顶部成功消息条
                    self._show_top_info_bar(
                        "success",
                        self.get_text("success") or "成功",
                        self.get_text("ffmpeg_set_success") or "FFmpeg路径设置成功"
                    )
                    
                    # 更新UI状态（使用静默检测，避免显示两次消息框）
                    self.check_ffmpeg_silent()
                else:
                    # 更新状态提示
                    state_tooltip.setContent(self.get_text("invalid_ffmpeg") or "所选文件不是有效的FFmpeg可执行文件")
                    state_tooltip.setState(False)
                    QTimer.singleShot(2000, state_tooltip.close)
                    
                    # 显示顶部错误消息条
                    self._show_top_info_bar(
                        "error",
                        self.get_text("error") or "错误",
                        self.get_text("invalid_ffmpeg") or "所选文件不是有效的FFmpeg可执行文件"
                    )
            except Exception as e:
                # 更新状态提示
                state_tooltip.setContent(self.get_text("ffmpeg_error") or f"FFmpeg验证失败")
                state_tooltip.setState(False)
                QTimer.singleShot(2000, state_tooltip.close)
                
                # 显示顶部错误消息条
                self._show_top_info_bar(
                    "error",
                    self.get_text("error") or "错误",
                    self.get_text("ffmpeg_error") or f"FFmpeg验证失败: {str(e)}"
                )
    
    def _show_top_info_bar(self, type_name: str, title: str, content: str):
        """显示顶部消息条"""
        if type_name == "success":
            InfoBar.success(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self.window()
            )
        elif type_name == "warning":
            InfoBar.warning(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self.window()
            )
        elif type_name == "error":
            InfoBar.error(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self.window()
            )
        else:
            InfoBar.info(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=4000,
                parent=self.window()
            )
    
    def setFFmpegPath(self, path: str):
        """设置FFmpeg路径"""
        if path and os.path.exists(path):
            self.ffmpeg_path = path
            self.check_ffmpeg_silent()  # 使用静默检测，避免自动弹出消息框
    
    def get_text(self, key: str) -> str | None:
        """获取翻译文本"""
        if lang is None:
            return None
        return lang.get(key) 