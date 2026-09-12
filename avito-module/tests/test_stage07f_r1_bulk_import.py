import json
import os
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


def test_bulk_import_requires_token():
    """Verify bulk import endpoint rejects unauthorized requests."""
    res = client.post("/extension/api/bulk-import", json={"items": []})
    assert res.status_code in [401, 403]


@pytest.mark.asyncio
async def test_bulk_import_card_list_success():
    """Verify bulk import parses lightweight card items and calls Core API."""
    token = _get_auth_token()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "status": "created",
        "product_id": 101,
        "message": "Product created"
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        payload = {
            "schema_version": 1,
            "items": [
                {
                    "avito_id": "4001",
                    "url": "https://www.avito.ru/item/4001",
                    "title": "Материнская плата B450",
                    "price": 5500,
                    "status": "active",
                    "location": "Москва",
                    "photo_url": "https://img.avito.st/image/1/4001.jpg"
                },
                {
                    "avito_id": "4002",
                    "url": "https://www.avito.ru/item/4002",
                    "title": "Процессор Ryzen 5 3600",
                    "price": 6000,
                    "status": "active",
                    "location": "Москва"
                }
            ]
        }

        res = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["total"] == 2
        assert data["created"] == 2
        assert data["updated"] == 0
        assert data["errors"] == []
        assert mock_post.call_count == 2

        first_call_json = mock_post.call_args_list[0].kwargs["json"]
        assert first_call_json["external_item_id"] == "4001"
        assert first_call_json["price"] == 5500
        assert first_call_json["photos"][0]["url"] == "https://img.avito.st/image/1/4001.jpg"


@pytest.mark.asyncio
async def test_bulk_import_handles_single_item_error_gracefully():
    """Verify single card error does not abort entire batch."""
    token = _get_auth_token()

    good_resp = MagicMock()
    good_resp.status_code = 200
    good_resp.json.return_value = {"status": "created", "product_id": 102}

    bad_resp = MagicMock()
    bad_resp.status_code = 500
    bad_resp.text = "Internal Server Error in Core"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [good_resp, bad_resp, good_resp]

        payload = {
            "items": [
                {"avito_id": "5001", "title": "Item 1", "price": 1000},
                {"avito_id": "5002", "title": "Item 2 (fails)", "price": 2000},
                {"avito_id": "5003", "title": "Item 3", "price": 3000}
            ]
        }

        res = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 3
        assert data["created"] == 2
        assert len(data["errors"]) == 1
        assert data["errors"][0]["avito_id"] == "5002"


@pytest.mark.asyncio
async def test_55_item_fixture_scenario_bulk_dedup_and_enrichment():
    """
    Scenario:
    1. 55 items across 3 pages imported in bulk -> 55 created.
    2. Second bulk run -> 0 created, 55 updated, 0 duplicates.
    3. Detailed import of item #17 -> updates description, characteristics, photos on exact same product.
    """
    token = _get_auth_token()

    # Create 55 items
    items_55 = [
        {
            "avito_id": f"ad_{i:03d}",
            "url": f"https://www.avito.ru/item/ad_{i:03d}",
            "title": f"Комплектующие ПК #{i}",
            "price": 1000 + i * 100,
            "status": "active",
            "location": "Москва, Сервисный Центр",
            "photo_url": f"https://img.avito.st/thumb/{i}.jpg"
        }
        for i in range(1, 56)
    ]

    # Run 1: First bulk import (55 items created)
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"status": "created", "product_id": 200})

        res1 = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json={"items": items_55})
        assert res1.status_code == 200
        d1 = res1.json()
        assert d1["total"] == 55
        assert d1["created"] == 55
        assert d1["updated"] == 0
        assert len(d1["errors"]) == 0
        assert mock_post.call_count == 55

    # Run 2: Second bulk import of exact same 55 items (0 duplicates, 55 updated)
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"status": "updated", "product_id": 200})

        res2 = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json={"items": items_55})
        assert res2.status_code == 200
        d2 = res2.json()
        assert d2["total"] == 55
        assert d2["created"] == 0
        assert d2["updated"] == 55
        assert len(d2["errors"]) == 0

    # Step 3: Later, Owner opens ad_017 and clicks 'Доимпортировать данные'
    item_17_payload = {
        "schema_version": 1,
        "extension_version": "0.2.49",
        "captured_at": "2026-09-10T12:00:00Z",
        "page_type": "listing",
        "listing": {
            "external_item_id": "ad_017",
            "external_url": "https://www.avito.ru/item/ad_017",
            "title": "Комплектующие ПК #17 (Полное описание)",
            "price": 2700,
            "description": "Подробное описание товара после обогащения карточки.",
            "characteristics": {
                "Категория": "Комплектующие",
                "Процессор": "Intel Core i5-12400F",
                "Память": "16GB DDR4",
                "Состояние": "Б/у"
            },
            "photos": [
                {"url": "https://img.avito.st/image/1/enriched_photo1.jpg"},
                {"url": "https://img.avito.st/image/1/enriched_photo2.jpg"}
            ]
        }
    }

    with patch("app.services.import_service.import_ad_to_core") as mock_core_import:
        mock_core_import.return_value = {
            "status": "updated",
            "product_id": 217,
            "photos_imported": 2,
            "photos_skipped": 0,
            "photos_total": 2
        }

        res_enrich = client.post("/extension/api/listing", headers={"X-Extension-Token": token}, json=item_17_payload)
        assert res_enrich.status_code == 200
        assert res_enrich.json()["status"] == "success"
        assert res_enrich.json()["product_id"] == 217

        from app import storage
        called_ext_id = mock_core_import.call_args[0][0]
        assert called_ext_id == "ad_017"
        saved_ad = storage.get_parsed_ad("ad_017")
        assert saved_ad is not None
        assert saved_ad.title == "Комплектующие ПК #17 (Полное описание)"
        assert "Intel Core i5-12400F" in saved_ad.parameters["Процессор"]
        assert len(saved_ad.photos) == 2


def test_extension_package_version_and_elements():
    """Verify Chrome extension package files match Stage 07F-R1-R1 requirements."""
    ext_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito"))
    
    # 1. manifest.json
    manifest_path = os.path.join(ext_dir, "manifest.json")
    assert os.path.exists(manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest.get("version") in ("0.2.52", "0.2.53", "0.2.54")
    assert "tabs" in manifest.get("permissions", [])

    # 2. popup.html elements
    popup_html_path = os.path.join(ext_dir, "popup.html")
    assert os.path.exists(popup_html_path)
    with open(popup_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    assert 'id="bulkSection"' in html_content
    assert 'id="bulkImportAllBtn"' in html_content
    assert 'id="bulkImportCurrentBtn"' in html_content
    assert 'id="bulkStopBtn"' in html_content
    assert 'id="bulkProgressBox"' in html_content
    assert 'Доимпортировать данные' in html_content

    # 3. service_worker.js
    sw_path = os.path.join(ext_dir, "service_worker.js")
    assert os.path.exists(sw_path)
    with open(sw_path, "r", encoding="utf-8") as f:
        sw_content = f.read()
    assert "bulk_import_batch" in sw_content
    assert "sendBulkImportPayload" in sw_content
    assert manifest.get("version") in sw_content

    # 4. content.js
    content_path = os.path.join(ext_dir, "content.js")
    assert os.path.exists(content_path)
    with open(content_path, "r", encoding="utf-8") as f:
        content_js = f.read()
    assert "extractMyListingsData" in content_js
    assert "extractPaginationInfo" in content_js
    assert manifest.get("version") in content_js
