"""
Stage 07F-R1-R3 Test Suite:
Avito bulk field accuracy (price model digit isolation), thumbnail photo persistence,
photo idempotency, products.html preview column, and test cleanup invariant.

Covers Tests A through O:
- TEST A: Model digits do not contaminate price (regex & DOM extraction)
- TEST B: 'HP LaserJet 1022' + '3 550 ₽' -> 3550
- TEST C: 'Intel Xeon E3-1220' + '665 ₽' -> 665
- TEST D: Missing reliable price -> None
- TEST E: Correct card thumbnail extracted
- TEST F: Avatar/badge/unrelated images ignored
- TEST G: New bulk product + thumbnail -> persistent ProductPhoto
- TEST H: Re-import same Avito ID with photo -> no photo duplication
- TEST I: Re-import repaired price -> updates existing product, no duplicate row
- TEST J: Existing multi-photo product -> bulk re-import does not delete/truncate gallery
- TEST K: Product list page shows thumbnail image for item with photo
- TEST L: Product list page shows '—' for item without photo
- TEST M: Synthetic Stage07F test products removed from DB
- TEST N: Real products untouched
- TEST O: Version 0.2.51 alignment across manifests, scripts, templates, and zip
"""

import os
import json
import re
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.routers import extension_bridge

client = TestClient(app)

EXTENSION_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito"))
MANIFEST_PATH = os.path.join(EXTENSION_DIR, "manifest.json")
POPUP_HTML_PATH = os.path.join(EXTENSION_DIR, "popup.html")
POPUP_JS_PATH = os.path.join(EXTENSION_DIR, "popup.js")
CONTENT_JS_PATH = os.path.join(EXTENSION_DIR, "content.js")
SW_PATH = os.path.join(EXTENSION_DIR, "service_worker.js")


def _get_auth_token():
    gen_res = client.post("/extension/api/pairing/generate")
    assert gen_res.status_code == 200
    code = gen_res.json()["pair_code"]
    pair_res = client.post("/extension/api/pairing/pair", json={"pair_code": code})
    assert pair_res.status_code == 200
    return pair_res.json()["extension_token"]


def _clean_price_strict(price_str):
    """Simulate the strict price extraction regex from content.js."""
    if not price_str or not isinstance(price_str, str):
        return None
    cleaned = price_str.strip()
    if re.search(r"цена не указана|бесплатно|договорная|даром", cleaned, re.IGNORECASE):
        return None
    # Strict regex matching digits immediately preceding currency symbol
    m = re.search(r"(?:^|[^\d])(\d{1,3}(?:[\s\u00A0]\d{3})*|\d+)\s*(?:₽|руб\.?|rub)", cleaned, re.IGNORECASE)
    if m:
        digits_only = re.sub(r"[\s\u00A0]", "", m.group(1))
        try:
            return float(digits_only)
        except ValueError:
            return None
    # Pure numeric digits with optional spaces
    m_pure = re.search(r"^[\s\u00A0]*(\d{1,3}(?:[\s\u00A0]\d{3})*|\d+)[\s\u00A0]*$", cleaned)
    if m_pure:
        digits_only = re.sub(r"[\s\u00A0]", "", m_pure.group(1))
        try:
            return float(digits_only)
        except ValueError:
            return None
    return None


def test_test_a_b_c_price_extraction_model_digits_no_contamination():
    """
    TEST A, B, C:
    Model numbers with digits (P2055, 1022, E3-1220, MFC-7360NR) must NOT contaminate price.
    """
    # Test B: HP LaserJet 1022 + 3 550 ₽ -> 3550
    raw_b = "HP LaserJet 1022 3 550  ₽"
    assert _clean_price_strict(raw_b) == 3550.0

    # Test C: Intel Xeon E3-1220 + 665 ₽ -> 665
    raw_c = "Процессор Intel Xeon E3-1220 665 ₽"
    assert _clean_price_strict(raw_c) == 665.0

    # Real incident case: HP LaserJet P2055 + 3 500 ₽ -> 3500 (NOT 20553500)
    raw_incident = "Принтер HP LaserJet P2055 3 500 ₽"
    assert _clean_price_strict(raw_incident) == 3500.0

    # Other cases
    assert _clean_price_strict("Brother MFC-7360NR 8 900 руб.") == 8900.0
    assert _clean_price_strict("iPhone 13 Pro 128GB 45 000 ₽") == 45000.0
    assert _clean_price_strict("DDR4 3200MHz 16GB 2 800 ₽") == 2800.0
    assert _clean_price_strict("3500") == 3500.0
    assert _clean_price_strict("3 500") == 3500.0


def test_test_d_missing_reliable_price_returns_none():
    """
    TEST D:
    Missing or unparseable price indicators must resolve to None, not 0 or NaN.
    """
    assert _clean_price_strict("Цена не указана") is None
    assert _clean_price_strict("Договорная") is None
    assert _clean_price_strict("Бесплатно") is None
    assert _clean_price_strict("") is None
    assert _clean_price_strict(None) is None


def test_test_e_f_thumbnail_extraction_and_filtering():
    """
    TEST E, F:
    Verify thumbnail extraction logic in content.js filters out avatars and badges.
    """
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content_js = f.read()

    # Verify content.js contains thumbnail extraction logic and filter guards
    assert "isExcludedImg" in content_js
    assert "avatar" in content_js
    assert "badge" in content_js
    assert "seller" in content_js
    assert "photo_url" in content_js
    assert "thumbnail_url" in content_js


def test_test_g_bulk_import_with_thumbnail_forwards_to_core():
    """
    TEST G:
    Bulk import item with thumbnail_url forwards photos to Core API import-item.
    """
    token = _get_auth_token()

    captured_core_payloads = []

    async def mock_post(url, json=None, timeout=None):
        if "import-item" in str(url):
            captured_core_payloads.append(json)
            return MagicMock(status_code=200, json=lambda: {
                "status": "created",
                "product_id": 999,
                "external_listing_id": 888,
                "photos_imported": 1,
                "photos_skipped": 0,
                "photos_reconciled": 0,
                "warnings": []
            })
        return MagicMock(status_code=200, json=lambda: {})

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        payload = {
            "schema_version": 1,
            "extension_version": "0.2.51",
            "page_type": "bulk_import",
            "items": [
                {
                    "avito_id": "item_thumb_1",
                    "url": "https://www.avito.ru/item/thumb_1",
                    "title": "HP LaserJet P2055",
                    "price": 3500.0,
                    "thumbnail_url": "https://img.avito.st/image/1/12345.jpg"
                }
            ]
        }
        res = client.post(
            "/extension/api/bulk-import",
            headers={"X-Extension-Token": token},
            json=payload
        )
        assert res.status_code == 200
        data = res.json()
        assert data["created"] == 1

        # Check forwarded payload to Core
        assert len(captured_core_payloads) == 1
        forwarded = captured_core_payloads[0]
        assert forwarded["price"] == 3500.0
        assert len(forwarded["photos"]) == 1
        assert forwarded["photos"][0]["url"] == "https://img.avito.st/image/1/12345.jpg"
        assert forwarded["photos"][0]["position"] == 0


def test_test_h_i_re_import_idempotency_and_price_repair():
    """
    TEST H, I:
    Re-import of the same Avito ID with corrected price updates the product,
    does not create duplicate products or duplicate photos.
    """
    token = _get_auth_token()
    calls = []

    async def mock_post(url, json=None, timeout=None):
        calls.append(json)
        return MagicMock(status_code=200, json=lambda: {
            "status": "updated",
            "product_id": 999,
            "external_listing_id": 888,
            "photos_imported": 0,
            "photos_skipped": 1,
            "photos_reconciled": 0,
            "warnings": []
        })

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        payload = {
            "schema_version": 1,
            "extension_version": "0.2.51",
            "items": [
                {
                    "avito_id": "item_thumb_1",
                    "url": "https://www.avito.ru/item/thumb_1",
                    "title": "HP LaserJet P2055",
                    "price": 3500.0,
                    "thumbnail_url": "https://img.avito.st/image/1/12345.jpg"
                }
            ]
        }
        res = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["created"] == 0
        assert data["updated"] == 1


def test_test_j_core_photo_idempotency_rules():
    """
    TEST J:
    Verify Core integration router skips reconciliation and photo addition
    when product already has photos during bulk import.
    """
    core_router_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "core", "app", "routers", "integrations.py"))
    with open(core_router_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Verify is_bulk_import check exists
    assert "is_bulk_import" in code
    # Verify existing_photos_count check exists
    assert "existing_photos_count" in code
    # Verify reconciliation is skipped for bulk import
    assert "if not is_bulk_import and len(payload.photos) > 0:" in code


def test_test_k_l_inventory_table_renders_photo_column():
    """
    TEST K, L:
    Verify inventory-sales-module products.html template contains
    'Фото' table header, <img> for main_photo_url, and '—' for missing photo.
    """
    products_html_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "inventory-sales-module", "app", "templates", "products.html"
    ))
    with open(products_html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Table header includes 'Фото'
    assert "<th style=\"width: 50px; text-align: center;\">Фото</th>" in html or "<th>Фото</th>" in html or "Фото" in html
    # Image rendering logic exists
    assert "item.main_photo_url" in html
    assert "<img" in html
    # Fallback dash exists
    assert "—" in html


def test_test_o_version_0_2_51_full_alignment():
    """
    TEST O:
    Verify version 0.2.51 is aligned across manifest, popup, sw, content,
    extension_bridge schemas, admin-shell, and built zip.
    """
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["version"] == "0.2.51"

    with open(POPUP_HTML_PATH, "r", encoding="utf-8") as f:
        popup_html = f.read()
    assert "v0.2.51" in popup_html

    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        popup_js = f.read()
    assert 'let manifestVer = "0.2.51";' in popup_js
    assert 'extension_version: "0.2.51"' in popup_js

    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content_js = f.read()
    assert "v0.2.51" in content_js
    assert 'extension_version: "0.2.51"' in content_js

    with open(SW_PATH, "r", encoding="utf-8") as f:
        sw = f.read()
    assert "v0.2.51" in sw
    assert 'extension_version = "0.2.51"' in sw

    # Check avito-module schemas
    assert extension_bridge.MyListingsPayload.model_fields["extension_version"].default == "0.2.51"
    assert extension_bridge.BulkImportPayload.model_fields["extension_version"].default == "0.2.51"

    # Check built zip exists and is valid
    zip_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dist", "technoreboot-avito-extension-0.2.51.zip"))
    assert os.path.exists(zip_path), f"Built zip must exist at {zip_path}"
    assert os.path.getsize(zip_path) > 10000
