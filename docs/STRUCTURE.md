# Project Structure

├── [LICENSE](LICENSE)
├── [README.md](README.md)
├── [generate_structure_md.py](generate_structure_md.py)
├── [main.py](main.py)
├── [requirements.txt](requirements.txt)
├── res/
│   └── icons/
│       ├── [Roblox-Audio-Extractor.ico](res/icons/Roblox-Audio-Extractor.ico)
│       └── [Roblox-Audio-Extractor.png](res/icons/Roblox-Audio-Extractor.png)
└── src/
    ├── components/
    │   ├── Greetings/
    │   │   ├── [__init__.py](src/components/Greetings/__init__.py)
    │   │   └── [greetings.py](src/components/Greetings/greetings.py)
    │   ├── avatar/
    │   │   ├── [__init__.py](src/components/avatar/__init__.py)
    │   │   └── [avatar_widget.py](src/components/avatar/avatar_widget.py)
    │   ├── cards/
    │   │   └── Settings/
    │   │       ├── [__init__.py](src/components/cards/Settings/__init__.py)
    │   │       ├── [always_on_top_card.py](src/components/cards/Settings/always_on_top_card.py)
    │   │       ├── [avatar_setting_card.py](src/components/cards/Settings/avatar_setting_card.py)
    │   │       ├── [custom_theme_color_card.py](src/components/cards/Settings/custom_theme_color_card.py)
    │   │       ├── [debug_mode_card.py](src/components/cards/Settings/debug_mode_card.py)
    │   │       ├── [ffmpeg_status_card.py](src/components/cards/Settings/ffmpeg_status_card.py)
    │   │       ├── [global_input_path_card.py](src/components/cards/Settings/global_input_path_card.py)
    │   │       ├── [greeting_setting_card.py](src/components/cards/Settings/greeting_setting_card.py)
    │   │       ├── [log_control_card.py](src/components/cards/Settings/log_control_card.py)
    │   │       └── [version_check_card.py](src/components/cards/Settings/version_check_card.py)
    │   └── ui/
    │       ├── [__init__.py](src/components/ui/__init__.py)
    │       └── [responsive_components.py](src/components/ui/responsive_components.py)
    ├── config/
    │   ├── [__init__.py](src/config/__init__.py)
    │   └── [config_manager.py](src/config/config_manager.py)
    ├── extractors/
    │   ├── [__init__.py](src/extractors/__init__.py)
    │   └── [audio_extractor.py](src/extractors/audio_extractor.py)
    ├── locale/
    │   ├── [__init__.py](src/locale/__init__.py)
    │   ├── [language_manager.py](src/locale/language_manager.py)
    │   └── [translations.py](src/locale/translations.py)
    ├── logging/
    │   ├── [__init__.py](src/logging/__init__.py)
    │   └── [central_log_handler.py](src/logging/central_log_handler.py)
    ├── management/
    │   ├── cache_management/
    │   │   ├── [__init__.py](src/management/cache_management/__init__.py)
    │   │   └── [cache_cleaner.py](src/management/cache_management/cache_cleaner.py)
    │   ├── language_management/
    │   │   ├── [__init__.py](src/management/language_management/__init__.py)
    │   │   └── [language_manager.py](src/management/language_management/language_manager.py)
    │   ├── theme_management/
    │   │   ├── [__init__.py](src/management/theme_management/__init__.py)
    │   │   └── [theme_manager.py](src/management/theme_management/theme_manager.py)
    │   └── window_management/
    │       ├── [__init__.py](src/management/window_management/__init__.py)
    │       ├── [responsive_handler.py](src/management/window_management/responsive_handler.py)
    │       └── [window_utils.py](src/management/window_management/window_utils.py)
    ├── utils/
    │   ├── [__init__.py](src/utils/__init__.py)
    │   ├── [file_utils.py](src/utils/file_utils.py)
    │   ├── [import_utils.py](src/utils/import_utils.py)
    │   └── [log_utils.py](src/utils/log_utils.py)
    └── workers/
        ├── [__init__.py](src/workers/__init__.py)
        └── [extraction_worker.py](src/workers/extraction_worker.py)
