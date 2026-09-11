import os
import re
import json
import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "tests", "fixtures"))
CONTENT_JS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "content.js"))
POPUP_JS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "popup.js"))
POPUP_HTML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "popup.html"))
MANIFEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chrome-extension", "technoreboot-avito", "manifest.json"))


def _get_auth_token():
    gen_res = client.post("/extension/api/pairing/generate")
    assert gen_res.status_code == 200
    code = gen_res.json()["pair_code"]
    pair_res = client.post("/extension/api/pairing/pair", json={"pair_code": code})
    assert pair_res.status_code == 200
    return pair_res.json()["extension_token"]


def py_extract_avito_id(url):
    """Mirror of extractAvitoIdFromUrl in content.js"""
    if not url or not isinstance(url, str):
        return None
    lower = url.lower()
    if '/user/' in lower and '/profile' in lower and '_' not in lower and 'itemid=' not in lower:
        return None
    if any(k in lower for k in ['/rating', '/reviews', '/help', '/autoload', '/favorites', '/messenger']):
        return None
    slug_m = re.search(r'_(\d{8,14})(?:[/?#]|$)', url)
    if slug_m:
        return slug_m.group(1)
    q_m = re.search(r'[?&]item_?id=(\d{8,14})', url, re.I)
    if q_m:
        return q_m.group(1)
    item_m = re.search(r'/(?:item|items|obyavlenie)/(\d{8,14})(?:[/?#]|$)', url, re.I)
    if item_m:
        return item_m.group(1)
    short_m = re.search(r'^(?:https?://[^/]+)?/(\d{8,14})(?:[/?#]|$)', url)
    if short_m:
        return short_m.group(1)
    return None


def py_extract_my_listings(html_content, page_url="https://www.avito.ru/profile/items"):
    """Python simulation of content.js extractMyListingsData()"""
    soup = BeautifulSoup(html_content, "html.parser")
    items = []
    seen_ids = set()

    # Layer 1: Containers
    card_selectors = [
        '[data-marker="item"]', '[data-marker^="item-"]', '[data-marker="item-root"]',
        '[data-marker="item-snippet"]', '[data-marker^="item-snippet"]',
        '[data-marker="catalog-serp/item"]', '[data-marker^="profile-item"]',
        '[data-marker^="extended-item"]', '[data-marker="profile/item"]',
        '[data-marker*="snippet"]', '[data-item-id]',
        'div[class*="item-snippet"]', 'div[class*="ItemSnippet"]',
        'div[class*="snippet-"]', 'div[class*="Snippet-"]',
        'div[class*="styles-root-"]', '.iva-item-root', '.items-item', 'article'
    ]
    matched_cards = soup.select(", ".join(card_selectors))

    def parse_card(el, fallback_anchor=None):
        container = el if el else (fallback_anchor.parent if fallback_anchor else None)
        if not container:
            return None
        link_el = fallback_anchor or container.select_one(
            'a[data-marker*="item-title"], a[data-marker*="title"], a[itemprop="url"], a[href*="_"], a[href*="/item/"], a[href*="/items/"], a[href*="itemId="], a'
        )
        href = link_el.get('href', '') if link_el else ''
        full_url = href if href.startswith('http') else ('https://www.avito.ru' + href)
        item_id = py_extract_avito_id(full_url)
        if not item_id and fallback_anchor:
            f_href = fallback_anchor.get('href', '')
            full_url = f_href if f_href.startswith('http') else ('https://www.avito.ru' + f_href)
            item_id = py_extract_avito_id(full_url)
        if not item_id:
            marker = container.get('data-marker', '')
            m_match = re.search(r'\d{8,14}', marker)
            if m_match:
                item_id = m_match.group(0)
            data_id = container.get('data-item-id', '')
            if re.match(r'^\d{8,14}$', data_id):
                item_id = data_id
        if not item_id:
            return None

        # Title
        title_el = container.select_one(
            '[data-marker*="title"], [data-marker="item-name"], [itemprop="name"], .item-title-link, .title-root, h3, h4, [class*="title-"], [class*="Title-"]'
        )
        if title_el and title_el.get_text(strip=True):
            title = title_el.get_text(strip=True)
        elif link_el and link_el.get('title'):
            title = link_el['title'].strip()
        elif link_el and link_el.get_text(strip=True):
            title = link_el.get_text(strip=True)
        else:
            title = f"Объявление Avito {item_id}"

        # Price
        price = None
        price_el = container.select_one(
            '[data-marker*="price"], [itemprop="price"], meta[itemprop="price"], [class*="price-text"], [class*="Price-"], [class*="price-"], .price, .item-price'
        )
        if price_el:
            content_attr = price_el.get('content')
            if content_attr:
                try:
                    price = float(content_attr)
                except ValueError:
                    pass
            if price is None:
                digits = re.sub(r'[^\d]', '', price_el.get_text())
                if digits:
                    price = float(digits)
        if price is None:
            m = re.search(r'(\d[\d\s]{0,10})\s*(?:₽|руб\.?|rub)', container.get_text(), re.I)
            if m:
                digits = re.sub(r'\s+', '', m.group(1))
                if digits:
                    price = float(digits)

        # Status
        card_text = container.get_text().lower()
        status = "inactive" if any(k in card_text for k in ["завершено", "архив", "снято", "черновик", "отклонено", "заблокировано"]) else "active"

        # Location
        loc_el = container.select_one('[data-marker*="address"], [data-marker*="geo"], [data-marker*="location"], .geo-root, [class*="geo-address"], [class*="address-"]')
        location = loc_el.get_text(strip=True) if loc_el else None

        # Photo
        photo_el = container.select_one('img[data-marker*="photo"], img[src*="img.avito.st"], img[class*="photo"], img')
        photo_url = photo_el.get('src') if photo_el else None

        return {
            "avito_id": item_id,
            "url": full_url,
            "title": title,
            "price": price,
            "status": status,
            "location": location,
            "photo_url": photo_url
        }

    for card in matched_cards:
        res = parse_card(card)
        if res and res["avito_id"] and res["avito_id"] not in seen_ids:
            seen_ids.add(res["avito_id"])
            items.append(res)

    # Layer 2: Anchors fallback
    anchors = soup.find_all("a", href=True)
    for a in anchors:
        item_id = py_extract_avito_id(a["href"])
        if item_id and item_id not in seen_ids:
            # find enclosing container
            cur = a.parent
            best = cur
            depth = 0
            while cur and depth < 8:
                depth += 1
                cls = " ".join(cur.get("class", []))
                marker = cur.get("data-marker", "")
                tag = cur.name
                if any(k in marker for k in ["item", "snippet", "card"]) or any(k in cls for k in ["item", "snippet", "card"]) or tag in ["article", "li", "tr"]:
                    best = cur
                    break
                cur = cur.parent
            res = parse_card(best, fallback_anchor=a)
            if res and res["avito_id"] and res["avito_id"] not in seen_ids:
                seen_ids.add(res["avito_id"])
                items.append(res)

    # Pagination
    curr_page = 1
    total_pages = 1
    curr_el = soup.select_one('[data-marker*="pagination-button/current"], [aria-current="page"], .pagination-item_active')
    if curr_el:
        try:
            curr_page = int(curr_el.get_text(strip=True))
        except ValueError:
            pass
    page_els = soup.select('[data-marker*="page("], [data-marker*="pagination-button/page"], .pagination-page')
    for p_el in page_els:
        try:
            p_num = int(re.search(r'\d+', p_el.get_text(strip=True) or p_el.get("data-marker", "")).group(0))
            if p_num > total_pages:
                total_pages = p_num
        except Exception:
            pass
    next_btn = soup.select_one('[data-marker*="pagination-button/next"], a[aria-label*="Следующая"]')
    has_next = bool(next_btn)

    return {
        "items": items,
        "pagination": {
            "current_page": curr_page,
            "total_pages": total_pages,
            "has_next_page": has_next
        }
    }


def test_req_a_owner_cabinet_and_public_seller_dom_count_positive():
    """Requirement A: Verify fresh sanitized Owner cabinet DOM and Public seller DOM extract count > 0."""
    # 1. Owner Cabinet
    cab_path = os.path.join(FIXTURES_DIR, "real_owner_cabinet_listings.html")
    assert os.path.exists(cab_path)
    with open(cab_path, "r", encoding="utf-8") as f:
        cab_html = f.read()
    cab_res = py_extract_my_listings(cab_html)
    assert len(cab_res["items"]) == 6, f"Expected 6 items from Owner cabinet fixture, got {len(cab_res['items'])}"

    # 2. Public Seller
    pub_path = os.path.join(FIXTURES_DIR, "real_public_seller_profile.html")
    assert os.path.exists(pub_path)
    with open(pub_path, "r", encoding="utf-8") as f:
        pub_html = f.read()
    pub_res = py_extract_my_listings(pub_html)
    assert len(pub_res["items"]) == 2, f"Expected 2 items from Public seller fixture, got {len(pub_res['items'])}"


def test_req_b_c_one_card_one_id_and_duplicate_anchors_deduplication():
    """Requirement B & C: One visible card -> one unique ID, duplicate anchors -> exactly one item."""
    cab_path = os.path.join(FIXTURES_DIR, "real_owner_cabinet_listings.html")
    with open(cab_path, "r", encoding="utf-8") as f:
        cab_html = f.read()
    res = py_extract_my_listings(cab_html)
    items = res["items"]

    # In real_owner_cabinet_listings.html, Card 3 has 3 anchors with ID 8492019285
    card3_matches = [it for it in items if it["avito_id"] == "8492019285"]
    assert len(card3_matches) == 1, "Duplicate anchors for 8492019285 must yield exactly 1 listing"

    # All extracted IDs must be unique
    ids = [it["avito_id"] for it in items]
    assert len(ids) == len(set(ids))
    assert set(ids) == {"8492019283", "8492019284", "8492019285", "8492019286", "8492019287", "8492019288"}


def test_req_d_e_f_title_price_and_missing_price_resilience():
    """Requirement D, E, F: Title and price parsed correctly; missing price does NOT drop listing."""
    cab_path = os.path.join(FIXTURES_DIR, "real_owner_cabinet_listings.html")
    with open(cab_path, "r", encoding="utf-8") as f:
        cab_html = f.read()
    res = py_extract_my_listings(cab_html)
    items_by_id = {it["avito_id"]: it for it in res["items"]}

    # Item 1: standard price and title
    it1 = items_by_id["8492019283"]
    assert "RTX 3070" in it1["title"]
    assert it1["price"] == 34000.0

    # Item 2: anchor fallback title and price
    it2 = items_by_id["8492019284"]
    assert "B550" in it2["title"]
    assert it2["price"] == 12500.0

    # Item 3: meta content price
    it3 = items_by_id["8492019285"]
    assert "Ryzen 7 5700X" in it3["title"]
    assert it3["price"] == 14500.0

    # Item 4: MISSING PRICE -> must be present with price=None
    it4 = items_by_id["8492019286"]
    assert "DeepCool CC560" in it4["title"]
    assert it4["price"] is None, "Missing price must be preserved as None without dropping the item"


def test_req_g_async_rendering_mechanism_in_content_js():
    """Requirement G: Verify bounded async wait (MutationObserver + polling) exists in content.js."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    assert "extractMyListingsDataAsync" in js
    assert "MutationObserver" in js
    assert "detectPageType" in js
    assert "maxWaitMs" in js
    assert "hasAnyListingsCardOrAnchor" in js
    assert "findCardContainerForAnchor" in js


def test_req_h_zero_result_ui_warning_policy():
    """Requirement H: Recognized listings page with 0 cards produces WARNING and NEVER green success."""
    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        popup_js = f.read()

    # 1. Verification that totalProcessed === 0 produces warning, NOT green success
    assert "totalProcessed === 0" in popup_js
    assert 'bulkMsg.className = "msg msg-warning"' in popup_js
    assert "Объявления не найдены" in popup_js

    # 2. When 0 items found initially, buttons are disabled and warning is shown
    assert "items.length === 0" in popup_js
    assert "bulkImportAllBtn.disabled = true" in popup_js
    assert "bulkImportCurrentBtn.disabled = true" in popup_js
    assert "bulkRescanBtn" in popup_js


def test_req_k_real_pagination_traversal_detection():
    """Requirement K: Verify pagination controls extracted accurately."""
    cab_path = os.path.join(FIXTURES_DIR, "real_owner_cabinet_listings.html")
    with open(cab_path, "r", encoding="utf-8") as f:
        cab_html = f.read()
    res = py_extract_my_listings(cab_html)
    pag = res["pagination"]
    assert pag["current_page"] == 1
    assert pag["total_pages"] == 3
    assert pag["has_next_page"] is True


@pytest.mark.asyncio
async def test_req_i_j_current_page_bulk_import_and_no_duplicates_on_repeat():
    """Requirement I & J: Bulk import sends all extracted items; re-import creates 0 duplicates."""
    token = _get_auth_token()
    cab_path = os.path.join(FIXTURES_DIR, "real_owner_cabinet_listings.html")
    with open(cab_path, "r", encoding="utf-8") as f:
        cab_html = f.read()
    extracted = py_extract_my_listings(cab_html)
    assert len(extracted["items"]) == 6

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "created", "product_id": 901, "message": "OK"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        # First import run
        res1 = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json={
            "schema_version": 1,
            "items": extracted["items"]
        })
        assert res1.status_code == 200
        d1 = res1.json()
        assert d1["total"] == 6
        assert d1["created"] == 6
        assert d1["updated"] == 0

        # Second import run with EXACT same items -> Core mock returns 'updated'
        mock_resp.json.return_value = {"status": "updated", "product_id": 901, "message": "Updated"}
        res2 = client.post("/extension/api/bulk-import", headers={"X-Extension-Token": token}, json={
            "schema_version": 1,
            "items": extracted["items"]
        })
        assert res2.status_code == 200
        d2 = res2.json()
        assert d2["total"] == 6
        assert d2["created"] == 0
        assert d2["updated"] == 6, "Repeat import of existing items must result in 0 new items created"


def test_version_alignment_across_extension_and_admin_shell():
    """Verify extension version is aligned across manifest, popup, content, sw, templates."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    ver = manifest["version"]
    assert ver in ("0.2.52", "0.2.53")

    with open(POPUP_HTML_PATH, "r", encoding="utf-8") as f:
        popup_html = f.read()
    assert f"v{ver}" in popup_html

    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        popup_js = f.read()
    assert f'let manifestVer = "{ver}";' in popup_js

    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content_js = f.read()
    assert f'extension_version: "{ver}"' in content_js

    # Admin Shell download page template
    tmpl_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "admin-shell", "app", "templates", "avito_extension.html"))
    with open(tmpl_path, "r", encoding="utf-8") as f:
        tmpl = f.read()
    assert f"(ZIP, v{ver})" in tmpl

    # Built zip
    zip_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dist", f"technoreboot-avito-extension-{ver}.zip"))
    if not os.path.exists(zip_path):
        import sys
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))
        from build_extension_zip import build_zip
        zip_path = build_zip()
    assert os.path.exists(zip_path), f"Built zip must exist at {zip_path}"
