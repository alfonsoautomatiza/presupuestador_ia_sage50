"""Compatibility and business exports for psage.

The presentation layer lives in :mod:`gradio_app`; this module remains a stable
import location for callers and tests that use the domain helpers.
"""
from models import *  # noqa: F401,F403
from tariff_parser import (
    APP_DIR, BACKUP_DIR, DATA_DIR, DATA_JSON, HOJA_TARIFA_PROCESOS, ORIGINALES_DIR,
    PDF_DIR, cargar_productos, guardar_ultima_tarifa, init_dirs, leer_ultima_tarifa,
    normalizar_ruta_usuario, procesar_tarifa,
)
from pdf_generator import generar_pdf
from excel_generator import generar_excel
from json_generator import generar_json
from templates import borrar_plantilla, cargar_plantilla, guardar_plantilla, listar_plantillas


def main():
    from importlib import import_module
    import_module("gradio_app").launch_app(8599)


if __name__ == "__main__":
    main()
