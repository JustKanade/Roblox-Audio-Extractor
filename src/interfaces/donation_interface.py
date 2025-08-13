#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont

from qfluentwidgets import (
    CardWidget, TitleLabel, SubtitleLabel,
    StrongBodyLabel, BodyLabel, CaptionLabel, 
    FluentIcon, IconWidget,
    DisplayLabel, ScrollArea,
    SettingCardGroup, ExpandLayout, SettingCard,
    HorizontalFlipView, HorizontalPipsPager
)

from src.utils.file_utils import resource_path
from src.management.theme_management.interface_theme_mixin import InterfaceThemeMixin
import os



class WeChatPayCard(SettingCard):
    """微信支付卡片"""
    
    def __init__(self, parent=None, lang=None):
        self.lang = lang
        if self.lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = self.lang.get
            
        super().__init__(
            FluentIcon.QRCODE,
            self.get_text("wechat_pay", "WeChat Pay"),
            self.get_text("scan_qr_code", "Scan QR Code to Donate"),
            parent
        )


class DonationInterface(QWidget, InterfaceThemeMixin):
    """捐款界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None):
        super().__init__(parent)
        self.setObjectName("donationInterface")
        self.config_manager = config_manager
        self.lang = lang
        
        # 确保语言对象存在
        if self.lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = self.lang.get
        
        # 初始化界面
        self.initUI()
        # 应用样式
        self.setInterfaceStyles()
        
    def initUI(self):
        """初始化界面"""
        # 创建滚动区域
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setObjectName('donationScrollArea')

        # 主内容容器
        content_widget = QWidget()
        content_widget.setObjectName('donationScrollWidget')
        self.expandLayout = ExpandLayout(content_widget)
        self.expandLayout.setContentsMargins(20, 20, 20, 20)
        self.expandLayout.setSpacing(28)
        
        # 确保内容容器有足够的最小高度
        content_widget.setMinimumHeight(800)

        # 支付方式卡片组
        self.paymentGroup = SettingCardGroup(
            self.get_text("support_development", "Support Development"),
            content_widget
        )
        
        # 微信支付卡片
        self.wechatCard = WeChatPayCard(parent=self.paymentGroup, lang=self.lang)
        self.paymentGroup.addSettingCard(self.wechatCard)
        
        self.expandLayout.addWidget(self.paymentGroup)

        # 二维码展示区域
        self.createQRCodeSection(content_widget)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # 设置为响应式
        self.setResponsiveContentWidget(scroll)
    
    def createQRCodeSection(self, parent):
        """创建二维码展示区域"""
        # 创建二维码卡片容器，参考demo代码的布局方式
        qr_card = CardWidget(parent)
        qr_card.setObjectName('qrCodeCard')
        
        # 设置卡片大小策略，确保有足够空间
        qr_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        qr_card.setMinimumHeight(400)  # 设置最小高度确保二维码完整显示
        
        # 创建垂直布局，参考demo中的布局设置
        qr_layout = QVBoxLayout(qr_card)
        qr_layout.setContentsMargins(30, 30, 30, 30)
        qr_layout.setSpacing(20)
        qr_layout.setAlignment(Qt.AlignCenter)
        
        
        # 二维码图片标签
        self.qr_image_label = QLabel()
        self.qr_image_label.setAlignment(Qt.AlignCenter)
        self.qr_image_label.setObjectName('qrImage')
        self.qr_image_label.setMinimumSize(280, 280)  # 确保图片区域有足够大小
        self.loadWeChatQR()
        qr_layout.addWidget(self.qr_image_label, 0, Qt.AlignCenter)
        
        # 说明文字
        desc_label = CaptionLabel(self.get_text("wechat_pay", "WeChat Pay"))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setObjectName('qrDescription')
        qr_layout.addWidget(desc_label, 0, Qt.AlignCenter)
        
        # 添加到主布局，参考demo代码的居中方式
        self.expandLayout.addWidget(qr_card)
    
    def loadWeChatQR(self):
        """加载微信收款码"""
        try:
            qr_path = resource_path(os.path.join("res", "wechat.jpg"))

            
            if os.path.exists(qr_path):
                pixmap = QPixmap(qr_path)
                if not pixmap.isNull():
                    # 缩放到合适大小，保持宽高比
                    scaled_pixmap = pixmap.scaled(
                        250, 250,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.qr_image_label.setPixmap(scaled_pixmap)
            else:
                self.showFallbackQR()
        except Exception as e:
            self.showFallbackQR()
    
    def showFallbackQR(self):
        """显示备用二维码提示"""
        self.qr_image_label.setText("📱\n微信收款码\n图片加载失败")
        self.qr_image_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        self.qr_image_label.setFont(font)
        self.qr_image_label.setMinimumSize(280, 280)
        self.qr_image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #cccccc;
                border-radius: 8px;
                background-color: #f5f5f5;
                color: #666666;
            }
        """)
    
    def setResponsiveContentWidget(self, scroll_area):
        """为滚动区域内的内容容器应用响应式布局设置"""
        if not scroll_area:
            return
            
        content_widget = scroll_area.widget()
        if not content_widget:
            return
            
        # 设置垂直大小策略，允许内容扩展
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 确保布局设置了顶部对齐
        if content_widget.layout():
            content_widget.layout().setAlignment(Qt.AlignTop)
            
            # 对于ExpandLayout，添加适当的伸缩项
            if hasattr(content_widget.layout(), 'addStretch'):
                content_widget.layout().addStretch(1)
            
    def setInterfaceStyles(self):
        """设置捐款页面样式"""
        # 调用父类的通用样式设置
        super().setInterfaceStyles()
        
        # 获取文本样式
        text_styles = self.get_text_styles()
        
        # 应用特定的捐款页面样式
        specific_styles = f"""
            #donationInterface {{
                background-color: transparent;
            }}
            #donationScrollArea {{
                background-color: transparent;
                border: none;
            }}
            #donationScrollWidget {{
                background-color: transparent;
            }}
            #donationTitle {{
                {text_styles['title']}
            }}
            #donationThanks {{
                {text_styles['version']}
            }}
            #qrCodeCard {{
                background-color: transparent;
            }}
            #qrTitle {{
                color: #666666;
                font-size: 16px;
                font-weight: 500;
                margin-bottom: 10px;
            }}
            #qrImage {{
                margin: 10px;
            }}
            #qrDescription {{
                color: #888888;
                font-size: 12px;
                margin-top: 10px;
            }}
        """
        
        # 合并通用样式和特定样式
        combined_styles = self.get_common_interface_styles() + specific_styles
        self.setStyleSheet(combined_styles) 