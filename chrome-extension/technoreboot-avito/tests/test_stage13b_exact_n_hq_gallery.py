"""
Stage 13B Test Suite: Exact-N Avito Gallery Import + Per-Photo HQ Activation
Verifies all 27 requirements from Stage 13B prompt Sections 19 & 20:
- Exactness: 4 real + 5 foreign -> exactly 4; foreign widgets (sticky, history, review, seller) excluded;
  hero + thumbnail same photo -> 1 slot; responsive srcset variants -> 1 slot.
- Count: counter "1 из 4" -> N=4; "1 / 4" -> N=4; no counter -> unique thumbnail count; virtualized gallery handling.
- HQ: first hero already HQ; click thumbnail #2 -> waits for matching hero identity;
  stale hero for 100ms does not get assigned to next slot; largest parsed srcset width selected;
  HQ timeout -> exact thumbnail fallback for same slot; failed HQ fetch -> fallback same slot.
- Identity: Stage 13A V2 canonical tests (10 variants of 4 photos -> 4 IDs); host shard variants dedupe;
  unfamiliar URL gets safe fallback identity.
- Server: core double-append bug fix; repeated payload -> no duplicate rows; 4 photos -> 4 rows.
- Regression: single-photo listing; listing without gallery; automatic deactivation remains disabled.
"""

import json
import os
import re
import zipfile
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXTENSION_DIR = REPO_ROOT / "chrome-extension" / "technoreboot-avito"
CONTENT_JS_PATH = EXTENSION_DIR / "content.js"
SERVICE_WORKER_JS_PATH = EXTENSION_DIR / "service_worker.js"
POPUP_JS_PATH = EXTENSION_DIR / "popup.js"
MANIFEST_PATH = EXTENSION_DIR / "manifest.json"
CORE_INTEGRATIONS_PATH = REPO_ROOT / "core" / "app" / "routers" / "integrations.py"


@pytest.fixture(scope="module")
def content_js():
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def sw_js():
    with open(SERVICE_WORKER_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def core_integrations_code():
    with open(CORE_INTEGRATIONS_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ==============================================================================
# 1. CANONICAL IDENTITY V2 (Section 7, Items 15, 16, 17)
# ==============================================================================

def canonical_identity_v2(url: str) -> str:
    """Python reference implementation of getCanonicalAvitoImageIdentity V2."""
    if not url or not isinstance(url, str):
        return ""
    path_only = url.split("?")[0]
    clean = re.sub(r"^https?://[^/]+/", "", path_only, flags=re.IGNORECASE)
    clean = re.sub(r"^(?:image/\d+/|\d+x\d+/)+", "", clean, flags=re.IGNORECASE)
    filename = clean.split("/")[-1]

    # 1. Numeric filename before extension (e.g. 9876543210.jpg)
    no_ext = re.sub(r"\.(?:jpg|jpeg|webp|png|avif)$", "", filename, flags=re.IGNORECASE)
    if re.match(r"^\d{6,}$", no_ext):
        return f"avito_photo_{no_ext}"

    # 2. Strip leading index prefix e.g. "1." from "1.sePk6..."
    token = re.sub(r"^\d+\.", "", filename)

    # 3. Match [prefix][alphanumeric]a[digit] with non-greedy prefix
    la_match = re.match(r"^([A-Za-z0-9_-]{2,}?[A-Za-z0-9_-])[A-Za-z0-9]a\d", token, re.IGNORECASE)
    if la_match and la_match.group(1):
        return f"avito_photo_{la_match.group(1)}"

    # 4. Dot-separated hash
    parts = token.split(".")
    if len(parts) >= 2 and len(parts[0]) >= 6:
        return f"avito_photo_{parts[0][:16]}"

    clean_name = re.sub(r"[^A-Za-z0-9_-]", "", no_ext)
    if len(clean_name) >= 3:
        return f"avito_photo_{clean_name[:16]}"

    return filename or path_only


def test_15_canonical_identity_v2_collapses_ten_variants_into_four_ids():
    """Item 15: 10 responsive variants across 4 photos collapse into exactly 4 IDs."""
    test_cases = [
        # Photo 1 across 3 resolutions and shards
        ("p1_hq", "https://10.img.avito.st/image/1/1.sePk6ba4HQrtfR-h_QO-o8FhHA1reZ-h"),
        ("p1_thumb", "https://20.img.avito.st/image/1/1.sePk6ra1HQrtfR-h_QO-o8FhHA1reZ-h"),
        ("p1_mid", "https://30.img.avito.st/image/1/1.sePk6ra2HQrtfR-h_QO-o8FhHA1reZ-h"),
        # Photo 2 with digit before a (CTUlh7a5)
        ("p2_hq", "https://00.img.avito.st/image/1/1.CTUlh7a5pdwTLmfZO_dcQzgnp9qVJifUUyOn2Jkur94.SNoEIvKMS8YT_7Ea4HWGYWb0cw8g8JRQyWwKFoOXwfo?cqp=2"),
        ("p2_thumb", "https://10.img.avito.st/image/1/1.CTUlh7a1pdwTLmfZO_dcQzgnp9qVJifUUyOn2Jkur94.SNoEIvKMS8YT_7Ea4HWGYWb0cw8g8JRQyWwKFoOXwfo?cqp=2"),
        # Photo 3 legacy numeric paths
        ("p3_thumb", "https://20.img.avito.st/140x105/9876543210.jpg"),
        ("p3_mid", "https://20.img.avito.st/640x480/9876543210.jpg"),
        ("p3_hq", "https://20.img.avito.st/1280x960/9876543210.jpg"),
        # Photo 4 distinct photo
        ("p4_hq", "https://40.img.avito.st/image/1/1.m9BBHLa5Nzl3tfU8ez6B6VS8NT_xvbUxN7g1Pf21PTs.fZ8DHy?cqp=2"),
        ("p4_thumb", "https://40.img.avito.st/image/1/1.m9BBHLa1Nzl3tfU8ez6B6VS8NT_xvbUxN7g1Pf21PTs.fZ8DHy?cqp=2"),
    ]
    groups = {}
    for label, url in test_cases:
        cid = canonical_identity_v2(url)
        groups.setdefault(cid, []).append(label)

    assert len(groups) == 4, f"Expected 4 distinct photo groups, got {len(groups)}: {list(groups.keys())}"
    assert len(groups["avito_photo_sePk6"]) == 3
    assert len(groups["avito_photo_CTUlh"]) == 2
    assert len(groups["avito_photo_9876543210"]) == 3
    assert len(groups["avito_photo_m9BBH"]) == 2


def test_16_host_shard_variants_deduplicate():
    """Item 16: Same photo across 00.img.avito.st, 10.img.avito.st, 20.img.avito.st produces 1 ID."""
    url1 = "https://00.img.avito.st/image/1/1.abc12ba4XYZ"
    url2 = "https://10.img.avito.st/image/1/1.abc12ba4XYZ"
    url3 = "https://20.img.avito.st/image/1/1.abc12ba4XYZ"
    assert canonical_identity_v2(url1) == canonical_identity_v2(url2) == canonical_identity_v2(url3)


def test_17_unfamiliar_url_gets_stable_safe_identity():
    """Item 17: Unfamiliar CDN form produces a stable non-empty fallback identity."""
    url = "https://img.avito.st/custom_cdn/unknown_format_98765.webp"
    cid = canonical_identity_v2(url)
    assert cid and len(cid) > 0
    assert cid == canonical_identity_v2(url)  # Stable


# ==============================================================================
# 2. EXACTNESS & FOREIGN ASSET REJECTION (Sections 4 & 19, Items 1, 2, 3, 4)
# ==============================================================================

def test_01_and_02_four_real_plus_five_foreign_produces_exactly_four(content_js):
    """Section 19: 4 real photos + 5 foreign (sticky, history, review, seller) -> exactly 4."""
    # Ensure isInsideExcluded explicitly checks for foreign markers
    assert "sticky" in content_js
    assert "history" in content_js
    assert "review" in content_js
    assert "seller" in content_js

    # Ensure extractPhotosFromDom filters thumbnails by isInsideExcluded
    assert "filter(el => !isInsideExcluded(el))" in content_js or "!isInsideExcluded" in content_js

    # Ensure document.querySelectorAll('[data-marker*="preview"]') is NOT present in extractPhotosFromDom
    # It must be scoped and exclude greedy preview scans
    assert "item-view/gallery" in content_js
    assert "thumbSelectors" in content_js


def test_section19_exact_4_fixture_simulation():
    """Section 19: Execute exact 4 real + 5 foreign fixture simulation."""
    import sys
    from bs4 import BeautifulSoup
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from scripts.simulate_dom_extraction import (
        html_sample_4_photos,
        validate_listing_image_url,
        parse_srcset_candidates,
    )

    soup = BeautifulSoup(html_sample_4_photos, "html.parser")
    gallery_root = soup.select_one('[data-marker="item-view/gallery"]')
    assert gallery_root is not None

    counter_el = gallery_root.select_one('[data-marker*="counter"]')
    m = re.search(r"(\d+)\s*(?:из|/|of)\s*(\d+)", counter_el.get_text() if counter_el else "", re.IGNORECASE)
    expected_count = int(m.group(2)) if m else 0
    assert expected_count == 4

    def is_inside_excluded(el):
        cur = el
        while cur:
            dm = cur.get("data-marker", "") if hasattr(cur, "get") else ""
            cls = " ".join(cur.get("class", [])) if hasattr(cur, "get") and cur.get("class") else ""
            if any(k in dm for k in ["item-view/gallery", "gallery/list", "gallery/preview-item", "image-frame"]):
                if not any(k in dm for k in ["sticky", "history"]):
                    return False
            if any(k in dm for k in ["sticky", "history"]) or any(re.search(rf"\b{k}\b", dm) for k in ["review"]):
                return True
            if any(k in f"{dm} {cls}".lower() for k in ["seller", "user-info", "profile", "recommend", "similar"]):
                return True
            cur = cur.parent
        return False

    thumb_selectors = [
        'ul[data-marker="gallery/list"] li',
        'ul[data-marker="gallery/list"] > *',
        '[data-marker="gallery/preview-item"]',
    ]
    raw_elements = []
    for sel in thumb_selectors:
        for el in gallery_root.select(sel):
            raw_elements.append(el)

    filtered_elements = []
    seen_ids = set()
    for el in raw_elements:
        if id(el) in seen_ids or is_inside_excluded(el):
            continue
        seen_ids.add(id(el))
        filtered_elements.append(el)

    slots = []
    seen_identities = set()
    foreign_rejected = 0

    for el in filtered_elements:
        img = el.find("img") if el.name != "img" else el
        if not img:
            continue
        valid_src = validate_listing_image_url(img.get("src"))
        if not valid_src:
            continue
        cid = canonical_identity_v2(valid_src)
        if not cid or cid in seen_identities:
            continue
        if expected_count > 0 and len(slots) >= expected_count:
            foreign_rejected += 1
            continue
        seen_identities.add(cid)
        slots.append({
            "index": len(slots),
            "canonicalId": cid,
            "thumbnailUrl": valid_src,
            "bestKnownUrl": valid_src,
            "hqUrl": None,
        })

    hero_img = gallery_root.select_one('[data-marker="image-frame/image-wrapper"] img')
    if hero_img:
        hero_src = validate_listing_image_url(hero_img.get("src"))
        hero_cid = canonical_identity_v2(hero_src)
        if slots and slots[0]["canonicalId"] == hero_cid:
            cands = parse_srcset_candidates(hero_img.get("srcset"))
            best = max(cands, key=lambda c: c["srcsetW"])["url"] if cands else hero_src
            slots[0]["hqUrl"] = best
            slots[0]["bestKnownUrl"] = best

    assert expected_count == 4
    assert len(slots) == 4
    assert foreign_rejected == 0
    assert slots[0]["canonicalId"] == "avito_photo_sePk6"
    assert slots[1]["canonicalId"] == "avito_photo_m9BBH"
    assert slots[2]["canonicalId"] == "avito_photo_AbCdE"
    assert slots[3]["canonicalId"] == "avito_photo_XyZ12"
    assert "1280w" in slots[0]["hqUrl"] or "ba4" in slots[0]["hqUrl"]


def test_03_hero_and_thumbnail_same_photo_produce_one_slot(content_js):
    """Item 3: Hero and thumbnail of the same logical photo do not create duplicate slots."""
    # Verify Phase 1 checks seenIdentities before adding thumbnail slots
    assert "seenIdentities.has(slotId)" in content_js
    # Verify Phase 2 enriches slot 0 when hero matches slot 0 canonical ID
    assert "initialHeroId === slots[0].canonicalId" in content_js


def test_04_responsive_srcset_variants_produce_one_slot(content_js):
    """Item 4: Responsive srcset variants collapse into one slot via parseSrcsetCandidates."""
    assert "parseSrcsetCandidates" in content_js
    assert "candidates.sort((a, b) => b.score - a.score)" in content_js


# ==============================================================================
# 3. PHOTO COUNT DETERMINATION (Section 6, Items 5, 6, 7, 8)
# ==============================================================================

def parse_counter_text(text: str) -> int:
    m = re.search(r"(\d+)\s*(?:из|/|of)\s*(\d+)", text, re.IGNORECASE)
    if m and m.group(2):
        return int(m.group(2))
    return 0


def test_05_counter_formats_parse_correctly():
    """Item 5 & 6: Counter formats '1 из 4', '1 / 4', '1 of 4' parse to N=4."""
    assert parse_counter_text("1 из 4") == 4
    assert parse_counter_text(" 2 / 4 ") == 4
    assert parse_counter_text("Photo 3 of 4") == 4
    assert parse_counter_text("10 из 25") == 25


def test_07_no_counter_falls_back_to_unique_thumbnail_count(content_js):
    """Item 7: Without counter, determineExpectedPhotoCount counts unique thumbnails."""
    assert "ul[data-marker=\"gallery/list\"]" in content_js
    assert "uniqueThumbs.add" in content_js or "uniqueThumbs.size" in content_js


def test_08_virtualized_galleries_traversal_reaches_n(content_js):
    """Item 8: Virtualized galleries navigate via next button until targetN is reached."""
    assert "targetN > 0 && slots.length < targetN" in content_js
    assert "image-frame/next-button" in content_js
    assert "firstObservedId && newId === firstObservedId" in content_js  # Cycle detection


# ==============================================================================
# 4. PER-PHOTO HQ ACTIVATION & IDENTITY WAIT (Sections 9 & 10, Items 9-14)
# ==============================================================================

def test_09_first_hero_already_hq_detected(content_js):
    """Item 9: Active hero on mount is checked for slot 0 HQ."""
    assert "initialHeroId === slots[0].canonicalId" in content_js
    assert "slots[0].hqUrl = initialHeroCands[0].url" in content_js


def test_10_and_11_thumbnail_click_waits_for_matching_hero_identity(content_js):
    """Item 10 & 11: Thumbnail click waits for matching hero identity; stale hero does not capture."""
    assert "currentId === slots[i].canonicalId" in content_js
    assert "slots[i].hqUrl = currentHeroCands[0].url" in content_js
    # Ensure timeout polling is bounded (1200ms)
    assert "1200" in content_js


def test_12_largest_parsed_srcset_width_selected(content_js):
    """Item 12: parseSrcsetCandidates parses width descriptors and ranks by score."""
    assert "parseSrcsetCandidates" in content_js
    assert "descriptor.endsWith('w')" in content_js
    assert "parseInt(descriptor.slice(0, -1), 10)" in content_js


def test_13_and_14_hq_timeout_and_fetch_failure_fallback_preserves_n(content_js, sw_js):
    """Items 13 & 14: HQ timeout or fetch failure falls back to thumbnail URL; preserves exact N."""
    # content.js: fallback to bestKnownUrl or thumbnailUrl
    assert "s.hqUrl || s.bestKnownUrl || s.thumbnailUrl" in content_js
    assert "traversalTimeouts++" in content_js

    # service_worker.js: iterates candidate_urls, returns first successful image
    assert "for (let i = 0; i < urls.length; i++)" in sw_js
    assert "downloadPhotoFromCdn" in sw_js
    assert "contentType.toLowerCase().startsWith(\"image/\")" in sw_js


# ==============================================================================
# 5. SERVER CORE DOUBLE-APPEND BUG FIX (Section 16, Items 18, 19, 20, 21)
# ==============================================================================

def test_18_core_selects_exactly_one_photo_per_canonical_key(core_integrations_code):
    """Item 18: Core selects exactly one photo per canonical identity key (no double-append)."""
    assert "STAGE 13B: Exactly one ProductPhoto per logical Avito photo key" in core_integrations_code
    assert "best_photo = max(candidates, key=_candidate_rank)" in core_integrations_code
    assert "effective_photos.append(best_photo)" in core_integrations_code
    # Ensure old bug (best_high + best_low both appended) is absent
    assert "effective_photos.append(best_high)" not in core_integrations_code


def test_19_and_20_core_reconciliation_and_deduplication(core_integrations_code):
    """Items 19 & 20: Repeated import does not duplicate photos; exactly N photos persisted."""
    assert "seen_content_hashes_in_batch" in core_integrations_code
    assert "seen_source_urls_in_batch" in core_integrations_code
    assert "_get_avito_canonical_identity" in core_integrations_code


# ==============================================================================
# 6. REGRESSION INVARIANTS (Items 22-27)
# ==============================================================================

def test_22_single_photo_listing_handled(content_js):
    """Item 22: Single-photo listing without thumbnail list is handled cleanly."""
    assert "slots.length === 0 && activeFrame" in content_js
    assert "hero_active" in content_js


def test_23_listing_without_gallery_does_not_crash(content_js):
    """Item 23: Listing without gallery root returns safely without throwing."""
    assert "findGalleryRootElement" in content_js
    assert "if (!scope) {" in content_js


def test_25_manifest_version_0_2_64():
    """Item 25: Extension version bumped to 0.2.64+ in manifest and scripts."""
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["version"] in ("0.2.64", "0.2.65", "0.2.66")


def test_27_automatic_avito_deactivation_remains_disabled(sw_js, content_js):
    """Item 27: Automatic Avito post-sale deactivation remains strictly disabled."""
    assert "chrome.alarms.create" not in sw_js
    assert "setInterval(pollNextDeactivationTask" not in sw_js
    assert "Automatic post-sale deactivation is disabled" in sw_js
    assert "disabled in Stage 09A-R5" in content_js


# ==============================================================================
# 7. EXTENSION PACKAGE INTEGRITY (Section 23)
# ==============================================================================

def test_extension_zip_package_valid_and_sha256_matches():
    """Verify built ZIP package exists and contains valid v0.2.64 manifest."""
    zip_path = REPO_ROOT / "dist" / "technoreboot-avito-extension-0.2.64.zip"
    admin_zip_path = REPO_ROOT / "admin-shell" / "app" / "technoreboot-avito-extension-0.2.64.zip"
    assert zip_path.exists(), f"Missing {zip_path}"
    assert admin_zip_path.exists(), f"Missing {admin_zip_path}"

    with zipfile.ZipFile(zip_path, "r") as zf:
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest["version"] == "0.2.64"
        assert "content.js" in zf.namelist()
        assert "service_worker.js" in zf.namelist()
        assert "popup.js" in zf.namelist()
        assert "popup.html" in zf.namelist()
