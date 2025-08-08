#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
窗口工具函数
提供窗口置顶等窗口管理功能
"""

import sys
import logging
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

logger = logging.getLogger(__name__)

def apply_always_on_top(window, is_top):
    """应用窗口置顶设置
    
    根据参数设置窗口是否置顶显示
    使用原生 Windows API 以避免与 FluentWindow 冲突
    
    Args:
        window: 要设置的窗口对象
        is_top: 是否置顶，True为置顶，False为取消置顶
    """
    logger.info(f"窗口应用置顶设置: {is_top}")
    
    try:
        if sys.platform == 'win32':
            # 使用 Windows API 设置窗口置顶
            import ctypes
            
            # 确保窗口被显示并处理事件，使句柄有效
            window.show()
            QApplication.processEvents()
            
            # 尝试多种方法获取有效的窗口句柄
            hwnd = None
            
            # 方法1: 尝试通过窗口标题查找
            try:
                window_title = window.windowTitle()
                if window_title:
                    logger.info(f"尝试通过标题查找窗口: {window_title}")
                    hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
                    if hwnd:
                        logger.info(f"通过FindWindow获取的窗口句柄: {hwnd}")
            except Exception as e:
                logger.warning(f"通过标题查找窗口失败: {e}")
            
            # 方法2: 如果FindWindow失败，使用Qt的winId
            if not hwnd:
                try:
                    hwnd = int(window.winId())
                    logger.info(f"使用Qt winId获取的窗口句柄: {hwnd}")
                    
                    # 验证句柄是否有效
                    if not ctypes.windll.user32.IsWindow(hwnd):
                        logger.warning("Qt winId获取的句柄无效")
                        hwnd = None
                except Exception as e:
                    logger.warning(f"使用Qt winId获取句柄失败: {e}")
            
            # 如果仍然没有有效句柄，尝试等待并重试
            if not hwnd:
                logger.info("等待窗口完全初始化...")
                QApplication.processEvents()
                import time
                time.sleep(0.1)  # 等待100ms
                
                try:
                    hwnd = int(window.winId())
                    if ctypes.windll.user32.IsWindow(hwnd):
                        logger.info(f"重试后获取的有效句柄: {hwnd}")
                    else:
                        hwnd = None
                except Exception as e:
                    logger.error(f"重试获取句柄失败: {e}")
            
            if not hwnd:
                logger.error("无法获取有效的窗口句柄")
                return False
            
            # Windows API 常量
            HWND_TOPMOST = -1      # 置于所有非顶层窗口之上
            HWND_NOTOPMOST = -2    # 置于所有顶层窗口之下
            SWP_NOMOVE = 0x0002    # 保持当前位置
            SWP_NOSIZE = 0x0001    # 保持当前大小
            SWP_SHOWWINDOW = 0x0040 # 显示窗口
            
            # 组合标志 - 不改变大小和位置
            flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
            
            if is_top:
                # 设置为置顶
                logger.info("尝试设置窗口为置顶")
                result = ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
            else:
                # 取消置顶
                logger.info("尝试取消窗口置顶")
                result = ctypes.windll.user32.SetWindowPos(
                    hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, flags)
            
            logger.info(f"SetWindowPos结果: {result}")
            
            if not result:
                error_code = ctypes.windll.kernel32.GetLastError()
                logger.error(f"SetWindowPos失败，错误码: {error_code}")
                return False
                
            logger.info(f"窗口置顶设置应用成功: {is_top}")
            return True
            
        else:
            # 非 Windows 平台回退到 Qt 方法
            logger.info("非Windows平台，使用Qt方法")
            current_flags = window.windowFlags()
            if is_top:
                new_flags = current_flags | Qt.WindowStaysOnTopHint
            else:
                new_flags = current_flags & ~Qt.WindowStaysOnTopHint
            
            window.setWindowFlags(new_flags)
            window.show()
            
            logger.info(f"窗口置顶设置应用成功: {is_top}")
            return True
            
    except Exception as e:
        logger.error(f"窗口置顶操作失败: {e}")
        return False 