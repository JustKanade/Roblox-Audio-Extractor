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
    MessageBox, StateToolTip, InfoBarPosition, ComboBox, CheckBox
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
        
        # 设置大小策略，防止界面拉伸
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
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
        # 应用样式
        self.setExtractStyles()
        
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
        
        # 创建设置卡片
        settings_card = CardWidget()
        settings_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(15)
        
        # 添加标题到设置卡片内部
        settings_label = TitleLabel(self.get_text("extract_audio_title"), self)
        settings_label.setObjectName("extractAudioTitle")
        settings_layout.addWidget(settings_label)

        # 添加路径选择器
        path_layout = QHBoxLayout()
        path_layout.setSpacing(10)

        path_label = BodyLabel(self.get_text("input_dir"))
        path_layout.addWidget(path_label)

        self.path_edit = LineEdit()
        self.path_edit.setText(self.default_dir)
        self.path_edit.setClearButtonEnabled(True)
        self.path_edit.setPlaceholderText(self.get_text("input_dir_placeholder"))
        path_layout.addWidget(self.path_edit, 1)

        self.browse_button = PushButton(self.get_text("browse"))
        self.browse_button.setIcon(FluentIcon.FOLDER_ADD)
        self.browse_button.clicked.connect(self.browseDirectory)
        path_layout.addWidget(self.browse_button)

        settings_layout.addLayout(path_layout)

        # 添加历史记录大小信息
        history_layout = QHBoxLayout()
        history_layout.setSpacing(10)
        
        history_icon = IconWidget(FluentIcon.HISTORY, self)
        history_icon.setFixedSize(16, 16)
        history_layout.addWidget(history_icon)
        
        # 显示历史记录大小
        history_size = 0
        content_size = 0
        if self.download_history:
            history_size = self.download_history.get_history_size()
            if hasattr(self.download_history, 'content_hashes'):
                content_size = len(self.download_history.content_hashes)
                
        self.historyCountLabel = CaptionLabel(
            f"{self.get_text('history_size')}: {history_size} {self.get_text('files')}, "
            f"{content_size} {self.get_text('unique_contents')}"
        )
        history_layout.addWidget(self.historyCountLabel)
        
        # 添加清除历史按钮
        self.clearHistoryBtn = PushButton(self.get_text("clear_history"))
        self.clearHistoryBtn.setIcon(FluentIcon.DELETE)
        self.clearHistoryBtn.clicked.connect(self.clearHistory)
        history_layout.addWidget(self.clearHistoryBtn)
        
        settings_layout.addLayout(history_layout)

        # 添加分类方法选择
        classification_layout = QVBoxLayout()  # 改为垂直布局
        classification_layout.setSpacing(8)
        
        selection_layout = QHBoxLayout()  # 创建水平子布局用于选择器
        selection_layout.setSpacing(10)

        classification_label = BodyLabel(self.get_text("classification_method"))
        selection_layout.addWidget(classification_label)

        self.classification_combo = ComboBox()
        self.classification_combo.addItems([
            self.get_text("by_duration"),
            self.get_text("by_size")
        ])
        # 设置默认选项
        saved_method = "duration"
        if self.config_manager:
            saved_method = self.config_manager.get("classification_method", "duration")
        if saved_method == "size":
            self.classification_combo.setCurrentIndex(1)
        else:
            self.classification_combo.setCurrentIndex(0)
        self.classification_combo.currentIndexChanged.connect(self.updateClassificationInfo)
        self.classification_combo.setFixedWidth(120)  # 固定宽度，确保不会占用过多空间
        selection_layout.addWidget(self.classification_combo)
        selection_layout.addStretch(1)  # 添加弹性空间
        
        classification_layout.addLayout(selection_layout)

        # 添加分类信息标签
        self.classification_info = BodyLabel("")
        self.classification_info.setWordWrap(True)  # 允许文本换行
        classification_layout.addWidget(self.classification_info)

        settings_layout.addLayout(classification_layout)

        # 添加线程数选择
        threads_layout = QHBoxLayout()
        threads_layout.setSpacing(10)

        threads_label = BodyLabel(self.get_text("threads"))
        threads_layout.addWidget(threads_label)

        self.threads_spin = SpinBox()
        self.threads_spin.setRange(1, 128)  # 设置范围从1到128
        # 设置默认值为CPU核心数的2倍，但不超过32
        default_threads = min(32, multiprocessing.cpu_count() * 2)
        saved_threads = default_threads
        if self.config_manager:
            saved_threads = self.config_manager.get("threads", default_threads)
        self.threads_spin.setValue(saved_threads)
        threads_layout.addWidget(self.threads_spin)

        threads_info = BodyLabel(self.get_text("threads_info"))
        threads_layout.addWidget(threads_info, 1)

        settings_layout.addLayout(threads_layout)
        
        # 添加数据库扫描选项
        db_scan_layout = QHBoxLayout()
        db_scan_layout.setSpacing(10)
        
        self.db_scan_checkbox = CheckBox(self.get_text("scan_database"))
        self.db_scan_checkbox.setChecked(True)  # 默认启用
        db_scan_layout.addWidget(self.db_scan_checkbox)
        
        db_scan_info = BodyLabel(self.get_text("scan_database_info"))
        db_scan_layout.addWidget(db_scan_info, 1)
        
        settings_layout.addLayout(db_scan_layout)

        content_layout.addWidget(settings_card)

        # 操作控制卡片
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
        self.progressLabel = CaptionLabel(self.get_text("ready"))
        self.progressLabel.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progressBar)
        progress_layout.addWidget(self.progressLabel)

        control_layout.addLayout(progress_layout)

        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.extractButton = PrimaryPushButton(FluentIcon.DOWNLOAD, self.get_text("extract"))
        self.extractButton.setFixedHeight(40)
        self.extractButton.clicked.connect(self.startExtraction)
        button_layout.addWidget(self.extractButton)

        self.cancelButton = PushButton(FluentIcon.CANCEL, self.get_text("cancel"))
        self.cancelButton.setFixedHeight(40)
        self.cancelButton.clicked.connect(self.cancelExtraction)
        self.cancelButton.hide()  # 初始隐藏取消按钮
        button_layout.addWidget(self.cancelButton)

        button_layout.addStretch()

        control_layout.addLayout(button_layout)

        # 添加日志区域
        log_card = CardWidget()
        log_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(self.get_text("recent_activity"))
        log_layout.addWidget(log_title)

        self.logTextEdit = TextEdit()
        self.logTextEdit.setReadOnly(True)
        self.logTextEdit.setFixedHeight(220)
        self.logTextEdit.setStyleSheet("font-family: Consolas, Courier, monospace;")
        log_layout.addWidget(self.logTextEdit)

        content_layout.addWidget(log_card)
        
        # 确保布局末尾有伸缩项，防止界面被拉伸
        content_layout.addStretch(1)
        
        # 设置滚动区域
        scroll.setWidget(content_widget)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 设置日志处理器
        self.extractLogHandler = LogHandler(self.logTextEdit)

        # 更新分类信息
        self.updateClassificationInfo()
        
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
            directory = QFileDialog.getExistingDirectory(self, self.get_text("directory"), self.path_edit.text())
            if directory:
                self.path_edit.setText(directory)
                if self.config_manager:
                    self.config_manager.set("last_directory", directory)
                    
    def updateClassificationInfo(self):
        """更新分类信息标签"""
        if self.classification_combo.currentIndex() == 0: # by duration
            self.classification_info.setText(self.get_text("info_duration_categories"))
        else: # by size
            self.classification_info.setText(self.get_text("info_size_categories"))
            
    def startExtraction(self):
        """开始提取音频"""
        # 获取输入路径
        input_dir = self.path_edit.text().strip()
        if not input_dir or not os.path.isdir(input_dir):
            InfoBar.error(
                title=self.get_text("error"),
                content=self.get_text("invalid_dir"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        # 保存配置
        if self.config_manager:
            # 保存分类方法
            method = "size" if self.classification_combo.currentIndex() == 1 else "duration"
            self.config_manager.set("classification_method", method)
            
            # 保存线程数
            threads = self.threads_spin.value()
            self.config_manager.set("threads", threads)
            
            # 保存输入路径
            self.config_manager.set("last_input_dir", input_dir)

        # 更新UI状态
        self.showExtractButton(False)
        self.showCancelButton(True)
        self.updateProgressBar(0)
        self.updateProgressLabel(self.get_text("preparing"))
        
        # 清空日志
        self.logTextEdit.clear()
        
        # 获取分类方法
        classification_method = ClassificationMethod.SIZE if self.classification_combo.currentIndex() == 1 else ClassificationMethod.DURATION
        
        # 获取线程数
        num_threads = self.threads_spin.value()
        
        # 获取数据库扫描选项
        scan_db = self.db_scan_checkbox.isChecked()
        
        # 创建提取工作线程
        self.extraction_worker = ExtractionWorker(
            input_dir, 
            num_threads, 
            self.download_history, 
            classification_method,
            None,  # 使用默认输出目录
            scan_db  # 传递数据库扫描选项
        )

        # 连接信号
        self.extraction_worker.progressUpdated.connect(self.updateExtractionProgress)
        self.extraction_worker.finished.connect(self.extractionFinished)
        self.extraction_worker.logMessage.connect(self.handleExtractionLog)
        
        # 创建定时器以定期更新UI
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(lambda: None)  # 仅触发Qt事件循环
        self.update_timer.start(100)  # 每100毫秒更新一次

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
            # 调用工作线程的取消方法
            self.extraction_worker.cancel()

            # 停止UI更新定时器
            if hasattr(self, 'update_timer') and self.update_timer.isActive():
                self.update_timer.stop()

            # 更新状态
            if hasattr(self, 'extractionStateTooltip'):
                self.extractionStateTooltip.setContent(self.get_text("task_canceled"))
                self.extractionStateTooltip.setState(True)
                # 2秒后关闭状态提示
                QTimer.singleShot(2000, self.extractionStateTooltip.close)

            # 恢复UI
            self.showCancelButton(False)
            self.showExtractButton(True)

            # 重置进度条
            self.updateProgressBar(0)
            self.updateProgressLabel(self.get_text("ready"))

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
        self.updateProgressBar(progress)
        self.updateProgressLabel(status_text)
        # 更新状态提示
        if hasattr(self, 'extractionStateTooltip'):
            self.extractionStateTooltip.setContent(status_text)
            
    def extractionFinished(self, result):
        """提取完成处理"""
        # 停止UI更新定时器
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
            
        # 恢复UI状态
        self.showCancelButton(False)
        self.showExtractButton(True)

        # 重置进度条为0而不是100
        self.updateProgressBar(0)
        self.updateProgressLabel(self.get_text("ready"))
        
        # 更新历史记录大小显示
        self.updateHistorySize()

        if result.get("success", False):
            # 显示提取结果
            if "processed" in result and result["processed"] > 0:
                self.handleExtractionLog(self.get_text("extraction_complete"), "success")
                self.handleExtractionLog(self.get_text("processed", result['processed']), "info")
                self.handleExtractionLog(self.get_text("skipped_duplicates", result.get('duplicates', 0)), "info")
                self.handleExtractionLog(self.get_text("skipped_already_processed", result.get('already_processed', 0)), "info")
                self.handleExtractionLog(self.get_text("errors", result.get('errors', 0)), "info")
                self.handleExtractionLog(self.get_text("time_spent", result.get('duration', 0)), "info")
                self.handleExtractionLog(self.get_text("files_per_sec", result.get('files_per_second', 0)), "info")
                self.handleExtractionLog(self.get_text("output_dir", result.get('output_dir', '')), "info")

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
                            self.extractLogHandler.info(self.get_text("opening_output_dir", self.get_text("audio_folder")))
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

    def setExtractStyles(self):
        """设置音频提取界面样式"""
        if not self.config_manager:
            return
            
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            self.setStyleSheet("""
                #extractAudioTitle {
                    color: rgb(0, 0, 0);
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                #extractAudioTitle {
                    color: rgb(255, 255, 255);
                    font-size: 24px;
                    font-weight: bold;
                }
            """) 
            
    def updateProgressBar(self, value):
        """更新进度条"""
        if hasattr(self, 'progressBar'):
            self.progressBar.setValue(value)
            
    def updateProgressLabel(self, text):
        """更新进度标签"""
        if hasattr(self, 'progressLabel'):
            self.progressLabel.setText(text)
            
    def showCancelButton(self, show=True):
        """显示/隐藏取消按钮"""
        if hasattr(self, 'cancelButton'):
            if show:
                self.cancelButton.show()
            else:
                self.cancelButton.hide()
                
    def showExtractButton(self, show=True):
        """显示/隐藏提取按钮"""
        if hasattr(self, 'extractButton'):
            if show:
                self.extractButton.show()
            else:
                self.extractButton.hide() 

    def updateThreadsValue(self):
        """更新线程数值，与设置界面同步"""
        if self.config_manager:
            default_threads = min(32, multiprocessing.cpu_count() * 2)
            saved_threads = self.config_manager.get("threads", default_threads)
            if hasattr(self, 'threads_spin'):
                self.threads_spin.setValue(saved_threads) 

    def clearHistory(self):
        """清除提取历史记录"""
        if not self.download_history:
            self.handleExtractionLog(self.get_text("history_not_available"), "error")
            return
            
        # 确认对话框
        result = MessageBox(
            self.get_text("confirm"),
            self.get_text("clear_history_confirm"),
            self._parent_window or self
        )

        if result.exec():
            try:
                # 清除历史记录
                self.download_history.clear_history()
                
                # 更新历史记录大小显示
                self.updateHistorySize()
                
                # 显示成功消息
                self.handleExtractionLog(self.get_text("history_cleared"), "success")
                
                InfoBar.success(
                    self.get_text("success"),
                    self.get_text("history_cleared"),
                    duration=3000,
                    position=InfoBarPosition.TOP,
                    parent=self._parent_window or self
                )
            except Exception as e:
                # 显示错误消息
                self.handleExtractionLog(f"{self.get_text('clear_history_failed')}: {str(e)}", "error")
                
                InfoBar.error(
                    self.get_text("error"),
                    f"{self.get_text('clear_history_failed')}: {str(e)}",
                    duration=3000,
                    position=InfoBarPosition.TOP,
                    parent=self._parent_window or self
                )
    
    def updateHistorySize(self):
        """更新历史记录大小显示"""
        if not self.download_history:
            return
            
        history_size = self.download_history.get_history_size()
        content_size = 0
        if hasattr(self.download_history, 'content_hashes'):
            content_size = len(self.download_history.content_hashes)
            
        self.historyCountLabel.setText(
            f"{self.get_text('history_size')}: {history_size} {self.get_text('files')}, "
            f"{content_size} {self.get_text('unique_contents')}"
        ) 