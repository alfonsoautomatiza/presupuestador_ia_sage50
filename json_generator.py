"""Strict, versioned JSON export for quote ingestion and calculations."""

import copy
import datetime
import json
import os
import re
import tempfile
from pathlib import Path

from models import agrupar_lineas, subtotal_grupo

_SCHEMA = "tarifas-sage50/oferta/v1"
_FILENAME = re.compile(r"[^A-Za-z0-9_.-]+")


def _timestamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _client_data(datos_cliente):
    cliente = copy.deepcopy(datos_cliente or {})
    if "condiciones_pago" not in cliente:
        cliente["condiciones_pago"] = cliente.get("condiciones", "")
    for key in ("empresa", "cif", "contacto", "email", "condiciones_pago"):
        cliente.setdefault(key, "")
    return cliente


def _tariff_data(tarifa):
    if isinstance(tarifa, dict):
        return {"nombre": tarifa.get("nombre", "")}
    return {"nombre": tarifa or ""}


def construir_oferta_json(
    datos_cliente,
    lineas,
    totales,
    notas="",
    agrupacion=None,
    tarifa=None,
    generado_en=None,
):
    """Build a detached, versioned quote representation without mutating inputs."""
    copied_lines = copy.deepcopy(lineas)
    numbered_lines = []
    for number, linea in enumerate(copied_lines, start=1):
        numbered = {**linea, "numero": number}
        numbered_lines.append(numbered)

    subtotales = []
    if agrupacion in {"plan", "periodicidad"}:
        for grupo, lineas_grupo in agrupar_lineas(copied_lines, agrupacion):
            subtotales.append({"criterio": agrupacion, "grupo": grupo, "subtotal": subtotal_grupo(lineas_grupo)})

    return {
        "schema": _SCHEMA,
        "generado_en": generado_en or _timestamp(),
        "moneda": "EUR",
        "tarifa": _tariff_data(tarifa),
        "cliente": _client_data(datos_cliente),
        "notas": notas,
        "agrupacion": agrupacion if agrupacion in {"plan", "periodicidad"} else None,
        "lineas": numbered_lines,
        "subtotales_grupo": subtotales,
        "totales": {
            "subtotal": totales["subtotal"],
            "iva_pct": totales["iva_pct"],
            "iva": totales["iva"],
            "total_con_iva": totales["total"],
        },
    }


def _safe_filename():
    date = datetime.datetime.now().strftime("%Y%m%d")
    return f"presupuesto_{date}.json"


def generar_json(
    datos_cliente,
    lineas,
    totales,
    salida_dir,
    notas="",
    agrupacion=None,
    tarifa=None,
    generado_en=None,
):
    """Persist a quote atomically and return its path."""
    output_dir = Path(salida_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / _FILENAME.sub("_", _safe_filename())
    oferta = construir_oferta_json(datos_cliente, lineas, totales, notas, agrupacion, tarifa, generado_en)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output_dir, prefix=".", suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(oferta, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except Exception:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
        raise
    return str(destination)
