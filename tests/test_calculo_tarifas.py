"""Tests del cálculo de precios y descuentos de presupuestador.py."""

import pytest

from presupuestador import (
    obtener_precio,
    calcular_dto,
    cumple_filtro_periodicidad,
    precio_referencia_por_periodicidad,
    csv_a_set,
)


def _producto(precios, periodicidades="Anual, Mensual"):
    return {
        "_precios": precios,
        "periodicidades": periodicidades,
    }


# ── obtener_precio ──────────────────────────────────────────────

def test_obtener_precio_plan_y_periodo_exactos():
    producto = _producto({"complete_anual": 949.0, "standard_anual": 499.0})
    assert obtener_precio(producto, "Complete", "Anual") == 949.0


def test_obtener_precio_fallback_sin_nivel_servicio():
    producto = _producto({"sin_ns_mensual": 45.0})
    assert obtener_precio(producto, "Standard", "Mensual") == 45.0


def test_obtener_precio_periodicidad_puntual_usa_ssrs():
    producto = _producto({"ssrs": 120.0, "complete_anual": 949.0})
    assert obtener_precio(producto, "Complete", "Puntual") == 120.0


def test_obtener_precio_sin_coincidencia_devuelve_cero():
    producto = _producto({"complete_anual": 949.0})
    assert obtener_precio(producto, "Extra", "Trienal") == 0


# ── calcular_dto ────────────────────────────────────────────────

def test_calcular_dto_sin_descuentos():
    assert calcular_dto(100.0, 0, 0, 0) == 100.0


def test_calcular_dto_un_solo_descuento():
    assert calcular_dto(100.0, 0.1, 0, 0) == 90.0


def test_calcular_dto_descuentos_en_cascada():
    # 100 -> -10% -> 90 -> -5% -> 85.5 -> -2% -> 83.79
    resultado = calcular_dto(100.0, 0.10, 0.05, 0.02)
    assert resultado == 83.79


def test_calcular_dto_redondea_a_dos_decimales():
    resultado = calcular_dto(33.333, 0.1, 0, 0)
    assert resultado == round(33.333 * 0.9, 2)


# ── cumple_filtro_periodicidad ──────────────────────────────────

def test_cumple_filtro_periodicidad_sin_filtro_pasa_todo():
    producto = {"periodicidades": "Anual, Mensual"}
    assert cumple_filtro_periodicidad(producto, []) is True


def test_cumple_filtro_periodicidad_coincide():
    producto = {"periodicidades": "Anual, Mensual"}
    assert cumple_filtro_periodicidad(producto, ["Anual"]) is True


def test_cumple_filtro_periodicidad_no_coincide():
    producto = {"periodicidades": "Trienal"}
    assert cumple_filtro_periodicidad(producto, ["Mensual"]) is False


def test_cumple_filtro_periodicidad_puntual_siempre_pasa():
    producto = {"periodicidades": "Puntual"}
    assert cumple_filtro_periodicidad(producto, ["Mensual"]) is True


# ── precio_referencia_por_periodicidad ──────────────────────────

def test_precio_referencia_toma_el_minimo_del_periodo():
    producto = _producto({
        "standard_anual": 499.0,
        "extra_anual": 739.0,
        "complete_anual": 949.0,
    })
    assert precio_referencia_por_periodicidad(producto, "Anual") == 499.0


def test_precio_referencia_puntual_usa_ssrs():
    producto = _producto({"ssrs": 120.0})
    assert precio_referencia_por_periodicidad(producto, "Puntual") == 120.0


def test_precio_referencia_sin_candidatos_es_cero():
    producto = _producto({"complete_anual": 949.0})
    assert precio_referencia_por_periodicidad(producto, "Trienal") == 0.0


# ── csv_a_set ────────────────────────────────────────────────────

def test_csv_a_set_recorta_espacios_y_descarta_vacios():
    assert csv_a_set("Anual,  Mensual ,, Trienal") == {"Anual", "Mensual", "Trienal"}
