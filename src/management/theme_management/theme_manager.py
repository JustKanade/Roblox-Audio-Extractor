#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主题管理器
提供主题设置、应用和切换功能
"""

import os
import json
import logging
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from qfluentwidgets import setTheme, Theme, setThemeColor

# 设置日志记录
logger = logging.getLogger(__name__)


def apply_theme_from_config(window, config_manager, central_log_handler=None):
    """从配置文件应用主题设置
    
    根据配置管理器中的设置应用主题
    
    Args:
        window: 要应用主题的窗口对象
        config_manager: 配置管理器实例
        central_log_handler: 中央日志处理器实例（可选）
    """
    try:
        # 获取主题设置
        theme_setting = config_manager.get("theme", "dark")
        
        # 更新中央日志处理器的主题设置
        if central_log_handler:
            central_log_handler.set_theme(theme_setting)
        
        # 使用延迟调用来应用主题，避免在字典迭代过程中修改字典
        QTimer.singleShot(10, lambda: _safely_apply_theme(window, theme_setting, config_manager))
    except Exception as e:
        logger.error(f"应用主题配置时出错: {e}")


def _safely_apply_theme(window, theme_setting, config_manager):
    """安全地应用主题设置
    
    处理主题应用过程中可能出现的异常
    
    Args:
        window: 要应用主题的窗口对象
        theme_setting: 主题设置（"dark"、"light"或"auto"）
        config_manager: 配置管理器实例
    """
    try:
        # 应用主题模式
        if theme_setting == "light":
            setTheme(Theme.LIGHT)
        elif theme_setting == "dark":
            setTheme(Theme.DARK)
        else:  # auto
            setTheme(Theme.AUTO)
        
        # 应用主题颜色
        try:
            # 使用配置管理器中定义的QFluentWidgets配置文件路径
            qfluent_config_file = config_manager.qfluent_config_file
            if os.path.exists(qfluent_config_file):
                with open(qfluent_config_file, 'r', encoding='utf-8') as f:
                    qfluent_config = json.load(f)
                
                # 从QFluentWidgets配置中获取主题色
                if "QFluentWidgets" in qfluent_config and "ThemeColor" in qfluent_config["QFluentWidgets"]:
                    theme_color = qfluent_config["QFluentWidgets"]["ThemeColor"]
                    setThemeColor(QColor(theme_color))
                else:
                    # 如果配置文件中没有主题色，则应用默认颜色
                    setThemeColor(QColor("#ff0078d4"))  # 默认蓝色
            else:
                # 配置文件不存在，应用默认颜色
                setThemeColor(QColor("#ff0078d4"))  # 默认蓝色
                
            # 打印调试信息
            print(f"应用主题色，配置文件路径: {qfluent_config_file}")
            if os.path.exists(qfluent_config_file):
                print(f"配置文件内容: {qfluent_config}")
            
        except Exception as e:
            logger.error(f"应用主题颜色时出错: {e}")
            # 回退到默认颜色
            try:
                setThemeColor(QColor("#ff0078d4"))
            except:
                pass

        # 确保UI已初始化后再更新样式
        QTimer.singleShot(100, lambda: update_all_styles(window))
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
        # 保存主题设置到配置文件
        theme_value = None
        
        # 根据语言管理器获取主题名称对应的值
        if lang:
            if theme_name == lang.get("theme_dark"):
                theme_value = "dark"
            elif theme_name == lang.get("theme_light"):
                theme_value = "light"
            else:
                theme_value = "auto"
        else:
            # 如果没有语言管理器，根据名称判断
            if "dark" in theme_name.lower():
                theme_value = "dark"
            elif "light" in theme_name.lower():
                theme_value = "light"
            else:
                theme_value = "auto"
        
        # 保存设置
        config_manager.set("theme", theme_value)
        
        # 更新中央日志处理器的主题设置
        if central_log_handler:
            central_log_handler.set_theme(theme_value)
                
        # 使用延迟调用来应用主题，避免在字典迭代过程中修改字典
        QTimer.singleShot(10, lambda: _apply_theme_change(window, theme_value, theme_name, settings_log_handler, lang))
        
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
        # 应用主题
        if theme_value == "dark":
            setTheme(Theme.DARK)
        elif theme_value == "light":
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.AUTO)
            
        # 重新应用所有界面样式
        update_all_styles(window)
        
        # 记录主题更改
        if settings_log_handler:
            if lang:
                settings_log_handler.success(lang.get("theme_changed", theme_name))
            else:
                settings_log_handler.success(f"主题已更改为: {theme_name}")
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
            
        theme = window.config_manager.get("theme", "dark")

        # 设置主窗口背景
        if theme == "light":
            main_bg = "rgb(243, 243, 243)"
            text_color = "rgb(0, 0, 0)"
            subtitle_color = "rgba(0, 0, 0, 0.7)"
            accent_color = "rgb(0, 120, 215)"
        else:
            main_bg = "rgb(32, 32, 32)"
            text_color = "rgb(255, 255, 255)"
            subtitle_color = "rgba(255, 255, 255, 0.8)"
            accent_color = "rgb(0, 212, 255)"

        # 应用主窗口样式
        window.setStyleSheet(f"""
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
        """)

        # 更新各个界面样式
        # 主页样式
        if hasattr(window, 'setHomeStyles'):
            window.setHomeStyles()

        # 提取音频界面样式
        if hasattr(window, 'setExtractStyles'):
            window.setExtractStyles()

        # 清除缓存界面样式
        if hasattr(window, 'setCacheStyles'):
            window.setCacheStyles()

        # 历史界面样式
        if hasattr(window, 'setHistoryStyles'):
            window.setHistoryStyles()

        # 关于界面样式
        if hasattr(window, 'setAboutStyles'):
            window.setAboutStyles()

    except Exception as e:
        logger.error(f"更新样式时出错: {e}") 