from PyQt5.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QColorDialog,
    QRadioButton, QButtonGroup, QLabel, QGridLayout,
    QPushButton
)
import logging

# 设置日志记录
logger = logging.getLogger(__name__)

# 尝试导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None
    print("警告：无法导入语言管理器，将使用默认翻译")

# 导入 PyQt-Fluent-Widgets
from qfluentwidgets import (
    CardWidget, SettingCard, PushButton, FluentIcon,
    setThemeColor, ColorConfigItem, ColorValidator, ColorSerializer,
    CustomColorSettingCard
)

# 默认翻译，如果lang未初始化时使用
DEFAULT_TRANSLATIONS = {
    "theme_color_settings": "主题颜色设置",
    "theme_color_default": "默认颜色",
    "theme_color_custom": "自定义颜色",
    "theme_color_choose": "选择颜色"
}

# 添加 PyQt-Fluent-Widgets 组件内部使用的文本翻译
FLUENT_TRANSLATIONS = {
    'Custom color': '自定义颜色',
    'Default color': '默认颜色',
    'Custom': '自定义',
    'Default': '默认',
    'Choose color': '选择颜色',
    'Pick Color': '选择颜色'
}

# 默认主题颜色 - 这个颜色永远不会被修改
DEFAULT_THEME_COLOR = "#e8b3ff"

def get_text(key):
    """获取翻译文本，如果lang未初始化则使用默认值"""
    if lang and hasattr(lang, 'get'):
        return lang.get(key)
    return DEFAULT_TRANSLATIONS.get(key, key)
    

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
        self.setupFluentUI()
        
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
            
            # 延迟翻译组件内部文本
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._translateFluentWidgetsTexts())
            
        except Exception as e:
            logger.error(f"创建 Fluent 界面时出错: {e}")
            
    def _translateFluentWidgetsTexts(self):
        """翻译 PyQt-Fluent-Widgets 组件内部文本"""
        try:
            # 检查当前语言设置
            is_chinese = False
            
            # 尝试从lang模块获取当前语言
            if lang:
                # 检查是否为中文界面
                if hasattr(lang, 'current_language') and hasattr(lang, 'CHINESE'):
                    is_chinese = lang.current_language == lang.CHINESE
                
            logger.debug(f"当前是否为中文界面: {is_chinese}")
            
            if not is_chinese:
                logger.debug("当前不是中文界面，不应用中文翻译")
                return
                
            logger.debug("当前是中文界面，开始应用中文翻译")
            
            # 翻译标签文本
            for label in self.colorCard.findChildren(QLabel):
                text = label.text()
                if text in FLUENT_TRANSLATIONS:
                    logger.debug(f"翻译标签: '{text}' -> '{FLUENT_TRANSLATIONS[text]}'")
                    label.setText(FLUENT_TRANSLATIONS[text])
            
            # 翻译按钮文本
            for button in self.colorCard.findChildren(QPushButton):
                text = button.text()
                if text in FLUENT_TRANSLATIONS:
                    logger.debug(f"翻译按钮: '{text}' -> '{FLUENT_TRANSLATIONS[text]}'")
                    button.setText(FLUENT_TRANSLATIONS[text])
            
            # 翻译单选按钮文本
            for radio in self.colorCard.findChildren(QRadioButton):
                text = radio.text()
                if text in FLUENT_TRANSLATIONS:
                    logger.debug(f"翻译单选按钮: '{text}' -> '{FLUENT_TRANSLATIONS[text]}'")
                    radio.setText(FLUENT_TRANSLATIONS[text])
                    
            logger.debug("已完成 PyQt-Fluent-Widgets 组件内部文本翻译")
        except Exception as e:
            logger.error(f"翻译 PyQt-Fluent-Widgets 组件内部文本时出错: {e}")
    
    def onColorChanged(self, color):
        """当颜色更改时的处理函数"""
        self.updateCustomColor(color)
    
    def updateCustomColor(self, color):
        """更新自定义颜色"""
        # 保存颜色
        self.customColor = color
        
        # 更新配置
        self.config_manager.set("theme_color", color.name())
        self.config_manager.set("use_custom_theme_color", True)
        self.useCustom = True
        
        # 更新界面
        self.applyThemeColor(color)
        
        # 发送颜色变更信号
        self.colorChanged.emit(color)
        
    def applyThemeColor(self, color):
        """应用主题颜色"""
        # 获取颜色名称（格式为 #RRGGBB）
        color_name = color.name()
        
        # 应用到 PyQt-Fluent-Widgets 主题
        try:
            setThemeColor(color)
            logger.debug(f"应用主题颜色: {color_name}")
        except Exception as e:
            logger.error(f"应用主题颜色时出错: {e}")
        
        # 保存当前使用的颜色到配置
        if color == self.defaultColor:
            self.config_manager.set("use_custom_theme_color", False)
        else:
            self.config_manager.set("use_custom_theme_color", True)
            self.config_manager.set("theme_color", color_name)
        