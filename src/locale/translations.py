from enum import Enum, auto

# 统一的版本号常量
VERSION = "0.16.1"

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
                ENGLISH: "System Settings",
                CHINESE: "跟随系统设置"
            },
            "simplified_chinese": {
                ENGLISH: "zn-cn",
                CHINESE: "简体中文"
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
                CHINESE: "启用或禁用程序启动时的问候通知。",
                ENGLISH: "Enable or disable greeting notifications when the program starts."
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
            
            # 总是置顶窗口相关
            "always_on_top": {
                CHINESE: "总是置顶程序窗口",
                ENGLISH: "Always On Top"
            },
            "always_on_top_description": {
                CHINESE: "保持程序窗口始终显示在最前面",
                ENGLISH: "Keep the program window always on top of other windows"
            },
            "always_on_top_enabled": {
                CHINESE: "窗口置顶已启用",
                ENGLISH: "Window Pin Enabled"
            },
            "always_on_top_disabled": {
                CHINESE: "窗口置顶已禁用",
                ENGLISH: "Window Pin Disabled"
            },
            "always_on_top_enabled_tip": {
                CHINESE: "程序窗口将始终显示在最前面",
                ENGLISH: "The program window will always stay on top of other windows"
            },
            "always_on_top_disabled_tip": {
                CHINESE: "程序窗口将不再置顶",
                ENGLISH: "The program window will no longer stay on top"
            },
            
            "app_name": {
                CHINESE: "Roblox音频提取器",
                ENGLISH: "Roblox Audio Extractor"
            },
            "title": {
                ENGLISH: f"Roblox Audio Extractor v{VERSION}",
                CHINESE: f"Roblox Audio Extractor v{VERSION}"
            },
            "welcome_message": {
                ENGLISH: "Welcome to Roblox Audio Extractor!",
                CHINESE: "欢迎使用 Roblox Audio Extractor！"
            },
            "extract_audio": {
                ENGLISH: "Extract Audio",
                CHINESE: "提取音频"
            },
            "extract": {
                ENGLISH: "Extract",
                CHINESE: "提取"
            },
            "extract_images": {
                ENGLISH: "Extract Images",
                CHINESE: "提取图像"
            },
            "extract_textures": {
                ENGLISH: "Extract Textures",
                CHINESE: "提取纹理"
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
                ENGLISH: "Clear Roblox database and storage cache to free up disk space. Extracted files will be preserved.",
                CHINESE: "清除Roblox数据库和存储缓存，释放磁盘空间。提取的文件将被保留。"
            },
            'cache_details': {
                ENGLISH: "This operation will clear:\n1. rbx-storage.db database file\n2. Contents of rbx-storage folder (except the extracted folder)",
                CHINESE: "此操作将清除以下内容：\n1. rbx-storage.db 数据库文件\n2. rbx-storage 文件夹中的内容（除了extracted文件夹）"
            },
            'confirm_clear_cache': {
                ENGLISH: "Are you sure you want to clear Roblox database and storage cache?\n\nThis operation cannot be undone.",
                CHINESE: "确定要清除Roblox数据库和存储缓存吗？\n\n此操作无法撤销。"
            },
            'cache_cleared': {
                ENGLISH: "Successfully cleared {0} of {1} cache items.",
                CHINESE: "成功清除了 {0} 个缓存项，共 {1} 个。"
            },
            'no_cache_found': {
                ENGLISH: "No cache items found.",
                CHINESE: "未找到缓存项。"
            },
            'clear_cache_failed': {
                ENGLISH: "Failed to clear cache: {0}",
                CHINESE: "清除缓存失败：{0}"
            },
            'cache_location': {
                ENGLISH: "Cache Location",
                CHINESE: "缓存位置"
            },
            'path_not_found': {
                ENGLISH: "Roblox directory not found",
                CHINESE: "未找到Roblox目录"
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
                CHINESE: "确定要清除所有提取历史吗？\n\n此操作无法撤销。"
            },
            "history_cleared": {
                ENGLISH: "Extraction history has been cleared.",
                CHINESE: "提取历史已清除。"
            },
            "select_history_type_to_clear": {
                ENGLISH: "Select which history records to clear:",
                CHINESE: "选择要清除的历史记录类型:"
            },
            "all_history": {
                ENGLISH: "All History Records",
                CHINESE: "所有历史记录"
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
                CHINESE: "操作已取消。"
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
                ENGLISH: "Scan rbx-storage.db to extract more audio files",
                CHINESE: "扫描rbx-storage.db以提取更多音频文件"
            },
            "extract_audio_title": {
                ENGLISH: "Extract Audio Files",
                CHINESE: "提取音频文件"
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
            "threads": {
                ENGLISH: "Threads:",
                CHINESE: "线程数:"
            },
            "threads_info": {
                ENGLISH: "Higher values may increase speed but use more CPU",
                CHINESE: "更高的值可能提高速度但会使用更多CPU"
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
                CHINESE: "⚠ 未找到 FFmpeg。按时长分类可能无法正常工作。"
            },
            # 语言设置相关
            "restart_required": {
                ENGLISH: "Restart Required",
                CHINESE: "需要重启"
            },
            "restart_message": {
                ENGLISH: "The language change will take effect after restarting the application.\n\nWould you like to restart now?",
                CHINESE: "语言更改将在重启应用程序后生效。\n\n您想要现在重启吗？"
            },
            "language_close_message": {
                ENGLISH: "The language change will take effect after restarting the application.\n\nWould you like to close the application now?",
                CHINESE: "语言更改将在重启应用程序后生效。\n\n您想要现在关闭应用程序吗？"
            },
            "language_saved": {
                ENGLISH: "Language setting saved. Please restart the application.",
                CHINESE: "语言设置已保存。请重启应用程序。"
            },
            "language_unchanged": {
                ENGLISH: "Language setting unchanged.",
                CHINESE: "语言设置未改变。"
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
                ENGLISH: "Follow System",
                CHINESE: "跟随系统"
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
                ENGLISH: "An open-source tool for extracting audio files from Roblox cache. Files can be classified by audio duration or file size.",
                CHINESE: "一个用于从 Roblox 缓存中提取音频文件的开源工具。文件可以按音频时长或文件大小分类。"
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
                ENGLISH: "Audio classification by duration or size",
                CHINESE: "按时长或大小分类音频"
            },
            "feature_4": {
                ENGLISH: "Automatic MP3 conversion",
                CHINESE: "自动 MP3 转换"
            },
            "default_dir": {
                ENGLISH: "Default directory",
                CHINESE: "默认目录"
            },
            "input_dir": {
                ENGLISH: "Enter directory (press Enter for default)",
                CHINESE: "输入目录（按回车使用默认值）"
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
            "readme_title": {
                ENGLISH: "Roblox Audio Files - Classification Information",
                CHINESE: "Roblox 音频文件 - 分类信息"
            },
            "ffmpeg_not_installed": {
                ENGLISH: "FFmpeg is not installed. Please install FFmpeg to convert files and get duration information.",
                CHINESE: "未安装 FFmpeg。请安装 FFmpeg 以转换文件并获取时长信息。"
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
                ENGLISH: "Default: ‘extracted’ folder under extraction directory",
                CHINESE: "默认使用提取目录下的 ‘extracted’ 文件夹"
            },
            "save_logs": {
                ENGLISH: "Save logs to file",
                CHINESE: "保存日志到文件"
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
            "auto_check_update": {
                ENGLISH: "Auto-check for updates on startup",
                CHINESE: "启动时自动检测更新"
            },
            "check_update_now": {
                ENGLISH: "Check Now",
                CHINESE: "立即检查更新"
            },
            "checking_update": {
                ENGLISH: "Checking for updates...",
                CHINESE: "正在检查更新..."
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
                CHINESE: "确定要清空所有日志吗？此操作无法撤销。"
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
                CHINESE: "清空日志时出错：{}"
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
                ENGLISH: "Detect FFmpeg",
                CHINESE: "检测 FFmpeg"
            },
            "browse_ffmpeg": {
                ENGLISH: "Browse FFmpeg",
                CHINESE: "浏览 FFmpeg"
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
                CHINESE: "FFmpeg 已安装，按时长分类功能可以正常工作。"
            },
            "ffmpeg_not_available": {
                ENGLISH: "FFmpeg Not Available",
                CHINESE: "FFmpeg 不可用"
            },
            "ffmpeg_not_available_message": {
                ENGLISH: "FFmpeg not detected. Duration classification may not work properly. Please click 'Browse FFmpeg' to set manually.",
                CHINESE: "未检测到 FFmpeg，按时长分类功能可能无法正常工作。请点击'浏览 FFmpeg'手动设置。"
            },
            "ffmpeg_available_info": {
                ENGLISH: "FFmpeg is available. Duration classification feature can work properly.",
                CHINESE: "FFmpeg 可用，按时长分类功能可以正常工作。"
            },
            "ffmpeg_available_info_path": {
                ENGLISH: "FFmpeg is available at: {}. Duration classification feature can work properly.",
                CHINESE: "FFmpeg 可用，路径：{}。按时长分类功能可以正常工作。"
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
        }