# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller打包配置文件
Word繁体转简体转换工具

使用方法:
    pyinstaller word_converter.spec

生成的可执行文件位于 dist/Word繁体转简体转换工具/ 目录下
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# 项目根目录
ROOT_DIR = Path(SPECPATH)

# 收集OpenCC数据文件
opencc_datas = collect_data_files('opencc')

# 收集所有需要的子模块
hidden_imports = [
    'opencc',
    'docx',
    'docx.oxml',
    'docx.oxml.ns',
    'docx.oxml.text',
    'docx.oxml.table',
    'docx.shared',
    'docx.enum.text',
    'docx.enum.style',
    'docx.enum.table',
    'lxml',
    'lxml._elementpath',
    'lxml.etree',
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
]

# 分析配置
a = Analysis(
    ['src/main.py'],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=[
        *opencc_datas,
        # 添加资源文件（如果有）
        # ('resources/*', 'resources'),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'hypothesis',
        'pytest_qt',
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 打包配置
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

# 可执行文件配置
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Word繁体转简体转换工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='resources/icon.ico',  # 如果有图标文件
)

# 收集所有文件
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Word繁体转简体转换工具',
)
