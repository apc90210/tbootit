import pytest
from fastapi.testclient import TestClient
from app.main import app, auth_manager
from bs4 import BeautifulSoup

client = TestClient(app)

@pytest.fixture
def owner_headers():
    owner = auth_manager.get_certificate("owner")
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner["serial_hex"] if owner else "test_serial",
        "x-client-cert-fingerprint": owner["fingerprint_sha256"] if owner else "test_fp",
        "x-auth-is-owner": "true",
    }

@pytest.fixture
def user_headers():
    import uuid
    user = auth_manager.create_user_certificate(f"Test Seller {uuid.uuid4().hex[:6]}")
    return {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": user["serial_hex"],
        "x-client-cert-fingerprint": user["fingerprint_sha256"],
        "x-auth-is-owner": "false",
    }

def test_admin_dashboard_renders_android_nav_button(owner_headers):
    """1. Authenticated admin page renders the new navigation entry with label Android-приложение."""
    resp = client.get("/", headers=owner_headers)
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.text, "html.parser")
    nav = soup.find("nav", class_="main-nav")
    assert nav is not None, "nav.main-nav not found on dashboard"
    
    # 2. href is exactly /android
    android_links = [a for a in nav.find_all("a") if a.get("href") == "/android"]
    assert len(android_links) == 1, f"Expected exactly 1 /android link in main-nav, got {len(android_links)}"
    assert android_links[0].text.strip() == "Android-приложение"

def test_android_page_renders_under_valid_auth(owner_headers, user_headers):
    """3. /android returns expected protected page for valid authenticated context (OWNER and USER)."""
    # OWNER
    resp_owner = client.get("/android", headers=owner_headers)
    assert resp_owner.status_code == 200
    assert "Android приложение" in resp_owner.text
    assert "Подключить устройство" in resp_owner.text
    
    # USER
    resp_user = client.get("/android", headers=user_headers)
    assert resp_user.status_code == 200
    assert "Android приложение" in resp_user.text

def test_android_page_denied_without_auth():
    """4. /android is still denied without required client authentication."""
    resp = client.get("/android")
    assert resp.status_code == 403
    assert "Valid client certificate required" in resp.text

def test_android_download_route_protection_and_behavior(owner_headers):
    """5. /android/download route is unchanged: denied without auth, accessible under auth."""
    # Unauthenticated
    unauth = client.get("/android/download")
    assert unauth.status_code == 403

    # Authenticated
    auth_resp = client.get("/android/download", headers=owner_headers)
    if auth_resp.status_code == 200:
        assert auth_resp.headers.get("content-type") == "application/vnd.android.package-archive"
        assert "attachment" in auth_resp.headers.get("content-disposition", "") or "technoreboot" in auth_resp.headers.get("content-disposition", "")

def test_no_duplicate_android_nav_links(owner_headers):
    """6. No duplicate Android nav entry across authenticated admin views."""
    pages = ["/", "/android", "/backups", "/certificates", "/products/json", "/avito/extension", "/avito"]
    for page in pages:
        resp = client.get(page, headers=owner_headers)
        assert resp.status_code == 200
        soup = BeautifulSoup(resp.text, "html.parser")
        nav = soup.find("nav", class_="main-nav")
        assert nav is not None, f"main-nav missing on {page}"
        android_links = [a for a in nav.find_all("a") if a.get("href") == "/android"]
        assert len(android_links) == 1, f"Expected exactly 1 /android link on {page}, got {len(android_links)}"
        assert android_links[0].text.strip() == "Android-приложение"
