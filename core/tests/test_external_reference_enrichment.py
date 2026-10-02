"""
Unit tests for External Reference Enrichment Pipeline (WEB-07C).
Covers validation rules:
- rejection of missing provenance
- rejection of conflicting sources silently merged
- rejection of forbidden instance fields
- acceptance of verified Tier A/B specification data
- product-level preservation invariants (existing specs win, restoration category preserved)
"""

import pytest
import json
from unittest.mock import MagicMock
from scripts.validate_external_reference_enrichment import validate_enrichment_package
from app.services.product_reference_enricher import enrich_product_from_reference
from app import models


def test_validator_accepts_clean_verified_package():
    payload = {
        "batch_id": "BATCH_01_TEST",
        "models": [
            {
                "stable_key": "hp|laserjet-pro-400-m401a",
                "canonical_name": "HP LaserJet Pro 400 M401a",
                "device_type": "printer",
                "decision": "verified_apply",
                "sources": [
                    {
                        "source_id": "hp_m401_ds",
                        "url": "https://support.hp.com/us-en/document/c03333333",
                        "publisher": "HP Inc.",
                        "source_type": "official_datasheet",
                        "retrieved_at": "2026-10-02"
                    }
                ],
                "fields": {
                    "print_technology": {
                        "value": "Лазерная",
                        "source_ids": ["hp_m401_ds"]
                    },
                    "print_speed_a4_mono": {
                        "value": "33 стр/мин",
                        "source_ids": ["hp_m401_ds"]
                    },
                    "max_format": {
                        "value": "A4",
                        "source_ids": ["hp_m401_ds"]
                    }
                },
                "specifications": {
                    "Технология печати": "Лазерная",
                    "Скорость печати (A4, ч/б)": "33 стр/мин",
                    "Максимальный формат": "A4"
                }
            }
        ]
    }
    is_valid, issues, stats = validate_enrichment_package(payload)
    assert is_valid is True
    assert len([i for i in issues if i.severity == "ERROR"]) == 0
    assert stats["verified_apply_count"] == 1
    assert stats["total_fields"] == 3


def test_validator_rejects_missing_provenance():
    payload = {
        "batch_id": "BATCH_TEST_PROVENANCE",
        "models": [
            {
                "stable_key": "canon|lbp-6030b",
                "canonical_name": "Canon i-SENSYS LBP6030B",
                "device_type": "printer",
                "decision": "verified_apply",
                "sources": [
                    {
                        "source_id": "canon_src_1",
                        "url": "https://www.canon-europe.com/printers/i-sensys-lbp6030b/specifications/",
                        "publisher": "Canon Europe",
                        "source_type": "official_datasheet",
                        "retrieved_at": "2026-10-02"
                    }
                ],
                "fields": {
                    "print_technology": {
                        "value": "Лазерная",
                        "source_ids": []  # Missing source_ids!
                    },
                    "print_speed_a4_mono": {
                        "value": "18 стр/мин",
                        "source_ids": ["non_existent_source_id"]  # Undeclared source_id!
                    }
                },
                "specifications": {
                    "Технология печати": "Лазерная"
                }
            }
        ]
    }
    is_valid, issues, stats = validate_enrichment_package(payload)
    assert is_valid is False
    errors = [str(i) for i in issues if i.severity == "ERROR"]
    assert any("has no source provenance" in e for e in errors)
    assert any("references undeclared source_id" in e for e in errors)


def test_validator_rejects_forbidden_instance_fields():
    payload = {
        "batch_id": "BATCH_TEST_FORBIDDEN",
        "models": [
            {
                "stable_key": "hp|laserjet-p2035",
                "canonical_name": "HP LaserJet P2035",
                "device_type": "printer",
                "decision": "verified_apply",
                "sources": [
                    {
                        "source_id": "hp_src",
                        "url": "https://support.hp.com/p2035",
                        "publisher": "HP",
                        "source_type": "official_datasheet",
                        "retrieved_at": "2026-10-02"
                    }
                ],
                "fields": {
                    "sale_price": {  # Forbidden instance field!
                        "value": "5000",
                        "source_ids": ["hp_src"]
                    },
                    "serial_number": {  # Forbidden instance field!
                        "value": "VNC12345",
                        "source_ids": ["hp_src"]
                    },
                    "condition": {  # Forbidden instance field!
                        "value": "used",
                        "source_ids": ["hp_src"]
                    }
                },
                "specifications": {
                    "Технология печати": "Лазерная"
                }
            }
        ]
    }
    is_valid, issues, stats = validate_enrichment_package(payload)
    assert is_valid is False
    errors = [str(i) for i in issues if i.severity == "ERROR"]
    assert any("Forbidden instance-level field in reference model: 'sale_price'" in e for e in errors)
    assert any("Forbidden instance-level field in reference model: 'serial_number'" in e for e in errors)
    assert any("Forbidden instance-level field in reference model: 'condition'" in e for e in errors)


def test_validator_rejects_conflicting_sources_silently_merged():
    payload = {
        "batch_id": "BATCH_TEST_CONFLICT",
        "models": [
            {
                "stable_key": "brother|mfc-8880dn",
                "canonical_name": "Brother MFC-8880DN",
                "device_type": "mfu",
                "decision": "verified_apply",
                "sources": [
                    {
                        "source_id": "brother_us",
                        "url": "https://www.brother-usa.com/mfc-8880dn",
                        "publisher": "Brother USA",
                        "source_type": "official_datasheet",
                        "retrieved_at": "2026-10-02"
                    }
                ],
                "fields": {
                    "print_speed_a4_mono": {
                        "value": "30 стр/мин",
                        "source_ids": ["brother_us"]
                    }
                },
                "conflicts": [
                    {
                        "field": "print_speed_a4_mono",
                        "values": [
                            {"value": "30 ppm", "source": "brother_us"},
                            {"value": "32 ppm", "source": "brother_eu"}
                        ]
                    }
                ],
                "specifications": {
                    "Скорость печати": "30 стр/мин"
                }
            }
        ]
    }
    is_valid, issues, stats = validate_enrichment_package(payload)
    assert is_valid is False
    errors = [str(i) for i in issues if i.severity == "ERROR"]
    assert any("marked as unresolved conflict but included in verified_apply fields" in e for e in errors)


def test_validator_rejects_forbidden_domains():
    payload = {
        "batch_id": "BATCH_TEST_FORBIDDEN_DOMAIN",
        "models": [
            {
                "stable_key": "hp|laserjet-p1505",
                "canonical_name": "HP LaserJet P1505",
                "device_type": "printer",
                "decision": "verified_apply",
                "sources": [
                    {
                        "source_id": "avito_src",
                        "url": "https://www.avito.ru/moskva/orgtehnika/hp_laserjet_p1505_123456",
                        "publisher": "Avito User",
                        "source_type": "official_datasheet",
                        "retrieved_at": "2026-10-02"
                    }
                ],
                "fields": {
                    "print_technology": {
                        "value": "Лазерная",
                        "source_ids": ["avito_src"]
                    }
                },
                "specifications": {}
            }
        ]
    }
    is_valid, issues, stats = validate_enrichment_package(payload)
    assert is_valid is False
    errors = [str(i) for i in issues if i.severity == "ERROR"]
    assert any("forbidden domain/fragment: 'avito.ru'" in e for e in errors)


def test_existing_product_specs_win_over_reference():
    mock_db = MagicMock()
    product = models.Product(
        id=101,
        title="HP LaserJet Pro 400 M401a",
        brand="HP",
        model="LaserJet Pro 400 M401a",
        category_id=1,
        sale_price=9500.0,
        purchase_price=4000.0,
        quantity=1,
        status="in_stock",
        serial_number="ABC12345",
        avito_params_json=json.dumps({
            "Скорость печати (A4, ч/б)": "35 стр/мин (индивидуальный замер)",
            "Технология печати": "Лазерная"
        }, ensure_ascii=False)
    )

    ref = models.ProductReferenceModel(
        id=28,
        stable_key="hp|laserjet-pro-400-m401a",
        canonical_name="HP LaserJet Pro 400 M401a",
        brand="HP",
        model="LaserJet Pro 400 M401a",
        device_type="printer",
        specifications_json=json.dumps({
            "Скорость печати (A4, ч/б)": "33 стр/мин",
            "Максимальный формат": "A4",
            "Разрешение печати": "1200 x 1200 dpi"
        }, ensure_ascii=False)
    )

    res = enrich_product_from_reference(mock_db, product, ref, method="canonical_match", confidence=1.0, apply=True)

    # Check that product's existing value was NOT overwritten
    product_specs = json.loads(product.avito_params_json)
    assert product_specs["Скорость печати (A4, ч/б)"] == "35 стр/мин (индивидуальный замер)"
    # Missing specs were added
    assert product_specs["Максимальный формат"] == "A4"
    assert product_specs["Разрешение печати"] == "1200 x 1200 dpi"
    # Prices and serial were untouched
    assert product.sale_price == 9500.0
    assert product.purchase_price == 4000.0
    assert product.serial_number == "ABC12345"


def test_restoration_category_preserved():
    mock_db = MagicMock()
    product = models.Product(
        id=202,
        title="HP LaserJet P2035 на запчасти / восстановление",
        category_id=52,  # Restoration category
        sale_price=1500.0,
        status="in_stock",
        avito_params_json=None
    )

    ref = models.ProductReferenceModel(
        id=30,
        stable_key="hp|laserjet-p2035",
        canonical_name="HP LaserJet P2035",
        device_type="printer",
        default_category_id=1,  # Normal printer category
        specifications_json=json.dumps({"Технология печати": "Лазерная"}, ensure_ascii=False)
    )

    enrich_product_from_reference(mock_db, product, ref, method="canonical_match", confidence=1.0, apply=True)

    # Category must REMAIN 52 (Техника под восстановление)
    assert product.category_id == 52
