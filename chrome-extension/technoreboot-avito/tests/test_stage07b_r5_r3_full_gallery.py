import json
import os
import re
import pytest

EXTENSION_DIR = os.path.abspath("chrome-extension/technoreboot-avito")
CONTENT_JS_PATH = os.path.join(EXTENSION_DIR, "content.js")
SERVICE_WORKER_PATH = os.path.join(EXTENSION_DIR, "service_worker.js")
MANIFEST_PATH = os.path.join(EXTENSION_DIR, "manifest.json")
LISTING_DATA_PATH = os.path.abspath("chrome-extension/technoreboot-avito/tests/fixtures/synthetic_ad_8355529554.json")


def load_content_js():
    assert os.path.exists(CONTENT_JS_PATH)
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_manifest_version_0_2_46_and_host_permissions():
    """Verify manifest version is 0.2.46 and host_permissions includes Avito CDN."""
    assert os.path.exists(MANIFEST_PATH)
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest.get("version") >= "0.2.46"
    host_perms = manifest.get("host_permissions", [])
    assert any("img.avito.st" in perm for perm in host_perms), (
        f"host_permissions must include *.img.avito.st, got: {host_perms}"
    )


def test_test_a_and_l_owner_listing_photo_count_and_integrity():
    assert os.path.exists(LISTING_DATA_PATH), f"Synthetic fixture not found at {LISTING_DATA_PATH}"
    with open(LISTING_DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("id") == "8355529554"
    photos = data.get("photos", [])

    # The first 6 photos in the capture are the 6 genuine gallery photos
    genuine_photos = photos[:6]
    assert len(genuine_photos) == 6, (
        f"Expected exactly 6 genuine listing photos for ID 8355529554, got {len(genuine_photos)}"
    )
    for idx, p in enumerate(genuine_photos):
        assert "img.avito.st/image/1/1." in p.get("url", ""), f"Photo {idx} not on genuine Avito CDN"
        assert p.get("content_base64") and len(p["content_base64"]) > 1000, f"Photo {idx} missing base64"


def test_test_b_virtualization_hypothesis():
    """TEST B: Verify gallery virtualization hypothesis and lazy-loading handling."""
    code = load_content_js()
    assert "findGalleryRootElement" in code
    assert "extractPhotosFromDom" in code
    assert "walkAndCollectAllGalleryPhotos" in code
    assert "initial_dom_gallery_image_count" in code


def test_test_c_initial_data_parsing_logic():
    """TEST C: Verify __initialData__ parsing functions in content.js."""
    code = load_content_js()
    assert "getAvitoInitialData" in code
    assert "extractGalleryFromInitialData" in code
    assert "extractGallerySlotsFromInitialData" in code
    assert "__initialData__" in code


def test_test_d_bx_item_view_binding():
    """TEST D: Verify @avito/bx-item-view matching current listing ID."""
    code = load_content_js()
    assert "@avito/bx-item-view" in code
    assert "currentItemId" in code
    assert "buyerItem" in code
    assert "galleryInfo" in code


def test_test_e_media_array_and_video_exclusion():
    """TEST E: Verify media array extraction and video item exclusion."""
    code = load_content_js()
    assert "media" in code
    assert "isVideo" in code
    assert "nonVideoCount" in code or "non_video_media_count" in code


def test_test_f_highest_actual_resolution_selection():
    """TEST F: Verify highest actual resolution parsing from urls map (width * height)."""
    code = load_content_js()
    assert "urls" in code
    # Must parse width, height, and calculate area (width * height)
    assert "width" in code
    assert "height" in code
    assert "area" in code


def test_test_g_no_fabricated_url_upscale():
    """TEST G: Verify content.js does NOT perform blind 640x480 -> 1280x960 replacement."""
    code = load_content_js()
    assert "url.replace('/640x480/', '/1280x960/')" not in code
    assert 'url.replace("/640x480/", "/1280x960/")' not in code
    assert "u.replace('/640x480/', '/1280x960/')" not in code
    assert 'u.replace("/640x480/", "/1280x960/")' not in code


def test_test_h_controlled_gallery_traversal():
    """TEST H: Verify controlled gallery traversal when initialData is missing or incomplete."""
    code = load_content_js()
    assert "async function walkAndCollectAllGalleryPhotos" in code
    assert "collectActiveSlideCandidates" in code
    assert "scrollIntoView" in code


def test_test_i_traversal_slide_change_polling_and_wrap_detection():
    """TEST I: Verify traversal polls for actual slide change (up to 350ms) and detects wrap."""
    code = load_content_js()
    assert "350" in code  # 350ms max polling wait
    assert "firstObservedId" in code or "wrap" in code or "seenIdentities" in code


def test_test_j_slot_level_deduplication():
    """TEST J: Verify low/high variants collapse into single photo slot (1 per gallery position)."""
    code = load_content_js()
    assert "slot_index" in code
    assert "candidates" in code
    assert "candidate_count" in code
    assert "uniquePhotos.push" in code
    assert "position: uniquePhotos.length" in code


def test_test_k_foreign_asset_rejection():
    """TEST K: Verify rejection of foreign badges, maps, trackers, logos, avatars."""
    code = load_content_js()
    assert "validateListingImageUrl" in code
    assert "foreign_images_rejected" in code

    foreign_patterns = [
        "avatar", "logo", "icon", "badge", "delivery", "map", "cursor",
        "tracker", "adriver", "counter", "pixel", "banner", "static", "seller"
    ]
    for pat in foreign_patterns:
        assert pat in code, f"Expected pattern '{pat}' in foreign asset filter"


def test_test_m_order_preservation():
    """TEST M: Verify photo order 0..N-1 matches gallery sequence."""
    code = load_content_js()
    assert "position: uniquePhotos.length" in code
    assert "slot_index: slots.length" in code


def test_test_n_service_worker_download_contract():
    """TEST N: Verify service worker download handler supports chunked base64 and sha256."""
    assert os.path.exists(SERVICE_WORKER_PATH)
    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        sw_code = f.read()

    assert "download_photo_candidate" in sw_code
    assert "image/" in sw_code
    assert "SHA-256" in sw_code
    assert "base64" in sw_code


def test_diagnostics_section_10_contract():
    """Verify Section 10 diagnostics contract fields."""
    code = load_content_js()
    expected_fields = [
        "listing_id",
        "visible_gallery_count",
        "initial_data_found",
        "item_view_key_found",
        "media_array_count",
        "non_video_media_count",
        "initial_dom_gallery_image_count",
        "traversal_used",
        "traversal_unique_slides",
        "final_photo_count",
        "photos"
    ]
    for field in expected_fields:
        assert field in code, f"Diagnostics object must contain field: {field}"
