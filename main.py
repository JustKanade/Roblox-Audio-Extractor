


VERSION = "0.17.1"

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


from src.extractors.audio_extractor import RobloxAudioExtractor, ExtractedHistory, ContentHashCache, ProcessingStats, ClassificationMethod, is_ffmpeg_available


from src.utils.file_utils import resource_path, open_directory
from src.utils.log_utils import LogHandler, setup_basic_logging, save_log_to_file
from src.utils.import_utils import import_libs


from src.locale import Language, initialize_lang
from src.locale import lang

from src.management.language_management.language_manager import apply_language, get_language_code


from src.workers.extraction_worker import ExtractionWorker

from src.management.cache_management.cache_cleaner import CacheClearWorker

from src.components.ui.responsive_components import ResponsiveFeatureItem

from src.management.window_management.responsive_handler import apply_responsive_handler
from src.management.window_management.window_utils import apply_always_on_top

from src.management.theme_management.theme_manager import apply_theme_from_config, apply_theme_change, _pre_cache_theme_styles

from src.components.cards.Settings.custom_theme_color_card import CustomThemeColorCard

from src.logging.central_log_handler import CentralLogHandler

from src.components.cards.Settings.auto_check_update_card import AutoCheckUpdateCard
from src.components.cards.Settings.manual_check_update_card import ManualCheckUpdateCard

from src.components.cards.Settings.log_control_card import LogControlCard

from src.components.cards.Settings.ffmpeg_status_card import FFmpegStatusCard

from src.components.cards.Settings.avatar_setting_card import AvatarSettingCard

from src.components.cards.Settings.debug_mode_card import DebugModeCard

from src.components.cards.Settings.always_on_top_card import AlwaysOnTopCard

from src.components.cards.Settings.greeting_setting_card import GreetingSettingCard

from src.config import ConfigManager

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


logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class MainWindow(FluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        
        self.config_manager = ConfigManager()
        
        
        logger.debug("配置管理器初始化完成，使用qconfig系统")
        
        
        if self.config_manager.get("debug_mode_enabled", False):
            print(f"配置文件路径: {self.config_manager.config_file}")
            print(f"QFluentWidgets配置文件路径: {self.config_manager.qfluent_config_file}")
            print(f"QFluentWidgets配置内容: {self.config_manager.get_qfluent_config()}")
            theme_color = self.config_manager.cfg.get(self.config_manager.cfg.themeColor)
            theme_mode = self.config_manager.cfg.get(self.config_manager.cfg.theme)
            print(f"当前主题配置: theme={theme_mode}, themeColor={theme_color.name() if isinstance(theme_color, QColor) else theme_color}")

        
        global lang
        lang = initialize_lang(self.config_manager)
        self.lang = lang  

        
        CentralLogHandler.getInstance().init_with_config(self.config_manager)

        
        self.initWindow()

        
        self.default_dir = self.config_manager.path_manager.get_roblox_default_dir() if self.config_manager.path_manager else ""
        
        
        app_data_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        os.makedirs(app_data_dir, exist_ok=True)
        history_file = os.path.join(app_data_dir, "extracted_history.json")
        
        
        self.download_history = ExtractedHistory(history_file)
        
        
        self.extraction_worker = None
        self.cache_clear_worker = None
        
        
        self.initUI()
        
        
        self.applyThemeFromConfig()
        
        
        self.applyResponsiveLayoutToAllInterfaces()
        
        
        apply_responsive_handler(self, self._adjust_responsive_layout)

    def initWindow(self):
        """初始化窗口设置"""
        
        self.setWindowTitle(lang.get("title"))
        self.resize(750, 630)

        
        self.setMinimumSize(750, 390)

        
        setTheme(Theme.AUTO)

        
        mica_enabled = self.config_manager.cfg.get(self.config_manager.cfg.micaEnabled)
        self.setMicaEffectEnabled(mica_enabled)

        
        try:
            icon_path = resource_path(os.path.join("res", "icons", "logo.png"))
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"无法设置窗口图标: {e}")

        
        
        always_on_top = self.config_manager.get("always_on_top", False)
        if always_on_top:
            apply_always_on_top(self, True)
            
            
            if self.config_manager.get("debug_mode_enabled", False):
                print("窗口初始化时设置置顶")
            
        
        current_theme = self.config_manager.get("theme", "dark")
        other_theme = "light" if current_theme == "dark" else "dark"
        QTimer.singleShot(200, lambda: _pre_cache_theme_styles(self, other_theme))



    def applyThemeFromConfig(self):
        """从配置文件应用主题设置"""
        
        if self.config_manager.get("debug_mode_enabled", False):
            theme_color = self.config_manager.cfg.get(self.config_manager.cfg.themeColor)
            theme_mode = self.config_manager.cfg.get(self.config_manager.cfg.theme)
            print(f"应用主题前配置状态: theme={theme_mode}, themeColor={theme_color.name() if isinstance(theme_color, QColor) else theme_color}")
        
        
        apply_theme_from_config(self, self.config_manager, CentralLogHandler.getInstance())

    def initUI(self):
        """初始化UI组件"""
        
        self.homeInterface = HomeInterface(
            parent=self,
            default_dir=self.default_dir,
            config_manager=self.config_manager,
            lang=lang
        )

        
        self.extractInterface = ExtractAudioInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang,
            default_dir=self.default_dir,
            download_history=self.download_history
        )

        
        self.extractImagesInterface = ExtractImagesInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang
        )

        
        self.extractTexturesInterface = ExtractTexturesInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang
        )

        
        self.clearCacheInterface = ClearCacheInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang,
            default_dir=self.default_dir
        )

        
        self.historyInterface = HistoryInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang,
            download_history=self.download_history
        )

        
        self.settingsInterface = SettingsInterface(
            parent=self,
            config_manager=self.config_manager,
            lang=lang,
            version=VERSION
        )

        
        self.aboutInterface = AboutInterface(
                parent=self,
                config_manager=self.config_manager,
                lang=lang
        )

        
        self.addSubInterface(self.homeInterface, FluentIcon.HOME, lang.get("home"))
        
        
        self.navigationInterface.addSeparator()

        
        extract_tree = self.navigationInterface.addItem(
            routeKey="extract",
            icon=FluentIcon.DOWNLOAD,
            text=lang.get("extract"),
            onClick=None,
            selectable=False,
            position=NavigationItemPosition.SCROLL
        )
        
        
        self.stackedWidget.addWidget(self.extractInterface)
        
        
        self.navigationInterface.addItem(
            routeKey=self.extractInterface.objectName(),
            icon=FluentIcon.MUSIC,
            text=lang.get("extract_audio"),
            onClick=lambda: self.switchTo(self.extractInterface),
            selectable=True,
            position=NavigationItemPosition.SCROLL,
            parentRouteKey="extract"
        )
        
        
        self.stackedWidget.addWidget(self.extractImagesInterface)
        self.stackedWidget.addWidget(self.extractTexturesInterface)
        
        self.navigationInterface.addItem(
            routeKey=self.extractImagesInterface.objectName(),
            icon=FluentIcon.PHOTO,
            text=lang.get("extract_images"),
            onClick=lambda: self.switchTo(self.extractImagesInterface),
            selectable=True,
            position=NavigationItemPosition.SCROLL,
            parentRouteKey="extract"
        )
        
        self.navigationInterface.addItem(
            routeKey=self.extractTexturesInterface.objectName(),
            icon=FluentIcon.PALETTE,
            text=lang.get("extract_textures"),
            onClick=lambda: self.switchTo(self.extractTexturesInterface),
            selectable=True,
            position=NavigationItemPosition.SCROLL,
            parentRouteKey="extract"
        )
        
        
        extract_tree.setExpanded(False)
        
        self.addSubInterface(self.clearCacheInterface, FluentIcon.DELETE, lang.get("clear_cache"), position=NavigationItemPosition.SCROLL)
        self.addSubInterface(self.historyInterface, FluentIcon.HISTORY, lang.get("view_history"), position=NavigationItemPosition.SCROLL)

        
        
        try:
            from src.components.avatar import AvatarWidget
            
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

        
        self.navigationInterface.addItem(
            routeKey="launch",
            icon=FluentIcon.PLAY,
            text=self.lang.get("launch"),
            onClick=self.onLaunchButtonClicked,
            selectable=False,
            position=NavigationItemPosition.BOTTOM
        )
     
        self.addSubInterface(self.settingsInterface, FluentIcon.SETTING, lang.get("settings"),
                             position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.aboutInterface, FluentIcon.INFO, lang.get("about"),
                             position=NavigationItemPosition.BOTTOM)

        
        acrylic_enabled = self.config_manager.cfg.get(self.config_manager.cfg.acrylicEnabled)
        self.navigationInterface.setAcrylicEnabled(acrylic_enabled)

        
        self.switchTo(self.homeInterface)

        
        self.stackedWidget.currentChanged.connect(self.onInterfaceChanged)
        
        
        self.homeInterface.copyPathToClipboard = self.copyPathToClipboard
        
        
        self.homeInterface.switchToInterface = self.switchToInterfaceByName
        
        
        self.homeInterface.add_welcome_message()

    def _adjust_responsive_layout(self, window_width):
        """根据窗口宽度调整响应式布局"""
        try:
            
            if hasattr(self, 'homeInterface') and isinstance(self.homeInterface, HomeInterface):
                self.homeInterface.adjust_responsive_layout(window_width)
        except Exception as e:
            
            pass
            
    def switchToInterfaceByName(self, interface_name):
        """通过界面名称切换界面"""
        try:
            
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
            
            if current_widget == self.historyInterface:
                self.historyInterface.refreshHistoryInterface()
            
            elif current_widget == self.extractInterface:
                if hasattr(current_widget, 'updateThreadsValue'):
                    current_widget.updateThreadsValue()
        except Exception as e:
            pass
          
    def setExtractStyles(self):
        """设置提取音频界面的样式"""
        try:
            theme = self.config_manager.get("theme", "dark")
            
            
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
        
        from src.components.Greetings import TimeGreetings
        
        
        current_language = lang.get_language_name()
        
        language_code = 'zh' if lang.current_language == lang.CHINESE else 'en'
        
        
        greeting_enabled = self.config_manager.get("greeting_enabled", True)
        if greeting_enabled:
            
            TimeGreetings.show_greeting(language_code)
        
        
        if hasattr(self, 'homeInterface') and hasattr(self.homeInterface, 'logHandler'):
            self.homeInterface.logHandler.info(lang.get('welcome_message'))
            self.homeInterface.logHandler.info(lang.get('about_version'))
            self.homeInterface.logHandler.info(f"{lang.get('default_dir')}: {self.default_dir}")
            self.homeInterface.logHandler.info(lang.get("config_file_location", self.config_manager.config_file))
            
    def onThemeChanged(self, theme_name):
        """主题更改事件处理"""
        
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
        
        global_input_path = self.config_manager.get("global_input_path", "")
        
        
        selected_dir = global_input_path if global_input_path else self.dirInput.text()
        
        
        if global_input_path and self.dirInput.text() != global_input_path:
            self.dirInput.setText(global_input_path)
            self.extractLogHandler.info(lang.get("using_global_input_path", "使用全局输入路径") + f": {global_input_path}")

        
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

        
        classification_method = ClassificationMethod.DURATION if self.durationRadio.isChecked() else ClassificationMethod.SIZE

        
        if classification_method == ClassificationMethod.DURATION and not is_ffmpeg_available():
            result = MessageBox(
                lang.get("confirm"),
                lang.get("ffmpeg_not_installed"),
                self
            )

            if not result.exec():
                self.extractLogHandler.warning(lang.get("operation_cancelled"))
                return

        
        custom_output_dir = self.config_manager.get("custom_output_dir", "")
        
        
        # 获取多进程配置
        use_multiprocessing = self.config_manager.get("useMultiprocessing", False)
        conservative_multiprocessing = self.config_manager.get("conservativeMultiprocessing", True)
        
        self.extraction_worker = ExtractionWorker(
            selected_dir,
            num_threads,
            self.download_history,
            classification_method,
            custom_output_dir,
            True,  # scan_db 默认为True
            False,  # convert_enabled 默认为False  
            "MP3",  # convert_format 默认为MP3
            use_multiprocessing,
            conservative_multiprocessing
        )

        
        self.extraction_worker.progressUpdated.connect(self.updateExtractionProgress)
        self.extraction_worker.finished.connect(self.extractionFinished)
        self.extraction_worker.logMessage.connect(self.handleExtractionLog)

        
        self.extractButton.hide()
        self.cancelButton.show()
        self.progressBar.setValue(0)
        self.progressLabel.setText(lang.get("processing"))

        
        self.extractionStateTooltip = StateToolTip(
            lang.get("task_running"),
            lang.get("processing"),
            self
        )
        self.extractionStateTooltip.show()

        
        self.extraction_worker.start()
    def cancelExtraction(self):
        """取消提取操作"""
        if self.extraction_worker and self.extraction_worker.isRunning():
            self.extraction_worker.cancel()

            
            if hasattr(self, 'extractionStateTooltip'):
                self.extractionStateTooltip.setContent(lang.get("task_canceled"))
                self.extractionStateTooltip.setState(True)
                
                QTimer.singleShot(2000, self.extractionStateTooltip.close)

            
            self.cancelButton.hide()
            self.extractButton.show()

            
            self.progressBar.setValue(0)
            self.progressLabel.setText(lang.get("ready"))

            self.handleExtractionLog(lang.get("canceled_by_user"), "warning")

    def updateExtractionProgress(self, current, total, elapsed, speed):
        """更新提取进度"""
        
        progress = min(100, int((current / total) * 100)) if total > 0 else 0

        
        remaining = (total - current) / speed if speed > 0 else 0
        remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"

        
        status_text = f"{progress}% - {current}/{total} | {speed:.1f} files/s"

        
        self.progressBar.setValue(progress)
        self.progressLabel.setText(status_text)
        
        if hasattr(self, 'extractionStateTooltip'):
            self.extractionStateTooltip.setContent(status_text)

    def extractionFinished(self, result):
        """提取完成处理"""
        
        self.cancelButton.hide()
        self.extractButton.show()

        
        self.progressBar.setValue(0)
        self.progressLabel.setText(lang.get("ready"))

        if result.get("success", False):
            
            if "processed" in result and result["processed"] > 0:
                self.extractLogHandler.success(lang.get("extraction_complete"))
                self.extractLogHandler.info(lang.get("processed", result['processed']))
                self.extractLogHandler.info(lang.get("skipped_duplicates", result.get('duplicates', 0)))
                self.extractLogHandler.info(lang.get("skipped_already_processed", result.get('already_processed', 0)))
                self.extractLogHandler.info(lang.get("errors", result.get('errors', 0)))
                self.extractLogHandler.info(lang.get("time_spent", result.get('duration', 0)))
                self.extractLogHandler.info(lang.get("files_per_sec", result.get('files_per_second', 0)))
                self.extractLogHandler.info(lang.get("output_dir", result.get('output_dir', '')))

                
                final_dir = result.get("output_dir", "")
                
                audio_dir = os.path.join(final_dir, "Audio")

                
                if final_dir and os.path.exists(final_dir) and self.config_manager.get("auto_open_output_dir", True):
                    
                    if os.path.exists(audio_dir):
                        open_success = open_directory(audio_dir)
                        if open_success:
                            self.extractLogHandler.info(lang.get("opening_output_dir", lang.get("audio_folder")))
                        else:
                            self.extractLogHandler.info(lang.get("manual_navigate", audio_dir))
                    else:
                        
                        open_success = open_directory(final_dir)
                        if open_success:
                            self.extractLogHandler.info(lang.get("opening_output_dir", lang.get("ogg_category")))
                        else:
                            self.extractLogHandler.info(lang.get("manual_navigate", final_dir))

                
                if hasattr(self, 'extractionStateTooltip'):
                    self.extractionStateTooltip.setContent(lang.get("extraction_complete"))
                    self.extractionStateTooltip.setState(True)
                    
                    QTimer.singleShot(2000, self.extractionStateTooltip.close)

                
                InfoBar.success(
                    title=lang.get("task_completed"),
                    content=lang.get("extraction_complete"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )

                
                self.historyInterface.refreshHistoryInterface()
            else:
                self.extractLogHandler.warning(lang.get("no_files_processed"))

                
                if hasattr(self, 'extractionStateTooltip'):
                    self.extractionStateTooltip.setContent(lang.get("no_files_processed"))
                    self.extractionStateTooltip.setState(True)
                    
                    QTimer.singleShot(2000, self.extractionStateTooltip.close)
        else:
            
            self.extractLogHandler.error(lang.get("error_occurred", result.get('error', '')))

            
            if hasattr(self, 'extractionStateTooltip'):
                self.extractionStateTooltip.setContent(lang.get("task_failed"))
                self.extractionStateTooltip.setState(False)
                
                QTimer.singleShot(2000, self.extractionStateTooltip.close)

            
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
        
        result = MessageBox(
            lang.get("clear_cache"),
            lang.get("confirm_clear_cache"),
            self
        )

        if not result.exec():
            
            self.clearCacheInterface.logHandler.info(lang.get("operation_cancelled"))
            return

        
        self.cache_clear_worker = CacheClearWorker()

        
        self.cache_clear_worker.progressUpdated.connect(self.updateCacheProgress)
        self.cache_clear_worker.finished.connect(self.cacheClearFinished)

        
        
        self.clearCacheInterface.showClearButton(False)
        self.clearCacheInterface.showCancelButton(True)
        self.clearCacheInterface.updateProgressBar(0)
        self.clearCacheInterface.updateProgressLabel(lang.get("processing"))

        
        self.cacheStateTooltip = StateToolTip(
            lang.get("task_running"),
            lang.get("processing"),
            self
        )
        self.cacheStateTooltip.show()

        
        self.cache_clear_worker.start()

    def cancelClearCache(self):
        """取消缓存清理操作"""
        if self.cache_clear_worker and self.cache_clear_worker.isRunning():
            self.cache_clear_worker.cancel()

            
            if hasattr(self, 'cacheStateTooltip'):
                self.cacheStateTooltip.setContent(lang.get("task_canceled"))
                self.cacheStateTooltip.setState(True)
                
                QTimer.singleShot(2000, self.cacheStateTooltip.close)

            
            
            self.clearCacheInterface.showCancelButton(False)
            self.clearCacheInterface.showClearButton(True)

            
            self.clearCacheInterface.updateProgressBar(0)
            self.clearCacheInterface.updateProgressLabel(lang.get("ready"))

            self.clearCacheInterface.logHandler.warning(lang.get("canceled_by_user"))

    def updateCacheProgress(self, current, total):
        """更新缓存清理进度"""
        
        progress = min(100, int((current / total) * 100)) if total > 0 else 0

        
        status_text = f"{progress}% - {current}/{total}"

        
        
        self.clearCacheInterface.updateProgressBar(progress)
        self.clearCacheInterface.updateProgressLabel(status_text)

        
        if hasattr(self, 'cacheStateTooltip'):
            self.cacheStateTooltip.setContent(status_text)

    def cacheClearFinished(self, success, cleared_files, total_files, error_msg):
        """缓存清理完成处理"""
        
        
        self.clearCacheInterface.showCancelButton(False)
        self.clearCacheInterface.showClearButton(True)

        
        self.clearCacheInterface.updateProgressBar(0)
        self.clearCacheInterface.updateProgressLabel(lang.get("ready"))

        if success:
            if cleared_files > 0:
                self.clearCacheInterface.logHandler.success(lang.get("cache_cleared", cleared_files, total_files))

                
                if hasattr(self, 'cacheStateTooltip'):
                    self.cacheStateTooltip.setContent(lang.get("cache_cleared", cleared_files, total_files))
                    self.cacheStateTooltip.setState(True)
                    
                    QTimer.singleShot(2000, self.cacheStateTooltip.close)
                
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

                
                if hasattr(self, 'cacheStateTooltip'):
                    self.cacheStateTooltip.setContent(lang.get("no_cache_found"))
                    self.cacheStateTooltip.setState(True)
                    
                    QTimer.singleShot(2000, self.cacheStateTooltip.close)
        else:
            
            self.clearCacheInterface.logHandler.error(lang.get("clear_cache_failed", error_msg))

            
            if hasattr(self, 'cacheStateTooltip'):
                self.cacheStateTooltip.setContent(lang.get("task_failed"))
                self.cacheStateTooltip.setState(False)
                
                QTimer.singleShot(2000, self.cacheStateTooltip.close)

            
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
            
            if record_type == "all":
                self.download_history.clear_history()
                message = lang.get("all_history_cleared")
            else:
                
                record_type_str = str(record_type)
                self.download_history.clear_history(record_type_str)
                message = lang.get("history_type_cleared").format(record_type_str.capitalize())

            
            QTimer.singleShot(100, self.historyInterface.refreshHistoryInterfaceAfterClear)
                
            
            if hasattr(self.historyInterface, 'logHandler'):
                self.historyInterface.logHandler.success(message)

            
            QTimer.singleShot(200, lambda: InfoBar.success(
                title=lang.get("task_completed"),
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            ))
            
            
            if hasattr(self, 'extractInterface') and hasattr(self.extractInterface, 'updateHistorySize'):
                self.extractInterface.updateHistorySize()
        
        except Exception as e:
            
            if hasattr(self.historyInterface, 'logHandler'):
                self.historyInterface.logHandler.error(lang.get("error_occurred", str(e)))
            traceback.print_exc()

            
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
        
        if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'languageCombo'):
            selected_language = self.settingsInterface.languageCombo.currentText()
            current_language = lang.get_language_name()
            
            
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
            
        
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        
        if content_widget.layout():
            content_widget.layout().setAlignment(Qt.AlignTop)
            
            
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
        
        for interface in [self.homeInterface, self.extractInterface, self.clearCacheInterface, 
                        self.historyInterface, self.settingsInterface, self.aboutInterface]:
            if not interface or not interface.layout():
                continue
                
            
            for i in range(interface.layout().count()):
                item = interface.layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), ScrollArea):
                    
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
        """更新全局输入路径（保持向后兼容）"""
        
        if hasattr(self.config_manager, 'path_manager') and self.config_manager.path_manager:
            success = self.config_manager.path_manager.set_global_input_path(path)
            if success and hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'settingsLogHandler'):
                self.settingsInterface.settingsLogHandler.success(f"{self.lang.get('global_input_path_updated')}: {path}")
        else:
            
            self.config_manager.set("global_input_path", path)
            self.config_manager.save_config()
            
            
            if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'settingsLogHandler'):
                self.settingsInterface.settingsLogHandler.success(f"{self.lang.get('global_input_path_updated')}: {path}")

    def restoreDefaultInputPath(self):
        """恢复默认输入路径"""
        
        if hasattr(self.config_manager, 'path_manager') and self.config_manager.path_manager:
            default_roblox_dir = self.config_manager.path_manager.restore_default_path()
            if default_roblox_dir and hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'settingsLogHandler'):
                self.settingsInterface.settingsLogHandler.success(lang.get("default_path_restored", "默认路径已恢复") + f": {default_roblox_dir}")
        else:
            
            from src.utils.file_utils import get_roblox_default_dir
            default_roblox_dir = get_roblox_default_dir()
            if default_roblox_dir:
                self.config_manager.set("global_input_path", default_roblox_dir)
                self.config_manager.save_config()
                
                
                if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'globalInputPathCard') and hasattr(self.settingsInterface.globalInputPathCard, 'inputPathEdit'):
                    self.settingsInterface.globalInputPathCard.inputPathEdit.setText(default_roblox_dir)
                
                
                if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'settingsLogHandler'):
                    self.settingsInterface.settingsLogHandler.success(lang.get("default_path_restored", "默认路径已恢复") + f": {default_roblox_dir}")

    def applyAlwaysOnTop(self, is_top):
        """应用总是置顶设置"""
        apply_always_on_top(self, is_top)
        
        
        if hasattr(self, 'settingsInterface') and hasattr(self.settingsInterface, 'settingsLogHandler'):
            self.settingsInterface.settingsLogHandler.info(self.lang.get("always_on_top_toggled"))

    def copyPathToClipboard(self, path):
        """复制路径到剪贴板并显示提示"""
        QApplication.clipboard().setText(path)
        
        
        InfoBar.success(
            title=lang.get("copied"),
            content=lang.get("path_copied_to_clipboard", path),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def onLaunchButtonClicked(self):
        """启动按钮点击事件处理"""
        import subprocess
        import platform
        
        
        launch_file = self.config_manager.get("launch_file", "")
        
        if not launch_file:
            
            InfoBar.warning(
                title=lang.get("launch_failed"),
                content=lang.get("no_launch_file_set"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return
        
        
        if not os.path.exists(launch_file):
            InfoBar.error(
                title=lang.get("launch_failed"),
                content=lang.get("file_not_found", launch_file),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return
        
        try:
            
            system = platform.system()
            if system == "Windows":
                os.startfile(launch_file)
            elif system == "Darwin":  
                subprocess.run(["open", launch_file])
            else:  
                subprocess.run(["xdg-open", launch_file])
            
            
            InfoBar.success(
                title=lang.get("launch_success"),
                content=lang.get("file_launched", os.path.basename(launch_file)),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            
            InfoBar.error(
                title=lang.get("launch_failed"),
                content=lang.get("launch_error", str(e)),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )


def main():
    """主函数 - 程序入口点，使用 GUI 界面"""
    try:
        
        from src.config.config_manager import ConfigManager
        temp_config = ConfigManager()
        dpi_scale = temp_config.get("dpi_scale", "Auto")
        
        
        if dpi_scale == "Auto":
            
            QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        else:
            
            os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
            os.environ["QT_SCALE_FACTOR"] = str(dpi_scale)
        
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

        
        app_data_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        os.makedirs(app_data_dir, exist_ok=True)
        

        
        icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "res", "icons")
        os.makedirs(icon_dir, exist_ok=True)

        
        app = QApplication(sys.argv)

        
        app.setApplicationName("Roblox Audio Extractor")
        app.setApplicationDisplayName("Roblox Audio Extractor")
        app.setApplicationVersion(VERSION)
        app.setOrganizationName("JustKanade")

        
        try:
            icon_path = resource_path(os.path.join("res", "icons", "logo.png"))
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"无法设置应用图标: {e}")

        
        main_window = MainWindow()

        
        try:
            splash_icon = resource_path(os.path.join("res", "icons", "logo.png"))
            if os.path.exists(splash_icon):
                splash = SplashScreen(QIcon(splash_icon), main_window)
                splash.setIconSize(QSize(200, 200))
                splash.raise_()

                
                QTimer.singleShot(2000, splash.finish)
        except Exception as e:
            print(f"无法显示启动画面: {e}")

        
        main_window.show()

        
        return app.exec_()
    except Exception as e:
        logger.error(f"程序出错: {e}")
        traceback.print_exc()
        
        
        try:
            CentralLogHandler.getInstance().save_crash_log(str(e), traceback.format_exc())
        except Exception as log_e:
            print(f"Failed to save crash log: {str(log_e)}")
            
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        
        logger.error(f"发生错误: {str(e)}")
        traceback.print_exc()
        
        
        crash_log_path = None
        try:
            crash_log_path = CentralLogHandler.getInstance().save_crash_log(str(e), traceback.format_exc())
        except Exception as log_e:
            print(f"Failed to save crash log: {str(log_e)}")

        
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            from PyQt5.QtWidgets import QMessageBox

            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle("错误")
            error_dialog.setText(f"发生错误: {str(e)}")
            
            
            detailed_text = traceback.format_exc()
            if crash_log_path:
                detailed_text += f"\n\nCrash log saved to: {crash_log_path}"
            error_dialog.setDetailedText(detailed_text)
            
            error_dialog.exec_()
        except:
            pass

        sys.exit(1)