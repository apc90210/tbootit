"""
Tests for Deterministic Product Reference Matcher Service.
Fulfills PROMPT_WEB_07A Section 23:
- Exact aliases (confidence = 1.00)
- Model specificity (1320 != 1320n, T480 != T480s, P2040dn != P2040dw)
- Ambiguity safety (competing candidates, bundle titles, part/consumables)
"""

import pytest
from sqlalchemy.orm import Session

from app import models
from app.services.product_reference_matcher import match_product, find_reference_candidates
from app.services.product_reference_json_service import import_reference_models_from_dict


@pytest.fixture(autouse=True)
def setup_reference_catalog(db: Session):
    """Seed test database with known reference models for testing."""
    test_models = {
        "version": 1,
        "models": [
            {
                "canonical_name": "HP LaserJet 1320",
                "brand": "HP",
                "model": "LaserJet 1320",
                "device_type": "printer",
                "aliases": ["HP LaserJet 1320", "HP 1320", "HP LJ 1320", "LaserJet 1320"],
                "specifications": {"Тип устройства": "Принтер", "Двусторонняя печать": "Да"}
            },
            {
                "canonical_name": "HP LaserJet 1320n",
                "brand": "HP",
                "model": "LaserJet 1320n",
                "device_type": "printer",
                "aliases": ["HP LaserJet 1320n", "HP 1320n", "HP LJ 1320n"],
                "specifications": {"Тип устройства": "Принтер", "Сетевой интерфейс": "Да"}
            },
            {
                "canonical_name": "Kyocera ECOSYS P2040dn",
                "brand": "Kyocera",
                "model": "ECOSYS P2040dn",
                "device_type": "printer",
                "aliases": ["Kyocera ECOSYS P2040dn", "Kyocera P2040dn", "ECOSYS P2040dn"],
                "specifications": {"Тип устройства": "Принтер", "Сетевой интерфейс": "Да", "Wi-Fi": "Нет"}
            },
            {
                "canonical_name": "Kyocera ECOSYS P2040dw",
                "brand": "Kyocera",
                "model": "ECOSYS P2040dw",
                "device_type": "printer",
                "aliases": ["Kyocera ECOSYS P2040dw", "Kyocera P2040dw", "ECOSYS P2040dw"],
                "specifications": {"Тип устройства": "Принтер", "Wi-Fi": "Да"}
            },
            {
                "canonical_name": "Lenovo ThinkPad T480",
                "brand": "Lenovo",
                "model": "ThinkPad T480",
                "device_type": "laptop",
                "aliases": ["Lenovo ThinkPad T480", "ThinkPad T480", "Lenovo T480"],
                "specifications": {"Тип устройства": "Ноутбук"}
            },
            {
                "canonical_name": "Lenovo ThinkPad T480s",
                "brand": "Lenovo",
                "model": "ThinkPad T480s",
                "device_type": "laptop",
                "aliases": ["Lenovo ThinkPad T480s", "ThinkPad T480s", "Lenovo T480s"],
                "specifications": {"Тип устройства": "Ультрабук"}
            },
            {
                "canonical_name": "Xerox VersaLink B405",
                "brand": "Xerox",
                "model": "VersaLink B405",
                "device_type": "mfu",
                "aliases": ["Xerox VersaLink B405", "Xerox B405", "VersaLink B405"],
                "specifications": {"Тип устройства": "МФУ"}
            }
        ]
    }
    import_reference_models_from_dict(db, test_models, dry_run=False, source="test_fixture")


def test_tier1_exact_unique_alias_match(db: Session):
    title = "Лазерный принтер HP LaserJet 1320 в отличном состоянии"
    res = match_product(db, title=title)
    assert res.matched is True
    assert res.canonical_name == "HP LaserJet 1320"
    assert res.method == "tier1_exact_alias"
    assert res.confidence == 1.00
    assert res.status == "matched"
    assert res.would_fill["brand"] == "HP"
    assert res.would_fill["model"] == "LaserJet 1320"


def test_model_specificity_1320_vs_1320n(db: Session):
    # 1320n must strictly match 1320n, NOT 1320
    res_n = match_product(db, title="Принтер HP LaserJet 1320n сетевой")
    assert res_n.matched is True
    assert res_n.canonical_name == "HP LaserJet 1320n"

    # 1320 must match 1320, NOT 1320n
    res_base = match_product(db, title="Принтер HP LaserJet 1320 с дуплексом")
    assert res_base.matched is True
    assert res_base.canonical_name == "HP LaserJet 1320"


def test_model_specificity_p2040dn_vs_p2040dw(db: Session):
    # P2040dn must match P2040dn
    res_dn = match_product(db, title="Лазерный принтер Kyocera ecosys p2040dn")
    assert res_dn.matched is True
    assert res_dn.canonical_name == "Kyocera ECOSYS P2040dn"

    # P2040dw must match P2040dw
    res_dw = match_product(db, title="Лазерный принтер Kyocera ecosys p2040dw с вай-фай")
    assert res_dw.matched is True
    assert res_dw.canonical_name == "Kyocera ECOSYS P2040dw"


def test_model_specificity_t480_vs_t480s(db: Session):
    # T480s must match T480s
    res_s = match_product(db, title="Ноутбук Lenovo ThinkPad T480s i5/8gb")
    assert res_s.matched is True
    assert res_s.canonical_name == "Lenovo ThinkPad T480s"

    # T480 must match T480
    res_base = match_product(db, title="Ноутбук Lenovo ThinkPad T480 i7/16gb")
    assert res_base.matched is True
    assert res_base.canonical_name == "Lenovo ThinkPad T480"


def test_ambiguity_no_auto_match_when_ambiguous_suffix(db: Session):
    # Title says "Kyocera P2040" without dn or dw suffix:
    # Both P2040dn and P2040dw exist -> ambiguous candidates -> NO AUTO MATCH!
    res = match_product(db, title="Лазерный принтер Kyocera P2040")
    assert res.matched is False
    assert res.status == "needs_review"
    assert "ambiguous" in (res.reason or "")
    assert len(res.candidates) >= 2


def test_ambiguity_bundle_titles_detected(db: Session):
    # Multiple distinct models in single title -> bundle -> NO AUTO MATCH
    bundle_title = "Принтеры HP LaserJet 1320 / 1018 / P2055 на складе"
    res = match_product(db, title=bundle_title)
    assert res.matched is False
    assert res.status == "needs_review"
    assert "bundle" in (res.reason or "")


def test_part_or_consumable_rejected(db: Session):
    # Consumables / spare parts must not auto-match the full device
    res_toner = match_product(db, title="Тонер-картридж Xerox VersaLink B400/B405 106R03585")
    assert res_toner.matched is False
    assert res_toner.status == "needs_review"
    assert res_toner.reason == "part_or_consumable_not_whole_device"

    res_fuser = match_product(db, title="Фьюзер печка для Xerox VersaLink B400/B405")
    assert res_fuser.matched is False
    assert res_fuser.status == "needs_review"


def test_restoration_product_matches_reference(db: Session):
    # Product with restoration marker CAN match the reference model for its specs
    res = match_product(db, title="Лазерное мфу 3 в 1 xerox b405 под восстановление")
    assert res.matched is True
    assert res.canonical_name == "Xerox VersaLink B405"
