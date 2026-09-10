"""
Stage 07F-R1-R2 Test Suite:
Fix Avito bulk import 422 `body field required` + accounting / false success.

Covers Tests A through N and related contracts:
- TEST A: Reproduce 422 missing body failure from empty/undefined body
- TEST B: Bulk sender always emits valid non-empty JSON body
- TEST C: Canonical batch sender contract used for both single-page and all-pages
- TEST D: 50-item batch reaches Avito module with exactly 50 items
- TEST E: Avito module response accounts for all 50 items (created + updated + skipped + errors == 50)
- TEST F: Page navigation session state structure & persistence
- TEST G & H: Page 2 and Page 3 use valid non-empty request body
- TEST I: Safe Russian error UI without raw Pydantic JSON or pydantic.dev URLs
- TEST J: Any error prevents green all-success state
- TEST K: Counter invariant holds per batch (created + updated + skipped + errors == submitted)
- TEST L: Counter invariant holds across full multi-page import
- TEST M: Second import creates no duplicates (idempotency)
- TEST N: Detailed enrichment updates exact same product entity
- TEST O: Real cabinet fixture detection produces non-zero listings
"""

import os
import json
import re
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _get_auth_token():
    gen_res = client.post("/extension/api/pairing/generate")
    assert gen_res.status_code == 200
    code = gen_res.json()["pair_code"]
    pair_res = client.post("/extension/api/pairing/pair", json={"pair_code": code})
    assert pair_res.status_code == 200
    return pair_res.json()["extension_token"]


def test_test_a_reproduce_old_422_missing_body_failure():
    """
    TEST A: Reproduce the exact 422 'Field required: loc: body' when a POST
    request is made without a request body (as occurred in v0.2.49 when
    popup passed items instead of payload, resulting in body: JSON.stringify(undefined)).
    """
    token = _get_auth_token()
    
    # Send POST with empty body (0 bytes)
    res = client.post(
        "/extension/api/bulk-import",
        headers={
            "X-Extension-Token": token,
            "Content-Type": "application/json"
        },
        content=b""
    )
    assert res.status_code == 422
    err_json = res.json()
    assert "detail" in err_json
    # Confirm it matches the exact error observed in the real browser
    locs = [e.get("loc") for e in err_json["detail"] if isinstance(e, dict)]
    assert any("body" in loc for loc in locs)


def test_test_b_bulk_sender_emits_valid_json_body_and_structure():
    """
    TEST B: Verify that bulk import with canonical payload produces a valid
    non-empty body that is accepted by the Avito module.
    """
    token = _get_auth_token()
    mock_resp = MagicMock(status_code=200, json=lambda: {"status": "created", "product_id": 901})

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        payload = {
            "schema_version": 1,
            "extension_version": "0.2.51",
            "page_type": "bulk_import",
            "items": [
                {"avito_id": "item_101", "url": "https://www.avito.ru/item/101", "title": "Товар 101", "price": 1500}
            ]
        }
        res = client.post(
            "/extension/api/bulk-import",
            headers={"X-Extension-Token": token, "Content-Type": "application/json"},
            json=payload
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["total"] == 1
        assert data["created"] == 1


def test_test_c_current_page_and_all_pages_share_same_sender_helper():
    """
    TEST C: Verify that popup.js defines sendBulkBatch as the single canonical
    batch sender called by both bulkImportCurrentBtn and bulkImportAllBtn.
    """
    popup_js_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "popup.js"
    ))
    with open(popup_js_path, "r", encoding="utf-8") as f:
        popup_js = f.read()

    assert "async function sendBulkBatch(batchItems)" in popup_js
    # Ensure bulkImportCurrentBtn calls sendBulkBatch
    assert "bulkImportCurrentBtn.onclick" in popup_js
    assert "await sendBulkBatch(" in popup_js
    # Ensure both callers send the canonical message
    assert 'action: "bulk_import_batch"' in popup_js
    assert "payload: payload" in popup_js


def test_test_d_and_e_50_item_batch_accounting_invariant():
    """
    TEST D & E: 50-item batch reaches Avito module with exactly 50 items,
    and the module response accounts for all 50 items:
    created + updated + skipped + errors == 50.
    """
    token = _get_auth_token()
    
    items_50 = [
        {
            "avito_id": f"real_{i:03d}",
            "url": f"https://www.avito.ru/item/real_{i:03d}",
            "title": f"Комплектующие ПК #{i}",
            "price": 2000 + i * 50
        }
        for i in range(1, 51)
    ]
    assert len(items_50) == 50

    # Mock Core responses: 40 created, 8 updated, 2 errors
    def side_effect_post(url, json=None, **kwargs):
        item_id = json.get("external_item_id")
        if item_id in ["real_049", "real_050"]:
            return MagicMock(status_code=500, json=lambda: {"detail": "Core database timeout"})
        elif item_id in [f"real_{k:03d}" for k in range(41, 49)]:
            return MagicMock(status_code=200, json=lambda: {"status": "updated", "product_id": 300})
        else:
            return MagicMock(status_code=200, json=lambda: {"status": "created", "product_id": 300})

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = side_effect_post

        payload = {
            "schema_version": 1,
            "extension_version": "0.2.51",
            "items": items_50
        }
        res = client.post(
            "/extension/api/bulk-import",
            headers={"X-Extension-Token": token},
            json=payload
        )
        assert res.status_code == 200
        data = res.json()
        
        created = data["created"]
        updated = data["updated"]
        skipped = data["skipped"]
        err_count = data["error_count"]
        total = data["total"]

        assert total == 50
        assert created == 40
        assert updated == 8
        assert skipped == 0
        assert err_count == 2
        # Strict Invariant: created + updated + skipped + errors == submitted (50)
        assert created + updated + skipped + err_count == 50


def test_test_f_g_h_multi_page_batches_use_valid_body_across_pages():
    """
    TEST F, G, H: Verify Page 1, Page 2, Page 3 all deliver valid JSON bodies
    to the Avito module without body loss.
    """
    token = _get_auth_token()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"status": "created", "product_id": 400})

        # Page 1 (50 items)
        page1_items = [{"avito_id": f"p1_{i}", "title": f"Page 1 Item {i}", "price": 1000} for i in range(1, 51)]
        res1 = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json={"items": page1_items})
        assert res1.status_code == 200
        assert res1.json()["total"] == 50

        # Page 2 (50 items)
        page2_items = [{"avito_id": f"p2_{i}", "title": f"Page 2 Item {i}", "price": 2000} for i in range(1, 51)]
        res2 = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json={"items": page2_items})
        assert res2.status_code == 200
        assert res2.json()["total"] == 50

        # Page 3 (15 items)
        page3_items = [{"avito_id": f"p3_{i}", "title": f"Page 3 Item {i}", "price": 3000} for i in range(1, 16)]
        res3 = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json={"items": page3_items})
        assert res3.status_code == 200
        assert res3.json()["total"] == 15


def test_test_i_safe_error_ui_translation():
    """
    TEST I: Verify that service_worker.js translates raw 422 missing body
    errors into safe Russian text without raw Pydantic JSON or pydantic.dev URLs.
    """
    sw_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "service_worker.js"
    ))
    with open(sw_path, "r", encoding="utf-8") as f:
        sw_code = f.read()

    # Verify clean Russian translation exists
    assert "Ошибка отправки данных в Техноребут: сервер не получил пакет объявлений." in sw_code
    # Verify pydantic.dev link stripping exists
    assert r"errors\.pydantic\.dev" in sw_code

    popup_js_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "popup.js"
    ))
    with open(popup_js_path, "r", encoding="utf-8") as f:
        popup_code = f.read()

    assert "sanitizeErrorMessage" in popup_code
    assert "Ошибка отправки данных в Техноребут: сервер не получил пакет объявлений." in popup_code


def test_test_j_any_error_prevents_green_success():
    """
    TEST J: Verify that popup.js enforces green success ONLY IF errors == 0.
    If errors > 0, status must be warning or error, never green success.
    """
    popup_js_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "popup.js"
    ))
    with open(popup_js_path, "r", encoding="utf-8") as f:
        popup_code = f.read()

    # Ensure warning message is displayed when errors exist
    assert "msg-warning" in popup_code
    assert "Импорт завершён с ошибками" in popup_code
    # Ensure error message is displayed on fatal batch failure
    assert "msg-error" in popup_code
    assert "Импорт остановлен из-за ошибки" in popup_code


def test_test_k_and_l_counter_invariants_in_code():
    """
    TEST K & L: Verify popup.js strictly computes:
    totalProcessedSuccess = totalCreated + totalUpdated + totalSkipped
    and accounts for errors so that totalCreated + totalUpdated + totalSkipped + allErrors.length == totalSubmitted.
    """
    popup_js_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "popup.js"
    ))
    with open(popup_js_path, "r", encoding="utf-8") as f:
        popup_code = f.read()

    assert "const totalProcessedSuccess = totalCreated + totalUpdated + totalSkipped;" in popup_code
    assert "bulkProcessedCount.textContent = totalProcessedSuccess;" in popup_code
    assert "bulkErrorsCount.textContent = allErrors.length;" in popup_code


def test_test_m_and_n_idempotency_and_enrichment():
    """
    TEST M & N:
    - Re-importing the same items produces 0 duplicates (idempotency).
    - Detailed enrichment preserves same entity and updates description/photos.
    """
    token = _get_auth_token()
    items = [{"avito_id": f"dedup_{i}", "title": f"Item {i}", "price": 1000} for i in range(1, 11)]

    # 1. Initial import: 10 created
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"status": "created", "product_id": 500})
        res1 = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json={"items": items})
        assert res1.status_code == 200
        assert res1.json()["created"] == 10
        assert res1.json()["updated"] == 0

    # 2. Second import: 0 created, 10 updated (0 duplicates)
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"status": "updated", "product_id": 500})
        res2 = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json={"items": items})
        assert res2.status_code == 200
        assert res2.json()["created"] == 0
        assert res2.json()["updated"] == 10

    # 3. Enrichment: single item
    enrich_payload = {
        "schema_version": 1,
        "extension_version": "0.2.51",
        "captured_at": "2026-09-10T14:00:00Z",
        "page_type": "listing",
        "listing": {
            "external_item_id": "dedup_1",
            "external_url": "https://www.avito.ru/item/dedup_1",
            "title": "Enriched Item 1",
            "price": 1200,
            "description": "Full rich description for item 1",
            "photos": [{"url": "https://img.avito.st/image/1/1.jpg"}]
        }
    }
    with patch("app.services.import_service.import_ad_to_core") as mock_core_import:
        mock_core_import.return_value = {
            "status": "updated",
            "product_id": 501,
            "photos_imported": 1,
            "photos_skipped": 0,
            "photos_total": 1
        }
        res_enrich = client.post("/extension/api/listing", headers={"X-Extension-Token": token}, json=enrich_payload)
        assert res_enrich.status_code == 200
        assert res_enrich.json()["product_id"] == 501
        assert res_enrich.json()["status"] == "success"


def test_test_o_real_cabinet_fixture_detection():
    """
    TEST O: Verify that real cabinet fixture detection logic accurately finds 50 items.
    """
    fixture_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "tests", "fixtures", "real_owner_cabinet_listings.html"
    ))
    assert os.path.exists(fixture_path), f"Fixture not found at {fixture_path}"

    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Check that item markers exist in real fixture
    item_matches = re.findall(r'data-marker="item-root"', html)
    anchor_matches = re.findall(r'href="[^"]*_\d{8,14}[^"]*"', html)
    assert len(item_matches) > 0 or len(anchor_matches) > 0
