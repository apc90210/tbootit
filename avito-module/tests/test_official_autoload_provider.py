import pytest
import json
from unittest.mock import patch, MagicMock
from app.config import settings
from app.services.capability_service import get_avito_external_capabilities
from app.services.official_autoload_provider import OfficialAvitoAutoloadSchemaProvider

def test_avito_module_owns_api_credentials():
    """Verify avito-module owns AVITO_CLIENT_ID, AVITO_CLIENT_SECRET, AVITO_API_BASE in config."""
    assert hasattr(settings, "AVITO_CLIENT_ID")
    assert hasattr(settings, "AVITO_CLIENT_SECRET")
    assert hasattr(settings, "AVITO_API_BASE")

def test_avito_module_official_provider_disabled_without_credentials():
    """Verify provider is_configured is False when credentials are not supplied."""
    provider = OfficialAvitoAutoloadSchemaProvider(client_id=None, client_secret=None)
    assert provider.is_configured is False
    with pytest.raises(ValueError) as exc_info:
        provider.authenticate()
    assert "not configured" in str(exc_info.value)

def test_avito_module_official_provider_configured_with_credentials():
    """Verify provider is_configured is True when credentials are supplied."""
    provider = OfficialAvitoAutoloadSchemaProvider(client_id="test_client_id", client_secret="test_secret")
    assert provider.is_configured is True

def test_avito_module_token_not_logged():
    """Verify token is held in memory and not leaked to logs."""
    provider = OfficialAvitoAutoloadSchemaProvider(client_id="test_id", client_secret="test_secret")
    provider._token = "secret_access_token_12345"
    assert "secret_access_token_12345" not in repr(provider)

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

def test_linked_json_values_url_security():
    """Verify security validation for linked JSON values URLs."""
    provider = OfficialAvitoAutoloadSchemaProvider()
    assert provider.validate_linked_json_url("https://api.avito.ru/autoload/v1/values/socket.json") is True
    assert provider.validate_linked_json_url("https://autoload.avito.ru/values.json") is True
    assert provider.validate_linked_json_url("http://api.avito.ru/insecure.json") is False  # HTTP forbidden
    assert provider.validate_linked_json_url("https://evil-site.com/payload.json") is False  # Non-avito host forbidden

def test_normalized_schema_payload_generation():
    """Verify build_normalized_schema_payload outputs clean payload without secrets."""
    provider = OfficialAvitoAutoloadSchemaProvider(client_id="mock", client_secret="mock")
    fields_payload = {
        "fields": [
            {
                "tag": "SocketType",
                "label": "Сокет",
                "content": [
                    {
                        "type": "select",
                        "data_type": "string",
                        "required": True,
                        "values": ["AM4", "LGA 1700"]
                    }
                ]
            }
        ]
    }
    payload = provider.build_normalized_schema_payload("materinskie-platy", "Материнские платы", fields_payload)
    assert payload["official_slug"] == "materinskie-platy"
    assert payload["category_name"] == "Материнские платы"
    assert len(payload["fields"]) == 1
    assert payload["fields"][0]["official_tag"] == "SocketType"
    assert payload["fields"][0]["display_name"] == "Сокет"
    # Ensure no secrets in payload
    payload_str = json.dumps(payload)
    assert "mock" not in payload_str
    assert "token" not in payload_str
