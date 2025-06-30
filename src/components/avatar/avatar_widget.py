#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JustKanade Avatar Widget - 显示QQ头像的侧边栏导航组件
"""

import os
import requests
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap, QPainter, QBrush, QColor, QFont
from PyQt5.QtCore import Qt, QSize, QTimer, QRect, pyqtSignal, QThread, QUrl
from PyQt5.QtGui import QDesktopServices

from qfluentwidgets import NavigationWidget, isDarkTheme, MessageBox

# 全局语言管理器变量
lang = None

class AvatarDownloader(QThread):
    """头像下载线程，避免阻塞UI"""
    # 下载完成后发送信号，参数为下载的图像数据
    downloadFinished = pyqtSignal(bytes)
    downloadError = pyqtSignal(str)

    def __init__(self, qq_number):
        super().__init__()
        self.qq_number = qq_number
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'
        }

    def run(self):
        try:
            url = f"http://q1.qlogo.cn/g?b=qq&nk={self.qq_number}&s=100&t=1547904810"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                self.downloadFinished.emit(response.content)
            else:
                self.downloadError.emit(f"获取头像失败，状态码: {response.status_code}")
        except Exception as e:
            self.downloadError.emit(f"下载头像时发生错误: {str(e)}")


class AvatarWidget(NavigationWidget):
    """自定义头像导航组件，显示QQ头像"""

    def __init__(self, qq_number="2824333590", parent=None):
        super().__init__(isSelectable=False, parent=parent)
        self.qq_number = qq_number
        self.avatar = None
        self.setFixedHeight(36)  # 设置固定高度与其他导航按钮一致
        self.github_url = "https://github.com/JustKanade"  # GitHub主页链接
        
        # 定时器，用于周期性更新头像
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.refresh_avatar)
        self.update_timer.start(30 * 60 * 1000)  # 30分钟更新一次
        
        # 立即下载头像
        self.refresh_avatar()
    
    def refresh_avatar(self):
        """刷新头像"""
        self.downloader = AvatarDownloader(self.qq_number)
        self.downloader.downloadFinished.connect(self._on_avatar_downloaded)
        self.downloader.downloadError.connect(self._on_download_error)
        self.downloader.start()
    
    def _on_avatar_downloaded(self, content):
        """头像下载完成后处理"""
        image = QImage()
        if image.loadFromData(content):
            self.avatar = image.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.update()  # 更新界面
        else:
            # 加载失败时可以设置默认头像
            pass
    
    def _on_download_error(self, error_msg):
        """处理下载错误"""
        # 可以设置一个默认头像
        pass
    
    def setCompacted(self, isCompacted):
        """设置是否处于紧凑模式 - 这个方法会被NavigationInterface自动调用"""
        super().setCompacted(isCompacted)  # 必须调用父类方法
        self.update()  # 更新界面显示

    def mousePressEvent(self, event):
        """鼠标按下事件处理"""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.showConfirmDialog()

    def showConfirmDialog(self):
        """显示确认对话框"""
        # 获取主窗口作为父控件，确保对话框正确显示
        main_window = self.window()
        parent = main_window if main_window else self
        
        # 创建确认对话框标题和内容（支持多语言）
        if lang:
            # 使用语言管理器翻译
            title = lang.get("visit_github")
            content = lang.get("confirm_visit_github")
        else:
            # 默认中英文文本
            title = "访问GitHub / Visit GitHub"
            content = "是否跳转至JustKanade的GitHub主页？ / Do you want to visit JustKanade's GitHub page?"
        
        # 显示确认对话框
        confirm_box = MessageBox(title, content, parent)
        if confirm_box.exec():
            self.openGitHubPage()

    def openGitHubPage(self):
        """打开GitHub主页"""
        QDesktopServices.openUrl(QUrl(self.github_url))
    
    def paintEvent(self, e):
        """自定义绘制函数"""
        painter = QPainter(self)
        painter.setRenderHints(QPainter.SmoothPixmapTransform | QPainter.Antialiasing)

        painter.setPen(Qt.NoPen)

        if self.isPressed:
            painter.setOpacity(0.7)

        # 绘制背景
        if self.isEnter:
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 10))
            painter.drawRoundedRect(self.rect(), 5, 5)

        # 绘制头像
        if self.avatar:
            painter.translate(8, 6)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.avatar))
            painter.drawEllipse(0, 0, 24, 24)
            painter.translate(-8, -6)
        
        # 绘制文本 - 只在非紧凑模式下显示
        if not self.isCompacted:
            painter.setPen(Qt.white if isDarkTheme() else Qt.black)
            font = QFont('Segoe UI')
            font.setPixelSize(14)
            painter.setFont(font)
            painter.drawText(QRect(44, 0, 255, 36), Qt.AlignVCenter, 'JustKanade') 