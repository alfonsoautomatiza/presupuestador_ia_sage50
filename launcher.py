"""
Presupuestador Sage 50 — Launcher
=================================
Funciona en tres modos:
  1. Desarrollo / pipx: lanza streamlit vía subprocess
  2. Ejecutable PyInstaller (.exe): lanza streamlit programáticamente
  3. Ventana nativa (--window): streamlit en un hilo background y una
     ventana pywebview; es el modo por defecto del .exe

Autor: ALCA TIC S.L.
"""

import argparse
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser


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


def resolver_puerto(cli_port=None):
    """Resuelve el puerto a usar."""
    if cli_port:
        return cli_port
    if puerto_en_uso(DEFAULT_PORT):
        puerto = buscar_puerto_libre()
        print(f"[WARN] Puerto {DEFAULT_PORT} en uso -> usando puerto {puerto}")
        return puerto
    return DEFAULT_PORT


def _base_dir():
    """Directorio base del proyecto (compatible con PyInstaller)."""
    if getattr(sys, "frozen", False):
        # Modo PyInstaller: _MEIPASS tiene los archivos extraídos
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def main_subprocess(puerto, app_file, app_dir, no_browser=False):
    """Modo normal: lanza streamlit vía subprocess."""
    cmd = [
        sys.executable, "-m", "streamlit", "run", app_file,
        "--server.port", str(puerto),
        "--server.headless", "true",
    ]
    if not no_browser:
        webbrowser.open(f"http://localhost:{puerto}")
    try:
        subprocess.run(cmd, cwd=app_dir)
    except KeyboardInterrupt:
        print("\nPresupuestador detenido.")


def main_frozen(puerto, app_file, no_browser=False):
    """Modo PyInstaller: lanza streamlit programáticamente."""
    import streamlit.config as st_config
    import streamlit.web.bootstrap as bootstrap

    if not no_browser:
        url = f"http://localhost:{puerto}"
        print(f"Abriendo navegador: {url}")
        webbrowser.open(url)

    # Same pattern as the CLI: apply flag options before bootstrap.run so
    # they override the packaged .streamlit/config.toml (underscore keys).
    flag_options = {
        "server_port": puerto,
        "server_headless": True,
        "browser_gatherUsageStats": False,
        "global_developmentMode": False,
    }
    st_config._main_script_path = os.path.abspath(app_file)
    bootstrap.load_config_options(flag_options=flag_options)

    try:
        bootstrap.run(app_file, False, [], flag_options)
    except KeyboardInterrupt:
        print("\nPresupuestador detenido.")


def _wait_for_port(puerto, timeout_s=20.0):
    """Block until something listens on the port, or the timeout expires."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if puerto_en_uso(puerto):
            return True
        time.sleep(0.25)
    return False


def main_window(puerto, app_file):
    """Native window mode: streamlit in a background thread + pywebview window.

    Returns False when pywebview is not installed so the caller can fall
    back to the browser modes. Never returns True in practice: closing the
    window exits the process.
    """
    try:
        import webview
    except ImportError:
        # ASCII-only message: some Windows consoles (cp1252) cannot encode
        # emoji and would crash this fallback path with UnicodeEncodeError.
        print("[ERROR] pywebview is not installed (pip install pywebview).")
        print("        Falling back to browser mode.")
        return False

    import streamlit.web.bootstrap as bootstrap

    def _run_streamlit():
        # Mirror what `streamlit run` does in cli._main_run:
        # 1. set the main script path so the project's .streamlit/config.toml
        #    is located correctly,
        # 2. apply flag_options BEFORE bootstrap.run (bootstrap only re-applies
        #    them on config file changes, not at startup).
        # Flag keys MUST be CLI-flag style (underscores): streamlit converts
        # them via name.replace("_", ".") and they then override config.toml.
        flag_options = {
            "server_port": puerto,
            "server_headless": True,
            "browser_gatherUsageStats": False,
            # Required in frozen builds: streamlit may auto-enable dev mode
            # there, and server.port conflicts with it (RuntimeError).
            "global_developmentMode": False,
        }
        import streamlit.config as st_config
        st_config._main_script_path = os.path.abspath(app_file)
        bootstrap.load_config_options(flag_options=flag_options)
        # bootstrap.run installs SIGTERM/SIGINT handlers, which are only
        # allowed in the main thread. Neutralize signal.signal inside this
        # worker thread and restore it right after bootstrap.run returns.
        import signal
        original_signal = signal.signal
        signal.signal = lambda *a, **k: None
        try:
            bootstrap.run(app_file, False, [], flag_options)
        finally:
            signal.signal = original_signal

    hilo = threading.Thread(target=_run_streamlit, daemon=True)
    hilo.start()

    url = f"http://localhost:{puerto}"
    _wait_for_port(puerto)
    print(f"Opening native window: {url}")

    webview.create_window(
        "Presupuestador Sage 50",
        url,
        width=1400,
        height=900,
        confirm_close=True,
    )
    webview.start()

    # The streamlit server runs in a daemon thread, so exit the whole
    # process once the user closes the window.
    os._exit(0)


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
    parser.add_argument(
        "--window", action="store_true",
        help="Abrir en ventana nativa (pywebview) en lugar del navegador",
    )
    args = parser.parse_args()

    puerto = resolver_puerto(args.port)
    app_dir = _base_dir()
    app_file = os.path.join(app_dir, f"{APP_MODULE}.py")

    print(f"Presupuestador Sage 50 arrancando en http://localhost:{puerto}")

    frozen = getattr(sys, "frozen", False)

    # In the frozen executable the native window is the default mode
    # (unless the browser was explicitly disabled).
    usar_ventana = args.window or (frozen and not args.no_browser)

    if usar_ventana and main_window(puerto, app_file):
        # Unreachable in practice: main_window exits the process after
        # webview.start() returns.
        return

    if frozen:
        main_frozen(puerto, app_file, args.no_browser)
    else:
        main_subprocess(puerto, app_file, app_dir, args.no_browser)


if __name__ == "__main__":
    main()
