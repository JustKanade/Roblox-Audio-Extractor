#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一路径管理器
处理所有路径相关的逻辑，包括Roblox默认路径获取、全局输入路径管理等
"""

import os
import sys
import logging
from PyQt5.QtCore import QObject, pyqtSignal
from typing import Optional

logger = logging.getLogger(__name__)


class PathManager(QObject):
    """统一路径管理器"""
    
    # 路径变更信号
    globalInputPathChanged = pyqtSignal(str)  # 全局输入路径变更
    
    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self._cached_roblox_path = None
        
    def get_roblox_default_dir(self, force_refresh: bool = False) -> str:
        """
        获取Roblox默认目录路径，支持不同用户名
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            str: Roblox默认缓存目录路径
        """
        if self._cached_roblox_path and not force_refresh:
            return self._cached_roblox_path
            
        try:
            if os.name == 'nt':  # Windows
                default_path = self._get_windows_roblox_path()
            elif sys.platform == 'darwin':  # macOS
                default_path = self._get_macos_roblox_path()
            else:  # Linux及其他系统
                default_path = self._get_linux_roblox_path()
                
            # 缓存结果
            self._cached_roblox_path = default_path
            logger.debug(f"获取到Roblox默认路径: {default_path}")
            return default_path
            
        except Exception as e:
            logger.error(f"获取Roblox默认路径时出错: {e}")
            return ""
    
    def _get_windows_roblox_path(self) -> str:
        """获取Windows系统的Roblox路径"""
        # 方法1：使用USERPROFILE环境变量
        user_profile = os.environ.get('USERPROFILE')
        if user_profile:
            path = os.path.join(user_profile, "AppData", "Local", "Roblox", "rbx-storage")
            if os.path.exists(path):
                return path
        
        # 方法2：使用LOCALAPPDATA环境变量
        local_appdata = os.environ.get('LOCALAPPDATA')
        if local_appdata:
            path = os.path.join(local_appdata, "Roblox", "rbx-storage")
            if os.path.exists(path):
                return path
        
        # 方法3：使用USERNAME环境变量构建路径
        username = os.environ.get('USERNAME')
        if username:
            path = os.path.join("C:", "Users", username, "AppData", "Local", "Roblox", "rbx-storage")
            if os.path.exists(path):
                return path
        
        # 方法4：使用Windows API获取用户配置文件路径
        try:
            import ctypes.wintypes
            CSIDL_PROFILE = 40
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PROFILE, 0, 0, buf)
            user_profile = buf.value
            if user_profile:
                path = os.path.join(user_profile, "AppData", "Local", "Roblox", "rbx-storage")
                if os.path.exists(path):
                    return path
        except Exception as e:
            logger.debug(f"Windows API获取路径失败: {e}")
        
        # 方法5：遍历所有可能的用户目录
        users_dir = "C:\\Users"
        if os.path.exists(users_dir):
            for user_folder in os.listdir(users_dir):
                if user_folder in ['Public', 'Default', 'All Users']:
                    continue
                path = os.path.join(users_dir, user_folder, "AppData", "Local", "Roblox", "rbx-storage")
                if os.path.exists(path):
                    logger.info(f"找到Roblox路径: {path} (用户: {user_folder})")
                    return path
        
        # 默认路径（即使不存在也返回，用于创建）
        fallback_username = username or "Administrator"
        return os.path.join("C:", "Users", fallback_username, "AppData", "Local", "Roblox", "rbx-storage")
    
    def _get_macos_roblox_path(self) -> str:
        """获取macOS系统的Roblox路径"""
        # 方法1：使用HOME环境变量
        user_home = os.environ.get('HOME')
        if user_home:
            path = os.path.join(user_home, "Library", "Roblox", "rbx-storage")
            if os.path.exists(path):
                return path
        
        # 方法2：使用expanduser
        user_home = os.path.expanduser("~")
        path = os.path.join(user_home, "Library", "Roblox", "rbx-storage")
        return path
    
    def _get_linux_roblox_path(self) -> str:
        """获取Linux系统的Roblox路径（通过Wine）"""
        # 方法1：检查USER环境变量
        username = os.environ.get('USER', 'user')
        user_home = os.path.expanduser("~")
        
        # Wine默认配置路径
        wine_path = os.path.join(user_home, ".wine", "drive_c", "users", username, "AppData", "Local", "Roblox", "rbx-storage")
        if os.path.exists(wine_path):
            return wine_path
        
        # PlayOnLinux路径
        playonlinux_path = os.path.join(user_home, ".PlayOnLinux", "wineprefix", "Roblox", "drive_c", "users", username, "AppData", "Local", "Roblox", "rbx-storage")
        if os.path.exists(playonlinux_path):
            return playonlinux_path
        
        # Lutris路径
        lutris_path = os.path.join(user_home, "Games", "roblox", "drive_c", "users", username, "AppData", "Local", "Roblox", "rbx-storage")
        if os.path.exists(lutris_path):
            return lutris_path
        
        # 默认Wine路径
        return wine_path
    
    def get_global_input_path(self) -> str:
        """
        获取全局输入路径，如果未设置则返回Roblox默认路径
        
        Returns:
            str: 全局输入路径
        """
        if not self.config_manager:
            return self.get_roblox_default_dir()
        
        global_path = self.config_manager.get("global_input_path", "")
        
        # 如果全局路径为空，使用Roblox默认路径
        if not global_path:
            default_path = self.get_roblox_default_dir()
            # 自动设置并保存
            if default_path:
                self.set_global_input_path(default_path, save=True)
                return default_path
        
        return global_path
    
    def set_global_input_path(self, path: str, save: bool = True) -> bool:
        """
        设置全局输入路径
        
        Args:
            path: 要设置的路径
            save: 是否立即保存配置
            
        Returns:
            bool: 设置是否成功
        """
        if not self.config_manager:
            logger.error("配置管理器未初始化")
            return False
        
        try:
            # 标准化路径
            normalized_path = os.path.normpath(path) if path else ""
            
            # 设置配置
            self.config_manager.set("global_input_path", normalized_path)
            
            # 保存配置
            if save:
                self.config_manager.save_config()
            
            # 发出信号
            self.globalInputPathChanged.emit(normalized_path)
            
            logger.info(f"全局输入路径已更新: {normalized_path}")
            return True
            
        except Exception as e:
            logger.error(f"设置全局输入路径失败: {e}")
            return False
    
    def restore_default_path(self, save: bool = True) -> str:
        """
        恢复默认Roblox路径
        
        Args:
            save: 是否立即保存配置
            
        Returns:
            str: 恢复的默认路径
        """
        default_path = self.get_roblox_default_dir(force_refresh=True)
        if default_path:
            self.set_global_input_path(default_path, save=save)
        return default_path
    
    def is_path_valid(self, path: str) -> bool:
        """
        检查路径是否有效
        
        Args:
            path: 要检查的路径
            
        Returns:
            bool: 路径是否有效
        """
        if not path:
            return False
        
        try:
            return os.path.exists(path) and os.path.isdir(path)
        except Exception:
            return False
    
    def ensure_path_exists(self, path: str) -> bool:
        """
        确保路径存在，如果不存在则尝试创建
        
        Args:
            path: 要确保存在的路径
            
        Returns:
            bool: 路径是否存在或创建成功
        """
        if not path:
            return False
        
        try:
            if os.path.exists(path):
                return os.path.isdir(path)
            
            # 尝试创建目录
            os.makedirs(path, exist_ok=True)
            return os.path.exists(path)
            
        except Exception as e:
            logger.error(f"创建路径失败 {path}: {e}")
            return False
    
    def get_effective_input_path(self) -> str:
        """
        获取有效的输入路径，优先使用全局设置，fallback到默认路径
        
        Returns:
            str: 有效的输入路径
        """
        # 先尝试全局路径
        global_path = self.get_global_input_path()
        if global_path and self.is_path_valid(global_path):
            return global_path
        
        # 如果全局路径无效，尝试默认路径
        default_path = self.get_roblox_default_dir()
        if default_path and self.is_path_valid(default_path):
            return default_path
        
        # 如果都无效，返回全局路径（可能需要创建）
        return global_path or default_path
    
    def get_all_possible_roblox_paths(self) -> list:
        """
        获取所有可能的Roblox路径（用于调试和路径选择）
        
        Returns:
            list: 所有可能的路径列表
        """
        paths = []
        
        try:
            if os.name == 'nt':  # Windows
                # 当前用户路径
                user_profile = os.environ.get('USERPROFILE')
                if user_profile:
                    paths.append(os.path.join(user_profile, "AppData", "Local", "Roblox", "rbx-storage"))
                
                # 遍历所有用户
                users_dir = "C:\\Users"
                if os.path.exists(users_dir):
                    for user_folder in os.listdir(users_dir):
                        if user_folder not in ['Public', 'Default', 'All Users']:
                            path = os.path.join(users_dir, user_folder, "AppData", "Local", "Roblox", "rbx-storage")
                            if path not in paths:
                                paths.append(path)
            
            elif sys.platform == 'darwin':  # macOS
                user_home = os.path.expanduser("~")
                paths.append(os.path.join(user_home, "Library", "Roblox", "rbx-storage"))
            
            else:  # Linux
                user_home = os.path.expanduser("~")
                username = os.environ.get('USER', 'user')
                
                # Wine路径
                paths.append(os.path.join(user_home, ".wine", "drive_c", "users", username, "AppData", "Local", "Roblox", "rbx-storage"))
                # PlayOnLinux路径
                paths.append(os.path.join(user_home, ".PlayOnLinux", "wineprefix", "Roblox", "drive_c", "users", username, "AppData", "Local", "Roblox", "rbx-storage"))
                # Lutris路径
                paths.append(os.path.join(user_home, "Games", "roblox", "drive_c", "users", username, "AppData", "Local", "Roblox", "rbx-storage"))
        
        except Exception as e:
            logger.error(f"获取所有可能路径时出错: {e}")
        
        # 去重并过滤存在的路径
        unique_paths = []
        for path in paths:
            if path not in unique_paths:
                unique_paths.append(path)
        
        return unique_paths 