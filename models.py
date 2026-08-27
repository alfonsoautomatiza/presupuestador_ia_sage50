"""
Pure business logic for the Presupuestador Sage 50
==================================================
Price, discount, and filter logic with no UI dependencies.
Extracted from presupuestador.py so it can be tested and reused.

Autor: ALCA TIC S.L.
"""

PERIODICIDAD_LABELS = {
    "Mensual": "mensual",
    "Anual": "anual",
    "Bianual": "bianual",
    "Trienal": "trienal",
    "Puntual": "ssrs",
}

PERIODICIDADES_FILTRABLES = {"Anual", "Mensual", "Bianual", "Trienal"}
PERIODICIDAD_PRIORIDAD = ["Anual", "Mensual", "Bianual", "Trienal", "Puntual"]

PLAN_LABELS = {
    "Standard": "standard",
    "Extra": "extra",
    "Complete": "complete",
    "Sin Nivel": "sin_ns",
    "Puntual": "ssrs",
}


def obtener_precio(producto, plan, periodicidad):
    """Devuelve el precio unitario según plan y periodicidad seleccionados."""
    precios = producto["_precios"]

    if periodicidad == "Puntual":
        return precios.get("ssrs", 0)

    plan_key = PLAN_LABELS.get(plan, "sin_ns")
    periodo_key = PERIODICIDAD_LABELS.get(periodicidad, "anual")

    # Intentar precio con plan + periodo
    clave = f"{plan_key}_{periodo_key}"
    if clave in precios:
        return precios[clave]

    # Fallback: sin nivel de servicio
    clave_sin = f"sin_ns_{periodo_key}"
    if clave_sin in precios:
        return precios[clave_sin]

    return 0


def calcular_dto(precio, dto_partner, dto_tech_bp, dto_pam):
    """Aplica descuentos en cascada."""
    neto = precio
    if dto_partner > 0:
        neto = neto * (1 - dto_partner)
    if dto_tech_bp > 0:
        neto = neto * (1 - dto_tech_bp)
    if dto_pam > 0:
        neto = neto * (1 - dto_pam)
    return round(neto, 2)


def csv_a_set(valor):
    return {item.strip() for item in valor.split(",") if item.strip()}


def cumple_filtro_periodicidad(producto, filtro_periodicidad):
    if not filtro_periodicidad:
        return True

    periodicidades_producto = csv_a_set(producto["periodicidades"])
    if "Puntual" in periodicidades_producto:
        return True

    filtro_aplicable = {p for p in filtro_periodicidad if p in PERIODICIDADES_FILTRABLES}
    if not filtro_aplicable:
        return True

    return bool(periodicidades_producto & filtro_aplicable)


def resolver_periodicidad_referencia(producto, filtro_periodicidad):
    periodicidades_producto = csv_a_set(producto["periodicidades"])
    filtro_set = set(filtro_periodicidad or [])

    for periodicidad in PERIODICIDAD_PRIORIDAD:
        if periodicidad in filtro_set and periodicidad in periodicidades_producto:
            return periodicidad

    if "Puntual" in periodicidades_producto and filtro_set:
        return "Puntual"

    for periodicidad in PERIODICIDAD_PRIORIDAD:
        if periodicidad in periodicidades_producto:
            return periodicidad

    return "Anual"


def precio_referencia_por_periodicidad(producto, periodicidad):
    precios = producto["_precios"]

    if periodicidad == "Puntual":
        return float(precios.get("ssrs", 0) or 0)

    periodo_key = PERIODICIDAD_LABELS.get(periodicidad)
    if not periodo_key:
        return 0.0

    candidatos = [
        float(valor)
        for clave, valor in precios.items()
        if clave.endswith(f"_{periodo_key}") and valor is not None
    ]
    return min(candidatos) if candidatos else 0.0
