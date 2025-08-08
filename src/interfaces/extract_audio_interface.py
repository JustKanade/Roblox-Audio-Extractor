#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QButtonGroup,
    QSizePolicy
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
        
        # 获取路径管理器
        self.path_manager = getattr(config_manager, 'path_manager', None) if config_manager else None
        
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
        
        # 连接路径管理器信号实现实时同步
        if self.path_manager:
            self.path_manager.globalInputPathChanged.connect(self.onGlobalInputPathChanged)
        
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
        settings_group = SettingCardGroup(self.get_text("extract_audio_title"))
        
        # 路径选择卡片
        self.path_card = SettingCard(
            FluentIcon.FOLDER,
            self.get_text("input_dir"),
            self.get_text("input_dir_placeholder")
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
        self.path_edit.setPlaceholderText(self.get_text("input_dir_placeholder"))
        self.path_edit.setFixedWidth(350)  # 延长路径选择控件长度
        path_layout.addWidget(self.path_edit)
        
        self.browse_button = PushButton(self.get_text("browse"))
        self.browse_button.setIcon(FluentIcon.FOLDER_ADD)
        self.browse_button.setFixedSize(100, 32)
        self.browse_button.clicked.connect(self.browseDirectory)
        path_layout.addWidget(self.browse_button)
        
        # 将路径控件添加到卡片
        self.path_card.hBoxLayout.addWidget(path_widget)
        settings_group.addSettingCard(self.path_card)
        
        # 分类方法选择卡片
        self.classification_card = SettingCard(
            FluentIcon.MENU,
            self.get_text("classification_method"),
            self.get_text("info_duration_categories")  # 默认内容
        )
        
        # 创建分类方法选择控件容器
        classification_widget = QWidget()
        classification_layout = QHBoxLayout(classification_widget)
        classification_layout.setContentsMargins(0, 0, 20, 0)
        classification_layout.setSpacing(8)
        
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
        
        self.classification_combo.setFixedSize(120, 32)
        self.classification_combo.currentIndexChanged.connect(self.updateClassificationInfo)
        
        classification_layout.addStretch()
        classification_layout.addWidget(self.classification_combo)
        
        # 将分类方法控件添加到卡片
        self.classification_card.hBoxLayout.addWidget(classification_widget)
        settings_group.addSettingCard(self.classification_card)
        
        # 线程数设置卡片
        self.threads_card = SettingCard(
            FluentIcon.SPEED_HIGH,
            self.get_text("threads"),
            self.get_text("threads_info")
        )
        
        # 创建线程数控件容器
        threads_widget = QWidget()
        threads_layout = QHBoxLayout(threads_widget)
        threads_layout.setContentsMargins(0, 0, 20, 0)
        threads_layout.setSpacing(8)
        
        self.threads_spin = SpinBox()
        self.threads_spin.setRange(1, 128)  # 设置范围从1到128
        # 设置默认值为CPU核心数的2倍，但不超过32
        default_threads = min(32, multiprocessing.cpu_count() * 2)
        saved_threads = default_threads
        if self.config_manager:
            saved_threads = self.config_manager.get("threads", default_threads)
        self.threads_spin.setValue(saved_threads)
        self.threads_spin.setFixedSize(120, 32)
        
        threads_layout.addStretch()
        threads_layout.addWidget(self.threads_spin)
        
        # 将线程数控件添加到卡片
        self.threads_card.hBoxLayout.addWidget(threads_widget)
        settings_group.addSettingCard(self.threads_card)
        
        # 数据库扫描选项卡片
        self.db_scan_card = SwitchSettingCard(
            FluentIcon.COMMAND_PROMPT,
            self.get_text("scan_database"),
            self.get_text("scan_database_info")
        )
        self.db_scan_card.setChecked(True)  # 默认启用
        settings_group.addSettingCard(self.db_scan_card)
        
        # 音频格式转换设置卡片
        self.convert_audio_card = SettingCard(
            FluentIcon.MEDIA,
            self.get_text("convert_audio_format"),
            self.get_text("convert_audio_format_info")
        )
        
        # 创建转换格式控件容器
        convert_widget = QWidget()
        convert_layout = QHBoxLayout(convert_widget)
        convert_layout.setContentsMargins(0, 0, 20, 0)
        convert_layout.setSpacing(8)
        
        # 转换开关
        self.convert_enabled_switch = SwitchButton()
        self.convert_enabled_switch.setChecked(False)  # 默认关闭
        self.convert_enabled_switch.checkedChanged.connect(self.onConvertEnabledChanged)
        
        # 格式选择下拉菜单
        self.convert_format_combo = ComboBox()
        self.convert_format_combo.addItems(['MP3', 'WAV', 'FLAC', 'AAC', 'M4A'])
        self.convert_format_combo.setCurrentText('MP3')  # 默认选择MP3
        self.convert_format_combo.setFixedSize(80, 32)
        self.convert_format_combo.setEnabled(False)  # 初始禁用
        
        # 保存/读取转换设置
        if self.config_manager:
            convert_enabled = self.config_manager.get("convert_audio_enabled", False)
            convert_format = self.config_manager.get("convert_audio_format", "MP3")
            self.convert_enabled_switch.setChecked(convert_enabled)
            self.convert_format_combo.setCurrentText(convert_format)
            self.convert_format_combo.setEnabled(convert_enabled)
        
        # 连接格式变化信号，实现实时保存
        self.convert_format_combo.currentTextChanged.connect(self.onConvertFormatChanged)
        
        convert_layout.addStretch()
        convert_layout.addWidget(self.convert_enabled_switch)
        convert_layout.addWidget(self.convert_format_combo)
        
        # 将转换控件添加到卡片
        self.convert_audio_card.hBoxLayout.addWidget(convert_widget)
        settings_group.addSettingCard(self.convert_audio_card)

        content_layout.addWidget(settings_group)

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

        # 添加弹性空间，将按钮推至右侧
        button_layout.addStretch()

        self.cancelButton = PushButton(FluentIcon.CANCEL, self.get_text("cancel"))
        self.cancelButton.setFixedHeight(40)
        self.cancelButton.clicked.connect(self.cancelExtraction)
        self.cancelButton.hide()  # 初始隐藏取消按钮
        button_layout.addWidget(self.cancelButton)

        self.extractButton = PrimaryPushButton(FluentIcon.DOWNLOAD, self.get_text("extract"))
        self.extractButton.setFixedHeight(40)
        self.extractButton.clicked.connect(self.startExtraction)
        button_layout.addWidget(self.extractButton)

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
            self.classification_card.contentLabel.setText(self.get_text("info_duration_categories"))
        else: # by size
            self.classification_card.contentLabel.setText(self.get_text("info_size_categories"))
            
    def startExtraction(self):
        """开始提取音频"""
        # 获取有效输入路径（优先使用全局输入路径）
        input_dir = self._getEffectiveInputPath()
        
        # 更新界面显示的路径
        if self.path_edit.text().strip() != input_dir:
            self.path_edit.setText(input_dir)
            self.extractLogHandler.info(self.get_text("using_global_input_path", "使用全局输入路径") + f": {input_dir}")
        
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
            
            # 保存音频格式转换设置
            self.config_manager.set("convert_audio_enabled", self.convert_enabled_switch.isChecked())
            self.config_manager.set("convert_audio_format", self.convert_format_combo.currentText())

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
        scan_db = self.db_scan_card.isChecked()
        
        # 获取自定义输出目录
        custom_output_dir = None
        if self.config_manager:
            custom_dir = self.config_manager.get("custom_output_dir", "")
            if custom_dir and os.path.isdir(custom_dir):
                custom_output_dir = custom_dir
                self.extractLogHandler.info(f"使用自定义输出目录: {custom_output_dir}")
            else:
                self.extractLogHandler.info("使用默认输出目录（基于输入目录）")
        
        # 创建提取工作线程
        self.extraction_worker = ExtractionWorker(
            input_dir, 
            num_threads, 
            self.download_history, 
            classification_method,
            custom_output_dir,  # 使用配置的自定义输出目录
            scan_db,  # 传递数据库扫描选项
            self.convert_enabled_switch.isChecked(),  # 是否启用音频转换
            self.convert_format_combo.currentText()   # 音频转换格式
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

                # 显示音频转换结果
                if "conversion_result" in result:
                    conversion_result = result["conversion_result"]
                    if conversion_result["converted"] > 0:
                        self.handleExtractionLog(f"Audio Conversion: {conversion_result['converted']} files converted to {self.convert_format_combo.currentText()}", "success")
                        # 显示转换文件夹路径
                        if "converted_dir" in conversion_result:
                            self.handleExtractionLog(f"Converted files saved to: {conversion_result['converted_dir']}", "info")
                        if conversion_result["failed"] > 0:
                            self.handleExtractionLog(f"Conversion failures: {conversion_result['failed']} files", "warning")
                    elif conversion_result["failed"] > 0:
                        self.handleExtractionLog(f"Audio conversion failed: {conversion_result['failed']} files", "error")
                elif "conversion_error" in result:
                    self.handleExtractionLog(f"Audio conversion error: {result['conversion_error']}", "error")

                # 输出目录
                final_dir = result.get("output_dir", "")
                # 音频输出文件夹路径
                audio_dir = os.path.join(final_dir, "Audio")
                
                # 确定要打开的目录（优先转换后的文件夹）
                dir_to_open = audio_dir
                dir_description = self.get_text("audio_folder")
                
                # 如果有转换结果且转换成功，优先打开转换后的文件夹
                if "conversion_result" in result and result["conversion_result"]["converted"] > 0:
                    converted_dir = result["conversion_result"].get("converted_dir", "")
                    if converted_dir and os.path.exists(converted_dir):
                        dir_to_open = converted_dir
                        dir_description = f"{self.convert_format_combo.currentText()} files"

                # 根据设置决定是否自动打开目录
                if final_dir and os.path.exists(final_dir) and self.config_manager and self.config_manager.get("auto_open_output_dir", True):
                    # 优先打开确定的目录（原Audio文件夹或转换后文件夹）
                    if os.path.exists(dir_to_open):
                        open_success = open_directory(dir_to_open)
                        if open_success:
                            self.extractLogHandler.info(self.get_text("opening_output_dir", dir_description))
                        else:
                            self.extractLogHandler.info(self.get_text("manual_navigate", dir_to_open))
                    else:
                        # 如果确定的目录不存在，打开根输出目录
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
        # 使用PyQt-Fluent-Widgets原生组件，不需要自定义样式
        pass 
            
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
            
        # 创建下拉菜单
        menu = RoundMenu(parent=self)
        
        # 添加"清除所有历史"选项
        menu.addAction(Action(FluentIcon.DELETE, self.get_text("all_history"), 
                              triggered=lambda: self.clearHistoryByType("all")))
        
        # 添加分隔线
        menu.addSeparator()
        
        # 获取所有可用的记录类型
        if hasattr(self.download_history, "get_record_types"):
            record_types = self.download_history.get_record_types()
            for record_type in record_types:
                # 获取每种类型的记录数量
                records_count = self.download_history.get_history_size(record_type)
                if records_count > 0:
                    # 首字母大写，并添加记录数
                    display_name = f"{record_type.capitalize()} ({records_count})"
                    
                    # 使用闭包参数来避免闭包问题
                    def create_callback(rt):
                        return lambda: self.clearHistoryByType(rt)
                    
                    menu.addAction(Action(FluentIcon.DELETE, display_name, 
                                         triggered=create_callback(record_type)))
        
        # 显示菜单在清除历史按钮下方
        menu.exec_(self.clearHistoryBtn.mapToGlobal(
            QPoint(0, self.clearHistoryBtn.height())))
            
    def updateHistorySize(self):
        """更新历史记录大小显示"""
        if not self.download_history:
            return
        
        # 如果没有历史统计UI组件，直接返回
        if not hasattr(self, 'historyCountLabel'):
            return
            
        # 获取总历史记录数量
        history_size = self.download_history.get_history_size()
        content_size = 0
        if hasattr(self.download_history, 'get_content_hash_count'):
            content_size = self.download_history.get_content_hash_count()
        
        # 获取音频历史记录数量
        audio_history_size = self.download_history.get_history_size('audio')
        
        # 显示格式：总记录数 (音频记录数), 内容哈希数量
        history_text = f"{self.get_text('history_size')}: {history_size} {self.get_text('files')}"
        
        # 如果音频记录数与总记录数不同，添加音频记录数
        if audio_history_size != history_size:
            history_text += f" ({self.get_text('audio')}: {audio_history_size})"
            
        # 添加内容哈希数量
        history_text += f", {content_size} {self.get_text('unique_contents')}"
            
        self.historyCountLabel.setText(history_text) 

    def clearHistoryByType(self, record_type: str):
        """根据类型清除提取历史记录
        
        Args:
            record_type: 要清除的记录类型，'all'表示清除所有记录
        """
        if not self.download_history:
            self.handleExtractionLog(self.get_text("history_not_available"), "error")
            return
            
        try:
            # 清除历史记录
            if record_type == "all":
                self.download_history.clear_history()
                message = self.get_text("all_history_cleared")
            else:
                # 确保record_type是字符串类型，特别处理布尔值False的情况
                if record_type is False:
                    record_type_str = "false"
                else:
                    record_type_str = str(record_type)
                    
                self.download_history.clear_history(record_type_str)
                message = self.get_text("history_type_cleared").format(record_type_str.capitalize())
            
            # 更新历史记录大小显示
            self.updateHistorySize()
            
            # 显示成功消息
            self.handleExtractionLog(message, "success")
            
            InfoBar.success(
                self.get_text("success"),
                message,
                duration=3000,
                position=InfoBarPosition.TOP,
                parent=self._parent_window or self
            )
            
            # 刷新历史界面
            if self._parent_window and hasattr(self._parent_window, 'historyInterface') and \
               hasattr(self._parent_window.historyInterface, 'refreshHistoryInterface'):
                self._parent_window.historyInterface.refreshHistoryInterface()
                
        except Exception as e:
            # 显示错误消息
            error_message = f"{self.get_text('clear_history_failed')}: {str(e)}"
            self.handleExtractionLog(error_message, "error")
            
            InfoBar.error(
                self.get_text("error"),
                error_message,
                duration=3000,
                position=InfoBarPosition.TOP,
                parent=self._parent_window or self
            ) 

    def switchToHistoryInterface(self):
        """切换到历史界面"""
        if self._parent_window and hasattr(self._parent_window, 'historyInterface') and \
           hasattr(self._parent_window, 'switchTo'):
            self._parent_window.switchTo(self._parent_window.historyInterface)
    
    def _getEffectiveInputPath(self) -> str:
        """获取有效的输入路径"""
        # 优先使用路径管理器的有效路径
        if self.path_manager:
            effective_path = self.path_manager.get_effective_input_path()
            if effective_path:
                return effective_path
        
        # 备用方案：使用界面输入框的路径
        path_edit_text = self.path_edit.text().strip() if hasattr(self, 'path_edit') else ""
        if path_edit_text:
            return path_edit_text
        
        # 最后使用默认目录
        return self.default_dir or ""
    
    def onGlobalInputPathChanged(self, new_path: str):
        """全局输入路径变更处理"""
        if hasattr(self, 'path_edit'):
            # 更新界面显示
            current_text = self.path_edit.text().strip()
            if current_text != new_path:
                self.path_edit.setText(new_path)
                # 记录路径变更
                if hasattr(self, 'extractLogHandler'):
                    self.extractLogHandler.info(f"全局输入路径已同步: {new_path}") 

    def onConvertEnabledChanged(self, checked: bool):
        """音频格式转换开关状态变化处理"""
        self.convert_format_combo.setEnabled(checked)
        if self.config_manager:
            self.config_manager.set("convert_audio_enabled", checked)
            self.config_manager.set("convert_audio_format", self.convert_format_combo.currentText())
            # 检查extractLogHandler是否已初始化
            if hasattr(self, 'extractLogHandler'):
                self.extractLogHandler.info(f"音频格式转换{'启用' if checked else '禁用'}") 

    def onConvertFormatChanged(self, text: str):
        """音频格式选择变化处理"""
        if self.config_manager:
            self.config_manager.set("convert_audio_format", text)
            # 检查extractLogHandler是否已初始化
            if hasattr(self, 'extractLogHandler'):
                self.extractLogHandler.info(f"音频格式已设置为: {text}")
    
    def saveConvertSettings(self):
        """强制保存转换设置配置"""
        if self.config_manager:
            self.config_manager.set("convert_audio_enabled", self.convert_enabled_switch.isChecked())
            self.config_manager.set("convert_audio_format", self.convert_format_combo.currentText())
            # 调用配置管理器的保存方法
            self.config_manager.save_config()
            # 检查extractLogHandler是否已初始化
            if hasattr(self, 'extractLogHandler'):
                self.extractLogHandler.info("音频转换设置已保存")
            return True
        return False 