@echo off
chcp 65001 >nul
REM build.bat - Eyes 视频字幕提取工具打包脚本
REM 为 Windows 用户提供的便捷打包工具

echo =======================================================
echo Eyes - 视频字幕提取工具 打包脚本
echo =======================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python，请确保已安装 Python 3.8+
    echo.
    pause
    exit /b 1
)

echo ✅ Python 已安装

REM 检查 PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装 PyInstaller
    echo 💡 正在尝试自动安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ PyInstaller 安装失败，请手动运行: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo ✅ PyInstaller 已安装

REM 清理旧的构建目录
echo.
echo 清理旧的构建目录...
if exist build (
    rmdir /s /q build
    echo 已删除 build 目录
)
if exist dist (
    rmdir /s /q dist
    echo 已删除 dist 目录
)

REM 运行打包脚本
echo.
echo =======================================================
echo 开始打包...
echo =======================================================
echo.

python build.py

if errorlevel 1 (
    echo.
    echo ❌ 打包失败，请查看错误信息
    pause
    exit /b 1
)

echo.
echo =======================================================
echo ✅ 打包完成！
echo =======================================================
echo.
echo 📦 分发包位置: dist\
echo 📄 可执行文件: dist\Eyes字幕提取工具.exe
echo.

REM 检查文件是否存在
if exist "dist\Eyes字幕提取工具.exe" (
    echo 📊 文件大小:
    for %%I in ("dist\Eyes字幕提取工具.exe") do echo %%~zI 字节
    echo.
    echo 💡 提示：
    echo 1. 首次运行前，请将 dist\.env.example 复制为 .env
    echo 2. 配置 API 信息后才能正常使用
    echo 3. 如果运行时报错，请安装 Visual C++ Redistributable
) else (
    echo ❌ 可执行文件未生成，请检查错误信息
)

echo.
echo 是否打开输出目录？(y/n)
set /p open_dir=
if /i "%open_dir%"=="y" (
    start explorer dist\
)

echo.
pause
