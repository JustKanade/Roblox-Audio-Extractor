# Roblox Audio Extractor
<div align="center">
  
<img src="https://github.com/JustKanade/Roblox-Audio-Extractor/blob/main/.readme/images/Roblox-Audio-Extractor%20Logo.png" alt="" width="300px">

**An efficient tool for extracting and converting audio files from Roblox cache with one click**

![GitHub Release](https://img.shields.io/github/v/release/JustKanade/Roblox-Audio-Extractor?label=Release&color=green&logo=github)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-orange.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/JustKanade/Roblox-Audio-Extractor?style=social)](https://github.com/JustKanade/Roblox-Audio-Extractor/stargazers)


English | [简体中文](README_ZH.md)

</div>

## Features

- **Automatic Scanning** - Intelligently scans Roblox cache directories to quickly locate audio files
- **Audio Extraction** - Extracts hidden OGG audio files from cache files
- **Format Conversion** - Optional conversion of extracted OGG files to widely compatible MP3 format
- **Smart Classification** - Automatically categorizes audio files by size (tiny, small, medium, large, huge)
- **Multi-threading** - Utilizes multi-threading technology to significantly increase processing speed
- **Deduplication** - Intelligently records download history to avoid extracting duplicate files
- **Multi-language Support** - Built-in Chinese and English interfaces, easy to switch
- **Smart Naming** - Extracted files are named with timestamps and random strings to prevent overwriting
<p align="center">
  <img src="https://github.com/JustKanade/Roblox-Audio-Extractor/blob/main/.readme/images/Folder.png" alt="" width="200">
</p>
## System Requirements

- Python 3.7+
- Supports Windows, macOS, 和 Linux
- For MP3 conversion functionality, [FFmpeg](https://ffmpeg.org/download.html) must be installed

## Installation Guide

### 1. Clone the Repository
```bash
git clone https://github.com/JustKanade/Roblox-Audio-Extractor.git
cd Roblox-Audio-Extractor
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg (Optional, for MP3 conversion)
- **Windows**: Download the [official installer](https://ffmpeg.org/download.html) and add to system PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg` or the command suitable for your distribution

## Usage

Run the main program:
```bash
python roblox_audio_extractor.py
```

### Main Menu Options:

1. **Extract Audio Files** - Scan Roblox cache and extract audio
2. **View Download History** - Display statistics of processed files  
3. **Clear Download History** - Reset records of processed files
4. **Language Settings** - Switch between Chinese/English interface
5. **About** - Display program information
6. **Exit** - Exit the program

## Interface Preview

  
  <img src="https://github.com/JustKanade/Roblox-Audio-Extractor/blob/main/.readme/images/Extraction-Process.png" alt="Audio Extraction Process" width="80%">
  <p><i>Audio Extraction Process</i></p>
</div>

## Extraction Process Details

1. **Scanning Phase**: The program scans the Roblox cache directory (default at `C:\Users\username\AppData\Local\Temp\Roblox\http`)
2. **Extraction Phase**: Extracts OGG audio from cache files
3. **Classification Phase**: Categorizes audio into 5 classes (tiny, small, medium, large, huge) based on file size
4. **Conversion Phase** (optional): Converts OGG files to MP3 format
5. **Organization Phase**: Generates a classification description file to help users understand the categorization

## Output Directory Structure

```
Output Directory/
├── tiny_0-100KB_short/         - Tiny files (0-100KB, usually short sound effects)
├── small_100-500KB_medium/     - Small files (100-500KB, medium length audio)
├── medium_500KB-1MB_normal/    - Medium files (500KB-1MB, normal length audio)
├── large_1-5MB_long/           - Large files (1-5MB, longer audio)
├── huge_5MB+_very_long/        - Huge files (5MB+, very long audio)
└── README.txt                  - Classification description file
```

## Advanced Settings

- **Thread Count**: The program defaults to using twice the number of CPU cores as threads, up to a maximum of 32. This can be manually adjusted.
- **Custom Input Directory**: If the Roblox cache is in a non-default location, you can manually specify the directory path.
- **History Records**: History records are saved in `~/.roblox_audio_extractor/download_history.json`.

## FAQ

**Q: What if the program can't find the Roblox cache directory?**  
A: You can manually specify the directory, or check if your Roblox has a custom installation location.

**Q: What if the extracted audio files won't play?**  
A: Make sure the file is a valid audio file. Some cache may not be complete audio files or may be corrupted.

**Q: The MP3 conversion feature doesn't work?**  
A: Please make sure FFmpeg is correctly installed and added to the system path.

**Q: How do I find the best audio files?**  
A: Usually larger files (in the large and huge directories) contain more complete, higher quality audio.

## Contribution Guidelines

Pull Requests and Issues are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the GNU Affero General Public License v3.0 (AGPLv3) - see the [LICENSE](LICENSE) file for details

Key requirements of the AGPLv3 license:
- If you distribute copies of this program, you must also provide the complete source code
- If you modify this program, you must distribute your modifications under the same license
- If you offer the functionality of this program over a network, you must also provide the complete source code
- You must maintain the original copyright notice

This license ensures that all users of the software remain free, even those using it through network services.

## 💖 Acknowledgements

- Thanks to all users who use and support this tool
- Thanks to the developers of Python and related open-source libraries
- Roblox icon is used for identification only and is owned by Roblox Corporation

## 📬 Contact Information

- GitHub Issues: [https://github.com/JustKanade/Roblox-Audio-Extractor/issues](https://github.com/JustKanade/Roblox-Audio-Extractor/issues)
- Email: muxian0219@qq.com

---

<div align="center">
  <sub>| Remember to star ⭐ this project!</sub>
</div>
