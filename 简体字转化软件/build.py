#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
构建脚本 - 使用PyInstaller打包应用

使用方法:
    python build.py          # 默认构建（目录模式）
    python build.py --onefile  # 单文件模式
    python build.py --clean    # 清理构建文件
"""

import argparse
import subprocess
import shutil
import sys
from pathlib import Path


def clean_build():
    """清理构建文件"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.pyc', '*.pyo']
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"删除目录: {dir_path}")
            shutil.rmtree(dir_path)
    
    # 清理src和tests目录下的__pycache__
    for subdir in ['src', 'tests']:
        cache_dir = Path(subdir) / '__pycache__'
        if cache_dir.exists():
            print(f"删除目录: {cache_dir}")
            shutil.rmtree(cache_dir)
    
    print("清理完成")


def build_app(onefile: bool = False):
    """
    构建应用
    
    Args:
        onefile: 是否构建单文件版本
    """
    spec_file = 'word_converter_onefile.spec' if onefile else 'word_converter.spec'
    
    if not Path(spec_file).exists():
        print(f"错误: 找不到spec文件 {spec_file}")
        sys.exit(1)
    
    print(f"使用配置文件: {spec_file}")
    print("开始构建...")
    
    # 运行PyInstaller
    cmd = ['pyinstaller', spec_file, '--noconfirm']
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n构建成功!")
        
        if onefile:
            print("可执行文件位于: dist/Word繁体转简体转换工具.exe")
        else:
            print("可执行文件位于: dist/Word繁体转简体转换工具/Word繁体转简体转换工具.exe")
            
    except subprocess.CalledProcessError as e:
        print(f"\n构建失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n错误: 找不到pyinstaller命令")
        print("请先安装PyInstaller: pip install pyinstaller")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Word繁体转简体转换工具构建脚本')
    parser.add_argument('--onefile', action='store_true', help='构建单文件版本')
    parser.add_argument('--clean', action='store_true', help='清理构建文件')
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
    else:
        build_app(onefile=args.onefile)


if __name__ == '__main__':
    main()
