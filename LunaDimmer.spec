# -*- mode: python ; coding: utf-8 -*-
"""
Luna Dimmer - 官方精确瘦身构建配置 (PyInstaller Production Spec)

核心设计目标：
1. 0 误报白名单：绝不采用 UPX 压缩壳，保持 Windows Defender / 360 / 火绒 100% 纯净免杀；
2. 0 启动延迟：免去运行时二次解压解密，维持 1 秒内极致秒开；
3. 二进制精准脱壳：剔除 PyInstaller QtGui hook 默认捆绑的 15MB+ 无用 C++ 驱动与动态库
   (opengl32sw.dll、d3dcompiler_47.dll、Qt5Quick.dll、Qt5Qml.dll、Qt5Network.dll 等)。
"""

import os

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'pydoc',
        'sqlite3',
        'PyQt5.QtNetwork',
        'PyQt5.QtQml',
        'PyQt5.QtQuick',
        'PyQt5.QtSql',
        'PyQt5.QtSvg',
        'PyQt5.QtTest',
        'PyQt5.QtBluetooth',
        'PyQt5.QtMultimedia',
        'PyQt5.QtPositioning',
        'PyQt5.QtSensors',
        'PyQt5.QtSerialPort',
        'PyQt5.QtWebChannel',
        'PyQt5.QtWebSockets',
        'PyQt5.QtXml',
        'PyQt5.QtXmlPatterns',
        'PyQt5.QtPrintSupport',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 核心二进制精简：过滤掉 Qt hook 盲目包含的未使用的巨型 C++ DLL
# 经过真实运行链路检测，LunaDimmer 仅使用 QtWidgets、QtGui、QtCore 与 Windows 原生绘图
unwanted_binaries = {
    'opengl32sw.dll',      # 软件 OpenGL 模拟器 (单文件占 7.4MB 压缩体积，桌面真实渲染使用 DirectX/系统显卡驱动)
    'd3dcompiler_47.dll',  # HLSL 编译库 (占 1.7MB，Qt2D 矢量绘制无需独立着色器编译器)
    'libglesv2.dll',       # GLES 模拟库 (占 1.2MB)
    'qt5quick.dll',        # QML/Quick 引擎 (占 1.5MB)
    'qt5qml.dll',          # QML 运行时 (占 1.3MB)
    'qt5qmlmodels.dll',    # QML 数据模型 (占 0.3MB)
    'qt5network.dll',      # Qt 网络库 (占 0.5MB，本项目使用内置轻量 urllib)
    'qminimal.dll',        # 仅用于无头测试的平台插件
    'qoffscreen.dll',      # 仅用于离屏测试的平台插件
    'qwebgl.dll',          # WebGL 平台插件
}

a.binaries = [
    b for b in a.binaries
    if os.path.basename(str(b[0])).lower() not in unwanted_binaries
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LunaDimmer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 绝不使用 UPX 加壳，避免杀软误报与冷启动解密卡顿
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('assets', 'icon.ico'),
)
