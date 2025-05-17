# Roblox Audio Extractor
<div align="center">
  
<img src="https://github.com/JustKanade/Roblox-Audio-Extractor/blob/main/.readme/images/Roblox-Audio-Extractor%20Logo.png" alt="" width="300px">

**从 Roblox 缓存中提取和转换音频文件的高效工具**

![GitHub Release](https://img.shields.io/github/v/release/JustKanade/Roblox-Audio-Extractor?label=Release&color=green&logo=github)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-orange.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/JustKanade/Roblox-Audio-Extractor?style=social)](https://github.com/JustKanade/Roblox-Audio-Extractor/stargazers)


[English](README.md) | 简体中文

</div>

##  功能特点

-  **自动扫描** - 自动扫描Roblox缓存目录，快速定位音频文件
-  **音频提取** - 从缓存文件中提取隐藏的OGG音频文件
-  **格式转换** - 可选将提取的OGG文件转换为广泛兼容的MP3格式
-  **智能分类** - 按文件大小自动分类音频文件(极小、小、中、大、超大)
-  **多线程加速** - 利用多线程技术，提高处理速度
-  **去重功能** - 自动记录下载历史，避免重复提取相同文件
-  **多语言支持** - 内置中文和英文界面，轻松切换
- **自动命名** - 提取的文件使用时间戳和随机字符串命名，防止覆盖
<p align="center">
  <img src="https://github.com/JustKanade/Roblox-Audio-Extractor/blob/main/.readme/images/Folder.png" alt="" width="200">
</p>
##  系统要求

- Python 3.7+
- 支持Windows、macOS和Linux
- 如需MP3转换功能，需安装[FFmpeg](https://ffmpeg.org/download.html)

##  安装指南

### 1. 克隆仓库
```bash
git clone https://github.com/JustKanade/Roblox-Audio-Extractor.git
cd Roblox-Audio-Extractor
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 安装FFmpeg (可选，用于MP3转换)
- **Windows**: 下载[官方安装包](https://ffmpeg.org/download.html)并添加到系统PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg` 或适用于你的发行版的命令

##  使用方法

运行主程序:
```bash
python roblox_audio_extractor.py
```

### 主菜单选项:

1. **提取音频文件** - 扫描Roblox缓存并提取音频
2. **查看下载历史** - 显示已处理文件的统计信息  
3. **清除下载历史** - 重置已处理文件的记录
4. **语言设置** - 切换中文/英文界面
5. **关于** - 显示程序信息
6. **退出** - 退出程序

##  界面预览

  <img src="https://github.com/JustKanade/Roblox-Audio-Extractor/blob/main/.readme/images/Extraction-Process.png" alt="音频提取过程" width="80%">
  <p><i>音频提取过程</i></p>
</div>

##  提取过程详解

1. **扫描阶段**: 程序扫描Roblox缓存目录(默认位于`C:\Users\用户名\AppData\Local\Temp\Roblox\http`)
2. **提取阶段**: 从缓存文件中提取OGG音频
3. **分类阶段**: 根据文件大小将音频分为5类(极小、小、中、大、超大)
4. **转换阶段**(可选): 将OGG文件转换为MP3格式
5. **整理阶段**: 生成分类说明文件，帮助用户理解分类方式

##  输出目录结构

```
提取输出目录/
├── tiny_0-100KB_short/         - 极小文件(0-100KB，通常为短音效)
├── small_100-500KB_medium/     - 小文件(100-500KB，中等长度音频)
├── medium_500KB-1MB_normal/    - 中等文件(500KB-1MB，正常长度音频)
├── large_1-5MB_long/           - 大文件(1-5MB，较长音频)
├── huge_5MB+_very_long/        - 超大文件(5MB以上，非常长的音频)
└── README.txt                  - 分类说明文件
```

##  高级设置

- **线程数**: 程序默认使用系统CPU核心数的两倍作为线程数，最大不超过32。可手动调整。
- **自定义输入目录**: 如果Roblox缓存位于非默认位置，可手动指定目录路径。
- **历史记录**: 历史记录文件保存在`~/.roblox_audio_extractor/download_history.json`。

## 常见问题

**Q: 程序无法找到Roblox缓存目录怎么办?**  
A: 可以手动指定目录，或者检查你的Roblox是否是自定义安装位置。

**Q: 提取出的音频文件无法播放?**  
A: 确保文件是有效的音频文件。有些缓存可能不是完整的音频文件或已损坏。

**Q: MP3转换功能不工作?**  
A: 请确保已正确安装FFmpeg并添加到系统路径。

**Q: 如何找到最好的音频文件?**  
A: 通常更大的文件(large和huge目录中)包含更完整、质量更高的音频。

##  贡献指南

欢迎提交Pull Request或创建Issues!

1. Fork该仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个Pull Request

## 📜 许可证

本项目采用GNU Affero General Public License v3.0 (AGPLv3) - 详情请见[LICENSE](LICENSE)文件

AGPLv3许可证的主要要求：
- 如果您分发本程序的拷贝，您必须同时提供完整的源代码
- 如果您修改了本程序，您必须以同样的许可证分发您的修改
- 如果您通过网络提供本程序的功能，您也必须提供完整的源代码
- 您必须保留原始版权声明

这种许可证确保本软件的所有用户保持自由，即使是通过网络服务使用本软件的用户也是如此。

## 💖 致谢

- 感谢所有使用和支持本工具的用户
- 感谢Python和相关开源库的开发者
- Roblox图标仅用于识别，归Roblox Corporation所有

## 📬 联系方式

- GitHub Issues: [https://github.com/JustKanade/Roblox-Audio-Extractor/issues](https://github.com/JustKanade/Roblox-Audio-Extractor/issues)
- 电子邮件: muxian0219@qq.com

---

<div align="center">
  <sub>| 记得给项目点个⭐!</sub>
</div>
