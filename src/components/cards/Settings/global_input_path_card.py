from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFileDialog, QWidget
from PyQt5.QtGui import QKeyEvent

from qfluentwidgets import (
    ExpandSettingCard, LineEdit, PushButton, BodyLabel, 
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


class GlobalInputPathCard(ExpandSettingCard):
    """全局输入路径设置卡片"""
    
    inputPathChanged = pyqtSignal(str)
    restoreDefaultPath = pyqtSignal()
    
    def __init__(self, config_manager, parent=None):
        self.config_manager = config_manager
        
        # 获取翻译文本
        title = ""
        description = ""
        if lang:
            title = lang.get("global_input_path_title") or ""
            description = lang.get("global_input_path_description") or ""
        
        super().__init__(
            FluentIcon.FOLDER,
            title or "全局输入路径",
            description or "设置全局统一的输入路径，将应用于所有提取操作",
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
        # 创建内容控件
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        
        # 当前路径显示
        current_path_label = BodyLabel(self._get_text("current_path") or "当前路径:")
        setFont(current_path_label, 13)
        content_layout.addWidget(current_path_label)
        
        # 输入路径编辑框和浏览按钮的行
        path_row = QHBoxLayout()
        path_row.setSpacing(8)
        
        # 输入路径编辑框
        self.inputPathEdit = CustomLineEdit()
        self.inputPathEdit.setPlaceholderText(self._get_text("press_enter_restore_path") or "按Enter恢复默认Roblox缓存路径")
        self.inputPathEdit.setClearButtonEnabled(True)
        self.inputPathEdit.setText(self.config_manager.get("global_input_path", ""))
        self.inputPathEdit.editingFinished.connect(self._saveGlobalInputPath)
        self.inputPathEdit.enterPressed.connect(self._restoreDefaultPath)
        
        # 浏览按钮
        self.browseButton = PushButton(FluentIcon.FOLDER_ADD, self._get_text("browse") or "浏览")
        self.browseButton.setFixedWidth(80)
        self.browseButton.clicked.connect(self._browseDirectory)
        
        path_row.addWidget(self.inputPathEdit, 1)
        path_row.addWidget(self.browseButton)
        content_layout.addLayout(path_row)
        
        # 提示信息
        hint_label = BodyLabel(self._get_text("path_hint") or "提示：留空将使用默认的Roblox缓存路径")
        hint_label.setStyleSheet("color: gray; font-size: 12px;")
        content_layout.addWidget(hint_label)
        
        # 使用正确的API添加内容
        self.addWidget(content_widget)
    
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
            self._get_text("select_directory") or "选择目录",
            current_path
        )
        if directory:
            self.inputPathEdit.setText(directory)
            self._saveGlobalInputPath()
    
    def updatePath(self, path):
        """更新路径显示"""
        self.inputPathEdit.setText(path) 