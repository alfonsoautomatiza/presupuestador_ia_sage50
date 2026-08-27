"""
Excel generator for the Presupuestador Sage 50
==============================================
Builds the budget XLSX with openpyxl. Extracted from presupuestador.py.

Autor: ALCA TIC S.L.
"""

import datetime
import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side, numbers
from openpyxl.utils import get_column_letter


def generar_excel(datos_cliente, lineas, totales, notas=""):
    """Genera un Excel profesional del presupuesto y devuelve los bytes."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Presupuesto"

    hoy = datetime.date.today().strftime("%d/%m/%Y")
    num_presupuesto = datetime.datetime.now().strftime("PRE-%Y%m%d-%H%M")

    # Estilos
    titulo_font = Font(name="Calibri", size=16, bold=True, color="1A5276")
    subtitulo_font = Font(name="Calibri", size=11, bold=True, color="2C3E50")
    normal_font = Font(name="Calibri", size=10)
    bold_font = Font(name="Calibri", size=10, bold=True)
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1A5276", end_color="1A5276", fill_type="solid")
    total_fill = PatternFill(start_color="1A5276", end_color="1A5276", fill_type="solid")
    total_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    alt_fill = PatternFill(start_color="F2F7FB", end_color="F2F7FB", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="DEE2E6"),
        right=Side(style="thin", color="DEE2E6"),
        top=Side(style="thin", color="DEE2E6"),
        bottom=Side(style="thin", color="DEE2E6"),
    )
    money_fmt = '#,##0.00 €'

    # CABECERA
    ws.merge_cells("A1:G1")
    ws["A1"] = "PRESUPUESTO"
    ws["A1"].font = titulo_font

    ws.merge_cells("A2:G2")
    ws["A2"] = f"Nº {num_presupuesto}  |  Fecha: {hoy}  |  Validez: {datos_cliente.get('validez', '30 días')}"
    ws["A2"].font = Font(name="Calibri", size=9, color="666666")

    # DATOS CLIENTE
    row = 4
    ws.merge_cells(f"A{row}:G{row}")
    ws[f"A{row}"] = "DATOS DEL CLIENTE"
    ws[f"A{row}"].font = subtitulo_font

    row = 5
    for label, key in [("Empresa", "empresa"), ("CIF/NIF", "cif"), ("Contacto", "contacto"), ("Email", "email")]:
        val = datos_cliente.get(key, "")
        if val:
            ws[f"A{row}"] = f"{label}:"
            ws[f"A{row}"].font = bold_font
            ws.merge_cells(f"B{row}:D{row}")
            ws[f"B{row}"] = val
            ws[f"B{row}"].font = normal_font
            row += 1

    cond = datos_cliente.get("condiciones", "")
    if cond:
        ws[f"A{row}"] = "Condiciones:"
        ws[f"A{row}"].font = bold_font
        ws.merge_cells(f"B{row}:D{row}")
        ws[f"B{row}"] = cond
        ws[f"B{row}"].font = normal_font
        row += 1

    # TABLA DE LÍNEAS
    row += 1
    ws.merge_cells(f"A{row}:G{row}")
    ws[f"A{row}"] = "DETALLE DEL PRESUPUESTO"
    ws[f"A{row}"].font = subtitulo_font
    row += 1

    headers = ["Descripción", "Plan", "Periodo", "Uds", "Precio Ud.", "Dto %", "Total"]
    col_widths = [42, 14, 14, 8, 14, 10, 14]

    for col_idx, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=row, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    row += 1
    header_row = row - 1

    for i, linea in enumerate(lineas):
        dto_pct = linea.get("dto_total_pct", 0)
        for col_idx, val in enumerate([
            linea["descripcion"],
            linea.get("plan", "-"),
            linea.get("periodicidad", "-"),
            linea["cantidad"],
            linea["precio_unitario"],
            dto_pct if dto_pct > 0 else 0,
            linea["total"],
        ], 1):
            cell = ws.cell(row=row, column=col_idx, value=val)
            cell.font = normal_font
            cell.border = thin_border
            if col_idx in (4, 5, 6, 7):
                cell.alignment = Alignment(horizontal="right")
            if col_idx == 5 and isinstance(val, (int, float)):
                cell.number_format = money_fmt
            if col_idx == 6 and isinstance(val, (int, float)):
                cell.number_format = '0%'
            if col_idx == 7 and isinstance(val, (int, float)):
                cell.number_format = money_fmt
            if i % 2 == 1:
                cell.fill = alt_fill
        row += 1

    data_end_row = row - 1

    # TOTALES
    totales_start = row
    for label, key, is_total in [
        ("SUBTOTAL", "subtotal", False),
        (f"IVA ({totales['iva_pct']:.0%})", "iva", False),
        ("TOTAL", "total", True),
    ]:
        cell_label = ws.cell(row=row, column=6, value=label)
        cell_val = ws.cell(row=row, column=7, value=totales[key])
        cell_val.number_format = money_fmt
        if is_total:
            cell_label.font = total_font
            cell_val.font = total_font
            cell_label.fill = total_fill
            cell_val.fill = total_fill
        else:
            cell_label.font = bold_font
            cell_val.font = bold_font
        cell_label.alignment = Alignment(horizontal="right")
        cell_val.alignment = Alignment(horizontal="right")
        row += 1

    # NOTAS
    if notas:
        row += 1
        ws.merge_cells(f"A{row}:G{row}")
        ws[f"A{row}"] = "OBSERVACIONES"
        ws[f"A{row}"].font = subtitulo_font
        row += 1
        ws.merge_cells(f"A{row}:G{row}")
        ws[f"A{row}"] = notas
        ws[f"A{row}"].font = normal_font

    # PIE
    row += 2
    ws.merge_cells(f"A{row}:G{row}")
    ws[f"A{row}"] = f"Generado el {hoy} — ALCA TIC S.L. — Cádiz, España"
    ws[f"A{row}"].font = Font(name="Calibri", size=8, color="999999")

    # Auto-filtro
    ws.auto_filter.ref = f"A{header_row}:G{data_end_row}"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()
