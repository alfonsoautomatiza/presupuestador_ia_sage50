"""Gradio presentation layer for psage.

The callbacks in this module are deliberately thin: tariff parsing, pricing,
template persistence, and export formats remain owned by the business modules.
"""
from __future__ import annotations

import datetime
import glob
import html
import os
from typing import Any

from importlib import import_module

# Imported dynamically so the business/CLI modules remain importable in minimal
# environments; the packaged application declares Gradio as a dependency.
gr = import_module("gradio")
import pandas as pd

from excel_generator import generar_excel
from json_generator import generar_json
from models import (
    PERIODICIDADES_FILTRABLES,
    agrupar_lineas,
    calcular_dto,
    csv_a_set,
    cumple_filtro_periodicidad,
    obtener_precio,
    precio_referencia_por_periodicidad,
    resolver_periodicidad_referencia,
    subtotal_grupo,
)
from pdf_generator import generar_pdf
from tariff_parser import (
    APP_DIR,
    DATA_DIR,
    DATA_JSON,
    HOJA_TARIFA_PROCESOS,
    ORIGINALES_DIR,
    PDF_DIR,
    cargar_productos,
    guardar_ultima_tarifa,
    init_dirs,
    leer_ultima_tarifa,
    procesar_tarifa,
)
from templates import borrar_plantilla, cargar_plantilla, guardar_plantilla, listar_plantillas

TEMPLATE_PATH = os.path.join(DATA_DIR, "plantillas.json")


def initial_state() -> tuple[list, dict, str, str | None, list, dict, dict]:
    """Return isolated values for the app's explicit Gradio state objects."""
    ultima = leer_ultima_tarifa()
    return [], {}, "", None, cargar_productos(), ultima, {}


def calcular_totales(lineas: list[dict], iva_pct: float = 0.21) -> dict:
    try:
        subtotal = round(sum(float(linea.get("total", 0)) for linea in lineas), 2)
    except (TypeError, ValueError):
        subtotal = 0.0
    iva = round(subtotal * iva_pct, 2)
    return {"subtotal": subtotal, "iva_pct": iva_pct, "iva": iva, "total": round(subtotal + iva, 2)}


def filtrar_productos(productos: list[dict], planes=None, periodicidades=None, modulos=None, sabores=None, plataformas=None, texto="") -> list[dict]:
    """Filter products without changing their tariff representation."""
    result = list(productos or [])
    if planes:
        result = [p for p in result if csv_a_set(p["planes"]) & set(planes)]
    if periodicidades:
        result = [p for p in result if cumple_filtro_periodicidad(p, periodicidades)]
    if modulos:
        result = [p for p in result if p["modulo"] in modulos]
    if sabores:
        result = [p for p in result if p["sabor"] in sabores]
    if plataformas:
        result = [p for p in result if p["plataforma"] in plataformas]
    if texto:
        needle = texto.lower()
        result = [p for p in result if needle in p["descripcion"].lower() or needle in p["codigo"].lower()]
    return result


def select_all_filter_values(products: list[dict]) -> dict:
    """Collect every catalog filter option for the bulk-select button."""
    return {
        "plans": sorted({x for p in products for x in csv_a_set(p["planes"])}),
        "periodicidades": sorted({x for p in products for x in csv_a_set(p["periodicidades"])}),
        "sabores": sorted({p["sabor"] for p in products if p["sabor"]}),
        "plataformas": sorted({p["plataforma"] for p in products if p["plataforma"]}),
    }


def normalize_lineas(lineas: list[dict] | None) -> list[dict]:
    """Return exporter/display-safe copies without changing valid values."""
    normalized = []
    for linea in lineas or []:
        item = dict(linea)
        for field in ("codigo", "descripcion", "plan", "periodicidad"):
            item[field] = "" if item.get(field) is None else str(item[field])
        for field, default in (("cantidad", 1), ("precio_unitario", 0), ("dto_total_pct", 0), ("precio_neto", 0), ("total", 0)):
            if item.get(field) is None:
                item[field] = default
        normalized.append(item)
    return normalized


def lineas_dataframe(lineas: list[dict], agrupacion: str | None = None) -> pd.DataFrame:
    rows = [{"Código": x.get("codigo", ""), "Descripción": x.get("descripcion", ""), "Plan": x.get("plan", ""), "Periodicidad": x.get("periodicidad", ""), "Cantidad": x.get("cantidad", 0), "Total": f"{x.get('total', 0):.2f} €"} for x in normalize_lineas(lineas)]
    return pd.DataFrame(rows, columns=pd.Index(["Código", "Descripción", "Plan", "Periodicidad", "Cantidad", "Total"]))


def _catalog_dataframe(productos):
    return pd.DataFrame([{"Código": p["codigo"], "Descripción": p["descripcion"], "Módulo": p["modulo"], "Sabor": p["sabor"], "Plataforma": p["plataforma"], "Tipo": p["tipo_articulo"], "Periodicidades": p["periodicidades"], "Planes": p["planes"], "Precio ref.": f"{precio_referencia_por_periodicidad(p, resolver_periodicidad_referencia(p, [])):.2f} €"} for p in productos])


def _safe_tariff_file(file_value):
    if not file_value:
        return None
    source = file_value if isinstance(file_value, str) else getattr(file_value, "name", None)
    if not source:
        return None
    init_dirs()
    destination = os.path.join(ORIGINALES_DIR, os.path.basename(source))
    if os.path.abspath(source) != os.path.abspath(destination):
        try:
            with open(source, "rb") as src, open(destination, "wb") as dst:
                dst.write(src.read())
        except OSError:
            return None
    return destination


def process_tariff(file_value, sheet_name):
    path = _safe_tariff_file(file_value)
    if not path:
        return "Seleccione un Excel de tarifas.", cargar_productos(), leer_ultima_tarifa()
    try:
        count, errors, extracted = procesar_tarifa(path, sheet_name or HOJA_TARIFA_PROCESOS)
        guardar_ultima_tarifa(os.path.basename(path), path)
        message = f"✅ {count} productos cargados ({errors} filas omitidas). Hoja extraída en {extracted}"
        return message, cargar_productos(), leer_ultima_tarifa()
    except (OSError, ValueError, KeyError) as error:
        return f"❌ {error}", cargar_productos(), leer_ultima_tarifa()


def add_line(producto, plan, periodicidad, cantidad, lineas):
    if not producto:
        return lineas or [], "Seleccione un producto."
    try:
        cantidad = max(1, int(cantidad or 1))
    except (TypeError, ValueError):
        cantidad = 1
    precio = obtener_precio(producto, plan, periodicidad)
    dto = 1 - (1 - producto["dto_partner"]) * (1 - producto["dto_tech_bp"]) * (1 - producto["dto_pam"])
    neto = calcular_dto(precio, producto["dto_partner"], producto["dto_tech_bp"], producto["dto_pam"])
    updated = list(lineas or []) + [{"codigo": producto["codigo"], "descripcion": producto["descripcion"], "plan": plan, "periodicidad": periodicidad, "cantidad": cantidad, "precio_unitario": precio, "dto_total_pct": dto, "precio_neto": neto, "total": round(neto * cantidad, 2)}]
    return updated, f"Añadido: {producto['descripcion']} x{cantidad}"


def _product_options(producto, field, fallback):
    values = [value.strip() for value in str(producto.get(field) or "").split(",") if value.strip()]
    return values or [fallback]


def add_product_lines(producto, plan, periodicidad, cantidad, lineas):
    if not producto:
        return lineas or [], "Seleccione un producto."
    plans = [plan] if plan else _product_options(producto, "planes", "Sin Nivel")
    periods = [periodicidad] if periodicidad else _product_options(producto, "periodicidades", "Anual")
    updated = list(lineas or [])
    added = 0
    for selected_plan in plans:
        for selected_period in periods:
            updated, _ = add_line(producto, selected_plan, selected_period, cantidad, updated)
            added += 1
    return updated, f"Añadidas {added} líneas de {producto.get('descripcion', '')}."


def delete_line(index, lineas):
    updated = list(lineas or [])
    try:
        parsed_index = int(index)
    except (TypeError, ValueError):
        parsed_index = -1
    if 0 <= parsed_index < len(updated):
        updated.pop(parsed_index)
    return updated


def render_budget_html(lineas: list[dict], agrupacion: str | None = None) -> str:
    """Render the budget with safe values and one delete action per line."""
    grouping_map = {"Ninguna": None, "Por plan": "plan", "Por periodo": "periodicidad"}
    criterio = grouping_map.get(agrupacion) if agrupacion is not None else None
    if agrupacion is not None and agrupacion not in grouping_map:
        criterio = agrupacion
    rows = []
    line_index = 0
    for group, items in agrupar_lineas(normalize_lineas(lineas), criterio):
        if group is not None:
            rows.append('<tr class="budget-group"><th colspan="7">{}</th></tr>'.format(html.escape(str(group))))
        for item in items:
            index = line_index
            line_index += 1
            try:
                total = float(item.get("total", 0) or 0)
            except (TypeError, ValueError):
                total = 0.0
            rows.append(
                '<tr><td><button type="button" class="budget-delete" data-line-index="{}">🗑️ Eliminar</button></td>'
                '<td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{:.2f} €</td></tr>'.format(
                    index, html.escape(item["codigo"]), html.escape(item["descripcion"]),
                    html.escape(item["plan"]), html.escape(item["periodicidad"]),
                    html.escape(str(item["cantidad"])), total,
                )
            )
    if not rows:
        return '<p class="budget-empty">No hay líneas en el presupuesto.</p>'
    return ('<table class="budget-table"><thead><tr><th>Acciones</th><th>Código</th><th>Descripción</th>'
            '<th>Plan</th><th>Periodicidad</th><th>Cantidad</th><th>Total</th>'
            '</tr></thead><tbody>{}</tbody></table>').format("".join(rows))


def refresh_budget(lineas, agrupacion, iva_pct, client_data=None, notes=""):
    criterio = {"Ninguna": None, "Por plan": "plan", "Por periodo": "periodicidad"}.get(agrupacion, agrupacion)
    try:
        rate = float(iva_pct or 21) / 100
    except (TypeError, ValueError):
        rate = 0.21
    totals = calcular_totales(lineas or [], rate)
    groups = [{"grupo": group, "subtotal": subtotal_grupo(items)} for group, items in agrupar_lineas(lineas or [], criterio) if group is not None]
    return lineas_dataframe(lineas or [], criterio), f"Subtotal: {totals['subtotal']:.2f} € | IVA: {totals['iva']:.2f} € | TOTAL: {totals['total']:.2f} €", groups, totals


APP_CSS = """
:root, body, .gradio-container {
    font-family: Inter, "Segoe UI", sans-serif !important;
}
button, input, textarea, select, label, table {
    font-family: inherit !important;
}
"""


BUDGET_DELETE_JS = """
() => {
    if (window.__budgetDeleteBridgeInstalled) return;
    window.__budgetDeleteBridgeInstalled = true;
    document.addEventListener("click", (event) => {
        const button = event.target.closest(".budget-delete");
        if (!button) return;
        const textbox = document.querySelector("#budget-delete-index input, #budget-delete-index textarea");
        const trigger = document.querySelector("#budget-delete-trigger button");
        if (!textbox || !trigger) return;
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
        if (setter) setter.call(textbox, button.dataset.lineIndex);
        textbox.dispatchEvent(new Event("input", {bubbles: true}));
        textbox.dispatchEvent(new Event("change", {bubbles: true}));
        trigger.click();
    });
}
"""


def build_app():
    init_dirs()
    lines, client, notes, grouping, products, tariff, artifacts = initial_state()
    with gr.Blocks(title="Presupuestador Sage 50", theme=gr.themes.Soft(), css=APP_CSS, js=BUDGET_DELETE_JS) as app:
        lines_state = gr.State(lines)
        client_state = gr.State(client)
        notes_state = gr.State(notes)
        grouping_state = gr.State(grouping)
        products_state = gr.State(products)
        tariff_state = gr.State(tariff)
        artifacts_state = gr.State(artifacts)
        gr.Markdown("# 📋 Presupuestador Sage 50\nGenerá presupuestos profesionales a partir de tarifas oficiales.")
        with gr.Row():
            with gr.Column(scale=1, min_width=280):
                gr.Markdown("## 📂 Tarifa y cliente")
                tariff_file = gr.File(label="Subir Excel de tarifas", file_types=[".xlsx", ".xlsm", ".xls"], type="filepath")
                sheet = gr.Textbox(label="Hoja", value=HOJA_TARIFA_PROCESOS)
                process = gr.Button("Procesar tarifa", variant="primary")
                tariff_status = gr.Markdown()
                company = gr.Textbox(label="Empresa")
                cif = gr.Textbox(label="CIF / NIF")
                contact = gr.Textbox(label="Persona de contacto")
                email = gr.Textbox(label="Email")
                validity = gr.Dropdown(["30 días", "15 días", "60 días", "90 días"], value="30 días", label="Validez")
                conditions = gr.Textbox(label="Condiciones de pago", value="Pago a 30 días")
                iva = gr.Number(label="IVA (%)", value=21, minimum=0, maximum=100)
            with gr.Column(scale=4):
                with gr.Tabs():
                    with gr.Tab("🗂️ Plantillas"):
                        template_name = gr.Textbox(label="Nombre de la plantilla")
                        template_select = gr.Dropdown(choices=listar_plantillas(TEMPLATE_PATH), label="Plantilla guardada")
                        with gr.Row():
                            save_template = gr.Button("💾 Guardar")
                            load_template = gr.Button("📂 Cargar")
                            delete_template = gr.Button("🗑️ Eliminar")
                        template_status = gr.Markdown()
                        notes = gr.Textbox(label="Observaciones", lines=5)
                    with gr.Tab("🔍 Catálogo"):
                        with gr.Row():
                            search = gr.Textbox(label="Buscar por nombre o código", scale=4)
                            mark_all = gr.Button("📌 Todo", variant="secondary", scale=1)
                        with gr.Row():
                            plan_filter = gr.CheckboxGroup(label="Plan / Nivel", choices=sorted({x for p in products for x in csv_a_set(p["planes"])}))
                            period_filter = gr.CheckboxGroup(label="Periodicidad", choices=sorted({x for p in products for x in csv_a_set(p["periodicidades"])}))
                        with gr.Row():
                            module_filter = gr.CheckboxGroup(label="Módulo", choices=sorted({p["modulo"] for p in products if p["modulo"]}))
                            flavor_filter = gr.CheckboxGroup(label="Sabor", choices=sorted({p["sabor"] for p in products if p["sabor"]}))
                        with gr.Row():
                            platform_filter = gr.CheckboxGroup(label="Plataforma", choices=sorted({p["plataforma"] for p in products if p["plataforma"]}))
                        catalog = gr.Dataframe(value=_catalog_dataframe(products), interactive=False, wrap=True)
                        add_filtered = gr.Button("➕ Añadir todos los filtrados al presupuesto", variant="secondary")
                        catalog_status = gr.Markdown()
                    with gr.Tab("📝 Presupuesto"):
                        gr.Markdown("### Añadir al presupuesto")
                        product = gr.Dropdown(label="Producto filtrado", choices=[f"{p['descripcion']} [{p['codigo']}]" for p in products])
                        with gr.Row():
                            product_plan = gr.Dropdown(label="Plan / Nivel")
                            product_period = gr.Dropdown(label="Periodicidad")
                            quantity = gr.Number(label="Cantidad", value=1, minimum=1, precision=0)
                        add = gr.Button("✅ Añadir al presupuesto", variant="primary")
                        budget_status = gr.Markdown()
                        grouping = gr.Dropdown(["Ninguna", "Por plan", "Por periodo"], value="Ninguna", label="Agrupar por")
                        line_index = gr.Textbox(label="Índice interno de eliminación", elem_id="budget-delete-index", visible=False)
                        delete = gr.Button("Eliminar línea seleccionada", elem_id="budget-delete-trigger", visible=False)
                        budget = gr.HTML(render_budget_html(lines, grouping), elem_id="budget-view")
                        totals = gr.Markdown()
                    with gr.Tab("📤 Exportar"):
                        with gr.Row():
                            pdf = gr.DownloadButton("📄 Generar PDF")
                            excel = gr.DownloadButton("📊 Generar Excel")
                            json_export = gr.DownloadButton("🤖 Generar JSON")
                        clear = gr.Button("🧹 Limpiar presupuesto")
                        export_status = gr.Markdown()

        client_inputs = [company, cif, contact, email, validity, conditions]
        process.click(process_tariff, [tariff_file, sheet], [tariff_status, products_state, tariff_state])
        for field in client_inputs:
            field.change(lambda *values: dict(zip(["empresa", "cif", "contacto", "email", "validez", "condiciones"], values)), client_inputs, client_state)
        notes.change(lambda value: value, notes, notes_state)
        grouping.change(lambda value: value, grouping, grouping_state)
        save_template.click(lambda name, lines, note: (guardar_plantilla(TEMPLATE_PATH, name.strip(), lines, note) if name and name.strip() else None, gr.update(choices=listar_plantillas(TEMPLATE_PATH)), "Plantilla guardada."), [template_name, lines_state, notes], [template_status, template_select, template_status])
        load_template.click(lambda name: ((cargar_plantilla(TEMPLATE_PATH, name) or {}).get("lineas", []), (cargar_plantilla(TEMPLATE_PATH, name) or {}).get("notas", ""), "Plantilla cargada."), template_select, [lines_state, notes, template_status]).then(refresh_budget, [lines_state, grouping, iva, client_state, notes_state], [budget, totals, gr.State([]), gr.State({})])
        delete_template.click(lambda name: (borrar_plantilla(TEMPLATE_PATH, name) if name else False, gr.update(choices=listar_plantillas(TEMPLATE_PATH)), "Plantilla eliminada."), template_select, [template_status, template_select, template_status])
        def update_catalog(text, plans, periods, modules, flavors, platforms, products):
            filtered = filtrar_productos(products, plans, periods, modules, flavors, platforms, text)
            labels = [f"{p['descripcion']} [{p['codigo']}]" for p in filtered]
            return _catalog_dataframe(filtered), gr.update(choices=labels, value=labels[0] if labels else None)
        catalog_filters = (search, plan_filter, period_filter, module_filter, flavor_filter, platform_filter)
        for component in catalog_filters:
            component.change(update_catalog, [search, plan_filter, period_filter, module_filter, flavor_filter, platform_filter, products_state], [catalog, product])
        def select_all_filters(products):
            values = select_all_filter_values(products)
            return (
                gr.update(value=values["plans"]),
                gr.update(value=values["periodicidades"]),
                gr.update(value=values["sabores"]),
                gr.update(value=values["plataformas"]),
            )

        mark_all.click(select_all_filters, [products_state], [plan_filter, period_filter, flavor_filter, platform_filter])

        def choose_product(label, products):
            found = next((p for p in products if f"{p['descripcion']} [{p['codigo']}]" == label), None)
            return gr.update(choices=[x.strip() for x in found["planes"].split(",") if x.strip()] if found else []), gr.update(choices=[x.strip() for x in found["periodicidades"].split(",") if x.strip()] if found else [])
        product.change(choose_product, [product, products_state], [product_plan, product_period])
        def add_selected(label, pl, pe, q, current, products, current_grouping, current_iva):
            selected = next((p for p in products if f"{p['descripcion']} [{p['codigo']}]" == label), None)
            updated, status = add_line(selected, pl, pe, q, current)
            view, summary, _, _ = refresh_budget(updated, current_grouping, current_iva)
            return updated, status, render_budget_html(updated, current_grouping), summary
        add.click(add_selected, [product, product_plan, product_period, quantity, lines_state, products_state, grouping, iva], [lines_state, budget_status, budget, totals])

        def add_all_filtered(plans, periods, modules, flavors, platforms, text, current, available, current_grouping, current_iva):
            filtered = filtrar_productos(available, plans, periods, modules, flavors, platforms, text)
            updated = list(current or [])
            for item in filtered:
                item_plans = [value for value in _product_options(item, "planes", "Sin Nivel") if not plans or value in plans]
                item_periods = [value for value in _product_options(item, "periodicidades", "Anual") if not periods or value in periods]
                for item_plan in item_plans:
                    for item_period in item_periods:
                        updated, _ = add_line(item, item_plan, item_period, 1, updated)
            added = len(updated) - len(current or [])
            _, summary, _, _ = refresh_budget(updated, current_grouping, current_iva)
            return updated, f"Añadidas {added} líneas filtradas.", render_budget_html(updated, current_grouping), summary

        add_filtered.click(
            add_all_filtered,
            [plan_filter, period_filter, module_filter, flavor_filter, platform_filter, search, lines_state, products_state, grouping, iva],
            [lines_state, catalog_status, budget, totals],
        )

        def delete_selected(index, current, current_grouping, current_iva):
            updated = delete_line(index, current)
            _, summary, _, _ = refresh_budget(updated, current_grouping, current_iva)
            return updated, render_budget_html(updated, current_grouping), summary

        delete.click(delete_selected, [line_index, lines_state, grouping, iva], [lines_state, budget, totals])
        grouping.change(lambda value, current: (render_budget_html(current, value),), [grouping, lines_state], [budget])
        def prepare_download(kind, lineas, cliente, notas, agrupacion):
            files, status = export_artifact(kind, lineas, cliente, notas, agrupacion)
            return (files[0] if files else None), status

        for button, kind in ((pdf, "pdf"), (excel, "excel"), (json_export, "json")):
            button.click(
                lambda l, c, n, g, k=kind: prepare_download(k, l, c, n, g),
                [lines_state, client_state, notes, grouping],
                [button, export_status],
            )
        clear.click(lambda current_grouping: ([], render_budget_html([], current_grouping), "Subtotal: 0.00 € | IVA: 0.00 € | TOTAL: 0.00 €", "Presupuesto limpiado."), grouping, [lines_state, budget, totals, export_status])
    return app


def collect_client(values, iva_pct=21):
    values = values if isinstance(values, (list, tuple)) else []
    keys = ["empresa", "cif", "contacto", "email", "validez", "condiciones"]
    try:
        rate = float(iva_pct) / 100
    except (TypeError, ValueError):
        rate = 0.21
    return dict(zip(keys, values)) | {"iva_pct": rate}


def export_artifact(kind, lineas, cliente, notas, agrupacion, iva_pct=21):
    if not lineas:
        return [], "Añada productos antes de exportar."
    try:
        rate = float(cliente.get("iva_pct", iva_pct / 100))
    except (TypeError, ValueError):
        rate = 0.21
    lineas = normalize_lineas(lineas)
    totals = calcular_totales(lineas, rate)
    criterio = {"Ninguna": None, "Por plan": "plan", "Por periodo": "periodicidad"}.get(agrupacion, agrupacion)
    data = b""
    if kind == "pdf":
        data, number = generar_pdf(cliente, lineas, totals, notas, criterio)
        path = os.path.join(PDF_DIR, f"{number}.pdf")
    elif kind == "excel":
        data = generar_excel(cliente, lineas, totals, notas, criterio)
        path = os.path.join(PDF_DIR, f"presupuesto_{datetime.date.today():%Y%m%d}.xlsx")
    else:
        path = generar_json(cliente, lineas, totals, PDF_DIR, notas, criterio, leer_ultima_tarifa())
    if kind in {"pdf", "excel"}:
        try:
            with open(path, "wb") as stream:
                stream.write(data)
        except OSError as error:
            return [], f"No se pudo guardar el archivo: {error}"
    return [path], f"✅ Generado: {os.path.basename(path)}"


def launch_app(port: int, inbrowser: bool = True, native_window: bool = False):
    """Launch Gradio; native_window is handled by cli.py's pywebview wrapper."""
    return build_app().launch(server_name="127.0.0.1", server_port=port, inbrowser=inbrowser, prevent_thread_lock=native_window)


if __name__ == "__main__":
    launch_app(8599)
