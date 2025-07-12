"""
翻译文件包，提供多语言支持
"""
from .translations import Language, get_translations
from .language_manager import LanguageManager

# 全局语言管理器实例，将在主程序中初始化
lang = None

def initialize_lang(config_manager=None):
    """初始化全局语言管理器"""
    global lang
    lang = LanguageManager(config_manager)
    return lang 