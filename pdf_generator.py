"""PDF generator for the Presupuestador Sage 50."""

import datetime
import io
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from models import agrupar_lineas, subtotal_grupo


def _xml_text(value, default=""):
    """Convert optional values to text before passing them to XML escaping."""
    return xml_escape(default if value is None else str(value))


def generar_pdf(datos_cliente, lineas, totales, notas="", agrupacion=None):
    """Generate a professional quote PDF and return its bytes and number."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    titulo = ParagraphStyle("Titulo", parent=styles["Title"], fontSize=20, textColor=colors.HexColor("#1a5276"), spaceAfter=6 * mm)
    subtitulo = ParagraphStyle("Subtitulo", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#2c3e50"), spaceAfter=3 * mm)
    normal = ParagraphStyle("Normal2", parent=styles["Normal"], fontSize=9, leading=12)
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.grey)
    derecha = ParagraphStyle("Derecha", parent=normal, alignment=TA_RIGHT)
    elements = [Paragraph("PRESUPUESTO", titulo), HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a5276"), spaceAfter=4 * mm)]
    hoy = datetime.date.today().strftime("%d/%m/%Y")
    num = datetime.datetime.now().strftime("PRE-%Y%m%d-%H%M")
    info = [[Paragraph(f"<b>Nº Presupuesto:</b> {num}", normal), Paragraph(f"<b>Fecha:</b> {hoy}", normal)], [Paragraph(f"<b>Válido hasta:</b> {_xml_text(datos_cliente.get('validez'), '30 días')}", normal), Paragraph(f"<b>Condiciones:</b> {_xml_text(datos_cliente.get('condiciones'), 'Pago a 30 días')}", normal)]]
    t = Table(info, colWidths=[doc.width / 2] * 2)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    elements += [t, Spacer(1, 6 * mm), Paragraph("DATOS DEL CLIENTE", subtitulo)]
    cliente = [[Paragraph(f"<b>Empresa:</b> {_xml_text(datos_cliente.get('empresa'))}", normal), Paragraph(f"<b>CIF/NIF:</b> {_xml_text(datos_cliente.get('cif'))}", normal)], [Paragraph(f"<b>Contacto:</b> {_xml_text(datos_cliente.get('contacto'))}", normal), Paragraph(f"<b>Email:</b> {_xml_text(datos_cliente.get('email'))}", normal)]]
    t = Table(cliente, colWidths=[doc.width / 2] * 2)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8f9fa")), ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#dee2e6")), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    elements += [t, Spacer(1, 8 * mm), Paragraph("DETALLE DEL PRESUPUESTO", subtitulo)]
    header = [Paragraph("<b>Código</b>", normal), Paragraph("<b>Descripción</b>", normal), Paragraph("<b>Plan</b>", normal), Paragraph("<b>Periodo</b>", normal), Paragraph("<b>Uds</b>", derecha), Paragraph("<b>Precio Ud.</b>", derecha), Paragraph("<b>Dto %</b>", derecha), Paragraph("<b>Total</b>", derecha)]
    table_data = [header]
    col_widths = [doc.width * value for value in (.10, .25, .11, .11, .06, .12, .09, .16)]
    groups = agrupar_lineas(lineas, agrupacion)
    for grupo, group_lines in groups:
        if grupo is not None:
            table_data.append([Paragraph(f"<b>{'PLAN' if agrupacion == 'plan' else 'PERIODO'}: {xml_escape(str(grupo))}</b>", normal)] + [Paragraph("", normal)] * 7)
        for linea in group_lines:
            dto = linea.get("dto_total_pct", 0)
            table_data.append([Paragraph(xml_escape(str(linea.get("codigo", ""))), normal), Paragraph(_xml_text(linea.get("descripcion")), normal), Paragraph(_xml_text(linea.get("plan"), "-"), normal), Paragraph(_xml_text(linea.get("periodicidad"), "-"), normal), Paragraph(str(linea["cantidad"]), derecha), Paragraph(f"{linea['precio_unitario']:.2f} €", derecha), Paragraph(f"{dto:.0%}" if dto > 0 else "-", derecha), Paragraph(f"{linea['total']:.2f} €", derecha)])
        if grupo is not None:
            table_data.append([Paragraph("", normal)] * 6 + [Paragraph(f"<b>Subtotal {xml_escape(str(grupo))}</b>", derecha), Paragraph(f"<b>{subtotal_grupo(group_lines):.2f} €</b>", derecha)])
    table_data += [[Paragraph("", normal)] * 5 + [Paragraph("<b>SUBTOTAL</b>", derecha), Paragraph("", normal), Paragraph(f"<b>{totales['subtotal']:.2f} €</b>", derecha)], [Paragraph("", normal)] * 5 + [Paragraph("<b>TOTAL + IVA</b>", derecha), Paragraph("", normal), Paragraph(f"<b>{totales['total']:.2f} €</b>", derecha)]]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    n = len(table_data)
    style = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a5276")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, n - 3), .5, colors.HexColor("#dee2e6")), ("LINEABOVE", (5, n - 2), (-1, n - 2), 1, colors.HexColor("#1a5276")), ("BACKGROUND", (5, n - 1), (-1, n - 1), colors.HexColor("#1a5276")), ("TEXTCOLOR", (5, n - 1), (-1, n - 1), colors.white), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]
    for index, (grupo, group_lines) in enumerate(groups):
        if grupo is not None:
            start = 1 + sum(1 + len(gl) + 1 for _, gl in groups[:index])
            style += [("SPAN", (0, start), (-1, start)), ("BACKGROUND", (0, start), (-1, start), colors.HexColor("#d9eaf7"))]
    table.setStyle(TableStyle(style))
    elements += [table, Spacer(1, 8 * mm)]
    if notas:
        elements += [Paragraph("OBSERVACIONES", subtitulo), Paragraph(_xml_text(notas), normal), Spacer(1, 4 * mm)]
    elements += [HRFlowable(width="100%", thickness=.5, color=colors.grey, spaceAfter=2 * mm), Paragraph(f"Generado el {hoy} — alfonsoautomatiza.com — Cádiz, España", small)]
    doc.build(elements)
    return buf.getvalue(), num
