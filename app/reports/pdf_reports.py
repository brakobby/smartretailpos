"""
SmartRetail POS — PDF Report Generator (ReportLab)

Generates:
  - Sales report PDF
  - Inventory report PDF
  - Customer debt report PDF
  - Supplier balance report PDF
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import List

from app.config.settings import (
    BUSINESS_NAME, BUSINESS_ADDRESS, BUSINESS_PHONE,
    CURRENCY_SYMBOL, REPORTS_DIR,
)
from app.utils.helpers import format_currency, format_datetime

logger = logging.getLogger(__name__)


def _get_reportlab():
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph,
            Spacer, HRFlowable,
        )
        return True, {
            "colors": colors, "A4": A4, "landscape": landscape,
            "getSampleStyleSheet": getSampleStyleSheet,
            "ParagraphStyle": ParagraphStyle, "mm": mm,
            "SimpleDocTemplate": SimpleDocTemplate, "Table": Table,
            "TableStyle": TableStyle, "Paragraph": Paragraph,
            "Spacer": Spacer, "HRFlowable": HRFlowable,
        }
    except ImportError:
        return False, {}


def _header_footer(rl, title: str, subtitle: str = "") -> list:
    """Return a list of flowables for the report header."""
    styles = rl["getSampleStyleSheet"]()
    mm = rl["mm"]
    Paragraph = rl["Paragraph"]
    Spacer    = rl["Spacer"]
    HRFlowable = rl["HRFlowable"]
    colors    = rl["colors"]

    title_style = rl["ParagraphStyle"](
        "ReportTitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=4,
    )
    sub_style = rl["ParagraphStyle"](
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748B"),
    )
    biz_style = rl["ParagraphStyle"](
        "BizName",
        parent=styles["Normal"],
        fontSize=13,
        textColor=colors.HexColor("#2563EB"),
        fontName="Helvetica-Bold",
    )

    return [
        Paragraph(BUSINESS_NAME, biz_style),
        Paragraph(BUSINESS_ADDRESS or "", sub_style),
        Spacer(1, 4 * mm),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB")),
        Spacer(1, 3 * mm),
        Paragraph(title, title_style),
        Paragraph(subtitle or f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}", sub_style),
        Spacer(1, 5 * mm),
    ]


def generate_sales_report_pdf(sales, date_from=None, date_to=None) -> Path:
    """Generate a sales report PDF and return the file path."""
    ok, rl = _get_reportlab()
    if not ok:
        raise ImportError("reportlab is not installed. Run: pip install reportlab")

    filename = REPORTS_DIR / f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = rl["SimpleDocTemplate"](
        str(filename),
        pagesize=rl["A4"],
        rightMargin=15 * rl["mm"],
        leftMargin=15 * rl["mm"],
        topMargin=20 * rl["mm"],
        bottomMargin=15 * rl["mm"],
    )

    colors = rl["colors"]
    Table  = rl["Table"]
    TS     = rl["TableStyle"]
    P      = rl["Paragraph"]
    Spacer = rl["Spacer"]
    styles = rl["getSampleStyleSheet"]()
    mm     = rl["mm"]

    period = ""
    if date_from and date_to:
        period = f"{date_from} → {date_to}"

    story = _header_footer(rl, "Sales Report", period)

    # Summary row
    total_sales  = sum(s.total_amount for s in sales)
    total_paid   = sum(s.amount_paid for s in sales)
    total_balance = sum(s.balance for s in sales)

    summary_data = [
        ["Total Sales", "Total Paid", "Outstanding", "Transactions"],
        [
            format_currency(total_sales),
            format_currency(total_paid),
            format_currency(total_balance),
            str(len(sales)),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[45 * mm] * 4)
    summary_table.setStyle(TS([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, 0), 10),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#DBEAFE")),
        ("FONTNAME",   (0, 1), (-1, 1), "Helvetica-Bold"),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#DBEAFE")]),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(rl["Spacer"](1, 8 * mm))

    # Detail table
    headers = ["Invoice", "Date", "Customer", "Payment", "Total", "Paid", "Balance"]
    rows = [headers]
    for s in sales:
        cust = s.customer.name if s.customer else "Walk-in"
        rows.append([
            s.invoice_number[:18],
            s.sale_date.strftime("%d/%m/%Y %H:%M"),
            cust[:20],
            s.payment_type.value,
            format_currency(s.total_amount),
            format_currency(s.amount_paid),
            format_currency(s.balance),
        ])

    col_widths = [38 * mm, 30 * mm, 35 * mm, 22 * mm, 28 * mm, 28 * mm, 28 * mm]
    detail_table = Table(rows, colWidths=col_widths, repeatRows=1)
    detail_table.setStyle(TS([
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
        ("ALIGN",        (4, 0), (-1, -1), "RIGHT"),
        ("ALIGN",        (0, 0), (3, -1), "LEFT"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
    ]))
    story.append(detail_table)
    doc.build(story)
    logger.info("Sales report PDF generated: %s", filename)
    return filename


def generate_inventory_report_pdf(products) -> Path:
    """Generate inventory stock report PDF."""
    ok, rl = _get_reportlab()
    if not ok:
        raise ImportError("reportlab not installed.")

    filename = REPORTS_DIR / f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    colors = rl["colors"]
    Table  = rl["Table"]
    TS     = rl["TableStyle"]
    mm     = rl["mm"]

    doc = rl["SimpleDocTemplate"](
        str(filename), pagesize=rl["landscape"](rl["A4"]),
        rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=20 * mm, bottomMargin=15 * mm,
    )

    story = _header_footer(rl, "Inventory Stock Report")

    headers = ["Barcode", "Product Name", "Category", "Cost", "Price", "Stock", "Min Stock", "Stock Value", "Status"]
    rows = [headers]
    for p in products:
        cat  = p.category.name if p.category else "—"
        status = "OUT" if p.quantity == 0 else ("LOW" if p.quantity <= p.minimum_quantity else "OK")
        rows.append([
            p.barcode, p.product_name[:30], cat,
            format_currency(p.cost_price),
            format_currency(p.selling_price),
            f"{p.quantity:.0f}", f"{p.minimum_quantity:.0f}",
            format_currency(p.cost_price * p.quantity),
            status,
        ])

    col_widths = [30*mm, 55*mm, 30*mm, 22*mm, 22*mm, 18*mm, 22*mm, 28*mm, 18*mm]
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TS([
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
        ("ALIGN",        (3, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    doc.build(story)
    return filename
