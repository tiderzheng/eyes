# 上传到 GitHub 指南

## 前提条件

1. 已安装 Git
2. 已有 GitHub 账号
3. 已完成项目开发

## 步骤

### 1. 在 GitHub 上创建新仓库

1. 登录 GitHub
2. 点击右上角的 "+" → "New repository"
3. 填写仓库信息：
   - Repository name: `eyes`
   - Description: `基于 AI 的视频字幕提取工具`
   - 选择 "Public"（开源）
   - 勾选 "Add a README file"（可选）
   - 点击 "Create repository"

### 2. 本地项目初始化

如果你还没有初始化 Git 仓库：

```bash
cd D:\ai\eyes  # 进入项目目录

# 如果还没有 Git 仓库
git init
```

### 3. 添加远程仓库

在 GitHub 创建仓库后，复制仓库的 HTTPS 或 SSH 地址：

```bash
# 使用 HTTPS（推荐新手）
git remote add origin https://github.com/tiderzheng/eyes.git

# 或使用 SSH（需要先配置 SSH 密钥）
git remote add origin git@github.com:tiderzheng/eyes.git
```

### 4. 检查 .gitignore

确保 `.gitignore` 文件已存在且配置正确：

```bash
# 检查 .gitignore 是否存在
ls -la .gitignore

# 应该包含以下内容：
# - __pycache__/
# - .env
# - configs/secret.key
# - configs/api_configs.json
# - *.mp4, *.srt, *.txt
```

### 5. 添加文件并提交

```bash
# 添加所有文件（除了 .gitignore 中指定的）
git add .

# 查看状态，确认忽略的文件不在其中
git status

# 提交更改
git commit -m "feat: 初始版本 - AI 视频字幕提取工具

功能特性：
- 视频加载和预览
- 可视化字幕区域选择
- AI 驱动的字幕 OCR 识别
- 实时进度显示和日志
- 响应式终止功能（5秒内）
- 同时生成 SRT 和 TXT 文件
- 支持多 API 配置和 Prompt 管理

技术栈：
- PyQt6 (GUI)
- OpenCV (视频处理)
- OpenAI 兼容 API (AI 识别)"
```

### 6. 推送到 GitHub

```bash
# 推送到远程仓库
git push -u origin main

# 如果是第一次推送，可能需要：
git push -u origin master  # 如果你的主分支是 master
```

**注意**：如果出现 "error: failed to push... updates were rejected"，先执行：

```bash
git pull --rebase origin main  # 或 master
git push -u origin main
```

### 7. 验证上传

访问你的 GitHub 仓库页面，确认：
- [x] 所有必要的文件都已上传
- [x] 敏感文件（.env、secret.key 等）被忽略
- [x] README.md 显示正常
- [x] 代码文件显示正确

### 8. 添加仓库描述和标签

在 GitHub 仓库页面：
1. 点击 "About" 右侧的齿轮图标 ⚙️
2. 添加描述："基于 AI 的视频字幕提取工具，支持可视化区域选择和实时进度显示"
3. 添加 Topics（标签）：
   - `video-subtitle`
   - `ai-ocr`
   - `pyqt6`
   - `opencv`
   - `openai-api`
   - `subtitle-extraction`
   - `computer-vision`
4. 保存更改

### 9. 创建第一个 Release（可选）

为项目创建版本号：

```bash
# 打标签
git tag -a v1.0.0 -m "第一个稳定版本"

# 推送标签到 GitHub
git push origin v1.0.0
```

然后在 GitHub 页面：
1. 点击 "Releases"
2. 点击 "Create a new release"
3. 选择标签 v1.0.0
4. 填写发布说明
5. 点击 "Publish release"

## 上传后检查清单

- [ ] 仓库设置为 Public（公开）
- [ ] README.md 显示正常
- [ ] 代码文件已上传
- [ ] 敏感文件被 .gitignore 忽略
- [ ] 添加了描述和标签
- [ ] 没有视频文件在仓库中
- [ ] 没有生成的字幕文件在仓库中
- [ ] 没有缓存文件（__pycache__）在仓库中

## 注意事项

1. **不要上传敏感信息**：
   - .env 文件（包含 API 密钥）
   - configs/secret.key（加密密钥）
   - configs/api_configs.json（API 配置）

2. **不要上传大文件**：
   - 视频文件（*.mp4, *.mkv 等）
   - 生成的字幕文件（*.srt, *.txt）

3. **包含必要的文档**：
   - README.md（主要说明）
   - QUICKSTART.md（快速上手）
   - LICENSE（许可证）
   - .env.example（配置示例）

4. **保持仓库整洁**：
   - 使用 .gitignore 忽略不需要的文件
   - 定期清理无用分支

## 推广你的项目

上传后，可以：

1. 在社交媒体上分享
2. 在相关技术论坛发帖
3. 添加更多示例和使用场景
4. 创建演示视频或 GIF
5. 持续更新和改进功能

## 需要帮助？

- Git 问题：查看 [Git 官方文档](https://git-scm.com/doc)
- GitHub 问题：查看 [GitHub Help](https://help.github.com)
- 项目问题：提交 Issue 到本仓库

祝你的项目大获成功！🎉
