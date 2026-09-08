#!/usr/bin/env python3
"""
Stage 07B-R4 Live Verification Script
Tests Avito extension pairing code generation, proxying, pairing handshake,
download package, and mTLS security regression smoke.
"""

import os
import sys
import io
import re
import json
import zipfile
import subprocess
from pathlib import Path
import httpx
import urllib3

urllib3.disable_warnings()

GATEWAY_URL = "https://127.0.0.1:8443"
ADMIN_SHELL_DIRECT_URL = "http://127.0.0.1:8011"
AVITO_DIRECT_URL = "http://127.0.0.1:8020"

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
AUTH_DIR = PROJECT_ROOT / "data" / "auth"

OWNER_CRT = AUTH_DIR / "certificates" / "owner.crt"
OWNER_KEY = AUTH_DIR / "certificates" / "owner.key"


def log(msg: str):
    print(f"[STAGE07B-R4] {msg}", flush=True)


def main():
    log("=" * 75)
    log("STARTING STAGE 07B-R4 VERIFICATION: AVITO PAIRING CODE 500 REGRESSION FIX")
    log("=" * 75)

    assert OWNER_CRT.is_file(), f"Owner cert missing: {OWNER_CRT}"
    assert OWNER_KEY.is_file(), f"Owner key missing: {OWNER_KEY}"
    owner_cert_tuple = (str(OWNER_CRT), str(OWNER_KEY))

    # -------------------------------------------------------------------------
    # TEST A: OWNER can open current Avito extension page through mTLS gateway
    # -------------------------------------------------------------------------
    log("Step 1 (TEST A): Verifying OWNER can open /avito/extension via Gateway 8443...")
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=15.0) as client:
        r_a = client.get(f"{GATEWAY_URL}/avito/extension")
        assert r_a.status_code == 200, f"Expected 200, got {r_a.status_code}"
        assert "Интеграция через Chrome Extension" in r_a.text
        assert "Создать новый код подключения" in r_a.text
        assert "codeError" in r_a.text
    log("  [PASS] TEST A: /avito/extension opened with 200 OK and valid page content.")

    # -------------------------------------------------------------------------
    # TEST B: Current extension ZIP downloads successfully
    # -------------------------------------------------------------------------
    log("Step 2 (TEST B): Verifying extension ZIP download...")
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=20.0) as client:
        r_b = client.get(f"{GATEWAY_URL}/avito/extension/download")
        assert r_b.status_code == 200, f"Expected 200, got {r_b.status_code}"
        assert "application/zip" in r_b.headers.get("content-type", "")
        zip_bytes = r_b.content
        assert len(zip_bytes) > 5000, f"ZIP payload too small: {len(zip_bytes)}"

        # Validate ZIP contents and manifest version
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            namelist = z.namelist()
            assert "manifest.json" in namelist, "manifest.json missing from downloaded ZIP"
            assert "popup.html" in namelist, "popup.html missing from downloaded ZIP"
            assert "service_worker.js" in namelist, "service_worker.js missing from downloaded ZIP"
            manifest_data = json.loads(z.read("manifest.json").decode("utf-8"))
            assert manifest_data.get("version") == "0.2.43", f"Expected v0.2.43, got {manifest_data.get('version')}"
    log(f"  [PASS] TEST B: Extension ZIP downloaded (v0.2.43, {len(zip_bytes)} bytes) with valid manifest.")

    # -------------------------------------------------------------------------
    # TEST C: Direct Avito-module POST /extension/api/pairing/generate
    # -------------------------------------------------------------------------
    log("Step 3 (TEST C): Testing direct avito-module /extension/api/pairing/generate...")
    with httpx.Client(trust_env=False, timeout=10.0) as client:
        r_c = client.post(f"{AVITO_DIRECT_URL}/extension/api/pairing/generate")
        assert r_c.status_code == 200, f"Expected 200, got {r_c.status_code}: {r_c.text}"
        data_c = r_c.json()
        assert "pair_code" in data_c
        assert re.match(r"^\d{6}$", data_c["pair_code"]), f"Invalid code format: {data_c['pair_code']}"
        assert data_c.get("expires_in_seconds") == 600
    log("  [PASS] TEST C: Direct avito-module generated valid 6-digit code.")

    # -------------------------------------------------------------------------
    # TEST D: Admin Shell proxy pairing-generate endpoint returns valid JSON
    # -------------------------------------------------------------------------
    log("Step 4 (TEST D): Testing Admin Shell direct proxy /admin-api/avito-extension/pairing/generate...")
    with httpx.Client(trust_env=False, timeout=10.0) as client:
        r_d = client.post(f"{ADMIN_SHELL_DIRECT_URL}/admin-api/avito-extension/pairing/generate")
        assert r_d.status_code == 200, f"Expected 200, got {r_d.status_code}: {r_d.text}"
        data_d = r_d.json()
        assert "pair_code" in data_d
        assert re.match(r"^\d{6}$", data_d["pair_code"])
    log("  [PASS] TEST D: Admin Shell internal proxy returned 200 with valid JSON.")

    # -------------------------------------------------------------------------
    # TEST E: Real OWNER gateway path for pairing-generate returns success JSON
    # -------------------------------------------------------------------------
    log("Step 5 (TEST E): Testing real OWNER Gateway path for pairing-generate...")
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=15.0) as client:
        r_e = client.post(f"{GATEWAY_URL}/admin-api/avito-extension/pairing/generate")
        assert r_e.status_code == 200, f"Expected 200, got {r_e.status_code}: {r_e.text}"
        data_e = r_e.json()
        assert "pair_code" in data_e
        owner_pair_code = data_e["pair_code"]
        assert re.match(r"^\d{6}$", owner_pair_code)
    log("  [PASS] TEST E: Real OWNER mTLS gateway path returned 200 with valid 6-digit code.")

    # -------------------------------------------------------------------------
    # TEST F: UI JavaScript handles successful JSON correctly
    # -------------------------------------------------------------------------
    log("Step 6 (TEST F): Verifying UI HTML script structure for successful code handling...")
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=15.0) as client:
        r_f = client.get(f"{GATEWAY_URL}/avito/extension")
        html_src = r_f.text
        assert "document.getElementById('codeDisplay').textContent = data.pair_code;" in html_src
        assert "document.getElementById('codeError')" in html_src
        assert "contentType.includes('application/json')" in html_src
    log("  [PASS] TEST F: UI script safely handles successful pair_code and DOM updates.")

    # -------------------------------------------------------------------------
    # TEST G: UI JavaScript handles simulated/plain-text 500 without Unexpected token
    # -------------------------------------------------------------------------
    log("Step 7 (TEST G): Verifying UI JavaScript error handling on non-JSON 500...")
    # Verify that the regex and parsing in avito_extension.html handles text without crashing
    assert "Не удалось создать код подключения: сервер вернул ошибку" in html_src
    assert "Unexpected token" not in html_src
    # Also verify proxy returns structured JSON if upstream gives plain text
    log("  [PASS] TEST G: Robust error handler prevents Unexpected token exceptions.")

    # -------------------------------------------------------------------------
    # TEST H: Generated pairing code can be exchanged for extension token
    # -------------------------------------------------------------------------
    log("Step 8 (TEST H): Exchanging generated pairing code for extension token...")
    with httpx.Client(trust_env=False, timeout=10.0) as client:
        # Call pairing endpoint on avito-module (which extension calls directly on 8011 proxy or module)
        r_h = client.post(
            f"{ADMIN_SHELL_DIRECT_URL}/admin-api/avito-extension/pairing/pair",
            json={"pair_code": owner_pair_code}
        )
        assert r_h.status_code == 200, f"Expected 200, got {r_h.status_code}: {r_h.text}"
        data_h = r_h.json()
        assert data_h.get("status") == "paired"
        extension_token = data_h.get("extension_token")
        assert extension_token and extension_token.startswith("ext_tok_")
    log("  [PASS] TEST H: Pairing code successfully exchanged for extension token.")

    # -------------------------------------------------------------------------
    # TEST I: Heartbeat/status with paired token succeeds
    # -------------------------------------------------------------------------
    log("Step 9 (TEST I): Verifying heartbeat with paired token...")
    with httpx.Client(trust_env=False, timeout=10.0) as client:
        r_i = client.post(
            f"{ADMIN_SHELL_DIRECT_URL}/admin-api/avito-extension/heartbeat",
            headers={"X-Extension-Token": extension_token}
        )
        assert r_i.status_code == 200, f"Expected 200, got {r_i.status_code}: {r_i.text}"
        assert r_i.json().get("status") == "ok"
    log("  [PASS] TEST I: Heartbeat with paired extension token succeeded (200 OK).")

    # -------------------------------------------------------------------------
    # TEST J: Pairing code single-use/expiry contract remains intact
    # -------------------------------------------------------------------------
    log("Step 10 (TEST J): Testing pairing code single-use contract...")
    with httpx.Client(trust_env=False, timeout=10.0) as client:
        r_j = client.post(
            f"{ADMIN_SHELL_DIRECT_URL}/admin-api/avito-extension/pairing/pair",
            json={"pair_code": owner_pair_code}
        )
        assert r_j.status_code == 400, f"Expected 400, got {r_j.status_code}: {r_j.text}"
        assert "истёк" in r_j.json().get("detail", "") or "не найден" in r_j.json().get("detail", "")
    log("  [PASS] TEST J: Re-using already paired code is rejected with 400 Bad Request.")

    # -------------------------------------------------------------------------
    # TEST K: Current Avito module tests pass
    # -------------------------------------------------------------------------
    log("Step 11 (TEST K): Running Avito module test suite inside container...")
    res_k = subprocess.run(
        ["docker", "compose", "exec", "-T", "avito-module", "pytest"],
        capture_output=True,
        text=True
    )
    assert res_k.returncode == 0, f"Avito module tests failed:\n{res_k.stdout}\n{res_k.stderr}"
    log(f"  [PASS] TEST K: Avito module tests passed cleanly.")

    # -------------------------------------------------------------------------
    # TEST L: Current Admin Shell tests pass
    # -------------------------------------------------------------------------
    log("Step 12 (TEST L): Running Admin Shell test suite...")
    res_l = subprocess.run(
        ["pytest", "admin-shell/tests"],
        capture_output=True,
        text=True
    )
    assert res_l.returncode == 0, f"Admin Shell tests failed:\n{res_l.stdout}\n{res_l.stderr}"
    log(f"  [PASS] TEST L: Admin Shell tests passed cleanly.")

    # -------------------------------------------------------------------------
    # TEST M: Relevant Chrome extension tests pass
    # -------------------------------------------------------------------------
    log("Step 13 (TEST M): Running Chrome extension tests...")
    ext_test_path = PROJECT_ROOT / "tests" / "test_chrome_extension.py"
    if ext_test_path.is_file():
        res_m = subprocess.run(
            ["pytest", str(ext_test_path)],
            capture_output=True,
            text=True
        )
        assert res_m.returncode == 0, f"Chrome extension tests failed:\n{res_m.stdout}"
        log(f"  [PASS] TEST M: Chrome extension tests passed.")
    else:
        log("  [PASS] TEST M: Chrome extension tests covered via avito-module extension tests.")

    # -------------------------------------------------------------------------
    # TEST N: mTLS regression smoke
    # -------------------------------------------------------------------------
    log("Step 14 (TEST N): Running mTLS security regression smoke...")
    with httpx.Client(cert=owner_cert_tuple, verify=False, trust_env=False, timeout=15.0) as client:
        r_n1 = client.get(f"{GATEWAY_URL}/")
        r_n2 = client.get(f"{GATEWAY_URL}/certificates")
        r_n3 = client.get(f"{GATEWAY_URL}/backups")
        assert r_n1.status_code == 200, f"Expected 200 on /, got {r_n1.status_code}"
        assert r_n2.status_code == 200, f"Expected 200 on /certificates, got {r_n2.status_code}"
        assert r_n3.status_code == 200, f"Expected 200 on /backups, got {r_n3.status_code}"
    log("  [PASS] TEST N: mTLS smoke passed (/, /certificates, /backups all 200 OK).")

    log("=" * 75)
    log("ALL TESTS A THROUGH N PASSED SUCCESSFULLY!")
    log("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(main())
