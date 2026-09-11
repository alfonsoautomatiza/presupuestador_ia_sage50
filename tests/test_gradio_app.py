from importlib import import_module

_app = import_module("gradio_app")
add_line = _app.add_line
add_product_lines = _app.add_product_lines
calcular_totales = _app.calcular_totales
filtrar_productos = _app.filtrar_productos
normalize_lineas = _app.normalize_lineas
render_budget_html = _app.render_budget_html
delete_line = _app.delete_line
select_all_filter_values = _app.select_all_filter_values


def product():
    return {
        "codigo": "A1", "descripcion": "Producto", "planes": "Standard",
        "periodicidades": "Anual", "modulo": "", "sabor": "", "plataforma": "",
        "dto_partner": 0.1, "dto_tech_bp": 0, "dto_pam": 0,
        "_precios": {"standard_anual": 100},
    }


def test_select_all_filter_values_covers_every_dimension():
    products = [
        {
            "codigo": "A1", "descripcion": "Uno", "planes": "Complete, Extra",
            "periodicidades": "Anual, Mensual", "modulo": "Contabilidad",
            "sabor": "Essential", "plataforma": "Desktop",
        },
        {
            "codigo": "B2", "descripcion": "Dos", "planes": "Standard",
            "periodicidades": "Bianual", "modulo": "Nóminas",
            "sabor": "", "plataforma": "Web",
        },
    ]
    assert select_all_filter_values(products) == {
        "plans": ["Complete", "Extra", "Standard"],
        "periodicidades": ["Anual", "Bianual", "Mensual"],
        "sabores": ["Essential"],
        "plataformas": ["Desktop", "Web"],
    }


def test_gradio_helpers_filter_and_add_without_server():
    item = product()
    assert filtrar_productos([item], texto="producto") == [item]
    lines, message = add_line(item, "Standard", "Anual", 2, [])
    assert lines[0]["total"] == 180.0
    assert "Añadido" in message


def multi_product():
    item = product()
    item["planes"] = "Standard, Extra"
    item["periodicidades"] = "Anual, Mensual"
    item["_precios"] = {
        "standard_anual": 100, "standard_mensual": 10,
        "extra_anual": 200, "extra_mensual": 20,
    }
    return item


def test_add_product_lines_without_selection_adds_all_combinations():
    lines, status = add_product_lines(multi_product(), None, None, 2, [])
    assert [(line["plan"], line["periodicidad"]) for line in lines] == [
        ("Standard", "Anual"), ("Standard", "Mensual"),
        ("Extra", "Anual"), ("Extra", "Mensual"),
    ]
    assert all(line["cantidad"] == 2 for line in lines)
    assert "Añadidas 4 líneas" in status


def test_add_product_lines_with_plan_adds_all_periodicities():
    lines, _ = add_product_lines(multi_product(), "Extra", None, 1, [])
    assert [(line["plan"], line["periodicidad"]) for line in lines] == [("Extra", "Anual"), ("Extra", "Mensual")]


def test_add_product_lines_with_periodicity_adds_all_plans():
    lines, _ = add_product_lines(multi_product(), None, "Mensual", 1, [])
    assert [(line["plan"], line["periodicidad"]) for line in lines] == [("Standard", "Mensual"), ("Extra", "Mensual")]


def test_add_product_lines_with_both_selections_adds_one_combination():
    existing = [{"codigo": "previous"}]
    lines, status = add_product_lines(multi_product(), "Extra", "Mensual", 3, existing)
    assert lines[0] == existing[0]
    assert [(line["plan"], line["periodicidad"]) for line in lines[1:]] == [("Extra", "Mensual")]
    assert lines[1]["total"] == 54.0
    assert "Añadidas 1 líneas" in status


def test_gradio_totals_are_explicit_and_rounded():
    assert calcular_totales([{"total": 10.005}], 0.21) == {
        "subtotal": 10.01, "iva_pct": 0.21, "iva": 2.1, "total": 12.11
    }


def test_delete_line_removes_exact_zero_based_line():
    lines = [{"codigo": "A"}, {"codigo": "B"}, {"codigo": "C"}]
    assert [line["codigo"] for line in delete_line("1", lines)] == ["A", "C"]
    assert lines[1]["codigo"] == "B"


def test_budget_html_escapes_values_and_has_row_delete_actions():
    rendered = render_budget_html([{"codigo": "<A>", "descripcion": '"x"', "plan": "P", "periodicidad": "Anual", "cantidad": 1, "total": 2}], "Ninguna")
    assert "&lt;A&gt;" in rendered
    assert "&quot;x&quot;" in rendered
    assert 'data-line-index="0"' in rendered
    assert "🗑️ Eliminar" in rendered


def test_normalize_lineas_fills_optional_export_fields():
    line = normalize_lineas([{"descripcion": None, "codigo": None, "plan": None, "periodicidad": None}])[0]
    assert line["descripcion"] == ""
    assert line["codigo"] == ""
    assert line["plan"] == ""
    assert line["periodicidad"] == ""


def test_pdf_accepts_none_description():
    from pdf_generator import generar_pdf
    data, _ = generar_pdf({}, [{"codigo": "A", "descripcion": None, "plan": None, "periodicidad": None, "cantidad": 1, "precio_unitario": 0, "dto_total_pct": 0, "total": 0}], {"subtotal": 0, "total": 0})
    assert data
