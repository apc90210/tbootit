"""
Canonical receipt PDF rendering service for Technoreboot.

Consumes the single canonical ReceiptDocumentData presentation model from
core.app.services.receipt_presentation.
Produces deterministic, print-ready PDF documents using ReportLab and DejaVu Sans fonts.
"""

import io
import os
from typing import Any, Dict, List, Optional, Union
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.services.receipt_presentation import (
    ReceiptDocumentData,
    build_receipt_document_data,
    PAYMENT_METHODS_LABELS,
)

_FONTS_REGISTERED = False


def _register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return

    candidate_dirs = [
        os.path.join(os.path.dirname(__file__), "..", "static", "fonts"),
        os.path.abspath("core/app/static/fonts"),
        "/app/app/static/fonts",
        "C:/Windows/Fonts",
    ]

    regular_path = None
    bold_path = None

    for d in candidate_dirs:
        reg = os.path.join(d, "DejaVuSans.ttf")
        bld = os.path.join(d, "DejaVuSans-Bold.ttf")
        if os.path.exists(reg) and os.path.exists(bld):
            regular_path = reg
            bold_path = bld
            break

    if regular_path and bold_path:
        pdfmetrics.registerFont(TTFont("TechnoSans", regular_path))
        pdfmetrics.registerFont(TTFont("TechnoSans-Bold", bold_path))
        _FONTS_REGISTERED = True
    else:
        # Fallback to standard Helvetica if TTF not found
        _FONTS_REGISTERED = True


def _get_font_names():
    _register_fonts()
    try:
        pdfmetrics.getFont("TechnoSans")
        return "TechnoSans", "TechnoSans-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def generate_sale_receipt_pdf(
    sale: Union[ReceiptDocumentData, Dict[str, Any], Any],
    org_settings: Optional[Union[Dict[str, Any], Any]] = None,
) -> bytes:
    """
    Generate a deterministic, print-ready PDF receipt.
    Accepts either a canonical ReceiptDocumentData instance or raw sale/org dicts.
    """
    _register_fonts()
    font_norm, font_bold = _get_font_names()

    if isinstance(sale, ReceiptDocumentData):
        receipt = sale
    else:
        receipt = build_receipt_document_data(sale, org_settings)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    content_width = A4[0] - 72  # 595.27 - 72 = 523.27 pt

    # Paragraph Styles
    style_org_title = ParagraphStyle(
        "OrgTitle",
        fontName=font_bold,
        fontSize=11,
        leading=15,
        alignment=1,  # Center
    )
    style_org_details = ParagraphStyle(
        "OrgDetails",
        fontName=font_norm,
        fontSize=9,
        leading=13,
        alignment=1,
    )
    style_title = ParagraphStyle(
        "Title",
        fontName=font_bold,
        fontSize=14,
        leading=18,
        alignment=1,
    )
    style_revision = ParagraphStyle(
        "Revision",
        fontName=font_norm,
        fontSize=8,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#555555"),
    )
    style_banner = ParagraphStyle(
        "Banner",
        fontName=font_bold,
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.white,
    )
    style_th = ParagraphStyle(
        "TableHead",
        fontName=font_bold,
        fontSize=8,
        leading=11,
        alignment=0,
    )
    style_th_r = ParagraphStyle(
        "TableHeadR",
        fontName=font_bold,
        fontSize=8,
        leading=11,
        alignment=2,  # Right
    )
    style_cell = ParagraphStyle(
        "TableCell",
        fontName=font_norm,
        fontSize=8,
        leading=11,
        alignment=0,
    )
    style_cell_r = ParagraphStyle(
        "TableCellR",
        fontName=font_norm,
        fontSize=8,
        leading=11,
        alignment=2,
    )
    style_summary_lbl = ParagraphStyle(
        "SummLbl",
        fontName=font_norm,
        fontSize=9,
        leading=13,
        alignment=2,
    )
    style_summary_val = ParagraphStyle(
        "SummVal",
        fontName=font_bold,
        fontSize=9,
        leading=13,
        alignment=2,
    )
    style_summary_meta = ParagraphStyle(
        "SummMeta",
        fontName=font_norm,
        fontSize=9,
        leading=14,
    )
    style_sig_lbl = ParagraphStyle(
        "SigLbl",
        fontName=font_norm,
        fontSize=9,
        leading=13,
    )
    style_sig_actor = ParagraphStyle(
        "SigActor",
        fontName=font_norm,
        fontSize=8,
        leading=11,
        alignment=1,
    )
    style_warranty_title = ParagraphStyle(
        "WarrantyTitle",
        fontName=font_bold,
        fontSize=9,
        leading=13,
        alignment=1,
    )
    style_warranty_body = ParagraphStyle(
        "WarrantyBody",
        fontName=font_norm,
        fontSize=8,
        leading=12,
    )
    style_warranty_no = ParagraphStyle(
        "WarrantyNo",
        fontName=font_bold,
        fontSize=8,
        leading=12,
        textColor=colors.HexColor("#cc0000"),
    )

    elements = []

    # 1. Organization Header
    elements.append(Paragraph(f"<b>{receipt.organization_name}</b>", style_org_title))
    elements.append(
        Paragraph(
            f"ИНН: {receipt.inn}<br/>Адрес: {receipt.address}<br/>Телефон: {receipt.phone}",
            style_org_details,
        )
    )
    elements.append(Spacer(1, 10))

    # 2. Status Banners (Cancelled / Superseded / Reissued)
    if receipt.status_banner_text and receipt.status_banner_bg_color:
        banner_table = Table(
            [[Paragraph(receipt.status_banner_text, style_banner)]],
            colWidths=[content_width],
        )
        banner_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(receipt.status_banner_bg_color)),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(banner_table)
        elements.append(Spacer(1, 6))

    # 3. Document Title & Revision Notice
    elements.append(Paragraph(receipt.receipt_title, style_title))
    if receipt.revision_notice:
        elements.append(Paragraph(receipt.revision_notice, style_revision))
    elements.append(Spacer(1, 8))

    # 4. Items Table
    # Col widths sum to content_width (523.27 pt):
    # № (24), Наименование (235.27), Код (40), Ед. (30), Кол-во (40), Цена (74), Сумма (80)
    col_widths = [24, 235.27, 40, 30, 40, 74, 80]
    table_rows = [
        [
            Paragraph("№", style_th),
            Paragraph("Наименование", style_th),
            Paragraph("Код", style_th),
            Paragraph("Ед.", style_th),
            Paragraph("Кол-во", style_th_r),
            Paragraph("Цена", style_th_r),
            Paragraph("Сумма", style_th_r),
        ]
    ]

    if receipt.items:
        for item in receipt.items:
            table_rows.append([
                Paragraph(str(item.idx), style_cell),
                Paragraph(item.title, style_cell),
                Paragraph(item.code, style_cell),
                Paragraph(item.unit, style_cell),
                Paragraph(str(item.quantity), style_cell_r),
                Paragraph(item.price_formatted, style_cell_r),
                Paragraph(item.line_total_formatted, style_cell_r),
            ])
    else:
        table_rows.append([
            Paragraph("—", style_cell),
            Paragraph("Товары отсутствуют", style_cell),
            Paragraph("", style_cell),
            Paragraph("", style_cell),
            Paragraph("", style_cell_r),
            Paragraph("", style_cell_r),
            Paragraph("", style_cell_r),
        ])

    items_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
    items_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f9f9f9")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    elements.append(items_table)
    elements.append(Spacer(1, 10))

    # 5. Summary Table
    summary_rows = [
        [Paragraph("Итого:", style_summary_lbl), Paragraph(receipt.total_amount_formatted, style_summary_val)],
        [Paragraph("Предоплата:", style_summary_lbl), Paragraph(receipt.prepayment_formatted, style_summary_val)],
        [Paragraph("К оплате:", style_summary_lbl), Paragraph(receipt.to_pay_formatted, style_summary_val)],
    ]
    summary_table = Table(
        summary_rows,
        colWidths=[content_width - 100, 100],
    )
    summary_table.setStyle(
        TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )
    elements.append(summary_table)

    meta_text = (
        f"Всего наименований: <b>{receipt.total_items_count}</b><br/>"
        f"Сумма: <b>{receipt.total_amount_formatted} ₽</b><br/>"
        f"Способ поступления денег: <b>{receipt.payment_method_label}</b>"
    )
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(meta_text, style_summary_meta))
    elements.append(Spacer(1, 14))

    # 6. Signatures (KeepTogether to prevent breaking across pages)
    sig_col_w = (content_width - 30) / 2
    sig_rows = [
        [
            Paragraph(receipt.seller_signature_title, style_sig_lbl),
            Paragraph(receipt.buyer_signature_title, style_sig_lbl),
        ],
        [
            Paragraph("_____________________________", style_sig_lbl),
            Paragraph(f"<b>{receipt.buyer_signature_actor}</b>", style_sig_lbl),
        ],
        [
            Paragraph(receipt.seller_signature_actor, style_sig_actor),
            Paragraph("", style_sig_lbl),
        ],
    ]
    sig_table = Table(sig_rows, colWidths=[sig_col_w, sig_col_w])
    sig_table.setStyle(
        TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ])
    )

    # 7. Warranty Terms Box
    warranty_elements = [
        Paragraph(receipt.warranty_title, style_warranty_title),
        Spacer(1, 4),
    ]

    if receipt.warranty_enabled:
        body_html = receipt.warranty_body_text.replace("\n", "<br/>")
        if body_html:
            w_html = f"<b>{receipt.warranty_headline}</b><br/>{body_html}"
        else:
            w_html = f"<b>{receipt.warranty_headline}</b>"
        warranty_elements.append(Paragraph(w_html, style_warranty_body))
    else:
        no_w_text = receipt.warranty_body_text.replace("\n", "<br/>")
        warranty_elements.append(Paragraph(no_w_text, style_warranty_no))

    warranty_elements.append(Spacer(1, 8))
    buyer_sign_html = (
        f"{receipt.buyer_acknowledgement_title}<br/>"
        f"{receipt.buyer_acknowledgement_prompt} ____________________________________"
    )
    warranty_elements.append(Paragraph(buyer_sign_html, style_warranty_body))

    warranty_box = Table(
        [[warranty_elements]],
        colWidths=[content_width],
    )
    warranty_box.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.75, colors.black),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ])
    )

    footer_group = KeepTogether([
        sig_table,
        Spacer(1, 14),
        warranty_box,
    ])
    elements.append(footer_group)

    doc.build(elements)
    return buf.getvalue()
