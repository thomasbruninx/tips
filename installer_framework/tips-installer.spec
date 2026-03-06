# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['installer_framework/main.py'],
    pathex=[],
    binaries=[],
    datas=[('examples', 'examples'), ('/Users/thomasbruninx/Projecten/tips/installer_framework/build/default_config_path.txt', 'build'), ('installer_framework/config/schema.json', 'installer_framework/config'), ('/Users/thomasbruninx/Projecten/tips/installer_framework/examples/assets/OpenSans-Regular.ttf', 'examples/assets'), ('/Users/thomasbruninx/Projecten/tips/plugins', 'plugins')],
    hiddenimports=['PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip'],
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
    name='tips-installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['/Users/thomasbruninx/Projecten/tips/installer_framework/examples/assets/appicon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='tips-installer',
)
app = BUNDLE(
    coll,
    name='tips-installer.app',
    icon='/Users/thomasbruninx/Projecten/tips/installer_framework/examples/assets/appicon.icns',
    bundle_identifier=None,
)
