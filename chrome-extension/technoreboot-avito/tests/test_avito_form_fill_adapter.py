import os
import pytest

def test_form_adapter_structure_in_content_js():
    """Verify content.js contains AvitoPublicationFormAdapter and fillAvitoPublicationForm."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    assert os.path.exists(content_js_path)

    with open(content_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "fillAvitoPublicationForm" in content
    assert "CORE_FIELD_ALIASES" in content
    assert "normalizeFieldLabel" in content
    assert "resolveFieldLabel" in content
    assert "setReactInputValue" in content
    assert "matchCoreFieldRole" in content

def test_fill_empty_only_discipline():
    """Verify content.js checks if field value is non-empty before setting."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    with open(content_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "skipped_nonempty" in content
    assert "currentVal !== ''" in content or "currentVal !== \"\"" in content

def test_react_controlled_input_event_dispatch():
    """Verify setReactInputValue dispatches input, change, and blur bubbling events."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    with open(content_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "new Event('input', { bubbles: true })" in content
    assert "new Event('change', { bubbles: true })" in content
    assert "new Event('blur', { bubbles: true })" in content

def test_field_aliases_coverage():
    """Verify core field aliases include standard Russian terms."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    with open(content_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert '"название"' in content
    assert '"описание"' in content
    assert '"цена"' in content
    assert '"состояние"' in content
    assert '"производитель"' in content
    assert '"модель"' in content

def test_condition_chip_button_matching():
    """Verify content.js normalizes condition values and supports button/chip selectors."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    with open(content_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "normalizeConditionValue" in content
    assert "button-chip" in content
    assert "data-marker*=\"condition\"" in content or "data-marker*=\\\"condition\\\"" in content

def test_cascading_multi_pass_combobox_engine():
    """Verify content.js contains multi-pass cascading combobox and suggest selection engine."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    with open(content_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "fillAvitoPublicationFormAsync" in content
    assert "selectDropdownSuggestion" in content
    assert "maxPasses" in content
    assert "role=\"combobox\"" in content or "role=\\\"combobox\\\"" in content
    assert "role=\"listbox\"" in content or "role=\\\"listbox\\\"" in content

def test_category_suggestion_matching_and_step_flow():
    """Verify content.js contains category keywords and suggested category tile selection."""
    content_js_path = os.path.abspath("chrome-extension/technoreboot-avito/content.js")
    with open(content_js_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "matchCategorySuggestion" in content
    assert "CATEGORY_HARDWARE_KEYWORDS" in content
    assert "category-tile" in content
    assert "suggested-category" in content



