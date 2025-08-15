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

# 导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None

logger = logging.getLogger(__name__)

def get_text(key, default="", *args):
    """获取翻译文本"""
    if lang and hasattr(lang, 'get'):
        text = lang.get(key, default)
        if args:
            return text.format(*args)
        return text
    if args and default:
        return default.format(*args)
    return default


class BackgroundManager(QObject):
    """背景管理器 - 统一管理背景相关设置和样式"""
    
    backgroundChanged = pyqtSignal()
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self._background_style_cache = {}
        self._blurred_pixmap_cache = {}  # 缓存模糊后的图片
        self._current_blur_key = None  # 当前模糊图片的缓存键
        
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
        """生成背景样式表（背景图片通过paintEvent实现）
        
        Args:
            theme_mode: 主题模式 ("light" 或 "dark")
            
        Returns:
            str: 空字符串（样式通过paintEvent实现）
        """
        # 背景图片现在通过paintEvent实现，不需要CSS样式
        return ""
    
    def _get_background_hash(self) -> str:
        """获取当前背景设置的哈希值，用于缓存"""
        if not self.config_manager:
            return "default"
            
        bg_enabled = self.config_manager.get("backgroundImageEnabled", False)
        bg_path = self.config_manager.get("backgroundImagePath", "")
        bg_opacity = self.config_manager.get("backgroundOpacity", 0.8)
        
        return f"{bg_enabled}_{bg_path}_{bg_opacity}"
    
    def clear_cache(self):
        """清除背景样式缓存和模糊图片缓存"""
        self._background_style_cache.clear()
        self._blurred_pixmap_cache.clear()
        self._current_blur_key = None
        logger.debug(get_text("background_cache_cleared", "背景样式缓存和模糊图片缓存已清除"))
    
    def apply_blur_effect(self, widget: QWidget, blur_radius: int = 10):
        """为指定组件应用模糊效果（暂时不实现，因为会影响性能）
        
        Args:
            widget: 要应用模糊效果的组件  
            blur_radius: 模糊半径 (0-100)
        """
        try:
            # 暂时不实现模糊效果，因为QGraphicsBlurEffect会严重影响性能
            # 如果需要模糊效果，建议使用预处理的模糊背景图片
            logger.debug(get_text("blur_effect_not_implemented", "模糊效果设置: radius={} (暂未实现)", blur_radius))
            
        except Exception as e:
            logger.error(get_text("apply_blur_failed", "应用模糊效果失败: {}", str(e)))
            
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
        
    def get_background_blur_radius(self) -> int:
        """获取背景模糊半径"""
        if not self.config_manager:
            return 0
        return self.config_manager.get("backgroundBlurRadius", 0)
        
    def get_background_pixmap(self, window_size):
        """获取处理后的背景图片（包含缓存的模糊效果）"""
        try:
            if not self.is_background_enabled():
                return None
                
            bg_path = self.get_background_image_path()
            if not bg_path or not self.validate_image_path(bg_path):
                return None
                
            blur_radius = self.get_background_blur_radius()
            
            # 生成缓存键
            cache_key = f"{bg_path}_{window_size.width()}_{window_size.height()}_{blur_radius}"
            
            # 检查缓存
            if cache_key in self._blurred_pixmap_cache:
                return self._blurred_pixmap_cache[cache_key]
                
            # 加载原始图片
            from PyQt5.QtGui import QPixmap
            from PyQt5.QtCore import Qt
            
            pixmap = QPixmap(bg_path)
            if pixmap.isNull():
                return None
                
            # 缩放图片
            scaled_pixmap = pixmap.scaled(
                window_size, 
                Qt.KeepAspectRatioByExpanding, 
                Qt.SmoothTransformation
            )
            
            # 如果需要模糊效果
            if blur_radius > 0:
                scaled_pixmap = self._apply_efficient_blur(scaled_pixmap, blur_radius)
            
            # 缓存处理后的图片
            self._blurred_pixmap_cache[cache_key] = scaled_pixmap
            self._current_blur_key = cache_key
            
            # 清理旧缓存（保留最近的5个）
            if len(self._blurred_pixmap_cache) > 5:
                oldest_key = next(iter(self._blurred_pixmap_cache))
                del self._blurred_pixmap_cache[oldest_key]
                
            return scaled_pixmap
            
        except Exception as e:
            logger.error(get_text("get_background_pixmap_failed", "获取背景图片失败: {}", str(e)))
            return None
            
    def _apply_efficient_blur(self, pixmap, blur_radius):
        """应用高效的模糊效果（简化版高斯模糊）"""
        try:
            from PyQt5.QtGui import QPainter, QPixmap
            from PyQt5.QtCore import Qt
            
            # 为了性能，使用简化的模糊算法
            # 对于较大的模糊半径，先缩小图片再放大以提高性能
            original_size = pixmap.size()
            
            if blur_radius > 20:
                # 高模糊半径时，先缩小到1/4处理
                small_size = original_size * 0.25
                temp_pixmap = pixmap.scaled(small_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                blurred = self._simple_blur(temp_pixmap, blur_radius // 4)
                return blurred.scaled(original_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            else:
                return self._simple_blur(pixmap, blur_radius)
                
        except Exception as e:
            logger.error(get_text("apply_blur_failed", "应用模糊效果失败: {}", str(e)))
            return pixmap
            
    def _simple_blur(self, pixmap, radius):
        """简单的模糊实现（避免使用QGraphicsBlurEffect）"""
        try:
            from PyQt5.QtGui import QPainter, QPixmap
            from PyQt5.QtCore import Qt
            
            # 创建结果图片
            result = QPixmap(pixmap.size())
            result.fill(Qt.transparent)
            
            painter = QPainter(result)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 使用多次绘制来模拟模糊效果（简化版）
            opacity_step = 0.3 / max(1, radius // 3)  # 根据半径调整透明度
            offset_step = max(1, radius // 5)  # 根据半径调整偏移步长
            
            for i in range(-radius//2, radius//2 + 1, offset_step):
                for j in range(-radius//2, radius//2 + 1, offset_step):
                    if i == 0 and j == 0:
                        painter.setOpacity(1.0)  # 中心图像不透明
                    else:
                        painter.setOpacity(opacity_step)
                    painter.drawPixmap(i, j, pixmap)
                    
            painter.end()
            return result
            
        except Exception as e:
            logger.error(get_text("simple_blur_failed", "简单模糊处理失败: {}", str(e)))
            return pixmap
    
    def update_background(self):
        """更新背景设置，清除缓存并发送信号"""
        self.clear_cache()
        self.backgroundChanged.emit()
        logger.info(get_text("background_settings_updated", "背景设置已更新"))


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