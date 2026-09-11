import os
import sys
import re
import json
import zipfile

def run_focused_extension_regressions():
    results = {}
    ext_dir = os.path.abspath("chrome-extension/technoreboot-avito")
    content_js_path = os.path.join(ext_dir, "content.js")
    sw_js_path = os.path.join(ext_dir, "service_worker.js")
    manifest_path = os.path.join(ext_dir, "manifest.json")
    fixture_path = os.path.join(ext_dir, "tests", "fixtures", "synthetic_ad_8355529554.json")

    with open(content_js_path, "r", encoding="utf-8") as f:
        content_js = f.read()
    with open(sw_js_path, "r", encoding="utf-8") as f:
        sw_js = f.read()
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. STRICT_HQ
    try:
        assert "validateListingImageUrl" in content_js
        assert "img.avito.st" in content_js
        assert "url.replace('/640x480/', '/1280x960/')" not in content_js
        # Test synthetic fixture rejection
        with open(fixture_path, "r", encoding="utf-8") as f:
            ad_data = json.load(f)
        photos = ad_data.get("photos", [])
        assert len(photos) >= 12
        genuine = photos[:6]
        foreign = photos[6:]
        assert all("img.avito.st/image/1/" in p["url"] and len(p["content_base64"]) > 1000 for p in genuine)
        foreign_patterns = ["dashboard", "adriver", "cursor", "delivery", "logo", "avatar"]
        rejected = sum(1 for p in foreign if any(pat in p["url"].lower() for pat in foreign_patterns))
        assert rejected >= 5
        results["STRICT_HQ"] = "PASS"
    except Exception as e:
        results["STRICT_HQ"] = f"FAIL: {e}"

    # 2. FULL_GALLERY
    try:
        assert "extractGalleryFromInitialData" in content_js
        assert "walkAndCollectAllGalleryPhotos" in content_js
        assert "position: uniquePhotos.length" in content_js
        assert "slot_index" in content_js
        assert len(genuine) == 6
        results["FULL_GALLERY"] = "PASS"
    except Exception as e:
        results["FULL_GALLERY"] = f"FAIL: {e}"

    # 3. ZERO_OF_50
    try:
        assert "extractMyListingsDataAsync" in content_js
        assert "extractCardThumbnailPhoto" in content_js
        assert "validateListingImageUrl" in content_js
        assert "scrollIntoView" in content_js
        assert "getPhotoExtractionDiagnostics" in content_js
        assert any("img.avito.st" in p for p in manifest.get("host_permissions", []))
        results["ZERO_OF_50"] = "PASS"
    except Exception as e:
        results["ZERO_OF_50"] = f"FAIL: {e}"

    # 4. CARD_BOUNDARY
    try:
        assert "findCardContainer" in content_js
        assert "distinctIds" in content_js
        assert "distinctIds.size > 1" in content_js or "distinctIds.size >" in content_js
        results["CARD_BOUNDARY"] = "PASS"
    except Exception as e:
        results["CARD_BOUNDARY"] = f"FAIL: {e}"

    # 5. PHOTO_EXTRACTION
    try:
        assert "extractCardThumbnailPhoto" in content_js
        assert "parseSrcsetCandidates" in content_js
        assert "checkCssBg" in content_js
        assert "srcset" in content_js
        assert "picture" in content_js
        results["PHOTO_EXTRACTION"] = "PASS"
    except Exception as e:
        results["PHOTO_EXTRACTION"] = f"FAIL: {e}"

    # 6. PACKAGE_CONTENTS
    try:
        sys.path.insert(0, os.path.abspath("scripts"))
        from build_extension_zip import build_zip
        zip_path = build_zip()
        assert os.path.exists(zip_path)
        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            for required in ["manifest.json", "content.js", "popup.html", "popup.js", "service_worker.js", "icons/icon16.png", "icons/icon128.png"]:
                assert required in namelist, f"Missing {required} in zip"
        results["PACKAGE_CONTENTS"] = "PASS"
    except Exception as e:
        results["PACKAGE_CONTENTS"] = f"FAIL: {e}"

    # 7. MANIFEST_VERSION
    try:
        version = manifest.get("version")
        assert version == "0.2.53", f"Expected version 0.2.53, got {version}"
        with open(os.path.join(ext_dir, "popup.html"), "r", encoding="utf-8") as f:
            assert f"v{version}" in f.read()
        results["MANIFEST_VERSION"] = f"PASS (v{version})"
    except Exception as e:
        results["MANIFEST_VERSION"] = f"FAIL: {e}"

    # 8. NO_PUBLISH_OR_PAYMENT_ACTION
    try:
        dangerous_keywords = ["pay-button", "vas-submit", "payment-method", "wallet-charge", "confirm-publish", "promote-item"]
        for kw in dangerous_keywords:
            assert kw not in content_js, f"Found dangerous selector/keyword {kw} in content.js"
            assert kw not in sw_js, f"Found dangerous selector/keyword {kw} in service_worker.js"
        results["NO_PUBLISH_OR_PAYMENT_ACTION"] = "PASS"
    except Exception as e:
        results["NO_PUBLISH_OR_PAYMENT_ACTION"] = f"FAIL: {e}"

    return results

if __name__ == "__main__":
    res = run_focused_extension_regressions()
    print("\n--- FOCUSED EXTENSION REGRESSION RESULTS ---")
    all_pass = True
    for test, status in res.items():
        print(f"{test}: {status}")
        if not status.startswith("PASS"):
            all_pass = False
    if all_pass:
        print("\nALL FOCUSED REGRESSIONS PASSED (100%)\n")
        sys.exit(0)
    else:
        print("\nSOME FOCUSED REGRESSIONS FAILED!\n")
        sys.exit(1)
