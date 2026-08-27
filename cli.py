"""
Presupuestador Sage 50 — CLI entry point
=========================================
Verifica si el puerto de Streamlit está libre; si no, busca uno disponible.
También acepta --port para indicar un puerto concreto.

Uso (tras pipx install):
    tarifas-sage50
    tarifas-sage50 --port 9000
"""

import argparse
import socket
import subprocess
import sys
import os


DEFAULT_PORT = 8599
APP_MODULE = "presupuestador"


def puerto_en_uso(puerto: int) -> bool:
    """Devuelve True si el puerto TCP ya está escuchando."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", puerto)) == 0


def buscar_puerto_libre(desde: int = 8600, hasta: int = 9000) -> int:
    """Busca el primer puerto libre en el rango dado."""
    for puerto in range(desde, hasta):
        if not puerto_en_uso(puerto):
            return puerto
    raise RuntimeError(f"No se encontró puerto libre en el rango {desde}-{hasta}")


def main():
    parser = argparse.ArgumentParser(
        description="Presupuestador Sage 50 — Genera presupuestos con Streamlit",
    )
    parser.add_argument(
        "--port", type=int, default=None,
        help=f"Puerto para Streamlit (defecto: {DEFAULT_PORT}, auto-si-ocupado)",
    )
    parser.add_argument(
        "--no-browser", action="store_true",
        help="No abrir el navegador automáticamente",
    )
    args = parser.parse_args()

    # Resolver puerto
    if args.port:
        puerto = args.port
    else:
        if puerto_en_uso(DEFAULT_PORT):
            puerto = buscar_puerto_libre()
            print(f"⚠️  Puerto {DEFAULT_PORT} en uso → usando puerto {puerto}")
        else:
            puerto = DEFAULT_PORT

    print(f"📋 Presupuestador Sage 50 arrancando en http://localhost:{puerto}")

    # Construir comando streamlit
    app_dir = os.path.dirname(os.path.abspath(__file__))
    app_file = os.path.join(app_dir, f"{APP_MODULE}.py")

    cmd = [
        sys.executable, "-m", "streamlit", "run", app_file,
        "--server.port", str(puerto),
        "--server.headless", "true",
    ]

    try:
        subprocess.run(cmd, cwd=app_dir)
    except KeyboardInterrupt:
        print("\n👋 Presupuestador detenido.")


if __name__ == "__main__":
    main()
