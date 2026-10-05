"""
Tests for Product Reference Enrichment Service.
Fulfills PROMPT_WEB_07A Section 23:
- Fills missing fields only
- Does not overwrite explicit fields
- Specs merge (existing value > reference default value)
- Restoration category priority (remains "Техника под восстановление")
- Provenance and audit logging
"""

import json
import pytest
from sqlalchemy.orm import Session

from app import models
from app.services.product_reference_enricher import (
    enrich_product_from_reference,
    RESTORATION_CATEGORY_ID,
    UNCATEGORIZED_CATEGORY_ID
)


@pytest.fixture
def sample_reference_model(db: Session) -> models.ProductReferenceModel:
    cat = db.query(models.Category).filter_by(slug="mfu").first()
    if not cat:
        cat = models.Category(name="МФУ", slug="mfu")
        db.add(cat)
        db.flush()

    specs_json = json.dumps({
        "Тип устройства": "МФУ",
        "Технология печати": "Лазерная",
        "Цветность печати": "Черно-белая",
        "Максимальный формат": "A4",
        "Двусторонняя печать": "Да"
    }, ensure_ascii=False)

    ref = db.query(models.ProductReferenceModel).filter_by(stable_key="xerox|versalink-b405").first()
    if not ref:
        ref = models.ProductReferenceModel(
            stable_key="xerox|versalink-b405",
            canonical_name="Xerox VersaLink B405",
            brand="Xerox",
            model="VersaLink B405",
            device_type="mfu",
            default_category_id=cat.id,
            specifications_json=specs_json,
            site_title="Сетевое МФУ Xerox VersaLink B405DN",
            site_description="Производительное лазерное МФУ А4 для офиса.",
            active=True,
            source="test",
        )
        db.add(ref)
    else:
        ref.default_category_id = cat.id
        ref.specifications_json = specs_json
        ref.site_title = "Сетевое МФУ Xerox VersaLink B405DN"
        ref.site_description = "Производительное лазерное МФУ А4 для офиса."

    db.commit()
    db.refresh(ref)
    return ref




def test_enrichment_fills_missing_fields(db: Session, sample_reference_model: models.ProductReferenceModel):
    product = models.Product(
        sku="TEST-SKU-001",
        title="Мфу Xerox VersaLink B405",
        brand=None,
        model=None,
        category_id=UNCATEGORIZED_CATEGORY_ID,
        site_title=None,
        site_description=None,
        sale_price=25000.0,
        purchase_price=15000.0,
        quantity=2,
        status="in_stock",
        condition="Б/у",
        serial_number="SN-12345",
        description="Хорошее состояние, проверен.",
    )
    db.add(product)
    db.flush()

    res = enrich_product_from_reference(
        db=db,
        product=product,
        reference=sample_reference_model,
        method="tier1_exact_alias",
        confidence=1.00,
        apply=True,
    )

    db.commit()
    db.refresh(product)

    # Missing fields must be filled
    assert product.brand == "Xerox"
    assert product.model == "VersaLink B405"
    assert product.category_id == sample_reference_model.default_category_id
    assert product.site_title == "Сетевое МФУ Xerox VersaLink B405DN"
    assert product.site_description == "Производительное лазерное МФУ А4 для офиса."

    # Provenance must be recorded
    assert product.reference_model_id == sample_reference_model.id
    assert product.reference_match_method == "tier1_exact_alias"
    assert product.reference_match_confidence == 1.00
    assert product.reference_enriched_at is not None

    # Specifications must be merged
    specs = json.loads(product.avito_params_json)
    assert specs["Тип устройства"] == "МФУ"
    assert specs["Технология печати"] == "Лазерная"
    assert specs["Двусторонняя печать"] == "Да"


def test_enrichment_does_not_overwrite_explicit_data(db: Session, sample_reference_model: models.ProductReferenceModel):
    # Product with explicit custom brand, model, site_title, and description
    custom_desc = "Индивидуальное описание с дефектом петли."
    product = models.Product(
        sku="TEST-SKU-002",
        title="Мфу Xerox VersaLink B405",
        brand="Xerox Corp",
        model="B405DN Special",
        site_title="Кастомный заголовок магазина",
        site_description="Кастомное описание",
        sale_price=22000.0,
        purchase_price=12000.0,
        quantity=1,
        status="in_stock",
        condition="Удовлетворительное",
        serial_number="SN-99999",
        description=custom_desc,
        notes="Внутренняя заметка мастера",
    )
    db.add(product)
    db.flush()

    res = enrich_product_from_reference(
        db=db,
        product=product,
        reference=sample_reference_model,
        method="tier1_exact_alias",
        confidence=1.00,
        apply=True,
    )
    db.commit()
    db.refresh(product)

    # Explicit values must NOT be overwritten!
    assert product.brand == "Xerox Corp"
    assert product.model == "B405DN Special"
    assert product.site_title == "Кастомный заголовок магазина"
    assert product.site_description == "Кастомное описание"
    assert product.sale_price == 22000.0
    assert product.purchase_price == 12000.0
    assert product.quantity == 1
    assert product.status == "in_stock"
    assert product.condition == "Удовлетворительное"
    assert product.serial_number == "SN-99999"
    assert product.description == custom_desc
    assert product.notes == "Внутренняя заметка мастера"


def test_specifications_merge_existing_value_wins(db: Session, sample_reference_model: models.ProductReferenceModel):
    # Product with existing custom spec value
    existing_specs = {
        "Двусторонняя печать": "С дефектом дуплекса",
        "Собственная характеристика": "Установлен новый картридж"
    }
    product = models.Product(
        sku="TEST-SKU-003",
        title="Мфу Xerox VersaLink B405",
        avito_params_json=json.dumps(existing_specs, ensure_ascii=False)
    )
    db.add(product)
    db.flush()

    enrich_product_from_reference(
        db=db,
        product=product,
        reference=sample_reference_model,
        method="tier1_exact_alias",
        confidence=1.00,
        apply=True,
    )
    db.commit()
    db.refresh(product)

    merged = json.loads(product.avito_params_json)
    # Existing product value must NOT be overwritten by reference default
    assert merged["Двусторонняя печать"] == "С дефектом дуплекса"
    # Unknown existing product spec must be preserved
    assert merged["Собственная характеристика"] == "Установлен новый картридж"
    # Missing specs from reference must be added
    assert merged["Тип устройства"] == "МФУ"
    assert merged["Технология печати"] == "Лазерная"


def test_restoration_category_strictly_preserved(db: Session, sample_reference_model: models.ProductReferenceModel):
    # Product in category 52 (Техника под восстановление)
    product = models.Product(
        sku="TEST-SKU-004",
        title="Лазерное мфу 3 в 1 xerox b405 под восстановление",
        category_id=RESTORATION_CATEGORY_ID,
    )
    db.add(product)
    db.flush()

    res = enrich_product_from_reference(
        db=db,
        product=product,
        reference=sample_reference_model,
        method="tier1_exact_alias",
        confidence=1.00,
        apply=True,
    )
    db.commit()
    db.refresh(product)

    # Reference model default category is МФУ, but product MUST remain restoration!
    assert product.category_id == RESTORATION_CATEGORY_ID
    # Model data should still be safely enriched
    assert product.brand == "Xerox"
    assert product.model == "VersaLink B405"
    assert product.reference_model_id == sample_reference_model.id
