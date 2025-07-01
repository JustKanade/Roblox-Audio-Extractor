from PyQt5.QtCore import pyqtSignal, Qt, QThread, QUrl, QSize, QPoint, QPropertyAnimation, QEasingCurve, QEvent
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog, QApplication,
    QMessageBox, QSizePolicy, QCheckBox, QPushButton, QDesktopWidget,
    QDialogButtonBox, QFrame, QTextEdit, QGraphicsDropShadowEffect
)
from PyQt5.QtGui import QDesktopServices, QColor, QFont, QPainter, QPainterPath, QBrush
import requests
import json
import os
import logging
import time

# 导入Qt常量
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractScrollArea

# 导入PyQt-Fluent-Widgets
from qfluentwidgets import (
    CardWidget, SettingCard, SwitchButton, PushButton, 
    InfoBar, InfoBarPosition, FluentIcon, SwitchSettingCard,
    StrongBodyLabel, BodyLabel, TextEdit, TitleLabel, Dialog,
    MessageBox, SubtitleLabel, PrimaryPushButton, IconWidget,
    ScrollArea, SimpleCardWidget, TransparentToolButton,
    isDarkTheme, setFont
)

# 导入MaskDialogBase
try:
    from qfluentwidgets.components.dialog_box.mask_dialog_base import MaskDialogBase
except ImportError:
    try:
        from qfluentwidgets import MaskDialogBase
    except ImportError:
        print("警告：无法导入 MaskDialogBase，版本检测功能可能无法正常工作")
        # 创建一个简单的替代类
        class MaskDialogBase(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.widget = QWidget(self)
                layout = QVBoxLayout(self)
                layout.addWidget(self.widget)
            
            def setMaskColor(self, color):
                pass
                
            def setShadowEffect(self, blurRadius=0, offset=(0, 0), color=None):
                pass

# 全局语言管理器引用，在主程序中初始化
lang = None

# 默认翻译，如果lang未初始化时使用
DEFAULT_TRANSLATIONS = {
    "version_check_settings": "版本检测设置",
    "auto_check_update": "启动时自动检测更新",
    "check_update_now": "立即检查更新",
    "checking_update": "正在检查更新...",
    "latest_version": "最新版本: {}",
    "current_version": "当前版本: {}",
    "update_available": "有新版本可用！",
    "already_latest": "已是最新版本",
    "check_failed": "检查更新失败: {}",
    "release_notes": "更新内容",
    "go_to_update": "前往更新",
    "close": "关闭"
}

logger = logging.getLogger(__name__)

def get_text(key, *args):
    """获取翻译文本，如果lang未初始化则使用默认值"""
    if lang and hasattr(lang, 'get'):
        text = lang.get(key)
        if text is not None and args:
            try:
                return text.format(*args)
            except:
                return text
        return text
    if args:
        try:
            text = DEFAULT_TRANSLATIONS.get(key, key)
            if text is not None:
                return text.format(*args)
            return key
        except Exception:
            return DEFAULT_TRANSLATIONS.get(key, key)
    return DEFAULT_TRANSLATIONS.get(key, key)

class UpdateDialog(MaskDialogBase):

    
    def __init__(self, title, version, release_notes, release_url, parent=None):
        """初始化更新对话框
        
        Args:
            title: 对话框标题
            version: 最新版本号
            release_notes: 更新内容
            release_url: 更新链接
            parent: 父窗口
        """
        super(UpdateDialog, self).__init__(parent)
        
        # 保存必要的数据
        self.release_url = release_url
        self.release_notes = release_notes
        self.version = version
        self.title = title
        
        # 设置窗口属性
        self.setWindowTitle(title)
        self.setMaskColor(QColor(0, 0, 0, 120))  # 半透明黑色蒙版
        
        # 创建对话框内容
        self.setupUI()
        
        # 添加漂亮的阴影效果
        self.setShadowEffect(blurRadius=40, offset=(0, 6), color=QColor(0, 0, 0, 60))
    
    def setupUI(self):
        """设置对话框UI"""
        # 获取对话框的内容区域
        self.widget.setFixedWidth(520)
        self.widget.setMinimumHeight(480)
        
        # 设置边框圆角和样式
        if isDarkTheme():
            self.widget.setStyleSheet("""
                background-color: #2b2b2b;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            """)
            text_color = "#ffffff"
            secondary_color = "rgba(255, 255, 255, 0.65)"
            card_bg = "#363636"
            separator_color = "rgba(255, 255, 255, 0.1)"
        else:
            self.widget.setStyleSheet("""
                background-color: white;
                border-radius: 10px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            """)
            text_color = "#202020"
            secondary_color = "rgba(0, 0, 0, 0.65)"
            card_bg = "#f5f5f5"
            separator_color = "rgba(0, 0, 0, 0.08)"
        
        # 创建主布局
        self.mainLayout = QVBoxLayout(self.widget)
        self.mainLayout.setContentsMargins(24, 20, 24, 24)
        self.mainLayout.setSpacing(16)
        
        # === 标题栏区域 ===
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(12)
        
        # 添加标题图标
        icon = IconWidget(FluentIcon.UPDATE, self.widget)
        icon.setFixedSize(28, 28)
        
        # 标题文本
        titleLabel = TitleLabel(self.title, self.widget)
        titleLabel.setStyleSheet(f"color: {text_color}; font-weight: bold;")
        
        # 关闭按钮
        closeBtn = TransparentToolButton(FluentIcon.CLOSE, self.widget)
        closeBtn.setFixedSize(32, 32)
        closeBtn.setIconSize(QSize(16, 16))
        closeBtn.clicked.connect(self.reject)
        
        header.addWidget(icon)
        header.addWidget(titleLabel, 1)
        header.addWidget(closeBtn)
        
        self.mainLayout.addLayout(header)
        
        # === 版本信息区域 ===
        versionInfo = QHBoxLayout()
        versionInfo.setContentsMargins(0, 4, 0, 4)
        
        # 获取主题色
        themeColor = self._getThemeColor()
        
        # 最新版本标签
        versionLabel = StrongBodyLabel(get_text("latest_version", self.version))
        versionLabel.setStyleSheet(f"color: {themeColor.name()};")
        
        versionInfo.addWidget(versionLabel)
        versionInfo.addStretch()
        
        self.mainLayout.addLayout(versionInfo)
        
        # === 更新内容标题区域 ===
        notesHeader = QHBoxLayout()
        notesHeader.setContentsMargins(0, 12, 0, 8)  # 增加上边距，替代分隔线的视觉效果
        notesHeader.setSpacing(8)
        
        # 添加图标
        noteIcon = IconWidget(FluentIcon.DOCUMENT, self.widget)
        noteIcon.setFixedSize(16, 16)
        
        # 更新内容标题
        notesTitle = SubtitleLabel(get_text("release_notes"))
        
        notesHeader.addWidget(noteIcon)
        notesHeader.addWidget(notesTitle)
        notesHeader.addStretch()
        
        self.mainLayout.addLayout(notesHeader)
        
        # === 更新内容卡片 ===
        contentCard = SimpleCardWidget(self.widget)
        contentCard.setBorderRadius(8)
        contentCard.setStyleSheet(f"""
            background-color: {card_bg};
            border-radius: 8px;
            border: none;
        """)
        
        contentLayout = QVBoxLayout(contentCard)
        contentLayout.setContentsMargins(16, 16, 16, 16)
        
        # 格式化并显示更新内容
        self.notesEdit = TextEdit(contentCard)
        self.notesEdit.setReadOnly(True)
        self.notesEdit.setText(self._formatReleaseNotes(self.release_notes))
        self.notesEdit.setStyleSheet(f"""
            border: none;
            background-color: transparent;
            color: {text_color};
            selection-background-color: {themeColor.name()};
        """)
        self.notesEdit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.notesEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.notesEdit.setMinimumHeight(200)
        
        # 设置文档边距为0
        try:
            document = self.notesEdit.document()
            if document:
                document.setDocumentMargin(0)
        except:
            pass
        
        contentLayout.addWidget(self.notesEdit)
        
        self.mainLayout.addWidget(contentCard, 1)  # 添加伸展因子，使内容区域可伸缩
        
        # === 按钮区域 ===
        buttonLayout = QHBoxLayout()
        buttonLayout.setContentsMargins(0, 8, 0, 0)
        buttonLayout.setSpacing(12)
        
        # 取消按钮
        self.cancelButton = PushButton(get_text("close"))
        self.cancelButton.clicked.connect(self.reject)
        
        # 更新按钮
        self.updateButton = PrimaryPushButton(get_text("go_to_update"))
        self.updateButton.setIcon(FluentIcon.LINK)
        self.updateButton.clicked.connect(self.openUpdateUrl)
        
        # 调整按钮大小
        self.cancelButton.setMinimumWidth(100)
        self.updateButton.setMinimumWidth(140)
        
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.updateButton)
        
        self.mainLayout.addLayout(buttonLayout)
    
    def _getThemeColor(self):
        """获取主题颜色"""
        try:
            # 尝试使用qfluentwidgets的主题色
            try:
                from qfluentwidgets import themeColor
                return themeColor()
            except (ImportError, AttributeError):
                pass
                
            # 默认蓝色
            return QColor(0, 120, 212)
        except:
            return QColor(0, 120, 212)
    
    def _formatReleaseNotes(self, notes):
        """格式化发布说明内容，使其更美观"""
        if not notes:
            return ""
            
        # 替换Markdown标题为大写粗体文本
        formatted = notes
        
        # 确保每个项目符号前后有足够的空间
        formatted = formatted.replace("\n- ", "\n\n- ")
        
        # 确保段落之间有足够的空间
        formatted = formatted.replace("\n\n\n", "\n\n")
        
        # 处理Markdown标题
        lines = formatted.split("\n")
        result = []
        
        for line in lines:
            if line.startswith("## "):
                result.append("\n" + line.replace("## ", "").upper() + "\n")
            elif line.startswith("# "):
                result.append("\n" + line.replace("# ", "").upper() + "\n")
            else:
                result.append(line)
                
        return "\n".join(result)
    
    def openUpdateUrl(self):
        """打开更新链接"""
        QDesktopServices.openUrl(QUrl(self.release_url))
        self.accept()

class VersionCheckerThread(QThread):
    """版本检查线程"""
    version_checked = pyqtSignal(dict)
    check_failed = pyqtSignal(str)
    
    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
        self.repo_url = "https://api.github.com/repos/JustKanade/Roblox-Audio-Extractor/releases/latest"
        self.max_retries = 3  # 最大重试次数
        
        # 请求头，避免GitHub API速率限制
        self.headers = {
            'User-Agent': f'Roblox-Audio-Extractor/{current_version}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def run(self):
        """运行版本检查"""
        # 添加一个小延迟，让UI有时间显示"正在检查"状态
        time.sleep(0.5)
        
        retries = 0
        while retries < self.max_retries:
            try:
                # 通过GitHub API获取最新版本信息
                response = requests.get(self.repo_url, headers=self.headers, timeout=10)
                
                # 检查是否遇到速率限制
                if response.status_code == 403 and 'X-RateLimit-Remaining' in response.headers:
                    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                    if remaining == 0:
                        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                        current_time = int(time.time())
                        wait_time = max(0, reset_time - current_time)
                        
                        if wait_time > 0 and retries < self.max_retries - 1:
                            logger.warning(f"GitHub API速率限制，将在{wait_time}秒后重试...")
                            time.sleep(min(wait_time, 30))  # 最多等待30秒
                            retries += 1
                            continue
                        else:
                            error_msg = "GitHub API速率限制，请稍后再试"
                            logger.error(error_msg)
                            self.check_failed.emit(error_msg)
                            return
                
                # 处理其他HTTP错误
                response.raise_for_status()
                
                data = response.json()
                latest_version = data['tag_name'].lstrip('v')  # 删除版本号前的'v'前缀
                
                # 返回版本信息
                result = {
                    'latest_version': latest_version,
                    'current_version': self.current_version,
                    'has_update': self._compare_versions(self.current_version, latest_version),
                    'release_url': data['html_url'],
                    'release_notes': data['body']
                }
                self.version_checked.emit(result)
                return
                
            except requests.exceptions.RequestException as e:
                retries += 1
                if retries >= self.max_retries:
                    error_msg = f"网络请求失败: {str(e)}"
                    logger.error(error_msg)
                    self.check_failed.emit(error_msg)
                    return
                else:
                    # 重试前等待（采用指数退避策略）
                    wait_time = 2 ** retries
                    logger.warning(f"请求失败，{wait_time}秒后重试 ({retries}/{self.max_retries})...")
                    time.sleep(wait_time)
            
            except Exception as e:
                error_msg = f"版本检查失败: {str(e)}"
                logger.error(error_msg)
                self.check_failed.emit(error_msg)
                return
    
    def _compare_versions(self, current, latest):
        """比较版本号，如果有更新返回True"""
        try:
            # 分割版本号
            current_parts = list(map(int, current.split('.')))
            latest_parts = list(map(int, latest.split('.')))
            
            # 确保版本号列表长度相同
            while len(current_parts) < len(latest_parts):
                current_parts.append(0)
            while len(latest_parts) < len(current_parts):
                latest_parts.append(0)
            
            # 逐位比较
            for i in range(len(current_parts)):
                if latest_parts[i] > current_parts[i]:
                    return True
                elif latest_parts[i] < current_parts[i]:
                    return False
            
            # 版本号完全相同
            return False
            
        except Exception as e:
            logger.error(f"版本比较错误: {str(e)}")
            return False

def createSeparator(parent=None):
    """创建分隔线"""
    separator = QFrame(parent)
    separator.setFrameShape(QFrame.HLine)
    separator.setFrameShadow(QFrame.Sunken)
    separator.setStyleSheet("background-color: rgba(200, 200, 200, 0.3); margin: 0px 0px; height: 1px;")
    return separator

class VersionCheckCard(QWidget):
    """版本检测设置卡片"""
    
    def __init__(self, config_manager, current_version, parent=None):
        """初始化版本检测卡片
        
        Args:
            config_manager: 配置管理器实例
            current_version: 当前应用版本
            parent: 父控件
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.current_version = current_version
        
        # 从配置中读取设置
        self.auto_check = self.config_manager.get("auto_check_update", True)
        
        # 初始化界面
        self.setupFluentUI()
        
        # 如果设置了自动检查，则启动时检查更新
        if self.auto_check:
            self.checkUpdate()
    
    def setupFluentUI(self):
        """使用 PyQt-Fluent-Widgets 设置界面"""
        # 创建新布局前删除所有现有子控件
        for child in self.children():
            if isinstance(child, QWidget):
                child.deleteLater()
        
        # 创建新布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 确定主题颜色
        if hasattr(isDarkTheme, '__call__') and isDarkTheme():
            # 深色主题
            text_color = "#ffffff"
            secondary_text_color = "rgba(255, 255, 255, 0.6)"
            separator_color = "rgba(255, 255, 255, 0.1)"
        else:
            # 浅色主题
            text_color = "#333333"
            secondary_text_color = "rgba(0, 0, 0, 0.6)"
            separator_color = "rgba(0, 0, 0, 0.1)"
        
        # 创建主卡片
        main_card = CardWidget(self)
        main_card.setBorderRadius(8)
        
        # 设置卡片样式，确保没有多余边框
        main_card.setStyleSheet("""
            border: none;
        """)
        
        main_card_layout = QVBoxLayout(main_card)
        main_card_layout.setContentsMargins(20, 15, 20, 20)
        main_card_layout.setSpacing(12)
        
        # 标题区域
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        
        # 添加标题图标
        title_icon = IconWidget(FluentIcon.SETTING, main_card)
        title_icon.setFixedSize(20, 20)
        
        # 标题文本
        title_label = StrongBodyLabel(get_text("version_check_settings"), main_card)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        main_card_layout.addLayout(title_layout)
        
        # 自动检测更新选项
        auto_check_container = QWidget(main_card)
        auto_check_layout = QHBoxLayout(auto_check_container)
        auto_check_layout.setContentsMargins(0, 0, 0, 0)
        auto_check_layout.setSpacing(10)
        
        # 添加图标
        auto_icon = IconWidget(FluentIcon.UPDATE, auto_check_container)
        auto_icon.setFixedSize(16, 16)
        
        # 添加文本
        auto_check_label = BodyLabel(get_text("auto_check_update"), auto_check_container)
        
        # 添加开关
        self.auto_check_switch = SwitchButton(auto_check_container)
        self.auto_check_switch.setChecked(self.auto_check)
        self.auto_check_switch.checkedChanged.connect(self.onAutoCheckChanged)
        
        auto_check_layout.addWidget(auto_icon)
        auto_check_layout.addWidget(auto_check_label)
        auto_check_layout.addStretch()
        auto_check_layout.addWidget(self.auto_check_switch)
        
        main_card_layout.addWidget(auto_check_container)
        
        # 版本信息区域
        version_info_container = QWidget(main_card)
        version_info_layout = QHBoxLayout(version_info_container)
        version_info_layout.setContentsMargins(0, 8, 0, 8)
        version_info_layout.setSpacing(10)
        
        # 添加版本信息图标
        version_icon = IconWidget(FluentIcon.TAG, version_info_container)
        version_icon.setFixedSize(16, 16)
        
        # 版本信息标签
        self.version_label = BodyLabel(get_text("current_version", self.current_version), version_info_container)
        self.version_label.setStyleSheet(f"color: {secondary_text_color};")
        
        version_info_layout.addWidget(version_icon)
        version_info_layout.addWidget(self.version_label)
        version_info_layout.addStretch()
        
        main_card_layout.addWidget(version_info_container)
        
        # 检查更新按钮区域
        button_container = QWidget(main_card)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.setSpacing(10)
        
        # 立即检查更新按钮
        self.check_now_button = PrimaryPushButton(get_text("check_update_now"), button_container)
        self.check_now_button.setIcon(FluentIcon.SYNC)
        self.check_now_button.clicked.connect(self.checkUpdate)
        self.check_now_button.setMinimumWidth(140)  # 设置最小宽度，使按钮更美观
        
        button_layout.addStretch()
        button_layout.addWidget(self.check_now_button)
        
        main_card_layout.addWidget(button_container)
        
        # 将主卡片添加到布局
        layout.addWidget(main_card)

    def onAutoCheckChanged(self, checked):
        """自动检查设置改变的响应函数"""
        self.auto_check = checked
        self.config_manager.set("auto_check_update", checked)
    
    def checkUpdate(self):
        """检查更新"""
        # 禁用检查按钮，避免重复点击
        self.check_now_button.setEnabled(False)
        self.check_now_button.setText(get_text("checking_update"))
        
        # 创建并启动检查线程
        self.checker_thread = VersionCheckerThread(self.current_version)
        self.checker_thread.version_checked.connect(self.onVersionChecked)
        self.checker_thread.check_failed.connect(self.onCheckFailed)
        self.checker_thread.finished.connect(self.onCheckFinished)
        self.checker_thread.start()
    
    def onVersionChecked(self, result):
        """版本检查完成的响应函数"""
        # 更新版本信息标签
        self.version_label.setText(
            f"{get_text('current_version', self.current_version)} | "
            f"{get_text('latest_version', result['latest_version'])}"
        )
        
        # 获取主窗口实例
        main_window = self.window()
        
        # 如果有更新，显示提示
        if result['has_update']:
            # 使用自定义对话框显示更新信息和下载链接
            dialog = UpdateDialog(
                get_text("update_available"),
                result['latest_version'],
                result['release_notes'],
                result['release_url'],
                main_window
            )
            dialog.exec_()
        else:
            # 使用InfoBar显示已是最新版本的消息
            InfoBar.success(
                title=get_text("already_latest"),
                content=f"{get_text('current_version', self.current_version)}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=main_window  # 使用主窗口作为父控件
            )
    
    def onCheckFailed(self, error_msg):
        """版本检查失败的响应函数"""
        # 获取主窗口实例
        main_window = self.window()
        
        # 准备错误信息和解决方案提示
        display_msg = error_msg
        
        # 针对不同错误类型提供更具体的解决方案
        if "速率限制" in error_msg or "API rate limit" in error_msg:
            display_msg = (
                f"{error_msg}\n\n"
                f"解决方案:\n"
                f"1. 稍后再试\n"
                f"2. 设置环境变量 SKIP_UPDATE_CHECK=1 可跳过更新检查\n"
                f"3. 在配置中关闭自动检查更新"
            )
        elif "timeout" in error_msg.lower():
            display_msg = (
                f"{error_msg}\n\n"
                f"连接超时，请检查您的网络连接或代理设置"
            )
        
        # 使用InfoBar显示在顶部
        InfoBar.error(
            title=get_text("check_failed", ""),
            content=display_msg,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=8000,  # 增加显示时间，让用户有足够时间阅读解决方案
            parent=main_window  # 使用主窗口作为父控件
        )
    
    def onCheckFinished(self):
        """版本检查线程完成的响应函数"""
        # 恢复检查按钮
        self.check_now_button.setEnabled(True)
        self.check_now_button.setText(get_text("check_update_now")) 
