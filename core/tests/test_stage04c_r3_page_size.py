"""
Stage 04C-R3: Canonical Receipt Page Size and MediaBox Regression Test.

Prevents future silent page-size drift between A4 and 80mm thermal receipt formats.
Proves that:
1. Canonical ReportLab PDF generator strictly produces ISO A4 (595.28 x 841.89 pt / 210 x 297 mm, portrait).
2. Core HTTP endpoint /api/sales/{sale_id}/receipt/print produces exact ISO A4 PDF.
3. Android ReceiptPrintHelper strictly declares PrintAttributes.MediaSize.ISO_A4.
"""

import sys
import os
import io
import pytest
from decimal import Decimal
import pypdf
from fastapi.testclient import TestClient

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
core_dir = os.path.join(project_root, "core")

for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        sys.modules.pop(k, None)

while core_dir in sys.path:
    sys.path.remove(core_dir)
sys.path.insert(0, core_dir)

from app.main import app
from app.database import SessionLocal
from app import models
from app.services.receipt_pdf_service import generate_sale_receipt_pdf
from app.services.receipt_presentation import build_receipt_document_data

client = TestClient(app)

# Canonical A4 constants (ISO 216)
A4_WIDTH_PT = 595.28
A4_HEIGHT_PT = 841.89
A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0
THERMAL_80MM_PT = 226.77


def test_canonical_pdf_generator_produces_exact_iso_a4():
    """Prove generate_sale_receipt_pdf produces exact ISO A4 page dimensions."""
    sample_sale = {
        "id": 101,
        "created_at": "2026-10-02T09:30:00",
        "total_amount": 4900.0,
        "payment_method": "cash",
        "status": "completed",
        "warranty_enabled": True,
        "warranty_days": 30,
        "items": [
            {
                "product_id": 229,
                "title": "МФУ HP LaserJet 3055 / пробег 12к",
                "price": 4900.0,
                "quantity": 1,
            }
        ],
    }

    doc_data = build_receipt_document_data(sample_sale)
    pdf_bytes = generate_sale_receipt_pdf(doc_data)

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1
    page = reader.pages[0]
    mb = page.mediabox

    w_pt = float(mb.width)
    h_pt = float(mb.height)
    w_mm = round(w_pt * 25.4 / 72.0, 1)
    h_mm = round(h_pt * 25.4 / 72.0, 1)

    # 1. Exact A4 dimensions in points (within 0.5 pt tolerance)
    assert abs(w_pt - A4_WIDTH_PT) < 0.5, f"Expected A4 width ~{A4_WIDTH_PT} pt, got {w_pt} pt"
    assert abs(h_pt - A4_HEIGHT_PT) < 0.5, f"Expected A4 height ~{A4_HEIGHT_PT} pt, got {h_pt} pt"

    # 2. Exact A4 dimensions in millimeters
    assert w_mm == A4_WIDTH_MM, f"Expected {A4_WIDTH_MM} mm width, got {w_mm} mm"
    assert h_mm == A4_HEIGHT_MM, f"Expected {A4_HEIGHT_MM} mm height, got {h_mm} mm"

    # 3. Portrait orientation
    assert h_pt > w_pt, "Receipt PDF must be in portrait orientation"

    # 4. Strictly NOT 80mm thermal receipt
    assert abs(w_pt - THERMAL_80MM_PT) > 100.0, f"Receipt width must not match 80mm thermal ({THERMAL_80MM_PT} pt)"


def test_core_http_print_endpoint_produces_exact_iso_a4():
    """Prove Core HTTP print endpoint returns valid A4 PDF."""
    db = SessionLocal()
    try:
        sale = db.query(models.Sale).first()
        if not sale:
            sale = models.Sale(
                total_amount=Decimal("1000.00"),
                payment_method="cash",
                status="completed",
                warranty_enabled=True,
                warranty_days=30,
            )
            db.add(sale)
            db.commit()
            db.refresh(sale)
        sale_id = sale.id
    finally:
        db.close()

    resp = client.get(f"/api/sales/{sale_id}/receipt/print")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"

    reader = pypdf.PdfReader(io.BytesIO(resp.content))
    page = reader.pages[0]
    mb = page.mediabox

    w_pt = float(mb.width)
    h_pt = float(mb.height)
    w_mm = round(w_pt * 25.4 / 72.0, 1)
    h_mm = round(h_pt * 25.4 / 72.0, 1)

    assert abs(w_pt - A4_WIDTH_PT) < 0.5
    assert abs(h_pt - A4_HEIGHT_PT) < 0.5
    assert w_mm == A4_WIDTH_MM
    assert h_mm == A4_HEIGHT_MM


def test_android_receipt_print_helper_declares_iso_a4():
    """Prove Android ReceiptPrintHelper.kt declares MediaSize.ISO_A4 and no 80mm drift."""
    android_helper_path = os.path.join(
        project_root,
        "android-app",
        "app",
        "src",
        "main",
        "java",
        "com",
        "technoreboot",
        "mobile",
        "print",
        "ReceiptPrintHelper.kt",
    )
    assert os.path.exists(android_helper_path), f"ReceiptPrintHelper.kt must exist at {android_helper_path}"

    with open(android_helper_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "PrintAttributes.MediaSize.ISO_A4" in content, (
        "Android ReceiptPrintHelper must configure PrintAttributes.MediaSize.ISO_A4"
    )
    assert "80mm" not in content.lower(), "ReceiptPrintHelper must not declare 80mm"
    assert "PrintAttributes.COLOR_MODE_COLOR" in content, (
        "Android ReceiptPrintHelper must configure COLOR_MODE_COLOR"
    )
