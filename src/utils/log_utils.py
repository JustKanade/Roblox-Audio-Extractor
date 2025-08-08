#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具函数和类
Logging Utility Functions and Classes
"""

import logging
from typing import Optional

# 尝试导入中央日志处理系统
try:
    from src.logging.central_log_handler import CentralLogHandler
except ImportError:
    CentralLogHandler = None
    print("无法导入CentralLogHandler，将使用内置日志系统")


class LogHandler:
    """
    日志处理类，用于记录消息到PyQt的TextEdit控件
    Log Handler Class, used to record messages to PyQt TextEdit widget
    """

    def __init__(self, text_edit):
        """
        初始化日志处理器
        Initialize log handler
        
        参数:
        text_edit: TextEdit控件，用于显示日志
        """
        self.text_edit = text_edit
        # 注册到中央日志系统
        if CentralLogHandler is not None:
            CentralLogHandler.getInstance().register_text_edit(text_edit)

    def info(self, message: str):
        """
        记录信息消息
        Record information message
        
        参数:
        message: 要记录的消息
        """
        if CentralLogHandler is not None:
            CentralLogHandler.getInstance().add_log(message)
        else:
            self._fallback_log(message)

    def success(self, message: str):
        """
        记录成功消息
        Record success message
        
        参数:
        message: 要记录的消息
        """
        if CentralLogHandler is not None:
            CentralLogHandler.getInstance().add_log(message, "✓ ")
        else:
            self._fallback_log(f"✓ {message}")

    def warning(self, message: str):
        """
        记录警告消息
        Record warning message
        
        参数:
        message: 要记录的消息
        """
        if CentralLogHandler is not None:
            CentralLogHandler.getInstance().add_log(message, "⚠ ")
        else:
            self._fallback_log(f"⚠ {message}")

    def error(self, message: str):
        """
        记录错误消息
        Record error message
        
        参数:
        message: 要记录的消息
        """
        if CentralLogHandler is not None:
            CentralLogHandler.getInstance().add_log(message, "✗ ")
        else:
            self._fallback_log(f"✗ {message}")
            
    def _fallback_log(self, message: str):
        """
        当中央日志处理器不可用时的后备日志方法
        Fallback logging method when central log handler is not available
        
        参数:
        message: 要记录的消息
        """
        if hasattr(self.text_edit, 'append'):
            self.text_edit.append(message)
        logging.info(message)


def setup_basic_logging():
    """
    设置基本的日志配置
    Setup basic logging configuration
    """
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def save_log_to_file(log_content: str, filename: Optional[str] = None) -> str:
    """
    将日志内容保存到文件
    Save log content to file
    
    参数:
    log_content: 日志内容
    filename: 文件名，如果为None则使用时间戳生成
    
    返回:
    str: 保存的文件路径
    """
    import os
    import datetime
    
    if filename is None:
        # 使用当前时间创建文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"log_{timestamp}.txt"
    
    # 确保日志目录存在
    log_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # 完整的文件路径
    filepath = os.path.join(log_dir, filename)
    
    # 保存日志内容
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(log_content)
    
    return filepath


def get_crash_log_dir() -> str:
    """
    获取崩溃日志目录路径
    Get crash log directory path
    
    返回:
    str: 崩溃日志目录的完整路径
    """
    import os
    
    # 强制使用用户目录，不受自定义输出目录影响
    crash_log_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor", "logs", "crash_logs")
    
    # 确保目录存在
    os.makedirs(crash_log_dir, exist_ok=True)
    
    return crash_log_dir


def get_crash_log_path(timestamp: Optional[str] = None) -> str:
    """
    获取崩溃日志文件的完整路径
    Get complete path for crash log file
    
    参数:
    timestamp: 时间戳，如果为None则使用当前时间生成
    
    返回:
    str: 崩溃日志文件的完整路径
    """
    import os
    import datetime
    
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    crash_log_dir = get_crash_log_dir()
    return os.path.join(crash_log_dir, f"crash_log_{timestamp}.txt") 