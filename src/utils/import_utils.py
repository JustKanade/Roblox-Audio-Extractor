#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
延迟导入工具模块
Delayed Import Utility Module

此模块提供延迟导入功能，可以在需要时才导入库，减少启动时间和内存占用。
This module provides delayed import functionality, importing libraries only when needed,
reducing startup time and memory usage.
"""

import importlib
import sys
from typing import Dict, Any, Optional, List, Callable

# 全局变量跟踪导入状态
_LIBS_IMPORTED = False

# 导入的模块字典
_imported_modules = {}

def import_libs() -> Dict[str, Any]:
    """
    按需导入常用库，减少启动时间和内存占用
    Import commonly used libraries on demand, reducing startup time and memory usage
    
    Returns:
        Dict[str, Any]: 包含导入模块的字典 / Dictionary containing imported modules
    """
    global _LIBS_IMPORTED, _imported_modules
    
    if _LIBS_IMPORTED:
        return _imported_modules
    
    # 导入标准库
    modules_to_import = {
        'gzip': 'gzip',
        'shutil': 'shutil',
        'random': 'random',
        'string': 'string',
        'hashlib': 'hashlib',
        'subprocess': 'subprocess',
    }
    
    # 尝试导入每个模块
    for module_name, import_path in modules_to_import.items():
        try:
            # 普通模块导入
            _imported_modules[module_name] = importlib.import_module(import_path)
        except ImportError:
            # 如果导入失败，设置为None
            _imported_modules[module_name] = None
            print(f"警告: 无法导入模块 {module_name}")
    
    # 特殊处理: 尝试导入concurrent.futures和ThreadPoolExecutor
    try:
        import concurrent.futures
        _imported_modules['concurrent.futures'] = concurrent.futures
        _imported_modules['ThreadPoolExecutor'] = concurrent.futures.ThreadPoolExecutor
    except ImportError:
        _imported_modules['concurrent.futures'] = None
        _imported_modules['ThreadPoolExecutor'] = None
        print("警告: 无法导入模块 concurrent.futures")
    
    _LIBS_IMPORTED = True
    return _imported_modules

def get_module(module_name: str) -> Any:
    """
    获取指定的模块，如果尚未导入则先导入
    Get the specified module, importing it first if not already imported
    
    Args:
        module_name (str): 模块名称 / Module name
        
    Returns:
        Any: 导入的模块 / Imported module
    """
    if not _LIBS_IMPORTED:
        import_libs()
    
    return _imported_modules.get(module_name)

def check_dependencies(dependencies: List[str]) -> Dict[str, bool]:
    """
    检查指定的依赖项是否可用
    Check if specified dependencies are available
    
    Args:
        dependencies (List[str]): 要检查的依赖项列表 / List of dependencies to check
        
    Returns:
        Dict[str, bool]: 依赖项及其可用状态的字典 / Dictionary of dependencies and their availability status
    """
    results = {}
    
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            results[dep] = True
        except ImportError:
            results[dep] = False
    
    return results

def is_dependency_available(dependency: str) -> bool:
    """
    检查单个依赖项是否可用
    Check if a single dependency is available
    
    Args:
        dependency (str): 要检查的依赖项 / Dependency to check
        
    Returns:
        bool: 依赖项是否可用 / Whether the dependency is available
    """
    try:
        importlib.import_module(dependency)
        return True
    except ImportError:
        return False 