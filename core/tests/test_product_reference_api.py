import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Product, Category, ProductReferenceModel, ProductReferenceAlias

client = TestClient(app)

OWNER_HEADERS = {"x-auth-is-owner": "1", "x-api-token": "dev-token"}
NON_OWNER_HEADERS = {"x-auth-is-owner": "0", "x-api-token": "invalid-token"}

def test_product_reference_auth_guard():
    """Ensure non-owner receives 403 Forbidden on reference catalog management endpoints."""
    # List models
    resp = client.get("/api/product-reference/models", headers=NON_OWNER_HEADERS)
    assert resp.status_code == 403

    # Match preview
    resp = client.post("/api/product-reference/match-preview", json={"title": "HP LaserJet 1320"}, headers=NON_OWNER_HEADERS)
    assert resp.status_code == 403

    # Export
    resp = client.get("/api/product-reference/export", headers=NON_OWNER_HEADERS)
    assert resp.status_code == 403


def test_reference_model_crud_and_aliases(db_session):
    """Test full CRUD lifecycle for reference models and aliases."""
    # Ensure category exists
    cat = db_session.query(Category).filter_by(id=10).first()
    if not cat:
        cat = Category(id=10, name="Принтеры")
        db_session.add(cat)
        db_session.commit()

    # 1. Create model
    create_payload = {
        "brand": "Pantum",
        "model": "P2500W",
        "canonical_name": "Pantum P2500W",
        "default_category_id": 10,
        "device_type": "Принтер",
        "specifications": {
            "Тип печати": "Лазерный",
            "Цветность": "Черно-белый",
            "Wi-Fi": "Да"
        },
        "site_title": "Лазерный принтер Pantum P2500W б/у",
        "aliases": ["Pantum P2500W", "P2500W", "Пантум 2500"]
    }

    create_resp = client.post("/api/product-reference/models", json=create_payload, headers=OWNER_HEADERS)
    assert create_resp.status_code == 200, create_resp.text
    created = create_resp.json()
    model_id = created["id"]
    assert created["brand"] == "Pantum"
    assert created["model"] == "P2500W"
    assert "pantum|p2500w" in created["stable_key"]
    assert len(created["aliases"]) >= 3

    # 2. Get model by ID
    get_resp = client.get(f"/api/product-reference/models/{model_id}", headers=OWNER_HEADERS)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == model_id

    # 3. List models with search
    list_resp = client.get("/api/product-reference/models?q=P2500", headers=OWNER_HEADERS)
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(m["id"] == model_id for m in items)

    # 4. Add additional alias
    alias_payload = {"alias": "Pantum P 2500 W Wireless", "priority": 90}
    alias_resp = client.post(f"/api/product-reference/models/{model_id}/aliases", json=alias_payload, headers=OWNER_HEADERS)
    assert alias_resp.status_code == 200
    alias_data = alias_resp.json()
    alias_id = alias_data["id"]
    assert alias_data["normalized_alias"] == "pantum p 2500 w wireless"

    # 5. Update model
    update_payload = {
        "site_title": "Скоростной принтер Pantum P2500W с Wi-Fi"
    }
    update_resp = client.put(f"/api/product-reference/models/{model_id}", json=update_payload, headers=OWNER_HEADERS)
    assert update_resp.status_code == 200
    assert update_resp.json()["site_title"] == "Скоростной принтер Pantum P2500W с Wi-Fi"

    # 6. Delete alias
    del_alias_resp = client.delete(f"/api/product-reference/models/{model_id}/aliases/{alias_id}", headers=OWNER_HEADERS)
    assert del_alias_resp.status_code == 200

    # Verify alias removed
    get_resp_after = client.get(f"/api/product-reference/models/{model_id}", headers=OWNER_HEADERS)
    assert all(a["id"] != alias_id for a in get_resp_after.json()["aliases"])

    # 7. Delete model (hard delete for clean test)
    del_model_resp = client.delete(f"/api/product-reference/models/{model_id}?hard=true", headers=OWNER_HEADERS)
    assert del_model_resp.status_code == 200

    # Verify model is gone
    get_gone_resp = client.get(f"/api/product-reference/models/{model_id}", headers=OWNER_HEADERS)
    assert get_gone_resp.status_code == 404


def test_match_preview_api(db_session):
    """Test /match-preview endpoint for high confidence and parts rejection."""
    # Ensure test model exists
    model = db_session.query(ProductReferenceModel).filter_by(stable_key="epson|ecotank-l3150").first()
    if not model:
        model = ProductReferenceModel(
            stable_key="epson|ecotank-l3150",
            canonical_name="Epson EcoTank L3150",
            brand="Epson",
            model="EcoTank L3150",
            device_type="printer"
        )
        db_session.add(model)
        db_session.flush()

        alias = ProductReferenceAlias(
            reference_model_id=model.id,
            alias="Epson L3150",
            normalized_alias="epson l3150",
            priority=100
        )
        db_session.add(alias)
        db_session.commit()

    # 1. High confidence match
    req = {"title": "Струйное МФУ Epson L3150 цветное"}
    resp = client.post("/api/product-reference/match-preview", json=req, headers=OWNER_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["matched"] is True
    assert data["status"] == "matched"
    assert data["reference_model_id"] == model.id
    assert data["confidence"] >= 0.95

    # 2. Consumable/part containing model name -> rejected / needs_review
    part_req = {"title": "Чернила для принтера Epson L3150 103"}
    part_resp = client.post("/api/product-reference/match-preview", json=part_req, headers=OWNER_HEADERS)
    assert part_resp.status_code == 200
    part_data = part_resp.json()
    assert part_data["status"] == "needs_review"
    assert part_data["matched"] is False


def test_enrich_preview_api(db_session):
    """Test /enrich-preview/{product_id} non-mutating preview."""
    # Create reference model
    model = db_session.query(ProductReferenceModel).filter_by(stable_key="dell|latitude-5490").first()
    if not model:
        model = ProductReferenceModel(
            stable_key="dell|latitude-5490",
            canonical_name="Dell Latitude 5490",
            brand="Dell",
            model="Latitude 5490",
            device_type="laptop",
            specifications_json=json.dumps({"Процессор": "Intel Core i5-8350U", "Экран": "14 FHD"}, ensure_ascii=False)
        )
        db_session.add(model)
        db_session.flush()

        alias = ProductReferenceAlias(
            reference_model_id=model.id,
            alias="Dell Latitude 5490",
            normalized_alias="dell latitude 5490",
            priority=100
        )
        db_session.add(alias)
        db_session.commit()

    # Create un-enriched product
    prod = Product(
        title="Ноутбук Dell Latitude 5490 i5",
        sku="TEST-ENRICH-PREVIEW-DELL",
        purchase_price=20000,
        sale_price=28000,
        avito_params_json=json.dumps({"Оперативная память": "16 ГБ", "SSD": "512 ГБ"}, ensure_ascii=False)
    )
    db_session.add(prod)
    db_session.commit()

    resp = client.post(f"/api/product-reference/enrich-preview/{prod.id}", headers=OWNER_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["matched"] is True
    assert "specifications" in data["enrichment_preview"]
    merged_specs = data["enrichment_preview"]["specifications"]
    # Reference spec proposed
    assert merged_specs["Процессор"] == "Intel Core i5-8350U"

    # Verify product in DB was NOT mutated
    db_session.refresh(prod)
    assert prod.reference_model_id is None
    prod_specs = json.loads(prod.avito_params_json or "{}")
    assert "Процессор" not in prod_specs



def test_import_export_api(db_session):
    """Test JSON export and import (dry_run and apply)."""
    # Create model to export
    model = db_session.query(ProductReferenceModel).filter_by(stable_key="canon|i-sensys-lbp2900-test").first()
    if not model:
        model = ProductReferenceModel(
            stable_key="canon|i-sensys-lbp2900-test",
            canonical_name="Canon i-SENSYS LBP2900 Test",
            brand="Canon",
            model="i-SENSYS LBP2900 Test",
            device_type="printer"
        )
        db_session.add(model)
        db_session.flush()
        alias = ProductReferenceAlias(
            reference_model_id=model.id,
            alias="Canon LBP2900 Test",
            normalized_alias="canon lbp2900 test",
            priority=100
        )
        db_session.add(alias)
        db_session.commit()

    # 1. Export
    exp_resp = client.get("/api/product-reference/export", headers=OWNER_HEADERS)
    assert exp_resp.status_code == 200
    catalog = exp_resp.json()
    assert catalog["version"] == 1
    assert catalog["schema_version"] == "1.0"
    assert catalog["total_models"] >= 1
    assert any("canon|i-sensys-lbp2900" in m["stable_key"] for m in catalog["models"])

    # 2. Import dry-run
    import_payload = {
        "version": 1,
        "models": [
            {
                "canonical_name": "Brother HL-L2300DR Test",
                "brand": "Brother",
                "model": "HL-L2300DR Test",
                "device_type": "printer",
                "aliases": ["Brother HL-L2300 Test", "HL-L2300DR Test"]
            }
        ]
    }
    dry_resp = client.post("/api/product-reference/import?dry_run=true", json=import_payload, headers=OWNER_HEADERS)
    assert dry_resp.status_code == 200
    dry_data = dry_resp.json()
    assert dry_data["dry_run"] is True
    assert dry_data["created"] == 1

    # Verify Brother model not committed yet
    bro = db_session.query(ProductReferenceModel).filter_by(stable_key="brother|hl-l2300dr-test").first()
    assert bro is None

    # 3. Import apply
    apply_resp = client.post("/api/product-reference/import?dry_run=false", json=import_payload, headers=OWNER_HEADERS)
    assert apply_resp.status_code == 200
    apply_data = apply_resp.json()
    assert apply_data["dry_run"] is False
    assert apply_data["created"] == 1

    # Verify committed
    bro_db = db_session.query(ProductReferenceModel).filter_by(stable_key="brother|hl-l2300dr-test").first()
    assert bro_db is not None
    assert len(bro_db.aliases) >= 2


def test_learn_from_product_api(db_session):
    """Test learning/promoting a confirmed product to a reference model."""
    prod = Product(
        title="МФУ Pantum M6500W лазерный",
        sku="TEST-LEARN-001",
        brand="Pantum",
        model="M6500W",
        purchase_price=5000,
        sale_price=9000,
        avito_params_json=json.dumps({"Тип": "МФУ", "Цветность": "Ч/Б", "Wi-Fi": "Да"}, ensure_ascii=False)
    )
    db_session.add(prod)
    db_session.commit()

    resp = client.post(
        f"/api/product-reference/learn-from-product/{prod.id}",
        json={"raw_alias": "Pantum M6500W MFP"},
        headers=OWNER_HEADERS
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["brand"] == "Pantum"
    assert data["model"] == "M6500W"
    assert "pantum|m6500w" in data["stable_key"]
    assert any(a["alias"] == "Pantum M6500W MFP" for a in data["aliases"])

    # Verify product was linked
    db_session.refresh(prod)
    assert prod.reference_model_id == data["id"]
    assert prod.reference_match_method in ("confirmed_product", "learned_from_product")

