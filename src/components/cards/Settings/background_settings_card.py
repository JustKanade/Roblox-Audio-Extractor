#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景设置卡片 - 提供背景图片、透明度、模糊效果等设置选项
"""

import os
import logging
from pathlib import Path
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QLabel
from PyQt5.QtGui import QPixmap

from qfluentwidgets import (
    SettingCardGroup, SettingCard, SwitchButton, PushButton, 
    Slider, FluentIcon, InfoBar, InfoBarPosition, BodyLabel,
    qconfig, ConfigItem, BoolValidator
)

# 尝试导入语言管理器
try:
    from src.locale import lang
except ImportError:
    lang = None
    print("警告：无法导入语言管理器，将使用默认翻译")

logger = logging.getLogger(__name__)

# 默认翻译，如果lang未初始化时使用
DEFAULT_TRANSLATIONS = {
    "background_image_title": "Background Image",
    "background_image_description": "Select a custom background image for the application",
    "background_opacity_title": "Background Opacity", 
    "background_opacity_description": "Adjust the opacity of the background image",
    "background_blur_title": "Background Blur",
    "background_blur_description": "Adjust the blur radius of the background image",
    "select_image": "Select Image",
    "clear_image": "Clear Image",
    "no_image_selected": "No image selected",
    "image_filter": "Image Files",
    "image_selected": "Background image selected successfully",
    "image_cleared": "Background image cleared successfully",
    "image_select_failed": "Failed to select background image",
    "success": "Success",
    "error": "Error",
    "blur_disabled": "Off"
}

def get_text(key, default=""):
    """获取翻译文本，如果lang未初始化则使用默认值"""
    if lang and hasattr(lang, 'get'):
        return lang.get(key, default or DEFAULT_TRANSLATIONS.get(key, key))
    return default or DEFAULT_TRANSLATIONS.get(key, key)


class BackgroundImageCard(SettingCard):
    """背景图片选择卡片"""
    
    imageChanged = pyqtSignal(str)  # 图片路径改变信号
    
    def __init__(self, config_manager, parent=None):
        self.config_manager = config_manager
        
        super().__init__(
            FluentIcon.PHOTO,
            get_text("background_image_title"),
            get_text("background_image_description"),
            parent
        )
        
        self.current_image_path = ""
        self._setup_ui()
        self._connect_signals()
            
    def _setup_ui(self):
        """设置UI界面"""
        # 选择图片按钮
        self.selectButton = PushButton(get_text("select_image"))
        self.selectButton.setFixedWidth(120)
        
        # 清除图片按钮
        self.clearButton = PushButton(get_text("clear_image"))
        self.clearButton.setFixedWidth(120)
        self.clearButton.setEnabled(False)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.selectButton)
        button_layout.addWidget(self.clearButton)
        button_layout.addStretch()
        
        content_widget = QWidget()
        content_widget.setLayout(button_layout)
        
        self.hBoxLayout.addWidget(content_widget, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        
        # 加载当前设置
        self._load_current_setting()
        
    def _connect_signals(self):
        """连接信号槽"""
        self.selectButton.clicked.connect(self._select_image)
        self.clearButton.clicked.connect(self._clear_image)
        
    def _load_current_setting(self):
        """加载当前设置"""
        try:
            current_path = self.config_manager.get("backgroundImagePath", "")
            if current_path and Path(current_path).exists():
                self._update_image_path(current_path)
        except Exception as e:
            logger.error(f"加载背景图片设置失败: {e}")
            
    def _select_image(self):
        """选择背景图片"""
        try:
            file_dialog = QFileDialog(self)
            file_dialog.setFileMode(QFileDialog.ExistingFile)
            file_dialog.setNameFilter(
                get_text("image_filter") + " (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
            )
            
            # 设置默认目录
            last_dir = self.config_manager.get("lastDirectory", "")
            if last_dir and Path(last_dir).exists():
                file_dialog.setDirectory(last_dir)
                
            if file_dialog.exec_() == QFileDialog.Accepted:
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    image_path = selected_files[0]
                    self._update_image_path(image_path)
                    
                    # 保存到配置
                    self.config_manager.set("backgroundImagePath", image_path)
                    self.config_manager.set("lastDirectory", str(Path(image_path).parent))
                    
                    # 发送信号
                    self.imageChanged.emit(image_path)
                    
                    # 显示成功提示
                    InfoBar.success(
                        title=get_text("success"),
                        content=get_text("image_selected"),
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self.window()
                    )
                    
        except Exception as e:
            logger.error(f"选择背景图片失败: {e}")
            InfoBar.error(
                title=get_text("error"),
                content=get_text("image_select_failed"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window()
            )
            
    def _clear_image(self):
        """清除背景图片"""
        try:
            self._update_image_path("")
            self.config_manager.set("backgroundImagePath", "")
            self.imageChanged.emit("")
            
            InfoBar.success(
                title=get_text("success"),
                content=get_text("image_cleared"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            )
            
        except Exception as e:
            logger.error(f"清除背景图片失败: {e}")
            
    def _update_image_path(self, path: str):
        """更新图片路径状态"""
        self.current_image_path = path
        
        # 更新清除按钮的可用状态
        if path and Path(path).exists():
            self.clearButton.setEnabled(True)
        else:
            self.clearButton.setEnabled(False)


class BackgroundOpacityCard(SettingCard):
    """背景透明度设置卡片"""
    
    opacityChanged = pyqtSignal(float)  # 透明度改变信号
    
    def __init__(self, config_manager, parent=None):
        self.config_manager = config_manager
        
        super().__init__(
            FluentIcon.TRANSPARENT,
            get_text("background_opacity_title"),
            get_text("background_opacity_description"),
            parent
        )
        
        self._setup_ui()
        self._connect_signals()
            
    def _setup_ui(self):
        """设置UI界面"""
        # 透明度滑块
        self.opacitySlider = Slider(Qt.Horizontal)
        self.opacitySlider.setRange(0, 100)
        self.opacitySlider.setValue(80)  # 默认80%
        self.opacitySlider.setFixedWidth(200)
        
        # 透明度值标签
        self.valueLabel = QLabel("80%")
        self.valueLabel.setFixedWidth(40)
        self.valueLabel.setAlignment(Qt.AlignCenter)
        
        # 布局
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.opacitySlider)
        slider_layout.addWidget(self.valueLabel)
        slider_layout.addStretch()
        
        slider_widget = QWidget()
        slider_widget.setLayout(slider_layout)
        
        self.hBoxLayout.addWidget(slider_widget, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        
        # 加载当前设置
        self._load_current_setting()
        
    def _connect_signals(self):
        """连接信号槽"""
        self.opacitySlider.valueChanged.connect(self._on_opacity_changed)
        
    def _load_current_setting(self):
        """加载当前设置"""
        try:
            opacity = self.config_manager.get("backgroundOpacity", 0.8)
            slider_value = int(opacity * 100)
            self.opacitySlider.setValue(slider_value)
            self._update_value_label(slider_value)
        except Exception as e:
            logger.error(f"加载背景透明度设置失败: {e}")
            
    def _on_opacity_changed(self, value):
        """透明度改变处理"""
        try:
            opacity = value / 100.0
            self._update_value_label(value)
            
            # 保存到配置
            self.config_manager.set("backgroundOpacity", opacity)
            
            # 发送信号
            self.opacityChanged.emit(opacity)
            
        except Exception as e:
            logger.error(f"更新背景透明度失败: {e}")
            
    def _update_value_label(self, value):
        """更新值标签"""
        self.valueLabel.setText(f"{value}%")


class BackgroundBlurCard(SettingCard):
    """背景模糊设置卡片"""
    
    blurChanged = pyqtSignal(int)  # 模糊半径改变信号
    
    def __init__(self, config_manager, parent=None):
        self.config_manager = config_manager
        
        super().__init__(
            FluentIcon.IOT,
            get_text("background_blur_title"),
            get_text("background_blur_description"),
            parent
        )
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """设置UI界面"""
        # 创建滑块
        self.slider = Slider(Qt.Horizontal)
        self.slider.setRange(0, 50)
        self.slider.setValue(self.config_manager.get("backgroundBlurRadius", 0) if self.config_manager else 0)
        self.slider.setFixedWidth(200)
        
        # 数值标签
        self.valueLabel = BodyLabel()
        self._update_value_label(self.slider.value())
        self.valueLabel.setFixedWidth(60)
        
        # 布局
        content_widget = QWidget()
        layout = QHBoxLayout(content_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.slider)
        layout.addWidget(self.valueLabel)
        layout.addStretch()
        
        self.hBoxLayout.addWidget(content_widget, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        
    def _connect_signals(self):
        """连接信号槽"""
        self.slider.valueChanged.connect(self._on_value_changed)
        
    def _on_value_changed(self, value):
        """值改变时的处理"""
        self._update_value_label(value)
        if self.config_manager:
            self.config_manager.set("backgroundBlurRadius", value)
        self.blurChanged.emit(value)
        
    def _update_value_label(self, value):
        """更新数值标签"""
        if value == 0:
            self.valueLabel.setText(get_text("blur_disabled", "0px"))
        else:
            self.valueLabel.setText(f"{value}px")


 