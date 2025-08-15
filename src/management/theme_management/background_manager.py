#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景管理器 - 处理应用程序背景图片、模糊效果和透明度设置
"""

import os
import logging
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QBrush
from PyQt5.QtWidgets import QWidget, QGraphicsBlurEffect

logger = logging.getLogger(__name__)


class BackgroundManager(QObject):
    """背景管理器 - 统一管理背景相关设置和样式"""
    
    backgroundChanged = pyqtSignal()
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self._background_style_cache = {}
        
    def validate_image_path(self, image_path: str) -> bool:
        """验证图片路径是否有效"""
        if not image_path:
            return False
            
        path = Path(image_path)
        if not path.exists() or not path.is_file():
            return False
            
        # 检查是否为支持的图片格式
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        return path.suffix.lower() in supported_formats
    
    def get_background_style(self, theme_mode="light") -> str:
        """生成组件透明度样式表（背景图片通过paintEvent实现）
        
        Args:
            theme_mode: 主题模式 ("light" 或 "dark")
            
        Returns:
            str: 组件透明度相关的CSS样式
        """
        if not self.config_manager:
            return ""
            
        try:
            # 检查缓存
            cache_key = f"{theme_mode}_{self._get_background_hash()}"
            if cache_key in self._background_style_cache:
                return self._background_style_cache[cache_key]
            
            style_parts = []
            
            # 获取配置
            bg_enabled = self.config_manager.get("backgroundImageEnabled", False)
            component_opacity = self.config_manager.get("componentOpacity", 0.9)
            
            # 调整组件透明度
            if bg_enabled:
                # 当启用背景图片时，调整组件透明度
                component_alpha_value = component_opacity * 0.5  # 背景图片时降低组件不透明度
                if theme_mode == "light":
                    component_bg_color = f"rgba(255, 255, 255, {component_alpha_value:.3f})"
                else:
                    component_bg_color = f"rgba(32, 32, 32, {component_alpha_value:.3f})"
                    
                style_parts.append(f"""
                    StackedWidget {{
                        background-color: {component_bg_color};
                    }}
                """)
            else:
                # 未启用背景图片时使用默认样式
                if theme_mode == "light":
                    default_bg = "rgba(255, 255, 255, 0.5)"
                else:
                    default_bg = "rgba(255, 255, 255, 0.0314)"  # 参考PyQt-Fluent-Widgets的深色主题
                    
                style_parts.append(f"""
                    StackedWidget {{
                        background-color: {default_bg};
                    }}
                """)
            
            final_style = "\n".join(style_parts)
            
            # 缓存样式
            self._background_style_cache[cache_key] = final_style
            logger.debug(f"生成组件样式: enabled={bg_enabled}, component_opacity={component_opacity}")
            
            return final_style
            
        except Exception as e:
            logger.error(f"生成组件样式失败: {e}")
            return ""
    
    def _get_background_hash(self) -> str:
        """获取当前背景设置的哈希值，用于缓存"""
        if not self.config_manager:
            return "default"
            
        bg_enabled = self.config_manager.get("backgroundImageEnabled", False)
        bg_path = self.config_manager.get("backgroundImagePath", "")
        bg_opacity = self.config_manager.get("backgroundOpacity", 0.8)
        component_opacity = self.config_manager.get("componentOpacity", 0.9)
        
        return f"{bg_enabled}_{bg_path}_{bg_opacity}_{component_opacity}"
    
    def clear_cache(self):
        """清除背景样式缓存"""
        self._background_style_cache.clear()
        logger.debug("背景样式缓存已清除")
    
    def apply_blur_effect(self, widget: QWidget, blur_radius: int = 10):
        """为指定组件应用模糊效果（暂时不实现，因为会影响性能）
        
        Args:
            widget: 要应用模糊效果的组件  
            blur_radius: 模糊半径 (0-100)
        """
        try:
            # 暂时不实现模糊效果，因为QGraphicsBlurEffect会严重影响性能
            # 如果需要模糊效果，建议使用预处理的模糊背景图片
            logger.debug(f"模糊效果设置: radius={blur_radius} (暂未实现)")
            
        except Exception as e:
            logger.error(f"应用模糊效果失败: {e}")
            
    def get_background_image_path(self) -> str:
        """获取当前背景图片路径"""
        if not self.config_manager:
            return ""
        return self.config_manager.get("backgroundImagePath", "")
        
    def is_background_enabled(self) -> bool:
        """检查背景图片是否启用"""
        if not self.config_manager:
            return False
        return self.config_manager.get("backgroundImageEnabled", False)
        
    def get_background_opacity(self) -> float:
        """获取背景透明度"""
        if not self.config_manager:
            return 0.8
        return self.config_manager.get("backgroundOpacity", 0.8)
    
    def update_background(self):
        """更新背景设置，清除缓存并发送信号"""
        self.clear_cache()
        self.backgroundChanged.emit()
        logger.info("背景设置已更新")


# 全局背景管理器实例
_background_manager = None

def get_background_manager(config_manager=None):
    """获取全局背景管理器实例"""
    global _background_manager
    if _background_manager is None:
        _background_manager = BackgroundManager(config_manager)
    elif config_manager and not _background_manager.config_manager:
        _background_manager.config_manager = config_manager
    return _background_manager 