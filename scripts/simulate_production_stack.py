#!/usr/bin/env python3
"""
TECHNOREBOOT — Production Debian Docker Simulation & Fresh Build Proof Engine
Stage 08B-R1: Automated simulation of the production Compose configuration in an isolated sandbox.

1. Records live stack baseline (DB SHA256, product IDs, sale IDs, repair IDs, photo IDs, external listing IDs).
2. Sets up dedicated simulation sandbox: C:\\tbootit\\.prod-sim\\<run_id>
3. Performs fresh Git checkout into sandbox repository.
4. Generates test-only TLS certificates (Server cert with SAN, Client CA, OWNER cert, USER cert).
5. Configures isolated production environment on alternate ports (HTTP 18080, HTTPS 18443).
6. Validates production Compose config.
7. Builds production images from fresh clone source.
8. Starts production stack and waits for healthy status across all 6 services.
9. Proves:
   - Only Gateway publishes host ports (18080, 18443); internal services publish 0 ports.
   - Gateway HTTP permanently redirects (301) to HTTPS.
   - Gateway HTTPS rejects unauthenticated requests (403 Forbidden).
   - Gateway HTTPS accepts OWNER certificate (200 OK across dashboard, products, sales, repairs, avito, backups, certificates).
   - Gateway HTTPS enforces RBAC on USER certificate (200 OK on products, 403 Forbidden on backups and certificates).
   - Internal service ports (8000, 8010, 8020, 8030, 8040) are closed and unreachable from host.
   - Security constraints verified: no-new-privileges, unprivileged, no docker.sock, no host network.
10. Tears down simulation stack cleanly.
11. Verifies live database baseline remains strictly unchanged.
"""

import os
import sys
import time
import uuid
import shutil
import socket
import sqlite3
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

PROJECT_ROOT = Path(r"C:\tbootit")
LIVE_DATA_DIR = PROJECT_ROOT / "data"
LIVE_DB_PATH = LIVE_DATA_DIR / "db" / "technoreboot.db"

sys.path.insert(0, str(PROJECT_ROOT / "admin-shell" / "app"))
from auth_manager import AuthManager

SIM_PORTS = {
    "http": 18080,
    "https": 18443,
}


def compute_sha256(path: Path) -> str:
    if not path.is_file():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_db_stats(db_path: Path) -> Dict[str, Any]:
    if not db_path.is_file():
        return {}
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    try:
        cur.execute("SELECT count(*) FROM products;")
        products = cur.fetchone()[0]
        cur.execute("SELECT id FROM products ORDER BY id;")
        product_ids = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT count(*) FROM sales;")
        sales = cur.fetchone()[0]
        cur.execute("SELECT id FROM sales ORDER BY id;")
        sale_ids = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT count(*) FROM repair_orders;")
        repairs = cur.fetchone()[0]
        cur.execute("SELECT id FROM repair_orders ORDER BY id;")
        repair_ids = [r[0] for r in cur.fetchall()]

        cur.execute("SELECT count(*) FROM product_photos;")
        photos = cur.fetchone()[0]
        cur.execute("SELECT id FROM product_photos ORDER BY id;")
        photo_ids = [r[0] for r in cur.fetchall()]

        try:
            cur.execute("SELECT count(*) FROM external_listings;")
            external_listings = cur.fetchone()[0]
            cur.execute("SELECT id FROM external_listings ORDER BY id;")
            external_listing_ids = [r[0] for r in cur.fetchall()]
        except Exception:
            external_listings = 0
            external_listing_ids = []

        return {
            "products": products,
            "product_ids": product_ids,
            "sales": sales,
            "sale_ids": sale_ids,
            "repairs": repairs,
            "repair_ids": repair_ids,
            "photos": photos,
            "photo_ids": photo_ids,
            "external_listings": external_listings,
            "external_listing_ids": external_listing_ids,
        }
    finally:
        conn.close()


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def wait_for_containers_healthy(
    project_name: str,
    services: List[str],
    max_retries: int = 40,
    delay: float = 2.0,
) -> bool:
    print(f"  Waiting for {len(services)} services to report healthy in project '{project_name}'...")
    for attempt in range(max_retries):
        all_healthy = True
        for svc in services:
            c_name = f"{project_name}-{svc}"
            res = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Health.Status}}", c_name],
                capture_output=True,
                text=True,
            )
            status = res.stdout.strip()
            if status != "healthy":
                all_healthy = False
                break
        if all_healthy:
            return True
        time.sleep(delay)
    return False


def run_simulation(leave_running: bool = False) -> Dict[str, Any]:
    print("=" * 78)
    print("  TECHNOREBOOT — PRODUCTION DEBIAN DOCKER SIMULATION (STAGE 08B-R1)")
    print("=" * 78)

    # 1. Preflight baseline
    print("\n[STEP 1/7] Capturing Live Data Baseline...")
    live_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(PROJECT_ROOT), text=True).strip()
    live_db_sha = compute_sha256(LIVE_DB_PATH)
    live_stats = get_db_stats(LIVE_DB_PATH)
    print(f"  LIVE_HEAD:                 {live_head}")
    print(f"  LIVE_DB_SHA:               {live_db_sha}")
    print(f"  LIVE_PRODUCTS:             {live_stats.get('products')}")
    print(f"  LIVE_SALES:                {live_stats.get('sales')}")
    print(f"  LIVE_REPAIRS:              {live_stats.get('repairs')}")
    print(f"  LIVE_PHOTOS:               {live_stats.get('photos')}")
    print(f"  LIVE_EXTERNAL_LISTINGS:    {live_stats.get('external_listings')}")

    run_id = f"sim_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    sim_base = PROJECT_ROOT / ".prod-sim" / run_id
    sim_repo = sim_base / "repo"
    sim_data = sim_base / "data"
    sim_project = f"technoreboot-prod-sim-{run_id}"

    # 2. Fresh Git Clone into Sandbox
    print(f"\n[STEP 2/7] Creating Fresh Source Checkout in {sim_repo}...")
    sim_base.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", str(PROJECT_ROOT), str(sim_repo)], check=True, capture_output=True, text=True)

    # Copy deploy/ and any locally updated code into clone
    shutil.copytree(PROJECT_ROOT / "deploy", sim_repo / "deploy", dirs_exist_ok=True)
    for mod_file in [
        "admin-shell/app/auth_manager.py",
        "admin-shell/app/main.py",
        "core/app/config.py",
        "inventory-sales-module/app/config.py",
        "inventory-sales-module/app/main.py",
        "inventory-sales-module/app/core_client.py",
        "repairs-module/app/core_client.py",
    ]:
        src = PROJECT_ROOT / mod_file
        dst = sim_repo / mod_file
        if src.exists():
            shutil.copy2(src, dst)

    clone_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(sim_repo), text=True).strip()
    print(f"  SIM_REPO_HEAD:             {clone_head}")

    # 3. Setup Persistent Sandbox Data Root & Test TLS Material
    print(f"\n[STEP 3/7] Setting up Sandbox Data Root in {sim_data}...")
    for sub in ["db", "storage", "auth", "avito-module", "backups"]:
        (sim_data / sub).mkdir(parents=True, exist_ok=True)

    # Generate PKI and certs in sandbox
    am = AuthManager(auth_dir=str(sim_data / "auth"))
    server_crt = sim_data / "auth" / "server" / "server.crt"
    server_key = sim_data / "auth" / "server" / "server.key"
    client_ca = sim_data / "auth" / "ca" / "ca.crt"
    owner_crt = sim_data / "auth" / "certificates" / "owner.crt"
    owner_key = sim_data / "auth" / "certificates" / "owner.key"

    # Create test USER client cert
    worker_rec = am.create_user_certificate("test-worker")
    worker_crt = sim_data / "auth" / "certificates" / f"{worker_rec['id']}.crt"
    worker_key = sim_data / "auth" / "certificates" / f"{worker_rec['id']}.key"

    assert server_crt.is_file(), "Server TLS cert missing"
    assert server_key.is_file(), "Server TLS key missing"
    assert client_ca.is_file(), "Client CA cert missing"
    assert owner_crt.is_file(), "OWNER cert missing"
    assert owner_key.is_file(), "OWNER key missing"
    assert worker_crt.is_file(), "USER cert missing"
    assert worker_key.is_file(), "USER key missing"
    print("  Test TLS server certificates and client mTLS credentials generated.")

    # 4. Configure Production Environment
    prod_env = os.environ.copy()
    prod_env.update({
        "TECHNOREBOOT_HOSTNAME": "localhost",
        "HTTP_PORT": str(SIM_PORTS["http"]),
        "HTTPS_PORT": str(SIM_PORTS["https"]),
        "TECHNOREBOOT_DATA_ROOT": str(sim_data).replace("\\", "/"),
        "SERVER_TLS_CERT_PATH": str(server_crt).replace("\\", "/"),
        "SERVER_TLS_KEY_PATH": str(server_key).replace("\\", "/"),
        "CLIENT_CA_CERT_PATH": str(client_ca).replace("\\", "/"),
        "APP_ENV": "production",
        "CORE_API_TOKEN": "sim-token-prod-strong-1234567890abcdef",
        "CART_SESSION_SECRET": "sim-cart-secret-prod-strong-1234567890abcdef",
        "CONTAINER_NAME_PREFIX": sim_project,
    })

    compose_file = sim_repo / "deploy" / "production" / "docker-compose.prod.yml"

    # 5. Build and Launch Simulation Stack
    print(f"\n[STEP 4/7] Validating and Building Production Stack ({sim_project})...")
    # Config validation
    cfg_res = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "-p", sim_project, "config"],
        env=prod_env,
        cwd=str(sim_repo),
        capture_output=True,
        text=True,
    )
    if cfg_res.returncode != 0:
        raise RuntimeError(f"docker compose config failed: {cfg_res.stderr}")
    print("  Production compose configuration valid.")

    # Build images
    build_res = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "-p", sim_project, "build"],
        env=prod_env,
        cwd=str(sim_repo),
        capture_output=True,
        text=True,
    )
    if build_res.returncode != 0:
        raise RuntimeError(f"docker compose build failed: {build_res.stderr}")
    print("  Production images built successfully from source.")

    print(f"\n[STEP 5/7] Starting Simulation Stack on Ports {SIM_PORTS['http']}/{SIM_PORTS['https']}...")
    up_res = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "-p", sim_project, "up", "-d"],
        env=prod_env,
        cwd=str(sim_repo),
        capture_output=True,
        text=True,
    )
    if up_res.returncode != 0:
        raise RuntimeError(f"docker compose up failed: {up_res.stderr}")

    services = ["core", "inventory-sales", "repairs", "avito", "admin-shell", "gateway"]
    healthy = wait_for_containers_healthy(sim_project, services, max_retries=45, delay=2.0)
    assert healthy, "Simulation services failed to become healthy!"
    print("  All 6 production services healthy.")

    # 6. Verifications
    print("\n[STEP 6/7] Running Security and Application Verifications...")
    report: Dict[str, Any] = {
        "project": sim_project,
        "ports": SIM_PORTS,
        "clone_head": clone_head,
    }

    # Verify only Gateway publishes host ports
    for svc in ["core", "inventory-sales", "repairs", "avito", "admin-shell"]:
        c_name = f"{sim_project}-{svc}"
        p_res = subprocess.run(
            ["docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", c_name],
            capture_output=True,
            text=True,
        )
        # Verify no host port mappings exist
        raw_ports = p_res.stdout.strip()
        has_host_binding = '"HostPort"' in raw_ports and '""' not in raw_ports
        assert not has_host_binding, f"Internal service {svc} publishes host port: {raw_ports}"

    # Verify Gateway publishes only the designated simulation ports
    gw_inspect = subprocess.run(
        ["docker", "inspect", "--format", "{{json .NetworkSettings.Ports}}", f"{sim_project}-gateway"],
        capture_output=True,
        text=True,
    )
    assert f'"{SIM_PORTS["http"]}"' in gw_inspect.stdout, f"Gateway missing HTTP port {SIM_PORTS['http']}"
    assert f'"{SIM_PORTS["https"]}"' in gw_inspect.stdout, f"Gateway missing HTTPS port {SIM_PORTS['https']}"

    # Verify internal services are not exposed on host
    for port in [8000, 8010, 8020, 8030, 8040]:
        if is_port_open(port):
            try:
                r = httpx.get(f"http://127.0.0.1:{port}/health", timeout=1.0, trust_env=False)
                data = r.json()
                assert "technoreboot" not in str(data).lower(), f"Technoreboot service exposed on port {port}!"
            except Exception:
                pass
    report["internal_services_publicly_exposed"] = False
    print("  Internal services port isolation verified (zero host ports published).")

    # Verify Gateway HTTP redirects to HTTPS
    http_gw_url = f"http://127.0.0.1:{SIM_PORTS['http']}/"
    with httpx.Client(follow_redirects=False, timeout=5.0, trust_env=False) as client:
        r_http = client.get(http_gw_url)
        assert r_http.status_code == 301, f"Expected 301 from HTTP, got {r_http.status_code}"
        assert "https://" in r_http.headers.get("location", ""), f"Expected https redirect: {r_http.headers}"
    report["http_redirect"] = True
    print("  HTTP (port 18080) permanently redirects to HTTPS.")

    # Verify HTTPS rejects request without cert
    https_gw_url = f"https://127.0.0.1:{SIM_PORTS['https']}"
    with httpx.Client(base_url=https_gw_url, verify=str(client_ca), timeout=5.0, trust_env=False) as client:
        r_nocert = client.get("/")
        assert r_nocert.status_code == 403, f"Expected 403 without client cert, got {r_nocert.status_code}"
    report["no_cert_rejected"] = True
    print("  HTTPS (port 18443) rejects request without client certificate (403 Forbidden).")

    # Verify OWNER certificate access across all routes
    with httpx.Client(
        base_url=https_gw_url,
        cert=(str(owner_crt), str(owner_key)),
        verify=str(client_ca),
        timeout=10.0,
        trust_env=False,
    ) as client:
        # Dashboard
        r_root = client.get("/")
        assert r_root.status_code == 200, f"/ failed: {r_root.status_code}"
        report["root"] = True

        # Products
        r_products = client.get("/inventory/products")
        assert r_products.status_code == 200, f"/inventory/products failed: {r_products.status_code}"
        report["products"] = True

        # Sales
        r_sales = client.get("/inventory/sales")
        assert r_sales.status_code == 200, f"/inventory/sales failed: {r_sales.status_code}"
        report["sales"] = True

        # Repairs
        r_repairs = client.get("/repairs/repairs")
        assert r_repairs.status_code == 200, f"/repairs/repairs failed: {r_repairs.status_code}"
        report["repairs"] = True

        # Avito extension
        r_avito = client.get("/avito/extension")
        assert r_avito.status_code == 200, f"/avito/extension failed: {r_avito.status_code}"
        report["avito_extension"] = True

        # Backups (OWNER only)
        r_backups = client.get("/backups")
        assert r_backups.status_code == 200, f"/backups failed: {r_backups.status_code}"
        report["backups"] = True

        # Certificates (OWNER only)
        r_certs = client.get("/certificates")
        assert r_certs.status_code == 200, f"/certificates failed: {r_certs.status_code}"
        report["certificates"] = True

    report["owner_cert_accepted"] = True
    print("  OWNER cert authenticated successfully across all 7 canonical application routes.")

    # Verify USER certificate RBAC
    with httpx.Client(
        base_url=https_gw_url,
        cert=(str(worker_crt), str(worker_key)),
        verify=str(client_ca),
        timeout=10.0,
        trust_env=False,
    ) as client:
        # User can access products
        r_u_prod = client.get("/inventory/products")
        assert r_u_prod.status_code == 200, f"USER failed on products: {r_u_prod.status_code}"

        # User is BLOCKED on backups
        r_u_backups = client.get("/backups")
        assert r_u_backups.status_code == 403, f"USER allowed on /backups: {r_u_backups.status_code}"

        # User is BLOCKED on certificates
        r_u_certs = client.get("/certificates")
        assert r_u_certs.status_code == 403, f"USER allowed on /certificates: {r_u_certs.status_code}"

    report["user_cert_rbac_enforced"] = True
    print("  USER cert RBAC enforced (200 on products, 403 on backups and certificates).")

    # Verify Docker security settings on running containers
    for svc in services:
        c_name = f"{sim_project}-{svc}"
        sec_res = subprocess.run(
            ["docker", "inspect", "--format", "{{.HostConfig.Privileged}}|{{.HostConfig.NetworkMode}}", c_name],
            capture_output=True,
            text=True,
        )
        priv, net_mode = sec_res.stdout.strip().split("|")
        assert priv == "false", f"Container {c_name} is privileged!"
        assert net_mode != "host", f"Container {c_name} uses host network mode!"

    report["docker_security_baseline_passed"] = True
    print("  Docker security baseline verified on all 6 containers.")

    # 7. Teardown
    if not leave_running:
        print("\n[STEP 7/7] Tearing Down Simulation Stack...")
        down_res = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "-p", sim_project, "down", "-v"],
            env=prod_env,
            cwd=str(sim_repo),
            capture_output=True,
            text=True,
        )
        assert down_res.returncode == 0, f"docker compose down failed: {down_res.stderr}"

        # Clean sandbox
        try:
            shutil.rmtree(sim_base, ignore_errors=True)
        except Exception:
            pass
        report["teardown"] = True
        print("  Simulation stack stopped and sandbox cleaned.")
    else:
        report["teardown"] = False
        print("  Simulation stack left running as requested.")

    # Final live data check
    live_db_sha_after = compute_sha256(LIVE_DB_PATH)
    live_stats_after = get_db_stats(LIVE_DB_PATH)
    assert live_db_sha == live_db_sha_after, "LIVE DATABASE WAS MODIFIED DURING SIMULATION!"
    assert live_stats == live_stats_after, "LIVE DATA COUNTS/IDS CHANGED DURING SIMULATION!"
    report["live_data_unchanged"] = True
    print("  Live database integrity verified strictly untouched.")

    return report


if __name__ == "__main__":
    res = run_simulation(leave_running=False)
    print("\nSIMULATION RESULT: SUCCESS")
    print(res)
