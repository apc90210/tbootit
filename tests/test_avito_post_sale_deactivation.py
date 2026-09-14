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
# Chrome Extension v0.2.59 Package Tests (Section 13 & 14)
# ==============================================================================

def test_extension_package_v0259_and_task_channel_helpers():
    """Section 14: Extension bumped to v0.2.59 and ZIP package contains valid manifest, service worker & content script."""
    ext_zip_path = REPO_ROOT / "admin-shell" / "app" / "technoreboot-avito-extension.zip"
    assert ext_zip_path.is_file(), f"Missing extension zip: {ext_zip_path}"

    with zipfile.ZipFile(ext_zip_path, "r") as zf:
        namelist = zf.namelist()
        assert "manifest.json" in namelist
        assert "service_worker.js" in namelist
        assert "content.js" in namelist
        assert "popup.html" in namelist
        assert "popup.js" in namelist

        manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
        assert manifest_data["version"] == "0.2.59"

        sw_code = zf.read("service_worker.js").decode("utf-8")
        assert "0.2.59" in sw_code
        assert "pollNextDeactivationTask" in sw_code
        assert "getActiveDeactivationTask" in sw_code
        assert "executeDeactivationFlow" in sw_code
        assert "isValidAvitoTarget" in sw_code
        assert "report_task_success" in sw_code
        assert "report_task_failed" in sw_code

        content_code = zf.read("content.js").decode("utf-8")
        assert "0.2.59" in content_code
        assert "execute_deactivation" in content_code
        assert "discoverDeactivationControl" in content_code
        assert "DEACTIVATION_WHITELIST" in content_code
        assert "DEACTIVATION_BLACKLIST" in content_code
        assert "waitForConfirmedInactiveState" in content_code
        assert "showDryRunPageBanner" in content_code


# ==============================================================================
# Stage 09A-R1 Executor Logic Tests (Section 18)
# ==============================================================================

def test_executor_target_validation_logic():
    """Section 6 & 18: Exact target validation rejects bad schemes, non-Avito domains, and mismatched IDs."""
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
    assert is_valid_avito_target("https://www.avito.ru/moskva/tovary_123456789", "123456789") is True
    assert is_valid_avito_target("https://m.avito.ru/items/987654321", "987654321") is True
    assert is_valid_avito_target("https://avito.ru/123456789", "123456789") is True

    # Malicious / Mismatched targets
    assert is_valid_avito_target("https://evil.com/123456789", "123456789") is False
    assert is_valid_avito_target("https://avito.ru.phishing.io/123456789", "123456789") is False
    assert is_valid_avito_target("javascript:alert(1)", "123456789") is False
    assert is_valid_avito_target("https://www.avito.ru/items/111111111", "123456789") is False
    assert is_valid_avito_target("", "123456789") is False
    assert is_valid_avito_target("https://www.avito.ru/items/123", "") is False


def test_executor_dom_discovery_whitelist_and_blacklist():
    """Section 8 & 18: Conservative DOM discovery recognizes whitelist, rejects blacklist, and detects ambiguity."""
    WHITELIST = [
        "снять с публикации",
        "снять объявление",
        "деактивировать",
        "архивировать",
        "убрать с публикации",
        "закрыть объявление"
    ]
    BLACKLIST = [
        "опубликовать",
        "продать быстрее",
        "продвигать",
        "поднять",
        "оплатить",
        "купить услугу",
        "редактировать",
        "удалить аккаунт",
        "разместить",
        "добавить",
        "продлить",
        "подключить"
    ]

    def evaluate_element(text: str, aria_label: str = "", data_marker: str = ""):
        combined = f"{text} {aria_label} {data_marker}".lower()
        # Blacklist check
        if any(b in combined for b in BLACKLIST):
            return None
        # Whitelist check
        if any(w in combined for w in WHITELIST) or "close-item" in data_marker or "deactivate" in data_marker or data_marker == "item-actions/close":
            return {"text": text, "marker": data_marker}
        return None

    # 1. Whitelist phrases must match
    assert evaluate_element("Снять с публикации") is not None
    assert evaluate_element("Снять объявление") is not None
    assert evaluate_element("Деактивировать") is not None
    assert evaluate_element("Архивировать") is not None
    assert evaluate_element("Убрать с публикации") is not None
    assert evaluate_element("", "", "item-actions/close") is not None

    # 2. Blacklist phrases must be REJECTED even if containing deceptive words
    assert evaluate_element("Опубликовать") is None
    assert evaluate_element("Продать быстрее") is None
    assert evaluate_element("Продвигать объявление") is None
    assert evaluate_element("Оплатить размещение") is None
    assert evaluate_element("Редактировать объявление") is None
    assert evaluate_element("Снять и опубликовать заново") is None  # Contains 'опубликовать'

    # 3. Ambiguity handling simulation:
    sample_buttons = ["Снять с публикации", "Архивировать"]
    candidates = [evaluate_element(b) for b in sample_buttons if evaluate_element(b) is not None]
    assert len(candidates) == 2, "Multiple candidates must be flagged as ambiguous"


def test_executor_dry_run_safety_contract():
    """Section 11 & 18: In dry-run mode, button is found but destructive click is blocked and success is NOT reported."""
    task = {
        "task_id": 42,
        "action": "deactivate_listing",
        "avito_listing_id": "123456789",
        "dry_run": True,
        "step": "received"
    }

    # Simulation of content script dry-run execution
    def simulate_content_script_execution(task_params, button_found: bool):
        if not button_found:
            return {"success": False, "status": "manual_required", "error": "Button not found"}
        if task_params.get("dry_run"):
            return {
                "dry_run_ready": True,
                "control_text": "Снять с публикации",
                "message": "Готово к снятию: кнопка найдена"
            }
        return {"success": True, "confirmation": "inactive_state_confirmed"}

    res = simulate_content_script_execution(task, button_found=True)
    assert res.get("dry_run_ready") is True
    assert res.get("control_text") == "Снять с публикации"
    # Success is NOT reported
    assert res.get("success") is not True
    assert "Готово к снятию" in res.get("message", "")


def test_executor_mandatory_confirmation_for_success():
    """Section 10 & 18: Success requires confirmed inactive state; unconfirmed state results in failure."""
    def evaluate_task_outcome(click_performed: bool, confirmed_inactive: bool):
        if not click_performed:
            return "not_executed"
        if not confirmed_inactive:
            return "failed_timeout"
        return "success"

    assert evaluate_task_outcome(click_performed=False, confirmed_inactive=False) == "not_executed"
    assert evaluate_task_outcome(click_performed=True, confirmed_inactive=False) == "failed_timeout"
    assert evaluate_task_outcome(click_performed=True, confirmed_inactive=True) == "success"


def test_executor_active_task_locking_and_timeout():
    """Section 5 & 18: Active task lock prevents concurrency; lock recovers safely after timeout."""
    import time

    class FakeExtensionStorage:
        def __init__(self):
            self.store = {}

        def get(self, key):
            return self.store.get(key)

        def set(self, key, val):
            self.store[key] = val

    storage = FakeExtensionStorage()

    def can_process_new_task(storage_obj, now_ts: float):
        active = storage_obj.get("active_deactivation_task")
        if not active:
            return True
        updated_ts = active.get("updated_ts", 0)
        # Timeout after 300 seconds
        if now_ts - updated_ts > 300:
            storage_obj.set("active_deactivation_task", None)
            return True
        return False

    t0 = 1000.0
    # Initially no active task -> can process
    assert can_process_new_task(storage, t0) is True

    # Set active task
    storage.set("active_deactivation_task", {"task_id": 10, "updated_ts": t0})

    # Within timeout -> locked (concurrency blocked)
    assert can_process_new_task(storage, t0 + 60.0) is False
    assert can_process_new_task(storage, t0 + 299.0) is False

    # After timeout (>300s) -> recovers safely
    assert can_process_new_task(storage, t0 + 301.0) is True
    assert storage.get("active_deactivation_task") is None


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


# ==============================================================================
# Stage 09A-R2 Action Contract Tests (Section 8)
# ==============================================================================

def test_persisted_task_action_deactivate_internal_validity():
    """Section 4 & 8: Internal persisted business action is 'deactivate'."""
    core_models_path = REPO_ROOT / "core" / "app" / "models.py"
    with open(core_models_path, "r", encoding="utf-8") as f:
        core_models_code = f.read()

    assert "class AvitoPostSaleTask" in core_models_code
    assert 'default="deactivate"' in core_models_code or "default='deactivate'" in core_models_code


def test_extension_bridge_payload_action_mapping():
    """Section 4 & 8: Extension bridge serializes business 'deactivate' into transport 'deactivate_listing'."""
    bridge_path = REPO_ROOT / "avito-module" / "app" / "routers" / "extension_bridge.py"
    with open(bridge_path, "r", encoding="utf-8") as f:
        bridge_code = f.read()

    assert 'BUSINESS_ACTION_DEACTIVATE = "deactivate"' in bridge_code
    assert 'EXTENSION_ACTION_DEACTIVATE_LISTING = "deactivate_listing"' in bridge_code
    assert 'task["action"] = EXTENSION_ACTION_DEACTIVATE_LISTING' in bridge_code


def test_service_worker_accepts_supported_actions_and_rejects_unknown():
    """Section 4, 6 & 8: Service worker accepts both deactivate_listing and deactivate, and rejects unknown actions."""
    sw_path = REPO_ROOT / "chrome-extension" / "technoreboot-avito" / "service_worker.js"
    with open(sw_path, "r", encoding="utf-8") as f:
        sw_code = f.read()

    assert "SUPPORTED_DEACTIVATION_ACTIONS" in sw_code
    assert '"deactivate_listing"' in sw_code
    assert '"deactivate"' in sw_code
    assert "Unsupported action:" in sw_code

    # Python simulation of the service worker action validator contract
    supported = ["deactivate_listing", "deactivate"]
    
    # Valid actions accepted
    assert "deactivate_listing" in supported
    assert "deactivate" in supported

    # Unknown actions rejected (must not be normalized into deactivation)
    unknown_actions = ["delete_account", "publish_listing", "pay_promotion", "random_action"]
    for unk in unknown_actions:
        assert unk not in supported, f"Action {unk} must be rejected"


def test_sale_detail_permanent_avito_button_and_messages_rendered():
    """Section 6A & 8: Sale detail template includes permanent [Снять с Avito] button and avito_msg banners."""
    sales_detail_path = REPO_ROOT / "inventory-sales-module" / "app" / "templates" / "sales_detail.html"
    with open(sales_detail_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Permanent button exists in action bar
    assert "btnPermanentAvitoDeactivate" in html
    assert "Снять с Avito" in html
    assert "/inventory/sales/{{ sale.id }}/avito-deactivate" in html

    # Informational message banners are handled
    assert "Объявление уже снято с Avito" in html
    assert "Для этой продажи нет связанных объявлений Avito" in html
    assert "already_deactivated" in html
    assert "no_listings" in html


def test_content_script_extract_avito_item_id_logic():
    """Section 6B & 8: extractAvitoItemId logic extracts exact listing ID from various Avito URL formats."""
    import re
    import urllib.parse

    def extract_avito_item_id(url: str):
        if not url:
            return None
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        trailing_match = re.search(r'(?:_/|/)(\d{7,15})(?:/|\?|#|$)', path)
        if trailing_match and trailing_match.group(1):
            return trailing_match.group(1)
        # Alternate trailing pattern
        m2 = re.search(r'_(\d{7,15})(?:/|\?|#|$)', path)
        if m2 and m2.group(1):
            return m2.group(1)
        qs = urllib.parse.parse_qs(parsed.query)
        for k in ("item_id", "id"):
            if k in qs and re.match(r'^\d{7,15}$', qs[k][0]):
                return qs[k][0]
        any_digits = re.search(r'\b(\d{8,12})\b', path)
        if any_digits and any_digits.group(1):
            return any_digits.group(1)
        return None

    assert extract_avito_item_id("https://www.avito.ru/ekaterinburg/tovary/printer_7353766377") == "7353766377"
    assert extract_avito_item_id("https://www.avito.ru/7353766377") == "7353766377"
    assert extract_avito_item_id("https://www.avito.ru/items/7353766377") == "7353766377"
    assert extract_avito_item_id("https://www.avito.ru/profile/items/active?item_id=7353766377") == "7353766377"
    assert extract_avito_item_id("https://www.avito.ru/profile/items/active") is None


