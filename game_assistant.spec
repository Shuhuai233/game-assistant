# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Game Assistant.
Builds a single .exe with all dependencies bundled.

Usage (on Windows):
    pip install pyinstaller
    pyinstaller game_assistant.spec
"""

import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.yaml', '.'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        # Audio
        'sounddevice',
        'soundfile',
        'scipy.io.wavfile',
        # Edge TTS
        'edge_tts',
        # faster-whisper
        'faster_whisper',
        'ctranslate2',
        'onnxruntime',
        # OpenAI
        'openai',
        # Screen capture
        'mss',
        'mss.windows',
        'PIL',
        # Keyboard
        'keyboard',
        # YAML
        'yaml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'notebook',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GameAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Add icon='icon.ico' if you have one
)
