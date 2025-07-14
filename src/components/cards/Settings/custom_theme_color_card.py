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

# 尝试导入 PyQt-Fluent-Widgets
try:
    from qfluentwidgets import (
        CardWidget, SettingCard, PushButton, FluentIcon,
        setThemeColor, ColorConfigItem, ColorValidator, ColorSerializer
    )
    # 尝试从settings包中导入CustomColorSettingCard
    try:
        from qfluentwidgets.components.settings import CustomColorSettingCard
        HAS_FLUENT_WIDGETS = True
    except ImportError:
        # 尝试从另一个位置导入
        try:
            from qfluentwidgets import CustomColorSettingCard
            HAS_FLUENT_WIDGETS = True
        except ImportError:
            HAS_FLUENT_WIDGETS = False
            print("警告：无法导入 CustomColorSettingCard 组件，将使用基本版本的主题颜色设置卡片")
except ImportError:
    HAS_FLUENT_WIDGETS = False
    print("警告：无法导入 qfluentwidgets 模块，将使用基本版本的主题颜色设置卡片")

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
DEFAULT_THEME_COLOR = "#ff893f"

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
            
            # 延迟翻译组件内部文本
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._translateFluentWidgetsTexts())
            
        except Exception as e:
            print(f"创建 Fluent 界面时出错: {e}")
            # 如果出错，回退到基本界面
            self.setupBasicUI()
            
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
        
        # 自定义颜色部分 - 使用QWidget容器
        self.custom_color_container = QWidget()
        self.custom_color_container.setMaximumHeight(0)  # 初始高度为0
        self.custom_color_layout = QVBoxLayout(self.custom_color_container)
        self.custom_color_layout.setContentsMargins(20, 0, 0, 0)
        self.custom_color_layout.setSpacing(16)
        
        # 设置初始透明度
        if self.useCustom:
            self.custom_color_container.setWindowOpacity(1.0)
        else:
            self.custom_color_container.setWindowOpacity(0.0)
        
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
        
        # 确保容器正确计算高度
        self.custom_color_container.adjustSize()
        self.preferredHeight = self.custom_color_container.sizeHint().height()
        
        # 初始化动画
        self._setupAnimations()
        
        layout.addWidget(self.custom_color_container)
        
        # 设置初始状态
        if self.useCustom:
            self.custom_radio.setChecked(True)
            self.custom_color_container.setMaximumHeight(self.preferredHeight)
            self.custom_color_container.setEnabled(True)
        else:
            self.default_radio.setChecked(True)
            self.custom_color_container.setMaximumHeight(0)
            self.custom_color_container.setEnabled(False)
        
        # 连接信号
        self.button_group.buttonClicked.connect(self.onRadioButtonClicked)
        
    def _setupAnimations(self):
        """初始化动画对象"""
        # 高度动画
        self.animation = QPropertyAnimation(self.custom_color_container, b"maximumHeight")
        
        # 透明度动画
        self.opacityAnimation = QPropertyAnimation(self.custom_color_container, b"windowOpacity")
    
    def onRadioButtonClicked(self, button):
        """处理单选按钮点击事件"""
        if not hasattr(self, 'default_radio'):
            return
            
        # 确定是否选择了自定义颜色
        use_custom = button == self.custom_radio
        
        # 停止正在运行的动画
        if self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()
        if self.opacityAnimation.state() == QPropertyAnimation.Running:
            self.opacityAnimation.stop()
            
        # 设置动画起始值
        self.animation.setStartValue(self.custom_color_container.maximumHeight())
        
        if use_custom:
            # 展开容器
            self.animation.setDuration(200)  # 展开时使用较快的动画
            self.animation.setEasingCurve(QEasingCurve.OutCubic)
            self.animation.setEndValue(self.preferredHeight)
            
            self.opacityAnimation.setDuration(220)
            self.opacityAnimation.setEasingCurve(QEasingCurve.OutCubic)
            self.opacityAnimation.setStartValue(0.0 if self.custom_color_container.maximumHeight() == 0 else self.custom_color_container.windowOpacity())
            self.opacityAnimation.setEndValue(1.0)
            
            # 在动画开始前设置为可用状态，确保内容正常显示
            self.custom_color_container.setEnabled(True)
            self.custom_color_container.show()
        else:
            # 收起容器 - 使用更长的动画时间和不同的缓动曲线
            self.animation.setDuration(180)  # 收起时稍快一些
            self.animation.setEasingCurve(QEasingCurve.InCubic)  # 使用InCubic，开始快结束慢
            self.animation.setEndValue(0)
            
            self.opacityAnimation.setDuration(160)  # 透明度变化更快，先于高度完成
            self.opacityAnimation.setEasingCurve(QEasingCurve.InQuad)
            self.opacityAnimation.setStartValue(self.custom_color_container.windowOpacity())
            self.opacityAnimation.setEndValue(0.0)
            
            # 断开之前可能连接的信号
            try:
                self.animation.finished.disconnect()
            except TypeError:
                pass  # 如果没有连接的信号，会抛出TypeError
                
            # 在动画完成后再禁用，避免内容提前消失
            self.animation.finished.connect(lambda: self.custom_color_container.setEnabled(False))
        
        # 启动动画
        self.animation.start()
        self.opacityAnimation.start()
        
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
        
        # 手动触发配置同步，确保切换状态同步到PyQt-Fluent-Widgets配置文件
        try:
            self.config_manager.sync_theme_to_qfluent()
        except Exception as e:
            print(f"同步主题色配置时出错: {e}")
    
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
        
        # 明确设置使用自定义颜色标志为True
        self.useCustom = True
        self.config_manager.set("use_custom_theme_color", True)
        print(f"已将use_custom_theme_color设置为True")
        
        # 确保选择了自定义颜色选项
        if hasattr(self, 'custom_radio'):
            self.custom_radio.setChecked(True)
            
            # 如果容器已隐藏，平滑展开它
            if self.custom_color_container.maximumHeight() == 0:
                # 停止正在运行的动画
                if self.animation.state() == QPropertyAnimation.Running:
                    self.animation.stop()
                if self.opacityAnimation.state() == QPropertyAnimation.Running:
                    self.opacityAnimation.stop()
                
                # 设置动画
                self.animation.setDuration(200)  # 展开时使用较快的动画
                self.animation.setEasingCurve(QEasingCurve.OutCubic)
                self.animation.setStartValue(0)
                self.animation.setEndValue(self.preferredHeight)
                
                self.opacityAnimation.setDuration(220)
                self.opacityAnimation.setEasingCurve(QEasingCurve.OutCubic)
                self.opacityAnimation.setStartValue(0.0)
                self.opacityAnimation.setEndValue(1.0)
                
                # 确保容器可见
                self.custom_color_container.setEnabled(True)
                self.custom_color_container.show()
                
                # 启动动画
                self.animation.start()
                self.opacityAnimation.start()
        
        # 更新颜色指示器（如果存在）
        if hasattr(self, 'color_indicator'):
            self.color_indicator.setStyleSheet(
                f"background-color: {color.name()}; border-radius: 6px; border: 1px solid rgba(0, 0, 0, 0.1);"
            )
        
        # 应用主题颜色
        self.applyThemeColor(color)
        
        # 确保即时同步到QFluentWidgets配置文件
        self.config_manager.sync_theme_to_qfluent()
        print(f"已更新并同步自定义主题色: {color.name()}, use_custom_theme_color=True")
    
    def applyThemeColor(self, color):
        """应用主题颜色"""
        if not color.isValid():
            logger.warning(f"无效的颜色值: {color.name()}")
            return
            
        logger.debug(f"正在应用主题颜色: {color.name()}")
            
        # 使用安全的方式应用主题颜色
        try:
            # 首先确保配置文件已同步
            try:
                # 更新内部状态
                self.useCustom = True
                self.config_manager.set("use_custom_theme_color", True)
                self.config_manager.set("theme_color", color.name())
                
                # 同步到QFluentWidgets配置
                self.config_manager.sync_theme_to_qfluent()
                logger.debug("已同步主题色到QFluentWidgets配置文件")
            except Exception as e:
                logger.error(f"同步主题色到QFluentWidgets配置文件时出错: {e}")
                
            if HAS_FLUENT_WIDGETS:
                # 直接使用 PyQt-Fluent-Widgets 的函数
                # 确保颜色格式正确
                color_str = color.name()
                if len(color_str) == 7:  # #RRGGBB 格式
                    color_with_alpha = QColor(f"#ff{color_str[1:]}")
                    setThemeColor(color_with_alpha)
                    logger.debug(f"已通过qfluentwidgets.setThemeColor成功应用主题色: {color_with_alpha.name()}")
                else:
                    setThemeColor(color)
                    logger.debug(f"已通过qfluentwidgets.setThemeColor成功应用主题色: {color.name()}")
                
                # 不再强制重新加载配置，直接使用setThemeColor已经足够
                # 这样可以确保动画流程不被中断
                
            else:
                # 尝试获取全局函数
                import sys
                module = sys.modules.get('qfluentwidgets', None)
                if module and hasattr(module, 'setThemeColor'):
                    module.setThemeColor(color)
                    logger.debug(f"已通过sys.modules['qfluentwidgets']应用主题色: {color.name()}")
                else:
                    logger.warning("无法找到setThemeColor函数，主题色可能未成功应用")
            
            # 确保颜色也保存在本地配置中
            self.config_manager.set("theme_color", color.name())
            self.config_manager.set("use_custom_theme_color", True)
            self.config_manager.save_config()
            logger.debug(f"已将主题色 {color.name()} 保存到本地配置")
            
            # 发送颜色变更信号
            self.colorChanged.emit(color)
            logger.debug(f"已发出colorChanged信号: {color.name()}")
        except Exception as e:
            logger.error(f"应用主题颜色时出错: {e}")
        