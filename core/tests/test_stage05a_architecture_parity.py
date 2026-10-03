"""
Stage 05A Architecture Parity & Regression Test Suite.
Verifies TR_Stage05A_Architecture_Parity_Closeout_R1:
1. Canonical matcher reuse between Core matcher and /api/product-reference/search.
2. Canonical Core Safe Enricher reuse in /api/products/quick-intake:
   Pipeline: Android -> Core Product -> canonical matcher -> canonical Core Safe Enricher -> canonical Product
3. Strict parity between standard Core product ingestion and Quick Intake:
   - reference_model_id
   - reference_match_method & reference_match_confidence
   - model-level enrichment fields (brand, model, category_id, site_title, site_description, avito_params_json)
   - safe-merge behavior preserving manual fields
"""

import json
import pytest
from app import models
from app.services.product_reference_matcher import find_reference_candidates, match_product


@pytest.fixture
def seed_test_reference_model(db_session):
    """Seed a known printer reference model with aliases for parity tests."""
    cat = db_session.query(models.Category).filter_by(slug="printery").first()
    if not cat:
        cat = models.Category(name="Принтеры", slug="printery")
        db_session.add(cat)
        db_session.commit()

    existing = db_session.query(models.ProductReferenceModel).filter_by(stable_key="hp_laserjet_p1102w").first()
    if existing:
        return existing

    ref = models.ProductReferenceModel(
        stable_key="hp_laserjet_p1102w",
        canonical_name="HP LaserJet P1102w",
        brand="HP",
        model="LaserJet P1102w",
        device_type="printer",
        default_category_id=cat.id,
        specifications_json=json.dumps({
            "technology": "лазерная",
            "color_mode": "монохромная",
            "max_format": "A4",
            "duplex": "нет",
            "print_speed": "до 18 стр/мин",
            "interfaces": "USB 2.0, Wi-Fi",
            "cartridge_family": "HP 85A (CE285A)"
        }, ensure_ascii=False),
        site_title="Лазерный принтер HP LaserJet P1102w б/у",
        site_description="Лазерный монохромный принтер с Wi-Fi. Картридж CE285A.",
        verification_state="verified",
        confidence=1.0,
        active=True
    )
    db_session.add(ref)
    db_session.flush()

    aliases = [
        models.ProductReferenceAlias(reference_model_id=ref.id, alias="HP LaserJet P1102w", normalized_alias="hp laserjet p1102w", priority=100),
        models.ProductReferenceAlias(reference_model_id=ref.id, alias="HP P1102w", normalized_alias="hp p1102w", priority=90),
        models.ProductReferenceAlias(reference_model_id=ref.id, alias="LaserJet P1102w", normalized_alias="laserjet p1102w", priority=80),
    ]
    db_session.add_all(aliases)
    db_session.commit()
    return ref


def test_candidate_search_canonical_parity(client, db_session, seed_test_reference_model):
    """
    Proves /api/product-reference/search reuses canonical Core matcher without duplicate logic.
    Direct call to find_reference_candidates and API endpoint return identical candidates.
    """
    query = "P1102w"

    # 1. Direct canonical service call
    canonical_candidates = find_reference_candidates(db=db_session, title=query, active_only=True)
    assert len(canonical_candidates) >= 1
    top_canonical = canonical_candidates[0]

    # 2. Endpoint call
    resp = client.get("/api/product-reference/search", params={"q": query})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_candidates"] >= 1
    top_api = data["candidates"][0]

    # Parity assertions
    assert top_api["reference_model_id"] == top_canonical.reference_model_id
    assert top_api["canonical_name"] == top_canonical.canonical_name
    assert top_api["brand"] == top_canonical.brand
    assert top_api["model"] == top_canonical.model
    assert top_api["confidence"] == pytest.approx(top_canonical.confidence, abs=0.001)
    assert top_api["tier"] == top_canonical.tier


def test_standard_vs_quick_intake_parity_matching(client, db_session, seed_test_reference_model):
    """
    Proves identical input Product via standard Core ingestion and /api/products/quick-intake
    receives identical:
    - reference_model_id
    - reference match method and confidence
    - model-level enrichment fields (brand, model, category_id, site_title, site_description)
    - specifications (avito_params_json)
    """
    title = "HP LaserJet P1102w"
    price = 5500.0
    qty = 1

    # Ingestion 1: Standard Core ingestion (POST /api/products/)
    core_payload = {
        "title": title,
        "sale_price": price,
        "quantity": qty,
        "condition": "Б/у",
        "description": "Базовое описание"
    }
    resp_core = client.post("/api/products/", json=core_payload)
    assert resp_core.status_code == 200, resp_core.text
    core_data = resp_core.json()
    core_prod_id = core_data["id"]

    # Ingestion 2: Quick Intake (POST /api/products/quick-intake)
    quick_payload = {
        "title": title,
        "sale_price": price,
        "quantity": qty,
        "condition": "Б/у",
        "notes": "Особое состояние: небольшая царапина",  # Instance-specific field
    }
    resp_quick = client.post("/api/products/quick-intake", json=quick_payload)
    assert resp_quick.status_code == 200, resp_quick.text
    quick_data = resp_quick.json()
    quick_prod_id = quick_data["id"]

    # Fetch DB rows for deep parity comparison
    p_core = db_session.query(models.Product).filter_by(id=core_prod_id).first()
    p_quick = db_session.query(models.Product).filter_by(id=quick_prod_id).first()

    assert p_core is not None
    assert p_quick is not None

    # 1. Reference model parity
    assert p_core.reference_model_id == seed_test_reference_model.id
    assert p_quick.reference_model_id == seed_test_reference_model.id
    assert p_core.reference_model_id == p_quick.reference_model_id

    # 2. Canonical Match Result parity
    assert p_core.reference_match_method == p_quick.reference_match_method
    assert p_core.reference_match_confidence == pytest.approx(p_quick.reference_match_confidence, abs=0.001)

    # 3. Model-level enrichment fields parity
    assert p_core.brand == p_quick.brand
    assert p_quick.brand == seed_test_reference_model.brand
    assert p_core.model == p_quick.model
    assert p_quick.model == seed_test_reference_model.model
    assert p_core.category_id == p_quick.category_id
    assert p_core.site_title == p_quick.site_title
    assert p_core.site_description == p_quick.site_description

    # 4. Specifications enrichment parity
    core_specs = json.loads(p_core.avito_params_json or "{}")
    quick_specs = json.loads(p_quick.avito_params_json or "{}")
    assert core_specs == quick_specs
    assert core_specs.get("technology") == "лазерная"

    # 5. Provenance timestamps set
    assert p_core.reference_enriched_at is not None
    assert p_quick.reference_enriched_at is not None

    # 6. Instance-specific isolation
    assert p_quick.notes == "Особое состояние: небольшая царапина"
    assert p_core.notes is None
    assert "небольшая царапина" not in seed_test_reference_model.site_description


def test_standard_vs_quick_intake_parity_safe_merge_manual_values(client, db_session, seed_test_reference_model):
    """
    Proves safe-merge non-overwrite parity:
    When manual values (e.g. custom brand) are supplied, both Core ingestion and Quick Intake:
    - Preserve manual brand (not overwritten by reference brand)
    - Safely enrich missing fields (model, specifications, category, etc.)
    - Maintain identical parity in reference match and enrichment
    """
    title = "HP LaserJet P1102w"
    manual_brand = "CustomBrandOverride"
    price = 6000.0

    # Ingestion 1: Standard Core ingestion with manual brand
    core_payload = {
        "title": title,
        "brand": manual_brand,
        "sale_price": price,
        "quantity": 1
    }
    resp_core = client.post("/api/products/", json=core_payload)
    assert resp_core.status_code == 200
    p_core = db_session.query(models.Product).filter_by(id=resp_core.json()["id"]).first()

    # Ingestion 2: Quick Intake with manual brand
    quick_payload = {
        "title": title,
        "brand": manual_brand,
        "sale_price": price,
        "quantity": 1,
        "condition": "Отличное"
    }
    resp_quick = client.post("/api/products/quick-intake", json=quick_payload)
    assert resp_quick.status_code == 200
    p_quick = db_session.query(models.Product).filter_by(id=resp_quick.json()["id"]).first()

    # Safe merge parity assertions: manual brand preserved on both!
    assert p_core.brand == manual_brand
    assert p_quick.brand == manual_brand

    # Model was missing, so both safely enriched model from reference
    assert p_core.model == seed_test_reference_model.model
    assert p_quick.model == seed_test_reference_model.model

    # Both matched and linked to reference model
    assert p_core.reference_model_id == p_quick.reference_model_id == seed_test_reference_model.id
    assert p_core.reference_match_method == p_quick.reference_match_method
    assert p_core.reference_match_confidence == pytest.approx(p_quick.reference_match_confidence, abs=0.001)

    # Both enriched specifications safely
    assert json.loads(p_core.avito_params_json) == json.loads(p_quick.avito_params_json)


def test_quick_intake_explicit_reference_id_parity(client, db_session, seed_test_reference_model):
    """
    Proves Quick Intake with explicit reference_model_id achieves parity with standard Core ingestion.
    """
    # 1. Standard Core ingestion
    resp_core = client.post("/api/products/", json={
        "title": "HP LaserJet P1102w",
        "sale_price": 4900.0,
        "quantity": 1
    })
    assert resp_core.status_code == 200
    p_core = db_session.query(models.Product).filter_by(id=resp_core.json()["id"]).first()

    # 2. Quick Intake with explicit reference_model_id
    resp_quick = client.post("/api/products/quick-intake", json={
        "reference_model_id": seed_test_reference_model.id,
        "sale_price": 4900.0,
        "quantity": 1,
        "condition": "Б/у"
    })
    assert resp_quick.status_code == 200
    p_quick = db_session.query(models.Product).filter_by(id=resp_quick.json()["id"]).first()

    # Verify parity
    assert p_core.reference_model_id == p_quick.reference_model_id
    assert p_core.brand == p_quick.brand
    assert p_core.model == p_quick.model
    assert p_core.category_id == p_quick.category_id
    assert p_core.site_title == p_quick.site_title
    assert p_core.site_description == p_quick.site_description
    assert json.loads(p_core.avito_params_json) == json.loads(p_quick.avito_params_json)
