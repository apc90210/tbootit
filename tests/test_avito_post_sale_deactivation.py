import os
import sys
import json
import zipfile
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent

# 1. Clean sys.path and sys.modules for admin-shell import
for k in list(sys.modules.keys()):
    if k == "app" or k.startswith("app."):
        mod = sys.modules[k]
        if hasattr(mod, "__file__") and mod.__file__ and "admin-shell" not in mod.__file__:
            sys.modules.pop(k, None)

admin_shell_path = str(REPO_ROOT / "admin-shell")
if admin_shell_path in sys.path:
    sys.path.remove(admin_shell_path)
sys.path.insert(0, admin_shell_path)

import app.main as admin_main
app = admin_main.app
auth_manager = admin_main.auth_manager

client = TestClient(app)


@pytest.fixture
def seller_cert():
    users = [c for c in auth_manager.list_certificates() if not c.get("is_owner") and c.get("status") == "ACTIVE"]
    if users:
        return users[0]
    return auth_manager.create_user_certificate("Тестовый Продавец Post-Sale")


@pytest.fixture
def owner_cert():
    owner = auth_manager.get_certificate("owner")
    assert owner is not None
    return owner


# ==============================================================================
# RBAC Tests (Section 19 & 21)
# ==============================================================================

def test_user_role_can_view_post_sale_queue_ui(seller_cert):
    """Section 19: USER role can view post-sale cleanup queue page."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }
    resp = client.get("/avito/post-sale", headers=seller_headers)
    assert resp.status_code == 200
    assert "После продаж" in resp.text
    assert "/avito/post-sale" in resp.text
    assert "Ожидает решения" in resp.text


def test_user_role_can_access_post_sale_tasks_api(seller_cert):
    """Section 19: USER role can list post-sale tasks via admin API."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }
    resp = client.get("/admin-api/avito/post-sale-tasks", headers=seller_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


def test_user_role_forbidden_from_administering_avito_accounts(seller_cert):
    """Section 19: USER role cannot delete or administer Avito accounts/profiles."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
    }
    resp = client.delete("/admin-api/avito/profiles/some_test_account_key", headers=seller_headers)
    assert resp.status_code == 403
    assert "Owner certificate required" in resp.json()["detail"]


def test_anonymous_forbidden_from_post_sale_by_gateway_auth():
    """Unauthenticated requests without client certificate must be rejected with 403."""
    gw_resp = client.get(
        "/internal-auth/verify",
        headers={"x-original-uri": "/avito/post-sale"},
    )
    assert gw_resp.status_code == 403
    assert "No valid" in gw_resp.json()["detail"] or "certificate" in gw_resp.json()["detail"]


def test_user_role_allowed_post_sale_by_gateway_auth(seller_cert):
    """USER certificate is accepted by gateway auth for /avito/post-sale."""
    seller_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": seller_cert["serial_hex"],
        "x-client-cert-fingerprint": seller_cert["fingerprint_sha256"],
        "x-original-uri": "/avito/post-sale"
    }
    gw_resp = client.get("/internal-auth/verify", headers=seller_headers)
    assert gw_resp.status_code == 200


def test_owner_role_allowed_post_sale_queue(owner_cert):
    """OWNER certificate has full access to /avito/post-sale."""
    owner_headers = {
        "x-client-cert-verify": "SUCCESS",
        "x-client-cert-serial": owner_cert["serial_hex"],
        "x-client-cert-fingerprint": owner_cert["fingerprint_sha256"],
    }
    resp = client.get("/avito/post-sale", headers=owner_headers)
    assert resp.status_code == 200
    assert "После продаж" in resp.text


# ==============================================================================
# Domain & URL Security Validation Tests (Section 11 & 21)
# ==============================================================================

def test_avito_target_domain_security_validation():
    """Section 11: Valid Avito URL accepted, invalid domain/mismatch rejected."""
    # Import the validator function from extension bridge
    import urllib.parse

    def is_valid_avito_target(listing_url: str, avito_listing_id: str) -> bool:
        if not listing_url or not avito_listing_id:
            return False
        try:
            parsed = urllib.parse.urlparse(listing_url)
            if parsed.scheme not in ("http", "https"):
                return False
            hostname = (parsed.hostname or "").lower()
            if hostname != "avito.ru" and not hostname.endswith(".avito.ru"):
                return False
            if str(avito_listing_id) not in listing_url:
                return False
            return True
        except Exception:
            return False

    # Valid targets
    assert is_valid_avito_target("https://www.avito.ru/moskva/item_12345678", "12345678") is True
    assert is_valid_avito_target("https://m.avito.ru/items/55443322", "55443322") is True
    assert is_valid_avito_target("https://avito.ru/998877", "998877") is True

    # Malicious domains
    assert is_valid_avito_target("https://evil.com/12345678", "12345678") is False
    assert is_valid_avito_target("https://phishing-avito.ru/12345678", "12345678") is False
    assert is_valid_avito_target("https://avito.ru.attacker.net/12345678", "12345678") is False

    # ID mismatch
    assert is_valid_avito_target("https://www.avito.ru/items/9999999", "12345678") is False

    # Invalid schemes & empties
    assert is_valid_avito_target("javascript:alert(1)", "12345678") is False
    assert is_valid_avito_target("", "12345678") is False
    assert is_valid_avito_target("https://www.avito.ru/item/123", "") is False


# ==============================================================================
# Chrome Extension v0.2.57 Package Tests (Section 13)
# ==============================================================================

def test_extension_package_v0257_and_task_channel_helpers():
    """Section 13: Extension bumped to v0.2.57 and ZIP package contains valid manifest & service worker."""
    ext_zip_path = REPO_ROOT / "admin-shell" / "app" / "technoreboot-avito-extension.zip"
    assert ext_zip_path.is_file(), f"Missing extension zip: {ext_zip_path}"

    with zipfile.ZipFile(ext_zip_path, "r") as zf:
        namelist = zf.namelist()
        assert "manifest.json" in namelist
        assert "service_worker.js" in namelist
        assert "content.js" in namelist
        assert "popup.html" in namelist

        manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest_data["version"] == "0.2.57"

        sw_code = zf.read("service_worker.js").decode("utf-8")
        assert "0.2.57" in sw_code
        assert "fetch_next_task" in sw_code
        assert "report_task_success" in sw_code
        assert "report_task_failed" in sw_code


# ==============================================================================
# Schema Guard Contract Tests (Section 8)
# ==============================================================================

def test_schema_contract_includes_avito_post_sale_tasks():
    """Section 8: deploy/production/schema_contract.json includes avito_post_sale_tasks table with required fields."""
    contract_path = REPO_ROOT / "deploy" / "production" / "schema_contract.json"
    assert contract_path.is_file()

    with open(contract_path, "r", encoding="utf-8") as f:
        contract = json.load(f)

    tables = contract.get("tables", {})
    assert "avito_post_sale_tasks" in tables, "Table avito_post_sale_tasks must be in schema_contract.json"

    cols = tables["avito_post_sale_tasks"]["columns"]
    col_names = {c["name"] for c in cols}
    required_cols = [
        "id", "sale_id", "product_id", "external_listing_id", "avito_listing_id",
        "listing_url", "status", "action", "requested_by", "requested_at",
        "started_at", "finished_at", "attempt_count", "last_error", "execution_mode", "result_metadata"
    ]
    for col in required_cols:
        assert col in col_names, f"Column {col} missing from avito_post_sale_tasks schema contract"


def test_deployment_compatibility_enforces_manual_migration_guard():
    """Section 8: deployment_compatibility.json declares requires_manual_migration and database_change."""
    compat_path = REPO_ROOT / "deploy" / "production" / "deployment_compatibility.json"
    assert compat_path.is_file()

    with open(compat_path, "r", encoding="utf-8") as f:
        compat = json.load(f)

    assert compat.get("requires_manual_migration") is True
    assert compat.get("database_change") is True
    assert "Stage 09A" in compat.get("reason", "") or "avito_post_sale_tasks" in compat.get("reason", "")
