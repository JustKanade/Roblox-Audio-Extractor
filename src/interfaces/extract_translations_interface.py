#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QHBoxLayout
from PyQt5.QtCore import Qt

from qfluentwidgets import (
    SwitchSettingCard, FluentIcon, InfoBar, InfoBarPosition
)

import os

from src.interfaces.base_extract_interface import BaseExtractInterface
from src.extractors.translation_extractor import TranslationClassificationMethod
from src.workers.translation_extraction_worker import TranslationExtractionWorker


class ExtractTranslationsInterface(BaseExtractInterface):
    """翻译文件提取界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None, default_dir=None, download_history=None):
        super().__init__(parent, config_manager, lang, default_dir, download_history)
        self.setObjectName("extractTranslationsInterface")
    
    def getExtractionType(self) -> str:
        """获取提取类型"""
        return "translation"
        
    def getWorkerClass(self):
        """获取工作线程类"""
        return TranslationExtractionWorker
        
    def getClassificationMethods(self) -> list:
        """获取分类方法列表"""
        return [
            self.get_text("by_locale", "按语言区域"),
            self.get_text("by_content_type", "按内容类型"),
            self.get_text("combined_classification", "组合分类"),
            self.get_text("no_classification", "无分类")
        ]
        
    def getClassificationMethodKey(self) -> str:
        """获取分类方法配置键"""
        return "translation_classification_method"
        
    def getThreadsConfigKey(self) -> str:
        """获取线程数配置键"""
        return "threads"
        
    def createSpecificSettingCards(self, settings_group):
        """创建翻译文件特定的设置卡片"""
        # 数据库扫描选项卡片
        self.db_scan_card = SwitchSettingCard(
            FluentIcon.COMMAND_PROMPT,
            self.get_text("scan_database", "扫描数据库"),
            self.get_text("scan_database_info", "同时扫描SQLite数据库中的翻译文件")
        )
        self.db_scan_card.setChecked(True)  # 默认启用
        settings_group.addSettingCard(self.db_scan_card)
        
        # 翻译文件处理开关
        self.convert_card = SwitchSettingCard(
            FluentIcon.LANGUAGE,
            self.get_text("enable_translation_processing", "启用翻译文件处理"),
            self.get_text("process_translation_files", "处理和保存发现的翻译文件")
        )
        
        # 从配置读取初始状态
        if self.config_manager:
            self.convert_card.setChecked(self.config_manager.get("translation_processing_enabled", True))
        else:
            self.convert_card.setChecked(True)
        
        settings_group.addSettingCard(self.convert_card)
        
        # 连接分类方法变更信号
        if hasattr(self, 'classification_combo'):
            self.classification_combo.currentIndexChanged.connect(self.updateClassificationInfo)
            # 初始更新
            self.updateClassificationInfo()
    
    def loadClassificationMethod(self):
        """加载分类方法设置"""
        saved_method = "locale"
        if self.config_manager:
            saved_method = self.config_manager.get("translation_classification_method", "locale")
        if saved_method == "content_type":
            self.classification_combo.setCurrentIndex(1)
        elif saved_method == "combined":
            self.classification_combo.setCurrentIndex(2)
        elif saved_method == "none":
            self.classification_combo.setCurrentIndex(3)
        else:
            self.classification_combo.setCurrentIndex(0)
    
    def updateClassificationInfo(self):
        """更新分类方法信息"""
        if not hasattr(self, 'classification_card'):
            return
            
        index = self.classification_combo.currentIndex()
        if index == 0:  # by_locale
            self.classification_card.contentLabel.setText(
                self.get_text("info_locale_classification", "翻译文件将按语言区域分类存储，如 zh-cn, en-us, fr-fr")
            )
        elif index == 1:  # by_content_type
            self.classification_card.contentLabel.setText(
                self.get_text("info_content_type_classification", "翻译文件将按内容类型分类存储，如 UI文本、错误消息、游戏内容")
            )
        elif index == 2:  # combined
            self.classification_card.contentLabel.setText(
                self.get_text("info_combined_classification", "翻译文件将按语言区域和内容类型组合分类存储")
            )
        else:  # no classification
            self.classification_card.contentLabel.setText(
                self.get_text("info_no_classification", "翻译文件将直接输出到主目录，无需分类")
            )
        
    def getExtractionParameters(self):
        """获取提取参数"""
        # 获取有效输入路径
        input_dir = self._getEffectiveInputPath()
        
        # 获取分类方法
        classification_method_map = {
            0: TranslationClassificationMethod.LOCALE,
            1: TranslationClassificationMethod.CONTENT_TYPE, 
            2: TranslationClassificationMethod.COMBINED,
            3: TranslationClassificationMethod.NONE
        }
        classification_method = classification_method_map[self.classification_combo.currentIndex()]
        
        # 获取线程数
        num_threads = self.threads_spin.value()
        
        # 获取数据库扫描选项
        scan_db = self.db_scan_card.isChecked()
        
        # 获取翻译文件处理选项
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
            "JSON",  # convert_format (保留以兼容接口)
            use_multiprocessing,
            conservative_multiprocessing
        )
        
    def saveConfiguration(self, input_dir):
        """保存配置"""
        if self.config_manager:
            # 保存通用配置
            super().saveConfiguration(input_dir)
            
            # 保存翻译文件特定配置
            self.config_manager.set("translation_processing_enabled", self.convert_card.isChecked())
            self.config_manager.save_config() 