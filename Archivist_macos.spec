# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['mytablewidget'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['_bootlocale', 'psutil', 'ctypes', 'tempfile'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Archivist',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Archivist',
)
app = BUNDLE(
    coll,
    name='Archivist.app',
    icon='app.icns',
    bundle_identifier=None,
    info_plist={
        'CFBundleShortVersionString': '0.1.0',
        'Associations': '7z zip rar dmg cdr iso pkg cpio exe',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeExtensions': ['7z', 'zip', 'rar', 'dmg', 'cdr', 'iso', 'pkg', 'cpio', 'exe'],
                'CFBundleTypeRole': 'Editor'
            }
        ]
    },
)
