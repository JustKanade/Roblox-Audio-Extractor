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
    FluentIcon, setThemeColor, CustomColorSettingCard
)

# 默认翻译，如果lang未初始化时使用
DEFAULT_TRANSLATIONS = {
    "theme_color_settings": "主题颜色设置",
    "theme_color_description": "更改应用程序的主题颜色",
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

def get_text(key):
    """获取翻译文本，如果lang未初始化则使用默认值"""
    if lang and hasattr(lang, 'get'):
        return lang.get(key)
    return DEFAULT_TRANSLATIONS.get(key, key)
    

class CustomThemeColorCard(CustomColorSettingCard):
    """主题颜色设置卡片 - 采用官方标准实现"""

    def __init__(self, config_manager, parent=None):
        """初始化主题颜色设置卡片
        
        Args:
            config_manager: 配置管理器实例
            parent: 父控件
        """
        self.config_manager = config_manager
        
        # 使用官方标准实现：直接传递配置项给CustomColorSettingCard
        super().__init__(
            configItem=config_manager.cfg.themeColor,  # 直接使用配置管理器的颜色配置项
            icon=FluentIcon.PALETTE,
            title=get_text("theme_color_settings"),
            content=get_text("theme_color_description"),
            parent=parent
        )
        
        # 连接颜色变更信号 - 官方标准实现
        self.colorChanged.connect(lambda color: setThemeColor(color))
        
        # 延迟翻译组件内部文本
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, lambda: self._translateFluentWidgetsTexts())
        
        logger.debug("CustomThemeColorCard初始化完成 - 使用官方标准实现")
    
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
            for label in self.findChildren(QLabel):
                text = label.text()
                if text in FLUENT_TRANSLATIONS:
                    logger.debug(f"翻译标签: '{text}' -> '{FLUENT_TRANSLATIONS[text]}'")
                    label.setText(FLUENT_TRANSLATIONS[text])
            
            # 翻译按钮文本
            for button in self.findChildren(QPushButton):
                text = button.text()
                if text in FLUENT_TRANSLATIONS:
                    logger.debug(f"翻译按钮: '{text}' -> '{FLUENT_TRANSLATIONS[text]}'")
                    button.setText(FLUENT_TRANSLATIONS[text])
            
            # 翻译单选按钮文本
            for radio in self.findChildren(QRadioButton):
                text = radio.text()
                if text in FLUENT_TRANSLATIONS:
                    logger.debug(f"翻译单选按钮: '{text}' -> '{FLUENT_TRANSLATIONS[text]}'")
                    radio.setText(FLUENT_TRANSLATIONS[text])
                    
            logger.debug("已完成 PyQt-Fluent-Widgets 组件内部文本翻译")
        except Exception as e:
            logger.error(f"翻译 PyQt-Fluent-Widgets 组件内部文本时出错: {e}")
        