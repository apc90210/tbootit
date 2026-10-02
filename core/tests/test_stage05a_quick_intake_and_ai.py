"""
Unit tests for Stage 05A:
- Reference catalog search (exact, alias, unknown)
- AI provider abstraction (disabled fallback, error handling, strict schema)
- Canonical description generator (Printer & MFP specs)
- Mobile Quick Intake endpoint (reference prefill, notes isolation, photo storage, stock movement)
- Historical data protection (no mutation of existing cards/sales)
"""

import json
import base64
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app import models
from app.services.ai.spec_schemas import build_canonical_description
from app.services.ai.base import AIIdentificationResult
from app.services.ai.disabled_provider import DisabledAIProvider
from app.services.ai.openai_compatible import OpenAICompatibleProvider

OWNER_HEADERS = {"x-auth-is-owner": "1", "x-api-token": "dev-token"}


@pytest.fixture
def seed_test_reference_model(db_session):
    """Seed a known printer reference model with aliases."""
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


def test_reference_search_exact_and_alias(client, seed_test_reference_model):
    """Test searching by exact canonical name and by alias."""
    # 1. Exact match
    resp = client.get("/api/product-reference/search", params={"q": "HP LaserJet P1102w"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_candidates"] >= 1
    top = data["candidates"][0]
    assert top["reference_model_id"] == seed_test_reference_model.id
    assert top["canonical_name"] == "HP LaserJet P1102w"
    assert top["confidence"] >= 0.90
    assert top["specifications"]["technology"] == "лазерная"

    # 2. Alias match
    resp_alias = client.get("/api/product-reference/search", params={"q": "P1102w"})
    assert resp_alias.status_code == 200
    data_alias = resp_alias.json()
    assert data_alias["total_candidates"] >= 1
    assert data_alias["candidates"][0]["reference_model_id"] == seed_test_reference_model.id

    # 3. Plural route alias (/api/product-references/search)
    resp_plural = client.get("/api/product-references/search", params={"q": "HP P1102w"})
    assert resp_plural.status_code == 200
    assert resp_plural.json()["total_candidates"] >= 1


def test_reference_search_unknown_model(client):
    """Test searching for an unknown model returns empty candidates without error."""
    resp = client.get("/api/product-reference/search", params={"q": "CompletelyUnknownWidgetX999"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_candidates"] == 0
    assert data["candidates"] == []


def test_ai_assist_disabled_fallback(client):
    """Verify AI assist endpoint returns graceful disabled status when AI is disabled."""
    with patch("app.services.ai.factory.settings.ai_enabled", False):
        resp = client.post("/api/product-reference/ai-assist", json={"query": "HP LaserJet M1132 MFP"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "disabled"
        assert data["confidence"] == 0.0
        assert "отключен" in data["message"].lower() or "disabled" in data["message"].lower()


@pytest.mark.asyncio
async def test_ai_provider_timeout_fallback():
    """Verify AI provider handles timeout gracefully without crash."""
    provider = OpenAICompatibleProvider(
        api_base_url="http://non-existent-domain-12345.xyz",
        api_key="test-key",
        model_name="test-model",
        timeout_seconds=1
    )
    result = await provider.identify_model(query="Kyocera ECOSYS M2040dn")
    assert result.status == "error"
    assert result.confidence == 0.0
    assert result.source_provenance == "error"


def test_spec_schemas_canonical_description_generator():
    """Verify pure technical description is generated from structured facts without defect leaks."""
    specs = {
        "technology": "лазерная",
        "color_mode": "монохромная",
        "max_format": "A4",
        "duplex": "да",
        "print_speed": "до 21 стр/мин",
        "interfaces": "USB 2.0",
        "cartridge_family": "Q5949A"
    }
    desc = build_canonical_description(
        device_type="printer",
        brand="HP",
        model="LaserJet 1320",
        specs=specs
    )
    assert "Принтер HP LaserJet 1320." in desc
    assert "Технология печати: лазерная." in desc
    assert "Цветность: монохромная." in desc
    assert "Автоматическая двусторонняя печать (дуплекс)." in desc
    assert "Картридж: Q5949A" in desc
    # Ensure defect text is NEVER generated by canonical generator
    assert "потертости" not in desc
    assert "дефект" not in desc


def test_quick_intake_product_creation(client, db_session, seed_test_reference_model):
    """
    Test creating a product card via /api/products/quick-intake:
    - Pre-fills from reference model
    - Item-specific notes are strictly isolated on product.notes
    - Reusable reference model is NOT mutated
    - Photos base64 are saved and linked to ProductPhoto
    - Initial stock movement is created
    """
    sample_img_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    sample_b64 = base64.b64encode(sample_img_bytes).decode("ascii")

    intake_payload = {
        "reference_model_id": seed_test_reference_model.id,
        "condition": "Б/у - хорошее",
        "notes": "Потертости на крышке лотка, картридж заправлен, печатает чисто",
        "sale_price": 5500.0,
        "quantity": 1,
        "photos": [
            {"filename": "product_front.png", "content_base64": sample_b64}
        ]
    }

    resp = client.post("/api/products/quick-intake", json=intake_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    prod_id = data["id"]
    assert data["sku"].startswith("PRD-") or data["sku"].startswith("TR-")
    assert data["title"] == "HP LaserJet P1102w"
    assert data["sale_price"] == 5500.0
    assert data["quantity"] == 1
    assert data["condition"] == "Б/у - хорошее"
    assert data["notes"] == "Потертости на крышке лотка, картридж заправлен, печатает чисто"
    assert data["reference_model_id"] == seed_test_reference_model.id
    assert data["photos_count"] == 1
    assert data["status"] == "in_stock"

    # Verify DB state
    db_prod = db_session.query(models.Product).filter_by(id=prod_id).first()
    assert db_prod is not None
    assert db_prod.notes == intake_payload["notes"]
    assert db_prod.quantity == 1

    # Verify initial stock movement
    mov = db_session.query(models.StockMovement).filter_by(product_id=prod_id).first()
    assert mov is not None
    assert mov.movement_type == "initial"
    assert mov.quantity_delta == 1

    # Verify photo record
    photo = db_session.query(models.ProductPhoto).filter_by(product_id=prod_id).first()
    assert photo is not None
    assert photo.filename.endswith(".png")

    # CRITICAL: Verify reusable reference model was NOT contaminated with item-specific notes!
    ref_fresh = db_session.query(models.ProductReferenceModel).filter_by(id=seed_test_reference_model.id).first()
    assert "Потертости" not in ref_fresh.site_description
    assert "картридж заправлен" not in ref_fresh.site_description


def test_quick_intake_preserves_historical_products(client, db_session, seed_test_reference_model):
    """
    Test when the same model arrives again, an old sold/archived product is NOT reopened.
    A new distinct product card is created with its own identity.
    """
    # Create an old sold product for the same reference model
    old_prod = models.Product(
        sku="TR-OLD-SOLD-001",
        title="HP LaserJet P1102w (old sold)",
        reference_model_id=seed_test_reference_model.id,
        sale_price=4500.0,
        quantity=0,
        status="sold"
    )
    db_session.add(old_prod)
    db_session.commit()
    old_id = old_prod.id

    # Intake a new product of the same reference model
    intake_payload = {
        "reference_model_id": seed_test_reference_model.id,
        "condition": "Б/у - отличное",
        "notes": "Новое поступление, идеальное состояние",
        "sale_price": 5900.0,
        "quantity": 1
    }
    resp = client.post("/api/products/quick-intake", json=intake_payload)
    assert resp.status_code == 200
    new_data = resp.json()
    new_id = new_data["id"]

    assert new_id != old_id

    # Verify old product remains untouched and sold with quantity=0
    old_check = db_session.query(models.Product).filter_by(id=old_id).first()
    assert old_check.status == "sold"
    assert old_check.quantity == 0
    assert old_check.sale_price == 4500.0

    # Verify new product is active and in_stock with quantity=1
    new_check = db_session.query(models.Product).filter_by(id=new_id).first()
    assert new_check.status == "in_stock"
    assert new_check.quantity == 1
    assert new_check.sale_price == 5900.0
