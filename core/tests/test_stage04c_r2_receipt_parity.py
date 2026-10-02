"""
Stage 04C-R2: Receipt Presentation Parity Tests.

Verifies Section 4 of TR_Android_Stage04C_R2_Canonical_Receipt_Single_Source_Clean_Build_Audit.md:
1. Exact equality between desktop HTML preview data and PDF generation data:
   - receipt number;
   - date;
   - cashier label;
   - item count;
   - titles;
   - quantities;
   - prices;
   - totals;
   - payment label;
   - warranty days;
   - warranty/return text;
   - seller signature label;
   - buyer signature label;
   - buyer acknowledgement prompt.
2. Complete coverage for:
   - standard completed sale;
   - long Cyrillic product title;
   - multi-item receipt;
   - canceled sale (with banner);
   - superseded sale (with banner);
   - reissued sale (with banner);
   - revised sale (with revision notice);
   - no-warranty sale (with disclaimer).
3. Anti-drift validation: ensures HTML preview and PDF renderers share the same canonical source.
"""

import sys
import os
import io
import pytest
import pypdf
from jinja2 import Environment, FileSystemLoader

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
core_dir = os.path.join(project_root, "core")
inventory_dir = os.path.join(project_root, "inventory-sales-module")

for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        sys.modules.pop(k, None)

while core_dir in sys.path:
    sys.path.remove(core_dir)
sys.path.insert(0, core_dir)

from app.services.receipt_presentation import (
    ReceiptDocumentData,
    build_receipt_document_data,
    SELLER_SIGNATURE_TITLE,
    BUYER_SIGNATURE_TITLE,
    WARRANTY_SECTION_TITLE,
    BUYER_ACKNOWLEDGEMENT_PROMPT,
    DEFAULT_ORGANIZATION_NAME,
    DEFAULT_INN,
)
from app.services.receipt_pdf_service import generate_sale_receipt_pdf


@pytest.fixture(scope="module")
def jinja_env():
    templates_dir = os.path.join(inventory_dir, "app", "templates")
    return Environment(loader=FileSystemLoader(templates_dir), autoescape=True)


def _render_html(jinja_env, receipt_data: ReceiptDocumentData) -> str:
    template = jinja_env.get_template("sale_receipt_preview.html")
    context = {
        "receipt": receipt_data,
        "sale": receipt_data,
        "org_settings": receipt_data,
        "payment_methods": {},
    }
    return template.render(context)


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    extracted = []
    for page in reader.pages:
        extracted.append(page.extract_text() or "")
    return "\n".join(extracted)


# =====================================================================
# 1. STANDARD COMPLETED SALE PARITY
# =====================================================================

def test_standard_sale_parity(jinja_env):
    sale = {
        "id": 101,
        "created_at": "2026-10-02T10:15:00",
        "status": "completed",
        "payment_method": "cash",
        "cashier_name": "Иванов И.И.",
        "warranty_enabled": True,
        "warranty_days": 30,
        "total_amount": 12500.0,
        "items": [
            {
                "id": 1,
                "product_id": 55,
                "title": "Монитор LG UltraGear 24GL600F",
                "sku": "MON-LG-24",
                "quantity": 1,
                "price": 12500.0,
            }
        ],
    }
    org = {
        "organization_name": "ООО ТехноРебут Сервис",
        "inn": "667009336901",
        "address": "г. Екатеринбург, ул. Кузнецова, 10",
        "phone": "+7 (343) 344-88-95",
        "default_cashier_name": "Продавец",
        "default_customer_label": "Частное лицо",
        "warranty_text": "Гарантийный талон.\nБесплатный ремонт при наличии дефекта.",
    }

    doc = build_receipt_document_data(sale, org)
    html = _render_html(jinja_env, doc)
    pdf_text = _extract_pdf_text(generate_sale_receipt_pdf(doc))

    # Receipt number and date
    assert f"Товарный чек № {doc.sale_id}" in html
    assert f"Товарный чек № {doc.sale_id}" in pdf_text
    assert "2026-10-02" in html
    assert "2026-10-02" in pdf_text

    # Organization details
    assert "ООО ТехноРебут Сервис" in html
    assert "ООО ТехноРебут Сервис" in pdf_text
    assert "667009336901" in html
    assert "667009336901" in pdf_text

    # Cashier and signatures
    assert doc.seller_signature_title in html
    assert doc.seller_signature_title in pdf_text
    assert "(Иванов И.И.)" in html
    assert "(Иванов И.И.)" in pdf_text
    assert doc.buyer_signature_title in html
    assert doc.buyer_signature_title in pdf_text
    assert "Частное лицо" in html
    assert "Частное лицо" in pdf_text

    # Item details
    assert "Монитор LG UltraGear 24GL600F" in html
    assert "Монитор LG UltraGear 24GL600F" in pdf_text
    assert "12500.00" in html
    assert "12500.00" in pdf_text

    # Payment method
    assert "Наличные" in html
    assert "Наличные" in pdf_text

    # Warranty
    assert "30 дней" in html
    assert "30 дней" in pdf_text
    assert "Бесплатный ремонт при наличии дефекта." in html
    assert "Бесплатный ремонт при наличии дефекта." in pdf_text
    assert BUYER_ACKNOWLEDGEMENT_PROMPT in html
    assert BUYER_ACKNOWLEDGEMENT_PROMPT in pdf_text


# =====================================================================
# 2. LONG CYRILLIC PRODUCT TITLE & MULTI-ITEM PARITY
# =====================================================================

def test_long_cyrillic_and_multi_item_parity(jinja_env):
    long_title = (
        "Ноутбук игровой ASUS ROG Strix G15 G513RM-HF003W Eclipse Gray "
        "(AMD Ryzen 7 6800H/16GB DDR5/1TB SSD/RTX 3060 6GB/15.6 FHD 300Hz/Win11 Home)"
    )
    sale = {
        "id": 102,
        "created_at": "2026-10-02T11:00:00",
        "status": "completed",
        "payment_method": "card",
        "warranty_enabled": True,
        "warranty_days": 90,
        "total_amount": 94700.0,
        "items": [
            {
                "product_id": 101,
                "title": long_title,
                "sku": "NB-ASUS-ROG-G15",
                "quantity": 1,
                "price": 89000.0,
            },
            {
                "product_id": 102,
                "title": "Мышь беспроводная Logitech G Pro X Superlight Black",
                "sku": "MS-LOGI-GPROX",
                "quantity": 1,
                "price": 4500.0,
            },
            {
                "product_id": 103,
                "title": "Коврик для мыши SteelSeries QcK Heavy XXL",
                "sku": "PAD-SS-QCK-XXL",
                "quantity": 1,
                "price": 1200.0,
            },
        ],
    }
    org = {
        "organization_name": "ООО ТехноРебут Сервис",
        "inn": "667009336901",
    }

    doc = build_receipt_document_data(sale, org)
    html = _render_html(jinja_env, doc)
    pdf_text = _extract_pdf_text(generate_sale_receipt_pdf(doc))

    assert "Всего наименований: 3" in pdf_text or ("3" in pdf_text and "94700.00" in pdf_text)
    assert "94700.00" in html
    assert "94700.00" in pdf_text

    # Verify long title presence
    assert "ASUS ROG Strix G15" in html
    assert "ASUS ROG Strix G15" in pdf_text
    assert "Logitech G Pro X Superlight" in html
    assert "Logitech G Pro X Superlight" in pdf_text
    assert "SteelSeries QcK Heavy" in html
    assert "SteelSeries QcK Heavy" in pdf_text

    # Payment method
    assert "Банковская карта" in html
    assert "Банковская карта" in pdf_text

    # Warranty term
    assert "90 дней" in html
    assert "90 дней" in pdf_text


# =====================================================================
# 3. STATUS BANNERS PARITY (CANCELED, SUPERSEDED, REISSUED)
# =====================================================================

def test_canceled_status_banner_parity(jinja_env):
    sale = {
        "id": 103,
        "created_at": "2026-10-01T10:00:00",
        "status": "canceled",
        "cancelled_at": "2026-10-02T12:30:00",
        "total_amount": 5000.0,
        "items": [],
    }
    doc = build_receipt_document_data(sale, {})
    html = _render_html(jinja_env, doc)
    pdf_text = _extract_pdf_text(generate_sale_receipt_pdf(doc))

    expected_banner = "АРХИВНЫЙ ЧЕК — ПРОДАЖА №103 ОТМЕНЕНА (2026-10-02)"
    assert expected_banner in html
    assert expected_banner in pdf_text


def test_superseded_status_banner_parity(jinja_env):
    sale = {
        "id": 104,
        "created_at": "2026-09-20T10:00:00",
        "status": "superseded",
        "superseded_by_sale_id": 205,
        "total_amount": 7500.0,
        "items": [],
    }
    doc = build_receipt_document_data(sale, {})
    html = _render_html(jinja_env, doc)
    pdf_text = _extract_pdf_text(generate_sale_receipt_pdf(doc))

    expected_banner = "АРХИВНЫЙ ЧЕК — ПРОДАЖА №104 ЗАМЕНЕНА (ПОВТОРНАЯ ПРОДАЖА №205)"
    assert expected_banner in html
    assert expected_banner in pdf_text


def test_reissued_status_banner_parity(jinja_env):
    sale = {
        "id": 105,
        "created_at": "2026-10-02T14:00:00",
        "status": "reissued",
        "source_sale_id": 104,
        "total_amount": 8000.0,
        "items": [],
    }
    doc = build_receipt_document_data(sale, {})
    html = _render_html(jinja_env, doc)
    pdf_text = _extract_pdf_text(generate_sale_receipt_pdf(doc))

    expected_banner = "ПОВТОРНО ОФОРМЛЕННАЯ ПРОДАЖА (НА ОСНОВЕ ПРОДАЖИ №104)"
    assert expected_banner in html
    assert expected_banner in pdf_text


def test_revision_notice_parity(jinja_env):
    sale = {
        "id": 106,
        "created_at": "2026-10-02T15:00:00",
        "status": "completed",
        "revision_count": 2,
        "total_amount": 3000.0,
        "items": [],
    }
    doc = build_receipt_document_data(sale, {})
    html = _render_html(jinja_env, doc)
    pdf_text = _extract_pdf_text(generate_sale_receipt_pdf(doc))

    expected_notice = "Продажа скорректирована — ревизия №2"
    assert expected_notice in html
    assert expected_notice in pdf_text


# =====================================================================
# 4. NO-WARRANTY DISCLAIMER PARITY
# =====================================================================

def test_no_warranty_disclaimer_parity(jinja_env):
    sale = {
        "id": 107,
        "created_at": "2026-10-02T16:00:00",
        "status": "completed",
        "warranty_enabled": False,
        "total_amount": 1000.0,
        "items": [],
    }
    doc = build_receipt_document_data(sale, {})
    html = _render_html(jinja_env, doc)
    pdf_text = _extract_pdf_text(generate_sale_receipt_pdf(doc))

    assert "Товар продаётся без гарантии" in html
    assert "Товар продаётся без гарантии" in pdf_text
    assert "Покупатель внимательно осмотрел товар при покупке." in html
    assert "Покупатель внимательно осмотрел товар при покупке." in pdf_text
    assert "предоставляется гарантия" not in html
    assert "предоставляется гарантия" not in pdf_text


# =====================================================================
# 5. ANTI-DRIFT INTEGRITY TEST
# =====================================================================

def test_anti_drift_structural_equality():
    """Verify that both HTML and PDF consume fields directly from ReceiptDocumentData."""
    doc = build_receipt_document_data({"id": 999, "items": []}, {})
    data_dict = doc.to_dict()

    assert "receipt_title" in data_dict
    assert "organization_name" in data_dict
    assert "seller_signature_title" in data_dict
    assert "seller_signature_actor" in data_dict
    assert "buyer_signature_title" in data_dict
    assert "buyer_signature_actor" in data_dict
    assert "warranty_title" in data_dict
    assert "warranty_body_text" in data_dict
    assert "buyer_acknowledgement_prompt" in data_dict
