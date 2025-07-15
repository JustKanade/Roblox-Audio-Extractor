#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件管理器 - 处理应用程序配置的加载、保存和访问
"""

import os
import json
import logging
import multiprocessing

# 设置日志记录
logger = logging.getLogger(__name__)

class ConfigManager:
    """配置文件管理器"""

    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".roblox_audio_extractor")
        self.config_file = os.path.join(self.config_dir, "config.json")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # PyQt-Fluent-Widgets配置文件路径
        self.qfluent_config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config")
        self.qfluent_config_file = os.path.join(self.qfluent_config_dir, "config.json")
        os.makedirs(self.qfluent_config_dir, exist_ok=True)
        
        self.config = self.load_config()

    def load_config(self):
        """加载配置文件"""
        default_config = {
            "language": "auto",  # auto, en, zh
            "theme": "auto",  # light, dark, auto
            "last_directory": "",
            "threads": min(32, multiprocessing.cpu_count() * 2),
            "classification_method": "duration",
            "custom_output_dir": "",  # 自定义输出目录，空字符串表示使用默认路径
            "save_logs": False,  # 是否保存日志
            "auto_open_output_dir": True,  # 提取完成后是否自动打开输出目录
            "use_custom_theme_color": False,  # 是否使用自定义主题颜色
            "theme_color": "#e8b3ff"  # 默认主题颜色
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置，确保所有必需的键都存在
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                return default_config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return default_config

    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
                
            # 同步主题色和主题模式到PyQt-Fluent-Widgets配置
            self.sync_theme_to_qfluent()
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

    def sync_theme_to_qfluent(self):
        """同步主题设置到PyQt-Fluent-Widgets配置文件
        
        仅更新配置文件，不强制重新加载配置，以避免干扰动画流程
        """
        try:
            # 默认配置
            qfluent_config = {
                "QFluentWidgets": {
                    "ThemeMode": "Auto",
                    "ThemeColor": "#ffff893f"
                }
            }
            
            # 读取现有配置（如果存在）
            if os.path.exists(self.qfluent_config_file):
                try:
                    with open(self.qfluent_config_file, 'r', encoding='utf-8') as f:
                        qfluent_config = json.load(f)
                except Exception as e:
                    logger.warning(f"读取QFluentWidgets配置失败: {e}")
            
            # 确保QFluentWidgets键存在
            if "QFluentWidgets" not in qfluent_config:
                qfluent_config["QFluentWidgets"] = {}
                
            # 同步主题模式
            theme_mode = self.config.get("theme", "auto")
            if theme_mode == "dark":
                qfluent_config["QFluentWidgets"]["ThemeMode"] = "Dark"
            elif theme_mode == "light":
                qfluent_config["QFluentWidgets"]["ThemeMode"] = "Light"
            else:
                qfluent_config["QFluentWidgets"]["ThemeMode"] = "Auto"
                
            # 同步主题色
            use_custom_color = self.config.get("use_custom_theme_color", False)
            
            if use_custom_color:
                # 获取自定义主题色，确保是带#前缀的十六进制颜色格式
                theme_color = self.config.get("theme_color", "#0078d4")
                if not theme_color.startswith('#'):
                    theme_color = f"#{theme_color}"
                
                # PyQt-Fluent-Widgets需要带ff前缀的ARGB格式
                if len(theme_color) == 7:  # #RRGGBB 格式
                    theme_color = f"#ff{theme_color[1:]}"
                    
                qfluent_config["QFluentWidgets"]["ThemeColor"] = theme_color
            else:
                # 使用默认主题色 #ff0078d4
                qfluent_config["QFluentWidgets"]["ThemeColor"] = "#ffe8b3ff"
            
            # 保存到PyQt-Fluent-Widgets配置文件
            os.makedirs(os.path.dirname(self.qfluent_config_file), exist_ok=True)
            with open(self.qfluent_config_file, 'w', encoding='utf-8') as f:
                json.dump(qfluent_config, f, indent=4, ensure_ascii=False)
                
            # 确保配置文件权限正确（在非Windows系统上可能需要）
            if os.name != 'nt':
                try:
                    os.chmod(self.qfluent_config_file, 0o644)
                except Exception:
                    pass
                
            # 不再尝试强制QFluentWidgets重新加载配置
            # 这样可以避免干扰主题切换动画流程
                
        except Exception as e:
            logger.error(f"同步主题到PyQt-Fluent-Widgets失败: {e}")
            import traceback
            logger.debug(traceback.format_exc())

    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)

    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
        self.save_config()
        
    def get_qfluent_config(self):
        """获取QFluentWidgets配置文件内容"""
        try:
            if os.path.exists(self.qfluent_config_file):
                with open(self.qfluent_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"QFluentWidgets": {"ThemeMode": "Auto", "ThemeColor": "#ffff893f"}}
        except Exception as e:
            logger.error(f"读取QFluentWidgets配置失败: {e}")
            return {"QFluentWidgets": {"ThemeMode": "Auto", "ThemeColor": "#ffff893f"}} 