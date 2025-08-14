#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QFont, QColor

from qfluentwidgets import (
    CardWidget, TitleLabel, SubtitleLabel,
    StrongBodyLabel, BodyLabel, CaptionLabel, 
    FluentIcon, IconWidget,
    DisplayLabel, ScrollArea,
    SettingCardGroup, ExpandLayout, SettingCard,
    HorizontalFlipView, HorizontalPipsPager,
    MaskDialogBase, PushButton, TransparentToolButton, isDarkTheme
)

from src.utils.file_utils import resource_path
from src.management.theme_management.interface_theme_mixin import InterfaceThemeMixin
import os


class QRCodeDialog(MaskDialogBase):
    """二维码显示对话框"""
    
    def __init__(self, parent=None, lang=None):
        super().__init__(parent)
        self.lang = lang
        if self.lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = self.lang.get
        
        # 设置窗口属性
        self.setWindowTitle(self.get_text("wechat_pay", "WeChat Pay"))
        self.setMaskColor(QColor(0, 0, 0, 120))  # 半透明黑色蒙版
        
        # 创建对话框内容
        self.setupUI()
        
        # 添加阴影效果
        self.setShadowEffect(blurRadius=40, offset=(0, 6), color=QColor(0, 0, 0, 60))
    
    def setupUI(self):
        """设置对话框UI"""
        # 设置对话框大小
        self.widget.setFixedWidth(400)
        self.widget.setFixedHeight(500)
        
        # 设置边框圆角和样式
        if isDarkTheme():
            self.widget.setStyleSheet("""
                background-color: #2b2b2b;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            """)
            text_color = "#ffffff"
        else:
            self.widget.setStyleSheet("""
                background-color: white;
                border-radius: 10px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            """)
            text_color = "#202020"
        
        # 创建主布局
        self.mainLayout = QVBoxLayout(self.widget)
        self.mainLayout.setContentsMargins(24, 20, 24, 24)
        self.mainLayout.setSpacing(16)
        
        # === 标题栏区域 ===
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)
        
        # 标题图标
        icon = IconWidget(FluentIcon.QRCODE, self.widget)
        icon.setFixedSize(28, 28)
        
        # 标题文本
        titleLabel = TitleLabel(self.get_text("wechat_pay", "WeChat Pay"), self.widget)
        titleLabel.setStyleSheet(f"color: {text_color}; font-weight: bold; border: none;")
        
        # 关闭按钮
        closeBtn = TransparentToolButton(FluentIcon.CLOSE, self.widget)
        closeBtn.setFixedSize(32, 32)
        closeBtn.setIconSize(QSize(16, 16))
        closeBtn.clicked.connect(self.reject)
        
        header.addWidget(icon)
        header.addWidget(titleLabel, 1)
        header.addWidget(closeBtn)
        
        self.mainLayout.addLayout(header)
        
        # === 二维码显示区域 ===
        qr_container = QWidget()
        qr_layout = QVBoxLayout(qr_container)
        qr_layout.setContentsMargins(20, 20, 20, 20)
        qr_layout.setSpacing(15)
        qr_layout.setAlignment(Qt.AlignCenter)
        
        # 二维码图片标签
        self.qr_image_label = QLabel()
        self.qr_image_label.setAlignment(Qt.AlignCenter)
        self.qr_image_label.setMinimumSize(280, 280)
        self.loadWeChatQR()
        qr_layout.addWidget(self.qr_image_label, 0, Qt.AlignCenter)
        
        # 说明文字
        desc_label = CaptionLabel(self.get_text("scan_qr_code", "Scan QR Code to Donate"))
        desc_label.setAlignment(Qt.AlignCenter)

        desc_label.setStyleSheet(f"color: {text_color}; border: none;")
        qr_layout.addWidget(desc_label, 0, Qt.AlignCenter)
        
        self.mainLayout.addWidget(qr_container)
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
            else:
                self.showFallbackQR()
        except Exception as e:
            self.showFallbackQR()
    
    def showFallbackQR(self):
        """显示备用二维码提示"""
        self.qr_image_label.setText("\n微信收款码\n图片加载失败")
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
        
        self._setupContent()
    
    def _setupContent(self):
        """设置内容"""
        # 创建右侧内容容器
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 20, 0)
        content_layout.setSpacing(8)
        
        # 创建查看二维码按钮
        self.view_qr_btn = PushButton(FluentIcon.VIEW, self.get_text("view_qr_code", "View QR Code"))
        self.view_qr_btn.setFixedHeight(32)
        self.view_qr_btn.clicked.connect(self.showQRCode)
        
        content_layout.addWidget(self.view_qr_btn)
        
        # 将内容添加到SettingCard的hBoxLayout
        self.hBoxLayout.addWidget(content_widget)
    
    def showQRCode(self):
        """显示二维码对话框"""
        dialog = QRCodeDialog(self.window(), self.lang)
        dialog.show()


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
        content_widget.setMinimumHeight(400)

        # 支付方式卡片组
        self.paymentGroup = SettingCardGroup(
            self.get_text("support_development", "Support Development"),
            content_widget
        )
        
        # 微信支付卡片
        self.wechatCard = WeChatPayCard(parent=self.paymentGroup, lang=self.lang)
        self.paymentGroup.addSettingCard(self.wechatCard)
        
        self.expandLayout.addWidget(self.paymentGroup)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
        # 设置为响应式
        self.setResponsiveContentWidget(scroll)
    
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
        """
        
        # 合并通用样式和特定样式
        combined_styles = self.get_common_interface_styles() + specific_styles
        self.setStyleSheet(combined_styles) 