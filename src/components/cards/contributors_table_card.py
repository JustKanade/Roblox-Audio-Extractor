#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贡献者表格卡片组件
Contributors Table Card Component
"""

import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QTableWidgetItem, QHeaderView, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QDesktopServices, QCursor, QColor, QFont
from PyQt5.QtCore import QUrl

from qfluentwidgets import (
    TableWidget, StrongBodyLabel, BodyLabel, 
    FluentIcon, HyperlinkButton, isDarkTheme, themeColor, qconfig
)

from src.utils.file_utils import resource_path


class ContributorsTableCard(QWidget):
    """贡献者表格组件"""
    
    def __init__(self, parent=None, lang=None):
        super().__init__(parent)
        
        # 确保语言对象存在，否则创建空的语言处理函数
        if lang is None:
            self.get_text = lambda key, default="": default
        else:
            self.get_text = lang.get
            
        self.lang = lang
        self.contributors_data = []
        self.setupContent()
        self.loadContributors()
        
        # 监听主题色变化 - 使用多种信号确保捕获变化
        try:
            qconfig.themeChanged.connect(self.updateLinkColors)
        except:
            pass
        try:
            qconfig.appRestartSig.connect(self.updateLinkColors)
        except:
            pass
        try:
            # 尝试监听配置文件变化
            if hasattr(qconfig, 'configChanged'):
                qconfig.configChanged.connect(self.updateLinkColors)
        except:
            pass
        
    def setupContent(self):
        """设置组件内容"""
        # 设置组件尺寸策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        
        # 设置组件布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        layout.setSpacing(0)
        
        # 创建表格
        self.table = TableWidget()
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.setupTable()
        
        layout.addWidget(self.table)
        
    def setupTable(self):
        """设置表格"""
        # 启用边框和圆角
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        
        # 设置表格属性
        self.table.setWordWrap(False)
        self.table.setColumnCount(4)
        self.table.setRowCount(0)
        
        # 设置表头
        headers = [
            self.get_text("contributor_name", "Name"),
            self.get_text("contributor_type", "Contribution Type"), 
            self.get_text("contributor_notes", "Notes"),
            self.get_text("contributor_links", "Links")
        ]
        self.table.setHorizontalHeaderLabels(headers)
        
        # 隐藏垂直表头
        self.table.verticalHeader().hide()
        
        # 设置表格样式
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(self.table.SelectRows)
        
        # 启用鼠标跟踪以支持悬停效果
        self.table.setMouseTracking(True)
        
    def loadContributors(self):
        """加载贡献者数据"""
        try:
            # 构建数据文件路径
            data_file = resource_path(os.path.join("data", "contributors.json"))
            
            if not os.path.exists(data_file):
                # 如果文件不存在，使用默认数据
                self.contributors_data = self.getDefaultContributors()
            else:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.contributors_data = data.get("contributors", [])
                    
            self.populateTable()
            
        except Exception as e:
            print(f"加载贡献者数据失败: {e}")
            self.contributors_data = self.getDefaultContributors()
            self.populateTable()
            
    def getDefaultContributors(self):
        """获取默认贡献者数据"""
        return [
            {
                "name": "JustKanade",
                "contribution_type": {
                    "en": "Main Developer",
                    "zh": "主要开发者"
                },
                "links": "https://github.com/JustKanade",
                "notes": {
                    "en": "Project creator and maintainer",
                    "zh": "项目创建者和维护者"
                }
            }
        ]
        
    def populateTable(self):
        """填充表格数据"""
        self.table.setRowCount(len(self.contributors_data))
        
        for row, contributor in enumerate(self.contributors_data):
            # 姓名
            name_item = QTableWidgetItem(contributor.get("name", ""))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # 贡献类型（支持多语言）
            contribution_type = contributor.get("contribution_type", {})
            if isinstance(contribution_type, dict):
                # 根据当前语言选择显示文本
                current_lang = "zh" if self.lang and hasattr(self.lang, 'current_language') and \
                              str(self.lang.current_language) == "Language.CHINESE" else "en"
                type_text = contribution_type.get(current_lang, contribution_type.get("en", ""))
            else:
                type_text = str(contribution_type)
                
            type_item = QTableWidgetItem(type_text)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, type_item)
            
            # 备注（支持多语言）
            notes = contributor.get("notes", {})
            if isinstance(notes, dict):
                current_lang = "zh" if self.lang and hasattr(self.lang, 'current_language') and \
                              str(self.lang.current_language) == "Language.CHINESE" else "en"
                notes_text = notes.get(current_lang, notes.get("en", ""))
            else:
                notes_text = str(notes)
                
            notes_item = QTableWidgetItem(notes_text)
            notes_item.setFlags(notes_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, notes_item)
            
            # 链接
            link_url = contributor.get("links", "") or contributor.get("github", "")  # 兼容旧数据
            if link_url:
                # 根据链接类型显示不同的文本
                if "github.com" in link_url.lower():
                    link_text = "GitHub"
                elif "twitter.com" in link_url.lower():
                    link_text = "Twitter"
                elif "linkedin.com" in link_url.lower():
                    link_text = "LinkedIn"
                elif "mailto:" in link_url.lower():
                    link_text = "Email"
                elif "bilibili.com" in link_url.lower():
                    link_text = "BiliBili"
                else:
                    link_text = "Website"
                    
                link_item = QTableWidgetItem(link_text)
                link_item.setFlags(link_item.flags() & ~Qt.ItemIsEditable)
                link_item.setData(Qt.UserRole, link_url)  # 存储URL
                link_item.setToolTip(link_url)
                
                # 设置链接文字颜色为主题色
                self.setLinkItemColor(link_item)
                
                self.table.setItem(row, 3, link_item)
            else:
                link_item = QTableWidgetItem("-")
                link_item.setFlags(link_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 3, link_item)
            
        # 自适应列宽
        self.table.resizeColumnsToContents()
        
        # 设置列宽模式 - 在填充数据后设置
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 姓名列自适应
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 贡献类型列自适应
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # 备注列拉伸填充
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 链接列自适应
        
        # 计算表格所需的高度
        self.updateTableSize()
        
        # 连接点击事件
        self.table.cellClicked.connect(self.onCellClicked)
        
        # 连接鼠标进入事件，为链接列设置手形光标
        self.table.cellEntered.connect(self.onCellEntered)
        
        # 添加定时器定期检查主题色变化
        try:
            self.current_theme_color = themeColor()
        except:
            self.current_theme_color = None
        self.theme_check_timer = QTimer()
        self.theme_check_timer.timeout.connect(self.checkThemeColorChange)
        self.theme_check_timer.start(1000)  # 每秒检查一次
        
    def updateTableSize(self):
        """更新表格和组件尺寸"""
        if self.table.rowCount() == 0:
            return
            
        # 计算行高
        row_height = self.table.rowHeight(0)
        header_height = self.table.horizontalHeader().height()
        
        # 计算总高度
        total_table_height = header_height + (row_height * self.table.rowCount())
        
        # 设置表格最小高度
        self.table.setMinimumHeight(total_table_height + 10)  # 额外10px边距
        
        # 设置组件最小高度（无额外边距）
        self.setMinimumHeight(total_table_height + 10)
        
        # 设置合理的最大高度以防内容过多
        max_height = 500
        if total_table_height > max_height:
            self.setMaximumHeight(max_height)
            # 如果内容超出最大高度，启用滚动条
            self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.setMaximumHeight(total_table_height + 10)
            self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
    def setLinkItemColor(self, link_item):
        """设置链接项的颜色"""
        try:
            color = themeColor()
            link_item.setForeground(color)
        except Exception:
            # 如果获取主题色失败，使用默认蓝色
            color = QColor("#0078d4")
            link_item.setForeground(color)
    
    def updateLinkColors(self):
        """更新所有链接的颜色"""
        if not hasattr(self, 'table') or self.table.rowCount() == 0:
            return
            
        # 遍历表格中的所有链接项（第3列）
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 3)
            if item and item.data(Qt.UserRole):  # 如果有链接数据
                self.setLinkItemColor(item)
    
    def checkThemeColorChange(self):
        """检查主题色是否变化"""
        try:
            current_color = themeColor()
            if self.current_theme_color != current_color:
                self.current_theme_color = current_color
                self.updateLinkColors()
        except Exception:
            pass
    
    def showEvent(self, event):
        """重写显示事件，确保主题色正确应用"""
        super().showEvent(event)
        # 在显示时更新链接颜色
        self.updateLinkColors()
        
    def closeEvent(self, event):
        """重写关闭事件，清理资源"""
        if hasattr(self, 'theme_check_timer'):
            self.theme_check_timer.stop()
        super().closeEvent(event)
        
    def __del__(self):
        """析构函数，确保清理定时器"""
        if hasattr(self, 'theme_check_timer'):
            self.theme_check_timer.stop()
    
    def onCellEntered(self, row, column):
        """处理鼠标进入单元格事件"""
        # 如果是链接列且有有效链接，设置手形光标
        if column == 3:
            item = self.table.item(row, column)
            if item and item.data(Qt.UserRole):
                self.table.setCursor(QCursor(Qt.PointingHandCursor))
            else:
                self.table.setCursor(QCursor(Qt.ArrowCursor))
        else:
            self.table.setCursor(QCursor(Qt.ArrowCursor))
    
    def onCellClicked(self, row, column):
        """处理单元格点击事件"""
        # 如果点击的是链接列
        if column == 3:
            item = self.table.item(row, column)
            if item and item.data(Qt.UserRole):
                url = item.data(Qt.UserRole)
                try:
                    QDesktopServices.openUrl(QUrl(url))
                except Exception as e:
                    print(f"打开URL失败: {e}") 