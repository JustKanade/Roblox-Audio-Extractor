from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFileDialog, QWidget
from PyQt5.QtGui import QKeyEvent

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


class GlobalInputPathCard(SettingCard):
    """全局输入路径设置卡片"""
    
    inputPathChanged = pyqtSignal(str)
    restoreDefaultPath = pyqtSignal()
    
    def __init__(self, config_manager, parent=None):
        self.config_manager = config_manager
        
        # 获取翻译文本
        title = self._get_text("global_input_path_title") or "Global Input Path"
        
        super().__init__(
            FluentIcon.FOLDER,
            title,

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
        
        # 输入路径编辑框
        self.inputPathEdit = CustomLineEdit()
        self.inputPathEdit.setPlaceholderText("Enter path or press Enter to restore default")  # 简化占位符文字
        self.inputPathEdit.setClearButtonEnabled(True)
        self.inputPathEdit.setText(self.config_manager.get("global_input_path", ""))
        self.inputPathEdit.editingFinished.connect(self._saveGlobalInputPath)
        self.inputPathEdit.enterPressed.connect(self._restoreDefaultPath)
        self.inputPathEdit.setFixedHeight(32)
        self.inputPathEdit.setMinimumWidth(300)  # 增加最小宽度确保文字显示完整
        
        # 浏览按钮
        self.browseButton = PushButton(FluentIcon.FOLDER_ADD, self._get_text("browse") or "Browse")
        self.browseButton.setFixedSize(100, 32)  # 增加按钮宽度确保文字完整显示
        self.browseButton.clicked.connect(self._browseDirectory)
        
        content_layout.addWidget(self.inputPathEdit, 1)
        content_layout.addWidget(self.browseButton)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)
    
    def _saveGlobalInputPath(self):
        """保存全局输入路径"""
        path = self.inputPathEdit.text().strip()
        self.config_manager.set("global_input_path", path)
        self.inputPathChanged.emit(path)
    
    def _restoreDefaultPath(self):
        """恢复默认路径"""
        self.inputPathEdit.clear()
        self.config_manager.set("global_input_path", "")
        self.restoreDefaultPath.emit()
    
    def _browseDirectory(self):
        """浏览目录"""
        current_path = self.inputPathEdit.text() or ""
        directory = QFileDialog.getExistingDirectory(
            self, 
            self._get_text("select_directory") or "Select Directory",
            current_path
        )
        if directory:
            self.inputPathEdit.setText(directory)
            self._saveGlobalInputPath()
    
    def updatePath(self, path):
        """更新路径显示"""
        self.inputPathEdit.setText(path) 