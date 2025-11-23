# Windows EXE 打包指南

## 📦 打包说明

本指南介绍如何将 Eyes 视频字幕提取工具打包成 Windows 可执行文件（.exe），无需安装 Python 环境即可运行。

## ✅ 前置要求

### 1. 安装 Python
- Python 3.8 或更高版本
- 下载地址：https://www.python.org/downloads/
- **安装时务必勾选 "Add Python to PATH"**

### 2. 安装依赖

```bash
# 在项目目录下打开命令行
cd D:\ai\eyes

# 安装所有依赖（包括 PyInstaller）
pip install -r requirements.txt
```

**requirements.txt 包含**：
- PyQt6
- opencv-python
- numpy
- requests
- cryptography
- PyInstaller

## 🚀 快速打包（推荐）

### 方法一：双击运行（最简单）

1. 双击运行 `build.bat`
2. 等待打包完成
3. 完成后在 `dist/` 目录找到 `.exe` 文件

### 方法二：命令行运行

```bash
# 方式1：运行批处理文件
build.bat

# 方式2：运行 Python 脚本
python build.py
```

## 🔧 手动打包（高级）

如果需要自定义打包参数，可以使用 PyInstaller 命令：

```bash
pyinstaller main.py \
    --name="Eyes字幕提取工具" \
    --onefile \
    --windowed \
    --add-data="configs;configs" \
    --exclude-module="tkinter" \
    --exclude-module="matplotlib" \
    --hidden-import="PyQt6.QtCore" \
    --hidden-import="PyQt6.QtGui" \
    --hidden-import="PyQt6.QtWidgets" \
    --hidden-import="cv2" \
    --hidden-import="requests" \
    --clean \
    --strip \
    --noupx
```

## 📊 打包后文件说明

打包完成后，项目目录结构：

```
D:\ai\eyes/
├── build/                           # 构建临时文件（可删除）
├── dist/                            # 分发包
│   ├── Eyes字幕提取工具.exe          # 🎯 主程序（可执行文件）
│   ├── .env.example                 # 环境变量示例
│   ├── README.md                    # 项目说明
│   ├── QUICKSTART.md               # 快速上手指南
│   ├── LICENSE                      # 许可证
│   └── configs/
│       └── prompts.json             # Prompt 预设
└── ...
```

## 📦 分发包使用

### 使用方法

1. **解压分发包**（如果是压缩包）
2. **配置环境变量**：
   - 将 `.env.example` 复制为 `.env`
   - 编辑 `.env` 文件，配置 API 信息
3. **运行程序**：
   - 双击 `Eyes字幕提取工具.exe`

### 首次运行配置

```env
# .env 文件示例
OCR_API_ENDPOINT=http://localhost:1234
OCR_API_MODEL=qwen/qwen3-vl-8b
OCR_API_KEY=your_api_key_here
OCR_PROMPT=只返回图片中的可读字幕文本
```

### 推荐配置

**对于普通用户（不想配置 API）**：
- 推荐下载并安装 LM Studio
- 下载 Qwen3-VL-8B 模型
- 在 LM Studio 中启动本地服务器
- 使用默认的 `.env` 配置即可

## ⚠️ 常见问题

### 1. 打包时报错：ModuleNotFoundError

**原因**：缺少依赖模块

**解决**：
```bash
pip install -r requirements.txt
```

### 2. 运行时报错：找不到 .env 文件

**原因**：没有配置环境变量

**解决**：
- 复制 `.env.example` 为 `.env`
- 编辑并填写 API 信息

### 3. 运行时报错：Visual C++ Redistributable

**原因**：缺少 Visual C++ 运行时

**解决**：
- 下载并安装 Visual C++ Redistributable for Visual Studio 2015-2022
- 下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe

### 4. 打包后的 exe 文件很大

**原因**：PyInstaller 打包了所有依赖

**解决方法**：
- 正常现象，通常 100-200MB
- 可以使用 UPX 压缩（可能触发杀毒软件误报）
- 在 `build.py` 中移除 `--noupx` 参数，添加 `--upx-dir` 参数

### 5. 杀毒软件报病毒

**原因**：PyInstaller 打包的 exe 可能被误报

**解决**：
- 这是 PyInstaller 的已知问题
- 将 exe 文件添加到杀毒软件白名单
- 或者使用 `--noupx` 参数重新打包（推荐）

### 6. 打包时报错：RecursionError

**原因**：递归深度限制

**解决**：
在 `build.py` 中增加递归限制：
```python
import sys
sys.setrecursionlimit(10000)
```

### 7. 运行时界面显示异常

**原因**：高 DPI 显示器兼容性问题

**解决**：
在 `main.py` 的 `main()` 函数中添加：
```python
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
```

## 🔧 自定义打包

### 添加程序图标

1. 准备 `.ico` 格式的图标文件（推荐 256x256）
2. 将文件命名为 `icon.ico` 并放在项目根目录
3. 重新运行打包脚本

### 修改版本信息

编辑 `version_info.txt` 文件：
```
VSVersionInfo(
  ffi=FixedFileInfo(...),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'你的公司名'),
         StringStruct(u'ProductVersion', u'2.0.0.0'),  # 修改版本号
         ...
        ])
    ])
  ]
)
```

### 修改打包参数

编辑 `build.py` 文件，修改 `pyinstaller_args` 列表：

```python
pyinstaller_args = [
    'main.py',
    '--name="自定义名称"',        # 修改程序名称
    '--onefile',
    '--windowed',
    '--add-data', 'configs;configs',  # 添加更多数据文件
    '--exclude-module', '模块名',      # 排除不需要的模块
    # 更多参数...
]
```

### 常用 PyInstaller 参数说明

| 参数 | 说明 |
|------|------|
| `--onefile` | 打包成单个可执行文件 |
| `--windowed` | 不显示控制台窗口（GUI 程序） |
| `--icon=icon.ico` | 添加程序图标 |
| `--add-data="src;dest"` | 添加数据和配置文件 |
| `--exclude-module=MODULE` | 排除不需要的模块 |
| `--hidden-import=MODULE` | 添加隐藏导入（PyInstaller 检测不到的） |
| `--noupx` | 不使用 UPX 压缩（防误报） |
| `--clean` | 清理临时文件 |
| `--strip` | 剥离符号信息 |
| `--debug=all` | 调试模式（开发时使用） |

## 📦 UPX 压缩（可选）

### 安装 UPX

1. 下载 UPX：https://github.com/upx/upx/releases
2. 解压到 `C:\Program Files\upx\`
3. 添加到系统 PATH 环境变量

### 使用 UPX 压缩

在 `build.py` 中修改：
```python
pyinstaller_args = [
    ...
    # 移除 '--noupx',
    '--upx-dir', 'C:\\Program Files\\upx',
    # 或者添加到 PATH 后直接移除 --noupx
]
```

⚠️ **注意**：使用 UPX 可能会被部分杀毒软件误报为病毒，请谨慎使用。

## 🎯 优化可执行文件大小

### 1. 使用虚拟环境

推荐在虚拟环境中打包，避免打包不必要的包：

```bash
# 创建虚拟环境
python -m venv build_env

# 激活虚拟环境
build_env\Scripts\activate

# 在虚拟环境中安装依赖
pip install -r requirements.txt

# 打包
python build.py
```

### 2. 排除不必要的模块

在 `build.py` 中排除不需要的模块：
```python
exclude_modules = [
    'matplotlib',
    'pandas',
    'scipy',
    'PIL',
    'test',
]

for module in exclude_modules:
    pyinstaller_args.extend(['--exclude-module', module])
```

### 3. 移除调试信息

确保使用 `--strip` 参数：
```python
pyinstaller_args = [
    ...
    '--strip',  # 剥离符号信息，减小文件大小
]
```

## 🔍 调试打包问题

### 启用调试模式

修改 `build.py`：
```python
pyinstaller_args = [
    'main.py',
    '--name="Eyes字幕提取工具"',
    '--debug=all',  # 启用调试模式
    '--log-level=DEBUG',  # 显示详细日志
]
```

在应用程序运行时会显示更多调试信息。

### 查看 PyInstaller 日志

1. PyInstaller 会在 `build/` 目录生成日志文件
2. 查看 `warn-*.txt` 文件中的警告信息
3. 查看 `xrefs-*.html` 查看模块依赖关系

### 运行时调试

如果打包后的程序运行时崩溃：

1. **在命令行中运行**：
```bash
dist\Eyes字幕提取工具.exe
```
查看错误输出

2. **启用控制台窗口**（临时）：
```bash
pyinstaller main.py --name=Eyes --onefile
```
移除 `--windowed` 参数，重新打包，查看控制台输出。

## 📋 完整打包流程

### 完整步骤（推荐顺序）

```bash
# 1. 确保所有代码已提交
git status
git add .
git commit -m "feat: 准备打包发布"

# 2. 创建虚拟环境（可选，推荐）
python -m venv build_env
build_env\Scripts\activate

# 3. 更新依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. 测试程序（确保能正常运行）
python main.py

# 5. 运行打包脚本
double-click: build.bat
or
run: python build.py

# 6. 验证打包结果
cd dist
Eyes字幕提取工具.exe

# 7. 测试所有功能
- 打开视频
- 框选区域
- 提取字幕
- 检查输出文件

# 8. 分发
- 压缩 dist 目录
- 上传到 GitHub Release
- 分享给用户
```

## 🚀 自动化构建（GitHub Actions）

可以配置 GitHub Actions 自动打包：

创建 `.github/workflows/build.yml`：
```yaml
name: Build Windows EXE

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.8'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Build with PyInstaller
        run: |
          python build.py

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: Eyes-subtitle-extractor
          path: dist/
```

## 📌 注意事项

### 打包前检查清单

- [ ] 代码已测试，可以正常运行
- [ ] requirements.txt 包含所有依赖
- [ ] .env.example 文件已配置
- [ ] README.md 已更新
- [ ] 版本号已更新
- [ ] 在虚拟环境中打包（推荐）
- [ ] 已清理旧的构建文件
- [ ] 已检查 `.gitignore` 配置

### 分发前检查清单

- [ ] 在干净的 Windows 系统上测试
- [ ] 测试所有功能是否正常
- [ ] 检查 .env 配置是否正确
- [ ] 确保包含了所有必要的文件
- [ ] 已添加使用说明文档
- [ ] 已测试不同的视频格式

## 📞 常见问题

**Q: 打包后的程序运行很慢？**
A: 首次启动会解压文件，稍等片刻。后续运行会快很多。

**Q: 可以打包成单个文件吗？**
A: 已经使用 `--onefile` 参数打包成单个 exe 文件。

**Q: 支持 Windows 7 吗？**
A: 需要安装 Visual C++ Redistributable，建议使用 Windows 10/11。

**Q: 文件大小可以优化吗？**
A: 可以使用 UPX 压缩，但可能触发杀毒软件误报。

**Q: 支持 macOS/Linux 吗？**
A: 需要在对应系统上使用 PyInstaller 重新打包，本配置仅针对 Windows。

## 📚 参考资源

- PyInstaller 官方文档：https://pyinstaller.readthedocs.io/
- LM Studio 官网：https://lmstudio.ai/
- Visual C++ Redistributable：https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist

---

## 🎉 完成！

打包完成后，你就可以将 `dist/` 目录压缩分享给其他 Windows 用户，他们无需安装 Python 环境即可使用！
