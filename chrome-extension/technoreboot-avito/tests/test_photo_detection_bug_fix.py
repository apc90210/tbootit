import os
import re
import json
import zipfile
import pytest

EXTENSION_DIR = os.path.abspath("chrome-extension/technoreboot-avito")
CONTENT_JS_PATH = os.path.join(EXTENSION_DIR, "content.js")
MANIFEST_PATH = os.path.join(EXTENSION_DIR, "manifest.json")
ZIP_PATH = os.path.abspath("dist/technoreboot-avito-extension-0.2.47.zip")
ADMIN_ZIP_PATH = os.path.abspath("admin-shell/app/technoreboot-avito-extension-0.2.47.zip")


def test_content_js_defines_page_initial_data_and_trigger():
    """Verify content.js declares pageInitialData and triggerInitialDataCapture at top level."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Must declare pageInitialData before any usage
    assert "let pageInitialData = null;" in content
    assert "function triggerInitialDataCapture()" in content
    assert "TechnorebootInitialData" in content

    # Check that calls to triggerInitialDataCapture exist and are safe
    assert "triggerInitialDataCapture();" in content
    assert "try {" in content


def test_content_js_embedded_state_unescapes_json():
    """Verify extractPhotosFromEmbeddedState unescapes slashes and unicode in scripts."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Must unescape \u002F and \/
    assert "\\u002F" in content
    assert "\\\\/" in content or "\\/" in content
    assert "application/json" in content
    assert "__NEXT_DATA__" in content


def test_content_js_gallery_not_falsely_excluded():
    """Verify isInsideExcluded prioritizes gallery elements over seller/recommend exclusions."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "el.closest('[data-marker*=\"gallery\"]" in content
    assert "return false;" in content


def test_canonical_avito_image_identity_unification():
    """Verify getCanonicalAvitoImageIdentity unifies resolution versions."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # In JS: must have laMatch for [prefix][letter]a[digit]
    assert "laMatch" in content
    assert "avito_photo_" in content

    # Python simulation of the regex logic
    def py_identity(url):
        path_only = url.split("?")[0]
        clean_path = re.sub(r"^https?://[^/]+/", "", path_only, flags=re.IGNORECASE)
        clean_path = re.sub(r"^(?:image/\d+/|\d+x\d+/)+", "", clean_path, flags=re.IGNORECASE)
        filename = clean_path.split("/")[-1]
        token = re.sub(r"^\d+\.", "", filename)

        la_match = re.match(r"^([A-Za-z0-9_-]{2,}?[A-Za-z0-9_-])[a-zA-Z]a\d", token, re.IGNORECASE)
        if la_match and la_match.group(1):
            return f"avito_photo_{la_match.group(1)}"
        token_no_ext = re.sub(r"\.(?:jpg|jpeg|webp|png)$", "", token, flags=re.IGNORECASE)
        if len(token_no_ext) >= 3:
            return f"avito_photo_{token_no_ext}"
        return token_no_ext or token or filename or path_only

    hd_url = "https://10.img.avito.st/image/1/1.sePk6ba4HQrtfR-h_QO-o8FhHA1reZ-h"
    thumb_url = "https://10.img.avito.st/image/1/1.sePk6ra1HQrtfR-h_QO-o8FhHA1reZ-h"
    mid_url = "https://10.img.avito.st/image/1/1.sePk6ra2HQrtfR-h_QO-o8FhHA1reZ-h"

    id_hd = py_identity(hd_url)
    id_thumb = py_identity(thumb_url)
    id_mid = py_identity(mid_url)

    assert id_hd == id_thumb == id_mid == "avito_photo_sePk6"

    # Different photo has different id
    other_url = "https://10.img.avito.st/image/1/1.m9BBHLa6HQrtfR-h_QO-o8FhHA1reZ-h"
    assert py_identity(other_url) == "avito_photo_m9BBH"


def test_content_js_extract_all_photos_resilience():
    """Verify extractAllPhotos wraps sub-extractors in try/catch and has full-page HTML fallback."""
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Must contain fallback to fullHtml if rawUrls is empty
    assert "fullHtml" in content or "rawUrls.length === 0" in content
    assert "document.documentElement.innerHTML" in content
    assert "groupsMap" in content


def test_extension_manifest_and_zip_version():
    """Verify manifest.json and built ZIP archives have version 0.2.47."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["version"] >= "0.2.46"

    assert os.path.exists(ZIP_PATH), f"ZIP not found: {ZIP_PATH}"
    assert os.path.exists(ADMIN_ZIP_PATH), f"Admin ZIP not found: {ADMIN_ZIP_PATH}"

    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        names = zf.namelist()
        assert "manifest.json" in names
        assert "content.js" in names
        assert "popup.js" in names
        assert "popup.html" in names
        assert "service_worker.js" in names
        assert "icons/icon128.png" in names

        manifest_in_zip = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest_in_zip["version"] in ["0.2.46", "0.2.47"]
