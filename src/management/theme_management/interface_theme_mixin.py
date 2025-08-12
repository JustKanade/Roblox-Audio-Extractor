#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
界面主题混合类
提供统一的主题样式管理功能，消除重复代码
"""

from typing import Dict


class InterfaceThemeMixin:
    """界面主题混合类
    
    为界面提供统一的主题样式管理功能
    """
    
    # 主题颜色常量
    LIGHT_THEME_COLORS = {
        'background': 'transparent',
        'text': 'rgb(0, 0, 0)',
        'subtitle': 'rgba(0, 0, 0, 0.7)',
        'accent': 'rgb(0, 120, 215)',
        'border': 'rgba(0, 0, 0, 0.1)'
    }
    
    DARK_THEME_COLORS = {
        'background': 'transparent', 
        'text': 'rgb(255, 255, 255)',
        'subtitle': 'rgba(255, 255, 255, 0.8)',
        'accent': 'rgb(0, 212, 255)',
        'border': 'rgba(255, 255, 255, 0.1)'
    }
    
    def get_current_theme(self) -> str:
        """获取当前主题设置
        
        Returns:
            str: 当前主题 ('light', 'dark', 'auto')
        """
        if hasattr(self, 'config_manager') and self.config_manager:
            return self.config_manager.get("theme", "dark")
        return "dark"
    
    def get_theme_colors(self, theme: str = None) -> Dict[str, str]:
        """获取指定主题的颜色配置
        
        Args:
            theme: 主题名称，如果为None则使用当前主题
            
        Returns:
            Dict[str, str]: 主题颜色配置字典
        """
        if theme is None:
            theme = self.get_current_theme()
            
        # 处理auto主题
        if theme == "auto":
            # 这里可以根据系统主题自动判断，现在先默认为dark
            theme = "dark"
            
        return self.LIGHT_THEME_COLORS if theme == "light" else self.DARK_THEME_COLORS
    
    def get_common_interface_styles(self) -> str:
        """获取通用界面样式
        
        Returns:
            str: 通用的界面样式表字符串
        """
        colors = self.get_theme_colors()
        
        return f"""
            QWidget {{
                background-color: {colors['background']};
            }}
            QScrollArea {{
                background-color: {colors['background']};
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {colors['background']};
            }}
        """
    
    def get_text_styles(self) -> Dict[str, str]:
        """获取文本相关的样式配置
        
        Returns:
            Dict[str, str]: 包含各种文本样式的字典
        """
        colors = self.get_theme_colors()
        
        return {
            'title': f"""
                color: {colors['text']};
                font-size: 32px;
                font-weight: bold;
            """,
            'subtitle': f"""
                color: {colors['text']};
                font-size: 28px;
                font-weight: bold;
                margin-bottom: 3px;
            """,
            'version': f"""
                color: {colors['accent']};
                font-size: 18px;
                font-weight: 600;
            """,
            'body': f"""
                color: {colors['text']};
            """,
            'log_text': f"""
                TextEdit {{
                    font-family: Consolas, Courier, monospace;
                    color: {colors['text']};
                    background-color: {colors['background']};
                    border: 1px solid {colors['border']};
                    border-radius: 6px;
                }}
            """
        }
    
    def get_card_styles(self) -> str:
        """获取卡片组件的样式
        
        Returns:
            str: 卡片样式表字符串
        """
        colors = self.get_theme_colors()
        
        return f"""
            CardWidget {{
                border-radius: 10px;
                background-color: {colors['background']};
            }}
        """
    
    def setInterfaceStyles(self):
        """设置界面样式 - 基础实现
        
        子类可以重写此方法来应用具体的样式
        """
        # 应用通用样式
        common_styles = self.get_common_interface_styles()
        card_styles = self.get_card_styles()
        
        # 合并样式
        full_styles = common_styles + card_styles
        
        # 应用到当前widget
        if hasattr(self, 'setStyleSheet'):
            self.setStyleSheet(full_styles) 