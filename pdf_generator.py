"""
PDF generator for the Presupuestador Sage 50
============================================
Builds the budget PDF with reportlab. Extracted from presupuestador.py.

Autor: ALCA TIC S.L.
"""

import datetime
import io
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generar_pdf(datos_cliente, lineas, totales, notas=""):
    """Genera un PDF profesional del presupuesto y devuelve los bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a5276"),
        spaceAfter=6 * mm,
    )
    estilo_subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=3 * mm,
    )
    estilo_normal = ParagraphStyle(
        "Normal2",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )
    estilo_small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.grey,
    )
    estilo_derecha = ParagraphStyle(
        "Derecha",
        parent=estilo_normal,
        alignment=TA_RIGHT,
    )

    elements = []

    # CABECERA
    elements.append(Paragraph("PRESUPUESTO", estilo_titulo))
    elements.append(
        HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a5276"), spaceAfter=4 * mm)
    )

    hoy = datetime.date.today().strftime("%d/%m/%Y")
    num_presupuesto = datetime.datetime.now().strftime("PRE-%Y%m%d-%H%M")

    # Info cabecera
    info_data = [
        [
            Paragraph(f"<b>Nº Presupuesto:</b> {num_presupuesto}", estilo_normal),
            Paragraph(f"<b>Fecha:</b> {hoy}", estilo_normal),
        ],
        [
            Paragraph(
                f"<b>Válido hasta:</b> {xml_escape(datos_cliente.get('validez', '30 días'))}", estilo_normal
            ),
            Paragraph(
                f"<b>Condiciones:</b> {xml_escape(datos_cliente.get('condiciones', 'Pago a 30 días'))}",
                estilo_normal,
            ),
        ],
    ]
    t_info = Table(info_data, colWidths=[doc.width / 2] * 2)
    t_info.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(t_info)
    elements.append(Spacer(1, 6 * mm))

    # DATOS CLIENTE
    elements.append(Paragraph("DATOS DEL CLIENTE", estilo_subtitulo))
    cliente_info = [
        [
            Paragraph(f"<b>Empresa:</b> {xml_escape(datos_cliente.get('empresa', ''))}", estilo_normal),
            Paragraph(f"<b>CIF/NIF:</b> {xml_escape(datos_cliente.get('cif', ''))}", estilo_normal),
        ],
        [
            Paragraph(f"<b>Contacto:</b> {xml_escape(datos_cliente.get('contacto', ''))}", estilo_normal),
            Paragraph(f"<b>Email:</b> {xml_escape(datos_cliente.get('email', ''))}", estilo_normal),
        ],
    ]
    t_cliente = Table(cliente_info, colWidths=[doc.width / 2] * 2)
    t_cliente.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8f9fa")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(t_cliente)
    elements.append(Spacer(1, 8 * mm))

    # TABLA DE LÍNEAS
    elements.append(Paragraph("DETALLE DEL PRESUPUESTO", estilo_subtitulo))

    header = [
        Paragraph("<b>Descripción</b>", estilo_normal),
        Paragraph("<b>Plan</b>", estilo_normal),
        Paragraph("<b>Periodo</b>", estilo_normal),
        Paragraph("<b>Uds</b>", estilo_derecha),
        Paragraph("<b>Precio Ud.</b>", estilo_derecha),
        Paragraph("<b>Dto %</b>", estilo_derecha),
        Paragraph("<b>Total</b>", estilo_derecha),
    ]

    table_data = [header]
    col_widths = [
        doc.width * 0.32,
        doc.width * 0.12,
        doc.width * 0.12,
        doc.width * 0.07,
        doc.width * 0.12,
        doc.width * 0.10,
        doc.width * 0.15,
    ]

    for linea in lineas:
        dto_pct = linea.get("dto_total_pct", 0)
        row = [
            Paragraph(xml_escape(linea["descripcion"]), estilo_normal),
            Paragraph(xml_escape(linea.get("plan", "-")), estilo_normal),
            Paragraph(xml_escape(linea.get("periodicidad", "-")), estilo_normal),
            Paragraph(str(linea["cantidad"]), estilo_derecha),
            Paragraph(f"{linea['precio_unitario']:.2f} €", estilo_derecha),
            Paragraph(f"{dto_pct:.0%}" if dto_pct > 0 else "-", estilo_derecha),
            Paragraph(f"{linea['total']:.2f} €", estilo_derecha),
        ]
        table_data.append(row)

    # Fila totales
    table_data.append(
        [
            Paragraph("", estilo_normal),
            "",
            "",
            "",
            "",
            Paragraph("<b>SUBTOTAL</b>", estilo_derecha),
            Paragraph(f"<b>{totales['subtotal']:.2f} €</b>", estilo_derecha),
        ]
    )
    table_data.append(
        [
            "",
            "",
            "",
            "",
            "",
            Paragraph(f"<b>IVA ({totales['iva_pct']:.0%})</b>", estilo_derecha),
            Paragraph(f"<b>{totales['iva']:.2f} €</b>", estilo_derecha),
        ]
    )
    table_data.append(
        [
            "",
            "",
            "",
            "",
            "",
            Paragraph("<b>TOTAL</b>", estilo_derecha),
            Paragraph(f"<b>{totales['total']:.2f} €</b>", estilo_derecha),
        ]
    )

    tabla = Table(table_data, colWidths=col_widths, repeatRows=1)
    n_filas = len(table_data)
    tabla.setStyle(
        TableStyle(
            [
                # Cabecera
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a5276")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                # Filas alternas
                *[
                    ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f2f7fb"))
                    for i in range(2, n_filas - 3, 2)
                ],
                # Bordes
                ("GRID", (0, 0), (-1, n_filas - 4), 0.5, colors.HexColor("#dee2e6")),
                ("LINEABOVE", (5, n_filas - 3), (-1, n_filas - 3), 1, colors.HexColor("#1a5276")),
                # Fila total final
                ("BACKGROUND", (5, n_filas - 1), (-1, n_filas - 1), colors.HexColor("#1a5276")),
                ("TEXTCOLOR", (5, n_filas - 1), (-1, n_filas - 1), colors.white),
                # Padding
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(tabla)
    elements.append(Spacer(1, 8 * mm))

    # NOTAS
    if notas:
        elements.append(Paragraph("OBSERVACIONES", estilo_subtitulo))
        elements.append(Paragraph(xml_escape(notas), estilo_normal))
        elements.append(Spacer(1, 4 * mm))

    # PIE
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=2 * mm))
    elements.append(Paragraph(f"Generado el {hoy} — ALCA TIC S.L. — Cádiz, España", estilo_small))

    doc.build(elements)
    buf.seek(0)
    return buf.getvalue(), num_presupuesto
