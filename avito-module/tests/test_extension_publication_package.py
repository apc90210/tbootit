import pytest
from unittest.mock import patch, MagicMock
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def paired_token():
    gen_res = client.post("/extension/api/pairing/generate")
    code = gen_res.json()["pair_code"]
    pair_res = client.post("/extension/api/pairing/pair", json={"pair_code": code})
    return pair_res.json()["extension_token"]

def test_publication_package_extension_endpoint_requires_pairing():
    """Verify endpoint rejects requests without paired X-Extension-Token."""
    res = client.get("/extension/api/publication-package/58")
    assert res.status_code == 401

    res_invalid = client.get("/extension/api/publication-package/58", headers={"X-Extension-Token": "invalid_tok"})
    assert res_invalid.status_code == 401

def test_publication_package_success_with_paired_token(paired_token):
    """Verify endpoint queries Core internal API and formats safe publication package."""
    mock_pkg = {
        "product_id": 58,
        "title": "Материнская плата ASRock H510M",
        "description": "Рабочая плата LGA 1200",
        "price": 4500.0,
        "category": "Материнские платы",
        "brand": "ASRock",
        "model": "H510M-H2/M.2 SE",
        "condition": "Б/у",
        "characteristics": {"Сокет": "LGA 1200", "Чипсет": "Intel H510"},
        "photos": [{"url": "http://localhost:8011/media/p58.jpg", "position": 0}]
    }
    mock_preflight = {
        "ready_for_browser_assisted": True,
        "ready_for_official_autoload": False,
        "official_slug": None,
        "errors": [],
        "warnings": ["AUTOLOAD_SCHEMA_UNAVAILABLE: Schema not configured"]
    }

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp_pkg = MagicMock()
        mock_resp_pkg.read.return_value = json.dumps(mock_pkg).encode("utf-8")
        mock_resp_pkg.__enter__.return_value = mock_resp_pkg

        mock_resp_pre = MagicMock()
        mock_resp_pre.read.return_value = json.dumps(mock_preflight).encode("utf-8")
        mock_resp_pre.__enter__.return_value = mock_resp_pre

        mock_urlopen.side_effect = [mock_resp_pkg, mock_resp_pre]

        res = client.get(
            "/extension/api/publication-package/58",
            headers={"X-Extension-Token": paired_token}
        )

        assert res.status_code == 200
        data = res.json()
        assert data["schema_version"] == 1
        assert data["product_id"] == 58
        assert data["title"] == "Материнская плата ASRock H510M"
        assert data["price"] == 4500.0
        assert data["brand"] == "ASRock"
        assert data["model"] == "H510M-H2/M.2 SE"
        assert data["characteristics"]["Сокет"] == "LGA 1200"
        assert len(data["photos"]) == 1
        assert data["preflight"]["ready_for_browser_assisted"] is True
        assert data["category"]["display_name"] == "Материнские платы"

def test_publication_package_contains_no_secrets(paired_token):
    """Verify returned package has ZERO tokens, client_secrets, or cookies."""
    mock_pkg = {"product_id": 10, "title": "Товар", "price": 100.0}
    mock_pre = {"ready_for_browser_assisted": True, "errors": [], "warnings": []}

    with patch("urllib.request.urlopen") as mock_urlopen:
        m1 = MagicMock()
        m1.read.return_value = json.dumps(mock_pkg).encode("utf-8")
        m1.__enter__.return_value = m1
        m2 = MagicMock()
        m2.read.return_value = json.dumps(mock_pre).encode("utf-8")
        m2.__enter__.return_value = m2
        mock_urlopen.side_effect = [m1, m2]

        res = client.get(
            "/extension/api/publication-package/10",
            headers={"X-Extension-Token": paired_token}
        )
        body_text = res.text.lower()
        assert "secret" not in body_text
        assert "cookie" not in body_text
        assert "password" not in body_text
        assert paired_token.lower() not in body_text
