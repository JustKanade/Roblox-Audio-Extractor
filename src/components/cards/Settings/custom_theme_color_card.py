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

# 导入 PyQt-Fluent-Widgets
from qfluentwidgets import (
    FluentIcon, setThemeColor, CustomColorSettingCard
)

# 默认翻译，如果lang未传递时使用
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


class CustomThemeColorCard(CustomColorSettingCard):
    """主题颜色设置卡片 - 采用官方标准实现"""

    def __init__(self, config_manager, lang=None, parent=None):
        """初始化主题颜色设置卡片
        
        Args:
            config_manager: 配置管理器实例
            lang: 语言管理器实例
            parent: 父控件
        """
        self.config_manager = config_manager
        self.lang = lang
        
        # 使用官方标准实现：直接传递配置项给CustomColorSettingCard
        super().__init__(
            configItem=config_manager.cfg.themeColor,  # 直接使用配置管理器的颜色配置项
            icon=FluentIcon.PALETTE,
            title=self._get_text("theme_color_settings"),
            content=self._get_text("theme_color_description"),
            parent=parent
        )
        
        # 连接颜色变更信号 - 官方标准实现
        self.colorChanged.connect(lambda color: setThemeColor(color))
        
        # 延迟翻译组件内部文本
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, lambda: self._translateFluentWidgetsTexts())
        
        logger.debug("CustomThemeColorCard初始化完成 - 使用官方标准实现")
    
    def _get_text(self, key):
        """获取翻译文本"""
        if self.lang and hasattr(self.lang, 'get'):
            return self.lang.get(key, DEFAULT_TRANSLATIONS.get(key, key))
        return DEFAULT_TRANSLATIONS.get(key, key)
    
    def _translateFluentWidgetsTexts(self):
        """翻译 PyQt-Fluent-Widgets 组件内部文本"""
        try:
            # 检查当前语言是否为中文
            if self.lang and hasattr(self.lang, 'current_language'):
                from src.locale.translations import Language
                if self.lang.current_language == Language.CHINESE:
                    # 查找并翻译内部按钮
                    self._findAndTranslateButtons()
        except Exception as e:
            logger.debug(f"翻译组件内部文本时出错: {e}")
    
    def _findAndTranslateButtons(self):
        """查找并翻译按钮文本"""
        try:
            # 递归查找所有QPushButton和QRadioButton
            buttons = self.findChildren(QPushButton) + self.findChildren(QRadioButton)
            
            for button in buttons:
                original_text = button.text()
                if original_text in FLUENT_TRANSLATIONS:
                    button.setText(FLUENT_TRANSLATIONS[original_text])
                    logger.debug(f"翻译按钮文本: '{original_text}' -> '{FLUENT_TRANSLATIONS[original_text]}'")
                    
        except Exception as e:
            logger.debug(f"翻译按钮文本时出错: {e}")
        