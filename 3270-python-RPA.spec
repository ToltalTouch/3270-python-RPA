# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['3270-python-RPA.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\python\\3270-python-RPA\\edgedriver_win64\\*', 'edgedriver_win64'), ('C:\\python\\3270-python-RPA\\__pycache__\\*', '__pycache__'), ('C:\\python\\3270-python-RPA\\config.py', '.'), ('C:\\python\\3270-python-RPA\\credential_manager.py', '.'), ('C:\\python\\3270-python-RPA\\download_terminal.py', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='3270-python-RPA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='3270-python-RPA',
)
