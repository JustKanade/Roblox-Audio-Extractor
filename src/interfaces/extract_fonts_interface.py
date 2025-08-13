#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtCore import Qt

from qfluentwidgets import (
    SwitchSettingCard, FluentIcon, InfoBar, InfoBarPosition
)

import os

from src.interfaces.base_extract_interface import BaseExtractInterface
from src.extractors.font_extractor import FontClassificationMethod
from src.workers.font_extraction_worker import FontExtractionWorker


class ExtractFontsInterface(BaseExtractInterface):
    """字体提取界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None, default_dir=None, download_history=None):
        super().__init__(parent, config_manager, lang, default_dir, download_history)
        self.setObjectName("extractFontsInterface")
    
    def getExtractionType(self) -> str:
        """获取提取类型"""
        return "font"
        
    def getWorkerClass(self):
        """获取工作线程类"""
        return FontExtractionWorker
        
    def getClassificationMethods(self) -> list:
        """获取分类方法列表"""
        return [
            self.get_text("by_font_family", "按字体家族"),
            self.get_text("by_font_style", "按字体样式"),
            self.get_text("by_size", "按文件大小"),
            self.get_text("no_classification", "无分类")
        ]
        
    def getClassificationMethodKey(self) -> str:
        """获取分类方法配置键"""
        return "font_classification_method"
        
    def getThreadsConfigKey(self) -> str:
        """获取线程数配置键"""
        return "font_threads"
        
    def createSpecificSettingCards(self, settings_group):
        """创建字体特定的设置卡片"""
        # 数据库扫描选项卡片
        self.db_scan_card = SwitchSettingCard(
            FluentIcon.COMMAND_PROMPT,
            self.get_text("scan_database", "扫描数据库"),
            self.get_text("scan_database_info", "同时扫描SQLite数据库中的字体文件")
        )
        self.db_scan_card.setChecked(True)  # 默认启用
        settings_group.addSettingCard(self.db_scan_card)
        
        # 字体下载设置卡片
        self.convert_card = SwitchSettingCard(
            FluentIcon.DOWNLOAD,
            self.get_text("download_fonts", "下载字体文件"),
            self.get_text("download_fonts_info", "自动下载FontList中引用的字体文件")
        )
        self.convert_card.setChecked(True)  # 默认启用
        settings_group.addSettingCard(self.convert_card)
        
    def loadClassificationMethod(self):
        """加载分类方法设置"""
        saved_method = "family"
        if self.config_manager:
            saved_method = self.config_manager.get("font_classification_method", "family")
        if saved_method == "style":
            self.classification_combo.setCurrentIndex(1)
        elif saved_method == "size":
            self.classification_combo.setCurrentIndex(2)
        elif saved_method == "none":
            self.classification_combo.setCurrentIndex(3)
        else:
            self.classification_combo.setCurrentIndex(0)
        
    def updateClassificationInfo(self):
        """更新分类方法信息"""
        current_index = self.classification_combo.currentIndex()
        if current_index == 0:  # by family
            self.classification_card.contentLabel.setText(self.get_text("info_font_family_categories", "按字体家族分类"))
        elif current_index == 1:  # by style
            self.classification_card.contentLabel.setText(self.get_text("info_font_style_categories", "按字体样式分类"))
        elif current_index == 2:  # by size
            self.classification_card.contentLabel.setText(self.get_text("info_font_size_categories", "按文件大小分类"))
        else:  # no classification
            self.classification_card.contentLabel.setText(self.get_text("info_no_classification", "文件将直接输出到主目录，无需分类"))
        
    def getExtractionParameters(self):
        """获取提取参数"""
        # 获取有效输入路径
        input_dir = self._getEffectiveInputPath()
        
        # 获取分类方法
        classification_method_map = {
            0: FontClassificationMethod.FAMILY,
            1: FontClassificationMethod.STYLE, 
            2: FontClassificationMethod.SIZE,
            3: FontClassificationMethod.NONE
        }
        classification_method = classification_method_map[self.classification_combo.currentIndex()]
        
        # 获取线程数
        num_threads = self.threads_spin.value()
        
        # 获取数据库扫描选项
        scan_db = self.db_scan_card.isChecked()
        
        # 获取字体下载选项
        convert_enabled = self.convert_card.isChecked()
        
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
            "TTF",  # convert_format (保留以兼容接口)
            use_multiprocessing,
            conservative_multiprocessing
        )
        
    def saveConfiguration(self, input_dir):
        """保存配置"""
        super().saveConfiguration(input_dir)
        
        if self.config_manager:
            # 保存分类方法
            method_map = {0: "family", 1: "style", 2: "size", 3: "none"}
            method = method_map[self.classification_combo.currentIndex()]
            self.config_manager.set("font_classification_method", method) 