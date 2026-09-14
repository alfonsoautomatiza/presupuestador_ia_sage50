"""psage command-line and frozen application launcher."""
import argparse
import os
import socket
import sys
import threading
import time
import webbrowser

# Import for PyInstaller detection (frozen apps only)
if getattr(sys, "frozen", False):
    import gradio_app as _gradio_app_frozen

DEFAULT_PORT = 8599


def puerto_en_uso(puerto: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", puerto)) == 0


def buscar_puerto_libre(desde: int = 8600, hasta: int = 9000) -> int:
    for puerto in range(desde, hasta):
        if not puerto_en_uso(puerto):
            return puerto
    raise RuntimeError(f"No se encontró puerto libre en el rango {desde}-{hasta}")


def resolver_puerto(cli_port=None):
    if cli_port:
        return cli_port
    if puerto_en_uso(DEFAULT_PORT):
        puerto = buscar_puerto_libre()
        print(f"⚠️  Puerto {DEFAULT_PORT} en uso → usando puerto {puerto}")
        return puerto
    return DEFAULT_PORT


def _wait_for_port(puerto, timeout_s=20.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if puerto_en_uso(puerto):
            return True
        time.sleep(0.25)
    return False


def _serve_gradio(puerto, inbrowser=False, prevent_thread_lock=False):
    from importlib import import_module
    # En hilo secundario (modo ventana del exe) no hay event loop: Gradio crea
    # los locks de su cola como None (safe_get_lock) y la app revienta al
    # entrar en la cola. Aseguramos loop antes de construir Blocks.
    import asyncio
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    build_app = import_module("gradio_app").build_app
    return build_app().launch(server_name="127.0.0.1", server_port=puerto, inbrowser=inbrowser, prevent_thread_lock=prevent_thread_lock)


def main_window(puerto):
    """Serve Gradio in the background and display it in a native pywebview window."""
    try:
        import webview
    except ImportError:
        print("[ERROR] pywebview no está instalado. Se usará el navegador.")
        return False

    threading.Thread(target=_serve_gradio, args=(puerto, False, True), daemon=True).start()
    url = f"http://127.0.0.1:{puerto}"
    if not _wait_for_port(puerto):
        print("[ERROR] Gradio no inició a tiempo.")
        return False
    print(f"Opening native window: {url}")
    webview.create_window("Presupuestador Sage 50", url, width=1400, height=900, confirm_close=True)
    webview.start()
    return True


def main():
    parser = argparse.ArgumentParser(description="Presupuestador Sage 50 — interfaz Gradio")
    parser.add_argument("--port", type=int, default=None, help=f"Puerto para Gradio (defecto: {DEFAULT_PORT}, auto-si-ocupado)")
    parser.add_argument("--no-browser", action="store_true", help="No abrir el navegador automáticamente")
    parser.add_argument("--window", action="store_true", help="Abrir en ventana nativa (pywebview)")
    args = parser.parse_args()
    puerto = resolver_puerto(args.port)
    print(f"Presupuestador Sage 50 arrancando en http://localhost:{puerto}")
    frozen = getattr(sys, "frozen", False)
    usar_ventana = args.window or (frozen and not args.no_browser)
    if usar_ventana and main_window(puerto):
        return
    # One process is used in source and frozen modes alike; this avoids a
    # subprocess that cannot locate the bundled Gradio application.
    _serve_gradio(puerto, inbrowser=not args.no_browser, prevent_thread_lock=False)


if __name__ == "__main__":
    main()
