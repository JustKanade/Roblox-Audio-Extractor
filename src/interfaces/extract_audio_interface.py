#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QButtonGroup,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer

from qfluentwidgets import (
    CardWidget, BodyLabel, TitleLabel, StrongBodyLabel,
    ScrollArea, PushButton, PrimaryPushButton, 
    FluentIcon, CaptionLabel, ProgressBar, RadioButton,
    TextEdit, IconWidget, SpinBox, LineEdit, InfoBar,
    MessageBox, StateToolTip, InfoBarPosition
)

import os
import multiprocessing
import time
from functools import partial

from src.utils.log_utils import LogHandler
from src.utils.file_utils import open_directory
from src.extractors.audio_extractor import ClassificationMethod, is_ffmpeg_available
from src.workers.extraction_worker import ExtractionWorker


class ExtractAudioInterface(QWidget):
    """音频提取界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None, default_dir=None, download_history=None):
        super().__init__(parent)
        self.setObjectName("extractInterface")
        self.config_manager = config_manager
        self.lang = lang
        self.default_dir = default_dir
        self.download_history = download_history
        self._parent_window = parent
        
        # 初始化工作线程
        self.extraction_worker = None
        
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
        """初始化界面"""
        # 创建滚动区域
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        
        # 添加页面标题
        page_title = TitleLabel(self.get_text("extract_audio"))
        page_title.setObjectName("extractAudioTitle")
        content_layout.addWidget(page_title)

        # 目录选择卡片
        dir_card = CardWidget()
        dir_card_layout = QVBoxLayout(dir_card)
        dir_card_layout.setContentsMargins(20, 15, 20, 15)
        dir_card_layout.setSpacing(15)

        dir_title = StrongBodyLabel(self.get_text("directory"))
        dir_card_layout.addWidget(dir_title)

        # 目录输入行
        dir_input_layout = QHBoxLayout()
        dir_input_layout.setSpacing(10)

        self.dirInput = LineEdit()
        self.dirInput.setText(self.default_dir)
        self.dirInput.setPlaceholderText(self.get_text("input_dir"))
        self.dirInput.setClearButtonEnabled(True)

        browse_btn = PushButton(FluentIcon.FOLDER_ADD, self.get_text("browse"))
        browse_btn.setFixedSize(100, 33)
        browse_btn.clicked.connect(self.browseDirectory)

        dir_input_layout.addWidget(self.dirInput, 1)
        dir_input_layout.addWidget(browse_btn)

        dir_card_layout.addLayout(dir_input_layout)

        # 添加目录提示
        dir_hint = CaptionLabel(f"{self.get_text('default_dir')}: {self.default_dir}")
        dir_hint.setWordWrap(True)
        dir_card_layout.addWidget(dir_hint)

        content_layout.addWidget(dir_card)

        # 分类方法卡片
        classification_card = CardWidget()
        class_card_layout = QVBoxLayout(classification_card)
        class_card_layout.setContentsMargins(20, 15, 20, 15)
        class_card_layout.setSpacing(15)

        class_title = StrongBodyLabel(self.get_text("classification_method"))
        class_card_layout.addWidget(class_title)

        # 分类方法选择
        self.classification_group = QButtonGroup()

        duration_row = QHBoxLayout()
        self.durationRadio = RadioButton(self.get_text("classify_by_duration"))
        self.durationRadio.setChecked(True)
        duration_icon = IconWidget(FluentIcon.CALENDAR)
        duration_icon.setFixedSize(16, 16)
        duration_row.addWidget(duration_icon)
        duration_row.addWidget(self.durationRadio)
        duration_row.addStretch()

        size_row = QHBoxLayout()
        self.sizeRadio = RadioButton(self.get_text("classify_by_size"))
        size_icon = IconWidget(FluentIcon.DOCUMENT)
        size_icon.setFixedSize(16, 16)
        size_row.addWidget(size_icon)
        size_row.addWidget(self.sizeRadio)
        size_row.addStretch()

        self.classification_group.addButton(self.durationRadio)
        self.classification_group.addButton(self.sizeRadio)

        class_card_layout.addLayout(duration_row)
        class_card_layout.addLayout(size_row)

        # FFmpeg警告
        if not is_ffmpeg_available():
            ffmpeg_warning = InfoBar.warning(
                title="FFmpeg",
                content=self.get_text("ffmpeg_not_found_warning"),
                orient=Qt.Horizontal,
                isClosable=False,
                duration=-1,
                parent=None
            )
            class_card_layout.addWidget(ffmpeg_warning)

        # 分类信息标签
        self.classInfoLabel = CaptionLabel(self.get_text("info_duration_categories"))
        self.classInfoLabel.setWordWrap(True)
        class_card_layout.addWidget(self.classInfoLabel)

        # 连接分类方法选择事件
        self.durationRadio.toggled.connect(self.updateClassificationInfo)

        content_layout.addWidget(classification_card)

        # 处理选项卡片
        options_card = CardWidget()
        options_card_layout = QVBoxLayout(options_card)
        options_card_layout.setContentsMargins(20, 15, 20, 15)
        options_card_layout.setSpacing(15)

        options_title = StrongBodyLabel(self.get_text("processing_info"))
        options_card_layout.addWidget(options_title)

        # 线程数设置
        threads_row = QHBoxLayout()
        threads_icon = IconWidget(FluentIcon.SPEED_HIGH)
        threads_icon.setFixedSize(16, 16)
        threads_label = BodyLabel(self.get_text("threads_prompt"))

        self.threadsSpinBox = SpinBox()
        self.threadsSpinBox.setRange(1, 128)
        self.threadsSpinBox.setValue(min(32, multiprocessing.cpu_count() * 2))
        self.threadsSpinBox.setFixedWidth(120)
        self.threadsSpinBox.setFixedHeight(32)

        threads_row.addWidget(threads_icon)
        threads_row.addWidget(threads_label)
        threads_row.addStretch()
        threads_row.addWidget(self.threadsSpinBox)

        options_card_layout.addLayout(threads_row)

        # 添加处理提示
        info_list = [
            self.get_text("info_skip_downloaded")
        ]

        for info in info_list:
            info_label = CaptionLabel(f"• {info}")
            info_label.setWordWrap(True)
            options_card_layout.addWidget(info_label)

        content_layout.addWidget(options_card)

        # 操作控制卡片
        control_card = CardWidget()
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(25, 20, 25, 20)
        control_layout.setSpacing(15)

        # 进度显示
        progress_layout = QVBoxLayout()

        # 进度条
        self.progressBar = ProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(True)

        # 进度信息
        self.progressLabel = CaptionLabel(self.get_text("ready"))
        self.progressLabel.setAlignment(Qt.AlignCenter)

        progress_layout.addWidget(self.progressBar)
        progress_layout.addWidget(self.progressLabel)

        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.extractButton = PrimaryPushButton(FluentIcon.DOWNLOAD, self.get_text("start_extraction"))
        self.extractButton.setFixedHeight(40)
        self.extractButton.clicked.connect(self.startExtraction)

        self.cancelButton = PushButton(FluentIcon.CLOSE, self.get_text("cancel"))
        self.cancelButton.setFixedHeight(40)
        self.cancelButton.clicked.connect(self.cancelExtraction)
        self.cancelButton.hide()  # 初始隐藏

        button_layout.addWidget(self.extractButton)
        button_layout.addWidget(self.cancelButton)
        button_layout.addStretch()

        control_layout.addLayout(progress_layout)
        control_layout.addLayout(button_layout)
        content_layout.addWidget(control_card)

        # 日志区域
        log_card = CardWidget()
        log_card.setFixedHeight(300)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(self.get_text("recent_activity"))
        log_layout.addWidget(log_title)

        self.extractLogText = TextEdit()
        self.extractLogText.setReadOnly(True)
        self.extractLogText.setFixedHeight(220)
        log_layout.addWidget(self.extractLogText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.extractLogHandler = LogHandler(self.extractLogText)
        
    def setResponsiveContentWidget(self, scroll_area):
        """为滚动区域内的内容容器应用响应式布局设置，防止卡片间距异常"""
        if not scroll_area:
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
                    
    def browseDirectory(self):
        """浏览目录对话框"""
        if self._parent_window:
            from PyQt5.QtWidgets import QFileDialog
            directory = QFileDialog.getExistingDirectory(self, self.get_text("directory"), self.dirInput.text())
            if directory:
                self.dirInput.setText(directory)
                if self.config_manager:
                    self.config_manager.set("last_directory", directory)
                    
    def updateClassificationInfo(self):
        """更新分类信息标签"""
        if self.durationRadio.isChecked():
            self.classInfoLabel.setText(self.get_text("info_duration_categories"))
        else:
            self.classInfoLabel.setText(self.get_text("info_size_categories"))
            
    def startExtraction(self):
        """开始提取音频"""
        # 获取全局输入路径（如果已设置）
        global_input_path = self.config_manager.get("global_input_path", "") if self.config_manager else ""
        
        # 获取用户选择的目录
        selected_dir = global_input_path if global_input_path else self.dirInput.text()
        
        # 如果使用了全局输入路径，更新输入框的显示
        if global_input_path and self.dirInput.text() != global_input_path:
            self.dirInput.setText(global_input_path)
            self.extractLogHandler.info(self.get_text("using_global_input_path", "使用全局输入路径") + f": {global_input_path}")

        # 检查目录是否存在
        if not os.path.exists(selected_dir):
            result = MessageBox(
                self.get_text("create_dir_prompt"),
                self.get_text("dir_not_exist", selected_dir),
                self
            )

            if result.exec():
                try:
                    os.makedirs(selected_dir, exist_ok=True)
                    self.extractLogHandler.success(self.get_text("dir_created", selected_dir))
                except Exception as e:
                    self.extractLogHandler.error(self.get_text("dir_create_failed", str(e)))
                    return
            else:
                self.extractLogHandler.warning(self.get_text("operation_cancelled"))
                return

        # 获取线程数
        try:
            num_threads = self.threadsSpinBox.value()
            if num_threads < 1:
                self.extractLogHandler.warning(self.get_text("threads_min_error"))
                num_threads = min(32, multiprocessing.cpu_count() * 2)
                self.threadsSpinBox.setValue(num_threads)

            if num_threads > 64:
                result = MessageBox(
                    self.get_text("confirm_high_threads"),
                    self.get_text("threads_high_warning"),
                    self
                )

                if not result.exec():
                    num_threads = min(32, multiprocessing.cpu_count() * 2)
                    self.threadsSpinBox.setValue(num_threads)
                    self.extractLogHandler.info(self.get_text("threads_adjusted", num_threads))
        except ValueError:
            self.extractLogHandler.warning(self.get_text("input_invalid"))
            num_threads = min(32, multiprocessing.cpu_count() * 2)
            self.threadsSpinBox.setValue(num_threads)

        # 获取分类方法
        classification_method = ClassificationMethod.DURATION if self.durationRadio.isChecked() else ClassificationMethod.SIZE

        # 如果选择时长分类但没有ffmpeg，显示警告
        if classification_method == ClassificationMethod.DURATION and not is_ffmpeg_available():
            result = MessageBox(
                self.get_text("confirm"),
                self.get_text("ffmpeg_not_installed"),
                self
            )

            if not result.exec():
                self.extractLogHandler.warning(self.get_text("operation_cancelled"))
                return

        # 获取自定义输出目录
        custom_output_dir = self.config_manager.get("custom_output_dir", "") if self.config_manager else ""
        
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
        self.progressLabel.setText(self.get_text("processing"))

        # 创建任务状态提示
        self.extractionStateTooltip = StateToolTip(
            self.get_text("task_running"),
            self.get_text("processing"),
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
                self.extractionStateTooltip.setContent(self.get_text("task_canceled"))
                self.extractionStateTooltip.setState(True)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.extractionStateTooltip.close)

            # 恢复UI
            self.cancelButton.hide()
            self.extractButton.show()

            # 重置进度条
            self.progressBar.setValue(0)
            self.progressLabel.setText(self.get_text("ready"))

            self.handleExtractionLog(self.get_text("canceled_by_user"), "warning")

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
        self.progressLabel.setText(self.get_text("ready"))

        if result.get("success", False):
            # 显示提取结果
            if "processed" in result and result["processed"] > 0:
                self.extractLogHandler.success(self.get_text("extraction_complete"))
                self.extractLogHandler.info(self.get_text("processed", result['processed']))
                self.extractLogHandler.info(self.get_text("skipped_duplicates", result.get('duplicates', 0)))
                self.extractLogHandler.info(self.get_text("skipped_already_processed", result.get('already_processed', 0)))
                self.extractLogHandler.info(self.get_text("errors", result.get('errors', 0)))
                self.extractLogHandler.info(self.get_text("time_spent", result.get('duration', 0)))
                self.extractLogHandler.info(self.get_text("files_per_sec", result.get('files_per_second', 0)))
                self.extractLogHandler.info(self.get_text("output_dir", result.get('output_dir', '')))

                # 输出目录
                final_dir = result.get("output_dir", "")
                # 音频输出文件夹路径
                audio_dir = os.path.join(final_dir, "Audio")

                # 根据设置决定是否自动打开目录
                if final_dir and os.path.exists(final_dir) and self.config_manager and self.config_manager.get("auto_open_output_dir", True):
                    # 优先打开Audio文件夹，如果存在
                    if os.path.exists(audio_dir):
                        open_success = open_directory(audio_dir)
                        if open_success:
                            self.extractLogHandler.info(self.get_text("opening_output_dir", "音频总文件夹"))
                        else:
                            self.extractLogHandler.info(self.get_text("manual_navigate", audio_dir))
                    else:
                        # 如果Audio文件夹不存在，打开根输出目录
                        open_success = open_directory(final_dir)
                        if open_success:
                            self.extractLogHandler.info(self.get_text("opening_output_dir", self.get_text("ogg_category")))
                        else:
                            self.extractLogHandler.info(self.get_text("manual_navigate", final_dir))

                # 更新状态提示
                if hasattr(self, 'extractionStateTooltip'):
                    self.extractionStateTooltip.setContent(self.get_text("extraction_complete"))
                    self.extractionStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.extractionStateTooltip.close)

                # 显示完成消息
                InfoBar.success(
                    title=self.get_text("task_completed"),
                    content=self.get_text("extraction_complete"),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )

                # 刷新历史界面以显示最新的文件数量
                if self._parent_window and hasattr(self._parent_window, 'historyInterface') and \
                   hasattr(self._parent_window.historyInterface, 'refreshHistoryInterface'):
                    self._parent_window.historyInterface.refreshHistoryInterface()
            else:
                self.extractLogHandler.warning(self.get_text("no_files_processed"))

                # 更新状态提示
                if hasattr(self, 'extractionStateTooltip'):
                    self.extractionStateTooltip.setContent(self.get_text("no_files_processed"))
                    self.extractionStateTooltip.setState(True)
                    # 2秒后关闭状态提示
                    QTimer.singleShot(2000, self.extractionStateTooltip.close)
        else:
            # 显示错误
            self.extractLogHandler.error(self.get_text("error_occurred", result.get('error', '')))

            # 更新状态提示
            if hasattr(self, 'extractionStateTooltip'):
                self.extractionStateTooltip.setContent(self.get_text("task_failed"))
                self.extractionStateTooltip.setState(False)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.extractionStateTooltip.close)

            # 显示错误消息
            InfoBar.error(
                title=self.get_text("task_failed"),
                content=result.get('error', self.get_text('error_occurred', '')),
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