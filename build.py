"""
PyInstaller Build Script for Eyes - Video Subtitle Extractor
自动打包脚本，生成 Windows 可执行文件
"""

import PyInstaller.__main__
import os
import sys
import shutil
from pathlib import Path

def clean_build_directories():
    """Clean previous build directories"""
    print("清理旧的构建目录...")
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除 {dir_name} 目录")

def create_distribution_package():
    """Create distribution package with necessary files"""
    print("\n创建分发包...")

    # Create dist directory if it doesn't exist
    if not os.path.exists('dist'):
        os.makedirs('dist')

    # Copy necessary files to dist
    files_to_copy = [
        ('.env.example', 'dist/.env.example'),
        ('README.md', 'dist/README.md'),
        ('QUICKSTART.md', 'dist/QUICKSTART.md'),
        ('LICENSE', 'dist/LICENSE'),
    ]

    for src, dst in files_to_copy:
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"已复制 {src} → {dst}")

    # Create configs directory in dist
    configs_dir = 'dist/configs'
    if not os.path.exists(configs_dir):
        os.makedirs(configs_dir)

    # Copy prompts.json
    if os.path.exists('configs/prompts.json'):
        shutil.copy2('configs/prompts.json', f'{configs_dir}/prompts.json')
        print("已复制 configs/prompts.json")

    print("\n✅ 分发包创建完成！")

def main():
    """Main build function"""
    print("=" * 60)
    print("Eyes - 视频字幕提取工具 打包脚本")
    print("=" * 60)

    # Clean previous builds
    clean_build_directories()

    print("\n开始打包...")
    print("=" * 60)

    # Get the path to the icon file if it exists
    icon_file = 'icon.ico'
    icon_option = ['--icon', icon_file] if os.path.exists(icon_file) else []

    # PyInstaller command options
    pyinstaller_args = [
        'main.py',  # Main script
        '--name=Eyes字幕提取工具',  # Executable name
        '--onefile',  # Create single executable file
        '--windowed',  # Hide console window (GUI application)
        '--noconfirm',  # Overwrite output files without asking
        '--clean',  # Clean cache

        # Add data files
        '--add-data', 'configs;configs',

        # Exclude unnecessary modules to reduce size
        '--exclude-module', 'tkinter',
        '--exclude-module', 'matplotlib',

        # Optimize
        '--strip',  # Strip symbols
        '--noupx',  # Don't use UPX (avoid antivirus false positives)
    ]

    # Add version file if exists
    if os.path.exists('version_info.txt'):
        pyinstaller_args.extend(['--version-file', 'version_info.txt'])

    # Add icon if exists
    if icon_option:
        pyinstaller_args.extend(icon_option)

    # Additional hidden imports (if needed)
    hidden_imports = [
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'cv2',
        'requests',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.backends',
    ]

    for module in hidden_imports:
        pyinstaller_args.extend(['--hidden-import', module])

    try:
        # Run PyInstaller
        print(f"\n执行命令: pyinstaller {' '.join(pyinstaller_args[1:])}")
        PyInstaller.__main__.run(pyinstaller_args)

        print("\n" + "=" * 60)
        print("[OK] 打包成功！")
        print("=" * 60)

        # Create distribution package
        create_distribution_package()

        # Print final instructions
        print("\n" + "=" * 60)
        print("[INFO] 分发包位置: dist/")
        print("[FILE] 可执行文件: dist/Eyes字幕提取工具.exe")
        print("=" * 60)

        print("\n[WARNING] 重要提示：")
        print("1. 首次运行前，请先将 .env.example 复制为 .env")
        print("2. 配置 API 信息后才能正常使用")
        print("3. 如果运行报错，请检查是否安装了 Visual C++ Redistributable")

        # Check final file size
        exe_path = os.path.join('dist', 'Eyes字幕提取工具.exe')
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n[INFO] 可执行文件大小: {size_mb:.2f} MB")

    except Exception as e:
        print(f"\n[ERROR] 打包失败: {e}")
        print("\n排查建议：")
        print("1. 确保已安装 PyInstaller: pip install pyinstaller")
        print("2. 确保所有依赖已安装: pip install -r requirements.txt")
        print("3. 尝试手动运行: pyinstaller main.py --name=Eyes字幕提取工具 --onefile --windowed")
        sys.exit(1)

if __name__ == '__main__':
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要 Python 3.8 或更高版本")
        sys.exit(1)

    # Check PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("❌ 错误: 未安装 PyInstaller")
        print("请运行: pip install pyinstaller")
        sys.exit(1)

    main()
