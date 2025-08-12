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
    获取资源的绝对路径，适用于开发环境、PyInstaller和Nuitka打包环境
    Get absolute path to resource, works for dev, PyInstaller and Nuitka
    
    参数:
    relative_path (str): 相对路径
    
    返回:
    str: 资源的绝对路径
    """
    try:
        # PyInstaller创建临时文件夹并存储路径在_MEIPASS中
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        return os.path.join(base_path, relative_path)
    except AttributeError:
        # Nuitka编译时的处理方式
        # Handle Nuitka compiled applications
        if hasattr(sys, 'frozen') and hasattr(sys, 'executable'):
            # Nuitka将资源文件放在可执行文件同级目录
            # Nuitka places resource files alongside the executable
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境
            # Development environment
            base_path = os.path.abspath(".")
        
        resource_file = os.path.join(base_path, relative_path)
        
        # 如果在可执行文件目录找不到资源，尝试相对于脚本目录查找
        # If resource not found near executable, try relative to script directory
        if not os.path.exists(resource_file):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # 回到项目根目录（从 src/utils 回到根目录）
            project_root = os.path.dirname(os.path.dirname(script_dir))
            resource_file = os.path.join(project_root, relative_path)
        
        return resource_file


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