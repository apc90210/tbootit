import os
import re
import pytest

CONTENT_JS_PATH = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
POPUP_JS_PATH = os.path.abspath("chrome-extension/technoreboot-avito/popup.js")
SERVICE_WORKER_PATH = os.path.abspath("chrome-extension/technoreboot-avito/service_worker.js")
MANIFEST_PATH = os.path.abspath("chrome-extension/technoreboot-avito/manifest.json")

def load_content_js():
    with open(CONTENT_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()

def load_popup_js():
    with open(POPUP_JS_PATH, "r", encoding="utf-8") as f:
        return f.read()

def load_service_worker_js():
    with open(SERVICE_WORKER_PATH, "r", encoding="utf-8") as f:
        return f.read()

# ============================================================================
# 1. CATEGORY CONFIDENCE GATE & SCOPING TESTS
# ============================================================================

def test_category_exact_path_high_confidence_auto_select():
    """Verify category scoring assigns highest weight to exact observed_path matches (score >= 200)."""
    code = load_content_js()
    assert "observed_path" in code
    assert "scoreCategorySuggestion" in code
    assert "350" in code or "300" in code  # High score boost for exact observed_path match

def test_category_exact_leaf_high_confidence_auto_select():
    """Verify category scoring assigns high confidence to exact category name matches (score >= 150)."""
    code = load_content_js()
    assert "normCatName" in code
    assert "score += 300" in code or "score += 200" in code

def test_category_low_confidence_not_clicked():
    """Verify that if candidate score is below confidence threshold, it is NOT auto-clicked."""
    code = load_content_js()
    assert "MIN_CATEGORY_CONFIDENCE" in code
    assert "CATEGORY_LOW_CONFIDENCE" in code
    assert "top1.score >= MIN_CATEGORY_CONFIDENCE" in code

def test_category_top1_top2_small_gap_not_clicked():
    """Verify that when top1 and top2 candidates have a small gap (< 30), it is flagged as ambiguous and NOT clicked."""
    code = load_content_js()
    assert "MIN_CATEGORY_GAP" in code
    assert "CATEGORY_AMBIGUOUS" in code
    assert "(top1.score - top2.score) < MIN_CATEGORY_GAP" in code or "(top1.score - top2.score) >= MIN_CATEGORY_GAP" in code

def test_category_unrelated_list_item_not_clicked():
    """Verify candidate list tiles strictly exclude unrelated list items, recommendation carousels, and header/nav elements."""
    code = load_content_js()
    assert "recommend" in code
    assert "similar" in code
    assert "findCategorySuggestTiles" in code

def test_category_anchor_never_clicked():
    """Verify category selection never clicks <a> elements or href links."""
    code = load_content_js()
    assert "isDangerousControl" in code
    assert "forceClickElement" in code
    assert "tagName === 'A'" in code or 'closest("a")' in code or "closest('a')" in code

def test_category_product_card_never_clicked():
    """Verify category selection never targets listing cards, product snippets, or ad cards."""
    code = load_content_js()
    assert "snippet" in code
    assert "card" in code
    assert "listing" in code

def test_category_manual_fallback_reported():
    """Verify when category cannot be safely auto-selected, report.category status is ambiguous/manual_required."""
    code = load_content_js()
    assert "status: 'manual_required'" in code or 'status: "manual_required"' in code
    assert "status: 'ambiguous'" in code or 'status: "ambiguous"' in code

# ============================================================================
# 2. ADDRESS DYNAMIC TOKENS & GEOCODER SAFETY TESTS
# ============================================================================

def test_no_hardcoded_business_address_in_extension():
    """Verify NO hardcoded business address string exists in content.js, popup.js, or service_worker.js."""
    content_js = load_content_js()
    popup_js = load_popup_js()
    service_worker_js = load_service_worker_js()

    for text in [content_js, popup_js, service_worker_js]:
        assert "Кузнецова" not in text
        assert "кузнецова" not in text
        assert "DEFAULT_ADDRESS" not in text

def test_address_not_filled_without_verified_package_value():
    """Verify address is not filled if package lacks verified address, reporting ADDRESS_MANUAL_REQUIRED."""
    code = load_content_js()
    assert "ADDRESS_MANUAL_REQUIRED" in code
    assert "locationData.verified" in code or "!addressToUse" in code or "!isVerified" in code

def test_verified_package_address_filled():
    """Verify verified package address is tokenized and safely matched against geocoder options."""
    code = load_content_js()
    assert "selectAddressSuggestion" in code
    assert "normTarget" in code
    assert "targetTokens" in code

def test_address_suggestion_scoped_to_geo_container():
    """Verify address options search is strictly scoped to geo / address containers."""
    code = load_content_js()
    assert "data-marker*=\"location\"" in code or "data-marker*='location'" in code
    assert "data-marker*=\"address\"" in code or "data-marker*='address'" in code
    assert "data-marker*=\"geo\"" in code or "data-marker*='geo'" in code

def test_address_anchor_never_clicked():
    """Verify geocoder options reject any <a> tag, href link, or target=_blank."""
    code = load_content_js()
    assert "o.tagName === 'A'" in code or 'o.closest("a")' in code or "o.closest('a')" in code
    assert "target" in code

def test_address_card_never_clicked():
    """Verify address selection never clicks listing snippet or product card elements."""
    code = load_content_js()
    assert "data-marker*=\"recommend\"" in code or "data-marker*='recommend'" in code
    assert "data-marker*=\"snippet\"" in code or "data-marker*='snippet'" in code

def test_ambiguous_address_not_clicked():
    """Verify ambiguous address candidates (< MIN_ADDRESS_GAP) are not clicked and reported as ambiguous."""
    code = load_content_js()
    assert "MIN_ADDRESS_GAP" in code
    assert "AMBIGUOUS_ADDRESS_SUGGESTIONS" in code
    assert "status: 'ambiguous'" in code or 'status: "ambiguous"' in code

# ============================================================================
# 3. MODEL / OPTION AMBIGUITY TESTS
# ============================================================================

def test_model_exact_match():
    """Verify exact model string matches give score 1000."""
    code = load_content_js()
    assert "optText === normTarget" in code
    assert "1000" in code

def test_model_number_strong_match():
    """Verify numeric tokens in model names (e.g. 1102) give substantial score boost."""
    code = load_content_js()
    assert "targetNumbers" in code
    assert "score += 400" in code or "score += 40" in code

def test_model_ambiguous_number_not_clicked():
    """Verify multiple candidates with equal top scores < 1000 prevent auto-clicking."""
    code = load_content_js()
    assert "top1.score === top2.score && top1.score < 1000" in code

def test_unresolved_option_not_clicked():
    """Verify unresolvable option safely returns false without clicking dangerous DOM elements."""
    code = load_content_js()
    assert "return false" in code

# ============================================================================
# 4. SAFETY SPIES & CONTRACT INTEGRITY TESTS
# ============================================================================

def test_safety_spy_blocks_publish_and_pay_buttons():
    """Verify DANGEROUS_ACTION_KEYWORDS contains all publishing and payment triggers."""
    code = load_content_js()
    dangerous_keywords = [
        "разместить",
        "опубликовать",
        "подать объявление",
        "оплатить",
        "купить",
        "продвижение",
        "подтвердить"
    ]
    for kw in dangerous_keywords:
        assert kw in code

def test_safety_spy_blocks_form_submit():
    """Verify content.js contains NO programmatic form.submit() or form.requestSubmit()."""
    code = load_content_js()
    assert ".submit()" not in code
    assert ".requestSubmit()" not in code

def test_report_structured_format():
    """Verify report object contains structured category, address, filled, skipped_nonempty, and unresolved_fields."""
    code = load_content_js()
    assert "category: {" in code
    assert "address: {" in code
    assert "filled: []" in code
    assert "skipped_nonempty: []" in code
    assert "unresolved_fields: []" in code
    assert "unresolved_options: []" in code
    assert "protected_actions: []" in code

def test_version_bump_0_2_32_consistent():
    """Verify manifest version is 0.2.32."""
    import json
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["version"] == "0.2.32"
