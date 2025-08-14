#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全状态提示管理器 - 统一管理StateToolTip对象的生命周期和安全访问
Safe State Tooltip Manager - Unified management of StateToolTip lifecycle and safe access
"""

import logging
from typing import Optional, Callable, Any
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QWidget
from qfluentwidgets import StateToolTip

logger = logging.getLogger(__name__)


class SafeStateTooltipManager:
    """安全状态提示管理器"""
    
    def __init__(self, parent: QWidget, get_text_func: Optional[Callable] = None):
        """
        初始化管理器
        
        Args:
            parent: 父组件
            get_text_func: 获取翻译文本的函数，可选
        """
        self.parent = parent
        self.get_text = get_text_func or (lambda key, default="": default)
        self.tooltip: Optional[StateToolTip] = None
        self._close_timer: Optional[QTimer] = None
        
    def create_tooltip(self, title: str, content: str) -> bool:
        """
        安全创建StateToolTip
        
        Args:
            title: 标题
            content: 内容
            
        Returns:
            bool: 创建是否成功
        """
        try:
            # 如果已存在tooltip，先安全关闭
            self.safe_close()
            
            # 创建新的tooltip
            self.tooltip = StateToolTip(
                title,
                content,
                self.parent.window() or self.parent
            )
            self.tooltip.show()
            
            logger.debug(f"成功创建StateToolTip: {title} - {content}")
            return True
            
        except Exception as e:
            logger.error(f"创建StateToolTip失败: {e}")
            self._show_user_friendly_error("tooltip_create_failed")
            return False
    
    def safe_set_content(self, content: str) -> bool:
        """
        安全设置内容
        
        Args:
            content: 新内容
            
        Returns:
            bool: 设置是否成功
        """
        if not self._is_tooltip_valid():
            logger.warning("StateToolTip对象无效，无法设置内容")
            return False
            
        try:
            self.tooltip.setContent(content)
            logger.debug(f"成功设置StateToolTip内容: {content}")
            return True
            
        except RuntimeError as e:
            logger.error(f"StateToolTip对象已被删除，无法设置内容: {e}")
            self._handle_deleted_object_error("set_content")
            return False
            
        except Exception as e:
            logger.error(f"设置StateToolTip内容失败: {e}")
            self._show_user_friendly_error("tooltip_update_failed")
            return False
    
    def safe_set_state(self, is_done: bool = False) -> bool:
        """
        安全设置状态
        
        Args:
            is_done: 是否完成
            
        Returns:
            bool: 设置是否成功
        """
        if not self._is_tooltip_valid():
            logger.warning("StateToolTip对象无效，无法设置状态")
            return False
            
        try:
            self.tooltip.setState(is_done)
            logger.debug(f"成功设置StateToolTip状态: {is_done}")
            return True
            
        except RuntimeError as e:
            logger.error(f"StateToolTip对象已被删除，无法设置状态: {e}")
            self._handle_deleted_object_error("set_state")
            return False
            
        except Exception as e:
            logger.error(f"设置StateToolTip状态失败: {e}")
            self._show_user_friendly_error("tooltip_update_failed")
            return False
    
    def safe_close(self, delay_ms: int = 0) -> bool:
        """
        安全关闭tooltip
        
        Args:
            delay_ms: 延迟关闭时间（毫秒），0表示立即关闭
            
        Returns:
            bool: 关闭操作是否成功启动
        """
        if not self._is_tooltip_valid():
            logger.debug("StateToolTip对象无效，无需关闭")
            return True
            
        try:
            # 取消之前的定时器
            self._cancel_close_timer()
            
            if delay_ms <= 0:
                # 立即关闭
                self.tooltip.close()
                self.tooltip = None
                logger.debug("立即关闭StateToolTip")
            else:
                # 延迟关闭
                self._close_timer = QTimer()
                self._close_timer.singleShot(delay_ms, self._delayed_close)
                logger.debug(f"设置延迟{delay_ms}ms关闭StateToolTip")
                
            return True
            
        except RuntimeError as e:
            logger.error(f"StateToolTip对象已被删除，关闭操作无效: {e}")
            self.tooltip = None  # 清理引用
            return True  # 对象已删除，算作"关闭成功"
            
        except Exception as e:
            logger.error(f"关闭StateToolTip失败: {e}")
            self._show_user_friendly_error("tooltip_close_failed")
            return False
    
    def update_progress_tooltip(self, content: str) -> bool:
        """
        更新进度tooltip（包含内容设置的快捷方法）
        
        Args:
            content: 进度内容
            
        Returns:
            bool: 更新是否成功
        """
        return self.safe_set_content(content)
    
    def update_completion_tooltip(self, content: str, auto_close_delay: int = 3000) -> bool:
        """
        更新完成状态tooltip（设置为完成状态并自动关闭）
        
        Args:
            content: 完成内容
            auto_close_delay: 自动关闭延迟（毫秒）
            
        Returns:
            bool: 更新是否成功
        """
        success = self.safe_set_content(content) and self.safe_set_state(True)
        if success and auto_close_delay > 0:
            self.safe_close(auto_close_delay)
        return success
    
    def update_cancel_tooltip(self, content: str, auto_close_delay: int = 2000) -> bool:
        """
        更新取消状态tooltip
        
        Args:
            content: 取消内容
            auto_close_delay: 自动关闭延迟（毫秒）
            
        Returns:
            bool: 更新是否成功
        """
        success = self.safe_set_content(content) and self.safe_set_state(True)
        if success and auto_close_delay > 0:
            self.safe_close(auto_close_delay)
        return success
    
    def _is_tooltip_valid(self) -> bool:
        """检查tooltip对象是否有效"""
        if self.tooltip is None:
            return False
            
        try:
            # 尝试访问一个简单属性来验证对象是否有效
            _ = self.tooltip.isVisible()
            return True
        except RuntimeError:
            # 对象已被Qt删除
            self.tooltip = None
            return False
        except Exception:
            # 其他错误也认为对象无效
            return False
    
    def _delayed_close(self):
        """延迟关闭的回调"""
        try:
            if self.tooltip:
                self.tooltip.close()
                self.tooltip = None
                logger.debug("延迟关闭StateToolTip完成")
        except RuntimeError:
            logger.debug("StateToolTip对象在延迟关闭前已被删除")
            self.tooltip = None
        except Exception as e:
            logger.error(f"延迟关闭StateToolTip时发生错误: {e}")
        finally:
            self._close_timer = None
    
    def _cancel_close_timer(self):
        """取消关闭定时器"""
        if self._close_timer:
            self._close_timer.stop()
            self._close_timer = None
    
    def _handle_deleted_object_error(self, operation: str):
        """处理对象已删除的错误"""
        self.tooltip = None
        logger.warning(f"StateToolTip对象在执行{operation}操作时已被删除，已清理引用")
        self._show_user_friendly_error("tooltip_object_deleted")
    
    def _show_user_friendly_error(self, error_key: str):
        """显示用户友好的错误信息"""
        try:
            from qfluentwidgets import InfoBar, InfoBarPosition
            from PyQt5.QtCore import Qt
            
            error_messages = {
                "tooltip_create_failed": self.get_text("tooltip_create_failed", "状态提示创建失败"),
                "tooltip_update_failed": self.get_text("tooltip_update_failed", "状态提示更新失败"), 
                "tooltip_close_failed": self.get_text("tooltip_close_failed", "状态提示关闭失败"),
                "tooltip_object_deleted": self.get_text("tooltip_object_deleted", "状态提示已被系统清理")
            }
            
            message = error_messages.get(error_key, self.get_text("tooltip_unknown_error", "状态提示发生未知错误"))
            
            InfoBar.warning(
                title=self.get_text("warning", "Warning"),
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.parent
            )
            
        except Exception as e:
            # 如果连InfoBar都无法显示，只记录日志
            logger.error(f"显示用户友好错误信息失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        self._cancel_close_timer()
        self.safe_close(0)
        self.tooltip = None
        logger.debug("SafeStateTooltipManager已清理")
    
    def __del__(self):
        """析构函数，确保资源清理"""
        try:
            self.cleanup()
        except Exception:
            pass 