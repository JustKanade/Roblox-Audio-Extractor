#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtCore import Qt

from qfluentwidgets import (
    SwitchSettingCard, FluentIcon, InfoBar, InfoBarPosition, ComboBox
)

import os

from src.interfaces.base_extract_interface import BaseExtractInterface
from src.extractors.audio_extractor import ClassificationMethod, is_ffmpeg_available
from src.workers.extraction_worker import ExtractionWorker


class ExtractAudioInterface(BaseExtractInterface):
    """音频提取界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None, default_dir=None, download_history=None):
        super().__init__(parent, config_manager, lang, default_dir, download_history)
        self.setObjectName("extractInterface")
    
    def getExtractionType(self) -> str:
        """获取提取类型"""
        return "audio"
        
    def getWorkerClass(self):
        """获取工作线程类"""
        return ExtractionWorker
        
    def getClassificationMethods(self) -> list:
        """获取分类方法列表"""
        return [
            self.get_text("by_duration", "按时长分类"),
            self.get_text("by_size", "按文件大小")
        ]
        
    def getClassificationMethodKey(self) -> str:
        """获取分类方法配置键"""
        return "classification_method"
        
    def getThreadsConfigKey(self) -> str:
        """获取线程数配置键"""
        return "threads"
        
    def createSpecificSettingCards(self, settings_group):
        """创建音频特定的设置卡片"""
        # 数据库扫描选项卡片
        self.db_scan_card = SwitchSettingCard(
            FluentIcon.COMMAND_PROMPT,
            self.get_text("scan_database", "扫描数据库"),
            self.get_text("scan_database_info", "同时扫描SQLite数据库中的音频文件")
        )
        self.db_scan_card.setChecked(True)  # 默认启用
        settings_group.addSettingCard(self.db_scan_card)
        
        # 转换格式设置卡片
        self.convert_card = SwitchSettingCard(
            FluentIcon.SEND,
            self.get_text("convert_format", "转换格式"),
            self.get_text("convert_info", "转换音频文件格式（需要FFmpeg支持）")
        )
        
        # 检查FFmpeg是否可用
        ffmpeg_available = is_ffmpeg_available()
        self.convert_card.setEnabled(ffmpeg_available)
        
        if not ffmpeg_available:
            self.convert_card.contentLabel.setText(
                self.get_text("ffmpeg_not_available", "FFmpeg不可用，无法进行格式转换")
            )
        
        # 从配置中读取转换开关状态
        convert_enabled = self.config_manager.get("convert_enabled", False) if self.config_manager else False
        self.convert_card.setChecked(convert_enabled and ffmpeg_available)
        
        # 连接开关变化信号
        self.convert_card.checkedChanged.connect(self.onConvertToggled)
        settings_group.addSettingCard(self.convert_card)
        
        # 转换格式选择
        if ffmpeg_available:
            self.createConvertFormatCard(settings_group)
            # 设置初始的启用/禁用状态
            self.onConvertToggled(self.convert_card.isChecked())
    
    def onConvertToggled(self, isChecked):
        """转换格式开关变化事件"""
        # 启用/禁用格式选择卡片和控件
        if hasattr(self, 'format_card'):
            self.format_card.setEnabled(isChecked)
        if hasattr(self, 'format_combo'):
            self.format_combo.setEnabled(isChecked)
            
        # 记录状态变化（可选）
        if hasattr(self, 'extractLogHandler'):
            status = self.get_text("enabled", "已启用") if isChecked else self.get_text("disabled", "已禁用")
            self.extractLogHandler.info(f"{self.get_text('convert_format', '转换格式')}: {status}")
    
    def createConvertFormatCard(self, settings_group):
        """创建转换格式选择卡片"""
        from qfluentwidgets import SettingCard
        
        self.format_card = SettingCard(
            FluentIcon.MUSIC,
            self.get_text("output_format", "输出格式"),
            self.get_text("select_output_format", "选择音频输出格式")
        )
        
        # 创建格式选择控件容器
        format_widget = QWidget()
        format_layout = QHBoxLayout(format_widget)
        format_layout.setContentsMargins(0, 0, 20, 0)
        format_layout.setSpacing(8)
        
        self.format_combo = ComboBox()
        self.format_combo.addItems(["MP3", "WAV", "FLAC", "AAC"])
        
        # 设置默认格式
        saved_format = "MP3"
        if self.config_manager:
            saved_format = self.config_manager.get("convert_format", "MP3")
        
        format_index = 0
        for i, fmt in enumerate(["MP3", "WAV", "FLAC", "AAC"]):
            if fmt == saved_format:
                format_index = i
                break
        self.format_combo.setCurrentIndex(format_index)
        self.format_combo.setFixedSize(120, 32)
        
        format_layout.addStretch()
        format_layout.addWidget(self.format_combo)
        
        # 将格式选择控件添加到卡片
        self.format_card.hBoxLayout.addWidget(format_widget)
        settings_group.addSettingCard(self.format_card)
        
    def loadClassificationMethod(self):
        """加载分类方法设置"""
        saved_method = "duration"
        if self.config_manager:
            saved_method = self.config_manager.get("classification_method", "duration")
        if saved_method == "size":
            self.classification_combo.setCurrentIndex(1)
        else:
            self.classification_combo.setCurrentIndex(0)
        
    def updateClassificationInfo(self):
        """更新分类方法信息"""
        current_index = self.classification_combo.currentIndex()
        if current_index == 0:  # by duration
            self.classification_card.contentLabel.setText(self.get_text("info_duration_categories", "按音频时长分类"))
        else:  # by size
            self.classification_card.contentLabel.setText(self.get_text("info_size_categories", "按文件大小分类"))
        
    def getExtractionParameters(self):
        """获取提取参数"""
        # 获取有效输入路径
        input_dir = self._getEffectiveInputPath()
        
        # 获取分类方法
        classification_method_map = {
            0: ClassificationMethod.DURATION,
            1: ClassificationMethod.SIZE
        }
        classification_method = classification_method_map[self.classification_combo.currentIndex()]
        
        # 获取线程数
        num_threads = self.threads_spin.value()
        
        # 获取数据库扫描选项
        scan_db = self.db_scan_card.isChecked()
        
        # 获取转换设置
        convert_enabled = self.convert_card.isChecked() if hasattr(self, 'convert_card') else False
        convert_format = "MP3"
        if hasattr(self, 'format_combo'):
            convert_format = self.format_combo.currentText()
        
        # 获取自定义输出目录
        custom_output_dir = None
        if self.config_manager:
            custom_dir = self.config_manager.get("custom_output_dir", "")
            if custom_dir and os.path.isdir(custom_dir):
                custom_output_dir = custom_dir
                self.extractLogHandler.info(f"{self.get_text('using_custom_output_dir', '使用自定义输出目录')}: {custom_output_dir}")
            else:
                self.extractLogHandler.info(self.get_text("using_default_output_dir", "使用默认输出目录"))
        
        # 获取多进程配置
        use_multiprocessing = self.config_manager.get("useMultiprocessing", False) if self.config_manager else False
        conservative_multiprocessing = self.config_manager.get("conservativeMultiprocessing", True) if self.config_manager else True
        
        return (
            input_dir, 
            num_threads, 
            self.download_history, 
            classification_method,
            custom_output_dir,
            scan_db,
            convert_enabled,
            convert_format,
            use_multiprocessing,
            conservative_multiprocessing
        )
        
    def saveConfiguration(self, input_dir):
        """保存配置"""
        super().saveConfiguration(input_dir)
        
        if self.config_manager:
            # 保存分类方法
            method_map = {0: "duration", 1: "size"}
            method = method_map[self.classification_combo.currentIndex()]
            self.config_manager.set("classification_method", method)
            
            # 保存转换设置
            if hasattr(self, 'convert_card'):
                self.config_manager.set("convert_enabled", self.convert_card.isChecked())
            if hasattr(self, 'format_combo'):
                self.config_manager.set("convert_format", self.format_combo.currentText())