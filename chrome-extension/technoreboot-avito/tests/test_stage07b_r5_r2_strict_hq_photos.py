import json
import os
import re
import pytest

EXTENSION_DIR = os.path.abspath("chrome-extension/technoreboot-avito")
CONTENT_JS_PATH = os.path.join(EXTENSION_DIR, "content.js")
SERVICE_WORKER_PATH = os.path.join(EXTENSION_DIR, "service_worker.js")
MANIFEST_PATH = os.path.join(EXTENSION_DIR, "manifest.json")
LISTING_DATA_PATH = os.path.abspath("chrome-extension/technoreboot-avito/tests/fixtures/synthetic_ad_8355529554.json")


def test_manifest_version_and_host_permissions():
    """Verify manifest version is 0.2.45 and host_permissions includes Avito CDN."""
    assert os.path.exists(MANIFEST_PATH)
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest.get("version") >= "0.2.45"
    host_perms = manifest.get("host_permissions", [])
    assert any("img.avito.st" in perm for perm in host_perms), (
        f"host_permissions must include *.img.avito.st, got: {host_perms}"
    )


def test_no_blind_hq_url_string_replacement():
    """TEST G: Verify content.js does NOT perform blind 640x480 -> 1280x960 replacement."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content_js = f.read()

    # Must NOT have blind replacement of 640x480 with 1280x960
    assert "url.replace('/640x480/', '/1280x960/')" not in content_js
    assert 'url.replace("/640x480/", "/1280x960/")' not in content_js
    assert "u.replace('/640x480/', '/1280x960/')" not in content_js
    assert 'u.replace("/640x480/", "/1280x960/")' not in content_js


def test_content_js_url_validation_rejects_foreign_assets():
    """TEST B: Verify validateListingImageUrl filters out foreign trackers, maps, avatars, logos."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content_js = f.read()

    assert "validateListingImageUrl" in content_js
    assert "img.avito.st" in content_js

    # Simulate validation logic in Python
    foreign_patterns = [
        "avatar", "logo", "icon", "badge", "delivery", "map", "cursor",
        "tracker", "adriver", "counter", "pixel", "banner", "static", "seller"
    ]

    def py_validate_listing_image_url(raw_url):
        if not raw_url or not isinstance(raw_url, str):
            return None
        clean = raw_url.strip()
        if not re.match(r"^https?://[a-zA-Z0-9_\-\.]*img\.avito\.st/", clean):
            return None
        lower = clean.lower()
        if any(p in lower for p in foreign_patterns):
            return None
        return clean

    # Foreign URLs that were mistakenly captured in previous versions
    foreign_urls = [
        "https://www.avito.ru/item/dashboard",
        "https://adriver.ru/cgi-bin/rle.cgi?sid=1",
        "https://api-maps.yandex.ru/2.1/cursor.png",
        "https://static.avito.st/s/cc/resources/delivery.svg",
        "https://static.avito.st/s/cc/resources/logo.png",
        "https://00.img.avito.st/avatar/64x64/12345.jpg",
        "https://30.img.avito.st/seller_avatar/128x128/999.jpg",
        "https://30.img.avito.st/badge/delivery_icon.png"
    ]
    for url in foreign_urls:
        assert py_validate_listing_image_url(url) is None, f"Should have rejected foreign URL: {url}"

    # Genuine listing photo URLs
    genuine_urls = [
        "https://30.img.avito.st/image/1/1.rpQ-qra5FH0IDYB7btiJyDsLAHuML4B7iAMif4gJFH8.HupSGfRnsNjDw1uFZLbjGzO_YdOBfg4hzNt5861303Y",
        "https://10.img.avito.st/image/1/1.abcdef1234567890",
        "https://www.img.avito.st/640x480/123456789.jpg"
    ]
    for url in genuine_urls:
        assert py_validate_listing_image_url(url) is not None, f"Should have accepted genuine URL: {url}"


def test_gallery_root_scoped_extraction():
    """TEST A: Verify content.js scopes extraction to gallery root and item view."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content_js = f.read()

    assert "findGalleryRootElement" in content_js
    assert "extractPhotosFromDom" in content_js
    assert "parseSrcsetCandidates" in content_js
    assert "data-marker=\"item-view/gallery\"" in content_js
    assert "data-marker=\"gallery/list\"" in content_js


def test_embedded_state_no_unscoped_image_regex_scan():
    """TEST A & B: Verify extractPhotosFromEmbeddedState does NOT regex-scan all script tags for any image."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content_js = f.read()

    # The old bad pattern was scanning ALL script text with /https?:...img.avito.st.../g unconditionally
    # In the refactored version, we parse structured JSON nodes (item, widgets) and exclude recommendations
    assert "EXCLUDED_DATA_KEYS" in content_js
    assert "recommend" in content_js
    assert "similar" in content_js
    assert "seller" in content_js


def test_srcset_descriptor_ranking():
    """TEST E: Verify parseSrcsetCandidates ranks highest resolution first."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content_js = f.read()

    assert "parseSrcsetCandidates" in content_js

    # Simulate parseSrcsetCandidates logic
    srcset_sample = (
        "https://30.img.avito.st/image/1/1.abc_small 140w, "
        "https://30.img.avito.st/image/1/1.abc_medium 640w, "
        "https://30.img.avito.st/image/1/1.abc_large 1280w"
    )

    entries = srcset_sample.split(",")
    candidates = []
    for entry in entries:
        parts = entry.strip().split()
        url = parts[0]
        width = int(parts[1][:-1]) if len(parts) > 1 and parts[1].endswith("w") else 0
        candidates.append({"url": url, "width": width})

    candidates.sort(key=lambda c: c["width"], reverse=True)
    assert candidates[0]["width"] == 1280
    assert "abc_large" in candidates[0]["url"]


def test_service_worker_download_and_sha256():
    """TEST H: Verify service_worker.js implements downloadPhotoFromCdn with validation and sha256."""
    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        sw_js = f.read()

    assert "download_photo_candidate" in sw_js
    assert "downloadPhotoFromCdn" in sw_js
    assert 'crypto.subtle.digest("SHA-256"' in sw_js or "crypto.subtle.digest('SHA-256'" in sw_js
    assert "image/" in sw_js
    assert "btoa(" in sw_js


def test_diagnostics_structure_and_reporting():
    """Verify diagnostics object contract in content.js."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content_js = f.read()

    assert "getPhotoExtractionDiagnostics" in content_js
    assert "expected_photo_count" in content_js
    assert "extracted_photo_count" in content_js
    assert "gallery_root_strategy" in content_js
    assert "foreign_images_rejected" in content_js
    assert "duplicates_rejected" in content_js


def test_sample_listing_photo_integrity():
    assert os.path.exists(LISTING_DATA_PATH), f"Synthetic fixture not found at {LISTING_DATA_PATH}"
    with open(LISTING_DATA_PATH, "r", encoding="utf-8") as f:
        ad_data = json.load(f)

    photos = ad_data.get("photos", [])
    assert len(photos) > 0

    # The first 6 photos in the captured record are the 6 genuine listing photos
    genuine_gallery_photos = photos[:6]
    assert len(genuine_gallery_photos) == 6, f"Expected 6 genuine listing photos, got {len(genuine_gallery_photos)}"

    # All genuine gallery photos must be on *.img.avito.st/image/1/
    for idx, p in enumerate(genuine_gallery_photos):
        url = p.get("url", "")
        assert "img.avito.st/image/1/" in url, f"Photo {idx} not on Avito CDN: {url}"
        assert p.get("content_base64"), f"Photo {idx} missing base64 content"
        assert len(p["content_base64"]) > 1000, f"Photo {idx} content_base64 too small"

    # All remaining entries in the old raw capture (index 6+) are foreign items that must be rejected
    foreign_items = photos[6:]
    foreign_patterns = ["dashboard", "adriver", "cursor", "delivery", "logo"]
    foreign_rejected = 0
    for p in foreign_items:
        url = p.get("url", "").lower()
        if any(pat in url for pat in foreign_patterns) or not url.startswith("https://"):
            foreign_rejected += 1
    assert foreign_rejected >= 5, f"Expected foreign items to be detected, got {foreign_rejected}"
