#!/usr/bin/env python3
# -*- coding: utf-8 -*-

VERSION = "0.16.1"

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import sys
import time
import json
import logging
import threading
import queue
import datetime
import traceback
import multiprocessing
from functools import lru_cache
from typing import Dict, List, Any, Set, Optional
from enum import Enum, auto

# 导入自定义提取器模块
from src.extractors.audio_extractor import RobloxAudioExtractor, ExtractedHistory, ContentHashCache, ProcessingStats, ClassificationMethod, is_ffmpeg_available

# 导入工具函数
from src.utils.file_utils import resource_path, get_roblox_default_dir, open_directory
from src.utils.log_utils import LogHandler, setup_basic_logging, save_log_to_file
from src.utils.import_utils import import_libs

# 导入语言管理
from src.locale import Language, initialize_lang
from src.locale import lang
# 导入语言管理功能
from src.management.language_management.language_manager import apply_language, get_language_code

# 导入自定义工作线程
from src.workers.extraction_worker import ExtractionWorker
# 导入缓存管理模块
from src.management.cache_management.cache_cleaner import CacheClearWorker
# 导入响应式UI组件
from src.components.ui.responsive_components import ResponsiveFeatureItem
# 导入窗口管理功能
from src.management.window_management.responsive_handler import apply_responsive_handler
from src.management.window_management.window_utils import apply_always_on_top
# 导入主题管理功能
from src.management.theme_management.theme_manager import apply_theme_from_config, apply_theme_change, _pre_cache_theme_styles
# 导入自定义主题颜色卡片
from src.components.cards.Settings.custom_theme_color_card import CustomThemeColorCard
# 导入中央日志处理系统
from src.logging.central_log_handler import CentralLogHandler
# 导入版本检测卡片
from src.components.cards.Settings.version_check_card import VersionCheckCard
# 导入日志控制卡片
from src.components.cards.Settings.log_control_card import LogControlCard
# 导入FFmpeg状态卡片
from src.components.cards.Settings.ffmpeg_status_card import FFmpegStatusCard
# 导入头像设置卡片
from src.components.cards.Settings.avatar_setting_card import AvatarSettingCard
# 导入Debug模式卡片
from src.components.cards.Settings.debug_mode_card import DebugModeCard
# 导入总是置顶窗口设置卡片
from src.components.cards.Settings.always_on_top_card import AlwaysOnTopCard
# 导入问候语设置卡片
from src.components.cards.Settings.greeting_setting_card import GreetingSettingCard
# 导入配置管理器
from src.config import ConfigManager
# 导入界面模块
from src.interfaces import HomeInterface, AboutInterface, ExtractImagesInterface, ExtractTexturesInterface, ClearCacheInterface, HistoryInterface, ExtractAudioInterface, SettingsInterface


if hasattr(sys, '_MEIPASS'):
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt', 'plugins')

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,QButtonGroup,
    QFileDialog, QLabel, QFrame, QSizePolicy, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QPixmap, QFont, QColor


from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, setTheme, Theme,
    InfoBar, FluentIcon, PushButton, PrimaryPushButton,
    ComboBox, BodyLabel, CardWidget, TitleLabel, CaptionLabel,
    ProgressBar, CheckBox, RadioButton, TextEdit,
    MessageBox, StateToolTip, InfoBarPosition,
    StrongBodyLabel, SubtitleLabel, DisplayLabel,
    HyperlinkButton, TransparentPushButton, ScrollArea,
    IconWidget, SpinBox, LineEdit, PillPushButton, FlowLayout,
    SplashScreen, setThemeColor, SwitchButton  
)

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class MainWindow(FluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 确保在启动时同步配置到PyQt-Fluent-Widgets
        self.config_manager.sync_theme_to_qfluent()
        
        # 只有在debug模式开启时才输出调试信息
        if self.config_manager.get("debug_mode_enabled", False):
            print(f"QFluentWidgets配置文件路径: {self.config_manager.qfluent_config_file}")
            if os.path.exists(self.config_manager.qfluent_config_file):
                try:
                    with open(self.config_manager.qfluent_config_file, 'r', encoding='utf-8') as f:
                        qfluent_config = json.load(f)
                        print(f"QFluentWidgets配置内容: {qfluent_config}")
                except Exception as e:
                    print(f"读取QFluentWidgets配置失败: {e}")

        # 初始化语言管理器
        global lang
        lang = initialize_lang(self.config_manager)

        # 初始化中央日志处理器
        CentralLogHandler.getInstance().init_with_config(self.config_manager)

        # 初始化窗口
        self.initWindow()

        # 初始化数据
        self.default_dir = get_roblox_default_dir()
        
        # 创建应用数据目录
        app_data_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        os.makedirs(app_data_dir, exist_ok=True)
        history_file = os.path.join(app_data_dir, "extracted_history.json")
        
        # 初始化提取历史
        self.download_history = ExtractedHistory(history_file)
        
        # 初始化工作线程
        self.extraction_worker = None
        self.cache_clear_worker = None
        
        # 初始化UI
        self.initUI()
        
        # 再次确保同步配置到PyQt-Fluent-Widgets，然后应用主题设置
        self.config_manager.sync_theme_to_qfluent()
        
        # 应用保存的主题设置
        self.applyThemeFromConfig()
        
        # 应用响应式布局到所有界面
        self.applyResponsiveLayoutToAllInterfaces()
        
        # 应用响应式窗口调整处理器
        apply_responsive_handler(self, self._adjust_responsive_layout)

    def initWindow(self):
        """初始化窗口设置"""
        # 设置窗口标题和大小
        self.setWindowTitle(lang.get("title"))
        self.resize(750, 570)

        # 设置最小窗口大小
        self.setMinimumSize(750, 570)

        # 设置自动主题
        setTheme(Theme.AUTO)

        # 设置窗口图标
        try:
            icon_path = resource_path(os.path.join("res", "icons", "logo.png"))
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"无法设置窗口图标: {e}")

        
        # 应用窗口置顶设置
        always_on_top = self.config_manager.get("always_on_top", False)
        if always_on_top:
            # 使用两段式延迟，先显示窗口，再设置置顶
            QTimer.singleShot(500, lambda: self.show())
            QTimer.singleShot(1500, lambda: apply_always_on_top(self, True))
            
            # 只有在debug模式开启时才输出调试信息
            if self.config_manager.get("debug_mode_enabled", False):
                print("窗口初始化时设置置顶")
            
        # 预加载其他主题样式，确保首次切换主题时流畅
        current_theme = self.config_manager.get("theme", "dark")
        other_theme = "light" if current_theme == "dark" else "dark"
        QTimer.singleShot(200, lambda: _pre_cache_theme_styles(self, other_theme))



    def applyThemeFromConfig(self):
        """从配置文件应用主题设置"""
        # 只有在debug模式开启时才输出调试信息
        if self.config_manager.get("debug_mode_enabled", False):
            use_custom_theme_color = self.config_manager.get("use_custom_theme_color", False)
            theme_color = self.config_manager.get("theme_color", "#0078d4")
            theme_mode = self.config_manager.get("theme", "dark")
            print(f"QFluentWidgets配置文件路径: {self.config_manager.qfluent_config_file}")
            print(f"QFluentWidgets配置内容: {self.config_manager.get_qfluent_config()}")
            print(f"应用主题前配置状态: theme={theme_mode}, use_custom_theme_color={use_custom_theme_color}, theme_color={theme_color}")
        
        # 使用主题管理器应用主题
        apply_theme_from_config(self, self.config_manager, CentralLogHandler.getInstance())

    def initUI(self):
        """初始化UI组件"""
        # 创建主界面 - 使用新的HomeInterface类
        self.homeInterface = HomeInterface(
            parent=self,
            default_dir=self.default_dir,
            config_manager=self.config_manager,
            lang=lang
        )

        # 添加提取音频界面 - 使用ExtractAudioInterface类
        self.extractInterface = ExtractAudioInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang,
            default_dir=self.default_dir,
            download_history=self.download_history
        )

        # 添加新的图像提取界面 - 使用ExtractImagesInterface类
        self.extractImagesInterface = ExtractImagesInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang
        )

        # 添加新的纹理提取界面 - 使用ExtractTexturesInterface类
        self.extractTexturesInterface = ExtractTexturesInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang
        )

        # 添加清除缓存界面 - 使用ClearCacheInterface类
        self.clearCacheInterface = ClearCacheInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang,
            default_dir=self.default_dir
        )

        # 添加历史记录界面 - 使用HistoryInterface类
        self.historyInterface = HistoryInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang,
            download_history=self.download_history
        )

        # 添加设置界面 - 使用SettingsInterface类
        self.settingsInterface = SettingsInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang,
            version=VERSION
        )

        # 使用AboutInterface类代替QWidget
        self.aboutInterface = AboutInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang
        )

        # 设置导航 - 
        self.addSubInterface(self.homeInterface, FluentIcon.HOME, lang.get("home"))
        
        # 添加Extract树形菜单
        extract_tree = self.navigationInterface.addItem(
            routeKey="extract",
            icon=FluentIcon.DOWNLOAD,
            text=lang.get("extract"),
            onClick=None,
            selectable=False,
            position=NavigationItemPosition.TOP
        )
        
        # 先确保接口被添加到堆叠窗口小部件
        self.stackedWidget.addWidget(self.extractInterface)
        
        # 添加子菜单项
        self.navigationInterface.addItem(
            routeKey=self.extractInterface.objectName(),
            icon=FluentIcon.MUSIC,
            text=lang.get("extract_audio"),
            onClick=lambda: self.switchTo(self.extractInterface),
            selectable=True,
            position=NavigationItemPosition.TOP,
            parentRouteKey="extract"
        )
        
        # 同样确保其他接口被添加到堆叠窗口小部件
        self.stackedWidget.addWidget(self.extractImagesInterface)
        self.stackedWidget.addWidget(self.extractTexturesInterface)
        
        self.navigationInterface.addItem(
            routeKey=self.extractImagesInterface.objectName(),
            icon=FluentIcon.PHOTO,
            text=lang.get("extract_images"),
            onClick=lambda: self.switchTo(self.extractImagesInterface),
            selectable=True,
            position=NavigationItemPosition.TOP,
            parentRouteKey="extract"
        )
        
        self.navigationInterface.addItem(
            routeKey=self.extractTexturesInterface.objectName(),
            icon=FluentIcon.PALETTE,
            text=lang.get("extract_textures"),
            onClick=lambda: self.switchTo(self.extractTexturesInterface),
            selectable=True,
            position=NavigationItemPosition.TOP,
            parentRouteKey="extract"
        )
        
        # 默认收起Extract树形菜单
        extract_tree.setExpanded(False)
        
        self.addSubInterface(self.clearCacheInterface, FluentIcon.DELETE, lang.get("clear_cache"))
        self.addSubInterface(self.historyInterface, FluentIcon.HISTORY, lang.get("view_history"))

        # 在提取历史导航下方添加分隔线
        self.navigationInterface.addSeparator()

        # 添加底部导航项 - 顺序很重要
        # 先添加JustKanade头像按钮，确保它在设置按钮上方
        try:
            from src.components.avatar import AvatarWidget
            # 设置avatar_widget模块的lang变量
            import src.components.avatar.avatar_widget as avatar_widget_module
            avatar_widget_module.lang = lang
            
            avatar_widget = AvatarWidget(parent=self)
            self.navigationInterface.addWidget(
                routeKey="avatar_widget",
                widget=avatar_widget,
                position=NavigationItemPosition.BOTTOM,
                tooltip="JustKanade"
            )
        except Exception as e:
            print(f"添加头像组件时出错: {e}")

     
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, lang.get("settings"),
                             position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.aboutInterface, FluentIcon.INFO, lang.get("about"),
                             position=NavigationItemPosition.BOTTOM)


        # 设置默认界面 - 使用界面对象而不是文本
        self.switchTo(self.homeInterface)

        # 监听界面切换事件
        self.stackedWidget.currentChanged.connect(self.onInterfaceChanged)
        
        # 设置复制到剪贴板的方法
        self.homeInterface.copyPathToClipboard = self.copyPathToClipboard
        
        # 设置界面切换方法
        self.homeInterface.switchToInterface = self.switchToInterfaceByName
        
        # 显示欢迎消息
        self.homeInterface.add_welcome_message()

    def _adjust_responsive_layout(self, window_width):
        """根据窗口宽度调整响应式布局"""
        try:
            # 如果homeInterface是HomeInterface类的实例，调用其响应式布局调整方法
            if hasattr(self, 'homeInterface') and isinstance(self.homeInterface, HomeInterface):
                self.homeInterface.adjust_responsive_layout(window_width)
        except Exception as e:
            # 静默处理异常，避免影响UI正常运行
            pass
            
    def switchToInterfaceByName(self, interface_name):
        """通过界面名称切换界面"""
        try:
            # 寻找名称匹配的界面对象
            for i in range(self.stackedWidget.count()):
                widget = self.stackedWidget.widget(i)
                if widget and widget.objectName() == interface_name:
                    self.switchTo(widget)
                    return
        except Exception as e:
            print(f"切换界面时出错: {e}")
            
    def onInterfaceChanged(self, index):
        """界面切换事件处理"""
        try:
            current_widget = self.stackedWidget.widget(index)
            # 如果切换到历史界面，刷新数据
            if current_widget == self.historyInterface:
                self.historyInterface.refreshHistoryInterface()
            # 如果切换到提取界面，更新线程数设置
            elif current_widget == self.extractInterface:
                if hasattr(current_widget, 'updateThreadsValue'):
                    current_widget.updateThreadsValue()
        except Exception as e:
            pass
          
    def setExtractStyles(self):
        """设置提取音频界面的样式"""
        try:
            theme = self.config_manager.get("theme", "dark")
            
            # 设置标题样式
            title_label = self.extractInterface.findChild(TitleLabel, "extractAudioTitle")
            if title_label:
                if theme == "light":
                    title_label.setStyleSheet("""
                        font-size: 28px;
                        font-weight: bold;
                        color: rgb(0, 0, 0);
                        margin-bottom: 3px;
                    """)
                else:
                    title_label.setStyleSheet("""
                        font-size: 28px;
                        font-weight: bold;
                        color: rgb(255, 255, 255);
                        margin-bottom: 3px;
                    """)
                    
        except Exception as e:
            print(f"设置提取音频界面样式时出错: {e}")
            
    def add_welcome_message(self):
        """添加欢迎消息到主页日志"""
        # 导入并显示时间问候
        from src.components.Greetings import TimeGreetings
        
        # 获取当前语言设置
        current_language = lang.get_language_name()
        # 修改判断逻辑，检查实际使用的语言而非名称
        language_code = 'zh' if lang.current_language == lang.CHINESE else 'en'
        
        # 检查问候语是否启用
        greeting_enabled = self.config_manager.get("greeting_enabled", True)
        if greeting_enabled:
            # 使用固定样式和当前语言显示问候
            TimeGreetings.show_greeting(language_code)
        
        # 添加日志信息
        if hasattr(self, 'homeInterface') and hasattr(self.homeInterface, 'logText'):
            log = LogHandler(self.homeInterface.logText)
            log.info(lang.get('welcome_message'))
            log.info(lang.get('about_version'))
            log.info(f"{lang.get('default_dir')}: {self.default_dir}")
            log.info(lang.get("config_file_location", self.config_manager.config_file))
            
    def onThemeChanged(self, theme_name):
        """主题更改事件处理"""
        # 使用主题管理器应用主题变更
        apply_theme_change(
            self, 
            theme_name, 
            self.config_manager, 
            CentralLogHandler.getInstance(), 
            self.settingsLogHandler if hasattr(self, 'settingsLogHandler') else None,
            lang
        )

    def saveThreadsConfig(self, value):
        """保存线程数配置"""
        self.config_manager.set("threads", value)
        if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'settingsLogHandler'):
            self.settingsInterface.settingsLogHandler.info(lang.get("saved", f"{lang.get('default_threads')}: {value}"))

    def startExtraction(self):
        """开始提取音频"""
        # 获取全局输入路径（如果已设置）
        global_input_path = self.config_manager.get("global_input_path", "")
        
        # 获取用户选择的目录
        selected_dir = global_input_path if global_input_path else self.dirInput.text()
        
        # 如果使用了全局输入路径，更新输入框的显示
        if global_input_path and self.dirInput.text() != global_input_path:
            self.dirInput.setText(global_input_path)
            self.extractLogHandler.info(lang.get("using_global_input_path", "使用全局输入路径") + f": {global_input_path}")

        # 检查目录是否存在
        if not os.path.exists(selected_dir):
            result = MessageBox(
                lang.get("create_dir_prompt"),
                lang.get("dir_not_exist", selected_dir),
                self
            )

            if result.exec():
                try:
                    os.makedirs(selected_dir, exist_ok=True)
                    self.extractLogHandler.success(lang.get("dir_created", selected_dir))
                except Exception as e:
                    self.extractLogHandler.error(lang.get("dir_create_failed", str(e)))
                    return
            else:
                self.extractLogHandler.warning(lang.get("operation_cancelled"))
                return

        # 获取线程数
        try:
            num_threads = self.threadsSpinBox.value()
            if num_threads < 1:
                self.extractLogHandler.warning(lang.get("threads_min_error"))
                num_threads = min(32, multiprocessing.cpu_count() * 2)
                self.threadsSpinBox.setValue(num_threads)

            if num_threads > 64:
                result = MessageBox(
                    lang.get("confirm_high_threads"),
                    lang.get("threads_high_warning"),
                    self
                )

                if not result.exec():
                    num_threads = min(32, multiprocessing.cpu_count() * 2)
                    self.threadsSpinBox.setValue(num_threads)
                    self.extractLogHandler.info(lang.get("threads_adjusted", num_threads))
        except ValueError:
            self.extractLogHandler.warning(lang.get("input_invalid"))
            num_threads = min(32, multiprocessing.cpu_count() * 2)
            self.threadsSpinBox.setValue(num_threads)

        # 获取分类方法
        classification_method = ClassificationMethod.DURATION if self.durationRadio.isChecked() else ClassificationMethod.SIZE

        # 如果选择时长分类但没有ffmpeg，显示警告
        if classification_method == ClassificationMethod.DURATION and not is_ffmpeg_available():
            result = MessageBox(
                lang.get("confirm"),
                lang.get("ffmpeg_not_installed"),
                self
            )

            if not result.exec():
                self.extractLogHandler.warning(lang.get("operation_cancelled"))
                return

        # 获取自定义输出目录
        custom_output_dir = self.config_manager.get("custom_output_dir", "")
        
        # 创建并启动提取线程
        self.extraction_worker = ExtractionWorker(
            selected_dir,
            num_threads,
            self.download_history,
            classification_method,
            custom_output_dir  # 传递自定义输出目录参数
        )

        # 连接信号
        self.extraction_worker.progressUpdated.connect(self.updateExtractionProgress)
        self.extraction_worker.finished.connect(self.extractionFinished)
        self.extraction_worker.logMessage.connect(self.handleExtractionLog)

        # 更新UI状态
        self.extractButton.hide()
        self.cancelButton.show()
        self.progressBar.setValue(0)
        self.progressLabel.setText(lang.get("processing"))

        # 创建任务状态提示
        self.extractionStateTooltip = StateToolTip(
            lang.get("task_running"),
            lang.get("processing"),
            self
        )
        self.extractionStateTooltip.show()

        # 启动线程
        self.extraction_worker.start()
    def cancelExtraction(self):
        """取消提取操作"""
        if self.extraction_worker and self.extraction_worker.isRunning():
            self.extraction_worker.cancel()

            # 更新状态
            if hasattr(self, 'extractionStateTooltip'):
                self.extractionStateTooltip.setContent(lang.get("task_canceled"))
                self.extractionStateTooltip.setState(True)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.extractionStateTooltip.close)

            # 恢复UI
            self.cancelButton.hide()
            self.extractButton.show()

            # 重置进度条
            self.progressBar.setValue(0)
            self.progressLabel.setText(lang.get("ready"))

            self.handleExtractionLog(lang.get("canceled_by_user"), "warning")

    def updateExtractionProgress(self, current, total, elapsed, speed):
        """更新提取进度"""
        # 计算进度百分比
        progress = min(100, int((current / total) * 100)) if total > 0 else 0

        # 计算剩余时间
        remaining = (total - current) / speed if speed > 0 else 0
        remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"

        # 构建状态文本
        status_text = f"{progress}% - {current}/{total} | {speed:.1f} files/s"

        # 更新UI
        self.progressBar.setValue(progress)
        self.progressLabel.setText(status_text)
        # 更新状态提示
        if hasattr(self, 'extractionStateTooltip'):
            self.extractionStateTooltip.setContent(status_text)

    def extractionFinished(self, result):
        """提取完成处理"""
        # 恢复UI状态
        self.cancelButton.hide()
        self.extractButton.show()

        # 重置进度条为0而不是100
        self.progressBar.setValue(0)
        self.progressLabel.setText(lang.get("ready"))

        if result.get("success", False):
            # 显示提取结果
            if "processed" in result and result["processed"] > 0:
                self.extractLogHandler.success(lang.get("extraction_complete"))
                self.extractLogHandler.info(lang.get("processed", result['processed']))
                self.extractLogHandler.info(lang.get("skipped_duplicates", result.get('duplicates', 0)))
                self.extractLogHandler.info(lang.get("skipped_already_processed", result.get('already_processed', 0)))
                self.extractLogHandler.info(lang.get("errors", result.get('errors', 0)))
                self.extractLogHandler.info(lang.get("time_spent", result.get('duration', 0)))
                self.extractLogHandler.info(lang.get("files_per_sec", result.get('files_per_second', 0)))
                self.extractLogHandler.info(lang.get("output_dir", result.get('output_dir', '')))

                # 输出目录
                final_dir = result.get("output_dir", "")
                # 音频输出文件夹路径
                audio_dir = os.path.join(final_dir, "Audio")

                # 根据设置决定是否自动打开目录
                if final_dir and os.path.exists(final_dir) and self.config_manager.get("auto_open_output_dir", True):
                    # 优先打开Audio文件夹，如果存在
                    if os.path.exists(audio_dir):
                        open_success = open_directory(audio_dir)
                        if open_success:
                            self.extractLogHandler.info(lang.get("opening_output_dir", lang.get("audio_folder")))
                        else:
                            self.extractLogHandler.info(lang.get("manual_navigate", audio_dir))
                    else:
                        # 如果Audio文件夹不存在，打开根输出目录
                        open_success = open_directory(final_dir)
                        if open_success:
                            self.extractLogHandler.info(lang.get("opening_output_dir", lang.get("ogg_category")))
                        else:
                            self.extractLogHandler.info(lang.get("manual_navigate", final_dir))

                # 更新状态提示
                if hasattr(self, 'extractionStateTooltip'):
                    self.extractionStateTooltip.setContent(lang.get("extraction_complete"))
                    self.extractionStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.extractionStateTooltip.close)

                # 显示完成消息
                InfoBar.success(
                    title=lang.get("task_completed"),
                    content=lang.get("extraction_complete"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )

                # 刷新历史界面以显示最新的文件数量
                self.historyInterface.refreshHistoryInterface()
            else:
                self.extractLogHandler.warning(lang.get("no_files_processed"))

                # 更新状态提示
                if hasattr(self, 'extractionStateTooltip'):
                    self.extractionStateTooltip.setContent(lang.get("no_files_processed"))
                    self.extractionStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.extractionStateTooltip.close)
        else:
            # 显示错误
            self.extractLogHandler.error(lang.get("error_occurred", result.get('error', '')))

            # 更新状态提示
            if hasattr(self, 'extractionStateTooltip'):
                self.extractionStateTooltip.setContent(lang.get("task_failed"))
                self.extractionStateTooltip.setState(False)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.extractionStateTooltip.close)

            # 显示错误消息
            InfoBar.error(
                title=lang.get("task_failed"),
                content=result.get('error', lang.get('error_occurred', '')),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def handleExtractionLog(self, message, msg_type="info"):
        """处理提取过程中的日志消息"""
        if msg_type == "info":
            self.extractLogHandler.info(message)
        elif msg_type == "success":
            self.extractLogHandler.success(message)
        elif msg_type == "warning":
            self.extractLogHandler.warning(message)
        elif msg_type == "error":
            self.extractLogHandler.error(message)

    def clearAudioCache(self):
        """清除音频缓存"""
        # 确认对话框
        result = MessageBox(
            lang.get("clear_cache"),
            lang.get("confirm_clear_cache"),
            self
        )

        if not result.exec():
            # 使用新界面类的日志处理器
            self.clearCacheInterface.logHandler.info(lang.get("operation_cancelled"))
            return

        # 创建并启动缓存清理线程
        self.cache_clear_worker = CacheClearWorker()

        # 连接信号
        self.cache_clear_worker.progressUpdated.connect(self.updateCacheProgress)
        self.cache_clear_worker.finished.connect(self.cacheClearFinished)

        # 更新UI状态
        # 使用新界面类的方法
        self.clearCacheInterface.showClearButton(False)
        self.clearCacheInterface.showCancelButton(True)
        self.clearCacheInterface.updateProgressBar(0)
        self.clearCacheInterface.updateProgressLabel(lang.get("processing"))

        # 创建任务状态提示
        self.cacheStateTooltip = StateToolTip(
            lang.get("task_running"),
            lang.get("processing"),
            self
        )
        self.cacheStateTooltip.show()

        # 启动线程
        self.cache_clear_worker.start()

    def cancelClearCache(self):
        """取消缓存清理操作"""
        if self.cache_clear_worker and self.cache_clear_worker.isRunning():
            self.cache_clear_worker.cancel()

            # 更新状态
            if hasattr(self, 'cacheStateTooltip'):
                self.cacheStateTooltip.setContent(lang.get("task_canceled"))
                self.cacheStateTooltip.setState(True)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.cacheStateTooltip.close)

            # 恢复UI
            # 使用新界面类的方法
            self.clearCacheInterface.showCancelButton(False)
            self.clearCacheInterface.showClearButton(True)

            # 重置进度条
            self.clearCacheInterface.updateProgressBar(0)
            self.clearCacheInterface.updateProgressLabel(lang.get("ready"))

            self.clearCacheInterface.logHandler.warning(lang.get("canceled_by_user"))

    def updateCacheProgress(self, current, total):
        """更新缓存清理进度"""
        # 计算进度百分比
        progress = min(100, int((current / total) * 100)) if total > 0 else 0

        # 构建状态文本
        status_text = f"{progress}% - {current}/{total}"

        # 更新UI
        # 使用新界面类的方法
        self.clearCacheInterface.updateProgressBar(progress)
        self.clearCacheInterface.updateProgressLabel(status_text)

        # 更新状态提示
        if hasattr(self, 'cacheStateTooltip'):
            self.cacheStateTooltip.setContent(status_text)

    def cacheClearFinished(self, success, cleared_files, total_files, error_msg):
        """缓存清理完成处理"""
        # 恢复UI状态
        # 使用新界面类的方法
        self.clearCacheInterface.showCancelButton(False)
        self.clearCacheInterface.showClearButton(True)

        # 重置进度条为0而不是100
        self.clearCacheInterface.updateProgressBar(0)
        self.clearCacheInterface.updateProgressLabel(lang.get("ready"))

        if success:
            if cleared_files > 0:
                self.clearCacheInterface.logHandler.success(lang.get("cache_cleared", cleared_files, total_files))

                # 更新状态提示
                if hasattr(self, 'cacheStateTooltip'):
                    self.cacheStateTooltip.setContent(lang.get("cache_cleared", cleared_files, total_files))
                    self.cacheStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.cacheStateTooltip.close)
                # 显示完成消息
                InfoBar.success(
                    title=lang.get("task_completed"),
                    content=lang.get('cache_cleared', cleared_files, total_files),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
            else:
                self.clearCacheInterface.logHandler.warning(lang.get("no_cache_found"))

                # 更新状态提示
                if hasattr(self, 'cacheStateTooltip'):
                    self.cacheStateTooltip.setContent(lang.get("no_cache_found"))
                    self.cacheStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.cacheStateTooltip.close)
        else:
            # 显示错误
            self.clearCacheInterface.logHandler.error(lang.get("clear_cache_failed", error_msg))

            # 更新状态提示
            if hasattr(self, 'cacheStateTooltip'):
                self.cacheStateTooltip.setContent(lang.get("task_failed"))
                self.cacheStateTooltip.setState(False)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.cacheStateTooltip.close)

            # 显示错误消息
            InfoBar.error(
                title=lang.get("task_failed"),
                content=lang.get('clear_cache_failed', error_msg),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def clearHistory(self, record_type="all"):
        """清除提取历史
        
        Args:
            record_type: 要清除的记录类型，默认为'all'表示清除所有记录
        """
        # 确认对话框
        result = MessageBox(
            lang.get("clear_history"),
            lang.get("confirm_clear_history"),
            self
        )

        if not result.exec():
            if hasattr(self.historyInterface, 'logHandler'):
                self.historyInterface.logHandler.info(lang.get("operation_cancelled"))
            return
            
        try:
            # 清除历史记录
            if record_type == "all":
                self.download_history.clear_history()
                message = lang.get("all_history_cleared")
            else:
                # 确保record_type是字符串类型
                record_type_str = str(record_type)
                self.download_history.clear_history(record_type_str)
                message = lang.get("history_type_cleared").format(record_type_str.capitalize())

            # 延迟刷新界面，避免立即更新UI导致的问题
            QTimer.singleShot(100, self.historyInterface.refreshHistoryInterfaceAfterClear)
                
            # 显示成功消息
            if hasattr(self.historyInterface, 'logHandler'):
                self.historyInterface.logHandler.success(message)

            # 延迟显示通知，避免阻塞
            QTimer.singleShot(200, lambda: InfoBar.success(
                title=lang.get("task_completed"),
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            ))
            
            # 更新提取界面的历史记录显示
            if hasattr(self, 'extractInterface') and hasattr(self.extractInterface, 'updateHistorySize'):
                self.extractInterface.updateHistorySize()
        
        except Exception as e:
            # 显示错误消息
            if hasattr(self.historyInterface, 'logHandler'):
                self.historyInterface.logHandler.error(lang.get("error_occurred", str(e)))
            traceback.print_exc()

            # 延迟显示错误通知
            QTimer.singleShot(200, lambda: InfoBar.error(
                title=lang.get("task_failed"),
                content=lang.get('error_occurred', str(e)),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            ))

    def applyLanguage(self):
        """应用语言设置"""
        # 从设置界面获取选择的语言
        if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'languageCombo'):
            selected_language = self.settingsInterface.languageCombo.currentText()
            current_language = lang.get_language_name()
            
            # 使用语言管理模块应用语言设置
            apply_language(
                self, 
                selected_language, 
                current_language, 
                lang, 
                self.settingsInterface.settingsLogHandler if hasattr(self.settingsInterface, 'settingsLogHandler') else None
            )

    def setResponsiveContentWidget(self, scroll_area):
        """为滚动区域内的内容容器应用响应式布局设置，防止卡片间距异常"""
        if not scroll_area or not isinstance(scroll_area, ScrollArea):
            return
            
        content_widget = scroll_area.widget()
        if not content_widget:
            return
            
        # 设置垂直大小策略为最小值，防止垂直方向上不必要的扩展
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        # 确保布局设置了顶部对齐
        if content_widget.layout():
            content_widget.layout().setAlignment(Qt.AlignTop)
            
            # 确保布局末尾有伸缩项
            if isinstance(content_widget.layout(), QVBoxLayout):
                has_stretch = False
                for i in range(content_widget.layout().count()):
                    item = content_widget.layout().itemAt(i)
                    if item and item.spacerItem():
                        has_stretch = True
                        break
                        
                if not has_stretch:
                    content_widget.layout().addStretch()

    def applyResponsiveLayoutToAllInterfaces(self):
        """为所有接口页面应用响应式布局"""
        # 处理每个界面
        for interface in [self.homeInterface, self.extractInterface, self.clearCacheInterface, 
                        self.historyInterface, self.settingsInterface, self.aboutInterface]:
            if not interface or not interface.layout():
                continue
                
            # 查找每个界面中的ScrollArea
            for i in range(interface.layout().count()):
                item = interface.layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), ScrollArea):
                    # 应用响应式布局
                    self.setResponsiveContentWidget(item.widget())

    def browseOutputDirectory(self):
        """浏览输出目录对话框"""
        if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'customOutputPath'):
            directory = QFileDialog.getExistingDirectory(self, lang.get("directory"), self.settingsInterface.customOutputPath.text())
            if directory:
                self.settingsInterface.customOutputPath.setText(directory)
                self.config_manager.set("custom_output_dir", directory)

    def toggleSaveLogs(self):
        """切换保存日志选项"""
        if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'saveLogsSwitch'):
            self.config_manager.set("save_logs", self.settingsInterface.saveLogsSwitch.isChecked())
            if hasattr(self.settingsInterface, 'settingsLogHandler'):
                self.settingsInterface.settingsLogHandler.info(lang.get("log_save_option_toggled"))

    def toggleAutoOpenOutputDir(self):
        """切换自动打开输出目录选项"""
        if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'autoOpenSwitch'):
            self.config_manager.set("auto_open_output_dir", self.settingsInterface.autoOpenSwitch.isChecked())
            if hasattr(self.settingsInterface, 'settingsLogHandler'):
                self.settingsInterface.settingsLogHandler.info(lang.get("auto_open_toggled"))

    def updateGlobalInputPath(self, path):
        """更新全局输入路径"""
        self.config_manager.set("global_input_path", path)
        
        # 更新所有需要使用这个路径的地方
        
        # 更新提取界面的输入路径框
        if hasattr(self, 'extractInterface') and hasattr(self.extractInterface, 'dirInput'):
            self.extractInterface.dirInput.setText(path)
            
        # 显示成功消息
        if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'settingsLogHandler'):
            self.settingsInterface.settingsLogHandler.success(f"全局输入路径已更新: {path}")
            
        # 保存配置
        self.config_manager.save_config()

    def restoreDefaultInputPath(self):
        """恢复默认输入路径"""
        # 获取默认的Roblox路径
        default_roblox_dir = get_roblox_default_dir()
        if default_roblox_dir:
            # 更新全局输入路径
            self.config_manager.set("global_input_path", default_roblox_dir)
            self.config_manager.save_config()
            
            # 更新输入框显示
            if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'globalInputPathCard') and hasattr(self.settingsInterface.globalInputPathCard, 'inputPathEdit'):
                self.settingsInterface.globalInputPathCard.inputPathEdit.setText(default_roblox_dir)
            
            # 调用更新路径函数
            self.updateGlobalInputPath(default_roblox_dir)
            
            # 显示成功消息
            if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'settingsLogHandler'):
                self.settingsInterface.settingsLogHandler.success(lang.get("default_path_restored") + f": {default_roblox_dir}")

    def applyAlwaysOnTop(self, is_top):
        """应用总是置顶设置"""
        apply_always_on_top(self, is_top)

    def copyPathToClipboard(self, path):
        """复制路径到剪贴板并显示提示"""
        QApplication.clipboard().setText(path)
        
        # 显示复制成功的通知
        InfoBar.success(
            title=lang.get("copied"),
            content=lang.get("path_copied_to_clipboard", path),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )


def main():
    """主函数 - 程序入口点，使用 GUI 界面"""
    try:
        # 设置高DPI缩放
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

        # 确保应用中的目录和资源存在
        app_data_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        os.makedirs(app_data_dir, exist_ok=True)
        

        
        icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "res", "icons")
        os.makedirs(icon_dir, exist_ok=True)

        # 创建应用程序实例
        app = QApplication(sys.argv)

        # 设置应用信息
        app.setApplicationName("Roblox Audio Extractor")
        app.setApplicationDisplayName("Roblox Audio Extractor")
        app.setApplicationVersion(VERSION)
        app.setOrganizationName("JustKanade")

        # 设置应用图标
        try:
            icon_path = resource_path(os.path.join("res", "icons", "logo.png"))
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"无法设置应用图标: {e}")

        # 创建主窗口实例
        main_window = MainWindow()

        # 显示启动画面（可选）
        try:
            splash_icon = resource_path(os.path.join("res", "icons", "logo.png"))
            if os.path.exists(splash_icon):
                splash = SplashScreen(QIcon(splash_icon), main_window)
                splash.setIconSize(QSize(150, 150))
                splash.raise_()

                # 显示启动画面2秒后关闭
                QTimer.singleShot(2000, splash.finish)
        except Exception as e:
            print(f"无法显示启动画面: {e}")

        # 显示主窗口
        main_window.show()

        # 运行应用程序
        return app.exec_()
    except Exception as e:
        logger.error(f"程序出错: {e}")
        traceback.print_exc()
        
        # 保存崩溃日志
        try:
            CentralLogHandler.getInstance().save_crash_log(str(e), traceback.format_exc())
        except Exception as log_e:
            print(f"保存崩溃日志失败: {str(log_e)}")
            
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        # 在终端模式下记录错误
        logger.error(f"发生错误: {str(e)}")
        traceback.print_exc()
        
        # 保存崩溃日志
        crash_log_path = None
        try:
            crash_log_path = CentralLogHandler.getInstance().save_crash_log(str(e), traceback.format_exc())
        except Exception as log_e:
            print(f"保存崩溃日志失败: {str(log_e)}")

        # 尝试显示错误对话框
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            from PyQt5.QtWidgets import QMessageBox

            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle("错误")
            error_dialog.setText(f"发生错误: {str(e)}")
            
            # 添加详细信息
            detailed_text = traceback.format_exc()
            if crash_log_path:
                detailed_text += f"\n\n崩溃日志已保存至: {crash_log_path}"
            error_dialog.setDetailedText(detailed_text)
            
            error_dialog.exec_()
        except:
            pass

        sys.exit(1)