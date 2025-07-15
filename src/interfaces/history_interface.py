#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer

from qfluentwidgets import (
    CardWidget, BodyLabel, TitleLabel, StrongBodyLabel,
    ScrollArea, PushButton, TransparentPushButton, 
    FluentIcon, CaptionLabel, ProgressBar, PrimaryPushButton,
    TextEdit, IconWidget, SubtitleLabel, RoundMenu, Action,
    DropDownPushButton, PrimaryDropDownPushButton
)

import os
from src.utils.file_utils import open_directory
from src.utils.log_utils import LogHandler
from src.extractors.audio_extractor import ExtractedHistory


class HistoryInterface(QWidget):
    """历史记录界面类"""
    
    def __init__(self, parent=None, config_manager=None, lang=None, download_history=None):
        super().__init__(parent)
        self.setObjectName("historyInterface")
        self.config_manager = config_manager
        self.lang = lang
        self.download_history = download_history
        self._parent_window = parent
        
        # 确保语言对象存在，否则创建空的语言处理函数
        if self.lang is None:
            # 创建一个返回默认值的函数
            self.get_text = lambda key, *args, **kwargs: kwargs.get("default", "")
        else:
            # 使用lang对象的get方法
            self.get_text = self.lang.get
        
        # 初始化界面
        self.initUI()
        # 应用样式
        self.setHistoryStyles()
        
    def initUI(self):
        """初始化界面"""
        # 创建滚动区域
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 主内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # 历史统计卡片
        stats_card = CardWidget()
        stats_card.setMaximumHeight(220)  # 限制最大高度，防止异常放大
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(25, 20, 25, 20)
        stats_layout.setSpacing(15)

        # 标题
        stats_title = TitleLabel(self.get_text("history_stats") or "历史统计")
        stats_title.setObjectName("historyTitle")
        stats_layout.addWidget(stats_title)

        # 统计信息
        history_size = self.download_history.get_history_size() if self.download_history else 0

        # 文件数量显示
        count_row = QHBoxLayout()
        count_icon = IconWidget(FluentIcon.DOCUMENT)
        count_icon.setFixedSize(24, 24)
        self.historyCountLabel = SubtitleLabel(self.get_text("files_recorded", history_size) or f"已记录文件数: {history_size}")
        self.historyCountLabel.setObjectName("historyCount")

        count_row.addWidget(count_icon)
        count_row.addWidget(self.historyCountLabel)
        count_row.addStretch()

        stats_layout.addLayout(count_row)

        # 历史文件位置标签（固定显示）
        self.historyLocationLabel = CaptionLabel("")
        self.historyLocationLabel.setWordWrap(True)
        self.historyLocationLabel.setStyleSheet(
            "QLabel { background-color: rgba(255, 255, 255, 0.05); padding: 8px; border-radius: 4px; }")
        stats_layout.addWidget(self.historyLocationLabel)

        # 根据是否有历史记录来更新位置标签
        if history_size > 0 and self.download_history:
            history_file = self.download_history.history_file
            self.historyLocationLabel.setText(self.get_text("history_file_location", history_file) or f"历史文件位置: {history_file}")
            self.historyLocationLabel.show()
        else:
            self.historyLocationLabel.hide()

        # 操作按钮行
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setContentsMargins(0, 10, 0, 0)

        # 创建历史记录菜单
        self.historyMenu = RoundMenu(parent=self)
        
        # 获取所有可用的记录类型
        if self.download_history and hasattr(self.download_history, "get_record_types"):
            # 添加"清除所有历史"选项
            self.historyMenu.addAction(Action(FluentIcon.DELETE, self.get_text("all_history"), triggered=lambda: self._clearHistoryByType("all")))
            
            # 添加分隔线
            self.historyMenu.addSeparator()
            
            # 添加各类型历史记录选项
            record_types = self.download_history.get_record_types()
            for record_type in record_types:
                # 获取每种类型的记录数量
                records_count = self.download_history.get_history_size(record_type)
                if records_count > 0:
                    # 首字母大写，并添加记录数
                    display_name = f"{record_type.capitalize()} ({records_count})"
                    # 使用固定参数值创建函数，避免闭包问题
                    def create_callback(rt=record_type):
                        return lambda: self._clearHistoryByType(rt)
                    self.historyMenu.addAction(Action(FluentIcon.DELETE, display_name, triggered=create_callback()))

        # 清除历史按钮（始终显示）
        self.clearHistoryButton = PrimaryDropDownPushButton(FluentIcon.DELETE, self.get_text("clear_history") or "清除历史")
        self.clearHistoryButton.setFixedHeight(40)
        self.clearHistoryButton.setMenu(self.historyMenu)
        button_layout.addWidget(self.clearHistoryButton)

        # 查看历史文件按钮（根据条件显示）
        self.viewHistoryButton = PushButton(FluentIcon.VIEW, self.get_text("view_history_file") or "查看历史文件")
        self.viewHistoryButton.setFixedHeight(40)
        self.viewHistoryButton.clicked.connect(self._viewHistoryFile)
        button_layout.addWidget(self.viewHistoryButton)

        # 根据是否有历史记录来显示/隐藏查看按钮
        if history_size > 0:
            self.viewHistoryButton.show()
        else:
            self.viewHistoryButton.hide()

        button_layout.addStretch()
        stats_layout.addLayout(button_layout)

        content_layout.addWidget(stats_card)

        # 历史记录概览卡片（固定结构）
        self.historyOverviewCard = CardWidget()
        self.historyOverviewCard.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # 关键：自适应宽度
        self.historyOverviewCard.setMaximumHeight(120)
        overview_layout = QVBoxLayout(self.historyOverviewCard)
        overview_layout.setContentsMargins(20, 15, 20, 15)

        overview_title = StrongBodyLabel(self.get_text("history_overview") or "历史概览")
        overview_layout.addWidget(overview_title)

        self.historyStatsLabel = CaptionLabel("")
        overview_layout.addWidget(self.historyStatsLabel)

        # 添加弹性空间
        overview_layout.addStretch()

        content_layout.addWidget(self.historyOverviewCard)

        # 更新历史概览信息
        self.updateHistoryOverview(history_size)

        # 日志区域
        log_card = CardWidget()
        log_card.setFixedHeight(300)

        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(20, 10, 20, 15)
        log_layout.setSpacing(10)

        log_title = StrongBodyLabel(self.get_text("recent_activity") or "最近活动")
        log_layout.addWidget(log_title)

        self.logText = TextEdit()
        self.logText.setReadOnly(True)
        self.logText.setFixedHeight(220)
        log_layout.addWidget(self.logText)

        content_layout.addWidget(log_card)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.logHandler = LogHandler(self.logText)
        
    def _clearHistory(self):
        """清除历史记录"""
        # 如果有父窗口并且它实现了clearHistory方法，则调用父窗口的方法
        if self._parent_window and hasattr(self._parent_window, 'clearHistory'):
            self._parent_window.clearHistory()
        else:
            # 如果父窗口不可用，则在此实现清除逻辑
            if not self.download_history:
                if hasattr(self, 'logHandler'):
                    self.logHandler.error(self.get_text("history_not_available"))
                return
                
            # 创建下拉菜单对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle(self.get_text("clear_history"))
            layout = QVBoxLayout(dialog)
            
            # 添加提示文本
            label = QLabel(self.get_text("select_history_type_to_clear"))
            layout.addWidget(label)
            
            # 添加下拉菜单
            combo = QComboBox()
            combo.addItem(self.get_text("all_history"), "all")
            
            # 获取所有可用的记录类型
            if hasattr(self.download_history, "get_record_types"):
                record_types = self.download_history.get_record_types()
                for record_type in record_types:
                    # 获取每种类型的记录数量
                    records_count = self.download_history.get_history_size(record_type)
                    if records_count > 0:
                        # 首字母大写，并添加记录数
                        display_name = f"{record_type.capitalize()} ({records_count})"
                        combo.addItem(display_name, record_type)
            
            layout.addWidget(combo)
            
            # 添加确认/取消按钮
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            # 显示对话框
            result = dialog.exec()
            
            # 如果用户点击了确定
            if result == QDialog.Accepted:
                selected_type = combo.currentData()
                
                try:
                    # 清除历史记录
                    if selected_type == "all":
                        self.download_history.clear_history()
                        message = self.get_text("all_history_cleared")
                    else:
                        self.download_history.clear_history(selected_type)
                        message = self.get_text("history_type_cleared").format(selected_type.capitalize())
                    
                    # 刷新界面
                    self.refreshHistoryInterfaceAfterClear()
                    
                    # 显示成功消息
                    if hasattr(self, 'logHandler'):
                        self.logHandler.success(message)
                    
                    # 显示通知
                    from qfluentwidgets import InfoBar, InfoBarPosition
                    from PyQt5.QtCore import Qt
                    
                    InfoBar.success(
                        title=self.get_text("success"),
                        content=message,
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                    
                except Exception as e:
                    # 显示错误消息
                    error_message = f"{self.get_text('clear_history_failed')}: {str(e)}"
                    if hasattr(self, 'logHandler'):
                        self.logHandler.error(error_message)
                    
                    from qfluentwidgets import InfoBar, InfoBarPosition
                    from PyQt5.QtCore import Qt
                    
                    InfoBar.error(
                        title=self.get_text("error"),
                        content=error_message,
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                    
    def _clearHistoryByType(self, record_type: str):
        """根据类型清除提取历史记录
        
        Args:
            record_type: 要清除的记录类型，'all'表示清除所有记录
        """
        if not self.download_history:
            if hasattr(self, 'logHandler'):
                self.logHandler.error(self.get_text("history_not_available"))
            return
            
        try:
            # 清除历史记录
            if record_type == "all":
                self.download_history.clear_history()
                message = self.get_text("all_history_cleared")
            else:
                # 确保record_type是字符串类型
                record_type_str = str(record_type)
                self.download_history.clear_history(record_type_str)
                message = self.get_text("history_type_cleared").format(record_type_str.capitalize())
            
            # 刷新界面
            self.refreshHistoryInterfaceAfterClear()
            
            # 显示成功消息
            if hasattr(self, 'logHandler'):
                self.logHandler.success(message)
            
            # 显示通知
            from qfluentwidgets import InfoBar, InfoBarPosition
            from PyQt5.QtCore import Qt
            
            InfoBar.success(
                title=self.get_text("success"),
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            
        except Exception as e:
            # 显示错误消息
            error_message = f"{self.get_text('clear_history_failed')}: {str(e)}"
            if hasattr(self, 'logHandler'):
                self.logHandler.error(error_message)
            
            from qfluentwidgets import InfoBar, InfoBarPosition
            from PyQt5.QtCore import Qt
            
            InfoBar.error(
                title=self.get_text("error"),
                content=error_message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
                    
    def _viewHistoryFile(self):
        """查看历史文件"""
        if self.download_history and self.download_history.history_file:
            history_dir = os.path.dirname(self.download_history.history_file)
            open_directory(history_dir)
        
    def updateHistoryOverview(self, history_size, record_counts=None):
        """更新历史概览信息
        
        Args:
            history_size: 历史记录总数
            record_counts: 不同类型历史记录的计数字典
        """
        if history_size > 0:
            avg_files = history_size // max(1, history_size // 50)
            try:
                file_size = os.path.getsize(self.download_history.history_file) / 1024 if self.download_history else 0
            except:
                file_size = 0

            # 构建统计信息
            total_files_text = self.get_text('total_files', history_size) or f"总文件数: {history_size}"
            avg_files_text = self.get_text('avg_files_per_extraction', avg_files) or f"每次提取平均文件数: {avg_files}"
            file_size_text = self.get_text('history_file_size', f"{file_size:.1f}") or f"历史文件大小: {file_size:.1f} KB"
            
            stats_info = f"""
• {total_files_text}
• {avg_files_text}
• {file_size_text}
            """
            
            # 如果有不同类型的历史记录，显示详情
            if record_counts and len(record_counts) > 1:
                type_stats = []
                for record_type, count in record_counts.items():
                    if count > 0:
                        type_text = self.get_text(f'{record_type}_files', count) or f"{record_type.capitalize()}文件: {count}"
                        type_stats.append(f"• {type_text}")
                
                if type_stats:
                    stats_info += "\n" + "\n".join(type_stats)
            
            self.historyStatsLabel.setText(stats_info.strip())
            self.historyOverviewCard.show()
        else:
            self.historyOverviewCard.hide()
            
    def refreshHistoryInterface(self):
        """刷新历史界面显示"""
        try:
            # 获取最新的历史记录数量
            history_size = self.download_history.get_history_size() if self.download_history else 0
            
            # 获取不同类型的历史记录数量
            record_counts = {}
            if self.download_history and hasattr(self.download_history, 'get_record_types'):
                record_types = self.download_history.get_record_types()
                for record_type in record_types:
                    count = self.download_history.get_history_size(record_type)
                    if count > 0:
                        record_counts[record_type] = count

            # 更新计数显示
            if hasattr(self, 'historyCountLabel'):
                count_text = self.get_text("files_recorded", history_size) or f"已记录文件数: {history_size}"
                # 如果有多种类型的记录，添加详细信息
                if len(record_counts) > 1:
                    details = []
                    for record_type, count in record_counts.items():
                        details.append(f"{record_type.capitalize()}: {count}")
                    count_text += f" ({', '.join(details)})"
                
                self.historyCountLabel.setText(count_text)

            # 更新位置标签
            if hasattr(self, 'historyLocationLabel'):
                if history_size > 0 and self.download_history:
                    history_file = self.download_history.history_file
                    self.historyLocationLabel.setText(self.get_text("history_file_location", history_file) or f"历史文件位置: {history_file}")
                    self.historyLocationLabel.show()
                else:
                    self.historyLocationLabel.hide()

            # 更新查看按钮的显示/隐藏
            if hasattr(self, 'viewHistoryButton'):
                if history_size > 0:
                    self.viewHistoryButton.show()
                else:
                    self.viewHistoryButton.hide()

            # 更新概览信息
            if hasattr(self, 'updateHistoryOverview'):
                self.updateHistoryOverview(history_size, record_counts)

        except Exception as e:
            print(f"刷新历史界面时出错: {e}")
        
    def setHistoryStyles(self):
        """设置历史界面样式"""
        if not self.config_manager:
            return
            
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            self.setStyleSheet("""
                #historyTitle {
                    color: rgb(0, 0, 0);
                    font-size: 24px;
                    font-weight: bold;
                }
                #historyCount {
                    color: rgb(0, 120, 215);
                    font-size: 20px;
                    font-weight: 600;
                }
            """)
        else:
            self.setStyleSheet("""
                #historyTitle {
                    color: rgb(255, 255, 255);
                    font-size: 24px;
                    font-weight: bold;
                }
                #historyCount {
                    color: rgb(0, 212, 255);
                    font-size: 20px;
                    font-weight: 600;
                }
            """)
            
    def refreshHistoryInterfaceAfterClear(self):
        """清除历史后刷新界面"""
        try:
            # 重新加载历史数据
            if self.download_history:
                self.download_history.load_history()
            # 刷新界面
            self.refreshHistoryInterface()
        except Exception as e:
            print(f"清除历史后刷新界面时出错: {e}") 