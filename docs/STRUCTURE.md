# Project Structure

```
├── LICENSE
├── README.md
├── generate_structure_md.py
├── main.py
├── requirements.txt
├── res/
│   └── icons/
│       ├── Roblox-Audio-Extractor.ico
│       └── Roblox-Audio-Extractor.png
└── src/
    ├── components/
    │   ├── Greetings/
    │   │   ├── __init__.py
    │   │   └── greetings.py
    │   ├── avatar/
    │   │   ├── __init__.py
    │   │   └── avatar_widget.py
    │   ├── cards/
    │   │   └── Settings/
    │   │       ├── __init__.py
    │   │       ├── always_on_top_card.py
    │   │       ├── avatar_setting_card.py
    │   │       ├── custom_theme_color_card.py
    │   │       ├── debug_mode_card.py
    │   │       ├── ffmpeg_status_card.py
    │   │       ├── global_input_path_card.py
    │   │       ├── greeting_setting_card.py
    │   │       ├── log_control_card.py
    │   │       └── version_check_card.py
    │   └── ui/
    │       ├── __init__.py
    │       └── responsive_components.py
    ├── config/
    │   ├── __init__.py
    │   └── config_manager.py
    ├── extractors/
    │   ├── __init__.py
    │   └── audio_extractor.py
    ├── locale/
    │   ├── __init__.py
    │   ├── language_manager.py
    │   └── translations.py
    ├── logging/
    │   ├── __init__.py
    │   └── central_log_handler.py
    ├── management/
    │   ├── cache_management/
    │   │   ├── __init__.py
    │   │   └── cache_cleaner.py
    │   ├── language_management/
    │   │   ├── __init__.py
    │   │   └── language_manager.py
    │   ├── theme_management/
    │   │   ├── __init__.py
    │   │   └── theme_manager.py
    │   └── window_management/
    │       ├── __init__.py
    │       ├── responsive_handler.py
    │       └── window_utils.py
    ├── utils/
    │   ├── __init__.py
    │   ├── file_utils.py
    │   ├── import_utils.py
    │   └── log_utils.py
    └── workers/
        ├── __init__.py
        └── extraction_worker.py
```
