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
    return auth_manager.create_user_certificate("Тестовый Продавец Reservations RBAC")


@pytest.fixture
def owner_cert():
    owner = auth_manager.get_certificate("owner")
    assert owner is not None
    return owner


def test_anonymous_forbidden_from_reservations():
    """Anonymous request without cert must receive 403 on reservations endpoints."""
    # HTML page
    resp_page = client.get("/inventory/reservations")
    assert resp_page.status_code == 403

    # API list
    resp_list = client.get("/admin-api/reservations")
    assert resp_list.status_code == 403

    # API status update
    resp_patch = client.patch("/admin-api/reservations/1/status", json={"status": "confirmed"})
    assert resp_patch.status_code == 403


def test_seller_forbidden_from_reservations(seller_cert):
    """USER role certificate must receive 403 on reservations endpoints."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }

    # HTML page
    resp_page = client.get("/inventory/reservations", headers=seller_headers)
    assert resp_page.status_code == 403

    # API list
    resp_list = client.get("/admin-api/reservations", headers=seller_headers)
    assert resp_list.status_code == 403

    # API status update
    resp_patch = client.patch(
        "/admin-api/reservations/1/status",
        json={"status": "confirmed"},
        headers=seller_headers
    )
    assert resp_patch.status_code == 403


def test_spoofed_owner_header_forbidden():
    """Sending X-Auth-Is-Owner: 1 directly without owner certificate must receive 403."""
    resp = client.get("/admin-api/reservations", headers={"x-auth-is-owner": "1"})
    assert resp.status_code == 403


def test_owner_reservations_list_proxy_success(owner_cert):
    """Owner certificate allows reservations list request to proxy to Core with owner credentials."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }

    mock_resp = httpx.Response(
        200,
        json={"items": [{"id": 1, "product_id": 10, "phone": "+79991234567", "status": "pending"}], "total": 1, "limit": 50, "offset": 0}
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp

        resp = client.get("/admin-api/reservations", headers=owner_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["phone"] == "+79991234567"

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["headers"]["x-auth-is-owner"] == "1"
        assert "x-api-token" in call_kwargs["headers"]


def test_owner_reservation_status_patch_proxy_success(owner_cert):
    """Owner certificate allows reservation status PATCH to proxy to Core with owner credentials."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }

    mock_resp = httpx.Response(
        200,
        json={"id": 1, "product_id": 10, "phone": "+79991234567", "status": "confirmed"}
    )

    with patch("httpx.AsyncClient.patch", new_callable=AsyncMock) as mock_patch:
        mock_patch.return_value = mock_resp

        resp = client.patch(
            "/admin-api/reservations/1/status",
            json={"status": "confirmed", "comment": "Confirmed by owner"},
            headers=owner_headers
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

        mock_patch.assert_called_once()
        call_kwargs = mock_patch.call_args[1]
        assert call_kwargs["headers"]["x-auth-is-owner"] == "1"
        assert call_kwargs["json"]["status"] == "confirmed"


def test_owner_reservations_page_renders(owner_cert):
    """Owner can load the /inventory/reservations HTML page."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }
    resp = client.get("/inventory/reservations", headers=owner_headers)
    assert resp.status_code == 200
    assert "Заявки на резервирование" in resp.text
