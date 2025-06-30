# Roblox Audio Extractor
<div align="center">
  
<img src="https://github.com/JustKanade/Roblox-Audio-Extractor/blob/main/.readme/images/Roblox-Audio-Extractor%20Logo.png" alt="" width="300px">

**一个高效的现代化 GUI 工具，用于从 Roblox 缓存中提取和转换音频文件**

![GitHub Release](https://img.shields.io/github/v/release/JustKanade/Roblox-Audio-Extractor?label=Release&color=green&logo=github)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-orange.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/JustKanade/Roblox-Audio-Extractor?style=social)](https://github.com/JustKanade/Roblox-Audio-Extractor/stargazers)

[English](README.md) | 简体中文

</div>

##  功能特色

- **现代化 GUI 界面** - 基于 PyQt5 和 PyQt-Fluent-Widgets 构建，提供美观、响应式的用户体验
- **自动扫描** - 智能扫描 Roblox 缓存目录，快速定位音频文件
- **音频提取** - 使用优化算法从缓存中提取隐藏的 OGG 音频文件
- **智能分类** - 两种分类方式：
  - **按时长分类**：根据音频长度分类（需要 FFmpeg）
  - **按大小分类**：根据文件大小分类（无需 FFmpeg）
- **格式转换** - 可选将 OGG 文件转换为 MP3 格式（需要 FFmpeg）
- **多线程处理** - 支持可配置的多线程（1-128 线程），实现极速提取
- **重复检测** - 基于哈希的智能检测，防止重复提取相同文件
- **提取历史** - 维护已提取文件的历史记录，跳过已处理的内容
- **缓存管理** - 内置缓存清理器，可在提取特定游戏音频前清除音频缓存
- **多语言支持** - 完整支持中英文界面
- **主题支持** - 深色模式、浅色模式和跟随系统主题
- **实时进度** - 实时进度跟踪，显示速度指标和预计剩余时间

<p align="center">
  <img src="https://github.com/JustKanade/Roblox-Audio-Extractor/blob/main/.readme/images/GUI-Screenshot.png" alt="GUI 界面" width="600">
</p>

##  系统要求

- **Python**：3.7 或更高版本
- **操作系统**：Windows、macOS、Linux
- **FFmpeg**：MP3 转换和基于时长分类功能需要
- **依赖库**：PyQt5、PyQt-Fluent-Widgets 等 Python 包（见 requirements.txt）

##  安装指南

### 选项 1：从源代码运行

1. **克隆仓库**
   ```bash
   git clone https://github.com/JustKanade/Roblox-Audio-Extractor.git
   cd Roblox-Audio-Extractor
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **安装 FFmpeg**（可选但推荐）
   - **Windows**：从[官方网站](https://ffmpeg.org/download.html)下载并添加到 PATH
   - **macOS**：`brew install ffmpeg`
   - **Linux**：`sudo apt install ffmpeg`（或适用于您的发行版的命令）

4. **运行应用程序**
   ```bash
   python Roblox_Audio_Extractor.py
   ```

### 选项 2：使用预编译的可执行文件（Windows）

从 [Releases 页面](https://github.com/JustKanade/Roblox-Audio-Extractor/releases)下载最新的 `.exe` 版本。

##  使用指南

### 主界面

应用程序采用现代化的标签式界面，包含以下部分：

1. **首页** - 快速概览和主要功能快捷方式
2. **提取音频** - 主要提取界面，包含所有选项
3. **清除缓存** - 缓存管理工具
4. **提取历史** - 查看和管理提取历史
5. **设置** - 语言、主题和性能设置
6. **关于** - 应用程序信息和链接

### 音频提取流程

1. **选择目录**：选择 Roblox 缓存目录（自动检测默认路径）
2. **选择分类方式**：
   - **按时长分类**：根据音频长度组织文件（需要 FFmpeg）
   - **按大小分类**：根据文件大小组织文件
3. **配置选项**：
   - 线程数（1-128，默认：2倍 CPU 核心数）
   - MP3 转换（开/关）
4. **开始提取**：点击"开始提取"并监控实时进度
5. **查看结果**：完成后自动打开输出目录

### 分类类别

#### 基于时长的分类：
- `ultra_short_0-5s` - 音效、提示音（0-5秒）
- `short_5-15s` - 短音效、通知音（5-15秒）
- `medium_15-60s` - 循环音乐、短背景音（15-60秒）
- `long_60-300s` - 完整音乐、长背景音（1-5分钟）
- `ultra_long_300s+` - 长音乐、语音（5分钟以上）

#### 基于大小的分类：
- `ultra_small_0-50KB` - 极小音频片段（0-50KB）
- `small_50-200KB` - 小型音频片段（50KB-200KB）
- `medium_200KB-1MB` - 中等大小音频（200KB-1MB）
- `large_1MB-5MB` - 大型音频文件（1MB-5MB）
- `ultra_large_5MB+` - 极大音频文件（5MB以上）

### 缓存管理

使用缓存标签页在提取特定游戏音频前清理音频缓存：
1. 清除缓存
2. 启动并完全加载目标游戏
3. 返回提取器并提取音频

这确保您只提取想要的特定游戏的音频。

##  高级功能

### 配置

设置自动保存在 `~/.roblox_audio_extractor/config.json`：
- 默认线程数
- 语言偏好（en/zh/auto）
- 主题偏好（dark/light/auto）
- MP3 转换默认设置
- 上次使用的目录

### 提取历史

- 历史记录存储在 `~/.roblox_audio_extractor/extracted_history.json`
- 防止重复提取相同文件
- 可从历史标签页清除

### 性能优化

- **线程数**：更高的线程数提高速度但使用更多 CPU
- **推荐**：2倍 CPU 核心数（自动计算）
- **最大值**：128 线程（谨慎使用）

##  故障排除

**问：提取器找不到任何音频文件？**  
答：确保您指向正确的缓存目录。默认通常是：
- Windows：`C:\Users\[用户名]\AppData\Local\Temp\Roblox\http`
- macOS：`/Users/[用户名]/Library/Caches/Roblox/http`
- Linux：`~/.local/share/Roblox/http`

**问：时长分类不工作？**  
答：此功能需要 FFmpeg。确保它已安装并在系统 PATH 中可用。

**问：提取的音频文件无法播放？**  
答：某些缓存文件可能已损坏或不完整。尝试 MP3 转换选项，有时可以修复播放问题。

**问：如何只提取特定游戏的音频？**  
答：先使用缓存清理功能，然后在提取前只加载您想要的游戏。

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。对于重大更改：

1. Fork 仓库
2. 创建您的功能分支（`git checkout -b feature/AmazingFeature`）
3. 提交您的更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

## 📜 许可证

本项目根据 GNU Affero 通用公共许可证 v3.0 (AGPLv3) 授权 - 详见 [LICENSE](LICENSE) 文件。

AGPLv3 许可证的主要要求：
- 如果您分发本程序的副本，必须提供完整的源代码
- 如果您修改本程序，必须在相同许可证下分发您的修改
- 如果您通过网络提供本程序的功能，必须提供完整的源代码
- 必须保留原始版权声明

## 🙏 致谢

- 感谢所有贡献者和使用本工具的用户
- PyQt5 和 PyQt-Fluent-Widgets 提供的出色 GUI 框架
- FFmpeg 提供的音频处理能力
- Python 社区提供的优秀库和支持

## 📬 联系方式

- **GitHub Issues**：[报告错误或请求功能](https://github.com/JustKanade/Roblox-Audio-Extractor/issues)
- **邮箱**：muxian0219@qq.com

---

<div align="center">
  <sub>| 记得给这个项目 ⭐！</sub>
</div>
