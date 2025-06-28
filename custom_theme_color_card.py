from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QColorDialog,
    QRadioButton, QButtonGroup, QLabel, QGridLayout,
    QPushButton
)

# 尝试导入 PyQt-Fluent-Widgets
try:
    from qfluentwidgets import (
        CardWidget, SettingCard, PushButton, FluentIcon,
        setThemeColor, CustomColorSettingCard, ColorConfigItem,
        ColorValidator, ColorSerializer
    )
    HAS_FLUENT_WIDGETS = True
except ImportError:
    HAS_FLUENT_WIDGETS = False
    print("警告：无法导入 qfluentwidgets 模块，将使用基本版本的主题颜色设置卡片")

# 全局语言管理器引用，在主程序中初始化
lang = None

# 默认翻译，如果lang未初始化时使用
DEFAULT_TRANSLATIONS = {
    "theme_color_settings": "主题颜色设置",
    "theme_color_default": "默认颜色",
    "theme_color_custom": "自定义颜色",
    "theme_color_choose": "选择颜色",
    "theme_color_presets": "预设颜色"
}

# 默认主题颜色 - 这个颜色永远不会被修改
DEFAULT_THEME_COLOR = "#29F1FF"

def get_text(key):
    """获取翻译文本，如果lang未初始化则使用默认值"""
    if lang and hasattr(lang, 'get'):
        return lang.get(key)
    return DEFAULT_TRANSLATIONS.get(key, key)

class ColorButton(QWidget):
    """简化的颜色按钮"""
    
    # 定义信号
    colorClicked = pyqtSignal(QColor)
    
    def __init__(self, color, size=30, parent=None):
        super().__init__(parent)
        self.color = color
        self.fixed_size = size  # 避免与QWidget.size()冲突
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(color.name())
        
    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QPen, QBrush
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制颜色方块
        painter.setPen(QPen(Qt.gray, 1))
        painter.setBrush(QBrush(self.color))
        painter.drawRoundedRect(1, 1, self.width()-2, self.height()-2, 4, 4)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 注意：pyqtSignal.emit 在静态类型检查时可能会报错，但实际运行时正常
            self.colorClicked.emit(self.color)
        super().mousePressEvent(event)

class ColorPresetPanel(QWidget):
    """简化的颜色预设面板"""
    
    colorSelected = pyqtSignal(QColor)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUI()
        
    def setupUI(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 精简预设颜色列表
        presets = [
            "#0078d4", "#2d7d9a", "#00b7c3", "#038387", "#00cc6a",
            "#10893e", "#107c10", "#7a7574", "#5c2e91", "#8764b8",
            "#8e562e", "#c74634", "#f7630c", "#ca5010", "#ffaa44"
        ]
        
        row, col = 0, 0
        for color_hex in presets:
            color = QColor(color_hex)
            btn = ColorButton(color)
            btn.colorClicked.connect(self.onButtonClicked)
            layout.addWidget(btn, row, col)
            
            col += 1
            if col >= 5:  # 每行5个颜色
                col = 0
                row += 1
    
    def onButtonClicked(self, color):
        """处理按钮点击事件"""
        # 注意：pyqtSignal.emit 在静态类型检查时可能会报错，但实际运行时正常
        self.colorSelected.emit(color)

class CustomThemeColorCard(QWidget):
    """主题颜色设置卡片"""

    colorChanged = pyqtSignal(QColor)  # 颜色变更信号

    def __init__(self, config_manager, parent=None):
        """初始化主题颜色设置卡片
        
        Args:
            config_manager: 配置管理器实例
            parent: 父控件
        """
        super().__init__(parent)
        self.config_manager = config_manager
        
        # 固定的默认主题颜色，永远不变
        self.defaultColor = QColor(DEFAULT_THEME_COLOR)
        
        # 从配置中读取用户设置
        self.useCustom = self.config_manager.get("use_custom_theme_color", False)
        
        # 读取保存的自定义颜色
        saved_color = self.config_manager.get("theme_color", DEFAULT_THEME_COLOR)
        self.customColor = QColor(saved_color)
        
        # 初始化界面
        if HAS_FLUENT_WIDGETS:
            self.setupFluentUI()
        else:
            self.setupBasicUI()
        
        # 应用当前主题颜色
        self.applyCurrentThemeColor()
    
    def applyCurrentThemeColor(self):
        """应用当前主题颜色（根据用户设置）"""
        if self.useCustom:
            self.applyThemeColor(self.customColor)
        else:
            self.applyThemeColor(self.defaultColor)
    
    def setupFluentUI(self):
        """使用 PyQt-Fluent-Widgets 设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            # 创建颜色配置项，根据 qfluentwidgets 的 API 调整参数
            colorConfigItem = ColorConfigItem(
                group="Appearance", 
                name="ThemeColor", 
                default=self.customColor
            )
            
            # 创建自定义颜色设置卡片
            self.colorCard = CustomColorSettingCard(
                configItem=colorConfigItem,
                icon=FluentIcon.PALETTE,
                title=get_text("theme_color_settings") or "主题颜色设置",
                content="",
                parent=self
            )
            
            # 连接信号
            self.colorCard.colorChanged.connect(self.onColorChanged)
            
            # 添加到布局
            layout.addWidget(self.colorCard)
        except Exception as e:
            print(f"创建 Fluent 界面时出错: {e}")
            # 如果出错，回退到基本界面
            self.setupBasicUI()
        
    def setupBasicUI(self):
        """设置基本界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 添加标题
        title = QLabel(get_text("theme_color_settings") or "主题颜色设置")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 单选按钮组
        self.radio_widget = QWidget()
        self.radio_layout = QVBoxLayout(self.radio_widget)
        self.radio_layout.setContentsMargins(0, 8, 0, 8)
        self.radio_layout.setSpacing(10)
        
        self.default_radio = QRadioButton(get_text("theme_color_default") or "默认颜色")
        self.custom_radio = QRadioButton(get_text("theme_color_custom") or "自定义颜色")
        
        self.radio_layout.addWidget(self.default_radio)
        self.radio_layout.addWidget(self.custom_radio)
        
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.default_radio, 0)
        self.button_group.addButton(self.custom_radio, 1)
        
        layout.addWidget(self.radio_widget)
        
        # 自定义颜色部分
        self.custom_color_container = QWidget()
        self.custom_color_layout = QVBoxLayout(self.custom_color_container)
        self.custom_color_layout.setContentsMargins(20, 0, 0, 0)
        self.custom_color_layout.setSpacing(16)
        
        # 当前颜色选择区域
        current_color_layout = QHBoxLayout()
        current_color_layout.setContentsMargins(0, 0, 0, 0)
        current_color_layout.setSpacing(12)
        
        # 当前自定义颜色指示器
        self.color_indicator = QWidget()
        self.color_indicator.setFixedSize(30, 30)
        self.color_indicator.setStyleSheet(
            f"background-color: {self.customColor.name()}; border-radius: 6px; border: 1px solid rgba(0, 0, 0, 0.1);"
        )
        
        # 选择颜色按钮
        if HAS_FLUENT_WIDGETS:
            self.choose_color_button = PushButton(get_text("theme_color_choose") or "选择颜色")
        else:
            self.choose_color_button = QPushButton(get_text("theme_color_choose") or "选择颜色")
        self.choose_color_button.clicked.connect(self.openColorDialog)
        
        current_color_layout.addWidget(self.color_indicator)
        current_color_layout.addWidget(self.choose_color_button)
        current_color_layout.addStretch(1)
        
        self.custom_color_layout.addLayout(current_color_layout)
        
        # 预设颜色部分
        preset_label = QLabel(get_text("theme_color_presets") or "预设颜色")
        preset_label.setStyleSheet("font-weight: bold;")
        self.custom_color_layout.addWidget(preset_label)
        
        self.presetPanel = ColorPresetPanel()
        self.presetPanel.colorSelected.connect(self.onColorSelected)
        self.custom_color_layout.addWidget(self.presetPanel)
        
        layout.addWidget(self.custom_color_container)
        
        # 设置初始状态
        if self.useCustom:
            self.custom_radio.setChecked(True)
            self.custom_color_container.setEnabled(True)
        else:
            self.default_radio.setChecked(True)
            self.custom_color_container.setEnabled(False)
        
        # 连接信号
        self.button_group.buttonClicked.connect(self.onRadioButtonClicked)
    
    def onRadioButtonClicked(self, button):
        """处理单选按钮点击事件"""
        if not hasattr(self, 'default_radio'):
            return
            
        # 确定是否选择了自定义颜色
        use_custom = button == self.custom_radio
        
        # 更新UI状态
        self.custom_color_container.setEnabled(use_custom)
        
        # 更新内部状态
        self.useCustom = use_custom
        
        # 保存设置
        self.config_manager.set("use_custom_theme_color", use_custom)
        
        # 应用相应的颜色
        if use_custom:
            self.applyThemeColor(self.customColor)
        else:
            # 恢复默认颜色
            self.applyThemeColor(self.defaultColor)
    
    def openColorDialog(self):
        """打开颜色选择对话框"""
        dialog = QColorDialog(self.customColor, self)
        dialog.setOption(QColorDialog.ShowAlphaChannel, False)
        dialog.setWindowTitle(get_text("theme_color_choose") or "选择颜色")
        
        if dialog.exec_():
            color = dialog.selectedColor()
            self.updateCustomColor(color)
    
    def onColorSelected(self, color):
        """处理颜色选择事件"""
        self.updateCustomColor(color)
    
    def onColorChanged(self, color):
        """处理颜色变更事件 (PyQt-Fluent-Widgets)"""
        self.updateCustomColor(color)
        
    def updateCustomColor(self, color):
        """更新自定义颜色"""
        if not color.isValid():
            return
            
        # 更新自定义颜色
        self.customColor = color
        
        # 保存颜色设置
        self.config_manager.set("theme_color", color.name())
        
        # 确保选择了自定义颜色选项
        if hasattr(self, 'custom_radio'):
            if not self.useCustom:
                self.useCustom = True
                self.custom_radio.setChecked(True)
                self.custom_color_container.setEnabled(True)
                self.config_manager.set("use_custom_theme_color", True)
        
        # 更新颜色指示器（如果存在）
        if hasattr(self, 'color_indicator'):
            self.color_indicator.setStyleSheet(
                f"background-color: {color.name()}; border-radius: 6px; border: 1px solid rgba(0, 0, 0, 0.1);"
            )
        
        # 应用主题颜色
        self.applyThemeColor(color)
    
    def applyThemeColor(self, color):
        """应用主题颜色"""
        # 使用安全的方式应用主题颜色
        try:
            if HAS_FLUENT_WIDGETS:
                # 直接使用 PyQt-Fluent-Widgets 的函数
                setThemeColor(color)
            else:
                # 尝试获取全局函数
                import sys
                module = sys.modules.get('qfluentwidgets', None)
                if module and hasattr(module, 'setThemeColor'):
                    module.setThemeColor(color)
            
            # 注意：pyqtSignal.emit 在静态类型检查时可能会报错，但实际运行时正常
            self.colorChanged.emit(color)
        except Exception as e:
            print(f"应用主题颜色时出错: {e}")
        