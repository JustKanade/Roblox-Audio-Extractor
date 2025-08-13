#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义图标枚举类
Custom Icon Enumeration Class

模仿PyQt Fluent Widget gallery的自定义图标系统，
提供主题自适应的自定义图标支持。
"""

import os
from enum import Enum
from qfluentwidgets import FluentIconBase, getIconColor, Theme


def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    import sys
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller打包后的路径
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境路径
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), relative_path)


class CustomIcon(FluentIconBase, Enum):
    """自定义图标枚举类
    
    继承FluentIconBase，提供主题自适应的自定义图标。
    每个图标需要提供黑色和白色两个版本，以支持明暗主题切换。
    
    使用方式：
        from src.common.custom_icon import CustomIcon
        
        # 在组件中使用
        icon_widget = IconWidget(CustomIcon.PRICE)
        
        # 在按钮中使用
        button = PushButton(CustomIcon.PRICE, "价格标签")
    """
    
    PRICE = "Price"
    
    def path(self, theme=Theme.AUTO):
        """获取图标文件路径
        
        Args:
            theme: 主题类型 (Theme.AUTO, Theme.LIGHT, Theme.DARK)
            
        Returns:
            str: 图标文件的绝对路径
        """
        # 获取当前主题对应的颜色后缀
        color = getIconColor(theme)
        
        # 构建图标文件路径
        icon_filename = f"{self.value}_{color}.svg"
        icon_path = resource_path(os.path.join("res", "icons", "custom", icon_filename))
        
        return icon_path 