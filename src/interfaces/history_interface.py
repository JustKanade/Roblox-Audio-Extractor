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
    DropDownPushButton, PrimaryDropDownPushButton, ComboBox,
    SettingCardGroup, SettingCard, SwitchSettingCard, LineEdit, PushSettingCard
)

import os
from src.utils.file_utils import open_directory
from src.utils.log_utils import LogHandler
from src.extractors.audio_extractor import ExtractedHistory

# 尝试导入LogControlCard
try:
    from src.components.cards.Settings.log_control_card import LogControlCard
except ImportError:
    LogControlCard = None

# 导入中央日志处理器
from src.logging.central_log_handler import CentralLogHandler


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

        # 创建历史信息设置卡片组
        history_info_group = SettingCardGroup(self.get_text("history_info", "历史信息"))
        
        # 历史统计信息卡片
        self.history_stats_card = PushSettingCard(
            self.get_text("refresh_statistics", "刷新统计"),
            FluentIcon.PIE_SINGLE,
            self.get_text("history_statistics", "历史统计"),
            self.get_text("history_statistics_desc", "显示提取历史记录的统计信息")
        )
        
        # 获取历史记录数量并更新卡片内容
        history_size = self.download_history.get_history_size() if self.download_history else 0
        self._updateHistoryStatsCard(history_size)
        
        # 连接点击信号到刷新方法
        self.history_stats_card.clicked.connect(self._refreshHistoryStats)
        
        history_info_group.addSettingCard(self.history_stats_card)
        
        # 历史文件位置卡片
        self.history_location_card = SettingCard(
            FluentIcon.FOLDER,
            self.get_text("history_file_location_title", "历史文件位置"),
            self.get_text("history_file_location_desc", "历史记录文件的存储位置")
        )
        
        # 创建位置显示控件容器
        location_widget = QWidget()
        location_layout = QVBoxLayout(location_widget)
        location_layout.setContentsMargins(0, 0, 20, 0)
        location_layout.setSpacing(8)
        
        # 历史文件位置显示（延长路径显示）
        self.historyLocationEdit = LineEdit()
        self.historyLocationEdit.setReadOnly(True)
        self.historyLocationEdit.setClearButtonEnabled(False)
        self.historyLocationEdit.setPlaceholderText(self.get_text("history_file_path_placeholder", "历史文件路径"))
        # 设置更长的最小宽度以便完整显示较长路径
        self.historyLocationEdit.setMinimumWidth(400)
        self.historyLocationEdit.setMaximumWidth(1200)
        # 可选：设置字体为等宽字体，便于显示路径
        font = self.historyLocationEdit.font()
        font.setFamily("Consolas, Courier, monospace")
        self.historyLocationEdit.setFont(font)
        
        # 根据是否有历史记录来更新位置显示
        if history_size > 0 and self.download_history:
            history_file = self.download_history.history_file
            self.historyLocationEdit.setText(history_file)
        else:
            self.historyLocationEdit.setText(self.get_text("no_history_file", "暂无历史文件"))
        
        location_layout.addWidget(self.historyLocationEdit)
        
        # 将位置控件添加到卡片
        self.history_location_card.hBoxLayout.addWidget(location_widget)
        history_info_group.addSettingCard(self.history_location_card)
        
        # 快速操作卡片
        self.quick_actions_card = SettingCard(
            FluentIcon.COMMAND_PROMPT,
            self.get_text("quick_actions", "快速操作"),
            self.get_text("history_quick_actions_desc", "清除历史记录和查看历史文件")
        )
        
        # 创建快速操作控件容器
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 20, 0)
        actions_layout.setSpacing(10)
        
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

        # 清除历史按钮
        self.clearHistoryButton = PrimaryDropDownPushButton(FluentIcon.DELETE, self.get_text("clear_history") or "清除历史")
        self.clearHistoryButton.setFixedSize(160, 32)
        self.clearHistoryButton.setMenu(self.historyMenu)

        # 查看历史文件按钮
        self.viewHistoryButton = PushButton(FluentIcon.VIEW, self.get_text("view_history_file") or "查看历史文件")
        self.viewHistoryButton.setFixedSize(160, 32)
        self.viewHistoryButton.clicked.connect(self._viewHistoryFile)

        # 根据是否有历史记录来显示/隐藏查看按钮
        if history_size > 0:
            self.viewHistoryButton.show()
        else:
            self.viewHistoryButton.hide()

        actions_layout.addStretch()
        actions_layout.addWidget(self.clearHistoryButton)
        actions_layout.addWidget(self.viewHistoryButton)
        
        # 将快速操作控件添加到卡片
        self.quick_actions_card.hBoxLayout.addWidget(actions_widget)
        history_info_group.addSettingCard(self.quick_actions_card)
        
        # 日志管理卡片
        if LogControlCard:
            self.log_management_card = LogControlCard(
                parent=self,
                lang=self.lang,
                central_log_handler=CentralLogHandler.getInstance()
            )
            history_info_group.addSettingCard(self.log_management_card)
        
        content_layout.addWidget(history_info_group)

        # 操作控制卡片（保留用于显示概览信息）
        control_card = CardWidget()
        control_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(25, 20, 25, 20)
        control_layout.setSpacing(15)

        # 历史记录概览信息
        overview_title = StrongBodyLabel(self.get_text("history_overview") or "历史概览")
        control_layout.addWidget(overview_title)

        self.historyOverviewLabel = CaptionLabel("")
        self.historyOverviewLabel.setWordWrap(True)
        control_layout.addWidget(self.historyOverviewLabel)

        content_layout.addWidget(control_card)
        self.historyOverviewCard = control_card  # 保持兼容性

        # 更新历史概览信息
        self.updateHistoryOverview(history_size)

        # 日志区域
        log_card = CardWidget()
        log_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
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
        
        # 确保布局末尾有伸缩项，防止界面被拉伸
        content_layout.addStretch(1)

        # 设置滚动区域
        scroll.setWidget(content_widget)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # 创建日志处理器
        self.logHandler = LogHandler(self.logText)

    def _updateHistoryStatsCard(self, history_size):
        """更新历史统计卡片的内容"""
        if history_size > 0:
            # 获取不同类型的历史记录数量
            record_counts = {}
            if self.download_history and hasattr(self.download_history, 'get_record_types'):
                record_types = self.download_history.get_record_types()
                for record_type in record_types:
                    count = self.download_history.get_history_size(record_type)
                    if count > 0:
                        record_counts[record_type] = count
            
            # 构建详细描述
            desc_parts = [f"{self.get_text('total_records', '总记录数')}: {history_size}"]
            
            if len(record_counts) > 1:
                for record_type, count in record_counts.items():
                    type_name = self.get_text(f'{record_type}_records', record_type.capitalize())
                    desc_parts.append(f"{type_name}: {count}")
            
            # 计算文件大小
            try:
                file_size = os.path.getsize(self.download_history.history_file) / 1024 if self.download_history else 0
                desc_parts.append(f"{self.get_text('file_size', '文件大小')}: {file_size:.1f} KB")
            except:
                pass
            
            content_desc = " | ".join(desc_parts)
        else:
            content_desc = self.get_text("no_history_records", "暂无历史记录")
        
        # 更新卡片内容描述
        self.history_stats_card.setContent(content_desc)
    
    def _refreshHistoryStats(self):
        """刷新历史统计信息"""
        try:
            # 重新加载历史数据
            if self.download_history:
                self.download_history.load_history()
            
            # 获取最新的历史记录数量
            history_size = self.download_history.get_history_size() if self.download_history else 0
            
            # 更新统计卡片
            self._updateHistoryStatsCard(history_size)
            
            # 刷新整个界面
            self.refreshHistoryInterface()
            
            # 记录刷新操作
            if hasattr(self, 'logHandler'):
                self.logHandler.info(self.get_text("statistics_refreshed", "统计信息已刷新"))
        
        except Exception as e:
            if hasattr(self, 'logHandler'):
                self.logHandler.error(f"{self.get_text('refresh_failed', '刷新失败')}: {str(e)}")

    # 添加筛选类型变更事件处理
    def _onFilterTypeChanged(self, index):
        """处理筛选类型变更事件"""
        selected_type = self.recordTypeComboBox.currentData()
        if selected_type and hasattr(self, 'logHandler'):
            # 根据选择类型进行筛选显示
            if selected_type == "all":
                self.logHandler.info(self.get_text("showing_all_history_records") or "显示所有历史记录")
            else:
                self.logHandler.info(self.get_text("showing_filtered_records", selected_type.capitalize()) or f"显示 {selected_type.capitalize()} 历史记录")
                
            # 这里可以添加根据类型筛选显示记录的代码
            # 例如: self._updateRecordsDisplay(selected_type)
        
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
            total_files_text = self.get_text('total_files', history_size) or f"{self.get_text('total_records', '总记录数')}: {history_size}"
            avg_files_text = self.get_text('avg_files_per_extraction', avg_files) or f"{self.get_text('avg_files_per_extraction_label', '每次提取平均文件数')}: {avg_files}"
            file_size_text = self.get_text('history_file_size', f"{file_size:.1f}") or f"{self.get_text('file_size', '文件大小')}: {file_size:.1f} KB"
            
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
                        type_name = self.get_text(f'{record_type}_records', record_type.capitalize())
                        type_text = f"{type_name}{self.get_text('files_suffix', '文件')}: {count}"
                        type_stats.append(f"• {type_text}")
                
                if type_stats:
                    stats_info += "\n" + "\n".join(type_stats)
            
            self.historyOverviewLabel.setText(stats_info.strip())
            self.historyOverviewCard.show()
        else:
            self.historyOverviewCard.hide()
            
    def refreshHistoryInterface(self):
        """刷新历史界面显示"""
        try:
            # 获取最新的历史记录数量
            history_size = self.download_history.get_history_size() if self.download_history else 0
            
            # 更新统计卡片
            if hasattr(self, '_updateHistoryStatsCard'):
                self._updateHistoryStatsCard(history_size)

            # 更新位置显示
            if hasattr(self, 'historyLocationEdit'):
                if history_size > 0 and self.download_history:
                    history_file = self.download_history.history_file
                    self.historyLocationEdit.setText(history_file)
                else:
                    self.historyLocationEdit.setText(self.get_text("no_history_file", "暂无历史文件"))

            # 更新查看按钮的显示/隐藏
            if hasattr(self, 'viewHistoryButton'):
                if history_size > 0:
                    self.viewHistoryButton.show()
                else:
                    self.viewHistoryButton.hide()

            # 获取不同类型的历史记录数量
            record_counts = {}
            if self.download_history and hasattr(self.download_history, 'get_record_types'):
                record_types = self.download_history.get_record_types()
                for record_type in record_types:
                    count = self.download_history.get_history_size(record_type)
                    if count > 0:
                        record_counts[record_type] = count

            # 更新概览信息
            if hasattr(self, 'updateHistoryOverview'):
                self.updateHistoryOverview(history_size, record_counts)
                
            # 更新筛选下拉菜单（如果存在）
            if hasattr(self, 'recordTypeComboBox'):
                # 保存当前选择
                current_data = self.recordTypeComboBox.currentData()
                
                # 清空下拉菜单（除了"全部"选项）
                while self.recordTypeComboBox.count() > 1:
                    self.recordTypeComboBox.removeItem(1)
                
                # 重新添加可用的记录类型
                if self.download_history and hasattr(self.download_history, "get_record_types"):
                    record_types = self.download_history.get_record_types()
                    for record_type in record_types:
                        count = self.download_history.get_history_size(record_type)
                        if count > 0:
                            display_name = f"{record_type.capitalize()} ({count})"
                            self.recordTypeComboBox.addItem(display_name, record_type)
                
                # 尝试恢复先前的选择
                if current_data != "all":
                    # 寻找先前选择的索引
                    for i in range(self.recordTypeComboBox.count()):
                        if self.recordTypeComboBox.itemData(i) == current_data:
                            self.recordTypeComboBox.setCurrentIndex(i)
                            break

        except Exception as e:
            print(f"刷新历史界面时出错: {e}")
        
    def setHistoryStyles(self):
        """设置历史界面样式"""
        if not self.config_manager:
            return
            
        theme = self.config_manager.get("theme", "dark")

        if theme == "light":
            # 浅色模式样式
            text_color = "rgb(0, 0, 0)"
        else:
            # 深色模式样式
            text_color = "rgb(255, 255, 255)"
        
        # 设置日志文本编辑器样式
        if hasattr(self, 'logText'):
            self.logText.setStyleSheet(f"""
                TextEdit {{
                    font-family: Consolas, Courier, monospace;
                    color: {text_color};
                }}
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