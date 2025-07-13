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
    
    Args:
        window: 要设置的窗口对象
        is_top: 是否置顶，True为置顶，False为取消置顶
        
    Returns:
        bool: 操作是否成功
    """
    logger.info(f"窗口应用置顶设置: {is_top}")
    
    try:
        if is_top:
            # 使用平台特定的API设置窗口置顶
            if sys.platform == 'win32':
                try:
                    import ctypes
                    # 确保窗口被显示并处理事件，使句柄有效
                    window.show()
                    QApplication.processEvents()
                    
                    # 获取窗口句柄
                    hwnd = ctypes.c_int(window.winId().__int__())
                    logger.info(f"窗口句柄: {hwnd.value}")
                    
                    HWND_TOPMOST = -1
                    SWP_NOMOVE = 0x0002
                    SWP_NOSIZE = 0x0001
                    SWP_SHOWWINDOW = 0x0040
                    
                    flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
                    logger.info("尝试设置窗口为置顶")
                    result = ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
                    logger.info(f"SetWindowPos结果: {result}")
                    
                    if not result:
                        error_code = ctypes.windll.kernel32.GetLastError()
                        logger.error(f"SetWindowPos失败，错误码: {error_code}")
                        # 回退到Qt方法
                        flags = window.windowFlags()
                        window.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
                        window.show()
                        
                    return True
                except Exception as e:
                    logger.error(f"设置窗口置顶时出错: {e}")
                    # 回退到Qt方法
                    flags = window.windowFlags()
                    window.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
                    window.show()
                    return True
            else:
                # 其他平台使用Qt方法
                flags = window.windowFlags()
                window.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
                window.show()
                return True
        else:
            # 取消置顶
            logger.info("尝试取消窗口置顶")
            if sys.platform == 'win32':
                try:
                    import ctypes
                    # 确保窗口被显示并处理事件，使句柄有效
                    window.show()
                    QApplication.processEvents()
                    
                    # 获取窗口句柄
                    hwnd = ctypes.c_int(window.winId().__int__())
                    logger.info(f"窗口句柄: {hwnd.value}")
                    
                    HWND_NOTOPMOST = -2
                    SWP_NOMOVE = 0x0002
                    SWP_NOSIZE = 0x0001
                    SWP_SHOWWINDOW = 0x0040
                    
                    flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
                    result = ctypes.windll.user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, flags)
                    logger.info(f"SetWindowPos结果: {result}")
                    
                    if not result:
                        error_code = ctypes.windll.kernel32.GetLastError()
                        logger.error(f"SetWindowPos失败，错误码: {error_code}")
                        # 回退到Qt方法
                        window.setWindowFlags(window.windowFlags() & ~Qt.WindowStaysOnTopHint)
                        window.show()
                        
                    return True
                except Exception as e:
                    logger.error(f"取消窗口置顶时出错: {e}")
                    # 回退到Qt方法
                    window.setWindowFlags(window.windowFlags() & ~Qt.WindowStaysOnTopHint)
                    window.show()
                    return True
            else:
                # 恢复默认窗口设置
                window.setWindowFlags(window.windowFlags() & ~Qt.WindowStaysOnTopHint)
                window.show()
                return True
                
    except Exception as e:
        logger.error(f"窗口置顶操作失败: {e}")
        return False 