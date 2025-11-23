# 快速上手指南

## 5 分钟开始使用

### 第 1 步：安装

```bash
# 克隆项目
git clone https://github.com/tiderzheng/eyes.git
cd eyes

# 安装依赖
pip install -r requirements.txt
```

### 第 2 步：配置 API

```bash
# 复制配置文件
cp .env.example .env
```

编辑 `.env` 文件，根据你的情况选择配置：

#### 方案 A：使用 LM Studio（本地，推荐新手）

```env
OCR_API_ENDPOINT=http://localhost:1234
OCR_API_MODEL=qwen/qwen3-vl-8b
OCR_API_KEY=
```

**设置步骤**：
1. 下载 [LM Studio](https://lmstudio.ai/) 并安装
2. 在 LM Studio 中搜索并下载 `qwen3-vl-8b` 模型
3. 启动本地服务器（默认端口 1234）

#### 方案 B：使用 SiliconFlow（云端）

```env
OCR_API_ENDPOINT=https://api.siliconflow.cn/v1
OCR_API_MODEL=Qwen/Qwen3-VL-8B
OCR_API_KEY=你的API密钥
```

**获取 API 密钥**：
1. 访问 [SiliconFlow](https://cloud.siliconflow.cn/)
2. 注册并登录账号
3. 在控制台获取 API 密钥

### 第 3 步：运行程序

```bash
python main.py
```

### 第 4 步：提取字幕

1. 点击"打开视频"，选择视频文件
2. 用鼠标在视频上框选字幕区域
3. 点击"开始提取"
4. 等待完成，查看日志
5. 在视频同目录下找到生成的 `.srt` 和 `.txt` 文件

## 常见问题快速解决

### ❌ 错误：API 连接失败

**原因**：API 服务未启动或配置错误

**解决**：
- LM Studio：确保 LM Studio 正在运行且模型已加载
- SiliconFlow：检查 API 密钥是否正确
- 检查 `.env` 文件中的 `OCR_API_ENDPOINT`

### ❌ 错误：识别结果全是描述性文本

**原因**：Prompt 不够明确

**解决**：
确保 `.env` 中的 Prompt 包含明确指令：
```env
OCR_PROMPT=只返回图片中的可读字幕文本。如果图片中没有字幕或文字，只返回空字符串，不要任何解释或描述。
```

### ⚠️ 警告：处理速度慢

**优化方法**：
- 增加采样间隔：修改 main.py 中的 `sample_ms` 参数（如从 800 改为 1200）
- 缩小字幕区域：精确框选字幕，减少不必要的图像处理
- 使用本地 API（LM Studio 比云端快）

### ⚠️ 警告：字幕识别不完整

**优化方法**：
- 减小采样间隔（如从 800 改为 500），捕获更多字幕变化
- 确保字幕区域完全包含在选框内
- 检查视频清晰度，低分辨率视频识别率较低

### ⚠️ 警告：有很多重复字幕

**优化方法**：
- 增加`最短字幕时长`参数：修改 main.py 中的 `min_duration_ms`（如从 1200 改为 2000）
- 这可以过滤掉短暂出现的字幕变化

## 最佳实践

### ✨ 提高识别准确率

1. **精确选择区域**：只框选字幕区域，避免包含视频内容
2. **选择合适的模型**：Qwen3-VL-8B 比 Qwen2-VL 更准确
3. **针对语言优化 Prompt**：
   - 中文视频：`只返回可读的中文字幕文本`
   - 英文视频：`Only return readable English subtitles`

### ✨ 提高处理速度

1. **本地处理**：使用 LM Studio 比云端 API 快
2. **增大采样间隔**：如果对时间精度要求不高
3. **选择小区域**：字幕区域越小，处理越快

### ✨ 获得干净的结果

1. **使用优化的 Prompt**（见上文）
2. **调整后处理参数**：
   - 增加最短字幕时长过滤噪音
   - 调整采样间隔平衡速度和精度

## 马上开始

完成以上 4 步，你就可以开始提取字幕了！

遇到问题？查看 [README.md](README.md) 的详细说明或提交 Issue。
