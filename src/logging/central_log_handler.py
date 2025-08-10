#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中央日志处理系统 - 管理所有界面的日志显示
Central Log Handling System - Manages log display across all interfaces
"""

import os
import datetime
import logging as std_logging  # 明确导入标准库的logging

# 设置日志记录
std_logging.basicConfig(level=std_logging.INFO, format='%(message)s')
logger = std_logging.getLogger(__name__)

class CentralLogHandler:
    """中央日志处理系统，管理所有界面的日志显示"""

    _instance = None  # 单例实例
    _log_entries = []  # 存储所有日志条目
    _text_edits = []   # 所有要更新的TextEdit控件
    _max_entries = 200  # 最大日志条目数
    _theme = "auto"    # 默认主题
    _config_manager = None  # 配置管理器
    _log_file_path = None  # 日志文件路径

    @classmethod
    def getInstance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = CentralLogHandler()
        return cls._instance
    
    def init_with_config(self, config_manager):
        """使用配置管理器初始化日志处理器"""
        self._config_manager = config_manager
        # 设置日志文件路径
        custom_output_dir = config_manager.get("custom_output_dir", "")
        if custom_output_dir and os.path.isdir(custom_output_dir):
            # 使用自定义路径
            log_dir = os.path.join(custom_output_dir, "logs")
        else:
            # 使用默认路径
            log_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor", "logs")
        
        os.makedirs(log_dir, exist_ok=True)
        self._log_file_path = os.path.join(log_dir, f"app_log_{datetime.datetime.now().strftime('%Y%m%d')}.txt")

    def register_text_edit(self, text_edit):
        """注册TextEdit控件以接收日志更新"""
        if text_edit not in self._text_edits:
            self._text_edits.append(text_edit)
            # 初始化显示已有日志
            text_edit.clear()
            # 根据当前主题重新生成所有日志条目
            self._refresh_logs_in_text_edit(text_edit)

    def _refresh_logs_in_text_edit(self, text_edit):
        """根据当前主题刷新TextEdit中的所有日志"""
        text_edit.clear()
        for entry in self._log_entries:
            # 解析纯文本日志以提取前缀和消息
            parts = entry.split("] ", 1)
            if len(parts) == 2:
                timestamp = parts[0] + "] "
                rest = parts[1]
                
                # 检查前缀
                prefix = ""
                message = rest
                if rest.startswith("✓ "):
                    prefix = "✓ "
                    message = rest[2:]
                elif rest.startswith("⚠ "):
                    prefix = "⚠ "
                    message = rest[2:]
                elif rest.startswith("✗ "):
                    prefix = "✗ "
                    message = rest[2:]
                
                # 根据前缀和当前主题确定颜色
                if prefix == "✓ ":
                    color = "#2ECC71"  # 成功消息 - 绿色
                elif prefix == "⚠ ":
                    color = "#FF8C00"  # 警告消息 - 橙色
                elif prefix == "✗ ":
                    color = "#FF0000"  # 错误消息 - 红色
                else:
                    # 根据当前主题设置默认颜色
                    if self._theme == "light":
                        color = "black"  # 浅色模式下默认黑色
                    else:
                        color = "white"  # 深色模式下默认白色
                
                # 创建HTML格式的日志条目
                html_entry = f'<span style="color:{color}">{timestamp}{prefix}{message}</span>'
                text_edit.append(html_entry)
            else:
                # 如果无法解析，直接添加原始条目
                text_edit.append(entry)
        
        text_edit.ensureCursorVisible()

    def set_theme(self, theme):
        """设置当前主题并刷新所有日志显示"""
        # 只有当主题实际变化时才进行刷新
        if self._theme != theme:
            self._theme = theme
            # 刷新所有TextEdit控件中的日志
            for text_edit in self._text_edits:
                try:
                    self._refresh_logs_in_text_edit(text_edit)
                except Exception:
                    pass  # 忽略刷新失败的控件

    def add_log(self, message, prefix=""):
        """添加日志条目并更新所有TextEdit控件"""
        # 添加时间戳
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
        
        # 根据前缀确定消息类型和颜色
        # 根据当前主题设置默认颜色
        if self._theme == "light":
            color = "black"  # 浅色模式下默认黑色
        else:
            color = "white"  # 深色模式下默认白色
            
        # 特殊消息类型覆盖默认颜色
        if prefix == "✓ ":
            color = "#008800"  # 成功消息 - 绿色
        elif prefix == "⚠ ":
            color = "#FF8C00"  # 警告消息 - 橙色
        elif prefix == "✗ ":
            color = "#FF0000"  # 错误消息 - 红色
            
        # 创建带颜色的HTML格式日志条目
        html_entry = f'<span style="color:{color}">{timestamp}{prefix}{message}</span>'
        plain_entry = f"{timestamp}{prefix}{message}"
        
        # 添加到日志条目列表 (保存纯文本版本用于后续处理)
        self._log_entries.append(plain_entry)
        
        # 限制日志条目数量
        if len(self._log_entries) > self._max_entries:
            self._log_entries = self._log_entries[-self._max_entries:]
            
        # 更新所有TextEdit控件
        for text_edit in self._text_edits:
            try:
                text_edit.append(html_entry)
                text_edit.ensureCursorVisible()
            except Exception:
                pass  # 忽略更新失败的控件
                
        # 如果启用了日志保存，保存到文件
        self._save_log_to_file(plain_entry)

    def clear_logs(self):
        """清除所有日志"""
        self._log_entries.clear()
        for text_edit in self._text_edits:
            try:
                text_edit.clear()
            except Exception:
                pass
                
    def _save_log_to_file(self, log_entry):
        """将日志保存到文件"""
        if not self._config_manager or not self._config_manager.get("save_logs", False):
            return
            
        if not self._log_file_path:
            return
            
        try:
            with open(self._log_file_path, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry}\n")
        except Exception as e:
            # 避免递归错误，不记录保存日志时的错误
            pass
            
    def save_crash_log(self, error_info, traceback_info):
        """保存崩溃日志到文件，如果Debug模式开启"""
        # 检查Debug模式是否开启
        if not self._config_manager or not self._config_manager.get("debug_mode_enabled", True):
            return None
            
        # 使用统一的崩溃日志路径工具
        from src.utils.log_utils import get_crash_log_path
        crash_log_path = get_crash_log_path()
        
        try:
            with open(crash_log_path, 'w', encoding='utf-8') as f:
                # 写入错误信息
                f.write("Roblox Audio Extractor\n")
                f.write(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Error: {error_info}\n\n")
                f.write("Stack Trace:\n")
                f.write(f"{traceback_info}\n\n")
                
                # 写入所有日志记录
                f.write("Log Records:\n")
                for entry in self._log_entries:
                    f.write(f"{entry}\n")
                    
            return crash_log_path
        except Exception:
            return None 