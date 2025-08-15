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
    Slider, FluentIcon, InfoBar, InfoBarPosition, 
    qconfig, ConfigItem, BoolValidator
)

from src.locale import lang

logger = logging.getLogger(__name__)


class BackgroundImageCard(SettingCard):
    """背景图片选择卡片"""
    
    imageChanged = pyqtSignal(str)  # 图片路径改变信号
    
    def __init__(self, config_manager, parent=None):
        self.config_manager = config_manager
        self.lang_manager = lang
        
        super().__init__(
            FluentIcon.PHOTO,
            self.get_text("background_image_title"),
            self.get_text("background_image_description"),
            parent
        )
        
        self.current_image_path = ""
        self._setup_ui()
        self._connect_signals()
        
    def get_text(self, key, default=""):
        """获取本地化文本"""
        try:
            return self.lang_manager.get(key, default)
        except:
            return default
            
    def _setup_ui(self):
        """设置UI界面"""
        # 选择图片按钮
        self.selectButton = PushButton(self.get_text("select_image", "选择图片"))
        self.selectButton.setFixedWidth(120)
        
        # 清除图片按钮
        self.clearButton = PushButton(self.get_text("clear_image", "清除图片"))
        self.clearButton.setFixedWidth(120)
        self.clearButton.setEnabled(False)
        
        # 当前图片路径标签
        self.pathLabel = QLabel(self.get_text("no_image_selected", "未选择图片"))
        self.pathLabel.setStyleSheet("color: gray; font-size: 12px;")
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.selectButton)
        button_layout.addWidget(self.clearButton)
        button_layout.addStretch()
        
        # 主布局
        content_layout = QVBoxLayout()
        content_layout.addLayout(button_layout)
        content_layout.addWidget(self.pathLabel)
        content_layout.setSpacing(8)
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        
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
                self.get_text("image_filter", "图片文件") + " (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
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
                        title=self.get_text("success", "成功"),
                        content=self.get_text("image_selected", "背景图片已选择"),
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self.window()
                    )
                    
        except Exception as e:
            logger.error(f"选择背景图片失败: {e}")
            InfoBar.error(
                title=self.get_text("error", "错误"),
                content=self.get_text("image_select_failed", "选择背景图片失败"),
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
                title=self.get_text("success", "成功"),
                content=self.get_text("image_cleared", "背景图片已清除"),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            )
            
        except Exception as e:
            logger.error(f"清除背景图片失败: {e}")
            
    def _update_image_path(self, path: str):
        """更新图片路径显示"""
        self.current_image_path = path
        
        if path and Path(path).exists():
            # 显示文件名
            file_name = Path(path).name
            if len(file_name) > 30:
                display_name = file_name[:27] + "..."
            else:
                display_name = file_name
                
            self.pathLabel.setText(display_name)
            self.pathLabel.setToolTip(path)
            self.clearButton.setEnabled(True)
        else:
            self.pathLabel.setText(self.get_text("no_image_selected", "未选择图片"))
            self.pathLabel.setToolTip("")
            self.clearButton.setEnabled(False)


class BackgroundOpacityCard(SettingCard):
    """背景透明度设置卡片"""
    
    opacityChanged = pyqtSignal(float)  # 透明度改变信号
    
    def __init__(self, config_manager, parent=None):
        self.config_manager = config_manager
        self.lang_manager = lang
        
        super().__init__(
            FluentIcon.TRANSPARENT,
            self.get_text("background_opacity_title", "背景透明度"),
            self.get_text("background_opacity_description", "调整背景图片的透明度"),
            parent
        )
        
        self._setup_ui()
        self._connect_signals()
        
    def get_text(self, key, default=""):
        """获取本地化文本"""
        try:
            return self.lang_manager.get(key, default)
        except:
            return default
            
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
    """背景模糊半径设置卡片"""
    
    blurChanged = pyqtSignal(int)  # 模糊半径改变信号
    
    def __init__(self, config_manager, parent=None):
        self.config_manager = config_manager
        self.lang_manager = lang
        
        super().__init__(
            FluentIcon.HISTORY,
            self.get_text("background_blur_title", "背景模糊"),
            self.get_text("background_blur_description", "调整背景图片的模糊半径"),
            parent
        )
        
        self._setup_ui()
        self._connect_signals()
        
    def get_text(self, key, default=""):
        """获取本地化文本"""
        try:
            return self.lang_manager.get(key, default)
        except:
            return default
            
    def _setup_ui(self):
        """设置UI界面"""
        # 模糊半径滑块
        self.blurSlider = Slider(Qt.Horizontal)
        self.blurSlider.setRange(0, 100)
        self.blurSlider.setValue(10)  # 默认10
        self.blurSlider.setFixedWidth(200)
        
        # 模糊值标签
        self.valueLabel = QLabel("10")
        self.valueLabel.setFixedWidth(40)
        self.valueLabel.setAlignment(Qt.AlignCenter)
        
        # 布局
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.blurSlider)
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
        self.blurSlider.valueChanged.connect(self._on_blur_changed)
        
    def _load_current_setting(self):
        """加载当前设置"""
        try:
            blur_radius = self.config_manager.get("backgroundBlurRadius", 10)
            self.blurSlider.setValue(blur_radius)
            self._update_value_label(blur_radius)
        except Exception as e:
            logger.error(f"加载背景模糊设置失败: {e}")
            
    def _on_blur_changed(self, value):
        """模糊半径改变处理"""
        try:
            self._update_value_label(value)
            
            # 保存到配置
            self.config_manager.set("backgroundBlurRadius", value)
            
            # 发送信号
            self.blurChanged.emit(value)
            
        except Exception as e:
            logger.error(f"更新背景模糊设置失败: {e}")
            
    def _update_value_label(self, value):
        """更新值标签"""
        self.valueLabel.setText(str(value))


class ComponentOpacityCard(SettingCard):
    """组件透明度设置卡片"""
    
    componentOpacityChanged = pyqtSignal(float)  # 组件透明度改变信号
    
    def __init__(self, config_manager, parent=None):
        self.config_manager = config_manager
        self.lang_manager = lang
        
        super().__init__(
            FluentIcon.SETTING,
            self.get_text("component_opacity_title", "组件透明度"),
            self.get_text("component_opacity_description", "调整界面组件的透明度"),
            parent
        )
        
        self._setup_ui()
        self._connect_signals()
        
    def get_text(self, key, default=""):
        """获取本地化文本"""
        try:
            return self.lang_manager.get(key, default)
        except:
            return default
            
    def _setup_ui(self):
        """设置UI界面"""
        # 透明度滑块
        self.opacitySlider = Slider(Qt.Horizontal)
        self.opacitySlider.setRange(30, 100)  # 30%-100%
        self.opacitySlider.setValue(90)  # 默认90%
        self.opacitySlider.setFixedWidth(200)
        
        # 透明度值标签
        self.valueLabel = QLabel("90%")
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
            opacity = self.config_manager.get("componentOpacity", 0.9)
            slider_value = int(opacity * 100)
            self.opacitySlider.setValue(slider_value)
            self._update_value_label(slider_value)
        except Exception as e:
            logger.error(f"加载组件透明度设置失败: {e}")
            
    def _on_opacity_changed(self, value):
        """透明度改变处理"""
        try:
            opacity = value / 100.0
            self._update_value_label(value)
            
            # 保存到配置
            self.config_manager.set("componentOpacity", opacity)
            
            # 发送信号
            self.componentOpacityChanged.emit(opacity)
            
        except Exception as e:
            logger.error(f"更新组件透明度失败: {e}")
            
    def _update_value_label(self, value):
        """更新值标签"""
        self.valueLabel.setText(f"{value}%") 