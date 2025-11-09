# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Detect platform
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')
IS_MAC = sys.platform.startswith('darwin')

# Get Playwright browsers path based on platform
if IS_WINDOWS:
    playwright_browsers_path = Path.home() / 'AppData' / 'Local' / 'ms-playwright'
elif IS_LINUX:
    playwright_browsers_path = Path.home() / '.cache' / 'ms-playwright'
elif IS_MAC:
    playwright_browsers_path = Path.home() / 'Library' / 'Caches' / 'ms-playwright'
else:
    raise Exception(f"Unsupported platform: {sys.platform}")

block_cipher = None

a = Analysis(
    ['pagehawk.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('report_template.html', '.'),
        ('report_template.css', '.'),
        ('report_template.js', '.'),
        ('pagehawk_logo.png', '.'),
        ('visits_template.json', '.'),
        # Bundle Playwright browsers
        (str(playwright_browsers_path / 'chromium_headless_shell-1187'), 'playwright_browsers/chromium_headless_shell-1187'),
        (str(playwright_browsers_path / 'ffmpeg-1011'), 'playwright_browsers/ffmpeg-1011'),
    ],
    hiddenimports=[
        'playwright',
        'playwright.sync_api',
        'playwright._impl._api_types',
        'playwright._impl._browser',
        'playwright._impl._browser_context',
        'playwright._impl._browser_type',
        'playwright._impl._page',
        'greenlet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Set icon based on platform
if IS_WINDOWS:
    icon_file = 'pagehawk_icon.ico'
else:
    icon_file = None  # Linux/Mac typically don't use .ico files

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PageHawk',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
