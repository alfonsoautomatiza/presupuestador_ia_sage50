"""Tests for the pure modules extracted from the Streamlit UI."""

import os

from models import agrupar_lineas, resolver_periodicidad_referencia, subtotal_grupo  # pyright: ignore[reportAttributeAccessIssue]
from tariff_parser import normalizar_ruta_usuario


def _producto(periodicidades):
    return {"periodicidades": periodicidades}


def test_resolver_filtro_tiene_prioridad_sobre_orden_global():
    producto = _producto("Anual, Mensual")
    assert resolver_periodicidad_referencia(producto, ["Mensual"]) == "Mensual"


def test_resolver_respeta_orden_de_prioridad_dentro_del_filtro():
    producto = _producto("Bianual, Mensual")
    assert resolver_periodicidad_referencia(producto, ["Bianual", "Mensual"]) == "Mensual"


def test_resolver_sin_filtro_devuelve_primera_del_producto():
    assert resolver_periodicidad_referencia(_producto("Trienal, Bianual"), []) == "Bianual"


def test_resolver_filtro_sin_interseccion_cae_en_puntual():
    assert resolver_periodicidad_referencia(_producto("Puntual, Trienal"), ["Mensual"]) == "Puntual"


def test_resolver_filtro_sin_interseccion_sin_puntual_usa_producto():
    assert resolver_periodicidad_referencia(_producto("Trienal"), ["Mensual"]) == "Trienal"


def test_resolver_sin_periodicidades_devuelve_anual_por_defecto():
    assert resolver_periodicidad_referencia(_producto(""), []) == "Anual"


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


def test_agrupar_lineas_preserva_orden_y_subtotales():
    lineas = [
        {"plan": "A", "periodicidad": "M", "total": 1.111},
        {"plan": "B", "periodicidad": "A", "total": 2.225},
        {"plan": "A", "periodicidad": "M", "total": 3},
    ]
    grupos = agrupar_lineas(lineas, "plan")
    assert [grupo for grupo, _ in grupos] == ["A", "B"]
    assert [linea["total"] for linea in grupos[0][1]] == [1.111, 3]
    assert subtotal_grupo(grupos[0][1]) == 4.11


def test_agrupar_lineas_none_unknown_and_single_group():
    lineas = [{"plan": "A", "total": 1}, {"plan": "A", "total": 2}]
    assert agrupar_lineas(lineas, None) == [(None, lineas)]
    assert agrupar_lineas(lineas, "otro") == [(None, lineas)]
    assert agrupar_lineas(lineas, "plan") == [("A", lineas)]
