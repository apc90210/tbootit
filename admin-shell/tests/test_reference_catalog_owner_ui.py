import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
import httpx
from app.main import app, auth_manager

client = TestClient(app)


@pytest.fixture
def seller_cert():
    users = [c for c in auth_manager.list_certificates() if not c.get("is_owner") and c.get("status") == "ACTIVE"]
    if users:
        return users[0]
    return auth_manager.create_user_certificate("Тестовый Продавец Reference UI RBAC")


@pytest.fixture
def owner_cert():
    owner = auth_manager.get_certificate("owner")
    assert owner is not None
    return owner


def test_anonymous_forbidden_from_reference_catalog():
    """Anonymous request without cert must receive 403 on reference catalog endpoints."""
    # HTML page
    resp_page = client.get("/reference/catalog")
    assert resp_page.status_code == 403

    # API models
    resp_models = client.get("/admin-api/product-reference/models")
    assert resp_models.status_code == 403

    # API review queue
    resp_rq = client.get("/admin-api/product-reference/review-queue")
    assert resp_rq.status_code == 403

    # API mutation
    resp_post = client.post("/admin-api/product-reference/models", json={"brand": "HP", "model": "Test"})
    assert resp_post.status_code == 403


def test_seller_forbidden_from_reference_catalog(seller_cert):
    """USER role certificate must receive 403 on all reference catalog endpoints."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }

    # HTML page
    resp_page = client.get("/reference/catalog", headers=seller_headers)
    assert resp_page.status_code == 403

    # API models
    resp_models = client.get("/admin-api/product-reference/models", headers=seller_headers)
    assert resp_models.status_code == 403

    # API review queue
    resp_rq = client.get("/admin-api/product-reference/review-queue", headers=seller_headers)
    assert resp_rq.status_code == 403

    # API mutation
    resp_post = client.post(
        "/admin-api/product-reference/models",
        json={"brand": "HP", "model": "Test"},
        headers=seller_headers
    )
    assert resp_post.status_code == 403


def test_spoofed_owner_header_forbidden():
    """Sending X-Auth-Is-Owner: 1 directly without owner certificate must receive 403."""
    resp = client.get("/admin-api/product-reference/models", headers={"x-auth-is-owner": "1"})
    assert resp.status_code == 403

    resp_page = client.get("/reference/catalog", headers={"x-auth-is-owner": "1"})
    assert resp_page.status_code == 403


def test_owner_reference_catalog_page_render_success(owner_cert):
    """Owner certificate successfully loads the Reference Catalog UI page."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }

    resp = client.get("/reference/catalog", headers=owner_headers)
    assert resp.status_code == 200
    html = resp.text

    # Verify navbar
    assert '<nav class="main-nav"' in html
    assert 'data-path="reference-catalog"' in html
    assert 'href="/reference/catalog"' in html

    # Verify key sections
    assert "Review Queue" in html
    assert "kpi-total-models" in html
    assert "kpi-review-queue" in html
    assert "models-tab" in html
    assert "review-tab" in html
    assert "create-tab" in html
    assert "import-export-tab" in html

    # Verify modal and instance protection container
    assert "model-modal" in html
    assert "modal-linked-tbody" in html
    assert "preview-modal" in html


def test_owner_reference_models_proxy_success(owner_cert):
    """Owner certificate allows /admin-api/product-reference/models to proxy to Core with owner credentials."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }

    mock_resp = httpx.Response(
        200,
        json={"items": [{"id": 1, "brand": "HP", "model": "LaserJet 1020"}], "total": 1, "limit": 50, "offset": 0}
    )

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp

        resp = client.get("/admin-api/product-reference/models?limit=50", headers=owner_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["brand"] == "HP"

        mock_req.assert_called_once()
        call_kwargs = mock_req.call_args[1]
        assert call_kwargs["method"] == "GET"
        assert "api/product-reference/models" in call_kwargs["url"]
        assert call_kwargs["headers"]["x-auth-is-owner"] == "1"
        assert "x-api-token" in call_kwargs["headers"]


def test_owner_review_queue_proxy_success(owner_cert):
    """Owner certificate allows /admin-api/product-reference/review-queue to proxy to Core with owner credentials."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }

    mock_resp = httpx.Response(
        200,
        json={
            "summary": {"total_review_items": 2, "unresolved_products": 1, "conflicts": 1},
            "unresolved_products": [{"product_id": 42, "name": "Лазерный принтер неизвестный"}],
            "conflicts": [{"reference_model_id": 1, "canonical_name": "HP LaserJet P3015", "field": "print_speed_ppm"}]
        }
    )

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp

        resp = client.get("/admin-api/product-reference/review-queue", headers=owner_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["total_review_items"] == 2
        assert len(data["unresolved_products"]) == 1
        assert len(data["conflicts"]) == 1

        mock_req.assert_called_once()
        call_kwargs = mock_req.call_args[1]
        assert call_kwargs["headers"]["x-auth-is-owner"] == "1"


def test_owner_conflict_resolve_proxy_success(owner_cert):
    """Owner certificate allows /admin-api/product-reference/conflicts/resolve to proxy to Core with owner credentials."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }

    mock_resp = httpx.Response(
        200,
        json={"status": "resolved", "reference_model_id": 1, "field": "print_speed_ppm", "chosen_value": 40}
    )

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp

        resp = client.post(
            "/admin-api/product-reference/conflicts/resolve",
            json={"reference_model_id": 1, "field": "print_speed_ppm", "chosen_value": 40},
            headers=owner_headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"

        mock_req.assert_called_once()
        call_kwargs = mock_req.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["headers"]["x-auth-is-owner"] == "1"
