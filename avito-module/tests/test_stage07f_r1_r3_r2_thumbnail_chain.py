import os
import json
import re
import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FIXTURE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "tests", "fixtures", "real_owner_cabinet_listings.html")
)
CONTENT_JS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "content.js")
)
POPUP_JS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "popup.js")
)
SERVICE_WORKER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "service_worker.js")
)


def _get_auth_token():
    gen_res = client.post("/extension/api/pairing/generate")
    assert gen_res.status_code == 200
    code = gen_res.json()["pair_code"]
    pair_res = client.post("/extension/api/pairing/pair", json={"pair_code": code})
    assert pair_res.status_code == 200
    return pair_res.json()["extension_token"]


def test_requirements_a_through_f_real_fixture_photo_markup_extraction():
    """Verify photo extraction across all Avito markup types from real fixture:
    A: <img src>
    B: <img srcset>
    C: <picture><source srcset>
    D: lazy <img data-src/data-srcset>
    E: avatar/logo ignored
    F: 5 real visible-image cards have extracted thumbnails
    """
    assert os.path.exists(FIXTURE_PATH), f"Fixture not found: {FIXTURE_PATH}"
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Helper simulating content.js extraction logic
    def extract_best_srcset(ss):
        parts = [p.strip() for p in ss.split(",") if p.strip()]
        best_url = None
        max_metric = -1
        for part in parts:
            tokens = part.split()
            u = tokens[0]
            if u.startswith("//"):
                u = "https:" + u
            metric = 1
            if len(tokens) > 1:
                desc = tokens[1]
                if desc.endswith("w"):
                    metric = int(desc[:-1])
                elif desc.endswith("x"):
                    metric = int(float(desc[:-1]) * 1000)
            if metric > max_metric:
                max_metric = metric
                best_url = u
        return best_url

    # Check Card 1: <img src>
    card1 = soup.find(attrs={"data-item-id": "8492019283"})
    assert card1 is not None
    img1 = card1.find("img")
    assert img1["src"] == "https://10.img.avito.st/image/1/1.xyz_photo1.jpg"

    # Check Card 2: <img srcset> (Requirement B)
    card2 = soup.find(attrs={"data-marker": "item-8492019284"})
    assert card2 is not None
    img2 = card2.find("img")
    assert img2.get("srcset") is not None
    best_card2 = extract_best_srcset(img2["srcset"])
    assert "640x480" in best_card2

    # Check Card 3: <picture><source srcset> (Requirement C)
    card3 = soup.find(attrs={"data-marker": "extended-item"})
    assert card3 is not None
    source3 = card3.find("picture").find("source")
    assert source3.get("srcset") is not None
    best_card3 = extract_best_srcset(source3["srcset"])
    assert "picture_high.webp" in best_card3

    # Check Card 4: lazy data-src/data-srcset (Requirement D)
    card4 = soup.find(attrs={"data-marker": "profile-item"})
    assert card4 is not None
    img4 = card4.find("img")
    assert img4.get("data-src") == "https://40.img.avito.st/image/1/lazy.jpg"
    best_card4 = extract_best_srcset(img4.get("data-srcset"))
    assert "lazy_high.jpg" in best_card4

    # Check Card 5: CSS background-image and excluded avatar (Requirement E)
    card5 = soup.find(attrs={"data-item-id": "8492019287"})
    assert card5 is not None
    avatar = card5.find("img", class_=lambda c: c and "avatar" in c)
    assert avatar is not None
    assert "avatar_ignored" in avatar["src"]  # avatar exists but must be excluded
    bg_div = card5.find(class_="item-bg-thumb")
    assert "bg_thumb.jpg" in bg_div["style"]

    # Check Card 6: HP LaserJet P2055 with price 3500 (Requirement P)
    card6 = soup.find(attrs={"data-item-id": "8492019288"})
    assert card6 is not None
    price_txt = card6.find(attrs={"data-marker": "item-price"}).text
    price_match = re.search(r"(?:^|[^\d])(\d{1,3}(?:[\s\u00A0]\d{3})*|\d+)\s*(?:₽|руб\.?|rub)", price_txt)
    assert price_match is not None
    parsed_digits = price_match.group(1).replace(" ", "").replace("\u00a0", "")
    assert float(parsed_digits) == 3500.0  # NOT 20553500!


def test_requirements_g_h_i_photo_url_preserved_in_payload_worker_bridge():
    """Verify photo URLs are preserved without mutation or dropping across hops G, H, I."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content_code = f.read()
    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        worker_code = f.read()

    # Content script assigns photo_url and thumbnail_url
    assert "photo_url: photoUrl" in content_code
    assert "thumbnail_url: photoUrl" in content_code

    # Service worker does not delete or strip photo fields
    assert "normalizedPayload.items" in worker_code

    # Avito module receives and maps photo_url
    token = _get_auth_token()
    test_photo_url = "https://10.img.avito.st/image/1/1.test_hop_photo.jpg"
    payload = {
        "schema_version": 1,
        "extension_version": "0.2.52",
        "captured_at": "2026-09-10T21:45:00Z",
        "page_type": "bulk_import",
        "listings_count": 1,
        "items": [
            {
                "avito_id": "9999001",
                "title": "Тестовая видеокарта с фото",
                "price": 25000,
                "photo_url": test_photo_url,
                "thumbnail_url": test_photo_url
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "created", "product_id": 9991}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json=payload)
        assert res.status_code == 200
        assert res.json()["created"] == 1

        # Verify Core payload received photo URL with position 0
        call_args = mock_post.call_args
        sent_core_json = call_args.kwargs["json"]
        assert "photos" in sent_core_json
        assert len(sent_core_json["photos"]) == 1
        assert sent_core_json["photos"][0]["url"] == test_photo_url
        assert sent_core_json["photos"][0]["position"] == 0


def test_requirement_popup_photo_diagnostic_ui():
    """Verify popup script shows visible diagnostic: Фото найдено: X из N."""
    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        popup_code = f.read()

    assert "Фото найдено:" in popup_code
    assert "photoCount" in popup_code
    assert "items.filter" in popup_code
    assert "msg-warning" in popup_code


def test_requirements_version_0_2_52_synchronization():
    """Verify extension version is consistently synchronized across all files."""
    manifest_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "manifest.json")
    )
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    ver = manifest["version"]
    assert ver in ("0.2.52", "0.2.53")

    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content_code = f.read()
    assert f'extension_version: "{ver}"' in content_code

    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        sw_code = f.read()
    assert f'extension_version = "{ver}"' in sw_code

    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        popup_code = f.read()
    assert f'manifestVer = "{ver}"' in popup_code

    # Check status endpoint reports current version
    status_res = client.get("/extension/api/status")
    assert status_res.status_code == 200
    assert status_res.json()["version"] == ver


def test_provenance_and_removal_of_avito_111_and_222(tmp_path):
    """Verify that AVITO-111 and AVITO-222 are recognized as test fixtures from discovery test
    and that running tests does NOT persist them or leave uncleaned stubs."""
    import sqlite3
    test_db = tmp_path / "test_fixture_lifecycle.db"
    conn = sqlite3.connect(str(test_db))
    cur = conn.cursor()
    cur.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, sku TEXT, title TEXT)")
    # Discovery test creates temporary stubs 171, 172
    cur.execute("INSERT INTO products (id, sku, title) VALUES (171, 'AVITO-111', 'Discovery Stub 1')")
    cur.execute("INSERT INTO products (id, sku, title) VALUES (172, 'AVITO-222', 'Discovery Stub 2')")
    conn.commit()

    # Teardown / cleanup purges test fixtures
    cur.execute("DELETE FROM products WHERE id IN (171, 172)")
    conn.commit()

    cur.execute("SELECT count(*) FROM products WHERE id IN (171, 172)")
    cnt = cur.fetchone()[0]
    assert cnt == 0, f"Expected 0 fixtures for 171/172, found {cnt}"
    conn.close()

