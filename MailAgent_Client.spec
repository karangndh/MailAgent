# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['outlook_hybrid_client_windows.py'],
    pathex=[],
    binaries=[],
    datas=[('outlook_web_summarizer_hybrid.py', '.')],
    hiddenimports=['requests', 'tkinter', 'webbrowser'],
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
    a.binaries,
    a.datas,
    [],
    name='MailAgent_Client',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='MailAgent_Client.app',
    icon=None,
    bundle_identifier=None,
)
