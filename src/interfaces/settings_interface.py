#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QFileDialog
)
from PyQt5.QtCore import Qt

from qfluentwidgets import (
    CardWidget, BodyLabel, TitleLabel, StrongBodyLabel,
    ScrollArea, PushButton, PrimaryPushButton, 
    FluentIcon, CaptionLabel, TextEdit, IconWidget,
    ComboBox, SpinBox, LineEdit, SwitchButton,
    SettingCardGroup, SettingCard, SwitchSettingCard, ComboBoxSettingCard,
    RangeSettingCard, PushSettingCard, HyperlinkCard,
    OptionsSettingCard, ExpandSettingCard, ConfigItem,
    BoolValidator, OptionsConfigItem, OptionsValidator,
    RangeConfigItem, RangeValidator, qconfig
)

import os
import sys
import subprocess
import multiprocessing
from functools import partial

from src.utils.log_utils import LogHandler
from src.components.cards.recent_activity_card import RecentActivityCard

from src.logging.central_log_handler import CentralLogHandler
from src.management.language_management.language_manager import apply_language
from src.config.config_manager import isWin11
from src.management.theme_management.interface_theme_mixin import InterfaceThemeMixin



        
# 尝试导入可能的卡片组件
try:
    from src.components.cards.Settings.custom_theme_color_card import CustomThemeColorCard
except ImportError:
    CustomThemeColorCard = None

try:
    from src.components.cards.Settings.auto_check_update_card import AutoCheckUpdateCard
except ImportError:
    AutoCheckUpdateCard = None

try:
    from src.components.cards.Settings.manual_check_update_card import ManualCheckUpdateCard
except ImportError:
    ManualCheckUpdateCard = None

try:
    from src.components.cards.Settings.ffmpeg_status_card import FFmpegStatusCard
except ImportError:
    FFmpegStatusCard = None

try:
    from src.components.cards.Settings.log_control_card import LogControlCard
except ImportError:
    LogControlCard = None

try:
    from src.components.cards.Settings.global_input_path_card import GlobalInputPathCard
except ImportError:
    GlobalInputPathCard = None

try:
    from src.components.cards.Settings.thread_count_card import ThreadCountCard
except ImportError:
    ThreadCountCard = None

try:
    from src.components.cards.Settings.multiprocessing_card import MultiprocessingCard, MultiprocessingStrategyCard
except ImportError:
    MultiprocessingCard = None
    MultiprocessingStrategyCard = None

try:
    from src.components.cards.Settings.launch_file_card import LaunchFileCard
except ImportError:
    LaunchFileCard = None

class SettingsInterface(QWidget, InterfaceThemeMixin):
    """设置界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None, version=None):
        super().__init__(parent)
        self.setObjectName("settingsInterface")
        self.config_manager = config_manager
        self.lang = lang
        self.version = version
        self._parent_window = parent
        
        # 获取路径管理器
        self.path_manager = getattr(config_manager, 'path_manager', None) if config_manager else None
        
        # 确保语言对象存在，否则创建空的语言处理函数
        if self.lang is None:
            # 创建一个返回键名的函数
            self.get_text = lambda key, *args: key
        else:
            # 使用lang对象的get方法
            self.get_text = self.lang.get
        
        # 创建配置项
        self.createConfigItems()
        
        # 初始化界面
        self.initUI()
        
    def _get_language_options(self):
        """获取语言选项的翻译文本"""
        return [
            self.get_text("follow_system_language"),
            self.get_text("simplified_chinese"),
            self.get_text("english")
        ]
    
    def _get_theme_options(self):
        """获取主题选项的翻译文本"""
        return [
            self.get_text("theme_dark"),
            self.get_text("theme_light"),
            self.get_text("theme_system")
        ]
        
    def _get_zoom_options(self):
        """获取界面缩放选项的翻译文本"""
        return [
            "100%", "125%", "150%", "175%", "200%",
            self.get_text("use_system_setting")
        ]
            
    def createConfigItems(self):
        """创建配置项"""
        # Debug模式配置项
        self.debugModeConfig = ConfigItem(
            "DebugMode", "debug_mode", False, BoolValidator()
        )
        
        # 总是置顶配置项
        self.alwaysOnTopConfig = ConfigItem(
            "AlwaysOnTop", "always_on_top", False, BoolValidator()
        )
        
        # 问候语配置项
        self.greetingConfig = ConfigItem(
            "GreetingEnabled", "greeting_enabled", True, BoolValidator()
        )
        
        # 语言配置项
        language_options = self._get_language_options()
        self.languageConfig = OptionsConfigItem(
            "Language", "language", self.get_text("follow_system_language"), OptionsValidator(language_options)
        )
        
        # 主题配置项  
        theme_options = self._get_theme_options()
        self.themeConfig = OptionsConfigItem(
            "Theme", "theme", self.get_text("theme_dark"), OptionsValidator(theme_options)
        )
        
        # 界面缩放配置项
        zoom_options = self._get_zoom_options()
        self.zoomConfig = OptionsConfigItem(
            "DpiScale", "dpi_scale", self.get_text("use_system_setting"), OptionsValidator(zoom_options)
        )
        
        # 线程数配置项
        default_threads = min(32, multiprocessing.cpu_count() * 2)
        self.threadsConfig = RangeConfigItem(
            "Threads", "threads", default_threads, RangeValidator(1, 128)
        )
        
        # 保存日志配置项
        self.saveLogsConfig = ConfigItem(
            "SaveLogs", "save_logs", False, BoolValidator()
        )
        
        # 自动打开输出目录配置项
        self.autoOpenConfig = ConfigItem(
            "AutoOpenOutputDir", "auto_open_output_dir", True, BoolValidator()
        )
        
        # 头像设置配置项
        self.avatarConfig = ConfigItem(
            "DisableAvatarAutoUpdate", "disable_avatar_auto_update", False, BoolValidator()
        )
        
        # 将配置项添加到qconfig
        self.config_items = [
            self.debugModeConfig, self.alwaysOnTopConfig, self.greetingConfig,
            self.languageConfig, self.themeConfig, self.zoomConfig, self.threadsConfig,
            self.saveLogsConfig, self.autoOpenConfig, self.avatarConfig
        ]
        
        # 从config_manager加载初始值
        if self.config_manager:
            qconfig.set(self.debugModeConfig, self.config_manager.get("debug_mode", False))
            qconfig.set(self.alwaysOnTopConfig, self.config_manager.get("always_on_top", False))
            qconfig.set(self.greetingConfig, self.config_manager.get("greeting_enabled", True))
            qconfig.set(self.saveLogsConfig, self.config_manager.get("save_logs", False))
            qconfig.set(self.autoOpenConfig, self.config_manager.get("auto_open_output_dir", True))
            qconfig.set(self.avatarConfig, self.config_manager.get("disable_avatar_auto_update", False))
            qconfig.set(self.threadsConfig, self.config_manager.get("threads", default_threads))
            
            # 加载语言配置项
            current_language_display = self._get_language_display_name(self.config_manager.get("language", "auto"))
            qconfig.set(self.languageConfig, current_language_display)
            
            # 加载界面缩放配置项
            current_zoom_display = self._get_zoom_display_name(self.config_manager.get("dpi_scale", "Auto"))
            qconfig.set(self.zoomConfig, current_zoom_display)
            
            # 加载主题配置项
            current_theme_display = self._get_theme_display_name(self.config_manager.get("theme", "auto"))
            qconfig.set(self.themeConfig, current_theme_display)
            
    def _get_language_display_name(self, language_code):
        """将语言代码转换为显示名称"""
        if language_code == "zh":
            return self.get_text("simplified_chinese")
        elif language_code == "en":
            return self.get_text("english")
        else:  # "auto" or any other value
            return self.get_text("follow_system_language")
            
    def _get_theme_display_name(self, theme_value):
        """将主题值转换为显示名称"""
        if theme_value == "dark":
            return self.get_text("theme_dark")
        elif theme_value == "light":
            return self.get_text("theme_light")
        else:  # "auto" or any other value
            return self.get_text("theme_system")
            
    def _get_zoom_display_name(self, zoom_value):
        """将界面缩放值转换为显示名称"""
        if zoom_value == "Auto":
            return self.get_text("use_system_setting")
        elif zoom_value == 1:
            return "100%"
        elif zoom_value == 1.25:
            return "125%"
        elif zoom_value == 1.5:
            return "150%"
        elif zoom_value == 1.75:
            return "175%"
        elif zoom_value == 2:
            return "200%"
        else:
            return self.get_text("use_system_setting")
            
    def _get_current_language_name(self):
        """获取当前语言显示名称"""
        if self.lang:
            return self.lang.get_language_name()
        return self.get_text("follow_system_language")
            
    def initUI(self):
        """初始化设置界面"""
        # 设置模块的全局语言变量
        self.setModulesLang()
        
        # 创建滚动区域
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # 创建设置卡片组
        self.createSettingGroups(content_layout)

        # 日志区域
        self.recent_activity_card = RecentActivityCard(parent=content_widget, lang=self.lang, config_manager=self.config_manager)
        # 保持向后兼容性
        self.settingsLogText = self.recent_activity_card.get_text_edit()

        content_layout.addWidget(self.recent_activity_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.settingsLogHandler = self.recent_activity_card.get_log_handler()
        
        # 应用样式
        self.setInterfaceStyles()
        
    def createSettingGroups(self, layout):
        """创建设置卡片组"""
        
        # 应用设置组
        app_group = SettingCardGroup(self.get_text("app_settings"))
        self.createAppSettingsCards(app_group)
        layout.addWidget(app_group)
        
        # 界面设置组
        ui_group = SettingCardGroup(self.get_text("interface_settings"))
        self.createUISettingsCards(ui_group)
        layout.addWidget(ui_group)
        
        # 性能设置组
        performance_group = SettingCardGroup(self.get_text("performance_settings"))
        self.createPerformanceSettingsCards(performance_group)
        layout.addWidget(performance_group)
        
        # 输出设置组
        output_group = SettingCardGroup(self.get_text("output_settings"))
        self.createOutputSettingsCards(output_group)
        layout.addWidget(output_group)
        
        # 系统信息组
        system_group = SettingCardGroup(self.get_text("system_info_settings"))
        self.createSystemInfoCards(system_group)
        layout.addWidget(system_group)
    
    def createAppSettingsCards(self, group):
        """创建应用设置卡片"""
        
        # Debug模式设置
        debug_card = SwitchSettingCard(
            FluentIcon.CODE,
            self.get_text("debug_mode"),
            self.get_text("debug_mode_description"),
            self.debugModeConfig
        )
        debug_card.checkedChanged.connect(self.onDebugModeChanged)
        group.addSettingCard(debug_card)
        
        # 浏览崩溃日志文件夹
        crash_logs_card = SettingCard(
            FluentIcon.FOLDER,
            self.get_text("open_error_logs_folder"),
            self.get_text("error_logs_folder_description")
        )
        
        # 创建右侧内容容器 - 水平布局（参考Launch File卡片的实现）
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)  # 添加右边距避免超出边框
        content_layout.setSpacing(8)
        
        # 添加浏览按钮
        browse_button = PushButton(FluentIcon.FOLDER_ADD, self.get_text("browse"))
        browse_button.setFixedSize(100, 32)
        browse_button.clicked.connect(self.openCrashLogsFolder)
        
        content_layout.addStretch()  # 添加伸缩空间，让按钮靠右
        content_layout.addWidget(browse_button)
        
        # 将内容容器添加到SettingCard的hBoxLayout
        crash_logs_card.hBoxLayout.addWidget(content_widget)
        
        group.addSettingCard(crash_logs_card)
        
        # 总是置顶设置
        always_on_top_card = SwitchSettingCard(
            FluentIcon.PIN,
            self.get_text("always_on_top"),
            self.get_text("always_on_top_description"),
            self.alwaysOnTopConfig
        )
        always_on_top_card.checkedChanged.connect(self.onAlwaysOnTopChanged)
        group.addSettingCard(always_on_top_card)
        
        # 问候语设置
        greeting_card = SwitchSettingCard(
            FluentIcon.HEART,
            self.get_text("greeting_setting"),
            self.get_text("greeting_setting_description"),
            self.greetingConfig
        )
        greeting_card.checkedChanged.connect(self.onGreetingChanged)
        group.addSettingCard(greeting_card)
        
        # 启动文件设置
        if LaunchFileCard is not None:
            try:
                self.launchFileCard = LaunchFileCard(self.config_manager)
                # 连接启动文件改变信号
                self.launchFileCard.launchFileChanged.connect(self.updateLaunchFile)
                # 连接清除启动文件信号
                self.launchFileCard.clearLaunchFile.connect(self.clearLaunchFile)
                group.addSettingCard(self.launchFileCard)
            except Exception as e:
                print(f"添加启动文件卡片时出错: {e}")
                if hasattr(self, 'settingsLogHandler'):
                    self.settingsLogHandler.error(f"添加启动文件卡片时出错: {e}")
    
    def createUISettingsCards(self, group):
        """创建界面设置卡片"""
        
        # 语言设置
        language_card = OptionsSettingCard(
            self.languageConfig,
            FluentIcon.LANGUAGE,
            self.get_text("current_language"),
            self.get_text("language_description"),
            self._get_language_options()
        )
        language_card.optionChanged.connect(self.onLanguageChanged)
        group.addSettingCard(language_card)
        
        # 主题设置
        theme_card = OptionsSettingCard(
            self.themeConfig,
            FluentIcon.BRUSH,
            self.get_text("theme_settings"),
            self.get_text("theme_description"),
            self._get_theme_options()
        )
        theme_card.optionChanged.connect(self.onThemeChanged)
        group.addSettingCard(theme_card)
        
        # 界面缩放设置
        zoom_card = OptionsSettingCard(
            self.zoomConfig,
            FluentIcon.ZOOM,
            self.get_text("interface_zoom"),
            self.get_text("interface_zoom_description"),
            self._get_zoom_options()
        )
        zoom_card.optionChanged.connect(self.onZoomChanged)
        group.addSettingCard(zoom_card)
        
        # 自定义主题颜色卡片
        if CustomThemeColorCard is not None:
            self.themeColorCard = CustomThemeColorCard(self.config_manager)
            group.addSettingCard(self.themeColorCard)
        
        # 亚克力效果设置 - 使用标准的 SwitchSettingCard
        acrylic_card = SwitchSettingCard(
            FluentIcon.TRANSPARENT,
            self.get_text("acrylic_effect"),
            self.get_text("acrylic_effect_desc"),
            self.config_manager.cfg.acrylicEnabled if self.config_manager else None
        )
        acrylic_card.checkedChanged.connect(self.onAcrylicToggled)
        group.addSettingCard(acrylic_card)
        self.acrylicCard = acrylic_card
        
        # 云母修效果设置 - 仅在 Windows 11 上启用
        mica_card = SwitchSettingCard(
            FluentIcon.BACKGROUND_FILL,
            self.get_text("mica_effect"),
            self.get_text("mica_effect_desc"),
            self.config_manager.cfg.micaEnabled if self.config_manager else None
        )
        mica_card.setEnabled(isWin11())  # 仅在 Windows 11 上启用
        mica_card.checkedChanged.connect(self.onMicaToggled)
        group.addSettingCard(mica_card)
        self.micaCard = mica_card
        
        # 如果不是 Windows 11，显示提示信息
        if not isWin11():
            mica_card.setToolTip(self.get_text("mica_effect_windows11_only"))
    
    def createPerformanceSettingsCards(self, group):
        """创建性能设置卡片"""
        
        # 多进程启用设置
        if MultiprocessingCard is not None:
            multiprocessing_card = MultiprocessingCard(self.config_manager, self.lang)
            multiprocessing_card.valueChanged.connect(self.saveMultiprocessingConfig)
            group.addSettingCard(multiprocessing_card)
            self.multiprocessing_card = multiprocessing_card
        
        # 多进程策略设置
        if MultiprocessingStrategyCard is not None:
            strategy_card = MultiprocessingStrategyCard(self.config_manager, self.lang)
            strategy_card.valueChanged.connect(self.saveMultiprocessingStrategyConfig)
            group.addSettingCard(strategy_card)
            self.strategy_card = strategy_card
            
            # 根据当前多进程状态设置初始可用性
            multiprocessing_enabled = self.config_manager.get("useMultiprocessing", False) if self.config_manager else False
            strategy_card.setEnabled(multiprocessing_enabled)
            
            # 如果多进程未启用，显示提示信息
            if not multiprocessing_enabled:
                strategy_card.setToolTip(self.get_text("multiprocessing_strategy_disabled_tooltip"))
        
        # 默认线程数设置（保留用于多线程模式）
        if ThreadCountCard is not None:
            threads_card = ThreadCountCard(self.config_manager, self.lang)
            threads_card.valueChanged.connect(self.saveThreadsConfig)
            group.addSettingCard(threads_card)
        else:
            # 降级到原来的RangeSettingCard
            threads_card = RangeSettingCard(
                self.threadsConfig,
                FluentIcon.SPEED_OFF,
                self.get_text("default_threads"),
                self.get_text("threads_description")
            )
            threads_card.valueChanged.connect(self.saveThreadsConfig)
            group.addSettingCard(threads_card)
    
    def createOutputSettingsCards(self, group):
        """创建输出设置卡片"""
        
        # 全局输入路径设置
        if GlobalInputPathCard is not None:
            try:
                self.globalInputPathCard = GlobalInputPathCard(self.config_manager)
                # 连接输入路径改变信号到更新路径函数
                self.globalInputPathCard.inputPathChanged.connect(self.updateGlobalInputPath)
                # 连接恢复默认路径信号
                self.globalInputPathCard.restoreDefaultPath.connect(self.restoreDefaultInputPath)
                group.addSettingCard(self.globalInputPathCard)
            except Exception as e:
                print(f"添加全局输入路径卡片时出错: {e}")
                if hasattr(self, 'settingsLogHandler'):
                    self.settingsLogHandler.error(f"添加全局输入路径卡片时出错: {e}")
     
        # 自定义输出目录设置
        output_dir_card = PushSettingCard(
            self.get_text("browse"),
            FluentIcon.FOLDER_ADD,
            self.get_text("custom_output_dir"),
            self.config_manager.get("custom_output_dir", "") if self.config_manager else ""
        )
        # 为按钮设置图标
        output_dir_card.button.setIcon(FluentIcon.FOLDER_ADD.icon())
        output_dir_card.clicked.connect(self.browseOutputDirectory)
        
        group.addSettingCard(output_dir_card)
        self.customOutputDirCard = output_dir_card
        
        # 保存日志选项
        save_logs_card = SwitchSettingCard(
            FluentIcon.SAVE,
            self.get_text("save_logs"),
            self.get_text("save_logs_description"),
            self.saveLogsConfig
        )
        save_logs_card.checkedChanged.connect(self.toggleSaveLogs)
        group.addSettingCard(save_logs_card)
        
        # 自动打开输出目录选项
        auto_open_card = SwitchSettingCard(
            FluentIcon.FOLDER,
            self.get_text("auto_open_output_dir"),
            self.get_text("auto_open_description"),
            self.autoOpenConfig
        )
        auto_open_card.checkedChanged.connect(self.toggleAutoOpenOutputDir)
        group.addSettingCard(auto_open_card)
    
    def createSystemInfoCards(self, group):
        """创建系统信息卡片"""
        
        # 自动检查更新卡片
        if AutoCheckUpdateCard is not None:
            current_version = self.version or ""
            self.autoCheckUpdateCard = AutoCheckUpdateCard(self.config_manager, current_version)
            group.addSettingCard(self.autoCheckUpdateCard)
        
        # 手动检查更新卡片
        if ManualCheckUpdateCard is not None:
            current_version = self.version or ""
            self.manualCheckUpdateCard = ManualCheckUpdateCard(self.config_manager, current_version)
            group.addSettingCard(self.manualCheckUpdateCard)
        
        # FFmpeg状态检测卡片
        if FFmpegStatusCard is not None:
            self.ffmpegStatusCard = FFmpegStatusCard()
            group.addSettingCard(self.ffmpegStatusCard)
        
        # 头像设置 - 简化为开关
        avatar_card = SwitchSettingCard(
            FluentIcon.GLOBE,
            self.get_text("avatar_settings"),
            self.get_text("disable_avatar_auto_update"),
            self.avatarConfig
        )
        avatar_card.checkedChanged.connect(self.onAvatarSettingChanged)
        group.addSettingCard(avatar_card)
        
        # 日志控制卡片
        if LogControlCard is not None:
            log_control_card = LogControlCard(
                parent=self,
                lang=self.lang,
                central_log_handler=CentralLogHandler.getInstance()
            )
            group.addSettingCard(log_control_card)

    # 事件处理方法
    def onDebugModeChanged(self, isChecked):
        """Debug模式改变事件"""
        if self.config_manager:
            self.config_manager.set("debug_mode", isChecked)
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.info(f"调试模式: {'启用' if isChecked else '禁用'}")
    
    def onAlwaysOnTopChanged(self, isChecked):
        """总是置顶改变事件"""
        if self.config_manager:
            self.config_manager.set("always_on_top", isChecked)
            
            # 调用父窗口的方法来应用设置
            if self._parent_window and hasattr(self._parent_window, 'applyAlwaysOnTop'):
                self._parent_window.applyAlwaysOnTop(isChecked)
    
    def onGreetingChanged(self, isChecked):
        """问候语设置改变事件"""
        if self.config_manager:
            self.config_manager.set("greeting_enabled", isChecked)
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.info(f"问候语: {'启用' if isChecked else '禁用'}")
    
    def openCrashLogsFolder(self):
        """打开崩溃日志文件夹"""
        try:
            # 使用统一的崩溃日志路径工具
            from src.utils.log_utils import get_crash_log_dir
            crash_log_dir = get_crash_log_dir()
            
            # 根据操作系统打开文件夹
            if sys.platform == 'win32':
                os.startfile(crash_log_dir)
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', crash_log_dir])
            else:  # Linux
                subprocess.Popen(['xdg-open', crash_log_dir])
            
            # 获取成功消息
            title = "打开文件夹成功"
            content = "已打开错误日志文件夹"
            
            if self.lang and hasattr(self.lang, 'get'):
                title = self.lang.get("open_folder_success") or title
                content = self.lang.get("error_logs_folder_opened") or content
                
            # 显示成功消息
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.success(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        except Exception as e:
            # 获取错误消息
            title = "打开文件夹失败"
            content = f"打开文件夹时出错: {str(e)}"
            
            if self.lang and hasattr(self.lang, 'get'):
                title = self.lang.get("open_folder_failed") or title
                content = self.lang.get("error_opening_folder", str(e)) or content
            
            # 显示错误消息
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.error(
                title=title,
                content=content,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def onLanguageChanged(self, config_item):
        """语言改变事件"""
        # 获取选中的语言
        selected_language = qconfig.get(config_item)
        
        # 获取当前语言名称
        current_language = self._get_current_language_name()
        
        # 调用apply_language函数处理语言变更
        if self.lang:
            try:
                apply_language(
                    window=self._parent_window or self,
                    selected_language=selected_language,
                    current_language=current_language,
                    lang=self.lang,
                    settings_log_handler=getattr(self, 'settingsLogHandler', None)
                )
            except Exception as e:
                # 如果apply_language出错，记录错误并回退到简单的applyLanguage调用
                if hasattr(self, 'settingsLogHandler'):
                    self.settingsLogHandler.error(f"语言设置出错: {e}")
                # 尝试调用父窗口的applyLanguage方法作为后备
                if self._parent_window and hasattr(self._parent_window, 'applyLanguage'):
                    self._parent_window.applyLanguage()
    
    def onThemeChanged(self, config_item):
        """主题改变事件"""
        selected_theme = qconfig.get(config_item)
        
        # 将显示名称转换为配置值
        theme_value = self._get_theme_value_from_display(selected_theme)
        
        if self.config_manager:
            # 保存配置
            self.config_manager.set("theme", theme_value)
        
        # 调用父窗口的onThemeChanged方法，传递显示名称
        if self._parent_window and hasattr(self._parent_window, 'onThemeChanged'):
            self._parent_window.onThemeChanged(selected_theme)
    
    def onZoomChanged(self, config_item):
        """界面缩放改变事件"""
        selected_zoom = qconfig.get(config_item)
        
        # 将显示名称转换为配置值
        zoom_value = self._get_zoom_value_from_display(selected_zoom)
        
        if self.config_manager:
            # 保存配置
            self.config_manager.set("dpi_scale", zoom_value)
            
            # 记录日志
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.info(self.get_text("zoom_changed", selected_zoom))
            
            # 显示重启提示对话框
            self._show_zoom_restart_dialog()
    
    def _get_theme_value_from_display(self, display_name):
        """将主题显示名称转换为配置值"""
        if display_name == self.get_text("theme_dark"):
            return "dark"
        elif display_name == self.get_text("theme_light"):
            return "light"
        else:  # self.get_text("theme_system") or any other value
            return "auto"
            
    def _get_zoom_value_from_display(self, display_name):
        """将显示名称转换为配置值"""
        if display_name == "100%":
            return 1
        elif display_name == "125%":
            return 1.25
        elif display_name == "150%":
            return 1.5
        elif display_name == "175%":
            return 1.75
        elif display_name == "200%":
            return 2
        else:  # "使用系统设置" or "Use system setting"
            return "Auto"
    
    def _show_zoom_restart_dialog(self):
        """显示界面缩放重启对话框"""
        from qfluentwidgets import MessageBox
        
        title = self.get_text("zoom_restart_required")
        content = self.get_text("zoom_restart_message")
        
        dialog = MessageBox(title, content, self)
        dialog.yesButton.setText(self.get_text("yes"))
        dialog.cancelButton.setText(self.get_text("no"))
        
        if dialog.exec():
            # 用户选择关闭应用程序
            if self._parent_window:
                self._parent_window.close()
            else:
                import sys
                sys.exit(0)
    
    def onAvatarSettingChanged(self, isChecked):
        """头像设置改变事件"""
        if self.config_manager:
            self.config_manager.set("disable_avatar_auto_update", isChecked)
            if hasattr(self, 'settingsLogHandler'):
                status_text = self.get_text('enabled') if isChecked else self.get_text('disabled')
                self.settingsLogHandler.info(f"{self.get_text('avatar_auto_update_setting')}: {status_text}")

    def updateLaunchFile(self, path):
        """更新启动文件路径"""
        if not self.config_manager:
            return
            
        self.config_manager.set("launch_file", path)
        
        # 显示成功消息
        if hasattr(self, 'settingsLogHandler'):
            if path:
                self.settingsLogHandler.success(self.get_text("launch_file_updated").format(path))
            else:
                self.settingsLogHandler.info(self.get_text("launch_file_cleared"))
        
        # qconfig系统会自动保存配置，无需手动调用save_config
        
    def clearLaunchFile(self):
        """清除启动文件路径"""
        if not self.config_manager:
            return
            
        self.config_manager.set("launch_file", "")
        
        # 显示成功消息
        if hasattr(self, 'settingsLogHandler'):
            self.settingsLogHandler.info(self.get_text("launch_file_cleared"))
        
        # qconfig系统会自动保存配置，无需手动调用save_config

    def onAcrylicToggled(self, isChecked):
        """亚克力效果设置改变事件"""
        if self.config_manager:
            # 保存到配置
            self.config_manager.cfg.set(self.config_manager.cfg.acrylicEnabled, isChecked)
            
            # 立即应用到导航界面
            if self._parent_window and hasattr(self._parent_window, 'navigationInterface'):
                self._parent_window.navigationInterface.setAcrylicEnabled(isChecked)
            
            # 记录日志
            if hasattr(self, 'settingsLogHandler'):
                status = self.get_text("enabled") if isChecked else self.get_text("disabled")
                self.settingsLogHandler.info(f"{self.get_text('acrylic_effect')}: {status}")

    def onMicaToggled(self, isChecked):
        """云母修效果设置改变事件"""
        if self.config_manager:
            # 保存到配置
            self.config_manager.cfg.set(self.config_manager.cfg.micaEnabled, isChecked)
            
            # 立即应用到主窗口
            if self._parent_window and hasattr(self._parent_window, 'setMicaEffectEnabled'):
                self._parent_window.setMicaEffectEnabled(isChecked)
            
            # 记录日志
            if hasattr(self, 'settingsLogHandler'):
                status = self.get_text("enabled") if isChecked else self.get_text("disabled")
                self.settingsLogHandler.info(f"{self.get_text('mica_effect')}: {status}")

    def saveThreadsConfig(self, value):
        """保存线程数配置"""
        if self.config_manager:
            self.config_manager.set("threads", value)
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.info(self.get_text("saved", f"{self.get_text('default_threads')}: {value}"))
            
            # 同步更新提取界面的线程数设置
            if self._parent_window and hasattr(self._parent_window, 'extractInterface'):
                extract_interface = self._parent_window.extractInterface
                if hasattr(extract_interface, 'updateThreadsValue'):
                    extract_interface.updateThreadsValue()
    
    def saveMultiprocessingConfig(self, value):
        """保存多进程启用配置"""
        if self.config_manager:
            self.config_manager.set("useMultiprocessing", value)
            if hasattr(self, 'settingsLogHandler'):
                status = self.get_text("enabled") if value else self.get_text("disabled")
                self.settingsLogHandler.info(f"{self.get_text('use_multiprocessing', '使用多进程')}: {status}")
            
            # 动态更新多进程策略卡片的可用性
            if hasattr(self, 'strategy_card'):
                self.strategy_card.setEnabled(value)
                if value:
                    # 启用时清除提示信息
                    self.strategy_card.setToolTip("")
                else:
                    # 禁用时显示提示信息
                    self.strategy_card.setToolTip(self.get_text("multiprocessing_strategy_disabled_tooltip"))
    
    def saveMultiprocessingStrategyConfig(self, value):
        """保存多进程策略配置"""
        if self.config_manager:
            self.config_manager.set("conservativeMultiprocessing", value)
            if hasattr(self, 'settingsLogHandler'):
                strategy = self.get_text("conservative_strategy", "保守策略") if value else self.get_text("aggressive_strategy", "激进策略")
                self.settingsLogHandler.info(f"{self.get_text('multiprocessing_strategy', '多进程策略')}: {strategy}")
                    
    def browseOutputDirectory(self):
        """浏览输出目录对话框"""
        current_path = self.customOutputDirCard.contentLabel.text() if hasattr(self.customOutputDirCard, 'contentLabel') else ""
        directory = QFileDialog.getExistingDirectory(self, self.get_text("directory"), current_path)
        if directory and self.config_manager:
            self.customOutputDirCard.setContent(directory)
            self.config_manager.set("custom_output_dir", directory)
            self.config_manager.save_config()
            
            # 显示成功消息
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.success(f"自定义输出目录已设置: {directory}")
                
    def toggleSaveLogs(self, isChecked):
        """切换保存日志选项"""
        if self.config_manager:
            self.config_manager.set("save_logs", isChecked)
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.info(self.get_text("log_save_option_toggled"))
                
    def toggleAutoOpenOutputDir(self, isChecked):
        """切换自动打开输出目录选项"""
        if self.config_manager:
            self.config_manager.set("auto_open_output_dir", isChecked)
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.info(self.get_text("auto_open_toggled"))
                
    def updateGlobalInputPath(self, path):
        """更新全局输入路径"""
        if not self.config_manager:
            return
            
        self.config_manager.set("global_input_path", path)
        
        # 更新所有需要使用这个路径的地方
        # 通知父窗口更新全局输入路径
        if self._parent_window and hasattr(self._parent_window, 'updateGlobalInputPath'):
            self._parent_window.updateGlobalInputPath(path)
        else:
            # 直接在这里更新提取界面
            if self._parent_window and hasattr(self._parent_window, 'extractInterface'):
                extract_interface = self._parent_window.extractInterface
                if hasattr(extract_interface, 'dirInput'):
                    extract_interface.dirInput.setText(path)
            
        # 显示成功消息
        if hasattr(self, 'settingsLogHandler'):
            self.settingsLogHandler.success(f"{self.get_text('global_input_path_updated')}: {path}")
            
        # 保存配置
        self.config_manager.save_config()
        
    def restoreDefaultInputPath(self):
        """恢复默认输入路径"""
        # 使用路径管理器获取默认的Roblox路径
        if self.path_manager:
            default_roblox_dir = self.path_manager.get_roblox_default_dir(force_refresh=True)
        else:
            # 如果路径管理器不可用，记录错误并返回
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.error(self.get_text("path_manager_not_available", "路径管理器不可用"))
            return
            
        if default_roblox_dir and self.config_manager:
            # 更新全局输入路径
            self.config_manager.set("global_input_path", default_roblox_dir)
            self.config_manager.save_config()
            
            # 更新输入框显示
            if hasattr(self, 'globalInputPathCard') and hasattr(self.globalInputPathCard, 'inputPathEdit'):
                self.globalInputPathCard.inputPathEdit.setText(default_roblox_dir)
            
            # 调用更新路径函数
            self.updateGlobalInputPath(default_roblox_dir)
            
            # 显示成功消息
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.success(self.get_text("default_path_restored") + f": {default_roblox_dir}")
                
    def applyLanguage(self):
        """应用语言设置"""
        # 调用父窗口的applyLanguage方法
        if self._parent_window and hasattr(self._parent_window, 'applyLanguage'):
            self._parent_window.applyLanguage()

    def setModulesLang(self):
        """设置各个模块的语言变量"""
        if not self.lang:
            return
            
        # 定义需要设置语言的模块列表
        modules_to_set = [
            'src.components.cards.Settings.custom_theme_color_card',
            'src.components.cards.Settings.auto_check_update_card', 
            'src.components.cards.Settings.manual_check_update_card',
            'src.components.cards.Settings.ffmpeg_status_card',
            'src.components.cards.Settings.global_input_path_card',
            'src.components.cards.Settings.launch_file_card'
        ]
        
        # 统一设置语言管理器
        for module_name in modules_to_set:
            try:
                module = __import__(module_name, fromlist=[''])
                # 设置lang变量
                if hasattr(module, '__dict__'):
                    module.lang = self.lang
                    
                # 如果模块有set_language_manager函数，也调用它
                if hasattr(module, 'set_language_manager'):
                    module.set_language_manager(self.lang)
                    
            except ImportError:
                # 模块不存在时忽略
                continue
            except Exception as e:
                # 记录其他错误但不中断流程
                if hasattr(self, 'settingsLogHandler'):
                    self.settingsLogHandler.warning(f"设置模块语言时出错 {module_name}: {e}") 

    def setInterfaceStyles(self):
        """设置界面样式"""
        # 调用父类的通用样式设置
        super().setInterfaceStyles()
        
        # 获取文本样式，settings界面主要使用通用样式即可
        # 可以在这里添加特定的设置界面样式
        pass 