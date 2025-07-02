from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFileDialog, QWidget
from PyQt5.QtGui import QKeyEvent

from qfluentwidgets import (
    CardWidget, LineEdit, PushButton, BodyLabel, 
    StrongBodyLabel, FluentIcon, IconWidget
)

# 全局语言对象，将由外部设置
lang = None

class GlobalInputPathCard(CardWidget):
    """全局输入路径设置卡片"""
    
    # 当输入路径改变时发出信号
    inputPathChanged = pyqtSignal(str)
    # 恢复默认路径信号
    restoreDefaultPath = pyqtSignal()
    
    def __init__(self, config_manager, parent=None):
        """
        初始化全局输入路径设置卡片
        
        Parameters:
        -----------
        config_manager: ConfigManager
            配置管理器对象，用于保存和获取配置
        parent: QWidget
            父组件
        """
        super().__init__(parent)
        
        self.config_manager = config_manager
        self._setupUI()
    
    def _setupUI(self):
        """设置UI组件"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        
        # 标题行布局
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # 添加图标
        title_icon = IconWidget(FluentIcon.FOLDER, self)
        title_icon.setFixedSize(16, 16)
        
        # 标题
        title_label = StrongBodyLabel(lang.get("global_input_path_title", "全局输入路径") if lang else "全局输入路径")
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        
        # 添加描述文本
        description = BodyLabel(lang.get("global_input_path_description", "设置全局统一的输入路径，将应用于所有提取操作") if lang else "设置全局统一的输入路径，将应用于所有提取操作")
        description.setWordWrap(True)
        main_layout.addWidget(description)
        
        # 输入路径编辑框和浏览按钮的行
        path_row = QHBoxLayout()
        path_row.setContentsMargins(0, 5, 0, 0)
        path_row.setSpacing(8)
        
        # 输入路径编辑框
        self.inputPathEdit = CustomLineEdit()
        self.inputPathEdit.setPlaceholderText(lang.get("press_enter_restore_path", "按Enter恢复默认Roblox缓存路径") if lang else "按Enter恢复默认Roblox缓存路径")
        self.inputPathEdit.setClearButtonEnabled(True)
        self.inputPathEdit.setText(self.config_manager.get("global_input_path", ""))
        # 文本框编辑完成后自动保存
        self.inputPathEdit.editingFinished.connect(self._saveGlobalInputPath)
        # 连接回车键事件到恢复默认路径函数
        self.inputPathEdit.enterPressed.connect(self._restoreDefaultPath)
        
        # 浏览按钮
        self.browseButton = PushButton(FluentIcon.FOLDER_ADD, lang.get("browse", "浏览") if lang else "浏览")
        self.browseButton.setFixedWidth(80)
        self.browseButton.clicked.connect(self._browseDirectory)
        
        # 将控件添加到布局
        path_row.addWidget(self.inputPathEdit, 1)
        path_row.addWidget(self.browseButton)
        
        main_layout.addLayout(path_row)
    
    def _browseDirectory(self):
        """打开文件夹选择对话框"""
        current_path = self.inputPathEdit.text()
        directory = QFileDialog.getExistingDirectory(
            self, 
            lang.get("select_directory", "选择目录") if lang else "选择目录",
            current_path
        )
        
        if directory:
            self.inputPathEdit.setText(directory)
            self._saveGlobalInputPath()
    
    def _saveGlobalInputPath(self):
        """保存全局输入路径到配置"""
        input_path = self.inputPathEdit.text()
        self.config_manager.set("global_input_path", input_path)
        self.config_manager.save_config()
        
        # 发出路径改变信号
        self.inputPathChanged.emit(input_path)
    
    def _restoreDefaultPath(self):
        """恢复默认路径"""
        # 发出恢复默认路径信号
        self.restoreDefaultPath.emit()


class CustomLineEdit(LineEdit):
    """自定义LineEdit，添加Enter键信号"""
    
    # 定义信号
    enterPressed = pyqtSignal()
    
    def keyPressEvent(self, event: QKeyEvent):
        """重写按键事件，捕获Enter键"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # 发出Enter键信号
            self.enterPressed.emit()
        else:
            # 其他键正常处理
            super().keyPressEvent(event) 