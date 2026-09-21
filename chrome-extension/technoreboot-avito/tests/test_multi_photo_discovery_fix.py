"""
Test suite verifying multi-photo discovery fixes across varied Avito DOM layouts,
resilient gallery root scoping, and next-button traversal unblocking.
"""

import json
import os
import re
import pytest
from pathlib import Path
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTENT_JS_PATH = REPO_ROOT / "chrome-extension" / "technoreboot-avito" / "content.js"


@pytest.fixture(scope="module")
def content_js():
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()


def test_find_gallery_root_element_checks_outer_containers_before_frame(content_js):
    """Verify outer gallery containers are checked before inner image-frame anchor."""
    idx_outer = content_js.find("outerGallerySelectors")
    idx_anchor = content_js.find("candidateSelectors")
    assert idx_outer != -1, "outerGallerySelectors must exist"
    assert idx_anchor != -1, "candidateSelectors must exist"
    assert idx_outer < idx_anchor, "outerGallerySelectors must precede candidateSelectors"
    assert "gallery-root" in content_js
    assert "gallery-layout" in content_js
    assert "item-view-gallery" in content_js


def test_find_gallery_root_element_climbs_out_of_image_frame(content_js):
    """Verify that image-frame anchor climbs up to enclosing parent rather than trapping query scope."""
    assert "el.closest('[data-marker=\"item-view/gallery\"]" in content_js
    assert "el.parentElement && (sel.includes('image-frame') || sel.includes('image-wrapper'))" in content_js


def test_gallery_thumb_selectors_include_modern_avito_variants(content_js):
    """Verify GALLERY_THUMB_SELECTORS contains carousel and class-based variants."""
    assert "GALLERY_THUMB_SELECTORS" in content_js
    assert "findGalleryThumbnailElements" in content_js
    for sel in [
        'ul[data-marker="gallery/list"] li',
        'div[class*="gallery-list"] > *',
        'ul[class*="gallery-list"] li',
        'div[class*="style-gallery-list"] li',
        '[data-marker="gallery/image"]',
        '[data-marker="slider-image/image"]',
    ]:
        assert sel in content_js, f"Missing selector: {sel}"


def test_find_gallery_thumbnail_elements_filters_foreign_widgets(content_js):
    """Verify findGalleryThumbnailElements strictly applies isInsideExcluded filtering."""
    assert "filtered = els.filter(el => !isInsideExcluded(el))" in content_js
    assert "topLevel = filtered.filter(el => !filtered.some(other => other !== el && other.contains(el)))" in content_js


def test_determine_expected_photo_count_uses_find_gallery_thumbnail_elements(content_js):
    """Verify determineExpectedPhotoCount discovers thumbnails across all layout variants."""
    det_fn = content_js[content_js.find("function determineExpectedPhotoCount"):content_js.find("function extractAllPhotos")]
    assert "findGalleryThumbnailElements(scope)" in det_fn
    assert "uniqueThumbs" in det_fn


def test_walk_next_button_unblocked_when_no_counter(content_js):
    """Verify next-button traversal is permitted when targetN is 0 and slots <= 1."""
    walk_fn = content_js[content_js.find("async function walkAndCollectAllGalleryPhotos"):content_js.find("function extractListingData")]
    assert "shouldWalkNext" in walk_fn
    assert "targetN > 0 && slots.length < targetN" in walk_fn
    assert "slots.length <= 1" in walk_fn
    assert "targetN === 0 && slots.length < 15" in walk_fn


def test_effective_target_n_does_not_truncate_genuine_traversed_slides(content_js):
    """Verify effectiveTargetN preserves multiple traversed slides when expected count was 0 or 1."""
    assert "effectiveTargetN" in content_js
    assert "traversalUsed && walkedSlots.length > expectedPhotoCount && expectedPhotoCount <= 1" in content_js


def test_extract_listing_data_multi_pass_triggers_traversal_on_dom_multi_photos(content_js):
    """Verify extractListingDataMultiPass runs traversal if DOM shows multiple photos or next button."""
    start = content_js.find("async function extractListingDataMultiPass")
    assert start != -1
    sub = content_js[start:start + 1200]
    assert "hasDomMultiPhotos" in sub
    assert "findGalleryThumbnailElements(galleryRoot).length > 1" in sub


def test_bs4_simulation_modern_carousel_gallery_discovers_all_photos():
    """Simulate modern Avito layout where thumbnails are nested in a carousel track."""
    html = '''
    <div class="style-item-view-gallery-3x8 gallery-root">
        <div data-marker="image-frame">
            <div data-marker="image-frame/image-wrapper">
                <img src="https://10.img.avito.st/image/1/1.hero123456.jpg" alt="Hero">
            </div>
            <button data-marker="image-frame/next-button" aria-label="Следующее фото"></button>
        </div>
        <div class="gallery-list-track">
            <div class="style-gallery-list-item">
                <img src="https://10.img.avito.st/image/1/1.thumbA11111.jpg">
            </div>
            <div class="style-gallery-list-item">
                <img src="https://10.img.avito.st/image/1/1.thumbB22222.jpg">
            </div>
            <div class="style-gallery-list-item">
                <img src="https://10.img.avito.st/image/1/1.thumbC33333.jpg">
            </div>
        </div>
    </div>
    <div data-marker="sticky-header">
        <img src="https://10.img.avito.st/image/1/1.foreignSticky.jpg">
    </div>
    <div data-marker="seller-info">
        <img src="https://10.img.avito.st/image/1/1.foreignSeller.jpg">
    </div>
    '''
    soup = BeautifulSoup(html, "html.parser")
    gallery_root = soup.select_one('.gallery-root')
    assert gallery_root is not None

    def is_inside_excluded(el):
        cur = el
        while cur:
            dm = cur.get("data-marker", "") if hasattr(cur, "get") else ""
            cls = " ".join(cur.get("class", [])) if hasattr(cur, "get") and cur.get("class") else ""
            if "sticky" in dm or "seller" in dm or "seller" in cls:
                return True
            cur = cur.parent
        return False

    thumb_selectors = [
        'div[class*="gallery-list"] > *',
        'div[class*="style-gallery-list"] li',
        'div[class*="style-gallery-list"] > *',
        'ul[data-marker="gallery/list"] li',
    ]

    found = []
    for sel in thumb_selectors:
        for el in gallery_root.select(sel):
            if not is_inside_excluded(el) and el not in found:
                found.append(el)

    # Top-level deduplication: remove any element whose ancestor is already in found
    top_level = [el for el in found if not any(other != el and el in other.descendants for other in found)]

    assert len(top_level) == 3
    img_srcs = [el.find('img')['src'] for el in top_level if el.find('img')]
    assert len(img_srcs) == 3
    assert any("thumbA11111" in s for s in img_srcs)
    assert any("thumbB22222" in s for s in img_srcs)
    assert any("thumbC33333" in s for s in img_srcs)
    assert not any("foreign" in s for s in img_srcs)
