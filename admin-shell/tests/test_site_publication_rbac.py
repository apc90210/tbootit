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
    return auth_manager.create_user_certificate("Тестовый Продавец SitePub RBAC")


@pytest.fixture
def owner_cert():
    owner = auth_manager.get_certificate("owner")
    assert owner is not None
    return owner


def test_anonymous_forbidden_from_site_publication():
    """Anonymous request without cert must receive 403 on site-publication."""
    resp_patch = client.patch("/admin-api/products/1/site-publication", json={"is_published_site": 1})
    assert resp_patch.status_code == 403
    assert "Owner certificate required" in resp_patch.json()["detail"]

    resp_put = client.put("/admin-api/products/1/site-publication", json={"is_published_site": 1})
    assert resp_put.status_code == 403
    assert "Owner certificate required" in resp_put.json()["detail"]


def test_seller_forbidden_from_site_publication(seller_cert):
    """USER role certificate must receive 403 on site-publication."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }
    resp = client.patch(
        "/admin-api/products/1/site-publication",
        json={"is_published_site": 1},
        headers=seller_headers
    )
    assert resp.status_code == 403
    assert "Owner certificate required" in resp.json()["detail"]


def test_spoofed_owner_header_forbidden():
    """Sending X-Auth-Is-Owner: 1 directly without owner certificate must receive 403."""
    resp = client.patch(
        "/admin-api/products/1/site-publication",
        json={"is_published_site": 1},
        headers={"x-auth-is-owner": "1"}
    )
    assert resp.status_code == 403
    assert "Owner certificate required" in resp.json()["detail"]


def test_owner_site_publication_proxy_success(owner_cert):
    """Owner certificate allows site publication request to proxy to Core with owner credentials."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }

    mock_resp = httpx.Response(
        200,
        json={"id": 1, "is_published_site": 1, "site_title": "Owner Title", "site_description": "Owner Desc"}
    )

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_resp

        # Test PATCH
        resp = client.patch(
            "/admin-api/products/1/site-publication",
            json={"is_published_site": 1, "site_title": "Owner Title"},
            headers=owner_headers
        )
        assert resp.status_code == 200
        assert resp.json()["site_title"] == "Owner Title"
        mock_req.assert_called_once()
        call_kwargs = mock_req.call_args[1]
        assert call_kwargs["headers"]["x-auth-is-owner"] == "1"
        assert call_kwargs["method"] == "PATCH"

    # Test PUT
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req_put:
        mock_req_put.return_value = mock_resp
        resp_put = client.put(
            "/admin-api/products/1/site-publication",
            json={"is_published_site": 1, "site_title": "Owner Title"},
            headers=owner_headers
        )
        assert resp_put.status_code == 200
        mock_req_put.assert_called_once()
        call_kwargs_put = mock_req_put.call_args[1]
        assert call_kwargs_put["headers"]["x-auth-is-owner"] == "1"
        assert call_kwargs_put["method"] == "PUT"
