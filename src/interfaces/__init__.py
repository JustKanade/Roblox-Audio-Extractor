#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
接口模块，包含应用中的各种界面类
"""

from src.interfaces.home_interface import HomeInterface
from src.interfaces.about_interface import AboutInterface
from src.interfaces.extract_images_interface import ExtractImagesInterface
from src.interfaces.extract_textures_interface import ExtractTexturesInterface
from src.interfaces.clear_cache_interface import ClearCacheInterface
from src.interfaces.history_interface import HistoryInterface
from src.interfaces.extract_audio_interface import ExtractAudioInterface
from src.interfaces.extract_fonts_interface import ExtractFontsInterface
from src.interfaces.settings_interface import SettingsInterface

__all__ = [
    'HomeInterface', 
    'AboutInterface', 
    'ExtractImagesInterface', 
    'ExtractTexturesInterface', 
    'ClearCacheInterface',
    'HistoryInterface',
    'ExtractAudioInterface',
    'ExtractFontsInterface',
    'SettingsInterface'
] 