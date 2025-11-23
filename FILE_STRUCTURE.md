# 项目文件结构说明

## 提交到 GitHub 的文件

### 核心代码
```
✅ main.py                    # 主程序（完整功能）
✅ requirements.txt            # Python 依赖
✅ .env.example               # 环境变量配置示例
✅ api_config_ui.py           # API 配置界面
✅ config_manager.py          # 配置管理器
✅ prompt_manager.py          # Prompt 管理器
✅ prompt_config_ui.py        # Prompt 配置界面
✅ configs/prompts.json       # Prompt 预设数据
```

### 文档文件
```
✅ README.md                   # 详细的项目说明文档
✅ QUICKSTART.md              # 快速上手指南（5分钟教程）
✅ GITHUB_SETUP.md            # GitHub 上传指南
✅ LICENSE                    # MIT 许可证
✅ CLAUDE.md                  # Claude Code 项目说明
```

### Git 配置
```
✅ .gitignore                 # Git 忽略文件配置
```

## 被 .gitignore 忽略的文件（不会上传）

### 敏感信息（安全原因）
```
❌ .env                       # 包含 API 密钥
❌ configs/secret.key         # 加密密钥
❌ configs/api_configs.json   # API 配置数据
❌ configs/audit.log          # 审计日志
```

### 临时文件和缓存
```
❌ __pycache__/              # Python 缓存
❌ *.pyc                     # 编译的 Python 文件
❌ .claude/                  # Claude Code 配置
```

### 测试文件
```
❌ test_*.py                 # 所有测试脚本
❌ test_stop_fix.py         # 终止功能测试
❌ test_main_fix.py         # 主程序测试
❌ test_txt_export.py       # TXT 导出测试
```

### 旧版本文件
```
❌ main_simple.py           # 简化版本（不再需要）
❌ README_SIMPLE.md         # 简化版 README（已废弃）
❌ AGENTS.md                # Agents 说明（内部使用）
```

### 生成的文件
```
❌ *.mp4, *.mkv, *.avi      # 视频文件（用户自备）
❌ *.srt, *.txt             # 生成的字幕文件（自动输出）
```

## 推荐的 GitHub 仓库结构

上传后，GitHub 仓库应该只包含：

```
video-subtitle-extractor/
├── .gitignore
├── LICENSE
├── README.md
├── QUICKSTART.md
├── GITHUB_SETUP.md
├── CLAUDE.md
├── requirements.txt
├── .env.example
├── main.py
├── api_config_ui.py
├── config_manager.py
├── prompt_manager.py
├── prompt_config_ui.py
└── configs/
    └── prompts.json
```

## 安全提醒

✅ **安全做法**：
- .env 文件被忽略（不上传密钥）
- secret.key 被忽略（不上传加密密钥）
- api_configs.json 被忽略（不上传 API 配置）

⚠️ **上传前确认**：
- [x] 检查 `git status` 确保没有敏感文件
- [x] 检查 `.gitignore` 包含所有需要忽略的文件
- [x] 确认只有必要的文件被添加

## 文件说明

### 需要保持的版本控制
- 所有 `.py` 源代码文件
- 所有 `.md` 文档文件
- `requirements.txt`
- `.env.example`
- `configs/prompts.json`

### 不需要版本控制
- 个人配置文件
- 测试脚本（临时）
- 生成的输出文件
- 缓存和临时文件

## 首次下载后的设置

用户克隆仓库后，需要：

1. 复制配置：`cp .env.example .env`
2. 编辑 `.env` 文件，填入 API 信息
3. 安装依赖：`pip install -r requirements.txt`
4. 运行程序：`python main.py`

---

这个结构确保：
- ✅ 代码可以正常分享
- ✅ 用户数据不会泄露
- ✅ 仓库保持整洁
- ✅ 使用简单明了
