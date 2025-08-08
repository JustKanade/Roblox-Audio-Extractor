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

from src.logging.central_log_handler import CentralLogHandler
from src.management.language_management.language_manager import apply_language

# 尝试导入可能的卡片组件
try:
    from src.components.cards.Settings.custom_theme_color_card import CustomThemeColorCard
except ImportError:
    CustomThemeColorCard = None

try:
    from src.components.cards.Settings.version_check_card import VersionCheckCard, set_language_manager
except ImportError:
    VersionCheckCard = None
    set_language_manager = None

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
    from src.components.cards.Settings.launch_file_card import LaunchFileCard
except ImportError:
    LaunchFileCard = None

class SettingsInterface(QWidget):
    """设置界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None, version=None):
        super().__init__(parent)
        self.setObjectName("settingsInterface")
        self.config_manager = config_manager
        self.lang = lang
        self.version = version
        self._parent_window = parent
        
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
        language_options = ["跟随系统设置", "简体中文", "English"]
        self.languageConfig = OptionsConfigItem(
            "Language", "language", "跟随系统设置", OptionsValidator(language_options)
        )
        
        # 主题配置项  
        theme_options = ["深色", "浅色", "跟随系统"]
        self.themeConfig = OptionsConfigItem(
            "Theme", "theme", "深色", OptionsValidator(theme_options)
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
            self.languageConfig, self.themeConfig, self.threadsConfig,
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
            
    def _get_language_display_name(self, language_code):
        """将语言代码转换为显示名称"""
        if language_code == "zh":
            return "简体中文"
        elif language_code == "en":
            return "English"
        else:  # "auto" or any other value
            return "跟随系统设置"
            
    def _get_current_language_name(self):
        """获取当前语言显示名称"""
        if self.lang:
            return self.lang.get_language_name()
        return "跟随系统设置"
            
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
        log_card = CardWidget()
        log_card.setFixedHeight(250)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(self.get_text("recent_activity"))
        log_layout.addWidget(log_title)

        self.settingsLogText = TextEdit()
        self.settingsLogText.setReadOnly(True)
        self.settingsLogText.setFixedHeight(170)
        log_layout.addWidget(self.settingsLogText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.settingsLogHandler = LogHandler(self.settingsLogText)
        
    def createSettingGroups(self, layout):
        """创建设置卡片组"""
        
        # 应用设置组
        app_group = SettingCardGroup(self.get_text("app_settings"))
        self.createAppSettingsCards(app_group)
        layout.addWidget(app_group)
        
        # 界面设置组
        ui_group = SettingCardGroup(self.get_text("interface_settings") or "界面设置")
        self.createUISettingsCards(ui_group)
        layout.addWidget(ui_group)
        
        # 性能设置组
        performance_group = SettingCardGroup(self.get_text("performance_settings") or "性能设置")
        self.createPerformanceSettingsCards(performance_group)
        layout.addWidget(performance_group)
        
        # 输出设置组
        output_group = SettingCardGroup(self.get_text("output_settings"))
        self.createOutputSettingsCards(output_group)
        layout.addWidget(output_group)
        
        # 系统信息组
        system_group = SettingCardGroup(self.get_text("system_info") or "系统信息")
        self.createSystemInfoCards(system_group)
        layout.addWidget(system_group)
    
    def createAppSettingsCards(self, group):
        """创建应用设置卡片"""
        
        # Debug模式设置
        debug_card = SwitchSettingCard(
            FluentIcon.CODE,
            self.get_text("debug_mode") or "调试模式",
            self.get_text("debug_mode_description") or "启用调试模式以获取详细日志",
            self.debugModeConfig
        )
        debug_card.checkedChanged.connect(self.onDebugModeChanged)
        group.addSettingCard(debug_card)
        
        # 浏览崩溃日志文件夹
        crash_logs_card = SettingCard(
            FluentIcon.FOLDER,
            self.get_text("open_error_logs_folder") or "打开错误日志文件夹",
            self.get_text("error_logs_folder_description") or "查看程序崩溃时生成的详细日志"
        )
        
        # 创建右侧内容容器 - 水平布局（参考Launch File卡片的实现）
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)  # 添加右边距避免超出边框
        content_layout.setSpacing(8)
        
        # 添加浏览按钮
        browse_button = PushButton(FluentIcon.FOLDER_ADD, self.get_text("browse") or "浏览")
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
            self.get_text("always_on_top") or "总是置顶",
            self.get_text("always_on_top_description") or "窗口始终保持在其他窗口之上",
            self.alwaysOnTopConfig
        )
        always_on_top_card.checkedChanged.connect(self.onAlwaysOnTopChanged)
        group.addSettingCard(always_on_top_card)
        
        # 问候语设置
        greeting_card = SwitchSettingCard(
            FluentIcon.HEART,
            self.get_text("greeting_setting") or "问候语",
            self.get_text("greeting_setting_description") or "启用启动时的问候通知",
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
            self.get_text("current_language") or "当前语言",
            self.get_text("language_description") or "选择界面语言",
            ["跟随系统设置", "简体中文", "English"]
        )
        language_card.optionChanged.connect(self.onLanguageChanged)
        group.addSettingCard(language_card)
        
        # 主题设置
        theme_card = OptionsSettingCard(
            self.themeConfig,
            FluentIcon.BRUSH,
            self.get_text("theme_settings") or "主题设置",
            self.get_text("theme_description") or "选择应用主题",
            ["深色", "浅色", "跟随系统"]
        )
        theme_card.optionChanged.connect(self.onThemeChanged)
        group.addSettingCard(theme_card)
        
        # 自定义主题颜色卡片
        if CustomThemeColorCard is not None:
            self.themeColorCard = CustomThemeColorCard(self.config_manager)
            group.addSettingCard(self.themeColorCard)
        
        # 亚克力效果设置 - 使用标准的 SwitchSettingCard
        acrylic_card = SwitchSettingCard(
            FluentIcon.TRANSPARENT,
            self.get_text("acrylic_effect") or "亚克力效果",
            self.get_text("acrylic_effect_desc") or "控制导航栏的半透明亚克力效果",
            self.config_manager.cfg.acrylicEnabled if self.config_manager else None
        )
        acrylic_card.checkedChanged.connect(self.onAcrylicToggled)
        group.addSettingCard(acrylic_card)
        self.acrylicCard = acrylic_card
    
    def createPerformanceSettingsCards(self, group):
        """创建性能设置卡片"""
        
        # 默认线程数设置
        if ThreadCountCard is not None:
            threads_card = ThreadCountCard(self.config_manager)
            threads_card.valueChanged.connect(self.saveThreadsConfig)
            group.addSettingCard(threads_card)
        else:
            # 降级到原来的RangeSettingCard
            threads_card = RangeSettingCard(
                self.threadsConfig,
                FluentIcon.SPEED_OFF,
                self.get_text("default_threads") or "默认线程数",
                self.get_text("threads_description") or "设置提取任务的默认线程数"
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
            self.get_text("browse") or "浏览",
            FluentIcon.FOLDER_ADD,
            self.get_text("custom_output_dir") or "自定义输出目录",
            self.config_manager.get("custom_output_dir", "") if self.config_manager else ""
        )
        output_dir_card.clicked.connect(self.browseOutputDirectory)
        group.addSettingCard(output_dir_card)
        self.customOutputDirCard = output_dir_card
        
        # 保存日志选项
        save_logs_card = SwitchSettingCard(
            FluentIcon.SAVE,
            self.get_text("save_logs") or "保存日志",
            self.get_text("save_logs_description") or "将日志保存到文件",
            self.saveLogsConfig
        )
        save_logs_card.checkedChanged.connect(self.toggleSaveLogs)
        group.addSettingCard(save_logs_card)
        
        # 自动打开输出目录选项
        auto_open_card = SwitchSettingCard(
            FluentIcon.FOLDER,
            self.get_text("auto_open_output_dir") or "自动打开输出目录",
            self.get_text("auto_open_description") or "提取完成后自动打开输出目录",
            self.autoOpenConfig
        )
        auto_open_card.checkedChanged.connect(self.toggleAutoOpenOutputDir)
        group.addSettingCard(auto_open_card)
    
    def createSystemInfoCards(self, group):
        """创建系统信息卡片"""
        
        # 版本检测卡片
        if VersionCheckCard is not None:
            current_version = self.version or ""
            self.versionCheckCard = VersionCheckCard(self.config_manager, current_version)
            group.addSettingCard(self.versionCheckCard)
        
        # FFmpeg状态检测卡片
        if FFmpegStatusCard is not None:
            self.ffmpegStatusCard = FFmpegStatusCard()
            group.addSettingCard(self.ffmpegStatusCard)
        
        # 头像设置 - 简化为开关
        avatar_card = SwitchSettingCard(
            FluentIcon.GLOBE,
            self.get_text("avatar_settings") or "头像设置",
            self.get_text("disable_avatar_auto_update") or "禁用侧边栏头像自动更新",
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
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.info(f"总是置顶: {'启用' if isChecked else '禁用'}")
            
            # 应用窗口置顶设置
            if self._parent_window:
                if isChecked:
                    self._parent_window.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                else:
                    self._parent_window.setWindowFlag(Qt.WindowStaysOnTopHint, False)
                self._parent_window.show()
    
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
        theme_value = qconfig.get(config_item)
        # 调用父窗口的onThemeChanged方法
        if self._parent_window and hasattr(self._parent_window, 'onThemeChanged'):
            self._parent_window.onThemeChanged(theme_value)
    
    def onAvatarSettingChanged(self, isChecked):
        """头像设置改变事件"""
        if self.config_manager:
            self.config_manager.set("disable_avatar_auto_update", isChecked)
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.info(f"禁用头像自动更新: {'启用' if isChecked else '禁用'}")

    def updateLaunchFile(self, path):
        """更新启动文件路径"""
        if not self.config_manager:
            return
            
        self.config_manager.set("launch_file", path)
        
        # 显示成功消息
        if hasattr(self, 'settingsLogHandler'):
            if path:
                self.settingsLogHandler.success(f"启动文件已更新: {path}")
            else:
                self.settingsLogHandler.info("启动文件已清除")
        
        # qconfig系统会自动保存配置，无需手动调用save_config
        
    def clearLaunchFile(self):
        """清除启动文件路径"""
        if not self.config_manager:
            return
            
        self.config_manager.set("launch_file", "")
        
        # 显示成功消息
        if hasattr(self, 'settingsLogHandler'):
            self.settingsLogHandler.info("启动文件已清除")
        
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
                    
    def browseOutputDirectory(self):
        """浏览输出目录对话框"""
        current_path = self.customOutputDirCard.contentLabel.text() if hasattr(self.customOutputDirCard, 'contentLabel') else ""
        directory = QFileDialog.getExistingDirectory(self, self.get_text("directory") or "选择目录", current_path)
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
            self.settingsLogHandler.success(f"全局输入路径已更新: {path}")
            
        # 保存配置
        self.config_manager.save_config()
        
    def restoreDefaultInputPath(self):
        """恢复默认输入路径"""
        # 获取默认的Roblox路径
        default_roblox_dir = get_roblox_default_dir()
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
        # 设置各个卡片模块的语言变量
        try:
            import src.components.cards.Settings.custom_theme_color_card as custom_theme_color_card_module
            if self.lang:
                custom_theme_color_card_module.lang = self.lang
        except ImportError:
            pass
            
        try:
            import src.components.cards.Settings.version_check_card as version_check_card_module
            if self.lang:
                version_check_card_module.lang = self.lang
                # 使用新的set_language_manager函数设置语言
                if hasattr(version_check_card_module, 'set_language_manager'):
                    version_check_card_module.set_language_manager(self.lang)
        except ImportError:
            pass
            
        try:
            import src.components.cards.Settings.ffmpeg_status_card as ffmpeg_status_card_module
            if self.lang:
                ffmpeg_status_card_module.lang = self.lang
        except ImportError:
            pass
            
        try:
            import src.components.cards.Settings.global_input_path_card as global_input_path_card_module
            if self.lang:
                global_input_path_card_module.lang = self.lang
        except ImportError:
            pass
            
        try:
            import src.components.cards.Settings.launch_file_card as launch_file_card_module
            if self.lang:
                launch_file_card_module.lang = self.lang
        except ImportError:
            pass 