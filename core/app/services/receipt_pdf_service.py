"""
Canonical receipt PDF rendering service for Technoreboot.

Reuses the exact canonical presentation and business text from
inventory-sales-module/app/templates/sale_receipt_preview.html.
Produces deterministic, print-ready PDF documents using ReportLab and DejaVu Sans fonts.
"""

import io
import os
from typing import Any, Dict, List, Optional
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

# Payment method labels mapping
PAYMENT_METHODS_LABELS = {
    "cash": "Наличные",
    "card": "Банковская карта",
    "card_terminal": "Банковская карта",
    "sbp": "СБП (Система быстрых платежей)",
    "transfer": "Безналичный перевод",
    "other": "Другое",
    "unspecified": "Не указано",
}

_FONTS_REGISTERED = False


def _register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return

    candidate_dirs = [
        os.path.join(os.path.dirname(__file__), "..", "static", "fonts"),
        os.path.join(os.path.dirname(__file__), "..", "..", "admin-shell", "app", "static", "fonts"),
        os.path.abspath("core/app/static/fonts"),
        os.path.abspath("admin-shell/app/static/fonts"),
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
    sale: Dict[str, Any],
    org_settings: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Generate a deterministic, print-ready PDF receipt for the given sale.
    sale: dictionary representing the sale snapshot (from core DB or schema)
    org_settings: dictionary of organization settings
    """
    _register_fonts()
    font_norm, font_bold = _get_font_names()

    if org_settings is None:
        org_settings = {}

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
    style_banner_cancelled = ParagraphStyle(
        "BannerCancel",
        fontName=font_bold,
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.white,
    )
    style_banner_superseded = ParagraphStyle(
        "BannerSuperseded",
        fontName=font_bold,
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.white,
    )
    style_banner_reissued = ParagraphStyle(
        "BannerReissued",
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
    org_name = org_settings.get("organization_name") or "Организация не задана"
    inn = org_settings.get("inn") or "—"
    address = org_settings.get("address") or "—"
    phone = org_settings.get("phone") or "—"

    elements.append(Paragraph(f"<b>{org_name}</b>", style_org_title))
    elements.append(Paragraph(f"ИНН: {inn}<br/>Адрес: {address}<br/>Телефон: {phone}", style_org_details))
    elements.append(Spacer(1, 10))

    # 2. Status Banners (Cancelled / Superseded / Reissued)
    status = (sale.get("status") or "completed").lower()
    sale_id = sale.get("id") or sale.get("sale_id") or 0
    created_at_raw = str(sale.get("created_at") or "")
    created_date = created_at_raw[:10] if len(created_at_raw) >= 10 else "—"

    if status in ["canceled", "cancelled"]:
        cancel_date = str(sale.get("cancelled_at") or "")[:10]
        banner_text = f"АРХИВНЫЙ ЧЕК — ПРОДАЖА №{sale_id} ОТМЕНЕНА ({cancel_date})"
        banner_table = Table(
            [[Paragraph(banner_text, style_banner_cancelled)]],
            colWidths=[content_width],
        )
        banner_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#dc3545")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(banner_table)
        elements.append(Spacer(1, 6))
    elif status == "superseded":
        sup_id = sale.get("superseded_by_sale_id") or sale.get("replaced_by_sale_id") or ""
        banner_text = f"АРХИВНЫЙ ЧЕК — ПРОДАЖА №{sale_id} ЗАМЕНЕНА (ПОВТОРНАЯ ПРОДАЖА №{sup_id})"
        banner_table = Table(
            [[Paragraph(banner_text, style_banner_superseded)]],
            colWidths=[content_width],
        )
        banner_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#6c757d")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(banner_table)
        elements.append(Spacer(1, 6))
    elif status == "reissued":
        src_id = sale.get("source_sale_id") or sale.get("original_sale_id") or ""
        banner_text = f"ПОВТОРНО ОФОРМЛЕННАЯ ПРОДАЖА (НА ОСНОВЕ ПРОДАЖИ №{src_id})"
        banner_table = Table(
            [[Paragraph(banner_text, style_banner_reissued)]],
            colWidths=[content_width],
        )
        banner_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#007bff")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(banner_table)
        elements.append(Spacer(1, 6))

    # 3. Document Title
    elements.append(Paragraph(f"Товарный чек № {sale_id} от {created_date}", style_title))
    rev_count = sale.get("revision_count") or 0
    if rev_count > 0:
        elements.append(Paragraph(f"Продажа скорректирована — ревизия №{rev_count}", style_revision))
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

    items = sale.get("items") or []
    if items:
        for idx, item in enumerate(items, start=1):
            if isinstance(item, dict):
                title = item.get("title") or f"Товар #{item.get('product_id')}"
                code = str(item.get("sku") or item.get("barcode") or item.get("product_id") or "")
                qty = item.get("quantity") or 1
                price = float(item.get("price") or item.get("unit_price") or 0.0)
            else:
                title = getattr(item, "title", "") or f"Товар #{getattr(item, 'product_id', '')}"
                code = str(getattr(item, "sku", None) or getattr(item, "barcode", None) or getattr(item, "product_id", ""))
                qty = getattr(item, "quantity", 1) or 1
                price = float(getattr(item, "price", None) or getattr(item, "unit_price", 0.0) or 0.0)
            
            line_sum = price * qty
            table_rows.append([
                Paragraph(str(idx), style_cell),
                Paragraph(title, style_cell),
                Paragraph(code, style_cell),
                Paragraph("шт", style_cell),
                Paragraph(str(qty), style_cell_r),
                Paragraph(f"{price:.2f}", style_cell_r),
                Paragraph(f"{line_sum:.2f}", style_cell_r),
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
    total_amt = float(sale.get("total_amount") or 0.0)
    raw_pm = str(sale.get("payment_method") or "unspecified").strip().lower()
    pm_label = PAYMENT_METHODS_LABELS.get(raw_pm, sale.get("payment_label") or raw_pm)

    summary_rows = [
        [Paragraph("Итого:", style_summary_lbl), Paragraph(f"{total_amt:.2f}", style_summary_val)],
        [Paragraph("Предоплата:", style_summary_lbl), Paragraph("0.00", style_summary_val)],
        [Paragraph("К оплате:", style_summary_lbl), Paragraph(f"{total_amt:.2f}", style_summary_val)],
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
        f"Всего наименований: <b>{len(items)}</b><br/>"
        f"Сумма: <b>{total_amt:.2f} ₽</b><br/>"
        f"Способ поступления денег: <b>{pm_label}</b>"
    )
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(meta_text, style_summary_meta))
    elements.append(Spacer(1, 14))

    # 6. Signatures (KeepTogether to prevent breaking across pages)
    cashier = (
        sale.get("cashier_name")
        or org_settings.get("default_cashier_name")
        or "Продавец"
    )
    customer = org_settings.get("default_customer_label") or "Частное лицо"

    sig_col_w = (content_width - 30) / 2
    sig_rows = [
        [
            Paragraph("Отпустил:", style_sig_lbl),
            Paragraph("Покупатель:", style_sig_lbl),
        ],
        [
            Paragraph("_____________________________", style_sig_lbl),
            Paragraph(f"<b>{customer}</b>", style_sig_lbl),
        ],
        [
            Paragraph(f"({cashier})", style_sig_actor),
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
    warranty_enabled = bool(sale.get("warranty_enabled", True))
    warranty_days = sale.get("warranty_days") or 30

    warranty_elements = [
        Paragraph("Гарантийные условия", style_warranty_title),
        Spacer(1, 4),
    ]

    if warranty_enabled:
        warranty_text_body = (
            org_settings.get("warranty_text")
            or "При обнаружении неисправности в течение гарантийного срока производится бесплатный ремонт или обмен."
        )
        # In desktop template: org_settings.warranty_text.split('\n')[1:]|join('\n')
        lines = warranty_text_body.split("\n")
        joined_terms = "<br/>".join(l.strip() for l in lines if l.strip())
        w_html = (
            f"На все Б/У товары предоставляется гарантия <b>{warranty_days} дней</b>.<br/>"
            f"{joined_terms}"
        )
        warranty_elements.append(Paragraph(w_html, style_warranty_body))
    else:
        no_w_text = (
            org_settings.get("no_warranty_text")
            or "Товар продаётся без гарантии, в том состоянии, в котором есть.<br/>Покупатель внимательно осмотрел товар при покупке."
        )
        warranty_elements.append(Paragraph(no_w_text.replace("\n", "<br/>"), style_warranty_no))

    warranty_elements.append(Spacer(1, 8))
    buyer_sign_html = (
        "Подпись покупателя:<br/>"
        "С условиями ознакомился и согласен: ____________________________________"
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
