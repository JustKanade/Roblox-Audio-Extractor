#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
)
from PyQt5.QtCore import Qt

from qfluentwidgets import (
    CardWidget, BodyLabel, TitleLabel, StrongBodyLabel,
    ScrollArea, PushButton, PrimaryPushButton, 
    FluentIcon, CaptionLabel, TextEdit, IconWidget,
    ComboBox, SpinBox, LineEdit, SwitchButton
)

import os
import multiprocessing
from functools import partial

from src.utils.log_utils import LogHandler
from src.utils.file_utils import get_roblox_default_dir
from src.logging.central_log_handler import CentralLogHandler

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
    from src.components.cards.Settings.debug_mode_card import DebugModeCard
except ImportError:
    DebugModeCard = None

try:
    from src.components.cards.Settings.always_on_top_card import AlwaysOnTopCard
except ImportError:
    AlwaysOnTopCard = None

try:
    from src.components.cards.Settings.greeting_setting_card import GreetingSettingCard
except ImportError:
    GreetingSettingCard = None

try:
    from src.components.cards.Settings.ffmpeg_status_card import FFmpegStatusCard
except ImportError:
    FFmpegStatusCard = None

try:
    from src.components.cards.Settings.log_control_card import LogControlCard
except ImportError:
    LogControlCard = None

try:
    from src.components.cards.Settings.avatar_setting_card import AvatarSettingCard
except ImportError:
    AvatarSettingCard = None

try:
    from src.components.cards.Settings.global_input_path_card import GlobalInputPathCard
except ImportError:
    GlobalInputPathCard = None


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
            # 创建一个返回默认值的函数
            self.get_text = lambda key, *args, **kwargs: kwargs.get("default", "")
        else:
            # 使用lang对象的get方法
            self.get_text = self.lang.get
        
        # 初始化界面
        self.initUI()
        
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

        # 应用设置组
        app_group = QWidget()
        app_group_layout = QVBoxLayout(app_group)
        
        # 标题
        group_title = TitleLabel(self.get_text("app_settings"))
        app_group_layout.addWidget(group_title)
        
        # 添加各种设置卡片
        self.addDebugModeCard(app_group_layout)
        self.addAlwaysOnTopCard(app_group_layout)
        self.addGreetingSettingCard(app_group_layout)
        self.addLanguageCard(app_group_layout)
        self.addAppearanceCard(app_group_layout)
        self.addPerformanceCard(app_group_layout)
        self.addOutputDirectoryCard(app_group_layout)
        self.addVersionCheckCard(app_group_layout)
        self.addFFmpegStatusCard(app_group_layout)
        self.addAvatarSettingCard(app_group_layout)
        self.addLogControlCard(app_group_layout)

        content_layout.addWidget(app_group)

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
            import src.components.cards.Settings.always_on_top_card as always_on_top_card_module
            if self.lang:
                always_on_top_card_module.lang = self.lang
        except ImportError:
            pass
            
        try:
            import src.components.cards.Settings.debug_mode_card as debug_mode_card_module
            if self.lang:
                debug_mode_card_module.lang = self.lang
        except ImportError:
            pass
            
        try:
            import src.components.cards.Settings.greeting_setting_card as greeting_setting_card_module
            if self.lang:
                greeting_setting_card_module.lang = self.lang
        except ImportError:
            pass
            
        try:
            import src.components.cards.Settings.ffmpeg_status_card as ffmpeg_status_card_module
            if self.lang:
                ffmpeg_status_card_module.lang = self.lang
        except ImportError:
            pass
            
        try:
            import src.components.cards.Settings.avatar_setting_card as avatar_setting_card_module
            if self.lang:
                avatar_setting_card_module.lang = self.lang
        except ImportError:
            pass
            
        try:
            import src.components.cards.Settings.global_input_path_card as global_input_path_card_module
            if self.lang:
                global_input_path_card_module.lang = self.lang
        except ImportError:
            pass
    
    def addDebugModeCard(self, layout):
        """添加Debug模式卡片"""
        if DebugModeCard is not None:
            try:
                debug_mode_card = DebugModeCard(
                    parent=self,
                    lang=self.lang,
                    config_manager=self.config_manager
                )
                layout.addWidget(debug_mode_card)
            except Exception as e:
                print(f"添加Debug模式卡片时出错: {e}")
                if hasattr(self, 'settingsLogHandler'):
                    self.settingsLogHandler.error(f"添加Debug模式卡片时出错: {e}")
    
    def addAlwaysOnTopCard(self, layout):
        """添加总是置顶窗口设置卡片"""
        if AlwaysOnTopCard is not None:
            try:
                always_on_top_card = AlwaysOnTopCard(
                    parent=self,
                    config_manager=self.config_manager
                )
                layout.addWidget(always_on_top_card)
            except Exception as e:
                print(f"添加总是置顶窗口卡片时出错: {e}")
                if hasattr(self, 'settingsLogHandler'):
                    self.settingsLogHandler.error(f"添加总是置顶窗口卡片时出错: {e}")
    
    def addGreetingSettingCard(self, layout):
        """添加问候语设置卡片"""
        if GreetingSettingCard is not None:
            try:
                greeting_card = GreetingSettingCard(
                    parent=self,
                    config_manager=self.config_manager
                )
                layout.addWidget(greeting_card)
            except Exception as e:
                print(f"添加问候语设置卡片时出错: {e}")
                if hasattr(self, 'settingsLogHandler'):
                    self.settingsLogHandler.error(f"添加问候语设置卡片时出错: {e}")
    
    def addLanguageCard(self, layout):
        """添加语言设置卡片"""
        language_card = CardWidget()
        lang_card_widget = QWidget()
        lang_card_layout = QVBoxLayout(lang_card_widget)
        lang_card_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        lang_card_layout.setContentsMargins(20, 15, 20, 15)
        lang_card_layout.setSpacing(15)

        # 然后将 lang_card_widget 添加到 language_card
        language_card_layout = QVBoxLayout(language_card)
        language_card_layout.addWidget(lang_card_widget)

        # 当前语言显示
        current_lang_row = QHBoxLayout()
 
        # 添加语言图标
        current_lang_icon = IconWidget(FluentIcon.LANGUAGE)
        current_lang_icon.setFixedSize(16, 16)
        current_lang_row.addWidget(current_lang_icon)

        current_lang_label = BodyLabel(self.get_text("current_language"))
        # 安全获取语言名称
        current_lang_name = ""
        if self.lang and hasattr(self.lang, 'get_language_name'):
            current_lang_name = self.lang.get_language_name()
        current_lang_value = StrongBodyLabel(current_lang_name)
   
        current_lang_row.addWidget(current_lang_label)
        current_lang_row.addStretch()
        current_lang_row.addWidget(current_lang_value)

        lang_card_layout.addLayout(current_lang_row)

        # 语言选择
        lang_select_row = QHBoxLayout()
        lang_select_label = BodyLabel(self.get_text("select_language"))
        self.languageCombo = ComboBox()
        
        # 使用翻译键获取语言名称
        system_setting_text = self.get_text("follow_system_language") if self.lang else "System Settings"
        simplified_chinese_text = self.get_text("simplified_chinese") if self.lang else "简体中文"
        
        self.languageCombo.addItems([system_setting_text, simplified_chinese_text, "English"])
        
        # 安全设置当前语言
        if self.lang and hasattr(self.lang, 'get_language_name'):
            self.languageCombo.setCurrentText(self.lang.get_language_name())
        self.languageCombo.setFixedWidth(150)

        lang_select_row.addWidget(lang_select_label)
        lang_select_row.addStretch()
        lang_select_row.addWidget(self.languageCombo)

        lang_card_layout.addLayout(lang_select_row)

        # 应用语言按钮
        apply_lang_layout = QHBoxLayout()
        self.applyLangButton = PrimaryPushButton(FluentIcon.SAVE, self.get_text("save"))
        self.applyLangButton.clicked.connect(self.applyLanguage)
        apply_lang_layout.addStretch()
        apply_lang_layout.addWidget(self.applyLangButton)

        lang_card_layout.addLayout(apply_lang_layout)
        layout.addWidget(language_card)
    
    def addAppearanceCard(self, layout):
        """添加外观设置卡片"""
        appearance_card = CardWidget()
        appearance_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        appearance_card_layout = QVBoxLayout(appearance_card)
        appearance_card_layout.setContentsMargins(20, 15, 20, 15)
        appearance_card_layout.setSpacing(15)

        # 主题选择
        theme_row = QHBoxLayout()
        theme_label = BodyLabel(self.get_text("theme_settings"))
        self.themeCombo = ComboBox()
        self.themeCombo.addItems([
            self.get_text("theme_dark"),
            self.get_text("theme_light"),
            self.get_text("theme_system")
        ])

        # 设置当前主题
        current_theme = self.config_manager.get("theme", "dark") if self.config_manager else "dark"
        if current_theme == "dark":
            self.themeCombo.setCurrentIndex(0)
        elif current_theme == "light":
            self.themeCombo.setCurrentIndex(1)
        else:
            self.themeCombo.setCurrentIndex(2)

        self.themeCombo.currentTextChanged.connect(self.onThemeChanged)
        self.themeCombo.setFixedWidth(150)

        theme_row.addWidget(theme_label)
        theme_row.addStretch()
        theme_row.addWidget(self.themeCombo)

        appearance_card_layout.addLayout(theme_row)
        
        # 添加自定义主题颜色卡片
        if CustomThemeColorCard is not None:
            self.themeColorCard = CustomThemeColorCard(self.config_manager)
            appearance_card_layout.addWidget(self.themeColorCard)
        
        layout.addWidget(appearance_card)
    
    def addPerformanceCard(self, layout):
        """添加性能设置卡片"""
        performance_card = CardWidget()
        performance_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        perf_card_layout = QVBoxLayout(performance_card)
        perf_card_layout.setContentsMargins(20, 15, 20, 15)
        perf_card_layout.setSpacing(15)

        # 默认线程数设置
        threads_row = QHBoxLayout()
 
        # 添加线程图标
        threads_icon = IconWidget(FluentIcon.SPEED_OFF)
        threads_icon.setFixedSize(16, 16)
        threads_row.addWidget(threads_icon)

        threads_label = BodyLabel(self.get_text("default_threads"))
        self.defaultThreadsSpinBox = SpinBox()
        self.defaultThreadsSpinBox.setRange(1, 128)
        
        # 从配置中获取默认线程数
        default_threads = min(32, multiprocessing.cpu_count() * 2)
        if self.config_manager:
            config_threads = self.config_manager.get("threads", default_threads)
            if isinstance(config_threads, int):
                default_threads = config_threads
                
        self.defaultThreadsSpinBox.setValue(default_threads)
        self.defaultThreadsSpinBox.setFixedWidth(120)
        self.defaultThreadsSpinBox.valueChanged.connect(self.saveThreadsConfig)
   
        threads_row.addWidget(threads_label)
        threads_row.addStretch()
        threads_row.addWidget(self.defaultThreadsSpinBox)

        perf_card_layout.addLayout(threads_row)
        layout.addWidget(performance_card)
    
    def addOutputDirectoryCard(self, layout):
        """添加输出目录设置卡片"""
        output_card = CardWidget()
        output_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(20, 15, 20, 15)
        output_layout.setSpacing(15)
        
        output_title = StrongBodyLabel(self.get_text("output_settings"))
        output_layout.addWidget(output_title)
        
        # 全局输入路径设置
        try:
            # 如果没有设置全局输入路径，则使用默认的Roblox路径
            if self.config_manager and not self.config_manager.get("global_input_path", ""):
                default_roblox_dir = get_roblox_default_dir()
                if default_roblox_dir:
                    self.config_manager.set("global_input_path", default_roblox_dir)
                    self.config_manager.save_config()
                    if hasattr(self, 'settingsLogHandler'):
                        self.settingsLogHandler.info(self.get_text("default_roblox_path_set", "已设置默认Roblox路径") + f": {default_roblox_dir}")
            
            if GlobalInputPathCard is not None:
                self.globalInputPathCard = GlobalInputPathCard(self.config_manager)
                # 连接输入路径改变信号到更新路径函数
                self.globalInputPathCard.inputPathChanged.connect(self.updateGlobalInputPath)
                # 连接恢复默认路径信号
                self.globalInputPathCard.restoreDefaultPath.connect(self.restoreDefaultInputPath)
                output_layout.addWidget(self.globalInputPathCard)
        except Exception as e:
            print(f"添加全局输入路径卡片时出错: {e}")
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.error(f"添加全局输入路径卡片时出错: {e}")
        
        # 自定义输出路径设置
        custom_output_row = QHBoxLayout()
        custom_output_label = BodyLabel(self.get_text("custom_output_dir"))
        custom_output_row.addWidget(custom_output_label)
        custom_output_row.addStretch()
        
        output_layout.addLayout(custom_output_row)
        
        # 输出路径输入框和浏览按钮
        output_path_layout = QHBoxLayout()
        self.customOutputPath = LineEdit()
        self.customOutputPath.setText(self.config_manager.get("custom_output_dir", "") if self.config_manager else "")
        self.customOutputPath.setPlaceholderText(self.get_text("output_dir_placeholder"))
        
        browse_output_btn = PushButton(FluentIcon.FOLDER_ADD, self.get_text("browse"))
        browse_output_btn.setFixedSize(80, 33)
        browse_output_btn.clicked.connect(self.browseOutputDirectory)
        
        output_path_layout.addWidget(self.customOutputPath)
        output_path_layout.addWidget(browse_output_btn)
        
        output_layout.addLayout(output_path_layout)
        
        # 保存日志选项
        save_logs_row = QHBoxLayout()
        save_logs_label = BodyLabel(self.get_text("save_logs"))
        self.saveLogsSwitch = SwitchButton()
        self.saveLogsSwitch.setChecked(self.config_manager.get("save_logs", False) if self.config_manager else False)
        self.saveLogsSwitch.checkedChanged.connect(self.toggleSaveLogs)
        
        save_logs_row.addWidget(save_logs_label)
        save_logs_row.addStretch()
        save_logs_row.addWidget(self.saveLogsSwitch)
        
        output_layout.addLayout(save_logs_row)
        
        # 自动打开输出目录选项
        auto_open_row = QHBoxLayout()
        auto_open_label = BodyLabel(self.get_text("auto_open_output_dir"))
        self.autoOpenSwitch = SwitchButton()
        self.autoOpenSwitch.setChecked(self.config_manager.get("auto_open_output_dir", True) if self.config_manager else True)
        self.autoOpenSwitch.checkedChanged.connect(self.toggleAutoOpenOutputDir)
        
        auto_open_row.addWidget(auto_open_label)
        auto_open_row.addStretch()
        auto_open_row.addWidget(self.autoOpenSwitch)
        
        output_layout.addLayout(auto_open_row)
        
        # 添加输出设置卡片
        layout.addWidget(output_card)
    
    def addVersionCheckCard(self, layout):
        """添加版本检测卡片"""
        if VersionCheckCard is not None:
            version_card = CardWidget()
            version_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            version_card_layout = QVBoxLayout(version_card)
            version_card_layout.setContentsMargins(0, 0, 0, 0)  # 让VersionCheckCard处理内边距
            
            # 获取当前版本号
            current_version = self.version or ""
            
            # 创建版本检测卡片
            self.versionCheckCard = VersionCheckCard(self.config_manager, current_version)
            version_card_layout.addWidget(self.versionCheckCard)
            
            # 添加版本检测卡片
            layout.addWidget(version_card)
    
    def addFFmpegStatusCard(self, layout):
        """添加FFmpeg状态检测卡片"""
        if FFmpegStatusCard is not None:
            ffmpeg_card = CardWidget()
            ffmpeg_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            ffmpeg_card_layout = QVBoxLayout(ffmpeg_card)
            ffmpeg_card_layout.setContentsMargins(0, 0, 0, 0)  # 让FFmpegStatusCard处理内边距
            
            # 创建FFmpeg状态卡片
            self.ffmpegStatusCard = FFmpegStatusCard()
            ffmpeg_card_layout.addWidget(self.ffmpegStatusCard)
            
            # 添加FFmpeg状态卡片
            layout.addWidget(ffmpeg_card)
    
    def addAvatarSettingCard(self, layout):
        """添加头像设置卡片"""
        if AvatarSettingCard is not None:
            try:
                avatar_card = CardWidget()
                avatar_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
                avatar_card_layout = QVBoxLayout(avatar_card)
                avatar_card_layout.setContentsMargins(0, 0, 0, 0)  # 让AvatarSettingCard处理内边距
                
                # 创建头像设置卡片
                self.avatarSettingCard = AvatarSettingCard(self.config_manager)
                avatar_card_layout.addWidget(self.avatarSettingCard)
                
                # 添加头像设置卡片
                layout.addWidget(avatar_card)
            except Exception as e:
                print(f"添加头像设置卡片时出错: {e}")
    
    def addLogControlCard(self, layout):
        """添加日志管理卡片"""
        if LogControlCard is not None:
            log_control_card = LogControlCard(
                parent=self,
                lang=self.lang,
                central_log_handler=CentralLogHandler.getInstance()
            )
            layout.addWidget(log_control_card)
            
    def onThemeChanged(self, theme_name):
        """主题更改事件处理"""
        # 调用父窗口的onThemeChanged方法
        if self._parent_window and hasattr(self._parent_window, 'onThemeChanged'):
            self._parent_window.onThemeChanged(theme_name)
            
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
        from PyQt5.QtWidgets import QFileDialog
        directory = QFileDialog.getExistingDirectory(self, self.get_text("directory"), self.customOutputPath.text())
        if directory and self.config_manager:
            self.customOutputPath.setText(directory)
            self.config_manager.set("custom_output_dir", directory)
            
    def toggleSaveLogs(self):
        """切换保存日志选项"""
        if self.config_manager:
            self.config_manager.set("save_logs", self.saveLogsSwitch.isChecked())
            if hasattr(self, 'settingsLogHandler'):
                self.settingsLogHandler.info(self.get_text("log_save_option_toggled"))
                
    def toggleAutoOpenOutputDir(self):
        """切换自动打开输出目录选项"""
        if self.config_manager:
            self.config_manager.set("auto_open_output_dir", self.autoOpenSwitch.isChecked())
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