"""
Reports Module - Professional PDF generation with ReportLab
Based on GageTrack reference PDFs:
  - CERTIFICADO DE CALIBRACION.pdf
  - HISTORIAL DE CALIBRACION.pdf
  - ORDEN DE TRABAJO DE CALIBRACION.pdf
  - REPORTE DETALLADO DE CALIBRACION.pdf
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import sys
import base64
sys.path.append('..')
from utils.db_manager import load_data, get_calibrations, get_instrument_by_id, get_overdue_instruments

# ReportLab imports
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    HRFlowable, KeepTogether, Image as RLImage
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.pdfgen import canvas

# ─────────────────────────────────────────────
# SHARED STYLES & COLORS (matching existing app palette)
# ─────────────────────────────────────────────

PRIMARY_BLUE   = colors.HexColor("#1e3c72")
ACCENT_BLUE    = colors.HexColor("#2a5298")
LIGHT_BLUE     = colors.HexColor("#667eea")
SUCCESS_GREEN  = colors.HexColor("#27AE60")
WARNING_ORANGE = colors.HexColor("#F39C12")
DANGER_RED     = colors.HexColor("#E74C3C")
GRAY_LIGHT     = colors.HexColor("#ecf0f1")
GRAY_TEXT      = colors.HexColor("#7f8c8d")
DARK_TEXT      = colors.HexColor("#2c3e50")
WHITE          = colors.white


def get_styles():
    """Get standard paragraph styles"""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DocTitle",
        fontSize=18, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name="DocSubtitle",
        fontSize=10, fontName="Helvetica",
        textColor=colors.HexColor("#b0c4de"), alignment=TA_CENTER, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontSize=11, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_LEFT,
        backColor=PRIMARY_BLUE, leftIndent=6, rightIndent=6,
        spaceBefore=8, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="FieldLabel",
        fontSize=9, fontName="Helvetica-Bold",
        textColor=DARK_TEXT
    ))
    styles.add(ParagraphStyle(
        name="FieldValue",
        fontSize=9, fontName="Helvetica",
        textColor=DARK_TEXT
    ))
    styles.add(ParagraphStyle(
        name="FooterText",
        fontSize=7, fontName="Helvetica",
        textColor=GRAY_TEXT, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        name="ResultApproved",
        fontSize=14, fontName="Helvetica-Bold",
        textColor=SUCCESS_GREEN, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        name="ResultRejected",
        fontSize=14, fontName="Helvetica-Bold",
        textColor=DANGER_RED, alignment=TA_CENTER
    ))
    return styles


def _header_table(title: str, subtitle: str, doc_number: str, date_str: str,
                  logo_path: str = "EA_2.png") -> list:
    """Generate header block with logo, title and document info"""
    styles = get_styles()
    elements = []

    # Build header data
    logo_cell = ""
    try:
        img = RLImage(logo_path, width=3.5*cm, height=1.8*cm)
        logo_cell = img
    except Exception:
        logo_cell = Paragraph("<b>GageTrack</b>", styles["Normal"])

    title_block = [
        Paragraph(f'<font color="white"><b>{title}</b></font>', styles["DocTitle"]),
        Spacer(1, 2),
        Paragraph(f'<font color="#b0c4de">{subtitle}</font>', styles["DocSubtitle"]),
    ]

    doc_info = [
        Paragraph(f'<font color="white"><b>No. Doc:</b> {doc_number}</font>', styles["DocSubtitle"]),
        Paragraph(f'<font color="white"><b>Fecha:</b> {date_str}</font>', styles["DocSubtitle"]),
        Paragraph('<font color="white"><b>Rev:</b> 01</font>', styles["DocSubtitle"]),
    ]

    header_data = [[logo_cell, title_block, doc_info]]
    header_table = Table(header_data, colWidths=[4*cm, 10*cm, 5*cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY_BLUE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [8, 8, 0, 0]),
    ]))

    elements.append(header_table)
    elements.append(Spacer(1, 4))
    return elements


def _section_title(text: str) -> Table:
    """Blue section header bar"""
    styles = get_styles()
    t = Table([[Paragraph(f'<b>{text}</b>', styles["SectionHeader"])]],
              colWidths=[19*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _two_col_table(data: list, col_widths: list = None) -> Table:
    """Label/Value table with alternating row colors"""
    if col_widths is None:
        col_widths = [7*cm, 12*cm]
    styles = get_styles()

    table_data = []
    for label, value in data:
        table_data.append([
            Paragraph(str(label), styles["FieldLabel"]),
            Paragraph(str(value) if value else "—", styles["FieldValue"])
        ])

    t = Table(table_data, colWidths=col_widths)
    row_styles = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce3ea")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(0, len(table_data), 2):
        row_styles.append(("BACKGROUND", (0, i), (-1, i), GRAY_LIGHT))

    t.setStyle(TableStyle(row_styles))
    return t


def _footer(elements: list, page: int = 1) -> None:
    styles = get_styles()
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE))
    elements.append(Spacer(1, 3))
    elements.append(Paragraph(
        f"GageTrack © {datetime.now().year} — Sistema de Gestión de Instrumentos de Medición | "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Página {page}",
        styles["FooterText"]
    ))


def _signature_block() -> Table:
    """3-column signature area"""
    styles = get_styles()
    sig_data = [[
        [Paragraph("_" * 35, styles["FieldValue"]),
         Paragraph("<b>Técnico Calibrador</b>", styles["FieldLabel"]),
         Paragraph("Nombre y Firma", styles["FooterText"])],
        [Paragraph("_" * 35, styles["FieldValue"]),
         Paragraph("<b>Supervisor de Calidad</b>", styles["FieldLabel"]),
         Paragraph("Nombre y Firma", styles["FooterText"])],
        [Paragraph("_" * 35, styles["FieldValue"]),
         Paragraph("<b>Responsable del Área</b>", styles["FieldLabel"]),
         Paragraph("Nombre y Firma", styles["FooterText"])],
    ]]

    # Flatten the nested lists
    flat = []
    for col in sig_data[0]:
        flat.append([item for item in col])

    # Build table with proper structure
    t_data = [["", "", ""]]  # spacer
    t = Table([[
        "\n\n_______________________________\nTécnico Calibrador",
        "\n\n_______________________________\nSupervisor de Calidad",
        "\n\n_______________________________\nResponsable del Área",
    ]], colWidths=[6.3*cm, 6.3*cm, 6.3*cm])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 30),
    ]))
    return t


# ─────────────────────────────────────────────
# PDF 1: CERTIFICADO DE CALIBRACIÓN
# ─────────────────────────────────────────────

def generate_calibration_certificate(instrument_data: dict, calibration_data: dict = None) -> BytesIO:
    """Generate professional calibration certificate PDF"""
    buffer = BytesIO()
    styles = get_styles()

    gage_id = instrument_data.get("gage_id", instrument_data.get("Id. de Instrumento", "N/A"))
    doc_number = f"CAL-{gage_id}-{datetime.now().strftime('%Y%m%d')}"
    date_str = datetime.now().strftime("%d/%m/%Y")

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=2*cm
    )

    elements = []

    # Header
    elements += _header_table(
        "CERTIFICADO DE CALIBRACIÓN",
        "Measurement System Control — GageTrack",
        doc_number, date_str
    )

    # Result badge
    result = calibration_data.get("result", "N/A") if calibration_data else "N/A"
    result_style = "ResultApproved" if result == "Aprobado" else "ResultRejected"
    result_color = "#27AE60" if result == "Aprobado" else "#E74C3C"

    result_t = Table([[
        Paragraph(f'<font color="{result_color}"><b>RESULTADO: {result.upper()}</b></font>',
                  styles["Normal"])
    ]], colWidths=[19*cm])
    result_t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("BACKGROUND", (0, 0), (-1, -1),
         colors.HexColor("#d4edda") if result == "Aprobado" else colors.HexColor("#f8d7da")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX", (0, 0), (-1, -1), 1.5,
         SUCCESS_GREEN if result == "Aprobado" else DANGER_RED),
        ("ROUNDEDCORNERS", [6, 6, 6, 6]),
    ]))
    elements.append(result_t)
    elements.append(Spacer(1, 8))

    # Instrument info
    elements.append(_section_title("📋 INFORMACIÓN DEL INSTRUMENTO"))
    elements.append(Spacer(1, 3))
    elements.append(_two_col_table([
        ("ID de Instrumento", gage_id),
        ("Descripción", instrument_data.get("description", instrument_data.get("Descripción", "N/A"))),
        ("Tipo", instrument_data.get("type", instrument_data.get("Tipo", "N/A"))),
        ("Número de Serie", instrument_data.get("serial_number", instrument_data.get("N/S del Instrumento", "N/A"))),
        ("Número de Modelo", instrument_data.get("model_number", instrument_data.get("No.  de Modelo", "N/A"))),
        ("No. de Contabilidad", instrument_data.get("accounting_number", instrument_data.get("No. de Contabilidad", "N/A"))),
        ("Estatus", instrument_data.get("status", instrument_data.get("Estatus", "N/A"))),
        ("Ubicación Actual", instrument_data.get("current_location", instrument_data.get("Ubicación Actual", "N/A"))),
        ("Responsable", instrument_data.get("responsible_person", instrument_data.get("Persona responsable", "N/A"))),
    ]))
    elements.append(Spacer(1, 8))

    # Calibration info
    elements.append(_section_title("🔬 INFORMACIÓN DE CALIBRACIÓN"))
    elements.append(Spacer(1, 3))

    if calibration_data:
        elements.append(_two_col_table([
            ("Fecha de Calibración",
             calibration_data.get("calibration_date", "N/A")),
            ("Próxima Calibración",
             calibration_data.get("next_calibration_date", "N/A")),
            ("Técnico Calibrador", calibration_data.get("technician", "N/A")),
            ("Proveedor / Laboratorio", calibration_data.get("supplier", "N/A")),
            ("N° de Certificado Externo", calibration_data.get("certificate_number", "N/A")),
            ("Valor de Referencia",
             f"{calibration_data.get('reference_value', 'N/A')}"),
            ("Valor Medido",
             f"{calibration_data.get('measured_value', 'N/A')}"),
            ("Tolerancia", calibration_data.get("tolerance", "N/A")),
            ("Incertidumbre (U)",
             f"{calibration_data.get('uncertainty', 'N/A')}"),
            ("Costo", f"${calibration_data.get('cost', 0):.2f}" if calibration_data.get("cost") else "N/A"),
            ("Observaciones", calibration_data.get("observations", "—")),
        ]))
    else:
        elements.append(_two_col_table([
            ("Fecha Última Calibración",
             str(instrument_data.get("last_calibration_date",
                 instrument_data.get("Fecha del última programación", "N/A")))),
            ("Próximo Vencimiento",
             str(instrument_data.get("next_calibration_date",
                 instrument_data.get("Próximo vencimiento", "N/A")))),
            ("Frecuencia", f"{instrument_data.get('calibration_frequency', instrument_data.get('Frecuencia de calibración', 'N/A'))} días"),
        ]))

    elements.append(Spacer(1, 15))

    # Certification text
    elements.append(_section_title("✅ DECLARACIÓN DE CONFORMIDAD"))
    elements.append(Spacer(1, 5))
    cert_text = (
        "Se certifica que el instrumento de medición descrito en este documento ha sido calibrado "
        "conforme a los procedimientos establecidos y trazables a patrones nacionales e internacionales "
        f"de medición. La calibración fue realizada el {calibration_data.get('calibration_date', date_str) if calibration_data else date_str} "
        "y es válida hasta la próxima fecha de calibración indicada."
    )
    elements.append(Paragraph(cert_text, styles["FieldValue"]))
    elements.append(Spacer(1, 20))

    # Signatures
    elements.append(_signature_block())
    elements.append(Spacer(1, 10))

    _footer(elements)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────
# PDF 2: HISTORIAL DE CALIBRACIONES
# ─────────────────────────────────────────────

def generate_calibration_history(instrument_data: dict, calibrations_df: pd.DataFrame) -> BytesIO:
    """Generate calibration history report PDF"""
    buffer = BytesIO()
    styles = get_styles()

    gage_id = instrument_data.get("gage_id", instrument_data.get("Id. de Instrumento", "N/A"))
    doc_number = f"HIST-{gage_id}-{datetime.now().strftime('%Y%m%d')}"
    date_str = datetime.now().strftime("%d/%m/%Y")

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=2*cm
    )

    elements = []
    elements += _header_table("HISTORIAL DE CALIBRACIONES",
                               f"Instrumento: {gage_id}", doc_number, date_str)

    # Instrument summary
    elements.append(_section_title("📋 DATOS DEL INSTRUMENTO"))
    elements.append(Spacer(1, 3))
    elements.append(_two_col_table([
        ("ID", gage_id),
        ("Descripción", instrument_data.get("description", instrument_data.get("Descripción", "N/A"))),
        ("Tipo", instrument_data.get("type", instrument_data.get("Tipo", "N/A"))),
        ("N/S", instrument_data.get("serial_number", instrument_data.get("N/S del Instrumento", "N/A"))),
        ("Ubicación", instrument_data.get("current_location", instrument_data.get("Ubicación Actual", "N/A"))),
        ("Responsable", instrument_data.get("responsible_person", instrument_data.get("Persona responsable", "N/A"))),
    ], col_widths=[5*cm, 14*cm]))
    elements.append(Spacer(1, 10))

    # History table
    elements.append(_section_title("📅 HISTORIAL DE CALIBRACIONES"))
    elements.append(Spacer(1, 5))

    if calibrations_df.empty:
        elements.append(Paragraph("No hay calibraciones registradas.", styles["FieldValue"]))
    else:
        headers = ["Fecha", "Próx. Cal.", "Técnico", "Proveedor", "N° Cert.", "Resultado", "Costo"]
        col_map = {
            "calibration_date": "Fecha",
            "next_calibration_date": "Próx. Cal.",
            "technician": "Técnico",
            "supplier": "Proveedor",
            "certificate_number": "N° Cert.",
            "result": "Resultado",
            "cost": "Costo",
        }

        table_data = [headers]
        for _, row in calibrations_df.iterrows():
            result = str(row.get("result", "—"))
            table_data.append([
                str(row.get("calibration_date", "—"))[:10],
                str(row.get("next_calibration_date", "—"))[:10],
                str(row.get("technician", "—")),
                str(row.get("supplier", "—")),
                str(row.get("certificate_number", "—")),
                result,
                f"${float(row['cost']):.2f}" if row.get("cost") else "—",
            ])

        hist_table = Table(table_data, colWidths=[2.5*cm, 2.5*cm, 3*cm, 3*cm, 2.5*cm, 2.5*cm, 2*cm])
        row_styles = [
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce3ea")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        # Color result column
        for i, row_data in enumerate(table_data[1:], 1):
            result = row_data[5]
            if result == "Aprobado":
                row_styles.append(("TEXTCOLOR", (5, i), (5, i), SUCCESS_GREEN))
                row_styles.append(("BACKGROUND", (5, i), (5, i), colors.HexColor("#d4edda")))
            elif result == "Rechazado":
                row_styles.append(("TEXTCOLOR", (5, i), (5, i), DANGER_RED))
                row_styles.append(("BACKGROUND", (5, i), (5, i), colors.HexColor("#f8d7da")))
            if i % 2 == 0:
                row_styles.append(("BACKGROUND", (0, i), (4, i), GRAY_LIGHT))
                row_styles.append(("BACKGROUND", (6, i), (6, i), GRAY_LIGHT))

        hist_table.setStyle(TableStyle(row_styles))
        elements.append(hist_table)

    _footer(elements)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────
# PDF 3: ORDEN DE TRABAJO DE CALIBRACIÓN
# ─────────────────────────────────────────────

def generate_work_order(instrument_data: dict, calibration_data: dict = None) -> BytesIO:
    """Generate calibration work order PDF"""
    buffer = BytesIO()
    styles = get_styles()

    gage_id = instrument_data.get("gage_id", instrument_data.get("Id. de Instrumento", "N/A"))
    doc_number = f"OT-{gage_id}-{datetime.now().strftime('%Y%m%d')}"
    date_str = datetime.now().strftime("%d/%m/%Y")

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=2*cm
    )

    elements = []
    elements += _header_table("ORDEN DE TRABAJO DE CALIBRACIÓN",
                               "Control de Instrumentos de Medición", doc_number, date_str)

    elements.append(_section_title("📋 DATOS DEL INSTRUMENTO"))
    elements.append(Spacer(1, 3))
    elements.append(_two_col_table([
        ("ID de Instrumento", gage_id),
        ("Descripción", instrument_data.get("description", instrument_data.get("Descripción", "N/A"))),
        ("Tipo", instrument_data.get("type", instrument_data.get("Tipo", "N/A"))),
        ("N° de Serie", instrument_data.get("serial_number", instrument_data.get("N/S del Instrumento", "N/A"))),
        ("N° de Modelo", instrument_data.get("model_number", instrument_data.get("No.  de Modelo", "N/A"))),
        ("Ubicación de Almacén", instrument_data.get("storage_location", instrument_data.get("Ubicación de Almacén", "N/A"))),
        ("Ubicación Actual", instrument_data.get("current_location", instrument_data.get("Ubicación Actual", "N/A"))),
        ("Responsable", instrument_data.get("responsible_person", instrument_data.get("Persona responsable", "N/A"))),
        ("Custodio", instrument_data.get("current_custodian", instrument_data.get("Custodio actual", "N/A"))),
    ]))
    elements.append(Spacer(1, 10))

    elements.append(_section_title("🔧 DATOS DE LA CALIBRACIÓN A REALIZAR"))
    elements.append(Spacer(1, 3))
    cal_info = [
        ("Fecha Solicitada", calibration_data.get("calibration_date", date_str) if calibration_data else date_str),
        ("Técnico Asignado", calibration_data.get("technician", "Por asignar") if calibration_data else "Por asignar"),
        ("Proveedor / Laboratorio", calibration_data.get("supplier", "Por definir") if calibration_data else "Por definir"),
        ("Frecuencia de Calibración", f"{instrument_data.get('calibration_frequency', instrument_data.get('Frecuencia de calibración', 'N/A'))} días"),
        ("Próxima Calibración", str(instrument_data.get("next_calibration_date", instrument_data.get("Próximo vencimiento", "N/A")))),
        ("Costo Estimado", f"${float(calibration_data.get('cost', 0)):.2f}" if calibration_data and calibration_data.get("cost") else "Por cotizar"),
    ]
    elements.append(_two_col_table(cal_info))
    elements.append(Spacer(1, 12))

    # Observations area
    elements.append(_section_title("📝 OBSERVACIONES"))
    elements.append(Spacer(1, 5))
    obs = calibration_data.get("observations", "").strip() if calibration_data else ""
    elements.append(Paragraph(obs if obs else "Sin observaciones.", styles["FieldValue"]))
    elements.append(Spacer(1, 8))

    # Lines for field entry
    obs_lines = Table(
        [[""] for _ in range(4)],
        colWidths=[19*cm], rowHeights=[12]*4
    )
    obs_lines.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce3ea")),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#dce3ea")),
    ]))
    elements.append(obs_lines)
    elements.append(Spacer(1, 20))

    elements.append(_signature_block())
    _footer(elements)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────
# PDF 4: REPORTE DETALLADO DE CALIBRACIÓN
# ─────────────────────────────────────────────

def generate_detailed_report(instrument_data: dict, calibrations_df: pd.DataFrame) -> BytesIO:
    """Generate comprehensive calibration report"""
    buffer = BytesIO()
    styles = get_styles()

    gage_id = instrument_data.get("gage_id", instrument_data.get("Id. de Instrumento", "N/A"))
    doc_number = f"RPT-{gage_id}-{datetime.now().strftime('%Y%m%d')}"
    date_str = datetime.now().strftime("%d/%m/%Y")

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=2*cm
    )

    elements = []
    elements += _header_table("REPORTE DETALLADO DE CALIBRACIÓN",
                               "Análisis Completo del Instrumento de Medición", doc_number, date_str)

    # Complete instrument data
    elements.append(_section_title("📋 DATOS COMPLETOS DEL INSTRUMENTO"))
    elements.append(Spacer(1, 3))
    elements.append(_two_col_table([
        ("ID de Instrumento", instrument_data.get("gage_id", instrument_data.get("Id. de Instrumento", "N/A"))),
        ("Descripción", instrument_data.get("description", instrument_data.get("Descripción", "N/A"))),
        ("Tipo", instrument_data.get("type", instrument_data.get("Tipo", "N/A"))),
        ("Estatus", instrument_data.get("status", instrument_data.get("Estatus", "N/A"))),
        ("N° de Serie", instrument_data.get("serial_number", instrument_data.get("N/S del Instrumento", "N/A"))),
        ("N° de Modelo", instrument_data.get("model_number", instrument_data.get("No.  de Modelo", "N/A"))),
        ("N° de Contabilidad", instrument_data.get("accounting_number", instrument_data.get("No. de Contabilidad", "N/A"))),
        ("Ubicación de Almacén", instrument_data.get("storage_location", instrument_data.get("Ubicación de Almacén", "N/A"))),
        ("Ubicación Actual", instrument_data.get("current_location", instrument_data.get("Ubicación Actual", "N/A"))),
        ("Persona Responsable", instrument_data.get("responsible_person", instrument_data.get("Persona responsable", "N/A"))),
        ("Custodio Actual", instrument_data.get("current_custodian", instrument_data.get("Custodio actual", "N/A"))),
        ("Frecuencia de Calibración", f"{instrument_data.get('calibration_frequency', instrument_data.get('Frecuencia de calibración', 'N/A'))} días"),
        ("Proveedor", instrument_data.get("supplier", "N/A")),
        ("Costo", f"${float(instrument_data.get('cost', 0)):.2f}" if instrument_data.get("cost") else "N/A"),
    ]))
    elements.append(Spacer(1, 10))

    # Statistics
    if not calibrations_df.empty:
        total_cals = len(calibrations_df)
        approved = len(calibrations_df[calibrations_df.get("result", pd.Series()) == "Aprobado"]) if "result" in calibrations_df.columns else 0
        rejected = total_cals - approved

        elements.append(_section_title("📊 ESTADÍSTICAS DE CALIBRACIÓN"))
        elements.append(Spacer(1, 3))

        stats_data = [
            ["Total Calibraciones", "Aprobadas", "Rechazadas", "% Conformidad"],
            [str(total_cals), str(approved), str(rejected),
             f"{(approved/total_cals*100):.1f}%" if total_cals > 0 else "N/A"]
        ]

        stat_t = Table(stats_data, colWidths=[4.75*cm]*4)
        stat_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dce3ea")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 1), (0, 1), GRAY_LIGHT),
            ("TEXTCOLOR", (1, 1), (1, 1), SUCCESS_GREEN),
            ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
            ("TEXTCOLOR", (2, 1), (2, 1), DANGER_RED),
            ("FONTNAME", (2, 1), (2, 1), "Helvetica-Bold"),
        ]))
        elements.append(stat_t)
        elements.append(Spacer(1, 10))

        # History table
        elements.append(_section_title("📅 HISTORIAL COMPLETO"))
        elements.append(Spacer(1, 3))
        elements += [generate_calibration_history(instrument_data, calibrations_df)]

    _footer(elements)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────
# PDF 5: REPORTE MSA
# ─────────────────────────────────────────────

def generate_msa_report(study_data: dict, results: dict, study_type: str = "GRR") -> BytesIO:
    """Generate MSA study report PDF"""
    buffer = BytesIO()
    styles = get_styles()

    gage_id = study_data.get("gage_id", "N/A")
    study_name = study_data.get("study_name", study_type)
    doc_number = f"MSA-{gage_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
    date_str = datetime.now().strftime("%d/%m/%Y")

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=2*cm
    )

    elements = []
    elements += _header_table(
        f"REPORTE MSA — {study_type.upper()}",
        f"Análisis del Sistema de Medición | {study_name}",
        doc_number, date_str
    )

    # Study info
    elements.append(_section_title("📋 INFORMACIÓN DEL ESTUDIO"))
    elements.append(Spacer(1, 3))
    elements.append(_two_col_table([
        ("ID de Instrumento",    gage_id),
        ("Tipo de Estudio",      study_type),
        ("Nombre del Estudio",   study_data.get("study_name", "N/A")),
        ("Operador / Analista",  study_data.get("operator", "N/A")),
        ("Característica",       study_data.get("characteristic", "N/A")),
        ("USL",                  study_data.get("specification_usl", "N/A")),
        ("LSL",                  study_data.get("specification_lsl", "N/A")),
        ("Tolerancia",           study_data.get("tolerance", "N/A")),
        ("Fecha",                date_str),
        ("Notas",                study_data.get("notes", "—")),
    ]))
    elements.append(Spacer(1, 10))

    # Results
    elements.append(_section_title("📊 RESULTADOS DEL ANÁLISIS"))
    elements.append(Spacer(1, 5))

    if results:
        result_rows = []
        for key, value in results.items():
            if isinstance(value, float):
                result_rows.append((str(key), f"{value:.4f}"))
            elif isinstance(value, dict):
                # Nested dict — flatten
                for sub_key, sub_val in value.items():
                    if isinstance(sub_val, float):
                        result_rows.append((f"{key} › {sub_key}", f"{sub_val:.4f}"))
                    else:
                        result_rows.append((f"{key} › {sub_key}", str(sub_val)))
            else:
                result_rows.append((str(key), str(value)))

        elements.append(_two_col_table(result_rows))
    else:
        elements.append(Paragraph("Sin resultados disponibles.", styles["FieldValue"]))

    elements.append(Spacer(1, 15))
    elements.append(_signature_block())
    _footer(elements)
    doc.build(elements)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────
# STREAMLIT UI
# ─────────────────────────────────────────────

def render_reports():
    """Main reports interface"""
    st.title("📄 Reportes — Generación de PDF")

    df = load_data()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📜 Certificado de Calibración",
        "📋 Historial de Calibraciones",
        "🔧 Orden de Trabajo",
        "📊 Reporte Detallado"
    ])

    # ── Shared instrument selector ──
    def _instrument_selector(key: str):
        if df.empty:
            st.warning("No hay instrumentos registrados.")
            return None, None
        ids = df["Id. de Instrumento"].dropna().tolist()
        desc = df.set_index("Id. de Instrumento")["Descripción"].to_dict()
        options = [f"{i} — {desc.get(i, '')}" for i in ids]
        sel = st.selectbox("Instrumento", options, key=key)
        gage_id = sel.split(" — ")[0] if sel else None
        inst = get_instrument_by_id(gage_id) if gage_id else None
        return gage_id, inst

    # ── Shared calibration selector ──
    def _cal_selector(gage_id: str, key: str):
        cal_df = get_calibrations(gage_id=gage_id)
        if cal_df.empty:
            st.info("No hay calibraciones registradas para este instrumento.")
            return None, None
        labels = [
            f"{row.get('calibration_date', 'N/A')} — {row.get('result', 'N/A')}"
            for _, row in cal_df.iterrows()
        ]
        sel_label = st.selectbox("Calibración", labels, key=key)
        idx = labels.index(sel_label)
        return sel_label, cal_df.iloc[idx].to_dict()

    # ─────────────────────────────────
    with tab1:
        st.markdown("### Certificado de Calibración")
        gage_id, inst = _instrument_selector("cert_inst")
        if inst:
            with st.expander("📋 Vista previa del instrumento"):
                st.json({k: str(v) for k, v in inst.items()})
            
            use_cal = st.checkbox("Incluir datos de calibración específica", value=True)
            cal_data = None
            if use_cal and gage_id:
                _, cal_data = _cal_selector(gage_id, "cert_cal")

            if st.button("📥 Generar Certificado PDF", type="primary", use_container_width=True):
                with st.spinner("Generando PDF..."):
                    pdf_buf = generate_calibration_certificate(inst, cal_data)
                fname = f"Certificado_Calibracion_{gage_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
                st.download_button(
                    label="⬇️ Descargar Certificado PDF",
                    data=pdf_buf,
                    file_name=fname,
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ PDF generado exitosamente.")

    # ─────────────────────────────────
    with tab2:
        st.markdown("### Historial de Calibraciones")
        gage_id, inst = _instrument_selector("hist_inst")
        if inst and gage_id:
            cals = get_calibrations(gage_id=gage_id)
            st.markdown(f"**{len(cals)} calibraciones** encontradas para `{gage_id}`")

            if st.button("📥 Generar Historial PDF", type="primary", use_container_width=True):
                with st.spinner("Generando PDF..."):
                    pdf_buf = generate_calibration_history(inst, cals)
                fname = f"Historial_Calibracion_{gage_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
                st.download_button(
                    label="⬇️ Descargar Historial PDF",
                    data=pdf_buf,
                    file_name=fname,
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ PDF generado.")

    # ─────────────────────────────────
    with tab3:
        st.markdown("### Orden de Trabajo de Calibración")
        gage_id, inst = _instrument_selector("ot_inst")
        if inst and gage_id:
            use_cal = st.checkbox("Incluir datos de calibración en la OT", value=False)
            cal_data = None
            if use_cal:
                _, cal_data = _cal_selector(gage_id, "ot_cal")

            if st.button("📥 Generar Orden de Trabajo PDF", type="primary", use_container_width=True):
                with st.spinner("Generando PDF..."):
                    pdf_buf = generate_work_order(inst, cal_data)
                fname = f"OT_Calibracion_{gage_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
                st.download_button(
                    label="⬇️ Descargar Orden de Trabajo PDF",
                    data=pdf_buf,
                    file_name=fname,
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ PDF generado.")

    # ─────────────────────────────────
    with tab4:
        st.markdown("### Reporte Detallado de Calibración")
        gage_id, inst = _instrument_selector("det_inst")
        if inst and gage_id:
            cals = get_calibrations(gage_id=gage_id)
            st.markdown(f"**{len(cals)} calibraciones** en el historial de `{gage_id}`")

            if st.button("📥 Generar Reporte Detallado PDF", type="primary", use_container_width=True):
                with st.spinner("Generando PDF..."):
                    pdf_buf = generate_detailed_report(inst, cals)
                fname = f"Reporte_Detallado_{gage_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
                st.download_button(
                    label="⬇️ Descargar Reporte Detallado PDF",
                    data=pdf_buf,
                    file_name=fname,
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ PDF generado.")


if __name__ == "__main__":
    render_reports()
