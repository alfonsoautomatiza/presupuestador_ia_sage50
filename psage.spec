# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for psage (Presupuestador Sage 50)
Build: pyinstaller psage.spec
Output: dist/psage.exe
"""
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
project_root = os.getcwd()

# Recolecta todos los datos y submodulos de Gradio
gradio_datas = collect_data_files('gradio', includes=['*.json', '*.html', '*.css', '*.js'])
gradio_client_datas = collect_data_files('gradio_client', includes=['*.json'])
gradio_submodules = collect_submodules('gradio')
gradio_client_submodules = collect_submodules('gradio_client')

a = Analysis(
    ['cli.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('originales', 'originales'),
        ('*.py', '.'),
    ] + gradio_datas + gradio_client_datas,
    hiddenimports=[
        'gradio',
        'gradio.components',
        'gradio.blocks',
        'pandas',
        'openpyxl',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib',
        'platformdirs',
        # Módulos locales del proyecto
        'gradio_app',
        'presupuestador',
        'models',
        'tariff_parser',
        'templates',
        'pdf_generator',
        'excel_generator',
        'json_generator',
        'simplificar_tarifas',
    ] + gradio_submodules + gradio_client_submodules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='psage',
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
    icon=None,
)
