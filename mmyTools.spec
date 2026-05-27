# -*- mode: python ; coding: utf-8 -*-
# 咩咩羊 Tools — PyInstaller spec
# 打包命令：
#   .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean mmyTools.spec

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

# ── shiboken6 / paho 手动收集（PyInstaller hooks 不会自动处理这两个小包）───────
binaries      = []
datas         = []
hiddenimports = []

for pkg in ('shiboken6', 'paho'):
    d, b, h = collect_all(pkg)
    datas         += d
    binaries      += b
    hiddenimports += h

# ── PySide6 交给 PyInstaller 内置 hooks 自动收集，这里只声明需要的子模块 ──────
hiddenimports += [
    'PySide6.QtWidgets',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'shiboken6',
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.utils',
    'paho.mqtt.client',
    'paho.mqtt.publish',
    'paho.mqtt.subscribe',
    'zoneinfo',
]

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 明确排除不用的重型 Qt 模块，阻止 hooks 把它们拉进来
        'PySide6.Qt3DAnimation', 'PySide6.Qt3DCore',   'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput',     'PySide6.Qt3DLogic',  'PySide6.Qt3DRender',
        'PySide6.QtBluetooth',   'PySide6.QtCharts',   'PySide6.QtDataVisualization',
        'PySide6.QtDesigner',    'PySide6.QtHelp',     'PySide6.QtLocation',
        'PySide6.QtMultimedia',  'PySide6.QtMultimediaWidgets',
        'PySide6.QtNfc',         'PySide6.QtPositioning',
        'PySide6.QtQml',         'PySide6.QtQuick',    'PySide6.QtQuick3D',
        'PySide6.QtQuickControls2', 'PySide6.QtQuickWidgets',
        'PySide6.QtRemoteObjects', 'PySide6.QtSensors', 'PySide6.QtSerialPort',
        'PySide6.QtSpatialAudio', 'PySide6.QtTest',
        'PySide6.QtWebChannel',   'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineQuick',
        'PySide6.QtWebEngineWidgets', 'PySide6.QtWebSockets',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# ─── EXE（onedir 模式：DLL 不压缩进 exe，运行时无解压，不会出现 Qt6Core.dll 报错）
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # ← onedir 关键：DLL 单独放，不内嵌
    name='mmyTools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='sheep.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ─── COLLECT（把所有 DLL / 数据收集到 dist\mmyTools\ 文件夹）────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='mmyTools',
)
