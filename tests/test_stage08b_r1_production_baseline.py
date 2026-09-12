"""
Stage 08B-R1: Automated Test Suite for Production Debian Docker Configuration and Security Baseline
Covers Tests A through X:
- Test A: production Compose parses successfully.
- Test B: only Gateway publishes host ports.
- Test C: internal services have zero production published ports.
- Test D: production hostname is configurable.
- Test E: no localhost/127.0.0.1 production dependency.
- Test F: HTTP redirects to HTTPS.
- Test G: mTLS remains required.
- Test H: OWNER-like cert accepted.
- Test I: no-cert rejected.
- Test J: /backups remains OWNER-only.
- Test K: /certificates remains OWNER-only.
- Test L: no insecure production secret defaults.
- Test M: no secrets committed.
- Test N: DB persists under configurable production data root.
- Test O: storage persists.
- Test P: auth persists.
- Test Q: Avito mutable state persists.
- Test R: backups persist.
- Test S: restart policies set.
- Test T: health checks defined.
- Test U: bounded Docker log rotation configured.
- Test V: no privileged containers.
- Test W: no Docker socket mount.
- Test X: no host networking.
"""

import os
import sys
import yaml
import pytest
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(r"C:\tbootit")
DEPLOY_PROD_DIR = PROJECT_ROOT / "deploy" / "production"
COMPOSE_PROD_FILE = DEPLOY_PROD_DIR / "docker-compose.prod.yml"
NGINX_TEMPLATE_FILE = DEPLOY_PROD_DIR / "nginx" / "nginx.conf.template"
ENV_EXAMPLE_FILE = DEPLOY_PROD_DIR / "env.production.example"

sys.path.insert(0, str(PROJECT_ROOT / "admin-shell" / "app"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "inventory-sales-module"))


@pytest.fixture(scope="module")
def parsed_compose_raw():
    """Loads raw YAML of docker-compose.prod.yml."""
    assert COMPOSE_PROD_FILE.is_file(), f"Missing {COMPOSE_PROD_FILE}"
    with open(COMPOSE_PROD_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def parsed_compose_interpolated(tmp_path_factory):
    """Parses docker-compose.prod.yml using `docker compose config` with mock env."""
    env = os.environ.copy()
    env.update({
        "TECHNOREBOOT_HOSTNAME": "prod.example.com",
        "HTTP_PORT": "80",
        "HTTPS_PORT": "443",
        "TECHNOREBOOT_DATA_ROOT": "/srv/technoreboot/data",
        "SERVER_TLS_CERT_PATH": "/srv/technoreboot/certs/server.crt",
        "SERVER_TLS_KEY_PATH": "/srv/technoreboot/certs/server.key",
        "CLIENT_CA_CERT_PATH": "/srv/technoreboot/data/auth/ca/ca.crt",
        "APP_ENV": "production",
        "CORE_API_TOKEN": "mock-strong-token-1234567890abcdef",
        "CART_SESSION_SECRET": "mock-strong-cart-secret-1234567890abcdef",
    })
    res = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_PROD_FILE), "config"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"docker compose config failed: {res.stderr}"
    return yaml.safe_load(res.stdout)


# ==============================================================================
# TESTS A - E: COMPOSE PARSING, PORTS, HOSTNAME ISOLATION
# ==============================================================================

def test_a_production_compose_parses_successfully(parsed_compose_raw, parsed_compose_interpolated):
    """TEST A: Production Compose parses successfully and defines all 6 canonical services."""
    expected_services = {
        "core",
        "admin-shell",
        "inventory-sales-module",
        "repairs-module",
        "avito-module",
        "gateway",
    }
    raw_services = set(parsed_compose_raw.get("services", {}).keys())
    assert raw_services == expected_services, f"Mismatch in raw services: {raw_services}"

    interpolated_services = set(parsed_compose_interpolated.get("services", {}).keys())
    assert interpolated_services == expected_services, f"Mismatch in interpolated services: {interpolated_services}"


def test_b_only_gateway_publishes_host_ports(parsed_compose_raw, parsed_compose_interpolated):
    """TEST B: Only the Gateway service publishes host ports (80 and 443)."""
    services_with_ports = []
    for svc_name, svc_cfg in parsed_compose_raw.get("services", {}).items():
        if svc_cfg.get("ports"):
            services_with_ports.append(svc_name)
    assert services_with_ports == ["gateway"], f"Expected only gateway to define ports, got: {services_with_ports}"

    # Also check interpolated
    gw_ports = parsed_compose_interpolated["services"]["gateway"].get("ports", [])
    assert len(gw_ports) == 2, f"Expected exactly 2 published ports on gateway, got: {gw_ports}"
    published_ports = {str(p.get("published")) for p in gw_ports}
    assert published_ports == {"80", "443"}, f"Expected published ports 80 and 443, got: {published_ports}"


def test_c_internal_services_zero_published_ports(parsed_compose_raw, parsed_compose_interpolated):
    """TEST C: Internal services (core, admin-shell, inventory, repairs, avito) have ZERO published ports."""
    internal_services = [
        "core",
        "admin-shell",
        "inventory-sales-module",
        "repairs-module",
        "avito-module",
    ]
    for svc in internal_services:
        raw_ports = parsed_compose_raw["services"][svc].get("ports")
        assert not raw_ports, f"Internal service '{svc}' must have no raw ports, found: {raw_ports}"

        interp_ports = parsed_compose_interpolated["services"][svc].get("ports")
        assert not interp_ports, f"Internal service '{svc}' must have no interpolated ports, found: {interp_ports}"


def test_d_production_hostname_configurable():
    """TEST D: Production hostname is configurable via TECHNOREBOOT_HOSTNAME and fails if unset."""
    env = os.environ.copy()
    env.update({
        "HTTP_PORT": "80",
        "HTTPS_PORT": "443",
        "TECHNOREBOOT_DATA_ROOT": "/srv/technoreboot/data",
        "SERVER_TLS_CERT_PATH": "/srv/technoreboot/certs/server.crt",
        "SERVER_TLS_KEY_PATH": "/srv/technoreboot/certs/server.key",
        "CLIENT_CA_CERT_PATH": "/srv/technoreboot/data/auth/ca/ca.crt",
        "APP_ENV": "production",
        "CORE_API_TOKEN": "mock-strong-token-1234567890abcdef",
        "CART_SESSION_SECRET": "mock-strong-cart-secret-1234567890abcdef",
    })
    # Remove TECHNOREBOOT_HOSTNAME
    env.pop("TECHNOREBOOT_HOSTNAME", None)

    res = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_PROD_FILE), "config"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode != 0, "Expected docker compose config to fail without TECHNOREBOOT_HOSTNAME"
    assert "TECHNOREBOOT_HOSTNAME is required" in res.stderr or "TECHNOREBOOT_HOSTNAME" in res.stderr


def test_e_no_localhost_dependency_in_production():
    """TEST E: No localhost or 127.0.0.1 hardcoded in production routing."""
    template_content = NGINX_TEMPLATE_FILE.read_text(encoding="utf-8")
    # server_name must use ${TECHNOREBOOT_HOSTNAME}
    assert "server_name ${TECHNOREBOOT_HOSTNAME};" in template_content
    assert "server_name localhost;" not in template_content
    assert "server_name 127.0.0.1;" not in template_content


# ==============================================================================
# TESTS F - K: HTTP REDIRECT, MTLS, AND RBAC POLICIES
# ==============================================================================

def test_f_http_redirects_to_https():
    """TEST F: HTTP permanently redirects to HTTPS (301) with no application content on port 80."""
    template_content = NGINX_TEMPLATE_FILE.read_text(encoding="utf-8")
    assert "listen 80;" in template_content
    assert "return 301 https://$host$request_uri;" in template_content
    assert "proxy_pass" not in template_content.split("listen 80;")[1].split("listen 443")[0]


def test_g_mtls_required():
    """TEST G: mTLS is configured with ssl_client_certificate and auth_request subrequest."""
    template_content = NGINX_TEMPLATE_FILE.read_text(encoding="utf-8")
    assert "ssl_client_certificate /etc/nginx/certs/ca/ca.crt;" in template_content
    assert "auth_request /internal-auth/verify;" in template_content
    assert "proxy_pass http://admin-shell:8010/internal-auth/verify;" in template_content


def _get_auth_manager():
    auth_mgr_dir = str(PROJECT_ROOT / "admin-shell" / "app")
    if auth_mgr_dir not in sys.path:
        sys.path.insert(0, auth_mgr_dir)
    from auth_manager import AuthManager
    return AuthManager


def test_h_owner_cert_accepted(tmp_path):
    """TEST H: OWNER-like certificate is accepted by auth_manager."""
    AuthManager = _get_auth_manager()
    am = AuthManager(auth_dir=str(tmp_path))
    registry = am._read_registry()
    owner_rec = next(r for r in registry if r.get("is_owner"))

    ok, code, msg, cert = am.verify_request(
        verify_status="SUCCESS",
        client_serial=owner_rec["serial_hex"],
        client_fingerprint=owner_rec["fingerprint_sha256"],
        request_uri="/inventory/products",
    )
    assert ok is True
    assert code == 200
    assert cert["is_owner"] is True


def test_i_no_cert_rejected(tmp_path):
    """TEST I: Request without client certificate is rejected with 403 Forbidden."""
    AuthManager = _get_auth_manager()
    am = AuthManager(auth_dir=str(tmp_path))

    # verify_status not SUCCESS (e.g. NONE or missing)
    ok, code, msg, cert = am.verify_request(
        verify_status="NONE",
        client_serial=None,
        client_fingerprint=None,
        request_uri="/inventory/products",
    )
    assert ok is False
    assert code == 403
    assert "No valid" in msg or "client certificate" in msg


def test_j_backups_owner_only(tmp_path):
    """TEST J: /backups route is strictly OWNER-only; USER cert receives 403."""
    AuthManager = _get_auth_manager()
    am = AuthManager(auth_dir=str(tmp_path))
    registry = am._read_registry()
    owner_rec = next(r for r in registry if r.get("is_owner"))

    # Create worker/USER certificate using create_user_certificate
    worker_rec = am.create_user_certificate("worker1")

    # 1. OWNER certificate allowed
    ok_owner, code_owner, _, _ = am.verify_request(
        verify_status="SUCCESS",
        client_serial=owner_rec["serial_hex"],
        client_fingerprint=owner_rec["fingerprint_sha256"],
        request_uri="/backups",
    )
    assert ok_owner is True
    assert code_owner == 200

    # 2. USER/worker certificate rejected with 403 Forbidden
    ok_user, code_user, msg_user, _ = am.verify_request(
        verify_status="SUCCESS",
        client_serial=worker_rec["serial_hex"],
        client_fingerprint=worker_rec["fingerprint_sha256"],
        request_uri="/backups",
    )
    assert ok_user is False
    assert code_user == 403
    assert "OWNER certificate required" in msg_user

    # Also test API route /admin-api/backups
    ok_user_api, code_user_api, _, _ = am.verify_request(
        verify_status="SUCCESS",
        client_serial=worker_rec["serial_hex"],
        client_fingerprint=worker_rec["fingerprint_sha256"],
        request_uri="/admin-api/backups",
    )
    assert ok_user_api is False
    assert code_user_api == 403


def test_k_certificates_owner_only(tmp_path):
    """TEST K: /certificates route is strictly OWNER-only; USER cert receives 403."""
    AuthManager = _get_auth_manager()
    am = AuthManager(auth_dir=str(tmp_path))
    registry = am._read_registry()
    owner_rec = next(r for r in registry if r.get("is_owner"))
    worker_rec = am.create_user_certificate("worker2")

    # USER cert accessing /certificates -> 403
    ok, code, msg, cert = am.verify_request(
        verify_status="SUCCESS",
        client_serial=worker_rec["serial_hex"],
        client_fingerprint=worker_rec["fingerprint_sha256"],
        request_uri="/certificates",
    )
    assert ok is False
    assert code == 403
    assert "OWNER" in msg and "required" in msg

    # OWNER cert accessing /certificates -> 200
    ok, code, msg, cert = am.verify_request(
        verify_status="SUCCESS",
        client_serial=owner_rec["serial_hex"],
        client_fingerprint=owner_rec["fingerprint_sha256"],
        request_uri="/certificates",
    )
    assert ok is True
    assert code == 200


# ==============================================================================
# TESTS L - M: SECRETS SAFETY AND FAIL-FAST VALIDATION
# ==============================================================================

def test_l_no_insecure_production_secret_defaults():
    """TEST L: Insecure/default secrets fail fast in production mode (APP_ENV=production)."""
    import importlib.util

    def load_class(file_path: Path, class_name: str, mod_name: str):
        spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, class_name)

    CoreSettings = load_class(PROJECT_ROOT / "core" / "app" / "config.py", "Settings", "core_cfg")
    InvSettings = load_class(PROJECT_ROOT / "inventory-sales-module" / "app" / "config.py", "Settings", "inv_cfg")

    insecure_tokens = ["dev-token", "change-me", "admin", "password", "123456", ""]
    for token in insecure_tokens:
        with pytest.raises(ValueError):
            CoreSettings(app_env="production", api_token=token)

    # Strong token succeeds
    cs = CoreSettings(app_env="production", api_token="a-very-strong-unique-production-token-12345")
    assert cs.api_token == "a-very-strong-unique-production-token-12345"

    insecure_cart_secrets = ["technoreboot_secret_cart_key_mvp", "dev-token", "change-me", "password", ""]
    for secret in insecure_cart_secrets:
        with pytest.raises(ValueError):
            InvSettings(app_env="production", cart_session_secret=secret)

    # Strong cart secret succeeds
    inv = InvSettings(app_env="production", cart_session_secret="a-very-strong-unique-cart-secret-12345")
    assert inv.cart_session_secret == "a-very-strong-unique-cart-secret-12345"


def test_m_no_secrets_committed():
    """TEST M: No real secrets committed in env.production.example or deploy directory."""
    example_text = ENV_EXAMPLE_FILE.read_text(encoding="utf-8")
    assert "CORE_API_TOKEN=" in example_text
    assert "CORE_API_TOKEN=dev-token" not in example_text
    assert "CART_SESSION_SECRET=" in example_text
    assert "CART_SESSION_SECRET=technoreboot_secret_cart_key_mvp" not in example_text

    # Verify .env is in .gitignore
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in gitignore

    # Verify no private keys in deploy/production/
    for p in DEPLOY_PROD_DIR.rglob("*"):
        if p.is_file():
            assert p.suffix != ".key", f"Private key found in deploy directory: {p}"
            assert p.suffix != ".p12", f"PKCS12 archive found in deploy directory: {p}"


# ==============================================================================
# TESTS N - R: DATA PERSISTENCE CONTRACT
# ==============================================================================

def test_n_db_persists_under_configurable_data_root(parsed_compose_raw):
    """TEST N: SQLite database persists under configurable ${TECHNOREBOOT_DATA_ROOT}/db."""
    core_vols = parsed_compose_raw["services"]["core"].get("volumes", [])
    db_vol = next((v for v in core_vols if "/data/db" in v), None)
    assert db_vol is not None, "Missing /data/db volume in core service"
    assert "${TECHNOREBOOT_DATA_ROOT" in db_vol
    assert "/db:/data/db" in db_vol


def test_o_storage_persists(parsed_compose_raw):
    """TEST O: Product photo storage persists under configurable ${TECHNOREBOOT_DATA_ROOT}/storage."""
    core_vols = parsed_compose_raw["services"]["core"].get("volumes", [])
    storage_vol = next((v for v in core_vols if "/data/storage" in v), None)
    assert storage_vol is not None, "Missing /data/storage volume in core service"
    assert "${TECHNOREBOOT_DATA_ROOT" in storage_vol
    assert "/storage:/data/storage" in storage_vol


def test_p_auth_persists(parsed_compose_raw):
    """TEST P: Auth certificates and PKI persist under configurable ${TECHNOREBOOT_DATA_ROOT}/auth."""
    admin_vols = parsed_compose_raw["services"]["admin-shell"].get("volumes", [])
    auth_vol = next((v for v in admin_vols if "/app/auth-data" in v), None)
    assert auth_vol is not None, "Missing /app/auth-data volume in admin-shell service"
    assert "${TECHNOREBOOT_DATA_ROOT" in auth_vol
    assert "/auth:/app/auth-data" in auth_vol


def test_q_avito_mutable_state_persists(parsed_compose_raw):
    """TEST Q: Avito mutable state persists under configurable ${TECHNOREBOOT_DATA_ROOT}/avito-module."""
    avito_vols = parsed_compose_raw["services"]["avito-module"].get("volumes", [])
    avito_vol = next((v for v in avito_vols if "/app/data" in v), None)
    assert avito_vol is not None, "Missing /app/data volume in avito-module service"
    assert "${TECHNOREBOOT_DATA_ROOT" in avito_vol
    assert "/avito-module:/app/data" in avito_vol


def test_r_backups_persist(parsed_compose_raw):
    """TEST R: Backups persist under configurable ${TECHNOREBOOT_DATA_ROOT}/backups."""
    core_vols = parsed_compose_raw["services"]["core"].get("volumes", [])
    backup_vol = next((v for v in core_vols if "/data/backups" in v), None)
    assert backup_vol is not None, "Missing /data/backups volume in core service"
    assert "${TECHNOREBOOT_DATA_ROOT" in backup_vol
    assert "/backups:/data/backups" in backup_vol


# ==============================================================================
# TESTS S - X: CONTAINER SECURITY BASELINE & POLICIES
# ==============================================================================

def test_s_restart_policies_set(parsed_compose_raw):
    """TEST S: Restart policy 'unless-stopped' is set across all services."""
    for svc_name, svc_cfg in parsed_compose_raw["services"].items():
        assert svc_cfg.get("restart") == "unless-stopped", f"Service {svc_name} missing restart: unless-stopped"


def test_t_healthchecks_defined(parsed_compose_raw):
    """TEST T: All 6 production services have explicit health checks defined."""
    for svc_name, svc_cfg in parsed_compose_raw["services"].items():
        assert "healthcheck" in svc_cfg, f"Service {svc_name} missing healthcheck"
        hc = svc_cfg["healthcheck"]
        assert "test" in hc, f"Service {svc_name} healthcheck missing test command"


def test_u_bounded_docker_log_rotation(parsed_compose_raw):
    """TEST U: Bounded Docker JSON log rotation (max-size 10m, max-file 5) on all services."""
    for svc_name, svc_cfg in parsed_compose_raw["services"].items():
        assert "logging" in svc_cfg, f"Service {svc_name} missing logging configuration"
        logging_cfg = svc_cfg["logging"]
        assert logging_cfg.get("driver") == "json-file", f"Service {svc_name} logging driver not json-file"
        options = logging_cfg.get("options", {})
        assert options.get("max-size") == "10m", f"Service {svc_name} max-size != 10m"
        assert options.get("max-file") == "5", f"Service {svc_name} max-file != 5"


def test_v_no_privileged_containers(parsed_compose_raw):
    """TEST V: No privileged containers; all services have no-new-privileges:true."""
    for svc_name, svc_cfg in parsed_compose_raw["services"].items():
        assert not svc_cfg.get("privileged", False), f"Service {svc_name} must not be privileged"
        sec_opt = svc_cfg.get("security_opt", [])
        assert "no-new-privileges:true" in sec_opt, f"Service {svc_name} missing no-new-privileges:true"


def test_w_no_docker_socket_mount(parsed_compose_raw):
    """TEST W: No service mounts the Docker socket (/var/run/docker.sock)."""
    for svc_name, svc_cfg in parsed_compose_raw["services"].items():
        vols = svc_cfg.get("volumes", [])
        for v in vols:
            assert "docker.sock" not in str(v), f"Service {svc_name} mounts docker.sock: {v}"


def test_x_no_host_networking(parsed_compose_raw):
    """TEST X: No service uses network_mode: host."""
    for svc_name, svc_cfg in parsed_compose_raw["services"].items():
        assert svc_cfg.get("network_mode") != "host", f"Service {svc_name} uses host network mode"
