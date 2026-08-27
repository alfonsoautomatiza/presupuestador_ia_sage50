"""Tests for the pure modules extracted from the Streamlit UI."""

import os

from models import resolver_periodicidad_referencia
from tariff_parser import normalizar_ruta_usuario


def _producto(periodicidades):
    return {"periodicidades": periodicidades}


# ── resolver_periodicidad_referencia ────────────────────────────

def test_resolver_filtro_tiene_prioridad_sobre_orden_global():
    # "Anual" ranks first globally, but the filter asks for "Mensual"
    producto = _producto("Anual, Mensual")
    assert resolver_periodicidad_referencia(producto, ["Mensual"]) == "Mensual"


def test_resolver_respeta_orden_de_prioridad_dentro_del_filtro():
    # PERIODICIDAD_PRIORIDAD = Anual, Mensual, Bianual, Trienal, Puntual
    producto = _producto("Bianual, Mensual")
    assert resolver_periodicidad_referencia(producto, ["Bianual", "Mensual"]) == "Mensual"


def test_resolver_sin_filtro_devuelve_primera_del_producto():
    producto = _producto("Trienal, Bianual")
    assert resolver_periodicidad_referencia(producto, []) == "Bianual"


def test_resolver_filtro_sin_interseccion_cae_en_puntual():
    producto = _producto("Puntual, Trienal")
    assert resolver_periodicidad_referencia(producto, ["Mensual"]) == "Puntual"


def test_resolver_filtro_sin_interseccion_sin_puntual_usa_producto():
    # Filter does not intersect the product and there is no "Puntual":
    # fall back to the product's own highest-priority periodicity
    producto = _producto("Trienal")
    assert resolver_periodicidad_referencia(producto, ["Mensual"]) == "Trienal"


def test_resolver_sin_periodicidades_devuelve_anual_por_defecto():
    assert resolver_periodicidad_referencia(_producto(""), []) == "Anual"


# ── normalizar_ruta_usuario ─────────────────────────────────────

def test_normalizar_convierte_ruta_windows_en_wsl(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")
    assert normalizar_ruta_usuario("C:\\sage50\\tarifa.xlsm") == "/mnt/c/sage50/tarifa.xlsm"


def test_normalizar_acepta_barra_normal_en_wsl(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")
    assert normalizar_ruta_usuario("D:/datos/tarifa.xlsx") == "/mnt/d/datos/tarifa.xlsx"


def test_normalizar_es_identidad_en_windows(monkeypatch):
    monkeypatch.setattr(os, "name", "nt")
    ruta = "C:\\sage50\\tarifa.xlsm"
    assert normalizar_ruta_usuario(ruta) == ruta


def test_normalizar_recorta_espacios_y_comillas(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")
    assert normalizar_ruta_usuario('  "C:\\sage50\\tarifa.xlsm" ') == "/mnt/c/sage50/tarifa.xlsm"
