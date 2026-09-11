"""Tests for strict quote JSON export."""

import datetime
import json
import math

import pytest

from json_generator import construir_oferta_json, generar_json


@pytest.fixture
def quote_data():
    return (
        {
            "empresa": "Ñandú S.L.",
            "cif": "B12345678",
            "contacto": "Ana",
            "email": "ana@example.test",
            "condiciones": "Pago a 30 días",
            "validez": "30 días",
        },
        [
            {
                "codigo": "A-1",
                "descripcion": "Servicio ágil",
                "plan": "Complete",
                "periodicidad": "Anual",
                "cantidad": 2,
                "precio_tarifa": 100.0,
                "precio_unitario": 90.0,
                "dto_total_pct": 0.1,
                "total": 180.0,
                "campo_extra": "conservado",
            },
            {
                "codigo": "B-2",
                "descripcion": "Soporte",
                "plan": "Standard",
                "periodicidad": "Mensual",
                "cantidad": 1,
                "precio_unitario": 20.5,
                "total": 20.5,
            },
        ],
        {"subtotal": 200.5, "iva_pct": 0.21, "iva": 42.105, "total": 242.605},
    )


def test_schema_keys_and_deterministic_timestamp(quote_data):
    oferta = construir_oferta_json(*quote_data, agrupacion="plan", tarifa={"nombre": "demo.xlsx"}, generado_en="2026-01-02T03:04:05Z")
    assert list(oferta) == ["schema", "generado_en", "moneda", "tarifa", "cliente", "notas", "agrupacion", "lineas", "subtotales_grupo", "totales"]
    assert oferta["schema"] == "tarifas-sage50/oferta/v1"
    assert oferta["generado_en"] == "2026-01-02T03:04:05Z"
    assert oferta["moneda"] == "EUR"
    assert oferta["tarifa"] == {"nombre": "demo.xlsx"}


def test_preserves_client_and_line_fields_without_mutating(quote_data):
    cliente, lineas, totales = quote_data
    original_cliente = cliente.copy()
    original_lineas = [linea.copy() for linea in lineas]
    oferta = construir_oferta_json(cliente, lineas, totales, generado_en="2026-01-01T00:00:00Z")
    assert oferta["cliente"]["empresa"] == cliente["empresa"]
    assert oferta["cliente"]["condiciones_pago"] == cliente["condiciones"]
    assert oferta["cliente"]["validez"] == cliente["validez"]
    assert oferta["lineas"][0]["campo_extra"] == "conservado"
    assert [linea["numero"] for linea in oferta["lineas"]] == [1, 2]
    assert cliente == original_cliente
    assert lineas == original_lineas
    assert oferta["lineas"] is not lineas


def test_totals_and_group_subtotals_are_exact_and_ordered(quote_data):
    oferta = construir_oferta_json(*quote_data, agrupacion="plan", generado_en="2026-01-01T00:00:00Z")
    assert oferta["totales"] == {"subtotal": 200.5, "iva_pct": 0.21, "iva": 42.105, "total_con_iva": 242.605}
    assert oferta["subtotales_grupo"] == [
        {"criterio": "plan", "grupo": "Complete", "subtotal": 180.0},
        {"criterio": "plan", "grupo": "Standard", "subtotal": 20.5},
    ]
    periodicidad = construir_oferta_json(*quote_data, agrupacion="periodicidad", generado_en="2026-01-01T00:00:00Z")
    assert [item["grupo"] for item in periodicidad["subtotales_grupo"]] == ["Anual", "Mensual"]
    assert construir_oferta_json(*quote_data, generado_en="2026-01-01T00:00:00Z")["subtotales_grupo"] == []


def test_persisted_json_is_utf8_strict_and_filename_is_usable(tmp_path, quote_data):
    path = generar_json(*quote_data, salida_dir=tmp_path, generado_en="2026-01-01T00:00:00Z")
    assert path.endswith(".json")
    assert ".." not in path.split("/")[-1]
    raw = open(path, encoding="utf-8").read()
    assert "Ñandú" in raw
    assert json.loads(raw)["schema"] == "tarifas-sage50/oferta/v1"


def test_nan_does_not_replace_existing_destination_or_leave_temp(tmp_path, quote_data):
    destination = tmp_path / f"presupuesto_{datetime.datetime.now().strftime('%Y%m%d')}.json"
    destination.write_text("old", encoding="utf-8")
    bad_totals = {**quote_data[2], "subtotal": math.nan}
    with pytest.raises(ValueError):
        generar_json(*quote_data[:2], bad_totals, salida_dir=tmp_path, generado_en="2026-01-01T00:00:00Z")
    assert destination.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.glob(".*.tmp")) == []
