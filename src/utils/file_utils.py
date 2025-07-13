#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件和路径工具函数
File and Path Utility Functions
"""

import os
import sys


def resource_path(relative_path):
    """
    获取资源的绝对路径，适用于开发环境和PyInstaller打包环境
    Get absolute path to resource, works for dev and for PyInstaller
    
    参数:
    relative_path (str): 相对路径
    
    返回:
    str: 资源的绝对路径
    """
    try:
        # PyInstaller创建临时文件夹并存储路径在_MEIPASS中
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_roblox_default_dir():
    """
    获取Roblox默认目录路径，根据不同操作系统返回不同的路径
    Get default Roblox directory path, returns different paths based on operating system
    
    返回:
    str: Roblox默认缓存目录路径
    """
    try:
        if os.name == 'nt':  # Windows
            # 获取用户主目录
            user_profile = os.environ.get('USERPROFILE')
            if not user_profile:
                # 备用方法获取用户主目录
                import ctypes.wintypes
                CSIDL_PROFILE = 40
                buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PROFILE, 0, 0, buf)
                user_profile = buf.value
                
            # Windows默认路径：C:\Users\用户名\AppData\Local\Roblox\rbx-storage
            default_path = os.path.join(user_profile, "AppData", "Local", "Roblox", "rbx-storage")
            
        elif sys.platform == 'darwin':  # macOS
            # macOS默认路径：~/Library/Roblox/rbx-storage
            user_home = os.path.expanduser("~")
            default_path = os.path.join(user_home, "Library", "Roblox", "rbx-storage")
            
        else:  # Linux及其他系统
            # Linux没有官方客户端，但可以通过Wine运行Windows版本
            # 假设Wine默认配置下的路径
            user_home = os.path.expanduser("~")
            default_path = os.path.join(user_home, ".wine", "drive_c", "users", os.environ.get('USER', 'user'), "AppData", "Local", "Roblox", "rbx-storage")
            
        return default_path
    except Exception as e:
        # 出错时返回空字符串
        print(f"获取Roblox默认路径时出错: {e}")
        return ""


def open_directory(path):
    """
    打开指定的目录
    Open specified directory
    
    参数:
    path (str): 要打开的目录路径
    
    返回:
    bool: 是否成功打开目录
    """
    if not path or not os.path.exists(path):
        return False
        
    try:
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.Popen(['open', path])
        else:
            import subprocess
            subprocess.Popen(['xdg-open', path])
        return True
    except Exception as e:
        print(f"打开目录时出错: {e}")
        return False 