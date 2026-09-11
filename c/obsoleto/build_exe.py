"""
Build script — Genera el .exe del Presupuestador Sage 50
=========================================================
Requiere: pip install pyinstaller

Uso:
    python build_exe.py
"""

import subprocess
import sys
import os


def main():
    base = os.path.dirname(os.path.abspath(__file__))

    print("=" * 55)
    print("  BUILD — Presupuestador Sage 50 (.exe)")
    print("=" * 55)

    # Verificar pyinstaller
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("\n[ERROR] PyInstaller no encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Verificar dependencias (nombre de importación, nombre pip)
    # Nota: el paquete pip "pywebview" se importa como "webview"
    for mod, pip_name in [
        ("streamlit", "streamlit"),
        ("pandas", "pandas"),
        ("openpyxl", "openpyxl"),
        ("reportlab", "reportlab"),
        ("webview", "pywebview"),
    ]:
        try:
            __import__(mod)
        except ImportError:
            print(f"\n[ERROR] Falta dependencia: {pip_name}")
            print(f"   Ejecuta: pip install {pip_name}")
            sys.exit(1)

    # Ejecutar PyInstaller
    spec_file = os.path.join(base, "tarifas_sage50.spec")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        spec_file,
    ]

    print(f"\nGenerando ejecutable...")
    print(f"   Spec: {spec_file}")
    print()

    result = subprocess.run(cmd, cwd=base)

    if result.returncode == 0:
        exe_path = os.path.join(base, "dist", "PresupuestadorSage50.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print()
            print("=" * 55)
            print(f"  OK - Ejecutable generado correctamente")
            print(f"  Ruta: {exe_path}")
            print(f"  Tamano: {size_mb:.1f} MB")
            print("=" * 55)
        else:
            print(f"\n[WARN] Build exitoso pero no se encontro el .exe en dist/")
    else:
        print(f"\n[ERROR] Error durante el build (codigo {result.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    main()
