"""
语言管理器，负责处理多语言翻译和切换
"""
import os
import locale
from functools import lru_cache

from .translations import Language, get_translations


class LanguageManager:
    """语言管理器，处理翻译和语言切换"""

    def __init__(self, config_manager=None):
        """初始化语言管理器，设置支持的语言和翻译"""
        self.ENGLISH = Language.ENGLISH
        self.CHINESE = Language.CHINESE
        self.config_manager = config_manager

        # 加载翻译字典
        self.translations = get_translations()

        # 设置当前语言
        if config_manager:
            # 默认使用"auto"（跟随系统设置）
            lang_setting = config_manager.get("language", "auto")
            if lang_setting == "en":
                self.current_language = self.ENGLISH
            elif lang_setting == "zh":
                self.current_language = self.CHINESE
            else:  # 对于"auto"或任何其他值，使用系统语言
                self.current_language = self._detect_system_language()
                # 如果配置中不是"auto"，将其更新为"auto"
                if lang_setting != "auto":
                    config_manager.set("language", "auto")
                    config_manager.save_config()
        else:
            self.current_language = self._detect_system_language()

        self._cache = {}  # 添加缓存以提高性能

    @lru_cache(maxsize=128)
    def _detect_system_language(self) -> Language:
        """检测系统语言并返回相应的语言枚举"""
        try:
            # 尝试获取系统语言设置
            system_lang = locale.getdefaultlocale()[0]
            if system_lang:
                system_lang = system_lang.lower()
                # 检查是否为中文语言区域
                if any(lang_code in system_lang for lang_code in ['zh_', 'cn', 'tw', 'hk']):
                    return self.CHINESE
            
            # 尝试使用环境变量
            env_lang = os.environ.get('LANG', '').lower()
            if any(lang_code in env_lang for lang_code in ['zh_', 'cn', 'tw', 'hk']):
                return self.CHINESE
                
            return self.ENGLISH
        except Exception as e:
            # 出现异常时默认返回英语
            print(f"语言检测出错：{e}")
            return self.ENGLISH

    def get(self, key: str, *args) -> str:
        """获取指定键的翻译并应用格式化参数"""
        # 检查缓存
        cache_key = (key, self.current_language, args)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 如果键不存在，返回键本身
        if key not in self.translations:
            return key

        translations = self.translations[key]
        if self.current_language not in translations:
            # 回退到英语
            if self.ENGLISH in translations:
                message = translations[self.ENGLISH]
            else:
                # 使用任何可用的翻译
                message = next(iter(translations.values()))
        else:
            message = translations[self.current_language]

        # 应用格式化参数
        if args:
            try:
                message = message.format(*args)
            except:
                pass

        # 更新缓存
        if len(self._cache) > 1000:  # 避免缓存无限增长
            self._cache.clear()
        self._cache[cache_key] = message
        return message

    def get_language_name(self) -> str:
        """获取当前语言的名称"""
        if self.config_manager:
            lang_setting = self.config_manager.get("language", "auto")
            if lang_setting == "auto":
                # 根据当前语言环境返回对应的翻译
                if self.current_language == self.CHINESE:
                    return "跟随系统设置"
                else:
                    return "Follow System Settings"
        
        return "简体中文" if self.current_language == self.CHINESE else "English"

    def save_language_setting(self, language_code: str):
        """保存语言设置到配置文件"""
        if self.config_manager:
            self.config_manager.set("language", language_code) 