#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
语言管理器
提供语言设置、应用和切换功能
"""

import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from qfluentwidgets import InfoBar, InfoBarPosition, MessageBox

# 设置日志记录
logger = logging.getLogger(__name__)


def apply_language(window, selected_language, current_language, lang, settings_log_handler=None):
    """应用语言设置
    
    根据用户选择的语言更改语言设置
    
    Args:
        window: 主窗口对象
        selected_language: 用户选择的语言名称（如"简体中文"、"English"、"跟随系统设置"或"Follow System Settings"）
        current_language: 当前语言名称
        lang: 语言管理器实例
        settings_log_handler: 设置界面日志处理器（可选）
    
    Returns:
        bool: 是否需要重启应用程序
    """
    try:
        # 检查语言是否真的改变了
        if selected_language == current_language:
            # 如果语言没有改变，只显示一个通知而不是重启确认框
            if settings_log_handler:
                settings_log_handler.info(lang.get("language_unchanged") if lang.get("language_unchanged", None) else "语言设置未改变")
            return False
            
        # 语言改变了，保存语言设置到配置文件
        english_text = lang.get("english")
        chinese_text = lang.get("simplified_chinese")
        system_text = lang.get("follow_system_language")
        
        if selected_language == english_text or selected_language == "English":
            lang.save_language_setting("en")
        elif selected_language == chinese_text or selected_language == "简体中文" or selected_language == "中文":
            lang.save_language_setting("zh")
        elif selected_language == system_text or selected_language == "跟随系统设置" or selected_language == "Follow System Settings":
            lang.save_language_setting("auto")

        # 记录更改
        if settings_log_handler:
            settings_log_handler.success(lang.get("language_saved"))

        # 显示重启确认对话框
        restart_dialog = MessageBox(
            lang.get("restart_required"),
            lang.get("language_close_message"),
            window
        )

        if restart_dialog.exec():
            # 用户选择立即关闭程序
            QApplication.quit()
            return True
        else:
            # 用户选择稍后重启
            InfoBar.info(
                title=lang.get("restart_required"),
                content=lang.get("language_saved"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=window
            )
            return False
    except Exception as e:
        logger.error(f"应用语言设置时出错: {e}")
        if settings_log_handler:
            settings_log_handler.error(f"应用语言设置时出错: {e}")
        return False


def get_language_name(lang):
    """获取当前语言名称
    
    Args:
        lang: 语言管理器实例
    
    Returns:
        str: 当前语言名称
    """
    try:
        return lang.get_language_name()
    except Exception as e:
        logger.error(f"获取语言名称时出错: {e}")
        return "English"  # 默认返回英语


def get_language_code(language_name):
    """根据语言名称获取语言代码
    
    Args:
        language_name: 语言名称（如"简体中文"、"English"、"跟随系统设置"或"Follow System Settings"）
    
    Returns:
        str: 语言代码（如"zh"、"en"或"auto"）
    """
    # 获取翻译后的语言名称（需要使用某个语言管理器实例）
    # 这里采用多种匹配方式以确保兼容性
    if (language_name == "English" or 
        language_name == "英语"):
        return "en"
    elif (language_name in ["简体中文", "中文", "Simplified Chinese"] or
          "简体中文" in language_name or "Chinese" in language_name):
        return "zh"
    elif (language_name in ["跟随系统设置", "Follow System Settings", "System Settings"] or
          "跟随系统设置" in language_name or "Follow System" in language_name):
        return "auto"
    else:
        return "en"  # 默认返回英语 