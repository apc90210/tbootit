import pytest
import json
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models
from app.config import settings
from app.services.avito_capability_service import get_avito_capabilities
from app.services.avito_canonical_service import (
    ensure_canonical_category_from_observed,
    sync_observed_category_to_canonical,
    get_canonical_projection_for_product,
    normalize_label
)
from app.services.avito_official_autoload_provider import OfficialAvitoAutoloadSchemaProvider
from app.services.avito_preflight_service import build_avito_publication_package, preflight_product_for_avito
from app.services.avito_transport import (
    OfficialAutoloadTransport,
    BrowserAssistedTransport,
    ManualTransport
)
from app.services.avito_schema_service import upsert_avito_category_schema, upsert_product_avito_attributes

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()

def test_capabilities_without_api_credentials():
    """Verify capabilities when API credentials are not set."""
    with patch.object(settings, "avito_client_id", None), patch.object(settings, "avito_client_secret", None):
        caps = get_avito_capabilities()
        assert caps["api_configured"] is False
        assert caps["autoload_schema_read"] is False
        assert caps["autoload_publish"] is False
        assert caps["browser_bridge"] is True
        assert caps["browser_assisted_available"] is True
        assert caps["manual_available"] is True
        assert caps["canonical_schema_source"] == "observed_only"

def test_capabilities_with_mock_api_credentials():
    """Verify capabilities when API credentials are provided."""
    with patch.object(settings, "avito_client_id", "test_id"), patch.object(settings, "avito_client_secret", "test_secret"):
        caps = get_avito_capabilities()
        assert caps["api_configured"] is True
        assert caps["autoload_schema_read"] is True
        assert caps["autoload_publish"] is False  # Explicitly disabled in R10A
        assert caps["canonical_schema_source"] == "official_api_ready"

def test_browser_assisted_available_without_autoload():
    """Verify browser-assisted transport is fully functional without official API."""
    transport = BrowserAssistedTransport()
    caps = transport.capabilities()
    assert caps["available"] is True
    assert caps["supports_form_fill"] is True
    assert caps["supports_direct_publish"] is False

def test_observed_category_can_exist_without_official_slug(db_session):
    """Verify canonical category can be created from observed category with official_slug=None."""
    obs_cat = models.AvitoCategory(name="Материнские платы", source="avito", is_active=True)
    db_session.add(obs_cat)
    db_session.commit()

    can_cat = ensure_canonical_category_from_observed(db_session, obs_cat)
    assert can_cat.id is not None
    assert can_cat.display_name == "Материнские платы"
    assert can_cat.official_slug is None
    assert can_cat.capability_source == "observed"
    assert can_cat.observed_category_id == obs_cat.id

def test_observed_field_mapping_exact_label(db_session):
    """Verify observed category sync creates exact_label mappings to canonical fields."""
    obs_cat = upsert_avito_category_schema(
        db=db_session,
        category_name="Материнские платы",
        characteristics={
            "Производитель": "ASRock",
            "Модель": "H510M-H2/M.2 SE",
            "Сокет": "LGA 1200",
            "Чипсет": "Intel H510"
        }
    )
    db_session.commit()

    can_cat, mappings = sync_observed_category_to_canonical(db_session, obs_cat.id)
    assert can_cat.display_name == "Материнские платы"
    assert len(mappings) >= 4

    # Check model mapping
    model_mapping = db_session.query(models.AvitoObservedFieldMapping).filter(
        models.AvitoObservedFieldMapping.category_id == obs_cat.id,
        models.AvitoObservedFieldMapping.observed_name_normalized == "модель"
    ).first()
    assert model_mapping is not None
    assert model_mapping.mapping_source == "exact_label"
    assert model_mapping.canonical_field is not None
    assert model_mapping.canonical_field.display_name == "Модель"

def test_unresolved_field_preserved(db_session):
    """Verify unmapped attributes remain intact and appear in unresolved_fields list."""
    obs_cat = models.AvitoCategory(name="Материнские платы", is_active=True)
    db_session.add(obs_cat)
    db_session.commit()

    prod = models.Product(
        sku="TEST-MB-101",
        title="Плата ASRock H510M",
        sale_price=4500.0,
        avito_category_id=obs_cat.id,
        status="draft"
    )
    db_session.add(prod)
    db_session.commit()

    # Add attribute without mapping
    attr_def = models.AvitoAttributeDefinition(
        category_id=obs_cat.id,
        external_key="custom_unmapped_feature",
        name="Нестандартная функция",
        type="string"
    )
    db_session.add(attr_def)
    db_session.commit()

    attr_val = models.ProductAvitoAttributeValue(
        product_id=prod.id,
        attribute_definition_id=attr_def.id,
        value="Специальный разъем RGB"
    )
    db_session.add(attr_val)
    db_session.commit()

    projection = get_canonical_projection_for_product(db_session, prod.id)
    assert len(projection["unresolved_fields"]) == 1
    assert projection["unresolved_fields"][0]["name"] == "Нестандартная функция"
    assert projection["unresolved_fields"][0]["raw_value"] == "Специальный разъем RGB"

def test_publication_package_builds_without_api(db_session):
    """Verify build_avito_publication_package generates transport-neutral output without API credentials."""
    prod = models.Product(
        sku="TEST-PROD-PKG",
        title="Комплект материнская плата и память",
        description="Полностью рабочая плата в отличном состоянии",
        sale_price=7900.0,
        brand="Gigabyte",
        model="B450M DS3H",
        condition="Б/у"
    )
    db_session.add(prod)
    db_session.commit()

    photo = models.ProductPhoto(
        product_id=prod.id,
        filename="photo.jpg",
        storage_path="/data/photos/test1.jpg",
        media_url="http://localhost:8011/media/products/test1.jpg"
    )
    db_session.add(photo)
    db_session.commit()

    with patch.object(settings, "avito_client_id", None), patch.object(settings, "avito_client_secret", None):
        package = build_avito_publication_package(db_session, prod.id)
        assert package["product_id"] == prod.id
        assert package["title"] == "Комплект материнская плата и память"
        assert package["price"] == 7900.0
        assert package["brand"] == "Gigabyte"
        assert package["model"] == "B450M DS3H"
        assert len(package["photos"]) == 1
        assert package["transport_options"]["browser_assisted"] is True
        assert package["transport_options"]["manual"] is True
        assert package["transport_options"]["official_autoload"] is False

def test_preflight_browser_ready_without_autoload(db_session):
    """Verify preflight passes for browser/manual publication when basic data is valid."""
    prod = models.Product(
        sku="TEST-PREFLIGHT-OK",
        title="Материнская плата ASUS H510",
        description="Отличная плата для офиса или игр",
        sale_price=5200.0,
        brand="ASUS",
        model="PRIME H510M-K"
    )
    db_session.add(prod)
    db_session.commit()

    photo = models.ProductPhoto(
        product_id=prod.id,
        filename="asus.jpg",
        storage_path="/data/photos/asus.jpg",
        media_url="http://localhost:8011/media/products/asus.jpg"
    )
    db_session.add(photo)
    db_session.commit()

    with patch.object(settings, "avito_client_id", None), patch.object(settings, "avito_client_secret", None):
        res = preflight_product_for_avito(db_session, prod.id)
        assert res["ready_for_any_publication"] is True
        assert res["ready_for_browser_assisted"] is True
        assert res["ready_for_manual"] is True
        assert res["ready_for_official_autoload"] is False
        assert len(res["errors"]) == 0
        assert any("AUTOLOAD_SCHEMA_UNAVAILABLE" in w for w in res["warnings"])

def test_preflight_official_not_ready_without_schema(db_session):
    """Verify preflight rejects official autoload when official slug/schema is missing."""
    prod = models.Product(
        sku="TEST-PREFLIGHT-NO-OFFICIAL",
        title="Тестовый товар",
        description="Описание",
        sale_price=1000.0
    )
    db_session.add(prod)
    db_session.commit()

    res = preflight_product_for_avito(db_session, prod.id)
    assert res["ready_for_official_autoload"] is False

def test_official_tree_parser():
    """Verify recursive parsing of official Avito category tree."""
    provider = OfficialAvitoAutoloadSchemaProvider(client_id="mock_id", client_secret="mock_secret")
    raw_tree = {
        "name": "Главная",
        "slug": "root",
        "nested": [
            {
                "name": "Товары для компьютера",
                "slug": "tovary-dlya-kompyutera",
                "nested": [
                    {
                        "name": "Материнские платы",
                        "slug": "materinskie-platy",
                        "nested": []
                    }
                ]
            }
        ]
    }
    assert raw_tree["nested"][0]["nested"][0]["slug"] == "materinskie-platy"

def test_content_rules_not_flattened():
    """Verify content rules are preserved as separate rule items with all types and dependencies."""
    provider = OfficialAvitoAutoloadSchemaProvider(client_id="mock_id", client_secret="mock_secret")
    field_payload = {
        "tag": "MotherboardSocket",
        "label": "Сокет",
        "content": [
            {
                "type": "select",
                "data_type": "string",
                "required": True,
                "values": ["LGA 1200", "LGA 1700", "AM4", "AM5"],
                "dependencies": {"action": "visible", "clause": "and"}
            },
            {
                "type": "input",
                "data_type": "string",
                "required": False,
                "values_range": {"min": 1, "max": 100}
            }
        ]
    }

    rules = provider.parse_content_rules(field_payload)
    assert len(rules) == 2
    assert rules[0]["field_type"] == "select"
    assert rules[0]["required"] is True
    assert len(rules[0]["values"]) == 4
    assert rules[1]["field_type"] == "input"
    assert rules[1]["required"] is False
    assert rules[1]["values_range"]["max"] == 100

def test_dependencies_preserved(db_session):
    """Verify dependencies JSON is persisted without loss."""
    cat = models.AvitoCanonicalCategory(internal_key="cat_test_mb", display_name="Тест")
    db_session.add(cat)
    db_session.commit()

    field = models.AvitoCanonicalField(category_id=cat.id, internal_key="socket", display_name="Сокет")
    db_session.add(field)
    db_session.commit()

    dep_data = {"action": "visible", "clause": "and", "pairs": [{"source_field_tag": "Brand", "values": ["Intel"]}]}
    rule = models.AvitoCanonicalFieldRule(
        field_id=field.id,
        ordinal=0,
        dependencies_json=json.dumps(dep_data),
        required=True
    )
    db_session.add(rule)
    db_session.commit()

    loaded = db_session.query(models.AvitoCanonicalFieldRule).filter_by(field_id=field.id).first()
    assert json.loads(loaded.dependencies_json) == dep_data

def test_inline_values_preserved(db_session):
    """Verify inline values are properly persisted and queryable."""
    cat = models.AvitoCanonicalCategory(internal_key="cat_test_vals", display_name="Тест")
    db_session.add(cat)
    db_session.commit()

    field = models.AvitoCanonicalField(category_id=cat.id, internal_key="form_factor", display_name="Форм-фактор")
    db_session.add(field)
    db_session.commit()

    db_session.add(models.AvitoCanonicalFieldValue(field_id=field.id, value="Micro-ATX", official_value="Micro-ATX", source="inline"))
    db_session.add(models.AvitoCanonicalFieldValue(field_id=field.id, value="Standard-ATX", official_value="Standard-ATX", source="inline"))
    db_session.commit()

    vals = db_session.query(models.AvitoCanonicalFieldValue).filter_by(field_id=field.id).all()
    assert len(vals) == 2
    assert {v.value for v in vals} == {"Micro-ATX", "Standard-ATX"}

def test_linked_json_values_url_security():
    """Verify security validation for linked JSON values URLs."""
    provider = OfficialAvitoAutoloadSchemaProvider()
    assert provider.validate_linked_json_url("https://api.avito.ru/autoload/v1/values/socket.json") is True
    assert provider.validate_linked_json_url("https://autoload.avito.ru/values.json") is True
    assert provider.validate_linked_json_url("http://api.avito.ru/insecure.json") is False  # HTTP forbidden
    assert provider.validate_linked_json_url("https://evil-site.com/payload.json") is False  # Non-avito host forbidden

def test_transport_publish_disabled(db_session):
    """Verify publish() raises NotImplementedError on all transports in Stage 06A-R10A."""
    prod = models.Product(sku="TEST-P1", title="Плата", sale_price=1000.0)
    db_session.add(prod)
    db_session.commit()

    for transport in (OfficialAutoloadTransport(), BrowserAssistedTransport(), ManualTransport()):
        with pytest.raises(NotImplementedError) as exc_info:
            transport.publish(db_session, prod.id)
        assert "disabled in Stage 06A-R10A" in str(exc_info.value)

def test_no_avito_write_calls():
    """Verify that provider and transports do not execute POST /autoload/v1/upload or real write calls."""
    provider = OfficialAvitoAutoloadSchemaProvider(client_id="mock", client_secret="mock")
    # Verify no upload / publish methods exist on provider
    assert not hasattr(provider, "upload_feed")
    assert not hasattr(provider, "publish_ad")
    assert not hasattr(provider, "create_ad")
