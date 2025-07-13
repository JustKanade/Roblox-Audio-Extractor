# Roblox Audio Extractor
<div align="center">
  
<img src="https://github.com/JustKanade/Roblox-Audio-Extractor/blob/main/.readme/images/Folder.png" alt="" width="300px">

**An efficient tool with modern GUI for extracting and converting audio files from Roblox cache**

![GitHub Release](https://img.shields.io/github/v/release/JustKanade/Roblox-Audio-Extractor?label=Release&color=green&logo=github)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-orange.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/JustKanade/Roblox-Audio-Extractor?style=social)](https://github.com/JustKanade/Roblox-Audio-Extractor/stargazers)
[![Auto Build and Release](https://github.com/JustKanade/Roblox-Audio-Extractor/actions/workflows/build.yml/badge.svg)](https://github.com/JustKanade/Roblox-Audio-Extractor/actions/workflows/build.yml)

English | [简体中文](.readme/README_ZH.md)

</div>

> [!IMPORTANT]
>  The development builds can be downloaded from the [releases](https://github.com/JustKanade/Roblox-Audio-Extractor/releases) page.

> [!TIP]
> If you want to extract a single game, click on cleaning the cache, add the game and wait for the full load to extract

##  Features

- **Modern GUI Interface** - Built with PyQt5 and PyQt-Fluent-Widgets for a beautiful, responsive user experience
- **Automatic Scanning** - Intelligently scans Roblox cache directories to quickly locate audio files
- **Audio Extraction** - Extracts hidden OGG audio files from cache with optimized algorithms
- **Smart Classification** - Two classification methods:
  - **By Duration**: Categorizes audio by length (requires FFmpeg)
  - **By File Size**: Categorizes audio by file size (no FFmpeg required)
- **Format Conversion** - Optional conversion of OGG files to MP3 format with FFmpeg
- **Multi-threading** - Utilizes configurable multi-threading (1-128 threads) for blazing fast extraction
- **Duplicate Detection** - Smart hash-based detection prevents extracting the same files multiple times
- **Extraction History** - Maintains history of extracted files to skip already processed content
- **Cache Management** - Built-in cache cleaner to remove audio cache files before extracting specific game audio
- **Multi-language Support** - Full support for English and Chinese interfaces
- **Theme Support** - Dark mode, light mode, and system theme following
- **Real-time Progress** - Live progress tracking with speed metrics and ETA

<p align="center">
  <img src="https://github.com/JustKanade/Roblox-Audio-Extractor/blob/main/.readme/images/GUI-Screenshot.png" alt="GUI Interface" width="600">
</p>

##  System Requirements

- **Python**: 3.7 or higher
- **Operating System**: Windows, macOS, Linux
- **FFmpeg**: Required for MP3 conversion and duration-based classification
- **Dependencies**: PyQt5, PyQt-Fluent-Widgets, and other Python packages (see requirements.txt)

## 🚀 Installation

### Option 1: Run from Source

1. **Clone the Repository**
   ```bash
   git clone https://github.com/JustKanade/Roblox-Audio-Extractor.git
   cd Roblox-Audio-Extractor
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (Optional but recommended)
   - **Windows**: Download from [official website](https://ffmpeg.org/download.html) and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg` (or equivalent for your distribution)

4. **Run the Application**
   ```bash
   python Roblox_Audio_Extractor.py
   ```

### Option 2: Use Pre-built Executable (Windows)

Download the latest `.exe` release from the [Releases page](https://github.com/JustKanade/Roblox-Audio-Extractor/releases).

##  Usage Guide

### Main Interface

The application features a modern tabbed interface with the following sections:

1. **Home** - Quick overview and shortcuts to main features
2. **Extract** - Main extraction interface with all options
3. **Cache** - Cache management tools
4. **History** - View and manage extraction history
5. **Settings** - Language, theme, and performance settings
6. **About** - Application information and links

### Audio Extraction Process

1. **Select Directory**: Choose the Roblox cache directory (default path is auto-detected)
2. **Choose Classification**: 
   - **By Duration**: Organizes files by audio length (requires FFmpeg)
   - **By Size**: Organizes files by file size
3. **Configure Options**:
   - Thread count (1-128, default: 2x CPU cores)
   - MP3 conversion (on/off)
4. **Start Extraction**: Click "Start Extraction" and monitor real-time progress
5. **View Results**: Output directory opens automatically upon completion

### Classification Categories

#### Duration-based Classification:
- `ultra_short_0-5s` - Sound effects, notification sounds (0-5 seconds)
- `short_5-15s` - Short effects, alerts (5-15 seconds)
- `medium_15-60s` - Loop music, short BGM (15-60 seconds)
- `long_60-300s` - Full music tracks, long BGM (1-5 minutes)
- `ultra_long_300s+` - Extended music, voice recordings (5+ minutes)

#### Size-based Classification:
- `ultra_small_0-50KB` - Very small audio clips (0-50KB)
- `small_50-200KB` - Small audio clips (50KB-200KB)
- `medium_200KB-1MB` - Medium size audio (200KB-1MB)
- `large_1MB-5MB` - Large audio files (1MB-5MB)
- `ultra_large_5MB+` - Very large audio files (5MB+)

### Cache Management

Use the Cache tab to clear audio cache files before extracting from a specific game:
1. Clear the cache
2. Launch and fully load the target game
3. Return to the extractor and extract audio

This ensures you only extract audio from the specific game you want.

##  Advanced Features

### Configuration

Settings are automatically saved in `~/.roblox_audio_extractor/config.json`:
- Default thread count
- Language preference (en/zh/auto)
- Theme preference (dark/light/auto)
- MP3 conversion default
- Last used directory

### Extraction History

- History stored in `~/.roblox_audio_extractor/extracted_history.json`
- Prevents re-extracting identical files
- Can be cleared from the History tab

### Performance Optimization

- **Thread Count**: Higher thread counts improve speed but use more CPU
- **Recommended**: 2x CPU cores (automatically calculated)
- **Maximum**: 128 threads (use with caution)

##  Troubleshooting

**Q: The extractor can't find any audio files?**  
A: Make sure you're pointing to the correct cache directory. The default is usually:
- Windows: `C:\Users\[username]\AppData\Local\Temp\Roblox\http`
- macOS: `/Users/[username]/Library/Caches/Roblox/http`
- Linux: `~/.local/share/Roblox/http`

**Q: Duration classification isn't working?**  
A: This feature requires FFmpeg. Make sure it's installed and available in your system PATH.

**Q: Extracted audio files won't play?**  
A: Some cache files may be corrupted or incomplete. Try the MP3 conversion option, which can sometimes fix playback issues.

**Q: How do I extract audio from a specific game only?**  
A: Use the Cache Cleaner feature first, then load only the game you want before extracting.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the GNU Affero General Public License v3.0 (AGPLv3) - see the [LICENSE](LICENSE) file for details.

Key requirements of the AGPLv3 license:
- If you distribute copies of this program, you must provide the complete source code
- If you modify this program, you must distribute your modifications under the same license
- If you offer the functionality of this program over a network, you must provide the complete source code
- You must maintain the original copyright notice

## 🙏 Acknowledgements

- Thanks to all contributors and users of this tool
- PyQt5 and PyQt-Fluent-Widgets for the amazing GUI framework
- FFmpeg for audio processing capabilities
- The Python community for excellent libraries and support

## 📬 Contact

- **GitHub Issues**: [Report bugs or request features](https://github.com/JustKanade/Roblox-Audio-Extractor/issues)
- **Email**: muxian0219@qq.com

---

<div align="center">
  <sub>Made with ❤️ by JustKanade | Remember to ⭐ this project!</sub>
</div>
