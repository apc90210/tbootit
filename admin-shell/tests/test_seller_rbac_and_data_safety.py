import os
import pytest
from fastapi.testclient import TestClient
from app.main import app, auth_manager

client = TestClient(app)


@pytest.fixture
def seller_cert():
    # Issue or retrieve an active USER certificate
    users = [c for c in auth_manager.list_certificates() if not c.get("is_owner") and c.get("status") == "ACTIVE"]
    if users:
        return users[0]
    return auth_manager.create_user_certificate("Тестовый Продавец")


@pytest.fixture
def owner_cert():
    owner = auth_manager.get_certificate("owner")
    assert owner is not None
    return owner


def test_seller_forbidden_from_dev_reset(seller_cert):
    """Sellers (USER certificate) must be blocked from dev-reset at both gateway and API levels."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }

    # Gateway auth subrequest check
    gw_resp = client.get(
        "/internal-auth/verify",
        headers={**seller_headers, "x-original-uri": "/admin-api/dev-reset"},
    )
    assert gw_resp.status_code == 403
    assert "OWNER certificate required" in gw_resp.json()["detail"]

    # Direct API proxy check
    api_resp = client.post("/admin-api/dev-reset", headers=seller_headers)
    assert api_resp.status_code == 403
    assert "Owner certificate required" in api_resp.json()["detail"]


def test_seller_forbidden_from_seed(seller_cert):
    """Sellers (USER certificate) must be blocked from seed data at both gateway and API levels."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }

    # Gateway auth subrequest check
    gw_resp = client.get(
        "/internal-auth/verify",
        headers={**seller_headers, "x-original-uri": "/admin-api/seed"},
    )
    assert gw_resp.status_code == 403
    assert "OWNER certificate required" in gw_resp.json()["detail"]

    # Direct API proxy check
    api_resp = client.post("/admin-api/seed", headers=seller_headers)
    assert api_resp.status_code == 403
    assert "Owner certificate required" in api_resp.json()["detail"]


def test_seller_forbidden_from_deleting_avito_profile(seller_cert):
    """Sellers must not be able to delete Avito profiles."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }

    resp = client.delete("/admin-api/avito/profiles/test_account_key", headers=seller_headers)
    assert resp.status_code == 403
    assert "Owner certificate required" in resp.json()["detail"]


def test_production_environment_blocks_dev_reset_even_for_owner(monkeypatch, owner_cert):
    """In production, dev-reset must fail-fast with 403 even if called with an owner certificate."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }

    monkeypatch.setenv("ENVIRONMENT", "production")
    resp = client.post("/admin-api/dev-reset", headers=owner_headers)
    assert resp.status_code == 403
    assert "strictly forbidden in production" in resp.json()["detail"]

    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("TECHNOREBOOT_DATA_ROOT", "/srv/technoreboot/data")
    resp2 = client.post("/admin-api/dev-reset", headers=owner_headers)
    assert resp2.status_code == 403
    assert "strictly forbidden in production" in resp2.json()["detail"]


def test_seller_ui_hides_destructive_buttons_and_admin_links(seller_cert):
    """The dashboard and accounts pages must NOT render reset/seed/backup/cert buttons for sellers."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }

    resp = client.get("/", headers=seller_headers)
    assert resp.status_code == 200
    # Seller cannot see reset or seed buttons
    assert "Сбросить БД" not in resp.text
    assert "Заполнить тестовыми данными" not in resp.text
    # Seller cannot see backups or certificate management in navigation
    assert 'href="/backups"' not in resp.text
    assert 'href="/certificates"' not in resp.text

    resp_avito = client.get("/avito/accounts", headers=seller_headers)
    assert resp_avito.status_code == 200
    assert "deleteProfile(" not in resp_avito.text


def test_owner_ui_shows_admin_controls(owner_cert):
    """Dashboard renders seed/reset buttons and backup/certificate links for owner."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }

    resp = client.get("/", headers=owner_headers)
    assert resp.status_code == 200
    assert "Сбросить БД" in resp.text
    assert "Заполнить тестовыми данными" in resp.text
    assert 'href="/backups"' in resp.text
    assert 'href="/certificates"' in resp.text
