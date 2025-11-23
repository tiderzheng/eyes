# 视频字幕提取工具

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.0+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 项目简介

这是一个基于 PyQt6 的桌面应用程序，使用 AI 视觉模型（OpenAI 兼容 API）从视频中提取字幕。支持可视化区域选择、实时进度显示和多种输出格式。

## ✨ 功能特点

- 🎬 **视频加载和预览** - 支持常见视频格式（MP4、MKV、AVI、MOV 等）
- 🎯 **可视化字幕区域选择** - 用鼠标框选字幕区域，提高识别准确率
- 🤖 **AI 驱动的 OCR 识别** - 支持 Qwen-VL、DeepSeek-VL2 等视觉模型
- 📊 **实时进度显示** - 显示处理进度、已用时间、识别条目数
- ⚡ **响应式终止功能** - 随时可终止提取，5 秒内响应
- 📄 **多格式输出** - 同时生成 SRT（带时间轴）和 TXT（纯文本）文件
- ⚙️ **灵活配置** - 支持多 API 端点、Prompt 预设管理
- 📝 **详细日志** - 实时显示处理日志，便于调试

## 🚀 快速开始

### 前置要求

- Python 3.8 或更高版本
- OpenAI 兼容的 API 服务（如 LM Studio、SiliconFlow）

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/tiderzheng/eyes.git
cd eyes
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 复制配置示例文件
cp .env.example .env
```

4. **编辑 `.env` 文件**
```env
# API 配置
OCR_API_ENDPOINT=http://localhost:1234  # 你的 API 地址
OCR_API_KEY=your_api_key_here           # 你的 API 密钥
OCR_API_MODEL=qwen/qwen3-vl-8b          # 模型名称

# Prompt 配置
OCR_PROMPT=只返回图片中的可读字幕文本。如果图片中没有字幕或文字，只返回空字符串，不要任何解释或描述。
OCR_SYSTEM_PROMPT=
```

5. **运行程序**
```bash
python main.py
```

## 📖 使用方法

### 基本流程

1. **打开视频**
   - 点击"打开视频"按钮
   - 选择要处理的视频文件（MP4、MKV、AVI、MOV 等）

2. **选择字幕区域**
   - 在视频画面上按住鼠标左键拖动
   - 框选包含字幕的区域（尽量精确）
   - 右下角会显示区域坐标

3. **配置 API（可选）**
   - 点击"管理API"配置多个 API 端点
   - 或从下拉框选择已配置的 API

4. **开始提取**
   - 点击"开始提取"按钮
   - 查看下方日志区域的实时进度
   - 进度条会显示当前处理百分比

5. **查看结果**
   - 提取完成后会弹出完成提示
   - 在视频同目录下生成 `.srt` 和 `.txt` 文件
   - 日志区域会显示详细的统计信息

### 高级功能

#### 配置 Prompt

在 `.env` 文件中自定义 Prompt 以提高识别准确率：

```env
# 针对中文视频
OCR_PROMPT=只返回图片中的可读中文字幕文本。如果没有字幕，返回空字符串。

# 针对英文视频
OCR_PROMPT=Only return readable English subtitles from the image. Return empty string if no subtitles.

# 通用优化版本
OCR_PROMPT=只返回图片中的可读字幕文本。如果图片中没有字幕或文字，只返回空字符串，不要任何解释或描述。
```

#### 管理 Prompt 预设

1. 从下拉框选择"管理Prompt预设..."
2. 添加/编辑/删除 Prompt 配置
3. 为不同类型的视频创建不同的 Prompt

#### 配置多个 API

1. 点击"管理API"按钮
2. 添加多个 API 配置（如 LM Studio、SiliconFlow）
3. 支持导入/导出配置
4. 可设置分组管理不同用途的 API

## ⚙️ 参数调优

### 提取参数说明

在 `start_extract()` 方法中可以调整以下参数：

```python
self.extractor = Extractor(
    self.video_path,      # 视频路径
    r,                    # 字幕区域（自动获取）
    engine,               # OCR 引擎
    800,                  # 采样间隔（毫秒）
    1200,                 # 最短字幕时长（毫秒）
    out                   # 输出路径（自动）
)
```

### 参数调优建议

- **采样间隔**（`sample_ms`）:
  - 减小（如 500ms）→ 捕获更多字幕变化，但处理时间增加
  - 增大（如 1200ms）→ 处理更快，但可能错过快速变化的字幕

- **最短字幕时长**（`min_duration_ms`）:
  - 减小（如 800ms）→ 保留更多短字幕
  - 增大（如 2000ms）→ 过滤短暂字幕，减少噪音

- **采样间隔计算公式**:
  ```
  采样帧数 = fps * sample_ms / 1000
  例如：25fps 视频，800ms 间隔 → 每 20 帧采样一次
  ```

## 🔧 API 服务配置

### LM Studio（本地运行）

1. 下载并安装 [LM Studio](https://lmstudio.ai/)
2. 下载支持视觉的模型（如 Qwen-VL、LLaVA）
3. 启动本地服务器
4. 配置：
```env
OCR_API_ENDPOINT=http://localhost:1234
OCR_API_MODEL=qwen/qwen3-vl-8b
OCR_API_KEY=  # 可留空
```

### SiliconFlow（云端）

1. 注册 [SiliconFlow](https://cloud.siliconflow.cn/)
2. 获取 API 密钥
3. 配置：
```env
OCR_API_ENDPOINT=https://api.siliconflow.cn/v1
OCR_API_MODEL=Qwen/Qwen3-VL-8B
OCR_API_KEY=your_api_key_here
```

### 其他 OpenAI 兼容 API

支持任何 OpenAI 兼容的 API 服务：

```env
OCR_API_ENDPOINT=https://api.example.com/v1
OCR_API_MODEL=your-model-name
OCR_API_KEY=your_api_key
```

**重要提示**：确保模型支持 **视觉识别（Vision）** 功能

## 📋 文件说明

```
video-subtitle-extractor/
├── main.py                 # 主程序（完整功能）
├── requirements.txt        # Python 依赖
├── .env.example           # 环境变量配置示例
├── .gitignore             # Git 忽略文件
├── LICENSE                # MIT 许可证
├── README.md              # 详细的项目说明
├── QUICKSTART.md          # 快速上手指南
├── GITHUB_SETUP.md        # GitHub 上传指南
├── FILE_STRUCTURE.md      # 文件结构说明
├── CLAUDE.md              # Claude Code 项目说明
├── api_config_ui.py       # API 配置界面
├── config_manager.py      # 配置管理器
├── prompt_manager.py      # Prompt 管理器
├── prompt_config_ui.py    # Prompt 配置界面
└── configs/
    └── prompts.json       # Prompt 预设数据
```

## 🐛 常见问题

### Q: 终止按钮不生效？
A: 已优化为 5 秒最大响应时间。如果仍有问题，请检查：
- API 超时设置是否过长
- 网络连接是否正常

### Q: 日志显示"发现字幕"但没有输出？
A: 可能是 Prompt 导致模型返回描述性文本。请：
- 使用优化后的 Prompt（见上文的 Prompt 配置）
- 后处理过滤器会自动过滤描述性文本

### Q: 识别准确率低？
A: 尝试以下方法：
- 精确框选字幕区域（减少干扰）
- 使用更高质量的模型（Qwen3-VL-8B 或更大）
- 调整 Prompt，指定语言类型
- 检查视频清晰度

### Q: 如何处理没有字幕的视频？
A: 程序会自动跳过没有字幕的帧，只输出识别到字幕的片段。

### Q: 支持哪些视频格式？
A: 支持常见格式：MP4、MKV、AVI、MOV、WMV、FLV、WebM 等（依赖 OpenCV 支持）

### Q: 如何提高处理速度？
A:
- 使用 GPU 加速的 API 服务
- 增加采样间隔（减少 API 调用）
- 确保选择的字幕区域尽量小
- 使用本地 API（如 LM Studio）

## 🛠️ 技术栈

- **GUI 框架**: PyQt6
- **视频处理**: OpenCV
- **HTTP 请求**: Requests
- **图像编码**: Base64
- **配置管理**: 自定义配置管理器
- **API 格式**: OpenAI Chat Completions

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

```bash
git clone https://github.com/yourusername/video-subtitle-extractor.git
cd video-subtitle-extractor
pip install -r requirements.txt
```

### 代码规范

- 遵循 PEP 8 编码规范
- 添加必要的注释和文档字符串
- 提交前运行语法检查：`python -m py_compile main.py`

## 📄 许可证

本项目基于 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 感谢所有开源社区的贡献者
- 感谢 OpenAI 提供的 API 标准
- 感谢 PyQt 团队提供的优秀 GUI 框架

## 📧 联系方式

- 项目地址: [https://github.com/tiderzheng/eyes](https://github.com/tiderzheng/eyes)
- 提交 Issue: [GitHub Issues](https://github.com/tiderzheng/eyes/issues)

---

⭐ 如果这个项目对你有帮助，请给个 Star！
