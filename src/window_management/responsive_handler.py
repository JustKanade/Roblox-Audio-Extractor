#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
响应式窗口处理器
提供窗口大小调整的响应式处理功能
"""

from PyQt5.QtCore import QObject


def create_responsive_resize_handler(window, original_resize_event, adjust_layout_func):
    """创建响应式窗口大小调整处理器
    
    创建一个新的resize事件处理函数，在调用原始处理函数的同时，
    执行响应式布局调整。
    
    Args:
        window: 要处理的窗口对象
        original_resize_event: 原始的resize事件处理函数
        adjust_layout_func: 布局调整函数，接收窗口宽度参数
        
    Returns:
        新的resize事件处理函数
    """
    def responsive_resize_event(event):
        # 调用原始的调整大小事件
        if original_resize_event:
            original_resize_event(event)

        # 响应式调整
        window_width = event.size().width()
        adjust_layout_func(window_width)

    return responsive_resize_event


def apply_responsive_handler(window, adjust_layout_func):
    """应用响应式处理器到窗口
    
    将响应式处理功能应用到指定窗口，替换其原有的resizeEvent方法。
    
    Args:
        window: 要应用处理器的窗口对象
        adjust_layout_func: 布局调整函数，接收窗口宽度参数
        
    Returns:
        None
    """
    # 保存原始的resize事件处理函数
    original_resize_event = window.resizeEvent
    
    # 创建新的处理函数
    new_resize_event = create_responsive_resize_handler(
        window, 
        original_resize_event, 
        adjust_layout_func
    )
    
    # 使用猴子补丁方式替换resize事件处理函数
    # 注意：这种方式可能会导致类型检查器警告，但在运行时是有效的
    window.resizeEvent = new_resize_event 