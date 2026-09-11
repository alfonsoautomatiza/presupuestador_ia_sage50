# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the psage Gradio application."""
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

BASE = os.path.abspath(SPECPATH)
app_modules = ["presupuestador.py", "gradio_app.py", "models.py", "tariff_parser.py", "pdf_generator.py", "excel_generator.py", "json_generator.py", "templates.py"]
hiddenimports = (
    ["pandas", "openpyxl", "reportlab", "reportlab.lib", "reportlab.platypus", "webview"]
    + collect_submodules("gradio")
    + collect_submodules("fastapi")
    + collect_submodules("uvicorn")
    + collect_submodules("websockets")
)
datas = [(os.path.join(BASE, "data"), "data")]
for package in ("gradio", "fastapi", "uvicorn", "websockets"):
    try:
        datas += collect_data_files(package, include_py_files=False)
        datas += copy_metadata(package)
    except Exception:
        pass
for filename in app_modules:
    datas.append((os.path.join(BASE, filename), "."))
for package in ("pandas", "openpyxl", "reportlab", "pywebview"):
    try:
        datas += copy_metadata(package)
    except Exception:
        pass

a = Analysis([os.path.join(BASE, "cli.py")], pathex=[BASE], binaries=[], datas=datas, hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=["matplotlib", "scipy", "numpy.f2py", "tkinter", "PIL.ImageQt", "PyQt5", "IPython", "jupyter"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="psage", debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=True, icon=None)
