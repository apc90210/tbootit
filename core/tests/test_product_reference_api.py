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
    cat = db_session.query(Category).filter((Category.id == 10) | (Category.name == "Принтеры")).first()
    if not cat:
        cat = Category(id=10, name="Принтеры")
        db_session.add(cat)
        db_session.commit()

    # 1. Create model
    create_payload = {
        "brand": "Pantum",
        "model": "P2500W",
        "canonical_name": "Pantum P2500W",
        "default_category_id": cat.id,
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


def test_owner_model_meta():
    """Ensure /meta returns brands, device_types, and categories for OWNER."""
    resp = client.get("/api/product-reference/meta", headers=OWNER_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "brands" in data
    assert "device_types" in data
    assert "categories" in data
    assert isinstance(data["brands"], list)
    assert isinstance(data["categories"], list)


def test_owner_alias_patch_deactivate(db_session):
    """Test OWNER can update alias active status and priority with audit logging."""
    ref = db_session.query(ProductReferenceModel).filter_by(stable_key="test|alias-patch-model").first()
    if not ref:
        ref = ProductReferenceModel(
            stable_key="test|alias-patch-model",
            canonical_name="Test Alias Patch Model",
            brand="TestBrand",
            model="PatchModel",
            device_type="printer"
        )
        db_session.add(ref)
        db_session.commit()
        db_session.refresh(ref)

    alias = ProductReferenceAlias(
        reference_model_id=ref.id,
        alias="Test Alias To Toggle",
        normalized_alias="test alias to toggle",
        priority=100,
        active=True
    )
    db_session.add(alias)
    db_session.commit()
    db_session.refresh(alias)

    # 1. Deactivate alias
    patch_resp = client.patch(
        f"/api/product-reference/models/{ref.id}/aliases/{alias.id}",
        json={"active": False, "priority": 50},
        headers=OWNER_HEADERS
    )
    assert patch_resp.status_code == 200
    res_data = patch_resp.json()
    assert res_data["active"] is False
    assert res_data["priority"] == 50

    # 2. Reactivate alias
    patch_resp2 = client.patch(
        f"/api/product-reference/models/{ref.id}/aliases/{alias.id}",
        json={"active": True},
        headers=OWNER_HEADERS
    )
    assert patch_resp2.status_code == 200
    assert patch_resp2.json()["active"] is True

    # 3. Clean up
    db_session.delete(alias)
    db_session.delete(ref)
    db_session.commit()


def test_owner_linked_products_read_only(db_session):
    """Test GET /models/{id}/products returns product instances and protects instance data."""
    ref = db_session.query(ProductReferenceModel).filter_by(stable_key="test|linked-model-01").first()
    if not ref:
        ref = ProductReferenceModel(
            stable_key="test|linked-model-01",
            canonical_name="Test Linked Model 01",
            brand="TestBrand",
            model="Linked 01",
            device_type="printer"
        )
        db_session.add(ref)
        db_session.commit()
        db_session.refresh(ref)

    # Create product linked to ref
    p = Product(
        title="Тестовый связанный экземпляр",
        sku="TEST-LINKED-PROD-01",
        reference_model_id=ref.id,
        reference_match_method="test_fixture",
        reference_match_confidence=1.0,
        sale_price=15000,
        status="in_stock"
    )
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)

    resp = client.get(f"/api/product-reference/models/{ref.id}/products", headers=OWNER_HEADERS)
    assert resp.status_code == 200
    items = resp.json()
    assert any(item["id"] == p.id for item in items)
    matched_item = next(item for item in items if item["id"] == p.id)
    assert matched_item["title"] == "Тестовый связанный экземпляр"
    assert matched_item["sale_price"] == 15000.0

    # Clean up
    db_session.delete(p)
    db_session.delete(ref)
    db_session.commit()


def test_owner_product_link_and_unlink(db_session):
    """Test linking a product to a reference model and unlinking (rejecting) with audit logging."""
    ref = db_session.query(ProductReferenceModel).filter_by(stable_key="test|link-unlink-model").first()
    if not ref:
        ref = ProductReferenceModel(
            stable_key="test|link-unlink-model",
            canonical_name="Test Link Unlink Model",
            brand="TestBrand",
            model="LinkUnlink 01",
            device_type="printer"
        )
        db_session.add(ref)
        db_session.commit()
        db_session.refresh(ref)

    prod = Product(
        title="Свободный товар для проверки привязки",
        sku="TEST-FREE-PROD-01",
        sale_price=8000
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)
    assert prod.reference_model_id is None

    # 1. Link product
    link_resp = client.post(
        f"/api/product-reference/products/{prod.id}/link",
        json={"reference_model_id": ref.id, "apply_enrichment": False},
        headers=OWNER_HEADERS
    )
    assert link_resp.status_code == 200
    assert link_resp.json()["success"] is True
    assert link_resp.json()["reference_model_id"] == ref.id

    db_session.refresh(prod)
    assert prod.reference_model_id == ref.id
    assert prod.reference_match_method == "manual_owner"
    assert prod.reference_match_confidence == 1.0

    # 2. Unlink product (reject match)
    unlink_resp = client.post(
        f"/api/product-reference/products/{prod.id}/unlink?reason=rejected_by_owner",
        headers=OWNER_HEADERS
    )
    assert unlink_resp.status_code == 200
    assert unlink_resp.json()["success"] is True

    db_session.refresh(prod)
    assert prod.reference_model_id is None
    assert prod.reference_match_method == "rejected_by_owner"

    # Clean up
    db_session.delete(prod)
    db_session.delete(ref)
    db_session.commit()


def test_owner_product_enrich_apply(db_session):
    """Test re-running canonical Safe Enrichment for a linked product."""
    ref = ProductReferenceModel(
        stable_key="test-brand|enrich-apply-model",
        canonical_name="Test Brand Enrich Model",
        brand="TestBrand",
        model="Enrich Model",
        device_type="printer",
        specifications_json=json.dumps({"Скорость": "20 стр/мин", "Формат": "A4"}, ensure_ascii=False)
    )
    db_session.add(ref)
    db_session.flush()

    prod = Product(
        title="Принтер Test Brand Enrich Model б/у",
        sku="TEST-ENRICH-APPLY-01",
        reference_model_id=ref.id,
        reference_match_method="manual_owner",
        reference_match_confidence=1.0,
        sale_price=9500
    )
    db_session.add(prod)
    db_session.commit()

    resp = client.post(f"/api/product-reference/products/{prod.id}/enrich-apply", headers=OWNER_HEADERS)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["applied"] is True
    assert "fields_filled" in res_data

    # Clean up
    db_session.delete(prod)
    db_session.delete(ref)
    db_session.commit()


def test_owner_review_queue_and_conflict_resolution(db_session):
    """Test GET /review-queue and POST /conflicts/resolve."""
    # 1. Review queue endpoint
    q_resp = client.get("/api/product-reference/review-queue", headers=OWNER_HEADERS)
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert "unresolved_products" in q_data
    assert "conflicts" in q_data
    assert "summary" in q_data
    assert "total_products" in q_data["summary"]

    # 2. Conflict resolution
    # Create a test reference model with a conflict
    ref = ProductReferenceModel(
        stable_key="test-conflict|model-xyz",
        canonical_name="Test Conflict Model XYZ",
        brand="TestBrand",
        model="XYZ",
        specifications_json=json.dumps({"duplex": "Manual"}, ensure_ascii=False)
    )
    db_session.add(ref)
    db_session.commit()

    resolve_payload = {
        "stable_key": "test-conflict|model-xyz",
        "field": "duplex",
        "resolved_value": "Automatic Duplex",
        "note": "Owner manually confirmed duplex option"
    }
    r_resp = client.post("/api/product-reference/conflicts/resolve", json=resolve_payload, headers=OWNER_HEADERS)
    assert r_resp.status_code == 200
    r_data = r_resp.json()
    assert r_data["success"] is True
    assert r_data["resolved_value"] == "Automatic Duplex"

    db_session.refresh(ref)
    specs = json.loads(ref.specifications_json)
    assert specs["duplex"] == "Automatic Duplex"
    assert "Owner manually confirmed duplex option" in ref.source_note

    # Clean up
    db_session.delete(ref)
    db_session.commit()


def test_non_owner_forbidden_from_new_endpoints():
    """Ensure non-owners are strictly rejected (403) from all owner mutation endpoints."""
    endpoints = [
        ("GET", "/api/product-reference/meta", None),
        ("GET", "/api/product-reference/review-queue", None),
        ("POST", "/api/product-reference/products/1/link", {"reference_model_id": 1}),
        ("POST", "/api/product-reference/products/1/unlink", None),
        ("POST", "/api/product-reference/products/1/enrich-apply", None),
        ("POST", "/api/product-reference/conflicts/resolve", {"stable_key": "x", "field": "f", "resolved_value": "v"}),
        ("PATCH", "/api/product-reference/models/1/aliases/1", {"active": False}),
    ]
    for method, path, json_data in endpoints:
        if method == "GET":
            resp = client.get(path, headers=NON_OWNER_HEADERS)
        elif method == "POST":
            resp = client.post(path, json=json_data, headers=NON_OWNER_HEADERS)
        elif method == "PATCH":
            resp = client.patch(path, json=json_data, headers=NON_OWNER_HEADERS)
        assert resp.status_code == 403, f"Expected 403 for {method} {path}, got {resp.status_code}"


