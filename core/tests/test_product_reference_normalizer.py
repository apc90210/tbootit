"""
Tests for Product Reference Normalizer & Token Utilities.
Fulfills PROMPT_WEB_07A Section 23 (Normalization & Model Specificity).
"""

import pytest
from app.services.product_reference_matcher import (
    normalize_for_matching,
    extract_tokens,
    generate_stable_key,
    has_token_boundary_phrase,
    is_part_or_consumable,
)


def test_normalize_case_insensitive():
    assert normalize_for_matching("HP LaserJet 1320") == "hp laserjet 1320"
    assert normalize_for_matching("XEROX VERSALINK B405") == "xerox versalink b405"


def test_normalize_cyrillic_yo_to_e():
    assert normalize_for_matching("Жёсткий диск") == "жесткий диск"
    assert normalize_for_matching("Чёрно-белая печать") == "черно-белая печать"


def test_normalize_punctuation_and_spaces():
    raw = "МФУ (3 в 1): HP LaserJet 3052, со сканером / копиром!"
    norm = normalize_for_matching(raw)
    assert "hp laserjet 3052" in norm
    assert "(" not in norm
    assert ")" not in norm
    assert "!" not in norm
    assert "/" not in norm
    assert "  " not in norm


def test_model_numbers_preserved():
    # Crucial model tokens must never be stripped or corrupted
    test_models = [
        "1320", "1320n", "P2040dn", "P2040dw", "T480", "T480s",
        "M428fdw", "M428fdn", "B405", "B405dn", "LBP6030B", "i3-6100"
    ]
    for m in test_models:
        norm = normalize_for_matching(m)
        assert norm == m.lower()
        tokens = extract_tokens(m)
        assert any(t == m.lower() or t in m.lower() for t in tokens)


def test_generate_stable_key():
    assert generate_stable_key("HP", "LaserJet 1320") == "hp|laserjet-1320"
    assert generate_stable_key("Xerox", "VersaLink B405") == "xerox|versalink-b405"
    assert generate_stable_key("Kyocera", "ECOSYS P2040dn") == "kyocera|ecosys-p2040dn"


def test_has_token_boundary_phrase():
    text = "лазерный принтер hp laserjet 1320 в отличном состоянии"
    assert has_token_boundary_phrase("hp laserjet 1320", text) is True
    assert has_token_boundary_phrase("laserjet 1320", text) is True
    assert has_token_boundary_phrase("1320", text) is True
    # Word boundary should prevent matching 1320 in 13200 or 1320n
    text_n = "лазерный принтер hp laserjet 1320n в отличном состоянии"
    assert has_token_boundary_phrase("1320", text_n) is False
    assert has_token_boundary_phrase("1320n", text_n) is True


def test_part_or_consumable_detection():
    # Consumables / Parts must be flagged as True
    assert is_part_or_consumable("Тонер-картридж Xerox VersaLink B400/B405") is True
    assert is_part_or_consumable("Фьюзер печка для Xerox VersaLink B400/B405") is True
    assert is_part_or_consumable("Крышка передняя Xerox Versalink B405") is True
    assert is_part_or_consumable("Шарниры Xerox B405") is True
    assert is_part_or_consumable("Плата питания Xerox B405") is True
    assert is_part_or_consumable("Xerox Versalink b405 разбор (зип, запчасти)") is True

    # Full devices must NOT be flagged as parts
    assert is_part_or_consumable("Лазерное мфу Xerox VersaLink B405") is False
    assert is_part_or_consumable("Принтер HP LaserJet 1320") is False
    assert is_part_or_consumable("Лазерное мфу 3 в 1 xerox b405 под восстановление") is False
    assert is_part_or_consumable("Лазерный принтер Pantum p3300dn на запчасти") is False
