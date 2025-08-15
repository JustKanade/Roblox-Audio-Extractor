from enum import Enum, auto

# 统一的版本号常量
VERSION = "0.17.2"

class Language(Enum):
    """支持的语言枚举类"""
    ENGLISH = auto()
    CHINESE = auto()

def get_translations():
    """返回包含所有翻译的字典"""
    ENGLISH = Language.ENGLISH
    CHINESE = Language.CHINESE
    
    return {
            # 语言设置相关
            "follow_system_language": {
                ENGLISH: "Follow System Settings",
                CHINESE: "跟随系统设置"
            },
            "simplified_chinese": {
                ENGLISH: "Simplified Chinese",
                CHINESE: "简体中文"
            },
            "english": {
                ENGLISH: "English",
                CHINESE: "English"
            },
            
            # 头像设置相关
            "avatar_settings": {
                CHINESE: "头像设置", 
                ENGLISH: "Avatar Settings"
            },
            "disable_avatar_auto_update": {
                CHINESE: "禁用侧边栏头像自动更新",
                ENGLISH: "Disable Sidebar Avatar Auto-Update"
            },
            "avatar_auto_update_tip": {
                CHINESE: "增快程序启动速度",
                ENGLISH: "Speed up program startup time"
            },
            
            # 问候语设置相关
            "greeting_setting": {
                CHINESE: "问候语设置",
                ENGLISH: "Greeting Settings"
            },
            "greeting_setting_description": {
                CHINESE: "启用或禁用程序启动时的问候通知",
                ENGLISH: "Enable or disable greeting notifications when the program starts."
            },
            
            # 亚克力效果设置相关
            "acrylic_effect": {
                CHINESE: "亚克力效果",
                ENGLISH: "Acrylic Effect"
            },
            "acrylic_effect_desc": {
                CHINESE: "控制导航栏的半透明亚克力效果",
                ENGLISH: "Control the semi-transparent acrylic effect of the navigation bar"
            },
            "acrylic_windows_only": {
                CHINESE: "注意：亚克力效果在 Windows 上效果最佳",
                ENGLISH: "Note: Acrylic effect works best on Windows"
            },
            
            # 云母效果设置相关
            "mica_effect": {
                CHINESE: "云母效果",
                ENGLISH: "Mica Effect"
            },
            "mica_effect_desc": {
                CHINESE: "为窗口背景应用半透明云母修材质效果",
                ENGLISH: "Apply semi-transparent mica material effect to window background"
            },
            "mica_effect_windows11_only": {
                CHINESE: "注意：云母效果仅在 Windows 11 上可用",
                ENGLISH: "Note: Mica effect is only available on Windows 11"
            },
            
            # 侧边栏展开设置相关
            "sidebar_expand_setting": {
                CHINESE: "侧边栏展开设置",
                ENGLISH: "Sidebar Expand Settings"
            },
            "sidebar_expand_setting_description": {
                CHINESE: "控制侧边栏是否总是保持展开状态",
                ENGLISH: "Control whether the sidebar is always kept in expanded state"
            },
            "sidebar_force_expand": {
                CHINESE: "强制侧边栏展开",
                ENGLISH: "Force Sidebar Expand"
            },
            "sidebar_expand_enabled": {
                CHINESE: "侧边栏已设置为总是展开",
                ENGLISH: "Sidebar set to always expand"
            },
            "sidebar_expand_disabled": {
                CHINESE: "侧边栏恢复可折叠状态",
                ENGLISH: "Sidebar restored to collapsible state"
            },
            "sidebar_expand_enabled_desc": {
                CHINESE: "侧边栏将不能被折叠，始终保持展开状态",
                ENGLISH: "Sidebar cannot be collapsed and will always remain expanded"
            },
            "sidebar_expand_disabled_desc": {
                CHINESE: "侧边栏可以通过菜单按钮进行折叠和展开",
                ENGLISH: "Sidebar can be collapsed and expanded using the menu button"
            },
            
            "enabled": {
                CHINESE: "已启用",
                ENGLISH: "Enabled"
            },
            "disabled": {
                CHINESE: "已禁用", 
                ENGLISH: "Disabled"
            },
            
            "greeting_enabled": {
                CHINESE: "问候语已启用",
                ENGLISH: "Greetings Enabled"
            },
            "greeting_disabled": {
                CHINESE: "问候语已禁用",
                ENGLISH: "Greetings Disabled"
            },
            "greeting_enabled_description": {
                CHINESE: "程序启动时将显示问候通知",
                ENGLISH: "Greeting notifications will be shown when the program starts"
            },
            "greeting_disabled_description": {
                CHINESE: "程序启动时将不再显示问候通知",
                ENGLISH: "Greeting notifications will no longer be shown when the program starts"
            },
            
            "app_name": {
                CHINESE: "Roblox音频提取器",
                ENGLISH: "Roblox Audio Extractor"
            },
            "title": {
                ENGLISH: f"Roblox-Audio-Extractor-v{VERSION}-Beta",
                CHINESE: f"Roblox-Audio-Extractor-v{VERSION}-Beta"
            },
            "welcome_message": {
                ENGLISH: "Welcome to Roblox Audio Extractor!",
                CHINESE: "欢迎使用 Roblox Audio Extractor！"
            },
            "extract_audio": {
                ENGLISH: "Audio",
                CHINESE: "音频"
            },
            "extract": {
                ENGLISH: "Extract",
                CHINESE: "提取"
            },
            "extract_images": {
                ENGLISH: "Images",
                CHINESE: "图像"
            },
            "extract_textures": {
                ENGLISH: "Textures",
                CHINESE: "纹理"
            },
            "extract_fonts": {
                ENGLISH: "Fonts",
                CHINESE: "字体"
            },
            "view_history": {
                ENGLISH: "History",
                CHINESE: "提取历史"
            },
            "clear_history": {
                ENGLISH: "Clear History",
                CHINESE: "清除历史"
            },
            "language_settings": {
                ENGLISH: "Settings",
                CHINESE: "设置"
            },
            "about": {
                ENGLISH: "About",
                CHINESE: "关于"
            },
            'clear_cache': {
                ENGLISH: "Cache",
                CHINESE: "清除缓存"
            },
            'cache_description': {
                ENGLISH: "Clear Roblox database and storage cache.",
                CHINESE: "清除Roblox数据库和存储缓存"
            },
            'cache_details': {
                ENGLISH: "This operation will clear:\n1. rbx-storage.db database file\n2. Contents of rbx-storage folder (except the extracted folder)",
                CHINESE: "此操作将清除以下内容：\n1. rbx-storage.db 数据库文件\n2. rbx-storage 文件夹中的内容（除了extracted文件夹）"
            },
            'cache_details_title': {
                ENGLISH: "This operation will clear the following:",
                CHINESE: "此操作将清除以下内容："
            },
            'cache_db_file': {
                ENGLISH: "rbx-storage.db database file",
                CHINESE: "rbx-storage.db 数据库文件"
            },
            'cache_folder_content': {
                ENGLISH: "Contents of rbx-storage folder",
                CHINESE: "rbx-storage 文件夹中的内容"
            },
            'cache_db_file_desc': {
                ENGLISH: "Roblox client database file containing cache index information",
                CHINESE: "Roblox客户端的数据库文件，包含缓存索引信息"
            },
            'cache_folder_content_desc': {
                ENGLISH: "Temporary files and resource cache in Roblox cache folder",
                CHINESE: "Roblox缓存文件夹中的临时文件和资源缓存"
            },
            'confirm_clear_cache': {
                ENGLISH: "Are you sure you want to clear Roblox database and storage cache?\n\nThis operation cannot be undone.",
                CHINESE: "确定要清除Roblox数据库和存储缓存吗？\n\n此操作无法撤销"
            },
            'cache_cleared': {
                ENGLISH: "Successfully cleared {0} of {1} cache items.",
                CHINESE: "成功清除了 {0} 个缓存项，共 {1} 个"
            },
            'no_cache_found': {
                ENGLISH: "No cache items found.",
                CHINESE: "未找到缓存项"
            },
            'clear_cache_failed': {
                ENGLISH: "Failed to clear cache: {0}",
                CHINESE: "清除缓存失败：{0}"
            },
            'cache_location': {
                ENGLISH: "Cache Location",
                CHINESE: "缓存位置"
            },
            'cache_info': {
                ENGLISH: "Cache Information",
                CHINESE: "缓存信息"
            },
            'quick_actions': {
                ENGLISH: "Quick Actions",
                CHINESE: "快速操作"
            },
            'quick_actions_info': {
                ENGLISH: "Quick access and management of cache directory",
                CHINESE: "快速访问和管理缓存目录"
            },
            'path_not_found': {
                ENGLISH: "Roblox directory not found",
                CHINESE: "未找到Roblox目录"
            },
            'cache_path_placeholder': {
                ENGLISH: "Roblox cache directory path",
                CHINESE: "Roblox缓存目录路径"
            },
            'opened_directory': {
                ENGLISH: "Opened directory",
                CHINESE: "已打开目录"
            },
            'copied_path': {
                ENGLISH: "Copied path",
                CHINESE: "已复制路径"
            },
            'directory_not_found': {
                ENGLISH: "Directory not found",
                CHINESE: "目录不存在"
            },
            'cache_path_synced': {
                ENGLISH: "Cache path synchronized",
                CHINESE: "缓存路径已同步"
            },
            'auto_clear_cache': {
                ENGLISH: "Auto Clear Cache",
                CHINESE: "自动清除缓存"
            },
            'auto_clear_cache_desc': {
                ENGLISH: "Automatically clear Roblox cache after resource extraction to save disk space",
                CHINESE: "在资源提取完成后自动清除Roblox缓存"
            },
            'auto_clear_cache_status_changed': {
                ENGLISH: "Auto clear cache status changed",
                CHINESE: "自动清除缓存状态已更改"
            },
            'auto_clear_cache_triggered': {
                ENGLISH: "Auto clear cache triggered",
                CHINESE: "触发自动清除缓存"
            },
            'auto_clear_cache_completed': {
                ENGLISH: "Auto clear cache completed",
                CHINESE: "自动清除缓存完成"
            },
            'auto_clear_cache_failed': {
                ENGLISH: "Auto clear cache failed",
                CHINESE: "自动清除缓存失败"
            },
            'history_info': {
                ENGLISH: "History Information",
                CHINESE: "历史信息"
            },
            'history_statistics': {
                ENGLISH: "History Statistics",
                CHINESE: "历史统计"
            },
            'history_statistics_desc': {
                ENGLISH: "Display statistics information of extraction history records",
                CHINESE: "显示提取历史记录的统计信息"
            },
            'history_file_location_title': {
                ENGLISH: "History File Location",
                CHINESE: "历史文件位置"
            },
            'history_file_location_desc': {
                ENGLISH: "Storage location of history record file",
                CHINESE: "历史记录文件的存储位置"
            },
            'history_file_path_placeholder': {
                ENGLISH: "History file path",
                CHINESE: "历史文件路径"
            },
            'history_quick_actions_desc': {
                ENGLISH: "Clear history records and view history file",
                CHINESE: "清除历史记录和查看历史文件"
            },
            'no_history_file': {
                ENGLISH: "No history file available",
                CHINESE: "暂无历史文件"
            },
            'refresh_statistics': {
                ENGLISH: "Refresh Statistics",
                CHINESE: "刷新统计"
            },
            'no_history_records': {
                ENGLISH: "No history records available",
                CHINESE: "暂无历史记录"
            },
            'statistics_refreshed': {
                ENGLISH: "Statistics refreshed",
                CHINESE: "统计信息已刷新"
            },
            'refresh_failed': {
                ENGLISH: "Refresh failed",
                CHINESE: "刷新失败"
            },
            'total_records': {
                ENGLISH: "Total Records",
                CHINESE: "总记录数"
            },
            'file_size': {
                ENGLISH: "File Size",
                CHINESE: "文件大小"
            },
            'audio_records': {
                ENGLISH: "Audio",
                CHINESE: "音频"
            },
            'image_records': {
                ENGLISH: "Image", 
                CHINESE: "图像"
            },
            'texture_records': {
                ENGLISH: "Texture",
                CHINESE: "纹理"
            },
            'false_records': {
                ENGLISH: "Other",
                CHINESE: "其他"
            },
            'total_files': {
                ENGLISH: "Total Files: {}",
                CHINESE: "总文件数: {}"
            },
            'avg_files_per_extraction': {
                ENGLISH: "Average Files per Extraction: {}",
                CHINESE: "每次提取平均文件数: {}"
            },
            'history_file_size': {
                ENGLISH: "History File Size: {} KB",
                CHINESE: "历史文件大小: {} KB"
            },
            'avg_files_per_extraction_label': {
                ENGLISH: "Average Files per Extraction",
                CHINESE: "每次提取平均文件数"
            },
            'files_suffix': {
                ENGLISH: " Files",
                CHINESE: "文件"
            },
            "error_occurred": {
                ENGLISH: "An error occurred: {}",
                CHINESE: "发生错误：{}"
            },
            "history_stats": {
                ENGLISH: "Extract History Statistics",
                CHINESE: "提取历史统计"
            },
            "files_recorded": {
                ENGLISH: "Files recorded: {}",
                CHINESE: "已记录文件：{}"
            },
            "history_file_location": {
                ENGLISH: "History file: {}",
                CHINESE: "历史文件：{}"
            },
            "confirm_clear_history": {
                ENGLISH: "Are you sure you want to clear all extraction history?\n\nThis operation cannot be undone.",
                CHINESE: "确定要清除所有提取历史吗？\n\n此操作无法撤销"
            },
            "confirm_clear_history_type": {
                ENGLISH: "Are you sure you want to clear {} type extraction history?\n\nThis operation cannot be undone.",
                CHINESE: "确定要清除 {} 类型的提取历史吗？\n\n此操作无法撤销"
            },
            "history_not_available": {
                ENGLISH: "History record is not available",
                CHINESE: "历史记录不可用"
            },
            "parent_window_not_available": {
                ENGLISH: "Unable to access main window",
                CHINESE: "无法访问主窗口"
            },
            "history_cleared": {
                ENGLISH: "Extraction history has been cleared.",
                CHINESE: "提取历史已清除"
            },
            "select_history_type_to_clear": {
                ENGLISH: "Select which history records to clear:",
                CHINESE: "选择要清除的历史记录类型:"
            },
            "all_history": {
                ENGLISH: "All History",
                CHINESE: "所有历史"
            },
            "all_history_cleared": {
                ENGLISH: "All history records cleared successfully",
                CHINESE: "所有历史记录已成功清除"
            },
            "history_type_cleared": {
                ENGLISH: "{0} history records cleared successfully",
                CHINESE: "{0}历史记录已成功清除"
            },
            "audio": {
                ENGLISH: "Audio",
                CHINESE: "音频"
            },
            "image": {
                ENGLISH: "Image",
                CHINESE: "图像"
            },
            "texture": {
                ENGLISH: "Texture",
                CHINESE: "纹理"
            },
            "model": {
                ENGLISH: "Model",
                CHINESE: "模型"
            },
            "other": {
                ENGLISH: "Other",
                CHINESE: "其他"
            },
            "audio_files": {
                ENGLISH: "Audio files: {0}",
                CHINESE: "音频文件数: {0}"
            },
            "image_files": {
                ENGLISH: "Image files: {0}",
                CHINESE: "图像文件数: {0}"
            },
            "texture_files": {
                ENGLISH: "Texture files: {0}",
                CHINESE: "纹理文件数: {0}"
            },
            "model_files": {
                ENGLISH: "Model files: {0}",
                CHINESE: "模型文件数: {0}"
            },
            "other_files": {
                ENGLISH: "Other files: {0}",
                CHINESE: "其他文件数: {0}"
            },
            "operation_cancelled": {
                ENGLISH: "Operation cancelled.",
                CHINESE: "操作已取消"
            },
            # 历史记录相关
            "history_size": {
                ENGLISH: "History size",
                CHINESE: "历史记录数量"
            },
            "unique_contents": {
                ENGLISH: "unique contents",
                CHINESE: "唯一内容"
            },
            "files": {
                ENGLISH: "files",
                CHINESE: "文件"
            },
            # 数据库扫描相关翻译
            "scan_database": {
                ENGLISH: "Scan Roblox Database",
                CHINESE: "扫描Roblox数据库"
            },
            "scan_database_info": {
                ENGLISH: "Enable to scan Roblox client SQLite database ",
                CHINESE: "启用扫描Roblox 客户端 SQLite 数据库"
            },
            # 字体下载相关翻译
            "download_fonts": {
                ENGLISH: "Download Font Files",
                CHINESE: "下载字体文件"
            },
            "download_fonts_info": {
                ENGLISH: "Automatically download font files referenced in FontList JSON files",
                CHINESE: "自动下载FontList JSON文件中引用的字体文件"
            },
            "audio_classification_method": {
                ENGLISH: "Audio Classification Method",
                CHINESE: "音频分类方法"
            },
            "font_classification_method": {
                ENGLISH: "Font Classification Method",
                CHINESE: "字体分类方法"
            },
            "video_classification_method": {
                ENGLISH: "Video Classification Method",
                CHINESE: "视频分类方法"
            },
            # 音频格式转换相关翻译
            "convert_audio_format": {
                ENGLISH: "Convert Audio Format",
                CHINESE: "转换音频格式"
            },
            "convert_audio_format_info": {
                ENGLISH: "Convert extracted OGG files to other audio formats after extraction",
                CHINESE: "提取完成后将OGG文件转换为其他音频格式"
            },
            "convert_format": {
                ENGLISH: "Convert Format",
                CHINESE: "转换格式"
            },
            "convert_info": {
                ENGLISH: "Convert audio file format (requires FFmpeg support)",
                CHINESE: "转换音频文件格式（需要FFmpeg支持）"
            },
            "output_format": {
                ENGLISH: "Output Format",
                CHINESE: "输出格式"
            },
            "select_output_format": {
                ENGLISH: "Select audio output format",
                CHINESE: "选择音频输出格式"
            },
            "extract_audio_title": {
                ENGLISH: "Extract Audio Files",
                CHINESE: "提取音频文件"
            },
            "extract_font_title": {
                ENGLISH: "Extract Font Files",
                CHINESE: "提取字体文件"
            },
            "extract_fonts_title": {
                ENGLISH: "Extract Font Files",
                CHINESE: "提取字体文件"
            },
            "extract_video_title": {
                ENGLISH: "Extract Video Files",
                CHINESE: "提取视频文件"
            },
            "extract_videos_title": {
                ENGLISH: "Extract Video Files",
                CHINESE: "提取视频文件"
            },
            "input_dir": {
                ENGLISH: "Input Directory:",
                CHINESE: "输入目录:"
            },
            "input_dir_placeholder": {
                ENGLISH: "Path to Roblox cache directory",
                CHINESE: "Roblox缓存目录路径"
            },
            "browse": {
                ENGLISH: "Browse",
                CHINESE: "浏览"
            },
            "by_duration": {
                ENGLISH: "By Duration",
                CHINESE: "按时长"
            },
            "by_size": {
                ENGLISH: "By Size",
                CHINESE: "按大小"
            },
            "by_font_family": {
                ENGLISH: "By Font Family",
                CHINESE: "按字体家族"
            },
            "by_font_style": {
                ENGLISH: "By Font Style", 
                CHINESE: "按字体样式"
            },
            "by_resolution": {
                ENGLISH: "By Resolution",
                CHINESE: "按分辨率"
            },
            "no_classification": {
                ENGLISH: "None",
                CHINESE: "无分类"
            },
            "threads": {
                ENGLISH: "Threads:",
                CHINESE: "线程数:"
            },
            "threads_info": {
                ENGLISH: "Number of parallel processing threads",
                CHINESE: "并行处理线程数量设置"
            },
            
            # 多进程设置相关
            "use_multiprocessing": {
                ENGLISH: "Use Multiprocessing",
                CHINESE: "使用多进程"
            },
            "multiprocessing_description": {
                ENGLISH: "Enable multiprocessing to improve performance for CPU-intensive tasks",
                CHINESE: "启用多进程处理以提高CPU密集型任务的性能"
            },
            "multiprocessing_strategy": {
                ENGLISH: "Multiprocessing Strategy",
                CHINESE: "多进程策略"
            },
            "multiprocessing_strategy_description": {
                ENGLISH: "Choose multiprocessing count strategy: Conservative strategy is more stable, aggressive strategy offers higher performance",
                CHINESE: "选择多进程数量策略：保守策略更稳定，激进策略性能更高"
            },
            "multiprocessing_strategy_disabled_tooltip": {
                ENGLISH: "Enable multiprocessing mode first to configure strategy",
                CHINESE: "请先启用多进程模式以配置策略"
            },
            "conservative_strategy": {
                ENGLISH: "(CPU cores + 1)",
                CHINESE: "(CPU核心数 + 1)"
            },
            "aggressive_strategy": {
                ENGLISH: "(CPU cores × 2)",
                CHINESE: " (CPU核心数 × 2)"
            },
            "processes": {
                ENGLISH: " processes",
                CHINESE: " 个进程"
            },
            "log_title": {
                ENGLISH: "Extraction Log",
                CHINESE: "提取日志"
            },
            "preparing": {
                ENGLISH: "Preparing...",
                CHINESE: "准备中..."
            },
            "error": {
                ENGLISH: "Error",
                CHINESE: "错误"
            },
            "invalid_dir": {
                ENGLISH: "Invalid directory path",
                CHINESE: "无效的目录路径"
            },
            "info_duration_categories": {
                ENGLISH: "Files will be sorted into folders by duration",
                CHINESE: "文件将按时长分类到不同文件夹"
            },
            "info_size_categories": {
                ENGLISH: "Files will be sorted into folders by file size",
                CHINESE: "文件将按文件大小分类到不同文件夹"
            },
            "info_font_family_categories": {
                ENGLISH: "Fonts will be sorted into folders by font family (e.g. Arial, Roboto)",
                CHINESE: "字体将按字体家族分类到不同文件夹 (如Arial、Roboto等)"
            },
            "info_font_style_categories": {
                ENGLISH: "Fonts will be sorted into folders by font style (e.g. Regular, Bold, Italic)",
                CHINESE: "字体将按字体样式分类到不同文件夹 (如Regular、Bold、Italic等)"
            },
            "info_font_size_categories": {
                ENGLISH: "Fonts will be sorted into folders by file size",
                CHINESE: "字体将按文件大小分类到不同文件夹"
            },
            "info_no_classification": {
                ENGLISH: "Files will be output directly to the main directory without classification",
                CHINESE: "文件将直接输出到主目录，无需分类"
            },
            "info_audio_default_category": {
                ENGLISH: "Select audio classification method",
                CHINESE: "选择音频分类方法"
            },
            "info_font_default_category": {
                ENGLISH: "Select font classification method", 
                CHINESE: "选择字体分类方法"
            },
            "info_resolution_categories": {
                ENGLISH: "Videos will be sorted into folders by resolution (e.g., 720p, 1080p)",
                CHINESE: "视频将按分辨率分类到不同文件夹 (如720p、1080p等)"
            },
            "info_video_default_category": {
                ENGLISH: "Select video classification method",
                CHINESE: "选择视频分类方法"
            },
            # 新增分类方法相关翻译
            "classification_method": {
                ENGLISH: "Classification Method",
                CHINESE: "分类方法"
            },
            "classify_by_duration": {
                ENGLISH: "By audio duration (requires FFmpeg)",
                CHINESE: "按音频时长分类（需要 FFmpeg）"
            },
            "classify_by_size": {
                ENGLISH: "By file size",
                CHINESE: "按文件大小分类"
            },
            "ffmpeg_not_found_warning": {
                ENGLISH: "⚠ FFmpeg not found. Duration classification may not work correctly.",
                CHINESE: "⚠ 未找到 FFmpeg按时长分类可能无法正常工作"
            },
            # 语言设置相关
            "restart_required": {
                ENGLISH: "Restart Required",
                CHINESE: "需要重启"
            },
            "restart_message": {
                ENGLISH: "The language change will take effect after restarting the application.\n\nWould you like to restart now?",
                CHINESE: "语言更改将在重启应用程序后生效\n\n您想要现在重启吗？"
            },
            "language_close_message": {
                ENGLISH: "The language change will take effect after restarting the application.\n\nWould you like to close the application now?",
                CHINESE: "语言更改将在重启应用程序后生效\n\n您想要现在关闭应用程序吗？"
            },
            "language_saved": {
                ENGLISH: "Language setting saved. Please restart the application.",
                CHINESE: "语言设置已保存请重启应用程序"
            },
            "language_unchanged": {
                ENGLISH: "Language setting unchanged.",
                CHINESE: "语言设置未改变"
            },
            "current_language": {
                ENGLISH: "Current language",
                CHINESE: "当前语言"
            },
            "select_language": {
                ENGLISH: "Select language",
                CHINESE: "选择语言"
            },
            # 主题设置
            "theme_settings": {
                ENGLISH: "Theme Settings",
                CHINESE: "主题设置"
            },
            "theme_light": {
                ENGLISH: "Light Theme",
                CHINESE: "浅色主题"
            },
            "theme_dark": {
                ENGLISH: "Dark Theme",
                CHINESE: "深色主题"
            },
            "theme_system": {
                ENGLISH: "Follow System Settings",
                CHINESE: "跟随系统设置"
            },
            "theme_changed": {
                ENGLISH: "Theme changed to: {}",
                CHINESE: "主题已更改为：{}"
            },
            # 通用UI文本
            "browse": {
                ENGLISH: "Browse",
                CHINESE: "浏览"
            },
            "start_extraction": {
                ENGLISH: "Start Extraction",
                CHINESE: "开始提取"
            },
            "start_font_extraction": {
                ENGLISH: "Start Font Extraction",
                CHINESE: "开始提取字体"
            },
            "processing": {
                ENGLISH: "Processing...",
                CHINESE: "处理中..."
            },
            "apply": {
                ENGLISH: "Apply",
                CHINESE: "应用"
            },
            "save": {
                ENGLISH: "Save",
                CHINESE: "保存"
            },
            "cancel": {
                ENGLISH: "Cancel",
                CHINESE: "取消"
            },
            "confirm": {
                ENGLISH: "Confirm",
                CHINESE: "确认"
            },
            "settings": {
                ENGLISH: "Settings",
                CHINESE: "设置"
            },
            "home": {
                ENGLISH: "Home",
                CHINESE: "首页"
            },
            "directory": {
                ENGLISH: "Directory",
                CHINESE: "目录"
            },
            "task_running": {
                ENGLISH: "Task Running",
                CHINESE: "任务运行中"
            },
            "task_completed": {
                ENGLISH: "Task Completed",
                CHINESE: "任务完成"
            },
            "task_failed": {
                ENGLISH: "Task Failed",
                CHINESE: "任务失败"
            },
            "task_canceled": {
                ENGLISH: "Task Canceled",
                CHINESE: "任务已取消"
            },
            "extraction_completed": {
                ENGLISH: "Extraction completed",
                CHINESE: "提取完成"
            },
            "extraction_failed": {
                ENGLISH: "Extraction failed",
                CHINESE: "提取失败"
            },
            "ready": {
                ENGLISH: "Ready",
                CHINESE: "就绪"
            },
            "restart_now": {
                ENGLISH: "Restart Now",
                CHINESE: "立即重启"
            },
            "restart_later": {
                ENGLISH: "Restart Later",
                CHINESE: "稍后重启"
            },
            "about_description": {
                ENGLISH: "An open-source tool for extracting resource files from Roblox cache.",
                CHINESE: "一个用于从 Roblox 缓存中提取缓存资源的开源工具"
            },
            "features": {
                ENGLISH: "Features",
                CHINESE: "功能特色"
            },
            "feature_1": {
                ENGLISH: "Fast multithreaded extraction",
                CHINESE: "快速多线程提取"
            },
            "feature_2": {
                ENGLISH: "Auto duplicate detection",
                CHINESE: "重复检测"
            },
            "feature_3": {
                ENGLISH: "Multiple classification methods",
                CHINESE: "多种分类方法"
            },
            "feature_4": {
                ENGLISH: "Automatic conversion",
                CHINESE: "自动转换"
            },
            "default_dir": {
                ENGLISH: "Default directory",
                CHINESE: "默认目录"
            },
            "input_dir": {
                ENGLISH: "Enter directory",
                CHINESE: "输入目录"
            },
            "dir_not_exist": {
                ENGLISH: "Directory does not exist: {}",
                CHINESE: "目录不存在：{}"
            },
            "create_dir_prompt": {
                ENGLISH: "Create directory?",
                CHINESE: "创建目录吗？"
            },
            "dir_created": {
                ENGLISH: "Directory created: {}",
                CHINESE: "目录已创建：{}"
            },
            "dir_create_failed": {
                ENGLISH: "Failed to create directory: {}",
                CHINESE: "创建目录失败：{}"
            },
            "processing_info": {
                ENGLISH: "Processing Options",
                CHINESE: "处理选项"
            },
            "info_duration_categories": {
                ENGLISH: "Files will be organized by audio duration into different folders",
                CHINESE: "文件将按音频时长分类到不同文件夹中"
            },
            "info_size_categories": {
                ENGLISH: "Files will be organized by file size into different folders",
                CHINESE: "文件将按文件大小分类到不同文件夹中"
            },
            "info_mp3_conversion": {
                ENGLISH: "You can convert OGG files to MP3 after extraction",
                CHINESE: "提取后可以将 OGG 文件转换为 MP3"
            },
            "info_skip_downloaded": {
                ENGLISH: "Previously extracted files will be skipped automatically",
                CHINESE: "将自动跳过之前提取过的文件"
            },
            "threads_prompt": {
                ENGLISH: "Number of threads",
                CHINESE: "线程数"
            },
            "threads_min_error": {
                ENGLISH: "Number of threads must be at least 1",
                CHINESE: "线程数必须至少为 1"
            },
            "threads_high_warning": {
                ENGLISH: "Using a high number of threads may slow down your computer",
                CHINESE: "使用过多线程可能会降低计算机性能"
            },
            "confirm_high_threads": {
                ENGLISH: "Continue with high thread count anyway?",
                CHINESE: "是否仍使用这么多线程？"
            },
            "threads_adjusted": {
                ENGLISH: "Thread count adjusted to: {}",
                CHINESE: "线程数已调整为：{}"
            },
            "input_invalid": {
                ENGLISH: "Invalid input, using default value",
                CHINESE: "输入无效，使用默认值"
            },
            "extraction_complete": {
                ENGLISH: "Extraction completed successfully!",
                CHINESE: "提取成功完成！"
            },
            "font_extraction_complete": {
                ENGLISH: "Font extraction completed!",
                CHINESE: "字体提取完成! "
            },
            "font_extraction_success": {
                ENGLISH: "Font extraction completed successfully!",
                CHINESE: "字体提取成功完成！"
            },
            "font_lists_found": {
                ENGLISH: "Font lists found: {}",
                CHINESE: "发现字体列表：{} 个"
            },
            "fonts_downloaded": {
                ENGLISH: "Fonts downloaded: {}",
                CHINESE: "已下载字体：{} 个"
            },
            "caches_scanned": {
                ENGLISH: "Caches scanned: {}",
                CHINESE: "已扫描缓存：{} 个"
            },
            "processing_errors": {
                ENGLISH: "Processing errors: {}",
                CHINESE: "处理错误：{} 个"
            },
            "download_failed": {
                ENGLISH: "Download failed: {}",
                CHINESE: "下载失败：{} 个"
            },
            "font_output_dir": {
                ENGLISH: "Font output directory: {}",
                CHINESE: "字体输出目录：{}"
            },
            "font_processing_speed": {
                ENGLISH: "Processing speed: {} font lists/second",
                CHINESE: "处理速度：{} 字体列表/秒"
            },
            "starting_font_extraction": {
                ENGLISH: "Starting font extraction...",
                CHINESE: "开始字体提取..."
            },
            "initializing_extractor": {
                ENGLISH: "Initializing font extractor...",
                CHINESE: "正在初始化字体提取器..."
            },
            "cache_info": {
                ENGLISH: "Cache",
                CHINESE: "缓存"
            },
            "cache_path_not_found": {
                ENGLISH: "Roblox cache path not found or inaccessible",
                CHINESE: "Roblox缓存路径不存在或无法访问"
            },
            "extracting_fonts": {
                ENGLISH: "Extracting font files...",
                CHINESE: "正在提取字体文件..."
            },
            "font_extraction_completed": {
                ENGLISH: "Font extraction completed! Found {} font lists, successfully downloaded {} font files (took {:.1f} seconds)",
                CHINESE: "字体提取完成! 发现{}个字体列表，成功下载{}个字体文件 (耗时{:.1f}秒)"
            },
            "extraction_failed": {
                ENGLISH: "Font extraction failed: {}",
                CHINESE: "字体提取失败: {}"
            },
            "extraction_error": {
                ENGLISH: "Error occurred during font extraction: {}",
                CHINESE: "字体提取过程中发生错误: {}"
            },
            "error_details": {
                ENGLISH: "Error details: {}",
                CHINESE: "错误详情: {}"
            },
            "progress_update": {
                ENGLISH: "Progress update: {:.1f}% ({}/{})",
                CHINESE: "进度更新: {:.1f}% ({}/{})"
            },
            "extraction_cancelled": {
                ENGLISH: "Font extraction cancelled",
                CHINESE: "字体提取已取消"
            },
            # 新增字体提取日志翻译键
            "scanning_cache": {
                ENGLISH: "Scanning cache...",
                CHINESE: "正在扫描缓存..."
            },
            "cache_scan_complete": {
                ENGLISH: "Cache scan complete, found {} items",
                CHINESE: "缓存扫描完成，发现 {} 个项目"
            },
            "no_cache_items_found": {
                ENGLISH: "No cache items found",
                CHINESE: "未发现缓存项目"
            },
            "cache_path_not_found": {
                ENGLISH: "Roblox cache path not found or inaccessible",
                CHINESE: "Roblox缓存路径不存在或无法访问"
            },
            "processing_font_list": {
                ENGLISH: "Processing font list: {}, contains {} fonts",
                CHINESE: "处理字体列表: {}，包含 {} 个字体"
            },
            "font_list_complete": {
                ENGLISH: "Font list complete: {}, downloaded {}/{} fonts",
                CHINESE: "字体列表处理完成: {}，成功下载 {}/{} 个字体"
            },
            "downloading_font": {
                ENGLISH: "Downloading font: {}...",
                CHINESE: "正在下载字体: {}..."
            },
            "font_download_success": {
                ENGLISH: "Successfully downloaded font: {}",
                CHINESE: "成功下载字体: {}"
            },
            "font_download_cancelled": {
                ENGLISH: "Font download cancelled by user",
                CHINESE: "字体下载被用户取消"
            },
            "multithread_download_cancelled": {
                ENGLISH: "Multi-threaded font download cancelled by user",
                CHINESE: "多线程字体下载被用户取消"
            },
            "thread_processing_cancelled": {
                ENGLISH: "Thread processing cancelled by user", 
                CHINESE: "线程处理被用户取消"
            },
            "font_extraction_cancelled": {
                ENGLISH: "Font extraction operation cancelled",
                CHINESE: "字体提取操作已取消"
            },
            "processing_caches_multiprocess": {
                ENGLISH: "Using {} processes to process cache items...",
                CHINESE: "使用 {} 个进程处理缓存项目..."
            },
            "processing_caches_multithread": {
                ENGLISH: "Using {} threads to process cache items...",
                CHINESE: "使用 {} 个线程处理缓存项目..."
            },
            "unknown": {
                ENGLISH: "Unknown",
                CHINESE: "未知"
            },
            "database": {
                ENGLISH: "Database",
                CHINESE: "数据库"
            },
            "filesystem": {
                ENGLISH: "File system",
                CHINESE: "文件系统"
            },
            "processed": {
                ENGLISH: "Processed: {} files",
                CHINESE: "已处理：{} 个文件"
            },
            "skipped_duplicates": {
                ENGLISH: "Skipped duplicates: {} files",
                CHINESE: "跳过重复：{} 个文件"
            },
            "skipped_already_processed": {
                ENGLISH: "Skipped already processed: {} files",
                CHINESE: "跳过已处理：{} 个文件"
            },
            "errors": {
                ENGLISH: "Errors: {} files",
                CHINESE: "错误：{} 个文件"
            },
            "time_spent": {
                ENGLISH: "Time spent: {:.2f} seconds",
                CHINESE: "耗时：{:.2f} 秒"
            },
            "files_per_sec": {
                ENGLISH: "Processing speed: {:.2f} files/second",
                CHINESE: "处理速度：{:.2f} 文件/秒"
            },
            "output_dir": {
                ENGLISH: "Output directory: {}",
                CHINESE: "输出目录：{}"
            },
            "convert_to_mp3_prompt": {
                ENGLISH: "Convert to MP3 after extraction",
                CHINESE: "提取后转换为 MP3"
            },
            "mp3_conversion_complete": {
                ENGLISH: "MP3 conversion completed!",
                CHINESE: "MP3 转换完成！"
            },
            "converted": {
                ENGLISH: "Converted: {} of {} files",
                CHINESE: "已转换：{} / {} 个文件"
            },
            "mp3_conversion_failed": {
                ENGLISH: "MP3 conversion failed: {}",
                CHINESE: "MP3 转换失败：{}"
            },
            "opening_output_dir": {
                ENGLISH: "Opening {} output directory...",
                CHINESE: "正在打开 {} 输出目录..."
            },
            "manual_navigate": {
                ENGLISH: "Please navigate manually to: {}",
                CHINESE: "请手动导航到：{}"
            },
            "no_files_processed": {
                ENGLISH: "No files were processed",
                CHINESE: "没有处理任何文件"
            },
            "total_runtime": {
                ENGLISH: "Total runtime: {:.2f} seconds",
                CHINESE: "总运行时间：{:.2f} 秒"
            },
            "canceled_by_user": {
                ENGLISH: "Operation canceled by user",
                CHINESE: "操作被用户取消"
            },
            "scanning_files": {
                ENGLISH: "Scanning for files...",
                CHINESE: "正在扫描文件..."
            },
            "found_files": {
                ENGLISH: "Found {} files in {:.2f} seconds",
                CHINESE: "找到 {} 个文件，耗时 {:.2f} 秒"
            },
            "no_files_found": {
                ENGLISH: "No files found in the specified directory",
                CHINESE: "在指定目录中未找到文件"
            },
            "processing_with_threads": {
                ENGLISH: "Processing with {} threads...",
                CHINESE: "使用 {} 个线程处理..."
            },
            "mp3_category": {
                ENGLISH: "MP3",
                CHINESE: "MP3"
            },
            "ogg_category": {
                ENGLISH: "OGG",
                CHINESE: "OGG"
            },
            "audio_folder": {
                ENGLISH: "Audio folder",
                CHINESE: "音频总文件夹"
            },
            "fonts_folder": {
                ENGLISH: "Fonts folder",
                CHINESE: "字体总文件夹"
            },
            "fonts_category": {
                ENGLISH: "Font files",
                CHINESE: "字体文件"
            },
            "readme_title": {
                ENGLISH: "Roblox Audio Files - Classification Information",
                CHINESE: "Roblox 音频文件 - 分类信息"
            },
            "ffmpeg_not_installed": {
                ENGLISH: "FFmpeg is not installed. Please install FFmpeg to convert files and get duration information.",
                CHINESE: "未安装 FFmpeg请安装 FFmpeg 以转换文件并获取时长信息"
            },
            "no_ogg_files": {
                ENGLISH: "No OGG files found to convert",
                CHINESE: "未找到要转换的 OGG 文件"
            },
            "mp3_conversion": {
                ENGLISH: "Converting {} OGG files to MP3...",
                CHINESE: "正在将 {} 个 OGG 文件转换为 MP3..."
            },
            "language_set": {
                ENGLISH: "Language set to: {}",
                CHINESE: "语言设置为：{}"
            },
            "about_title": {
                ENGLISH: "About Roblox Audio Extractor",
                CHINESE: "关于 Roblox 音频提取器"
            },
            "about_version": {
                ENGLISH: f"Version {VERSION}",
                CHINESE: f"版本 {VERSION}"
            },
            "about_author": {
                ENGLISH: "Created by JustKanade",
                CHINESE: "由 JustKanade 制作"
            },
            "about_license": {
                ENGLISH: "License: GNU AGPLv3",
                CHINESE: "许可协议：GNU AGPLv3"
            },
            "github_link": {
                ENGLISH: "View on GitHub",
                CHINESE: "在 GitHub 上查看"
            },
            "github_repository": {
                ENGLISH: "GitHub Repository",
                CHINESE: "GitHub 仓库"
            },
            "github_description": {
                ENGLISH: "View source code, report issues, and contribute to the project",
                CHINESE: "查看源代码、报告问题并为项目贡献"
            },
            "visit_fluent_widgets": {
                ENGLISH: "QFluentWidgets",
                CHINESE: "QFluentWidgets"
            },
            "provide_feedback": {
                ENGLISH: "Feedback",
                CHINESE: "提供反馈"
            },
            "feedback_description": {
                ENGLISH: "Help us improve project by providing feedback",
                CHINESE: "通过提供反馈帮助我们改进项目"
            },
            "quick_actions": {
                ENGLISH: "Quick Actions",
                CHINESE: "快速操作"
            },
            "quick_actions_description": {
                ENGLISH: "Commonly used functions for faster access",
                CHINESE: "常用功能的快速访问"
            },
            "extract_audio_description": {
                ENGLISH: "Extract audio files from Roblox cache for playback",
                CHINESE: "从 Roblox 缓存中提取音频文件用于播放"
            },
            "extract_fonts_description": {
                ENGLISH: "Extract font files from Roblox cache and download associated fonts",
                CHINESE: "从 Roblox 缓存中提取字体文件并下载相关字体"
            },
            "clear_cache_description": {
                ENGLISH: "Clean up temporary files and cached data to free up disk space",
                CHINESE: "清理临时文件和缓存数据以释放磁盘空间"
            },
            "settings_description": {
                ENGLISH: "Configure application preferences and customize your experience",
                CHINESE: "配置应用程序首选项并自定义您的体验"
            },
            "start_extraction": {
                ENGLISH: "Start Extraction",
                CHINESE: "开始提取"
            },
            "start_cleaning": {
                ENGLISH: "Start Cleaning",
                CHINESE: "开始清理"
            },
            "open_settings": {
                ENGLISH: "Open Settings",
                CHINESE: "打开设置"
            },
            "mp3_conversion_info": {
                ENGLISH: "Starting MP3 conversion...",
                CHINESE: "开始 MP3 转换..."
            },
            "getting_duration": {
                ENGLISH: "Getting audio duration...",
                CHINESE: "正在获取音频时长..."
            },
            "duration_unknown": {
                ENGLISH: "Unknown duration",
                CHINESE: "未知时长"
            },
            "readme_duration_title": {
                ENGLISH: "Audio Duration Categories:",
                CHINESE: "音频时长分类："
            },
            "readme_size_title": {
                ENGLISH: "File Size Categories:",
                CHINESE: "文件大小分类："
            },
            "classification_method_used": {
                ENGLISH: "Classification method: {}",
                CHINESE: "分类方法：{}"
            },
            "classification_by_duration": {
                ENGLISH: "by audio duration",
                CHINESE: "按音频时长"
            },
            "classification_by_size": {
                ENGLISH: "by file size",
                CHINESE: "按文件大小"
            },
            "quick_start": {
                ENGLISH: "Quick Start",
                CHINESE: "快速开始"
            },
            "recent_activity": {
                ENGLISH: "Recent Activity",
                CHINESE: "最近活动"
            },
            "system_info": {
                ENGLISH: "System Information",
                CHINESE: "系统信息"
            },
            "cpu_cores": {
                ENGLISH: "CPU Cores",
                CHINESE: "CPU 核心"
            },
            "recommended_threads": {
                ENGLISH: "Recommended Threads",
                CHINESE: "推荐线程数"
            },
            "ffmpeg_status": {
                ENGLISH: "FFmpeg Status",
                CHINESE: "FFmpeg 状态"
            },
            "available": {
                ENGLISH: "Available",
                CHINESE: "可用"
            },
            "not_available": {
                ENGLISH: "Not Available",
                CHINESE: "不可用"
            },
            "open_directory": {
                ENGLISH: "Open Directory",
                CHINESE: "打开目录"
            },
            "copy_path": {
                ENGLISH: "Copy Path",
                CHINESE: "复制路径"
            },
            "app_settings": {
                ENGLISH: "Application Settings",
                CHINESE: "应用设置"
            },
            "language_region": {
                ENGLISH: "Language & Region",
                CHINESE: "语言和地区"
            },
            "appearance": {
                ENGLISH: "Appearance",
                CHINESE: "外观"
            },
            "performance": {
                ENGLISH: "Performance",
                CHINESE: "性能"
            },
            "about_section": {
                ENGLISH: "About",
                CHINESE: "关于"
            },
            "about_application": {
                ENGLISH: "About Application",
                CHINESE: "关于应用"
            },
            # 贡献者相关翻译
            "contributors_section": {
                ENGLISH: "Thank You All:",
                CHINESE: "贡献者"
            },
            "contributors_table": {
                ENGLISH: "Project Contributors",
                CHINESE: "项目贡献者"
            },
            "contributors_description": {
                ENGLISH: "People who have contributed to this project",
                CHINESE: "为此项目做出贡献的人员"
            },
            "contributor_name": {
                ENGLISH: "Name",
                CHINESE: "昵称"
            },
            "contributor_type": {
                ENGLISH: "Contribution Type",
                CHINESE: "贡献类型"
            },
            "contributor_links": {
                ENGLISH: "Links",
                CHINESE: "链接"
            },
            "contributor_notes": {
                ENGLISH: "Notes",
                CHINESE: "备注"
            },
            "view_history_file": {
                ENGLISH: "View History File",
                CHINESE: "查看历史文件"
            },
            "history_overview": {
                ENGLISH: "History Overview",
                CHINESE: "历史记录概览"
            },
            "tech_stack": {
                ENGLISH: "Tech Stack",
                CHINESE: "技术栈"
            },
            "purpose": {
                ENGLISH: "Purpose",
                CHINESE: "用途"
            },
            "packaging": {
                ENGLISH: "Packaging",
                CHINESE: "打包"
            },
            "license": {
                ENGLISH: "License",
                CHINESE: "开源协议"
            },
            "operating_system": {
                ENGLISH: "Operating System",
                CHINESE: "操作系统"
            },
            "python_version": {
                ENGLISH: "Python Version",
                CHINESE: "Python 版本"
            },
            "ui_upgraded": {
                ENGLISH: "UI upgraded to PyQt-Fluent-Widget",
                CHINESE: "UI 已升级到 PyQt-Fluent-Widgets"
            },
            "config_file_location": {
                ENGLISH: "Config file location: {}",
                CHINESE: "配置文件位置: {}"
            },
            "total_files": {
                ENGLISH: "Total extraction files: {}",
                CHINESE: "总提取文件数: {}"
            },
            "avg_files_per_extraction": {
                ENGLISH: "Average per extraction: {} files",
                CHINESE: "平均每次提取: {} 文件"
            },
            "history_file_size": {
                ENGLISH: "History file size: {} KB",
                CHINESE: "历史记录大小: {} KB"
            },
            "links_and_support": {
                ENGLISH: "Links and Support",
                CHINESE: "链接和支持"
            },
            "default_threads": {
                ENGLISH: "Default thread count",
                CHINESE: "默认线程数"
            },
            "default_mp3_conversion": {
                ENGLISH: "Default MP3 conversion",
                CHINESE: "默认 MP3 转换"
            },
            "enabled": {
                ENGLISH: "Enabled",
                CHINESE: "启用"
            },
            "disabled": {
                ENGLISH: "Disabled",
                CHINESE: "禁用"
            },
            "saved": {
                ENGLISH: "Saved: {}",
                CHINESE: "已保存: {}"
            },
            "yes": {
                ENGLISH: "Yes",
                CHINESE: "是"
            },
            "no": {
                ENGLISH: "No",
                CHINESE: "否"
            },
            # 主题颜色设置相关的翻译
            "theme_color_settings": {
                ENGLISH: "Theme Color Settings",
                CHINESE: "主题颜色设置"
            },
            "theme_color_default": {
                ENGLISH: "Default Color",
                CHINESE: "默认颜色"
            },
            "theme_color_custom": {
                ENGLISH: "Custom Color",
                CHINESE: "自定义颜色"
            },
            "theme_color_choose": {
                ENGLISH: "Choose Color",
                CHINESE: "选择颜色"
            },
            # 新增翻译项
            "output_settings": {
                ENGLISH: "Output Settings",
                CHINESE: "输出设置"
            },
            "custom_output_dir": {
                ENGLISH: "Custom Output Directory",
                CHINESE: "自定义输出目录"
            },
            "output_dir_placeholder": {
                ENGLISH: "Default: 'extracted' folder under extraction directory",
                CHINESE: "默认使用提取目录下的 'extracted' 文件夹"
            },
            "save_logs": {
                ENGLISH: "Save logs to file",
                CHINESE: "保存日志到文件"
            },
            "save_logs_description": {
                ENGLISH: "Save application logs to file for debugging purposes",
                CHINESE: "将应用程序日志保存到文件以便调试"
            },
            "log_save_option_toggled": {
                ENGLISH: "Log save option toggled",
                CHINESE: "日志保存选项已切换"
            },
            # 版本检测卡片相关翻译
            "version_check_settings": {
                ENGLISH: "Version Check Settings",
                CHINESE: "版本检测设置"
            },
            "auto_check_settings": {
                ENGLISH: "Auto Check Update Settings",
                CHINESE: "自动检查更新设置"
            },
            "manual_check_settings": {
                ENGLISH: "Manual Check Update",
                CHINESE: "手动检查更新"
            },
            "auto_check_update": {
                ENGLISH: "Auto-check for updates on startup",
                CHINESE: "启动时自动检测更新"
            },
            "check_update_manually_desc": {
                ENGLISH: "Manually check for application updates",
                CHINESE: "手动检查应用程序更新"
            },
            "check_update_now": {
                ENGLISH: "Check Now",
                CHINESE: "检查更新"
            },
            "checking_update": {
                ENGLISH: "Checking...",
                CHINESE: "检查中..."
            },
            "latest_version": {
                ENGLISH: "Latest version: {}",
                CHINESE: "最新版本: {}"
            },
            "current_version": {
                ENGLISH: "Current version: {}",
                CHINESE: "当前版本: {}"
            },
            "update_available": {
                ENGLISH: "New Version Available!",
                CHINESE: "有新版本可用！"
            },
            "already_latest": {
                ENGLISH: "You have the latest version",
                CHINESE: "您已经使用的是最新版本"
            },
            "check_failed": {
                ENGLISH: "Update check failed: {}",
                CHINESE: "检查更新失败: {}"
            },
            "release_notes": {
                ENGLISH: "Release Notes",
                CHINESE: "更新内容"
            },
            "go_to_update": {
                ENGLISH: "Get Update",
                CHINESE: "获取更新"
            },
            "close": {
                ENGLISH: "Close",
                CHINESE: "关闭"
            },
            "download_update": {
                ENGLISH: "Download Update",
                CHINESE: "下载更新"
            },
            "cancel": {
                ENGLISH: "Cancel", 
                CHINESE: "取消"
            },
            "version_not_available": {
                ENGLISH: "Version information not available",
                CHINESE: "版本信息不可用"
            },
            # API和网络相关翻译
            "api_rate_limit": {
                ENGLISH: "GitHub API rate limit exceeded. Please try again later.",
                CHINESE: "GitHub API调用次数限制，请稍后再试"
            },
            "repository_not_found": {
                ENGLISH: "Repository not found",
                CHINESE: "仓库未找到"
            },
            "connection_timeout": {
                ENGLISH: "Connection timeout",
                CHINESE: "连接超时"
            },
            "connection_error": {
                ENGLISH: "Network connection error",
                CHINESE: "网络连接错误"
            },
            "network_error": {
                ENGLISH: "Network error occurred",
                CHINESE: "网络错误"
            },
            "invalid_response": {
                ENGLISH: "Invalid response from server",
                CHINESE: "服务器响应无效"
            },
            "unexpected_error": {
                ENGLISH: "Unexpected error occurred",
                CHINESE: "发生意外错误"
            },
            # 日志管理相关翻译
            "log_management": {
                ENGLISH: "Log Management",
                CHINESE: "日志管理"
            },
            "export_logs": {
                ENGLISH: "Export Logs",
                CHINESE: "导出日志"
            },
            "clear_logs": {
                ENGLISH: "Clear Logs",
                CHINESE: "清空日志"
            },
            "confirm_clear_logs": {
                ENGLISH: "Confirm Clear Logs",
                CHINESE: "确认清空日志"
            },
            "confirm_clear_logs_message": {
                ENGLISH: "Are you sure you want to clear all logs? This operation cannot be undone.",
                CHINESE: "确定要清空所有日志吗？此操作无法撤销"
            },
            "logs_cleared": {
                ENGLISH: "All logs have been cleared",
                CHINESE: "所有日志已清空"
            },
            "clear_successful": {
                ENGLISH: "Clear Successful",
                CHINESE: "清空成功"
            },
            "clear_failed": {
                ENGLISH: "Clear Failed",
                CHINESE: "清空失败"
            },
            "error_clearing_logs": {
                ENGLISH: "Error clearing logs: {}",
                CHINESE: "清空日志时发生错误: {}"
            },
            "save_log_file": {
                ENGLISH: "Save Log File",
                CHINESE: "保存日志文件"
            },
            "logs_exported_to": {
                ENGLISH: "Logs exported to: {}",
                CHINESE: "日志已导出至：{}"
            },
            "export_successful": {
                ENGLISH: "Export Successful",
                CHINESE: "导出成功"
            },
            "export_failed": {
                ENGLISH: "Export Failed",
                CHINESE: "导出失败"
            },
            "error_exporting_logs": {
                ENGLISH: "Error exporting logs: {}",
                CHINESE: "导出日志时出错：{}"
            },
            # FFmpeg状态卡片相关翻译
            "ffmpeg_status_title": {
                ENGLISH: "FFmpeg Status",
                CHINESE: "FFmpeg 状态"
            },
            "detect_ffmpeg": {
                ENGLISH: "Detect",
                CHINESE: "检测"
            },
            "browse_ffmpeg": {
                ENGLISH: "Browse",
                CHINESE: "浏览"
            },
            "detecting": {
                ENGLISH: "Detecting",
                CHINESE: "正在检测"
            },
            "detecting_ffmpeg": {
                ENGLISH: "Detecting FFmpeg...",
                CHINESE: "正在检测 FFmpeg..."
            },
            "verifying": {
                ENGLISH: "Verifying",
                CHINESE: "正在验证"
            },
            "verifying_ffmpeg": {
                ENGLISH: "Verifying FFmpeg...",
                CHINESE: "正在验证 FFmpeg..."
            },
            "ffmpeg_detected": {
                ENGLISH: "FFmpeg detected",
                CHINESE: "FFmpeg 检测完成"
            },
            "ffmpeg_not_detected": {
                ENGLISH: "FFmpeg not detected",
                CHINESE: "未检测到 FFmpeg"
            },
            "ffmpeg_available": {
                ENGLISH: "FFmpeg Available",
                CHINESE: "FFmpeg 可用"
            },
            "ffmpeg_available_message": {
                ENGLISH: "FFmpeg is installed. Duration classification feature can work properly.",
                CHINESE: "FFmpeg 已安装，按时长分类功能可以正常工作"
            },
            "ffmpeg_not_available": {
                ENGLISH: "FFmpeg Not Available",
                CHINESE: "FFmpeg 不可用"
            },
            "ffmpeg_not_available_message": {
                ENGLISH: "FFmpeg not detected. Duration classification may not work properly. Please click 'Browse FFmpeg' to set manually.",
                CHINESE: "未检测到 FFmpeg，按时长分类功能可能无法正常工作请点击'浏览 FFmpeg'手动设置"
            },
            "ffmpeg_available_info": {
                ENGLISH: "FFmpeg is available. Duration classification feature can work properly.",
                CHINESE: "FFmpeg 可用，按时长分类功能可以正常工作"
            },
            "ffmpeg_available_info_path": {
                ENGLISH: "FFmpeg is available at: {}. Duration classification feature can work properly.",
                CHINESE: "FFmpeg 可用，路径：{}按时长分类功能可以正常工作"
            },
            "success": {
                ENGLISH: "Success",
                CHINESE: "成功"
            },
            "error": {
                ENGLISH: "Error",
                CHINESE: "错误"
            },
            "ffmpeg_set_success": {
                ENGLISH: "FFmpeg path set successfully",
                CHINESE: "FFmpeg 路径设置成功"
            },
            "invalid_ffmpeg": {
                ENGLISH: "The selected file is not a valid FFmpeg executable",
                CHINESE: "所选文件不是有效的 FFmpeg 可执行文件"
            },
            "ffmpeg_error": {
                ENGLISH: "FFmpeg verification failed: {}",
                CHINESE: "FFmpeg 验证失败: {}"
            },
            "select_ffmpeg": {
                ENGLISH: "Select FFmpeg Executable",
                CHINESE: "选择 FFmpeg 可执行文件"
            },
            "select_ffmpeg_file": {
                ENGLISH: "Select FFmpeg Executable",
                CHINESE: "选择 FFmpeg 可执行文件"
            },
            # 新增翻译项
            "auto_open_output_dir": {
                ENGLISH: "Auto open output directory after extraction",
                CHINESE: "提取完成后自动打开输出目录"
            },
            "auto_open_toggled": {
                ENGLISH: "Auto open directory option toggled",
                CHINESE: "自动打开目录选项已切换"
            },
            # JustKanade 头像组件翻译
            "visit_github": {
                ENGLISH: "Visit GitHub",
                CHINESE: "访问GitHub"
            },
            "confirm_visit_github": {
                ENGLISH: "Do you want to visit JustKanade's GitHub page?",
                CHINESE: "是否跳转至JustKanade的GitHub主页？"
            },
            # Debug模式相关翻译
            "debug_mode": {
                ENGLISH: "Debug Mode",
                CHINESE: "调试模式"
            },
            "debug_mode_description": {
                ENGLISH: "Generate error logs when application crashes",
                CHINESE: "在程序崩溃时生成错误日志"
            },
            "debug_mode_tip": {
                ENGLISH: "",
                CHINESE: ""
            },
            "debug_mode_enabled": {
                ENGLISH: "Debug Mode Enabled",
                CHINESE: "调试模式已启用"
            },
            "debug_mode_disabled": {
                ENGLISH: "Debug Mode Disabled",
                CHINESE: "调试模式已禁用"
            },
            "debug_mode_enabled_tip": {
                ENGLISH: "The application will generate detailed error logs when crashes occur",
                CHINESE: "程序将在崩溃时生成详细的错误日志"
            },
            "debug_mode_disabled_tip": {
                ENGLISH: "No error logs will be generated when crashes occur",
                CHINESE: "程序崩溃时不会生成错误日志"
            },
            "open_error_logs_folder": {
                ENGLISH: "Open Error Logs",
                CHINESE: "打开崩溃日志"
            },
            "error_logs_folder_description": {
                ENGLISH: "View detailed logs generated when the program crashes",
                CHINESE: "查看程序崩溃时生成的详细日志"
            },
            "open_folder_success": {
                ENGLISH: "Open Folder Success",
                CHINESE: "打开文件夹成功"
            },
            "error_logs_folder_opened": {
                ENGLISH: "Error logs folder has been opened",
                CHINESE: "已打开错误日志文件夹"
            },
            "open_folder_failed": {
                ENGLISH: "Open Folder Failed",
                CHINESE: "打开文件夹失败"
            },
            "error_opening_folder": {
                ENGLISH: "Error opening folder: {}",
                CHINESE: "打开文件夹时出错: {}"
            },
            "click_for_more_info": {
                ENGLISH: "Click for more information",
                CHINESE: "点击获取更多信息"
            },
            "debug_mode_help": {
                ENGLISH: "Debug Mode Information",
                CHINESE: "调试模式说明"
            },
            "app_settings": {
                ENGLISH: "Application Settings",
                CHINESE: "应用程序设置"
            },
            # 全局输入路径相关
            "global_input_path_title": {
                ENGLISH: "Global Input Path",
                CHINESE: "全局输入路径"
            },
            "global_input_path_description": {
                ENGLISH: "Set a global unified input path that will be applied to all extraction operations",
                CHINESE: "设置全局统一的输入路径，将应用于所有提取操作"
            },
            "input_dir_placeholder": {
                ENGLISH: "Enter folder path",
                CHINESE: "输入文件夹路径"
            },
            "global_input_path_hint": {
                ENGLISH: "When set, this will override the default Roblox path",
                CHINESE: "设置后将覆盖默认的Roblox路径"
            },
            "select_directory": {
                ENGLISH: "Select Directory",
                CHINESE: "选择目录"
            },
            "default_roblox_path_set": {
                ENGLISH: "Default Roblox path set",
                CHINESE: "已设置默认Roblox路径"
            },
            "using_global_input_path": {
                ENGLISH: "Using global input path",
                CHINESE: "使用全局输入路径"
            },
            "restore_default_path_hint": {
                ENGLISH: "Press Enter to restore default Roblox path",
                CHINESE: "按Enter键恢复默认Roblox路径"
            },
            "default_path_restored": {
                ENGLISH: "Default Roblox path restored",
                CHINESE: "已恢复默认Roblox路径"
            },
            "path_manager_not_available": {
                ENGLISH: "Path manager not available",
                CHINESE: "路径管理器不可用"
            },
            "press_enter_restore_path": {
                ENGLISH: "Press Enter to restore default Roblox Cache path",
                CHINESE: "按Enter恢复默认Roblox缓存路径"
            },
            "copied": {
                ENGLISH: "Copied",
                CHINESE: "已复制"
            },
            "path_copied_to_clipboard": {
                ENGLISH: "Path copied to clipboard: {}",
                CHINESE: "路径已复制到剪贴板：{}"
            },
            
            # 版本检查设置相关
            "version_check_description": {
                ENGLISH: "Manage application version checking and update settings",
                CHINESE: "管理应用程序版本检查和更新设置"
            },
            "latest_version": {
                ENGLISH: "Latest version",
                CHINESE: "最新版本"
            },
            "release_notes": {
                ENGLISH: "Release Notes",
                CHINESE: "更新说明"
            },
            "download_update": {
                ENGLISH: "Download Update",
                CHINESE: "下载更新"
            },
            "cancel": {
                ENGLISH: "Cancel",
                CHINESE: "取消"
            },
            "check_failed": {
                ENGLISH: "Check Failed",
                CHINESE: "检查失败"
            },
            
            # FFmpeg状态相关
            "ffmpeg_description": {
                ENGLISH: "Detect and manage FFmpeg installation status",
                CHINESE: "检测和管理FFmpeg安装状态"
            },
            "ffmpeg_found_in_path": {
                ENGLISH: "Found FFmpeg in system PATH",
                CHINESE: "在系统PATH中找到FFmpeg"
            },
            "ffmpeg_found_at": {
                ENGLISH: "Found FFmpeg at",
                CHINESE: "找到FFmpeg"
            },
            "ffmpeg_ready": {
                ENGLISH: "FFmpeg is ready, duration classification feature can work properly",
                CHINESE: "FFmpeg已准备就绪，时长分类功能可正常工作"
            },
            "ffmpeg_not_found": {
                ENGLISH: "Not Found",
                CHINESE: "未找到"
            },
            "ffmpeg_install_hint": {
                ENGLISH: "Please install FFmpeg to enable audio duration classification",
                CHINESE: "请安装FFmpeg以启用音频时长分类功能"
            },
            "ffmpeg_install_instruction": {
                ENGLISH: "Please install FFmpeg to enable audio duration classification. You can manually specify FFmpeg path",
                CHINESE: "请安装FFmpeg以启用音频时长分类功能您可以手动指定FFmpeg路径"
            },
            "ffmpeg_custom_path": {
                ENGLISH: "Custom path",
                CHINESE: "自定义路径"
            },
            "ffmpeg_set_success": {
                ENGLISH: "FFmpeg Setup Successful",
                CHINESE: "FFmpeg设置成功"
            },
            "ffmpeg_path_updated": {
                ENGLISH: "FFmpeg path has been updated",
                CHINESE: "FFmpeg路径已更新"
            },
            "invalid_ffmpeg": {
                ENGLISH: "Invalid FFmpeg File",
                CHINESE: "无效的FFmpeg文件"
            },
            "invalid_ffmpeg_hint": {
                ENGLISH: "The selected file is not a valid FFmpeg executable",
                CHINESE: "选择的文件不是有效的FFmpeg可执行文件"
            },
            "ffmpeg_test_failed": {
                ENGLISH: "FFmpeg Test Failed",
                CHINESE: "FFmpeg测试失败"
            },
            "ffmpeg_test_error": {
                ENGLISH: "Unable to run the selected FFmpeg file",
                CHINESE: "无法运行选择的FFmpeg文件"
            },
            
            # 全局输入路径相关
            "current_path": {
                ENGLISH: "Current Path",
                CHINESE: "当前路径"
            },
            "path_hint": {
                ENGLISH: "Tip: Leave empty to use default Roblox cache path",
                CHINESE: "提示：留空将使用默认的Roblox缓存路径"
            },
            
            # 启动文件相关
            "launch": {
                ENGLISH: "Launch",
                CHINESE: "启动"
            },
            "launch_file_title": {
                ENGLISH: "Launch File",
                CHINESE: "启动文件"
            },
            "launch_file_description": {
                ENGLISH: "Select a file to be executed when clicking the Launch button",
                CHINESE: "选择一个文件，当点击启动按钮时执行"
            },
            "select_executable": {
                ENGLISH: "Select Executable File",
                CHINESE: "选择可执行文件"
            },
            "launch_file_placeholder": {
                ENGLISH: "Select an executable file to launch",
                CHINESE: "选择要启动的可执行文件"
            },
            "launch_success": {
                ENGLISH: "Launch Successful",
                CHINESE: "启动成功"
            },
            "launch_failed": {
                ENGLISH: "Launch Failed",
                CHINESE: "启动失败"
            },
            "file_launched": {
                ENGLISH: "File launched: {}",
                CHINESE: "文件已启动：{}"
            },
            "file_not_found": {
                ENGLISH: "Launch file not found: {}",
                CHINESE: "启动文件未找到：{}"
            },
            "no_launch_file_set": {
                ENGLISH: "No launch file configured. Please set one in Settings.",
                CHINESE: "未配置启动文件请在设置中配置"
            },
            "launch_error": {
                ENGLISH: "Error launching file: {}",
                CHINESE: "启动文件时出错：{}"
            },
            
            # 启动文件状态更新
            "launch_file_updated": {
                ENGLISH: "Launch file updated: {}",
                CHINESE: "启动文件已更新：{}"
            },
            "launch_file_cleared": {
                ENGLISH: "Launch file cleared",
                CHINESE: "启动文件已清除"
            },
            
            # 设置界面分组标题
            "interface_settings": {
                ENGLISH: "Interface Settings",
                CHINESE: "界面设置"
            },
            "performance_settings": {
                ENGLISH: "Performance Settings", 
                CHINESE: "性能设置"
            },
            "system_info_settings": {
                ENGLISH: "System Information",
                CHINESE: "系统信息"
            },
            
            # 设置项描述文本
            "language_description": {
                ENGLISH: "Select interface language",
                CHINESE: "选择界面语言"
            },
            "theme_description": {
                ENGLISH: "Select application theme",
                CHINESE: "选择应用主题"
            },
            "auto_open_description": {
                ENGLISH: "Automatically open output directory after extraction",
                CHINESE: "提取完成后自动打开输出目录"
            },
            "threads_description": {
                ENGLISH: "Set the default number of threads for extraction tasks",
                CHINESE: "设置提取任务的默认线程数"
            },
            "theme_color_description": {
                ENGLISH: "Change the theme color of the application", 
                CHINESE: "更改应用程序的主题颜色"
            },
            
            # 界面缩放相关翻译
            "interface_zoom": {
                ENGLISH: "Interface zoom",
                CHINESE: "界面缩放"
            },
            "interface_zoom_description": {
                ENGLISH: "Change the size of widgets and fonts",
                CHINESE: "调整小部件和字体的大小"
            },
            "use_system_setting": {
                ENGLISH: "Use system setting",
                CHINESE: "使用系统设置"
            },
            "zoom_changed": {
                ENGLISH: "Interface zoom changed to: {}",
                CHINESE: "界面缩放已更改为：{}"
            },
            "zoom_restart_required": {
                ENGLISH: "Restart Required",
                CHINESE: "需要重启"
            },
            "zoom_restart_message": {
                ENGLISH: "The interface zoom change will take effect after restarting the application.\n\nWould you like to close the application now?",
                CHINESE: "界面缩放更改将在重启应用程序后生效\n\n您想要现在关闭应用程序吗？"
            },
            "zoom_setting_saved": {
                ENGLISH: "Interface zoom setting saved. Please restart the application.",
                CHINESE: "界面缩放设置已保存请重启应用程序"
            },
            
            "theme_color_settings": {
                ENGLISH: "Theme Color Settings",
                CHINESE: "主题颜色设置" 
            },
            "log_management_description": {
                ENGLISH: "Export logs to file or clear all log entries",
                CHINESE: "将日志导出到文件或清除所有日志条目"
            },
            
            # 日志消息相关翻译
            "using_custom_output_dir": {
                ENGLISH: "Using custom output directory",
                CHINESE: "使用自定义输出目录"
            },
            "using_default_output_dir": {
                ENGLISH: "Using default output directory (based on input directory)",
                CHINESE: "使用默认输出目录（基于输入目录）"
            },
            "audio_format_conversion_enabled": {
                ENGLISH: "Audio format conversion enabled",
                CHINESE: "音频格式转换启用"
            },
            "audio_format_conversion_disabled": {
                ENGLISH: "Audio format conversion disabled",
                CHINESE: "音频格式转换禁用"
            },
            "audio_format_set_to": {
                ENGLISH: "Audio format set to",
                CHINESE: "音频格式已设置为"
            },
            "global_input_path_synced": {
                ENGLISH: "Global input path synchronized",
                CHINESE: "全局输入路径已同步"
            },
            "global_input_path_updated": {
                ENGLISH: "Global input path updated",
                CHINESE: "全局输入路径已更新"
            },
            "avatar_auto_update_setting": {
                ENGLISH: "Disable avatar auto-update",
                CHINESE: "禁用头像自动更新"
            },
            "enabled": {
                ENGLISH: "Enabled",
                CHINESE: "启用"
            },
            "disabled": {
                ENGLISH: "Disabled",
                CHINESE: "禁用"
            },
            
            # 预处理去重相关翻译
            "preprocessing_files": {
                ENGLISH: "Preprocessing files for deduplication...",
                CHINESE: "正在对文件进行预处理去重..."
            },
            "preprocessing_complete": {
                ENGLISH: "Preprocessing complete: found {} duplicates, skipped {} already processed",
                CHINESE: "预处理完成：发现 {} 个重复文件，跳过 {} 个已处理文件"
            },
            "final_processing": {
                ENGLISH: "Processing {} unique files (preprocessing took {:.2f} seconds)",
                CHINESE: "最终处理 {} 个唯一文件（预处理耗时 {:.2f} 秒）"
            },
            "calculating_content_hash": {
                ENGLISH: "Calculating content hashes...",
                CHINESE: "正在计算内容哈希..."
            },
            "deduplication_stats": {
                ENGLISH: "Deduplication completed: {} duplicates removed, {} already processed skipped",
                CHINESE: "去重完成：移除 {} 个重复文件，跳过 {} 个已处理文件"
            },
            "multiprocess_preprocessing": {
                ENGLISH: "Using {} processes for preprocessing...",
                CHINESE: "使用 {} 个进程进行预处理..."
            },
            
            # 多进程警告对话框相关翻译
            "multiprocessing_warning_title": {
                ENGLISH: "Multiprocessing Mode Warning",
                CHINESE: "多进程模式警告"
            },
            "multiprocessing_warning_message": {
                ENGLISH: "Multiprocessing mode is an experimental feature that may:\n\n• Consume more system resources\n• Potentially cause instability\n• Require more memory\n\nThis feature aims to improve performance for large-scale extraction tasks.\n\nAre you sure you want to enable multiprocessing mode?",
                CHINESE: "多进程模式是一个实验性功能，可能会：\n\n• 消耗更多系统资源\n• 可能导致不稳定\n• 需要更多内存\n\n此功能旨在提升大规模提取任务的性能\n\n您确定要启用多进程模式吗？"
            },
            "enable_multiprocessing": {
                ENGLISH: "Enable",
                CHINESE: "启用"
            },
            "cancel_multiprocessing": {
                ENGLISH: "Cancel",
                CHINESE: "取消"
            },
            "multiprocessing_enabled": {
                ENGLISH: "Multiprocessing mode has been enabled",
                CHINESE: "多进程模式已启用"
            },
            "multiprocessing_disabled": {
                ENGLISH: "Multiprocessing mode has been disabled",
                CHINESE: "多进程模式已禁用"
            },
            "parent_window_not_available": {
                ENGLISH: "Unable to access main window",
                CHINESE: "无法访问主窗口"
            },
            "no_history_to_clear": {
                ENGLISH: "No history records to clear",
                CHINESE: "暂无历史记录可清除"
            },
            "font_records": {
                ENGLISH: "Font Records",
                CHINESE: "字体记录"
            },
            "saving_font_history": {
                ENGLISH: "Saving font extraction history...",
                CHINESE: "正在保存字体提取历史记录..."
            },
            "extract_menu_button_title": {
                ENGLISH: "Extract Content",
                CHINESE: "内容提取"
            },
            "extract_menu_button_description": {
                ENGLISH: "Choose extraction type and access related functions",
                CHINESE: "选择提取类型并访问相关功能"
            },
            "extract_menu_button_text": {
                ENGLISH: "Start Extraction",
                CHINESE: "开始提取"
            },
            "extract_audio_menu_item": {
                ENGLISH: "Extract Audio",
                CHINESE: "提取音频"
            },
            "extract_fonts_menu_item": {
                ENGLISH: "Extract Fonts",
                CHINESE: "提取字体"
            },
            # Translation提取相关翻译
            "extract_translations": {
                ENGLISH: "Translations",
                CHINESE: "翻译文件"
            },
            "extract_translations_menu_item": {
                ENGLISH: "Extract Translations Files",
                CHINESE: "提取翻译文件"
            },
            "extract_videos_menu_item": {
                ENGLISH: "Videos",
                CHINESE: "视频"
            },
            "extract_translation_title": {
                ENGLISH: "Extract Translations Files",
                CHINESE: "提取翻译文件"
            },
            "extract_translations_title": {
                ENGLISH: "Translation Files",
                CHINESE: "翻译文件"
            },
            "extract_translations_description": {
                ENGLISH: "Extract translation files from Roblox cache for localization analysis",
                CHINESE: "从 Roblox 缓存中提取翻译文件用于本地化分析"
            },
            # Translation分类方法相关
            "by_locale": {
                ENGLISH: "By Locale",
                CHINESE: "按语言区域"
            },
            "by_content_type": {
                ENGLISH: "Content Type",
                CHINESE: "按内容类型"
            },
            "combined_classification": {
                ENGLISH: "Combined Classification",
                CHINESE: "组合分类"
            },
            "translation_classification_method": {
                ENGLISH: "Translation Classification Method",
                CHINESE: "翻译文件分类方法"
            },
            # Translation处理选项相关
            "enable_translation_processing": {
                ENGLISH: "Enable Translation Processing",
                CHINESE: "启用翻译文件处理"
            },
            "process_translation_files": {
                ENGLISH: "Process and save discovered translation files",
                CHINESE: "处理和保存发现的翻译文件"
            },
            # Translation分类说明相关
            "info_locale_classification": {
                ENGLISH: "Translation files will be classified by language locale, such as zh-cn",
                CHINESE: "翻译文件将按语言区域分类存储，如 zh-cn"
            },
            "info_content_type_classification": {
                ENGLISH: "Translation files will be classified by content type",
                CHINESE: "翻译文件将按内容类型分类存储"
            },
            "info_combined_classification": {
                ENGLISH: "Translation files will be classified by both language locale and content type",
                CHINESE: "翻译文件将按语言区域和内容类型组合分类存储"
            },
            # Translation输出目录相关
            "translations_folder": {
                ENGLISH: "Translations folder",
                CHINESE: "翻译文件总文件夹"
            },
            "translations_category": {
                ENGLISH: "Translation files",
                CHINESE: "翻译文件"
            },
            # Translation提取器日志相关
            "initializing_translation_extractor": {
                ENGLISH: "Initializing translation extractor...",
                CHINESE: "正在初始化翻译文件提取器..."
            },
            "starting_translation_extraction": {
                ENGLISH: "Starting translation extraction...",
                CHINESE: "开始翻译文件提取..."
            },
            "processing_translation": {
                ENGLISH: "Processing translation file: {} ({})",
                CHINESE: "处理翻译文件: {} ({})"
            },
            "translation_save_success": {
                ENGLISH: "Successfully saved translation file: {}",
                CHINESE: "成功保存翻译文件: {}"
            },
            "saving_translation_history": {
                ENGLISH: "Saving translation extraction history...",
                CHINESE: "正在保存翻译文件提取历史记录..."
            },
            "translation_extraction_complete": {
                ENGLISH: "Translation extraction complete! Found {} translation files, successfully saved {} files (took {:.1f} seconds)",
                CHINESE: "翻译文件提取完成! 发现{}个翻译文件，成功保存{}个文件 (耗时{:.1f}秒)"
            },
            "translation_extraction_failed": {
                ENGLISH: "Translation extraction failed: {}",
                CHINESE: "翻译文件提取失败: {}"
            },
            "processing": {
                ENGLISH: "Processing...",
                CHINESE: "处理中..."
            },
            # 历史记录类型显示名称
            "audio_history": {
                ENGLISH: "Audio Files",
                CHINESE: "音频文件"
            },
            "font_history": {
                ENGLISH: "Font Files",
                CHINESE: "字体文件"
            },
            "translation_history": {
                ENGLISH: "Translation Files",
                CHINESE: "翻译文件"
            },
            "video_history": {
                ENGLISH: "Video Files", 
                CHINESE: "视频文件"
            },
            "image_history": {
                ENGLISH: "Image Files",
                CHINESE: "图片文件"
            },
            "texture_history": {
                ENGLISH: "Texture Files",
                CHINESE: "纹理文件"
            },
            "model_history": {
                ENGLISH: "Model Files",
                CHINESE: "模型文件"
            },
            "other_history": {
                ENGLISH: "Other Files",
                CHINESE: "其他文件"
            },
            # 翻译文件提取统计信息
            "translation_found": {
                ENGLISH: "Translation files found",
                CHINESE: "发现翻译文件"
            },
            "translation_saved": {
                ENGLISH: "Translation files saved",
                CHINESE: "保存翻译文件"
            },
            
            # 捐款相关翻译
            "donation": {
                ENGLISH: "Donation",
                CHINESE: "捐款"
            },
            "donation_title": {
                ENGLISH: "Support Development",
                CHINESE: "支持开发"
            },
            "donation_description": {
                ENGLISH: "If this tool has been helpful to you, consider supporting development through donation.",
                CHINESE: "如果这个工具对您有帮助，请考虑通过捐款支持开发"
            },
            "wechat_pay": {
                ENGLISH: "WeChat Pay",
                CHINESE: "微信支付"
            },
            "scan_qr_code": {
                ENGLISH: "Scan QR Code to Donate",
                CHINESE: "扫描二维码进行捐款"
            },
            "view_qr_code": {
                ENGLISH: "View QR Code",
                CHINESE: "查看二维码"
            },
            "support_development": {
                ENGLISH: "Support Development",
                CHINESE: "支持开发"
            },
            "donation_thanks": {
                ENGLISH: "Thank you for your support!",
                CHINESE: "感谢您的支持！"
            },
            "donation_note": {
                ENGLISH: "Your donation helps maintain and improve this free tool.",
                CHINESE: "您的捐款有助于维护和改进这个免费工具"
            },
            # 捐款确认对话框相关翻译
            "donation_confirm_title": {
                ENGLISH: "Support Development",
                CHINESE: "支持开发"
            },
            "donation_confirm_message": {
                ENGLISH: "This program is maintained and developed by me alone. Development is not easy. Would you consider donating?",
                CHINESE: "本程序仅由我一人维护和开发，开发不易，是否考虑捐款？"
            },

            # 系统托盘相关翻译
            "show_main_window": {
                ENGLISH: "Show Main Window",
                CHINESE: "显示主窗口"
            },
            "exit_program": {
                ENGLISH: "Exit Program",
                CHINESE: "退出程序"
            },
            "tray_tooltip": {
                ENGLISH: "Roblox Audio Extractor",
                CHINESE: "Roblox 音频提取器"
            },

            # 首次关闭窗口对话框相关翻译
            "close_behavior_dialog_title": {
                ENGLISH: "Close Window Behavior",
                CHINESE: "关闭窗口行为"
            },
            "close_behavior_dialog_message": {
                ENGLISH: "What would you like to do when clicking the close button?",
                CHINESE: "当点击关闭按钮时，您希望执行什么操作？"
            },
            "close_program_directly": {
                ENGLISH: "Close Program Directly",
                CHINESE: "直接关闭程序"
            },
            "minimize_to_tray": {
                ENGLISH: "Minimize to System Tray",
                CHINESE: "最小化到系统托盘"
            },
            "remember_choice": {
                ENGLISH: "Remember my choice",
                CHINESE: "记住我的选择"
            },
            "close_behavior_saved": {
                ENGLISH: "Close behavior preference saved",
                CHINESE: "关闭行为偏好已保存"
            },
            "ok": {
                ENGLISH: "OK",
                CHINESE: "确定"
            },

            # 关闭行为设置相关翻译
            "close_behavior_settings": {
                ENGLISH: "Close Behavior Settings",
                CHINESE: "关闭行为设置"
            },
            "close_behavior_settings_desc": {
                ENGLISH: "Configure how the program behaves when the close button is clicked",
                CHINESE: "配置点击关闭按钮时程序的行为方式"
            },
            "close_behavior_ask": {
                ENGLISH: "Ask every time",
                CHINESE: "每次询问"
            },
            "close_behavior_close": {
                ENGLISH: "Close program directly",
                CHINESE: "直接关闭程序"
            },
            "close_behavior_minimize": {
                ENGLISH: "Minimize to system tray",
                CHINESE: "最小化到系统托盘"
            },
            
            # SafeStateTooltipManager 相关翻译
            "tooltip_create_failed": {
                ENGLISH: "Failed to create status tooltip",
                CHINESE: "状态提示创建失败"
            },
            "tooltip_update_failed": {
                ENGLISH: "Failed to update status tooltip",
                CHINESE: "状态提示更新失败"
            },
            "tooltip_close_failed": {
                ENGLISH: "Failed to close status tooltip",
                CHINESE: "状态提示关闭失败"
            },
            "tooltip_object_deleted": {
                ENGLISH: "Status tooltip was cleaned up by system",
                CHINESE: "状态提示已被系统清理"
            },
            "tooltip_unknown_error": {
                ENGLISH: "Unknown error occurred with status tooltip",
                CHINESE: "状态提示发生未知错误"
            },
            "warning": {
                ENGLISH: "Warning",
                CHINESE: "警告"
            },
            "cancelling": {
                ENGLISH: "Cancelling...",
                CHINESE: "正在取消..."
            },
            
            # 视频提取相关翻译键
            "videos_folder": {
                ENGLISH: "Videos folder",
                CHINESE: "视频总文件夹"
            },
            "videos_category": {
                ENGLISH: "Video files",
                CHINESE: "视频文件"
            },
            "video_extraction_complete": {
                ENGLISH: "Video extraction completed!",
                CHINESE: "视频提取完成！"
            },
            "videos_processed": {
                ENGLISH: "Videos processed",
                CHINESE: "处理视频"
            },
            "segments_downloaded": {
                ENGLISH: "Segments downloaded",
                CHINESE: "下载片段"
            },
            "videos_merged": {
                ENGLISH: "Videos merged",
                CHINESE: "合并视频"
            },
            "duplicate_videos": {
                ENGLISH: "Duplicate videos skipped",
                CHINESE: "跳过重复视频"
            },
            "download_failures": {
                ENGLISH: "Download failures",
                CHINESE: "下载失败"
            },
            "ffmpeg_required": {
                ENGLISH: "FFmpeg Required",
                CHINESE: "需要FFmpeg"
            },
            "video_ffmpeg_warning": {
                ENGLISH: "⚠ FFmpeg is required for video processing. Please install FFmpeg to enable video merging functionality.",
                CHINESE: "⚠ 视频处理需要FFmpeg。请安装FFmpeg以启用视频合并功能"
            },
            "network_settings": {
                ENGLISH: "Network Settings",
                CHINESE: "网络设置"
            },
            "storage_settings": {
                ENGLISH: "Storage Settings",
                CHINESE: "存储设置"
            },
            "concurrent_downloads": {
                ENGLISH: "Concurrent Segment Downloads",
                CHINESE: "并发片段下载"
            },
            "concurrent_downloads_desc": {
                ENGLISH: "Enable parallel downloading of video segments for faster processing",
                CHINESE: "启用并行下载视频片段以提高处理速度"
            },
            "concurrent_downloads_enabled": {
                ENGLISH: "Concurrent downloads enabled",
                CHINESE: "已启用并发下载"
            },
            "concurrent_downloads_disabled": {
                ENGLISH: "Concurrent downloads disabled",
                CHINESE: "已禁用并发下载"
            },
            "auto_cleanup_temp": {
                ENGLISH: "Auto Clean Temporary Files",
                CHINESE: "自动清理临时文件"
            },
            "auto_cleanup_temp_desc": {
                ENGLISH: "Automatically clean up temporary segment files after video processing",
                CHINESE: "视频处理完成后自动清理临时片段文件"
            },
            "auto_cleanup_enabled": {
                ENGLISH: "Auto cleanup enabled",
                CHINESE: "已启用自动清理"
            },
            "auto_cleanup_disabled": {
                ENGLISH: "Auto cleanup disabled",
                CHINESE: "已禁用自动清理"
            },
            "settings_updated": {
                ENGLISH: "Settings Updated",
                CHINESE: "设置已更新"
            },
            "seconds": {
                ENGLISH: "seconds",
                CHINESE: "秒"
            },
            # 视频提取过程相关翻译
            "video_initializing_extractor": {
                ENGLISH: "Initializing video extractor...",
                CHINESE: "初始化视频提取器..."
            },
            "video_scanning_cache": {
                ENGLISH: "Scanning video cache...",
                CHINESE: "开始扫描视频缓存..."
            },
            "video_extraction_cancelled": {
                ENGLISH: "Video extraction cancelled",
                CHINESE: "视频提取已取消"
            },
            "video_processing_complete": {
                ENGLISH: "Video processing complete!",
                CHINESE: "视频处理完成！"
            },
            "video_extraction_failed": {
                ENGLISH: "Video extraction failed",
                CHINESE: "视频提取失败"
            },
            "video_extraction_error": {
                ENGLISH: "Error occurred during video extraction: {}",
                CHINESE: "视频提取过程中发生错误：{}"
            },
            "video_error_details": {
                ENGLISH: "Error details: {}",
                CHINESE: "错误详情：{}"
            },
            "video_cancelling": {
                ENGLISH: "Cancelling video extraction...",
                CHINESE: "正在取消视频提取..."
            },
            "video_total_duration": {
                ENGLISH: "Total duration: {:.2f} seconds",
                CHINESE: "总耗时：{:.2f} 秒"
            },
            "video_output_directory": {
                ENGLISH: "Output directory: {}",
                CHINESE: "输出目录：{}"
            },
            "video_processed_count": {
                ENGLISH: "Videos processed: {} items",
                CHINESE: "处理视频：{} 个"
            },
            "video_segments_downloaded": {
                ENGLISH: "Segments downloaded: {} items",
                CHINESE: "下载片段：{} 个"
            },
            "video_merged_count": {
                ENGLISH: "Videos merged: {} items",
                CHINESE: "合并视频：{} 个"
            },
            "video_duplicates_skipped": {
                ENGLISH: "Duplicates skipped: {} items",
                CHINESE: "跳过重复：{} 个"
            },
            "video_download_failures": {
                ENGLISH: "Download failures: {} items",
                CHINESE: "下载失败：{} 个"
            },
            "video_progress_update": {
                ENGLISH: "Processing progress: {}/{} ({}%)",
                CHINESE: "处理进度：{}/{} ({}%)"
            },
            # 视频扫描和识别相关
            "video_scanning_cache_start": {
                ENGLISH: "Starting video cache scan...",
                CHINESE: "开始扫描视频缓存..."
            },
            "video_no_cache_items": {
                ENGLISH: "No cache items found",
                CHINESE: "未找到缓存项"
            },
            "video_cache_items_found": {
                ENGLISH: "Found {} cache items",
                CHINESE: "找到 {} 个缓存项"
            },
            "video_playlists_found": {
                ENGLISH: "Found {} video playlists",
                CHINESE: "找到 {} 个视频播放列表"
            },
            "video_no_content_found": {
                ENGLISH: "No video content found",
                CHINESE: "未找到视频内容"
            },
            # 视频质量选择相关
            "video_quality_selection": {
                ENGLISH: "Video Quality Selection",
                CHINESE: "视频质量选择"
            },
            "video_quality_auto": {
                ENGLISH: "Auto (Best Quality)",
                CHINESE: "自动（最佳质量）"
            },
            "video_quality_1080p": {
                ENGLISH: "1080p",
                CHINESE: "1080p"
            },
            "video_quality_720p": {
                ENGLISH: "720p",
                CHINESE: "720p"
            },
            "video_quality_480p": {
                ENGLISH: "480p",
                CHINESE: "480p"
            },
            "video_quality_lowest": {
                ENGLISH: "Lowest Available",
                CHINESE: "最低可用质量"
            },
            "video_quality_desc": {
                ENGLISH: "Select preferred video quality for extraction. ",
                CHINESE: "选择视频提取的首选质量"
            },
            "video_timestamp_repair": {
                ENGLISH: "Video Timestamp Repair",
                CHINESE: "视频时间戳修复"
            },
            "video_timestamp_repair_desc": {
                ENGLISH: "Automatically repair video segment timestamps for smooth playback (requires FFmpeg)",
                CHINESE: "自动修复视频片段时间戳以确保流畅播放（需要FFmpeg）"
            },
            "video_timestamp_repair_enabled": {
                ENGLISH: "Timestamp repair enabled",
                CHINESE: "已启用时间戳修复"
            },
            "video_timestamp_repair_disabled": {
                ENGLISH: "Timestamp repair disabled",
                CHINESE: "已禁用时间戳修复"
            },
            "video_repairing_segment": {
                ENGLISH: "Repairing video segment: {}",
                CHINESE: "修复视频片段：{}"
            },
            "video_repair_failed": {
                ENGLISH: "Video segment repair failed: {}",
                CHINESE: "视频片段修复失败：{}"
            },
            "video_repair_complete": {
                ENGLISH: "Video segment repair completed",
                CHINESE: "视频片段修复完成"
            },
            "video_selected_quality": {
                ENGLISH: "Selected video quality: {}",
                CHINESE: "选择的视频质量：{}"
            },
            "video_quality_not_available": {
                ENGLISH: "Requested quality {} not available, using: {}",
                CHINESE: "请求的质量 {} 不可用，使用：{}"
            },
            "video_processing_settings": {
                ENGLISH: "Video Processing",
                CHINESE: "视频处理"
            },

            
            # 视频格式转换相关
            "video_format_conversion": {
                ENGLISH: "Video Format Conversion",
                CHINESE: "视频格式转换"
            },
            "convert_video_format": {
                ENGLISH: "Convert Video Format",
                CHINESE: "转换视频格式"
            },
            "convert_video_format_desc": {
                ENGLISH: "Convert videos to specified format using FFmpeg",
                CHINESE: "使用FFmpeg将视频转换为指定格式"
            },
            "output_video_format": {
                ENGLISH: "Output Video Format",
                CHINESE: "输出视频格式"
            },
            "select_output_video_format": {
                ENGLISH: "Select the output video format",
                CHINESE: "选择输出视频格式"
            },
            "video_conversion_ffmpeg_warning": {
                ENGLISH: "⚠ FFmpeg is required for video format conversion. Please install FFmpeg to enable this feature.",
                CHINESE: "⚠ 视频格式转换需要FFmpeg。请安装FFmpeg以启用此功能。"
            },
            
            # 背景设置相关翻译
            "background_settings": {
                ENGLISH: "Background Settings",
                CHINESE: "背景设置"
            },
            "background_settings_description": {
                ENGLISH: "Customize application background image and effects",
                CHINESE: "自定义应用程序背景图片和效果"
            },
            "background_image_title": {
                ENGLISH: "Background Image",
                CHINESE: "背景图片"
            },
            "background_image_description": {
                ENGLISH: "Select a custom background image for the application",
                CHINESE: "为应用程序选择自定义背景图片"
            },
            "background_opacity_title": {
                ENGLISH: "Background Opacity",
                CHINESE: "背景透明度"
            },
            "background_opacity_description": {
                ENGLISH: "Adjust the opacity of the background image",
                CHINESE: "调整背景图片的透明度"
            },
            "background_blur_title": {
                ENGLISH: "Background Blur",
                CHINESE: "背景模糊"
            },
            "background_blur_description": {
                ENGLISH: "Adjust the blur radius of the background image",
                CHINESE: "调整背景图片的模糊半径"
            },

            "enable_background_image": {
                ENGLISH: "Enable Background Image",
                CHINESE: "启用背景图片"
            },
            "enable_background_image_description": {
                ENGLISH: "Show custom background image behind the interface",
                CHINESE: "在界面后方显示自定义背景图片"
            },
            "select_image": {
                ENGLISH: "Select Image",
                CHINESE: "选择图片"
            },
            "clear_image": {
                ENGLISH: "Clear Image",
                CHINESE: "清除图片"
            },
            "no_image_selected": {
                ENGLISH: "No image selected",
                CHINESE: "未选择图片"
            },
            "image_filter": {
                ENGLISH: "Image Files",
                CHINESE: "图片文件"
            },
            "image_selected": {
                ENGLISH: "Background image selected successfully",
                CHINESE: "背景图片选择成功"
            },
            "image_cleared": {
                ENGLISH: "Background image cleared successfully",
                CHINESE: "背景图片清除成功"
            },
            "image_select_failed": {
                ENGLISH: "Failed to select background image",
                CHINESE: "选择背景图片失败"
            },
            "background_updated": {
                ENGLISH: "Background settings updated",
                CHINESE: "背景设置已更新"
            },
            
            # 背景透明度相关翻译
            "background_opacity_changed": {
                ENGLISH: "Background opacity changed to: {}%",
                CHINESE: "：{}%"
            },
            "background_enabled": {
                ENGLISH: "Background image enabled",
                CHINESE: "背景图片已启用"
            },
            "background_disabled": {
                ENGLISH: "Background image disabled",
                CHINESE: "背景图片已禁用"
            },
            "background_image_changed": {
                ENGLISH: "Background image changed: {}",
                CHINESE: "背景图片已更改：{}"
            },
            "background_image_cleared_log": {
                ENGLISH: "Background image cleared",
                CHINESE: "背景图片已清除"
            },
            "background_settings_updated_log": {
                ENGLISH: "Background settings updated successfully",
                CHINESE: "背景设置更新成功"
            },
            "background_settings_update_failed": {
                ENGLISH: "Failed to update background settings: {}",
                CHINESE: "更新背景设置失败：{}"
            },
            
            # 背景功能禁用提示
            "background_disabled_tooltip": {
                ENGLISH: "Please enable background image function first",
                CHINESE: "请先启用背景图片功能"
            },
            
            # 背景模糊相关翻译
            "blur_disabled": {
                ENGLISH: "Off",
                CHINESE: "关闭"
            },
            "background_blur_changed": {
                ENGLISH: "Background blur radius changed to: {}",
                CHINESE: "背景模糊半径已更改为：{}"
            },
            "background_blur_disabled": {
                ENGLISH: "Background blur disabled",
                CHINESE: "背景模糊已关闭"
            },
            
            # 背景管理器日志翻译
            "background_cache_cleared": {
                ENGLISH: "Background cache and blur cache cleared",
                CHINESE: "背景样式缓存和模糊图片缓存已清除"
            },
            "blur_effect_not_implemented": {
                ENGLISH: "Blur effect setting: radius={} (not implemented yet)",
                CHINESE: "模糊效果设置: radius={} (暂未实现)"
            },
            "apply_blur_failed": {
                ENGLISH: "Failed to apply blur effect: {}",
                CHINESE: "应用模糊效果失败: {}"
            },
            "get_background_pixmap_failed": {
                ENGLISH: "Failed to get background pixmap: {}",
                CHINESE: "获取背景图片失败: {}"
            },
            "simple_blur_failed": {
                ENGLISH: "Simple blur processing failed: {}",
                CHINESE: "简单模糊处理失败: {}"
            },
            "background_settings_updated": {
                ENGLISH: "Background settings updated",
                CHINESE: "背景设置已更新"
            },
            
            # main.py中的错误信息翻译
            "draw_background_error": {
                ENGLISH: "Error drawing background image: {}",
                CHINESE: "绘制背景图片时出错: {}"
            },
            "update_background_settings_error": {
                ENGLISH: "Error updating background settings: {}",
                CHINESE: "更新背景设置时出错: {}"
            },
            "system_tray_unavailable": {
                ENGLISH: "System tray unavailable",
                CHINESE: "系统托盘不可用"
            },
            "set_tray_icon_failed": {
                ENGLISH: "Failed to set tray icon: {}",
                CHINESE: "设置托盘图标失败: {}"
            },
            "init_tray_failed": {
                ENGLISH: "Failed to initialize system tray: {}",
                CHINESE: "初始化系统托盘失败: {}"
            },
            "create_tray_menu_failed": {
                ENGLISH: "Failed to create tray menu: {}",
                CHINESE: "创建托盘菜单失败: {}"
            },
            "tray_activate_failed": {
                ENGLISH: "Tray icon activation event handling failed: {}",
                CHINESE: "托盘图标激活事件处理失败: {}"
            },
            "show_main_window_failed": {
                ENGLISH: "Failed to show main window: {}",
                CHINESE: "显示主窗口失败: {}"
            },
            "exit_app_failed": {
                ENGLISH: "Failed to exit application: {}",
                CHINESE: "退出应用程序失败: {}"
            },
            "close_event_failed": {
                ENGLISH: "Failed to handle window close event: {}",
                CHINESE: "处理窗口关闭事件失败: {}"
            },
            "show_close_dialog_failed": {
                ENGLISH: "Failed to show close behavior dialog: {}",
                CHINESE: "显示关闭行为对话框失败: {}"
            },
            "handle_close_choice_failed": {
                ENGLISH: "Failed to handle close behavior choice: {}",
                CHINESE: "处理关闭行为选择失败: {}"
            },
            "handle_cancel_failed": {
                ENGLISH: "Failed to handle cancel operation: {}",
                CHINESE: "处理取消操作失败: {}"
            },
            "set_app_icon_failed": {
                ENGLISH: "Unable to set application icon: {}",
                CHINESE: "无法设置应用图标: {}"
            },
            "show_splash_failed": {
                ENGLISH: "Unable to show splash screen: {}",
                CHINESE: "无法显示启动画面: {}"
            },
            
            # 缓存扫描器状态清理日志
            "audio_cache_scanner_cleared": {
                ENGLISH: "Audio cache scanner state cleared",
                CHINESE: "已清理音频缓存扫描器状态"
            },
            "video_cache_scanner_cleared": {
                ENGLISH: "Video cache scanner state cleared", 
                CHINESE: "已清理视频缓存扫描器状态"
            },
            "font_cache_scanner_cleared": {
                ENGLISH: "Font cache scanner state cleared",
                CHINESE: "已清理字体缓存扫描器状态"
            },
            "translation_cache_scanner_cleared": {
                ENGLISH: "Translation cache scanner state cleared",
                CHINESE: "已清理翻译缓存扫描器状态"
            },
            "global_cache_scanner_cleared": {
                ENGLISH: "Global cache scanner state cleared and force reset fallback flags",
                CHINESE: "已清理全局缓存扫描器状态并强制重置回退标志"
            },
            "scanner_instance_created": {
                ENGLISH: "Created global cache scanner instance for cleanup",
                CHINESE: "创建全局缓存扫描器实例以进行清理"
            },
            "cache_scanner_clear_error": {
                ENGLISH: "Error occurred while clearing {} cache scanner state: {}",
                CHINESE: "清理{}缓存扫描器状态时出错: {}"
            },
            
            # 基础术语
            "audio": {
                ENGLISH: "audio",
                CHINESE: "音频"
            },
            "videos": {
                ENGLISH: "video",
                CHINESE: "视频"
            },
            "font": {
                ENGLISH: "font",
                CHINESE: "字体"
            },
            "translation": {
                ENGLISH: "translation",
                CHINESE: "翻译"
            }

        }