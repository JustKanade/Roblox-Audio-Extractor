#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主题管理器
提供主题设置、应用和切换功能
"""

import os
import json
import logging
from typing import Dict, Optional
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from qfluentwidgets import setTheme, Theme, setThemeColor

# 导入默认主题色常量
from src.config.config_manager import DEFAULT_THEME_COLOR

# 设置日志记录
logger = logging.getLogger(__name__)

# 主题样式缓存，用于优化切换性能
_theme_styles_cache: Dict[str, Optional[str]] = {"light": None, "dark": None}


def apply_theme_from_config(window, config_manager, central_log_handler=None):
    """从配置文件应用主题设置
    
    根据配置管理器中的设置立即应用主题，避免启动时的白色闪现
    
    Args:
        window: 要应用主题的窗口对象
        config_manager: 配置管理器实例
        central_log_handler: 中央日志处理器实例（可选）
    """
    try:
        # 获取主题设置
        theme_setting = config_manager.get("theme")
        
        # 更新中央日志处理器的主题设置
        if central_log_handler:
            central_log_handler.set_theme(theme_setting)
        
        # 立即应用主题，避免延迟导致的白色闪现
        _safely_apply_theme(window, theme_setting, config_manager)
        
        # 预缓存另一个主题的样式，以便后续切换更流畅
        other_theme = "light" if theme_setting == "dark" else "dark"
        _pre_cache_theme_styles(window, other_theme)
    except Exception as e:
        logger.error(f"应用主题配置时出错: {e}")


def _pre_cache_theme_styles(window, theme_setting):
    """预缓存主题样式，以优化主题切换性能
    
    Args:
        window: 窗口对象
        theme_setting: 主题设置（"dark"或"light"）
    """
    try:
        if _theme_styles_cache.get(theme_setting) is None:
            # 生成主题样式并缓存，但不应用
            main_bg = "rgb(243, 243, 243)" if theme_setting == "light" else "rgb(32, 32, 32)"
            _theme_styles_cache[theme_setting] = f"""
                FluentWindow {{
                    background-color: {main_bg};
                }}
                QWidget {{
                    background-color: transparent;
                }}
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QScrollArea > QWidget > QWidget {{
                    background-color: transparent;
                }}
            """
            logger.debug(f"预缓存 {theme_setting} 主题样式完成")
    except Exception as e:
        logger.error(f"预缓存主题样式出错: {e}")


def _safely_apply_theme(window, theme_setting, config_manager):
    """安全地应用主题设置，避免白色闪现
    
    在应用主题前立即设置背景色，处理主题应用过程中可能出现的异常
    
    Args:
        window: 要应用主题的窗口对象
        theme_setting: 主题设置（"dark"、"light"或"auto"）
        config_manager: 配置管理器实例
    """
    try:
        # 立即设置窗口背景色，防止白色闪现
        if theme_setting == "light":
            initial_bg = "rgb(243, 243, 243)"
        elif theme_setting == "dark":
            initial_bg = "rgb(32, 32, 32)"
        else:  # auto - 根据系统主题决定
            import sys
            if sys.platform == "win32":
                try:
                    import winreg
                    registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                    value, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
                    winreg.CloseKey(registry_key)
                    initial_bg = "rgb(243, 243, 243)" if value else "rgb(32, 32, 32)"
                except:
                    initial_bg = "rgb(243, 243, 243)"  # 默认浅色
            else:
                initial_bg = "rgb(243, 243, 243)"  # 非Windows系统默认浅色
        
        # 立即应用背景色
        window.setStyleSheet(f"FluentWindow {{ background-color: {initial_bg}; }}")
        
        # 预缓存两种主题的样式表用于快速切换
        _pre_cache_theme_styles(window, "dark")
        _pre_cache_theme_styles(window, "light")
        
        logger.debug(f"立即应用主题背景: {theme_setting}，背景色: {initial_bg}")
        
        # 应用主题模式，直接使用QFluentWidgets的setTheme函数
        if theme_setting == "light":
            setTheme(Theme.LIGHT, lazy=False)
        elif theme_setting == "dark":
            setTheme(Theme.DARK, lazy=False)
        else:  # auto
            setTheme(Theme.AUTO, lazy=False)
        
        # 应用主题颜色 - 使用新的qconfig系统
        try:
            # 直接从配置项获取颜色
            theme_color = config_manager.cfg.get(config_manager.cfg.themeColor)
            
            if isinstance(theme_color, QColor) and theme_color.isValid():
                # 直接应用主题色
                setThemeColor(theme_color)
                logger.debug(f"应用主题色: {theme_color.name()}")
            else:
                # 应用默认主题色
                default_color = QColor(DEFAULT_THEME_COLOR)
                setThemeColor(default_color)
                logger.debug(f"应用默认主题色: {default_color.name()}")
            
        except Exception as e:
            logger.error(f"应用主题颜色时出错: {e}")
            # 回退到默认颜色
            try:
                default_color = QColor(DEFAULT_THEME_COLOR)
                setThemeColor(default_color)
            except Exception:
                pass

        # 立即更新界面样式
        update_all_styles(window)
    except Exception as e:
        logger.error(f"安全应用主题时出错: {e}")


def apply_theme_change(window, theme_name, config_manager, central_log_handler=None, settings_log_handler=None, lang=None):
    """应用主题变更
    
    根据用户选择的主题名称更改主题设置
    
    Args:
        window: 要应用主题的窗口对象
        theme_name: 主题名称（用户界面显示的名称）
        config_manager: 配置管理器实例
        central_log_handler: 中央日志处理器实例（可选）
        settings_log_handler: 设置界面日志处理器（可选）
        lang: 语言管理器实例（可选）
        
    Returns:
        str: 应用的主题值（"dark"、"light"或"auto"）
    """
    try:
        # 确定要应用的主题值
        theme_value = None
        
        # 根据语言管理器获取主题名称对应的值
        if lang:
            # 支持完整形式（"深色主题"、"浅色主题"）
            if theme_name == lang.get("theme_dark"):
                theme_value = "dark"
            elif theme_name == lang.get("theme_light"):
                theme_value = "light"
            # 支持简短形式和翻译后的文本（向后兼容性）
            elif theme_name in ["深色", "Dark Theme"]:
                theme_value = "dark"
            elif theme_name in ["浅色", "Light Theme"]:
                theme_value = "light"
            elif theme_name in ["跟随系统设置", "Follow System Settings"]:
                theme_value = "auto"
            else:
                theme_value = "auto"
        else:
            # 如果没有语言管理器，根据名称判断
            if ("dark" in theme_name.lower() or theme_name == "深色" or 
                "Dark Theme" in theme_name):
                theme_value = "dark"
            elif ("light" in theme_name.lower() or theme_name == "浅色" or 
                  "Light Theme" in theme_name):
                theme_value = "light"
            else:
                theme_value = "auto"
                
        # 记录应用主题前的配置状态
        logger.debug(f"应用主题变更: 从 {config_manager.get('theme')} 到 {theme_value}")
        
        # 首先应用预缓存的样式（如果有）- 这样可以提前开始视觉切换
        if theme_value in ["dark", "light"] and _theme_styles_cache.get(theme_value):
            window.setStyleSheet(_theme_styles_cache[theme_value])
            logger.debug(f"预先应用缓存的 {theme_value} 主题样式")
            
        # 保存设置到配置中
        config_manager.set("theme", theme_value)
        
        # 更新中央日志处理器的主题设置
        if central_log_handler:
            central_log_handler.set_theme(theme_value)
                
        # 立即应用主题变更，不使用延迟
        _apply_theme_change(window, theme_value, theme_name, settings_log_handler, lang)
        
        return theme_value
    except Exception as e:
        logger.error(f"主题切换错误: {e}")
        # 记录主题更改错误
        if settings_log_handler:
            settings_log_handler.error(f"主题切换错误: {e}")
        return None


def _apply_theme_change(window, theme_value, theme_name, settings_log_handler=None, lang=None):
    """安全地应用主题变更
    
    处理主题变更过程中可能出现的异常
    
    Args:
        window: 要应用主题的窗口对象
        theme_value: 主题值（"dark"、"light"或"auto"）
        theme_name: 主题名称（用户界面显示的名称）
        settings_log_handler: 设置界面日志处理器（可选）
        lang: 语言管理器实例（可选）
    """
    try:
        # 开始时记录变更
        logger.debug(f"正在应用主题变更: {theme_value}")
        
        # 使用lazy=True参数显著提高切换性能
        if theme_value == "dark":
            setTheme(Theme.DARK, lazy=True)
        elif theme_value == "light":
            setTheme(Theme.LIGHT, lazy=True)
        else:
            setTheme(Theme.AUTO, lazy=True)
            
        # 使用非常短的延迟，确保QFluentWidgets内部状态已更新但又不影响动画流畅度
        QTimer.singleShot(10, lambda: update_all_styles(window))
        
        # 记录主题更改
        if settings_log_handler:
            if lang:
                settings_log_handler.success(lang.get("theme_changed", theme_name))
            else:
                settings_log_handler.success(f"主题已更改为: {theme_name}")
                
        logger.debug(f"主题变更应用完成: {theme_value}")
    except Exception as e:
        logger.error(f"应用主题变更时出错: {e}")
        if settings_log_handler:
            settings_log_handler.error(f"应用主题变更时出错: {e}")


def update_all_styles(window):
    """更新所有界面的样式以匹配当前主题
    
    Args:
        window: 主窗口实例
    """
    try:
        if not hasattr(window, "config_manager"):
            return
            
        theme = window.config_manager.get("theme")
        
        # 确定当前主题和另一个主题
        current_theme = theme  # "dark" 或 "light"
        other_theme = "light" if current_theme == "dark" else "dark"

        # 同时为两种主题准备样式表
        for theme_to_update in [current_theme, other_theme]:
            # 设置主窗口背景
            if theme_to_update == "light":
                main_bg = "rgb(243, 243, 243)"
                text_color = "rgb(0, 0, 0)"
                subtitle_color = "rgba(0, 0, 0, 0.7)"
                accent_color = "rgb(0, 120, 215)"
            else:
                main_bg = "rgb(32, 32, 32)"
                text_color = "rgb(255, 255, 255)"
                subtitle_color = "rgba(255, 255, 255, 0.8)"
                accent_color = "rgb(0, 212, 255)"

            # 缓存主题样式表
            style_sheet = f"""
                FluentWindow {{
                    background-color: {main_bg};
                }}
                QWidget {{
                    background-color: transparent;
                }}
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QScrollArea > QWidget > QWidget {{
                    background-color: transparent;
                }}
            """
            
            # 更新缓存
            _theme_styles_cache[theme_to_update] = style_sheet

        # 应用当前主题的主窗口样式
        window.setStyleSheet(_theme_styles_cache[current_theme])

        # 更新各个界面样式
        # 主页样式
        if hasattr(window, 'setHomeStyles'):
            window.setHomeStyles()

        # 提取音频界面样式
        if hasattr(window, 'extractInterface') and hasattr(window.extractInterface, 'setExtractStyles'):
            window.extractInterface.setExtractStyles()
            
        # 关于界面样式
        if hasattr(window, 'aboutInterface') and hasattr(window.aboutInterface, 'setAboutStyles'):
            window.aboutInterface.setAboutStyles()

        # 清除缓存界面样式
        if hasattr(window, 'setCacheStyles'):
            window.setCacheStyles()

        # 历史界面样式
        if hasattr(window, 'setHistoryStyles'):
            window.setHistoryStyles()

        # 记录缓存状态
        logger.debug(f"当前主题:{current_theme}，两种主题样式都已缓存")

    except Exception as e:
        logger.error(f"更新样式时出错: {e}") 