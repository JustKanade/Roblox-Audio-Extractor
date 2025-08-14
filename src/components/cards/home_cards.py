#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
首页卡片组件
Home Page Card Components
"""

import os
import multiprocessing
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget

from qfluentwidgets import (
    SettingCard, CardWidget, StrongBodyLabel, BodyLabel, CaptionLabel,
    FluentIcon, PrimaryPushButton, PushButton, TransparentPushButton,
    PillPushButton, FlowLayout, PrimaryDropDownPushButton, RoundMenu, Action
)


class QuickActionsCard(SettingCard):
    """快速操作卡片"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        super().__init__(
            FluentIcon.SPEED_HIGH,
            self.get_text("quick_actions", "Quick Actions"),
            self.get_text("quick_actions_description", "Commonly used functions for faster access"),
            parent
        )
        
        self._setupContent()
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(12)
        
        # 不再添加任何按钮，仅保留空内容容器
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)


class ExtractAudioCard(SettingCard):
    """音频提取卡片"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        super().__init__(
            FluentIcon.DOWNLOAD,
            self.get_text("extract_audio", "Extract Audio"),
            self.get_text("extract_audio_description", "Extract audio files from Roblox cache for playback"),
            parent
        )
        
        self._setupContent()
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 创建开始提取按钮
        self.extract_btn = PrimaryPushButton(FluentIcon.DOWNLOAD, self.get_text("start_extraction"))
        self.extract_btn.setFixedSize(145, 32)
        
        content_layout.addWidget(self.extract_btn)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)


class ExtractFontsCard(SettingCard):
    """字体提取卡片"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        super().__init__(
            FluentIcon.FONT,
            self.get_text("extract_fonts", "Extract Fonts"),
            self.get_text("extract_fonts_description", "Extract font files from Roblox cache and download associated fonts"),
            parent
        )
        
        self._setupContent()
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 创建字体提取按钮
        self.extract_btn = PrimaryPushButton(FluentIcon.FONT, self.get_text("extract", "开始提取字体"))
        self.extract_btn.setFixedSize(145, 32)
        
        content_layout.addWidget(self.extract_btn)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)


class ClearCacheCard(SettingCard):
    """清理缓存卡片"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        super().__init__(
            FluentIcon.DELETE,
            self.get_text("clear_cache", "Clear Cache"),
            self.get_text("clear_cache_description", "Clean up temporary files and cached data to free up disk space"),
            parent
        )
        
        self._setupContent()
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 创建清理缓存按钮
        self.clear_btn = PushButton(FluentIcon.DELETE, self.get_text("start_cleaning"))
        self.clear_btn.setFixedSize(145, 32)
        
        content_layout.addWidget(self.clear_btn)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)


class SettingsCard(SettingCard):
    """设置卡片"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        super().__init__(
            FluentIcon.SETTING,
            self.get_text("settings", "Settings"),
            self.get_text("settings_description", "Configure application preferences and customize your experience"),
            parent
        )
        
        self._setupContent()
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 创建打开设置按钮
        self.settings_btn = TransparentPushButton(FluentIcon.SETTING, self.get_text("open_settings"))
        self.settings_btn.setFixedSize(145, 32)
        
        content_layout.addWidget(self.settings_btn)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)


class SystemInfoHomeCard(SettingCard):
    """首页系统信息卡片"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        # 收集系统信息
        cpu_info = f"{self.get_text('cpu_cores')}: {multiprocessing.cpu_count()}"
        recommended_threads = f"{self.get_text('recommended_threads')}: {min(32, multiprocessing.cpu_count() * 2)}"
        
        # 检查FFmpeg状态
        try:
            from src.extractors.audio_extractor import is_ffmpeg_available
            ffmpeg_status = f"{self.get_text('ffmpeg_status')}: {self.get_text('available') if is_ffmpeg_available() else self.get_text('not_available')}"
        except ImportError:
            ffmpeg_status = f"{self.get_text('ffmpeg_status')}: {self.get_text('unknown')}"
        
        system_info = f"{cpu_info} | {recommended_threads} | {ffmpeg_status}"
        
        super().__init__(
            FluentIcon.APPLICATION,
            self.get_text("system_info", "System Information"),
            system_info,
            parent
        )


class DirectoryInfoCard(SettingCard):
    """目录信息卡片"""
    
    def __init__(self, parent=None, lang=None, default_dir=""):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        self.default_dir = default_dir
        
        super().__init__(
            FluentIcon.FOLDER,
            self.get_text("default_dir", "Default Directory"),
            default_dir,
            parent
        )
        
        self._setupContent()
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 创建目录操作按钮
        self.open_dir_btn = PillPushButton(FluentIcon.FOLDER, self.get_text("open_directory"))
        self.open_dir_btn.setFixedHeight(32)
        self.open_dir_btn.setCheckable(False)
        
        self.copy_path_btn = TransparentPushButton(FluentIcon.COPY, self.get_text("copy_path"))
        self.copy_path_btn.setFixedHeight(32)
        
        content_layout.addWidget(self.open_dir_btn)
        content_layout.addWidget(self.copy_path_btn)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget) 


class ExtractMenuCard(SettingCard):
    """提取菜单卡片 - 包含音频和字体提取的下拉菜单"""
    
    def __init__(self, parent=None, lang=None):
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        super().__init__(
            FluentIcon.DOWNLOAD,
            self.get_text("extract_menu_button_title", "Extract Content"),
            self.get_text("extract_menu_button_description", "Choose extraction type and access related functions"),
            parent
        )
        
        self._setupContent()
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 创建下拉菜单
        self.menu = RoundMenu(parent=content_widget)
        
        # 添加音频提取菜单项
        self.audio_action = Action(
            FluentIcon.MUSIC,
            self.get_text("extract_audio_menu_item", "Extract Audio"),
            parent=self.menu
        )
        self.menu.addAction(self.audio_action)
        
        # 添加字体提取菜单项
        self.fonts_action = Action(
            FluentIcon.FONT,
            self.get_text("extract_fonts_menu_item", "Extract Fonts"),
            parent=self.menu
        )
        self.menu.addAction(self.fonts_action)
        
        # 添加翻译文件提取菜单项
        self.translations_action = Action(
            FluentIcon.LANGUAGE,
            self.get_text("extract_translations_menu_item", "Extract Translations"),
            parent=self.menu
        )
        self.menu.addAction(self.translations_action)
        
        # 添加视频提取菜单项
        self.videos_action = Action(
            FluentIcon.VIDEO,
            self.get_text("extract_videos_menu_item", "Extract Videos"),
            parent=self.menu
        )
        self.menu.addAction(self.videos_action)
        
        # 创建下拉按钮
        self.extract_dropdown_btn = PrimaryDropDownPushButton(
            FluentIcon.DOWNLOAD,
            self.get_text("extract_menu_button_text", "Start Extraction"),
            content_widget
        )
        self.extract_dropdown_btn.setMenu(self.menu)
        self.extract_dropdown_btn.setFixedSize(165, 32)
        
        content_layout.addWidget(self.extract_dropdown_btn)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)
    
    def get_audio_action(self):
        """获取音频提取动作"""
        return self.audio_action
    
    def get_fonts_action(self):
        """获取字体提取动作"""
        return self.fonts_action
    
    def get_translations_action(self):
        """获取翻译文件提取动作"""
        return self.translations_action 
    
    def get_videos_action(self):
        """获取视频提取动作"""
        return self.videos_action 