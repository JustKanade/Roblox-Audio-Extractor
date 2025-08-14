#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础提取界面类 - 包含音频和字体提取界面的共同逻辑
Base Extract Interface - Contains common logic for audio and font extraction interfaces
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QButtonGroup,
    QSizePolicy, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, QPoint

from qfluentwidgets import (
    CardWidget, BodyLabel, StrongBodyLabel,
    ScrollArea, PushButton, PrimaryPushButton, 
    FluentIcon, CaptionLabel, ProgressBar, RadioButton,
    TextEdit, IconWidget, SpinBox, LineEdit, InfoBar,
    MessageBox, StateToolTip, InfoBarPosition, ComboBox, CheckBox,
    RoundMenu, Action, DropDownPushButton, TransparentPushButton,
    SettingCardGroup, SettingCard, SwitchSettingCard, SwitchButton
)

import os
import multiprocessing
import time
from functools import partial
from abc import ABCMeta, abstractmethod

from src.utils.log_utils import LogHandler
from src.utils.safe_tooltip_manager import SafeStateTooltipManager

from src.management.theme_management.interface_theme_mixin import InterfaceThemeMixin

# 创建兼容的元类
class QWidgetMeta(type(QWidget), ABCMeta):
    pass
from src.utils.file_utils import open_directory
from src.logging.central_log_handler import CentralLogHandler
from src.components.cards.recent_activity_card import RecentActivityCard

# 尝试导入LogControlCard
try:
    from src.components.cards.Settings.log_control_card import LogControlCard
except ImportError:
    LogControlCard = None


class BaseExtractInterface(QWidget, InterfaceThemeMixin, metaclass=QWidgetMeta):
    """基础提取界面类 - 抽象基类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None, default_dir=None, download_history=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.lang = lang
        self.default_dir = default_dir
        self.download_history = download_history
        self._parent_window = parent
        
        # 获取路径管理器
        self.path_manager = getattr(config_manager, 'path_manager', None) if config_manager else None
        
        # 设置大小策略，防止界面拉伸
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 初始化工作线程
        self.extraction_worker = None
        self.update_timer = None
        
        # 确保语言对象存在，否则创建空的语言处理函数
        if self.lang is None:
            # 创建一个返回默认值的函数
            self.get_text = lambda key, *args, **kwargs: kwargs.get("default", "")
        else:
            # 使用lang对象的get方法
            self.get_text = self.lang.get
        
        # 初始化安全状态提示管理器
        self.tooltip_manager = SafeStateTooltipManager(self, self.get_text)
        
        # 初始化界面
        self.initUI()
        # 应用样式
        self.setInterfaceStyles()
        
        # 连接路径管理器信号实现实时同步
        if self.path_manager:
            self.path_manager.globalInputPathChanged.connect(self.onGlobalInputPathChanged)
        
    @abstractmethod
    def getExtractionType(self) -> str:
        """获取提取类型（如'audio', 'font'）"""
        pass
        
    @abstractmethod
    def getWorkerClass(self):
        """获取工作线程类"""
        pass
        
    @abstractmethod
    def getClassificationMethods(self) -> list:
        """获取分类方法列表"""
        pass
        
    @abstractmethod
    def getClassificationMethodKey(self) -> str:
        """获取分类方法配置键"""
        pass
        
    @abstractmethod
    def getThreadsConfigKey(self) -> str:
        """获取线程数配置键"""
        pass
        
    @abstractmethod
    def createSpecificSettingCards(self, settings_group):
        """创建特定的设置卡片（子类实现）"""
        pass
        
    @abstractmethod
    def getExtractionParameters(self):
        """获取提取参数（子类实现）"""
        pass
        
    def initUI(self):
        """初始化界面"""
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
        extraction_type = self.getExtractionType()
        settings_group = SettingCardGroup(
            self.get_text(f"extract_{extraction_type}_title", f"{extraction_type.title()} Extraction Settings")
        )
        
        # 路径选择卡片
        self.createPathCard(settings_group)
        
        # 分类方法选择卡片
        self.createClassificationCard(settings_group)
        
        # 线程数设置卡片
        self.createThreadsCard(settings_group)
        
        # 创建特定的设置卡片（子类实现）
        self.createSpecificSettingCards(settings_group)

        # 日志管理卡片
        if LogControlCard:
            self.log_management_card = LogControlCard(
                parent=self,
                lang=self.lang,
                central_log_handler=CentralLogHandler.getInstance()
            )
            settings_group.addSettingCard(self.log_management_card)

        content_layout.addWidget(settings_group)

        # 操作控制卡片
        self.createControlCard(content_layout)

        # 日志输出卡片
        self.createLogCard(content_layout)

        # 设置滚动区域
        scroll.setWidget(content_widget)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def createPathCard(self, settings_group):
        """创建路径选择卡片"""
        self.path_card = SettingCard(
            FluentIcon.FOLDER,
            self.get_text("input_dir", "Input Directory"),
            self.get_text("input_dir_placeholder", "Select directory containing files")
        )
        
        # 创建路径选择控件容器
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 20, 0)
        path_layout.setSpacing(8)
        
        self.path_edit = LineEdit()
        # 使用路径管理器获取有效路径
        effective_path = self._getEffectiveInputPath()
        self.path_edit.setText(effective_path)
        self.path_edit.setClearButtonEnabled(True)
        self.path_edit.setPlaceholderText(self.get_text("input_dir_placeholder", "Select directory containing files"))
        self.path_edit.setFixedWidth(350)
        path_layout.addWidget(self.path_edit)
        
        self.browse_button = PushButton(self.get_text("browse", "Browse"))
        self.browse_button.setIcon(FluentIcon.FOLDER_ADD)
        self.browse_button.setFixedSize(120, 32)
        self.browse_button.clicked.connect(self.browseDirectory)
        path_layout.addWidget(self.browse_button)
        
        # 将路径控件添加到卡片
        self.path_card.hBoxLayout.addWidget(path_widget)
        settings_group.addSettingCard(self.path_card)

    def createClassificationCard(self, settings_group):
        """创建分类方法选择卡片"""
        extraction_type = self.getExtractionType()
        self.classification_card = SettingCard(
            FluentIcon.TAG if extraction_type == "font" else FluentIcon.MENU,
            self.get_text(f"{extraction_type}_classification_method", "Classification Method"),
            self.get_text(f"info_{extraction_type}_default_category", "Default classification")
        )
        
        # 创建分类方法选择控件容器
        classification_widget = QWidget()
        classification_layout = QHBoxLayout(classification_widget)
        classification_layout.setContentsMargins(0, 0, 20, 0)
        classification_layout.setSpacing(8)
        
        self.classification_combo = ComboBox()
        methods = self.getClassificationMethods()
        self.classification_combo.addItems(methods)
        
        # 设置默认选项
        self.loadClassificationMethod()
        
        # 根据不同提取器类型设置合适的按钮宽度
        if extraction_type == "font":
            button_width = 160
        elif extraction_type == "translation":
            button_width = 190 # 翻译选项文本较长，需要更宽的按钮
        else:  # audio 和其他类型
            button_width = 140  # 比原来的120像素更宽一些
        
        self.classification_combo.setFixedSize(button_width, 32)
        self.classification_combo.currentIndexChanged.connect(self.updateClassificationInfo)
        
        classification_layout.addStretch()
        classification_layout.addWidget(self.classification_combo)
        
        # 将分类方法控件添加到卡片
        self.classification_card.hBoxLayout.addWidget(classification_widget)
        settings_group.addSettingCard(self.classification_card)

    def createThreadsCard(self, settings_group):
        """创建线程数设置卡片"""
        self.threads_card = SettingCard(
            FluentIcon.SPEED_HIGH,
            self.get_text("threads", "Threads"),
            self.get_text("threads_info", "Set number of concurrent processing threads")
        )
        
        # 创建线程数控件容器
        threads_widget = QWidget()
        threads_layout = QHBoxLayout(threads_widget)
        threads_layout.setContentsMargins(0, 0, 20, 0)
        threads_layout.setSpacing(8)
        
        self.threads_spin = SpinBox()
        self.threads_spin.setRange(1, 128)
        # 设置默认值为CPU核心数的2倍，但不超过32
        default_threads = min(32, multiprocessing.cpu_count() * 2)
        saved_threads = default_threads
        if self.config_manager:
            saved_threads = self.config_manager.get(self.getThreadsConfigKey(), default_threads)
        self.threads_spin.setValue(saved_threads)
        self.threads_spin.setFixedSize(120, 32)
        
        threads_layout.addStretch()
        threads_layout.addWidget(self.threads_spin)
        
        # 将线程数控件添加到卡片
        self.threads_card.hBoxLayout.addWidget(threads_widget)
        settings_group.addSettingCard(self.threads_card)

    def createControlCard(self, content_layout):
        """创建操作控制卡片"""
        control_card = CardWidget()
        control_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(25, 20, 25, 20)
        control_layout.setSpacing(15)
        content_layout.addWidget(control_card)

        # 进度显示
        progress_layout = QVBoxLayout()
        self.progressBar = ProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)
        self.progressLabel = CaptionLabel(self.get_text("ready", "Ready"))
        self.progressLabel.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progressBar)
        progress_layout.addWidget(self.progressLabel)

        control_layout.addLayout(progress_layout)

        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        # 添加弹性空间，将按钮推至右侧
        button_layout.addStretch()

        # 取消按钮
        self.cancelButton = PushButton(self.get_text("cancel", "Cancel"))
        self.cancelButton.setIcon(FluentIcon.CLOSE)
        self.cancelButton.setFixedSize(120, 35)
        self.cancelButton.clicked.connect(self.cancelExtraction)
        self.cancelButton.hide()
        button_layout.addWidget(self.cancelButton)

        # 开始提取按钮
        extraction_type = self.getExtractionType()
        self.extractButton = PrimaryPushButton(
            self.get_text(f"extract")
        )
        self.extractButton.setIcon(FluentIcon.PLAY)
        self.extractButton.setFixedSize(130, 35)
        self.extractButton.clicked.connect(self.startExtraction)
        button_layout.addWidget(self.extractButton)

        control_layout.addLayout(button_layout)

    def createLogCard(self, content_layout):
        """创建日志输出卡片"""
        # 最近活动卡片（统一的日志显示组件）
        self.recent_activity_card = RecentActivityCard(
            parent=self,
            lang=self.lang,
            config_manager=self.config_manager
        )
        content_layout.addWidget(self.recent_activity_card)

        # 使用RecentActivityCard中的日志处理器
        self.extractLogHandler = self.recent_activity_card.log_handler
        
        # 兼容性：保留logTextEdit引用，指向RecentActivityCard的文本编辑器
        self.logTextEdit = self.recent_activity_card.log_text_edit

    def loadClassificationMethod(self):
        """加载分类方法设置"""
        # 子类可以重写此方法以实现特定的分类方法加载逻辑
        pass

    @abstractmethod
    def updateClassificationInfo(self):
        """更新分类方法信息（子类实现）"""
        pass

    def _getEffectiveInputPath(self):
        """获取有效的输入路径"""
        # 优先使用全局输入路径
        if self.path_manager:
            global_path = self.path_manager.get_global_input_path()
            if global_path and os.path.isdir(global_path):
                return global_path
        
        # 使用保存的输入路径
        if self.config_manager:
            extraction_type = self.getExtractionType()
            saved_path = self.config_manager.get(f"last_{extraction_type}_input_dir", "")
            if saved_path and os.path.isdir(saved_path):
                return saved_path
        
        # 使用默认路径
        if self.default_dir and os.path.isdir(self.default_dir):
            return self.default_dir
        
        return ""

    def onGlobalInputPathChanged(self, new_path):
        """全局输入路径改变时的处理"""
        if new_path and os.path.isdir(new_path):
            self.path_edit.setText(new_path)
            extraction_type = self.getExtractionType()
            self.extractLogHandler.info(
                f"{self.get_text('global_input_path_updated', 'Global input path updated')}: {new_path}"
            )

    def browseDirectory(self):
        """浏览目录对话框"""
        current_path = self.path_edit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(
            self,
            self.get_text("select_directory", "Select Directory"),
            current_path
        )
        if directory:
            self.path_edit.setText(directory)

    def startExtraction(self):
        """开始提取（模板方法）"""
        # 获取有效输入路径
        input_dir = self._getEffectiveInputPath()
        
        # 更新界面显示的路径
        if self.path_edit.text().strip() != input_dir:
            self.path_edit.setText(input_dir)
            self.extractLogHandler.info(
                f"{self.get_text('using_global_input_path', 'Using global input path')}: {input_dir}"
            )
        
        if not input_dir or not os.path.isdir(input_dir):
            InfoBar.error(
                title=self.get_text("error", "Error"),
                content=self.get_text("invalid_dir", "Invalid directory path"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        # 保存配置
        self.saveConfiguration(input_dir)

        # 更新UI状态
        self.showExtractButton(False)
        self.showCancelButton(True)
        self.updateProgressBar(0)
        self.updateProgressLabel(self.get_text("preparing", "Preparing"))
        
        # 获取提取参数
        params = self.getExtractionParameters()
        
        # 创建工作线程
        worker_class = self.getWorkerClass()
        self.extraction_worker = worker_class(*params)

        # 连接信号
        self.extraction_worker.progressUpdated.connect(self.updateExtractionProgress)
        self.extraction_worker.finished.connect(self.extractionFinished)
        self.extraction_worker.logMessage.connect(self.handleExtractionLog)
        
        # 创建左上角进度通知
        extraction_type = self.getExtractionType()
        task_running_text = self.get_text("task_running", "Task Running")
        processing_text = self.get_text("processing", "Processing")
        
        # 使用安全的tooltip管理器创建tooltip
        self.tooltip_manager.create_tooltip(task_running_text, processing_text)
        
        # 创建定时器以定期更新UI
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(lambda: None)  # 仅触发Qt事件循环
        self.update_timer.start(100)  # 每100毫秒更新一次

        # 启动工作线程
        self.extraction_worker.start()

    def updateThreadsValue(self):
        """更新线程数设置值（从配置中同步）"""
        if self.config_manager and hasattr(self, 'threads_spin'):
            default_threads = min(32, multiprocessing.cpu_count() * 2)
            saved_threads = self.config_manager.get(self.getThreadsConfigKey(), default_threads)
            self.threads_spin.setValue(saved_threads)

    def saveConfiguration(self, input_dir):
        """保存配置"""
        if self.config_manager:
            extraction_type = self.getExtractionType()
            
            # 保存线程数
            threads = self.threads_spin.value()
            self.config_manager.set(self.getThreadsConfigKey(), threads)
            
            # 保存输入路径
            self.config_manager.set(f"last_{extraction_type}_input_dir", input_dir)

    def cancelExtraction(self):
        """取消提取"""
        if self.extraction_worker and self.extraction_worker.isRunning():
            self.extraction_worker.cancel()
            self.updateProgressLabel(self.get_text("cancelling", "Cancelling..."))
            
            # 使用安全的tooltip管理器更新取消状态
            cancel_text = self.get_text("task_canceled", "Task Canceled")
            self.tooltip_manager.update_cancel_tooltip(cancel_text, 2000)
            
            # 恢复UI状态
            self.showExtractButton(True)
            self.showCancelButton(False)
            self.updateProgressBar(0)
            self.updateProgressLabel(self.get_text("ready", "Ready"))

    def updateExtractionProgress(self, current, total, elapsed_time, speed):
        """更新提取进度"""
        if total > 0:
            progress = int((current / total) * 100)
            self.progressBar.setValue(progress)
            
            speed_text = f"{speed:.1f} files/s" if speed > 0 else "0.0 files/s"
            progress_text = f"{current}/{total} ({progress}%) - {speed_text}"
            self.updateProgressLabel(progress_text)
            
            # 使用安全的tooltip管理器更新进度
            self.tooltip_manager.update_progress_tooltip(progress_text)

    def extractionFinished(self, result):
        """提取完成处理"""
        # 停止定时器
        if self.update_timer:
            self.update_timer.stop()
            self.update_timer = None

        # 更新UI状态
        self.showExtractButton(True)
        self.showCancelButton(False)
        
        success = result.get("success", False)
        extraction_type = self.getExtractionType()
        
        if success:
            self.updateProgressBar(100)
            self.updateProgressLabel(self.get_text("extraction_completed", "Extraction completed"))
            
            # 显示详细统计信息
            self._showDetailedStats(result, extraction_type)
            
            # 处理自动打开输出目录
            self._handleAutoOpenOutputDir(result, extraction_type)
            
            # 使用安全的tooltip管理器更新完成状态
            completion_text = self.get_text("extraction_completed", "Extraction completed")
            self.tooltip_manager.update_completion_tooltip(completion_text, 3000)
            
            # 显示成功信息
            InfoBar.success(
                title=self.get_text("success", "Success"),
                content=self.get_text("extraction_success", "Extraction completed successfully"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            error_msg = result.get("error", self.get_text("unknown_error", "Unknown error"))
            self.updateProgressLabel(f"{self.get_text('extraction_failed', 'Extraction failed')}: {error_msg}")
            
            # 显示错误日志
            self.extractLogHandler.error(self.get_text("error_occurred", f"{self.get_text('extraction_failed', 'Extraction failed')}: {error_msg}"))
            
            # 使用安全的tooltip管理器更新错误状态
            error_text = self.get_text("extraction_failed", "Extraction failed")
            self.tooltip_manager.update_completion_tooltip(error_text, 5000)
            
            # 显示错误信息
            InfoBar.error(
                title=self.get_text("error", "Error"),
                content=error_msg,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

        # 清理工作线程
        self.extraction_worker = None
    
    def _handleAutoOpenOutputDir(self, result, extraction_type):
        """处理自动打开输出目录功能"""
        # 检查是否启用了自动打开输出目录设置
        if not (self.config_manager and self.config_manager.get("auto_open_output_dir", True)):
            return
            
        # 获取输出目录
        final_dir = result.get("output_dir", "")
        if not final_dir or not os.path.exists(final_dir):
            return
            
        # 根据提取类型确定要打开的子目录
        target_dir = final_dir
        subfolder_name = ""
        
        if extraction_type == "audio":
            audio_dir = os.path.join(final_dir, "Audio")
            if os.path.exists(audio_dir):
                target_dir = audio_dir
                subfolder_name = self.get_text("audio_folder", "Audio folder")
            else:
                subfolder_name = self.get_text("ogg_category", "Audio files")
                
        elif extraction_type == "font":
            fonts_dir = os.path.join(final_dir, "Fonts")
            if os.path.exists(fonts_dir):
                target_dir = fonts_dir
                subfolder_name = self.get_text("fonts_folder", "Fonts folder")
            else:
                subfolder_name = self.get_text("fonts_category", "Font files")
                
        elif extraction_type == "translation":
            translations_dir = os.path.join(final_dir, "Translations")
            if os.path.exists(translations_dir):
                target_dir = translations_dir
                subfolder_name = self.get_text("translations_folder", "Translations folder")
            else:
                subfolder_name = self.get_text("translations_category", "Translation files")
        
        # 尝试打开目录
        open_success = open_directory(target_dir)
        if open_success:
            if subfolder_name:
                self.extractLogHandler.info(self.get_text("opening_output_dir", "Opening output directory: {}").format(subfolder_name))
            else:
                self.extractLogHandler.info(self.get_text("opening_output_dir", "Opening output directory: {}").format(target_dir))
        else:
            self.extractLogHandler.info(self.get_text("manual_navigate", "Please manually navigate to: {}").format(target_dir))

    def _showDetailedStats(self, result, extraction_type):
        """显示详细的统计信息"""
        stats = result.get('stats', {})
        
        if extraction_type == "font":
            # 字体提取的统计信息
            if stats:
                self.extractLogHandler.success(self.get_text("font_extraction_success", "Font extraction completed successfully!"))
                
                # 显示字体特定的统计信息
                if 'fontlist_found' in stats:
                    fontlist_count = stats.get('fontlist_found', 0)
                    self.extractLogHandler.info(self.get_text("font_lists_found", "Font lists found: {}").format(fontlist_count))
                if 'fonts_downloaded' in stats:
                    fonts_count = stats.get('fonts_downloaded', 0)
                    self.extractLogHandler.info(self.get_text("fonts_downloaded", "Fonts downloaded: {}").format(fonts_count))
                if 'total_caches_scanned' in stats:
                    caches_count = stats.get('total_caches_scanned', 0)
                    self.extractLogHandler.info(self.get_text("caches_scanned", "Caches scanned: {}").format(caches_count))
                if 'processing_errors' in stats:
                    error_count = stats.get('processing_errors', 0)
                    self.extractLogHandler.info(self.get_text("processing_errors", "Processing errors: {}").format(error_count))
                if 'download_failed' in stats:
                    failed_count = stats.get('download_failed', 0)
                    self.extractLogHandler.info(self.get_text("download_failed", "Download failed: {}").format(failed_count))
                
                # 显示通用统计信息
                if 'duration' in result:
                    duration = result.get('duration', 0)
                    self.extractLogHandler.info(self.get_text("time_spent", "Time spent: {:.2f} seconds").format(duration))
                if 'output_dir' in result:
                    output_path = result.get('output_dir', '')
                    self.extractLogHandler.info(self.get_text("font_output_dir", "Font output directory: {}").format(output_path))
                
                # 计算处理速度
                duration = result.get('duration', 0)
                fontlist_found = stats.get('fontlist_found', 0)
                if duration > 0 and fontlist_found > 0:
                    speed = fontlist_found / duration
                    self.extractLogHandler.info(self.get_text("font_processing_speed", "Processing speed: {:.2f} font lists/second").format(speed))
            else:
                # 没有统计信息的情况
                self.extractLogHandler.success(self.get_text("extraction_completed", "Extraction completed"))
                if 'output_dir' in result:
                    output_path = result.get('output_dir', '')
                    self.extractLogHandler.info(self.get_text("output_dir", "Output directory: {}").format(output_path))
                    
        elif extraction_type == "audio":
            # 音频提取的统计信息 (保持与main.py一致)
            if "processed" in result and result["processed"] > 0:
                self.extractLogHandler.success(self.get_text("extraction_complete", "Extraction completed successfully!"))
                processed_count = result['processed']
                self.extractLogHandler.info(self.get_text("processed", "Processed: {} files").format(processed_count))
                duplicates_count = result.get('duplicates', 0)
                self.extractLogHandler.info(self.get_text("skipped_duplicates", "Skipped duplicates: {} files").format(duplicates_count))
                already_processed_count = result.get('already_processed', 0)
                self.extractLogHandler.info(self.get_text("skipped_already_processed", "Skipped already processed: {} files").format(already_processed_count))
                errors_count = result.get('errors', 0)
                self.extractLogHandler.info(self.get_text("errors", "Errors: {} files").format(errors_count))
                duration = result.get('duration', 0)
                self.extractLogHandler.info(self.get_text("time_spent", "Time spent: {:.2f} seconds").format(duration))
                speed = result.get('files_per_second', 0)
                self.extractLogHandler.info(self.get_text("files_per_sec", "Processing speed: {:.2f} files/second").format(speed))
                output_path = result.get('output_dir', '')
                self.extractLogHandler.info(self.get_text("output_dir", "Output directory: {}").format(output_path))
            else:
                self.extractLogHandler.warning(self.get_text("no_files_processed", "No files were processed"))
                
        elif extraction_type == "translation":
            # 翻译文件提取的统计信息
            stats = result.get('stats', {})
            translation_saved = stats.get('translation_saved', 0)
            
            if translation_saved > 0:
                self.extractLogHandler.success(self.get_text("extraction_complete", "Extraction completed successfully!"))
                translation_found = stats.get('translation_found', 0)
                self.extractLogHandler.info(f"{self.get_text('translation_found', 'Translation files found')}: {translation_found}")
                self.extractLogHandler.info(f"{self.get_text('translation_saved', 'Translation files saved')}: {translation_saved}")
                already_processed = stats.get('already_processed', 0)
                self.extractLogHandler.info(self.get_text("skipped_already_processed", "Skipped already processed: {} files").format(already_processed))
                duplicate_skipped = stats.get('duplicate_skipped', 0)
                self.extractLogHandler.info(self.get_text("skipped_duplicates", "Skipped duplicates: {} files").format(duplicate_skipped))
                processing_errors = stats.get('processing_errors', 0)
                self.extractLogHandler.info(self.get_text("errors", "Errors: {} files").format(processing_errors))
                duration = result.get('duration', 0)
                self.extractLogHandler.info(self.get_text("time_spent", "Time spent: {:.2f} seconds").format(duration))
                output_path = result.get('output_dir', '')
                self.extractLogHandler.info(self.get_text("output_dir", "Output directory: {}").format(output_path))
            else:
                self.extractLogHandler.warning(self.get_text("no_files_processed", "No files were processed"))
        else:
            # 其他提取类型的通用统计信息
            self.extractLogHandler.success(self.get_text("extraction_completed", "Extraction completed"))
            if 'duration' in result:
                duration = result.get('duration', 0)
                self.extractLogHandler.info(self.get_text("time_spent", "Time spent: {:.2f} seconds").format(duration))
            if 'output_dir' in result:
                output_path = result.get('output_dir', '')
                self.extractLogHandler.info(self.get_text("output_dir", "Output directory: {}").format(output_path))

    def handleExtractionLog(self, message, log_type):
        """处理提取日志"""
        # 处理翻译键和格式化消息
        translated_message = self._translate_log_message(message)
        
        # 添加到日志输出区域
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        formatted_message = f"[{timestamp}] {translated_message}"
        self.logTextEdit.append(formatted_message)
        
        # 发送到日志系统
        if log_type == "error":
            self.extractLogHandler.error(translated_message)
        elif log_type == "warning":
            self.extractLogHandler.warning(translated_message)
        elif log_type == "success":
            self.extractLogHandler.info(translated_message)
        else:
            self.extractLogHandler.info(translated_message)
    
    def _translate_log_message(self, message):
        """翻译日志消息"""
        # 检查是否包含参数分隔符
        if f"|{chr(31)}|" in message:
            # 解析消息格式: "message_key|{chr(31)}|arg1{chr(31)}arg2{chr(31)}..."
            parts = message.split(f"|{chr(31)}|", 1)
            message_key = parts[0]
            args = parts[1].split(chr(31)) if len(parts) > 1 else []
        else:
            # 没有参数的消息
            message_key = message
            args = []
        
        # 如果有翻译系统，进行翻译
        if hasattr(self, 'lang') and self.lang:
            # 获取翻译文本
            translated_text = self.lang.get(message_key, message_key)
            
            # 如果有参数，进行格式化
            if args:
                try:
                    # 尝试智能转换参数类型
                    converted_args = []
                    for arg in args:
                        try:
                            # 尝试转换为数字
                            if '.' in arg:
                                converted_args.append(float(arg))
                            else:
                                converted_args.append(int(arg))
                        except ValueError:
                            # 如果转换失败，保持为字符串
                            converted_args.append(arg)
                    
                    return translated_text.format(*converted_args)
                except Exception:
                    # 如果格式化失败，返回翻译文本 + 原始参数
                    return translated_text + " " + " ".join(args)
            else:
                return translated_text
        
        # 如果没有翻译系统，检查是否是翻译键格式，如果是则使用默认翻译
        if hasattr(self, '_get_default_translation'):
            translated_text = self._get_default_translation(message_key)
            if args:
                try:
                    # 尝试智能转换参数类型
                    converted_args = []
                    for arg in args:
                        try:
                            # 尝试转换为数字
                            if '.' in arg:
                                converted_args.append(float(arg))
                            else:
                                converted_args.append(int(arg))
                        except ValueError:
                            # 如果转换失败，保持为字符串
                            converted_args.append(arg)
                    
                    return translated_text.format(*converted_args)
                except Exception:
                    return translated_text + " " + " ".join(args)
            return translated_text
        
        # 最后返回原消息
        return message
    
    def _get_default_translation(self, message_key):
        """获取默认翻译（中文）"""
        default_translations = {
            'initializing_font_extractor': '正在初始化字体提取器...',
            'starting_font_extraction': '开始字体提取...',
            'scanning_cache': '正在扫描缓存...',
            'cache_scan_complete': '缓存扫描完成，发现 {} 个项目',
            'no_cache_items_found': '未发现缓存项目',
            'cache_path_not_found': 'Roblox缓存路径不存在或无法访问',
            'font_extraction_complete': '字体提取完成! 发现{}个字体列表，成功下载{}个字体文件 (耗时{:.1f}秒)',
            'font_extraction_failed': '字体提取失败: {}',
            'processing_font_list': '处理字体列表: {}，包含 {} 个字体',
            'font_list_complete': '字体列表处理完成: {}，成功下载 {}/{} 个字体',
            'downloading_font': '正在下载字体: {}...',
            'font_download_success': '成功下载字体: {}'
        }
        return default_translations.get(message_key, message_key)

    def showExtractButton(self, show):
        """显示/隐藏提取按钮"""
        if show:
            self.extractButton.show()
        else:
            self.extractButton.hide()

    def showCancelButton(self, show):
        """显示/隐藏取消按钮"""
        if show:
            self.cancelButton.show()
        else:
            self.cancelButton.hide()

    def updateProgressBar(self, value):
        """更新进度条"""
        self.progressBar.setValue(value)

    def updateProgressLabel(self, text):
        """更新进度标签"""
        self.progressLabel.setText(text)

    def setInterfaceStyles(self):
        """设置提取界面样式"""
        # 调用父类的通用样式设置
        super().setInterfaceStyles()
        
        # 获取主题相关样式
        colors = self.get_theme_colors()
        text_styles = self.get_text_styles()
        
        # 应用特定的提取界面样式
        specific_styles = f"""
            QWidget {{
                background-color: {colors['background']};
            }}
            CardWidget {{
                border-radius: 10px;
                background-color: {colors['background']};
            }}
            TextEdit {{
                border: 1px solid {colors['border']};
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.1);
                {text_styles['body']}
            }}
        """
        
        # 合并样式
        combined_styles = self.get_common_interface_styles() + specific_styles
        self.setStyleSheet(combined_styles)
        
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        try:
            # 清理tooltip管理器
            if hasattr(self, 'tooltip_manager'):
                self.tooltip_manager.cleanup()
                
            # 停止任何正在运行的提取工作
            if hasattr(self, 'extraction_worker') and self.extraction_worker:
                if self.extraction_worker.isRunning():
                    self.extraction_worker.cancel()
                    self.extraction_worker.wait(1000)  # 等待1秒
                    
            # 停止定时器
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"关闭BaseExtractInterface时发生错误: {e}")
        finally:
            super().closeEvent(event)
    
    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            if hasattr(self, 'tooltip_manager'):
                self.tooltip_manager.cleanup()
        except Exception:
            pass 