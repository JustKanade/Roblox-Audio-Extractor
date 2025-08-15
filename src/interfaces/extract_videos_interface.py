#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频提取界面 - 提供视频提取的用户界面
Video Extract Interface - Provides user interface for video extraction
"""

import os
import multiprocessing
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout

from qfluentwidgets import (
    SettingCardGroup, SwitchSettingCard, ComboBox, FluentIcon,
    BodyLabel, InfoBar, InfoBarPosition, SettingCard
)

from .base_extract_interface import BaseExtractInterface
from src.extractors.video_extractor import VideoClassificationMethod, VideoQualityPreference
from src.workers.video_extraction_worker import VideoExtractionWorker

class ExtractVideosInterface(BaseExtractInterface):
    """视频提取界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None, default_dir=None, download_history=None):
        super().__init__(parent, config_manager, lang, default_dir, download_history)
        self.setObjectName("extractVideosInterface")
        
    def getExtractionType(self) -> str:
        """获取提取类型"""
        return "video"
        
    def getWorkerClass(self):
        """获取工作线程类"""
        return VideoExtractionWorker
        
    def getClassificationMethods(self) -> list:
        """获取分类方法列表"""
        return [
            self.get_text("by_resolution", "By Resolution"),
            self.get_text("by_size", "By Size"),
            self.get_text("by_duration", "By Duration"),  
            self.get_text("no_classification", "No Classification")
        ]
        
    def getClassificationMethodKey(self) -> str:
        """获取分类方法配置键"""
        return "video_classification_method"
        
    def getThreadsConfigKey(self) -> str:
        """获取线程数配置键"""
        return "threads"
        
    def createSpecificSettingCards(self, settings_group):
        """创建视频特定的设置卡片"""
        # 数据库扫描选项卡片
        self.db_scan_card = SwitchSettingCard(
            FluentIcon.COMMAND_PROMPT,
            self.get_text("scan_database", "扫描数据库"),
            self.get_text("scan_database_info", "同时扫描SQLite数据库中的视频播放列表")
        )
        self.db_scan_card.setChecked(True)  # 默认启用
        settings_group.addSettingCard(self.db_scan_card)
        
        # FFmpeg依赖提示卡片
        self.createFFmpegWarningCard(settings_group)
        
        # 视频质量设置卡片
        self.createVideoQualityCard(settings_group)
        
        # 视频处理设置卡片
        self.createVideoProcessingCard(settings_group)
        
        # 网络设置卡片
        self.createNetworkSettingsCard(settings_group)
        
        # 存储清理设置卡片
        self.createStorageSettingsCard(settings_group)
        
        # 格式转换设置卡片
        self.createFormatConversionCard(settings_group)
    
    def createFFmpegWarningCard(self, parent_group):
        """创建FFmpeg警告卡片"""
        # 检查FFmpeg是否可用
        import shutil
        ffmpeg_available = shutil.which('ffmpeg') is not None
        
        if not ffmpeg_available:
            # 创建FFmpeg警告卡片
            ffmpeg_warning_card = SettingCardGroup(
                self.get_text("ffmpeg_required", "FFmpeg Required")
            )
            
            warning_label = BodyLabel(
                self.get_text("video_ffmpeg_warning", 
                    "⚠ FFmpeg is required for video processing. Please install FFmpeg to enable video merging functionality.")
            )
            warning_label.setWordWrap(True)
            
            # 添加到父组
            parent_group.addSettingCard(warning_label)
    
    def createVideoQualityCard(self, parent_group):
        """创建视频质量选择卡片"""
        self.video_quality_card = SettingCard(
            FluentIcon.VIDEO,
            self.get_text("video_quality_selection", "Video Quality Selection"),
            self.get_text("video_quality_desc", "Select preferred video quality for extraction. Auto selects the best available quality.")
        )
        
        # 创建质量选择控件容器
        quality_widget = QWidget()
        quality_layout = QHBoxLayout(quality_widget)
        quality_layout.setContentsMargins(0, 0, 20, 0)
        quality_layout.setSpacing(8)
        
        self.video_quality_combo = ComboBox()
        quality_options = [
            self.get_text("video_quality_auto", "Auto (Best Quality)"),
            self.get_text("video_quality_1080p", "1080p"),
            self.get_text("video_quality_720p", "720p"),
            self.get_text("video_quality_480p", "480p"),
            self.get_text("video_quality_lowest", "Lowest Available")
        ]
        self.video_quality_combo.addItems(quality_options)
        
        quality_layout.addWidget(self.video_quality_combo)
        quality_layout.addStretch()
        
        # 将控件添加到卡片
        self.video_quality_card.hBoxLayout.addWidget(quality_widget)
        
        # 从配置中读取当前设置
        current_quality_str = self.config_manager.get("video_quality_preference", "auto") if self.config_manager else "auto"
        quality_index_map = {
            "auto": 0,
            "1080p": 1,
            "720p": 2,
            "480p": 3,
            "lowest": 4
        }
        current_quality_index = quality_index_map.get(current_quality_str, 0)
        self.video_quality_combo.setCurrentIndex(current_quality_index)
        
        # 连接信号
        self.video_quality_combo.currentIndexChanged.connect(self.onVideoQualityChanged)
        
        parent_group.addSettingCard(self.video_quality_card)
    
    def createVideoProcessingCard(self, parent_group):
        """创建视频处理设置卡片"""
        processing_group = SettingCardGroup(
            self.get_text("video_processing_settings", "Video Processing")
        )
        
        # 时间戳修复设置
        self.timestamp_repair_card = SwitchSettingCard(
            FluentIcon.HISTORY,
            self.get_text("video_timestamp_repair", "Video Timestamp Repair"),
            self.get_text("video_timestamp_repair_desc", "Automatically repair video segment timestamps for smooth playback (requires FFmpeg)"),
            configItem=None,
            parent=processing_group
        )
        
        # 从配置中读取当前设置
        current_repair = self.config_manager.get("video_timestamp_repair", True) if self.config_manager else True
        self.timestamp_repair_card.setChecked(current_repair)
        
        # 连接信号
        self.timestamp_repair_card.checkedChanged.connect(self.onTimestampRepairChanged)
        
        processing_group.addSettingCard(self.timestamp_repair_card)
        parent_group.addSettingCard(processing_group)
    
    def createNetworkSettingsCard(self, parent_group):
        """创建网络设置卡片"""
        network_group = SettingCardGroup(
            self.get_text("network_settings", "Network Settings")
        )
        
        # 并发下载设置
        self.concurrent_downloads_card = SwitchSettingCard(
            FluentIcon.CLOUD,
            self.get_text("concurrent_downloads", "Concurrent Segment Downloads"),
            self.get_text("concurrent_downloads_desc", "Enable parallel downloading of video segments for faster processing"),
            configItem=None,
            parent=network_group
        )
        
        # 从配置中读取当前设置
        current_concurrent = self.config_manager.get("video_concurrent_downloads", True) if self.config_manager else True
        self.concurrent_downloads_card.setChecked(current_concurrent)
        
        # 连接信号
        self.concurrent_downloads_card.checkedChanged.connect(self.onConcurrentDownloadsChanged)
        
        network_group.addSettingCard(self.concurrent_downloads_card)
        
        # 重试设置卡片
        # 这里可以添加更多网络相关设置，如超时时间、重试次数等
        
        parent_group.addSettingCard(network_group)
    
    def createStorageSettingsCard(self, parent_group):
        """创建存储设置卡片"""
        storage_group = SettingCardGroup(
            self.get_text("storage_settings", "Storage Settings")
        )
        
        # 自动清理临时文件
        self.auto_cleanup_card = SwitchSettingCard(
            FluentIcon.DELETE,
            self.get_text("auto_cleanup_temp", "Auto Clean Temporary Files"),
            self.get_text("auto_cleanup_temp_desc", "Automatically clean up temporary segment files after video processing"),
            configItem=None,
            parent=storage_group
        )
        
        # 从配置中读取当前设置
        current_cleanup = self.config_manager.get("video_auto_cleanup", True) if self.config_manager else True
        self.auto_cleanup_card.setChecked(current_cleanup)
        
        # 连接信号
        self.auto_cleanup_card.checkedChanged.connect(self.onAutoCleanupChanged)
        
        storage_group.addSettingCard(self.auto_cleanup_card)
        parent_group.addSettingCard(storage_group)
    
    def createFormatConversionCard(self, parent_group):
        """创建格式转换设置卡片组"""
        # 检查FFmpeg是否可用
        import shutil
        ffmpeg_available = shutil.which('ffmpeg') is not None
        
        conversion_group = SettingCardGroup(
            self.get_text("video_format_conversion", "Video Format Conversion")
        )
        
        # 格式转换开关卡片
        self.convert_card = SwitchSettingCard(
            FluentIcon.MOVIE,
            self.get_text("convert_video_format", "Convert Video Format"),
            self.get_text("convert_video_format_desc", "Convert videos to specified format using FFmpeg")
        )
        
        # 读取配置
        convert_enabled = self.config_manager.get("convert_video_enabled", False) if self.config_manager else False
        self.convert_card.setChecked(convert_enabled and ffmpeg_available)
        
        # 如果FFmpeg不可用，禁用开关
        if not ffmpeg_available:
            self.convert_card.setEnabled(False)
            self.convert_card.setChecked(False)
        
        self.convert_card.checkedChanged.connect(self.onVideoConvertToggled)
        conversion_group.addSettingCard(self.convert_card)
        
        # 格式选择卡片
        self.createVideoFormatCard(conversion_group, ffmpeg_available)
        
        # 如果FFmpeg不可用，显示警告
        if not ffmpeg_available:
            warning_label = BodyLabel(
                self.get_text("video_conversion_ffmpeg_warning", 
                    "⚠ FFmpeg is required for video format conversion. Please install FFmpeg to enable this feature.")
            )
            warning_label.setWordWrap(True)
            conversion_group.addSettingCard(warning_label)
        
        parent_group.addSettingCard(conversion_group)
    
    def createVideoFormatCard(self, parent_group, ffmpeg_available):
        """创建视频格式选择卡片"""
        self.format_card = SettingCard(
            FluentIcon.VIDEO,
            self.get_text("output_video_format", "Output Video Format"),
            self.get_text("select_output_video_format", "Select the output video format")
        )
        
        # 创建格式选择控件容器
        format_widget = QWidget()
        format_layout = QHBoxLayout(format_widget)
        format_layout.setContentsMargins(0, 0, 20, 0)
        format_layout.setSpacing(8)
        
        self.format_combo = ComboBox()
        self.format_combo.addItems(["MP4", "AVI", "MKV", "MOV", "WEBM"])
        
        # 设置默认格式
        saved_format = "MP4"
        if self.config_manager:
            saved_format = self.config_manager.get("convert_video_format", "MP4")
        
        format_index = 0
        for i, fmt in enumerate(["MP4", "AVI", "MKV", "MOV", "WEBM"]):
            if fmt == saved_format:
                format_index = i
                break
        self.format_combo.setCurrentIndex(format_index)
        self.format_combo.setFixedSize(120, 32)
        
        # 保存格式变化
        self.format_combo.currentTextChanged.connect(self.onVideoFormatChanged)
        
        format_layout.addStretch()
        format_layout.addWidget(self.format_combo)
        
        # 将格式选择控件添加到卡片
        self.format_card.hBoxLayout.addWidget(format_widget)
        
        # 根据转换开关和FFmpeg可用性设置启用状态
        convert_enabled = self.config_manager.get("convert_video_enabled", False) if self.config_manager else False
        self.format_card.setEnabled(convert_enabled and ffmpeg_available)
        
        parent_group.addSettingCard(self.format_card)
    
    def onVideoConvertToggled(self, isChecked):
        """视频格式转换开关变化事件"""
        # 启用/禁用格式选择卡片
        if hasattr(self, 'format_card'):
            self.format_card.setEnabled(isChecked)
        if hasattr(self, 'format_combo'):
            self.format_combo.setEnabled(isChecked)
            
        # 保存设置
        if self.config_manager:
            self.config_manager.set("convert_video_enabled", isChecked)
            self.config_manager.save_config()
            
        # 记录状态变化
        if hasattr(self, 'extractLogHandler'):
            status = self.get_text("enabled", "已启用") if isChecked else self.get_text("disabled", "已禁用")
            self.extractLogHandler.info(f"{self.get_text('video_format_conversion', '视频格式转换')}: {status}")
    
    def onVideoFormatChanged(self, format_text):
        """视频格式选择变化事件"""
        if self.config_manager:
            self.config_manager.set("convert_video_format", format_text)
            self.config_manager.save_config()
    
    def onConcurrentDownloadsChanged(self, checked):
        """处理并发下载设置变更"""
        if self.config_manager:
            self.config_manager.set("video_concurrent_downloads", checked)
        
        # 显示状态信息
        if checked:
            message = self.get_text("concurrent_downloads_enabled", "Concurrent downloads enabled")
        else:
            message = self.get_text("concurrent_downloads_disabled", "Concurrent downloads disabled")
        
        InfoBar.success(
            title=self.get_text("settings_updated", "Settings Updated"),
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def onAutoCleanupChanged(self, checked):
        """处理自动清理设置变更"""
        if self.config_manager:
            self.config_manager.set("video_auto_cleanup", checked)
        
        # 显示状态信息
        if checked:
            message = self.get_text("auto_cleanup_enabled", "Auto cleanup enabled")
        else:
            message = self.get_text("auto_cleanup_disabled", "Auto cleanup disabled")
        
        InfoBar.success(
            title=self.get_text("settings_updated", "Settings Updated"),
            content=message,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def onVideoQualityChanged(self, index: int):
        """处理视频质量设置变更"""
        if self.config_manager:
            # 将索引转换为配置值
            index_to_value_map = {
                0: "auto",
                1: "1080p", 
                2: "720p",
                3: "480p",
                4: "lowest"
            }
            quality_value = index_to_value_map.get(index, "auto")
            
            self.config_manager.set("video_quality_preference", quality_value)
            self.config_manager.save_config()
            
            # 获取质量名称用于显示
            quality_names = ["Auto", "1080p", "720p", "480p", "Lowest"]
            quality_name = quality_names[index] if index < len(quality_names) else "Auto"
            
            # 显示通知
            message = self.get_text("video_selected_quality", "Selected video quality: {}").format(quality_name)
            InfoBar.success(
                title=self.get_text("settings_updated", "Settings Updated"),
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
    
    def onTimestampRepairChanged(self, checked: bool):
        """处理时间戳修复设置变更"""
        if self.config_manager:
            self.config_manager.set("video_timestamp_repair", checked)
            self.config_manager.save_config()
            
            # 显示通知
            message = self.get_text("video_timestamp_repair_enabled", "Timestamp repair enabled") if checked else self.get_text("video_timestamp_repair_disabled", "Timestamp repair disabled")
            InfoBar.success(
                title=self.get_text("settings_updated", "Settings Updated"),
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
    
    def getExtractionParameters(self):
        """获取视频提取参数"""
        # 获取有效输入路径
        input_dir = self._getEffectiveInputPath()
        
        # 获取分类方法
        classification_method = self.getSelectedClassificationMethod()
        
        # 获取线程数
        num_threads = self.threads_spin.value()
        
        # 获取数据库扫描选项
        scan_db = self.db_scan_card.isChecked() if hasattr(self, 'db_scan_card') else True
        
        # 获取自定义输出目录
        custom_output_dir = None
        if self.config_manager:
            custom_dir = self.config_manager.get("custom_output_dir", "")
            if custom_dir and os.path.isdir(custom_dir):
                custom_output_dir = custom_dir
                if hasattr(self, 'extractLogHandler'):
                    self.extractLogHandler.info(f"{self.get_text('using_custom_output_dir', '使用自定义输出目录')}: {custom_output_dir}")
            else:
                if hasattr(self, 'extractLogHandler'):
                    self.extractLogHandler.info(self.get_text("using_default_output_dir", "使用默认输出目录"))
        
        # 获取多进程配置
        use_multiprocessing = self.config_manager.get("useMultiprocessing", False) if self.config_manager else False
        conservative_multiprocessing = self.config_manager.get("conservativeMultiprocessing", True) if self.config_manager else True
        
        # 获取视频特定配置
        concurrent_downloads = self.config_manager.get("video_concurrent_downloads", True) if self.config_manager else True
        auto_cleanup = self.config_manager.get("video_auto_cleanup", True) if self.config_manager else True
        ffmpeg_path = self.config_manager.get("ffmpeg_path", None) if self.config_manager else None
        
        # 获取视频质量偏好
        quality_preference = self.getSelectedVideoQuality()
        
        # 获取时间戳修复设置
        timestamp_repair = self.config_manager.get("video_timestamp_repair", True) if self.config_manager else True
        
        # 获取格式转换设置
        convert_enabled = False
        convert_format = "MP4"
        if hasattr(self, 'convert_card') and hasattr(self, 'format_combo'):
            import shutil
            ffmpeg_available = shutil.which('ffmpeg') is not None
            convert_enabled = self.convert_card.isChecked() and ffmpeg_available
            convert_format = self.format_combo.currentText()
        
        return (
            input_dir,
            num_threads,
            self.download_history,
            classification_method,
            custom_output_dir,
            scan_db,
            use_multiprocessing,
            conservative_multiprocessing,
            concurrent_downloads,
            auto_cleanup,
            ffmpeg_path,
            quality_preference,
            timestamp_repair,
            convert_enabled,
            convert_format
        )
    
    def getSelectedClassificationMethod(self):
        """获取选中的分类方法"""
        if hasattr(self, 'classification_combo'):
            # 使用索引映射将ComboBox索引转换为枚举值
            classification_method_map = {
                0: VideoClassificationMethod.RESOLUTION,
                1: VideoClassificationMethod.SIZE,
                2: VideoClassificationMethod.DURATION,
                3: VideoClassificationMethod.NONE
            }
            index = self.classification_combo.currentIndex()
            return classification_method_map.get(index, VideoClassificationMethod.RESOLUTION)
        
        # 返回默认值
        return VideoClassificationMethod.RESOLUTION
    
    def getSelectedVideoQuality(self):
        """获取选中的视频质量偏好"""
        if hasattr(self, 'video_quality_combo'):
            # 使用索引映射将ComboBox索引转换为枚举值
            quality_map = {
                0: VideoQualityPreference.AUTO,
                1: VideoQualityPreference.P1080,
                2: VideoQualityPreference.P720,
                3: VideoQualityPreference.P480,
                4: VideoQualityPreference.LOWEST
            }
            return quality_map.get(self.video_quality_combo.currentIndex(), VideoQualityPreference.AUTO)
        else:
            return VideoQualityPreference.AUTO
    
    def updateClassificationInfo(self):
        """更新分类方法说明信息"""
        if not hasattr(self, 'classification_card'):
            return
            
        current_index = self.classification_combo.currentIndex()
        
        if current_index == 0:  # by resolution
            info_text = self.get_text("info_resolution_categories", 
                "Videos will be sorted into folders by resolution (e.g., 720p, 1080p)")
        elif current_index == 1:  # by size
            info_text = self.get_text("info_size_categories",
                "Videos will be sorted into folders by file size")
        elif current_index == 2:  # by duration
            info_text = self.get_text("info_duration_categories",
                "Videos will be sorted into folders by duration")
        elif current_index == 3:  # no classification
            info_text = self.get_text("info_no_classification",
                "Videos will be output directly to the main directory without classification")
        else:
            info_text = self.get_text("info_video_default_category",
                "Select video classification method")
        
        self.classification_card.contentLabel.setText(info_text)
    
    def showExtractionComplete(self, result_info):
        """显示提取完成信息"""
        if not result_info or not result_info.get('success', False):
            return
        
        stats = result_info.get('stats', {})
        
        # 构建消息
        messages = []
        messages.append(f"{self.get_text('videos_processed', 'Videos processed')}: {stats.get('processed_videos', 0)}")
        messages.append(f"{self.get_text('segments_downloaded', 'Segments downloaded')}: {stats.get('downloaded_segments', 0)}")
        messages.append(f"{self.get_text('videos_merged', 'Videos merged')}: {stats.get('merged_videos', 0)}")
        
        if stats.get('duplicate_videos', 0) > 0:
            messages.append(f"{self.get_text('duplicate_videos', 'Duplicate videos skipped')}: {stats.get('duplicate_videos', 0)}")
        
        if stats.get('download_failures', 0) > 0:
            messages.append(f"{self.get_text('download_failures', 'Download failures')}: {stats.get('download_failures', 0)}")
        
        duration = result_info.get('duration', 0)
        messages.append(f"{self.get_text('time_spent', 'Time spent')}: {duration:.2f} {self.get_text('seconds', 'seconds')}")
        
        message = '\n'.join(messages)
        
        InfoBar.success(
            title=self.get_text("video_extraction_complete", "Video extraction completed!"),
            content=message,
            orient=Qt.Vertical,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=5000,
            parent=self
        )
    
    def loadClassificationMethod(self):
        """加载分类方法设置"""
        saved_method = "resolution"
        if self.config_manager:
            saved_method = self.config_manager.get("video_classification_method", "resolution")
        
        if saved_method == "size":
            self.classification_combo.setCurrentIndex(1)
        elif saved_method == "duration":
            self.classification_combo.setCurrentIndex(2)
        elif saved_method == "none":
            self.classification_combo.setCurrentIndex(3)
        else:
            self.classification_combo.setCurrentIndex(0)
    
    def saveConfiguration(self, input_dir):
        """保存配置"""
        super().saveConfiguration(input_dir)
        
        if self.config_manager:
            # 保存分类方法
            method_map = {0: "resolution", 1: "size", 2: "duration", 3: "none"}
            method = method_map[self.classification_combo.currentIndex()]
            self.config_manager.set("video_classification_method", method)
            
            # 保存视频质量偏好
            if hasattr(self, 'video_quality_combo'):
                index_to_value_map = {0: "auto", 1: "1080p", 2: "720p", 3: "480p", 4: "lowest"}
                quality_value = index_to_value_map.get(self.video_quality_combo.currentIndex(), "auto")
                self.config_manager.set("video_quality_preference", quality_value)
            
            # 保存时间戳修复设置
            if hasattr(self, 'timestamp_repair_card'):
                self.config_manager.set("video_timestamp_repair", self.timestamp_repair_card.isChecked())
            
            # 保存并发下载设置
            if hasattr(self, 'concurrent_downloads_card'):
                self.config_manager.set("video_concurrent_downloads", self.concurrent_downloads_card.isChecked())
            
            # 保存自动清理设置
            if hasattr(self, 'auto_cleanup_card'):
                self.config_manager.set("video_auto_cleanup", self.auto_cleanup_card.isChecked())
            
            # 保存格式转换设置
            if hasattr(self, 'convert_card'):
                self.config_manager.set("convert_video_enabled", self.convert_card.isChecked())
            
            if hasattr(self, 'format_combo'):
                self.config_manager.set("convert_video_format", self.format_combo.currentText())
            
            # 确保配置保存到文件
            self.config_manager.save_config() 

    def updateHistorySize(self):
        """更新历史记录大小显示"""
        if self.download_history:
            super().updateHistorySize()

 