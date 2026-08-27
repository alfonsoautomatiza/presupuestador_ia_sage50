# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Presupuestador Sage 50
Genera un .exe standalone con Streamlit embebido.

Uso:
    pip install pyinstaller
    pyinstaller tarifas_sage50.spec
"""

import os
import sys
import importlib

from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

# Directorio base del proyecto
BASE = os.path.abspath(SPECPATH)

# Localizar paquetes que PyInstaller no detecta automáticamente
def find_package_path(name):
    """Devuelve la ruta al paquete para datas."""
    mod = importlib.import_module(name)
    # Para paquetes con __path__, usar el primero
    if hasattr(mod, '__path__'):
        return mod.__path__[0]
    # Para módulos, usar el directorio padre
    return os.path.dirname(mod.__file__)

# Paquetes de streamlit y dependencias que necesitan assets estáticos
hiddenimports = [
    "streamlit",
    "streamlit.web",
    "streamlit.web.bootstrap",
    "streamlit.runtime",
    "streamlit.runtime.scriptrunner",
    "streamlit.components",
    "streamlit.components.v1",
    "pandas",
    "openpyxl",
    "reportlab",
    "reportlab.lib",
    "reportlab.platypus",
    "pyarrow",
    "altair",
    # Native window mode (pywebview)
    "webview",
]

# Archivos de datos a incluir
datas = [
    # Streamlit static files (esenciales para la UI)
    (find_package_path("streamlit") + "/static", "streamlit/static"),
    # Datos de la app
    (os.path.join(BASE, "data"), "data"),
    (os.path.join(BASE, ".streamlit"), ".streamlit"),
    # El propio script de la app y sus módulos puros
    (os.path.join(BASE, "presupuestador.py"), "."),
    (os.path.join(BASE, "models.py"), "."),
    (os.path.join(BASE, "tariff_parser.py"), "."),
    (os.path.join(BASE, "pdf_generator.py"), "."),
    (os.path.join(BASE, "excel_generator.py"), "."),
]

# Package metadata (dist-info) for packages that call
# importlib.metadata.version() at runtime (streamlit/version.py etc.)
for _pkg in ["streamlit", "altair", "pyarrow", "pandas", "pywebview", "click"]:
    try:
        datas += copy_metadata(_pkg)
    except Exception:
        pass

# Binarios que PyInstaller puede necesitar
binaries = []

a = Analysis(
    [os.path.join(BASE, "launcher.py")],
    pathex=[BASE],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "scipy", "numpy.f2py", "tkinter",
        "PIL.ImageQt", "PyQt5", "IPython", "jupyter",
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PresupuestadorSage50",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)
