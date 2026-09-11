"""Pure business logic for the Presupuestador Sage 50."""

PERIODICIDAD_LABELS = {"Mensual": "mensual", "Anual": "anual", "Bianual": "bianual", "Trienal": "trienal", "Puntual": "ssrs"}
PERIODICIDADES_FILTRABLES = {"Anual", "Mensual", "Bianual", "Trienal"}
PERIODICIDAD_PRIORIDAD = ["Anual", "Mensual", "Bianual", "Trienal", "Puntual"]
PLAN_LABELS = {"Standard": "standard", "Extra": "extra", "Complete": "complete", "Sin Nivel": "sin_ns", "Puntual": "ssrs"}
__all__ = ["PERIODICIDADES_FILTRABLES", "PERIODICIDAD_LABELS", "PERIODICIDAD_PRIORIDAD", "PLAN_LABELS", "calcular_dto", "csv_a_set", "cumple_filtro_periodicidad", "obtener_precio", "resolver_periodicidad_referencia", "precio_referencia_por_periodicidad", "agrupar_lineas", "subtotal_grupo"]


def obtener_precio(producto, plan, periodicidad):
    precios = producto["_precios"]
    if periodicidad == "Puntual":
        return precios.get("ssrs", 0)
    periodo_key = PERIODICIDAD_LABELS.get(periodicidad, "anual")
    clave = f"{PLAN_LABELS.get(plan, 'sin_ns')}_{periodo_key}"
    return precios.get(clave, precios.get(f"sin_ns_{periodo_key}", 0))


def calcular_dto(precio, dto_partner, dto_tech_bp, dto_pam):
    neto = precio
    for descuento in (dto_partner, dto_tech_bp, dto_pam):
        if descuento > 0:
            neto *= 1 - descuento
    return round(neto, 2)


def csv_a_set(valor):
    return {item.strip() for item in valor.split(",") if item.strip()}


def cumple_filtro_periodicidad(producto, filtro_periodicidad):
    if not filtro_periodicidad:
        return True
    periodicidades = csv_a_set(producto["periodicidades"])
    if "Puntual" in periodicidades:
        return True
    aplicable = {p for p in filtro_periodicidad if p in PERIODICIDADES_FILTRABLES}
    return not aplicable or bool(periodicidades & aplicable)


def resolver_periodicidad_referencia(producto, filtro_periodicidad):
    periodicidades = csv_a_set(producto["periodicidades"])
    filtro = set(filtro_periodicidad or [])
    for periodicidad in PERIODICIDAD_PRIORIDAD:
        if periodicidad in filtro and periodicidad in periodicidades:
            return periodicidad
    if "Puntual" in periodicidades and filtro:
        return "Puntual"
    for periodicidad in PERIODICIDAD_PRIORIDAD:
        if periodicidad in periodicidades:
            return periodicidad
    return "Anual"


def agrupar_lineas(lineas, criterio):
    """Group quote lines by plan or periodicity, preserving first appearance."""
    if criterio not in {"plan", "periodicidad"}:
        return [(None, lineas)]
    grupos = {}
    for linea in lineas:
        grupo = linea.get(criterio)
        grupos.setdefault(grupo, []).append(linea)
    return list(grupos.items())


def subtotal_grupo(lineas):
    """Return a rounded subtotal for a group of quote lines."""
    return round(sum(linea.get("total", 0) for linea in lineas), 2)


def precio_referencia_por_periodicidad(producto, periodicidad):
    precios = producto["_precios"]
    if periodicidad == "Puntual":
        try:
            return float(precios.get("ssrs", 0) or 0)
        except (TypeError, ValueError):
            return 0.0
    periodo_key = PERIODICIDAD_LABELS.get(periodicidad)
    if not periodo_key:
        return 0.0
    candidatos = []
    for clave, valor in precios.items():
        if clave.endswith(f"_{periodo_key}") and valor is not None:
            try:
                candidatos.append(float(valor))
            except (TypeError, ValueError):
                continue
    return min(candidatos) if candidatos else 0.0
