#!/usr/bin/env python3
"""
Automated verification script for Stage 07A-R1: Minimal Certificate-Based Access Control (mTLS).
Runs tests A through K against the live Nginx gateway and Admin-Shell.
"""

import os
import sys
import json
import httpx

GATEWAY_URL = "https://127.0.0.1:8443"
AUTH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "auth"))

# Clean up proxy environment variables that can interfere on Windows
os.environ.pop("NO_PROXY", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

def print_result(test_name: str, passed: bool, detail: str = ""):
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {test_name}: {detail}")
    if not passed:
        sys.exit(1)

def main():
    print("=== STARTING STAGE 07A-R1 VERIFICATION (TEST A - TEST K) ===")
    
    owner_crt = os.path.join(AUTH_DIR, "certificates", "owner.crt")
    owner_key = os.path.join(AUTH_DIR, "certificates", "owner.key")
    owner_p12 = os.path.join(AUTH_DIR, "certificates", "owner.p12")
    owner_pwd_file = os.path.join(AUTH_DIR, "owner_password.txt")

    # TEST A: Pre-requisites & baseline
    assert os.path.exists(owner_crt), "owner.crt missing"
    assert os.path.exists(owner_key), "owner.key missing"
    assert os.path.exists(owner_p12), "owner.p12 missing"
    assert os.path.exists(owner_pwd_file), "owner_password.txt missing"
    print_result("TEST A (Baseline & Files)", True, "Auth artifacts and keys exist")

    # TEST B: No client certificate -> 403 Forbidden
    with httpx.Client(verify=False) as client:
        resp_b = client.get(f"{GATEWAY_URL}/")
        print_result("TEST B (No Client Cert)", resp_b.status_code == 403, f"Status code = {resp_b.status_code}")

    # TEST C: OWNER normal access -> 200 OK
    with httpx.Client(cert=(owner_crt, owner_key), verify=False) as owner_client:
        resp_c = owner_client.get(f"{GATEWAY_URL}/")
        has_nav = "Панель управления" in resp_c.text or "Доступ (mTLS)" in resp_c.text
        print_result("TEST C (OWNER Normal Access)", resp_c.status_code == 200 and has_nav, f"Status code = {resp_c.status_code}")

        # TEST D: OWNER admin access -> 200 OK
        resp_d1 = owner_client.get(f"{GATEWAY_URL}/certificates")
        resp_d2 = owner_client.get(f"{GATEWAY_URL}/admin-api/certificates")
        print_result("TEST D (OWNER Admin Access)", resp_d1.status_code == 200 and resp_d2.status_code == 200, f"/certificates={resp_d1.status_code}, /admin-api/certificates={resp_d2.status_code}")

        # TEST E: Create USER certificate
        resp_e = owner_client.post(f"{GATEWAY_URL}/admin-api/certificates", json={"name": "Точка Продаж №2"})
        user_cert = resp_e.json()
        user_id = user_cert["id"]
        user_crt = os.path.join(AUTH_DIR, "certificates", f"{user_id}.crt")
        user_key = os.path.join(AUTH_DIR, "certificates", f"{user_id}.key")
        user_p12 = os.path.join(AUTH_DIR, "certificates", f"{user_id}.p12")

        # Download p12 verification
        resp_e_dl = owner_client.get(f"{GATEWAY_URL}/admin-api/certificates/{user_id}/download")
        user_created_ok = (resp_e.status_code == 200 and user_cert["status"] == "ACTIVE" and 
                           os.path.exists(user_crt) and os.path.exists(user_key) and 
                           resp_e_dl.status_code == 200 and len(resp_e_dl.content) > 0)
        print_result("TEST E (Create USER Cert)", user_created_ok, f"User cert ID={user_id}, status={user_cert.get('status')}")

    # TEST F: USER normal access -> 200 OK
    with httpx.Client(cert=(user_crt, user_key), verify=False) as user_client:
        resp_f = user_client.get(f"{GATEWAY_URL}/")
        print_result("TEST F (USER Normal Access)", resp_f.status_code == 200, f"Status code = {resp_f.status_code}")

        # TEST G: USER admin access -> 403 Forbidden
        resp_g1 = user_client.get(f"{GATEWAY_URL}/certificates")
        resp_g2 = user_client.get(f"{GATEWAY_URL}/admin-api/certificates")
        print_result("TEST G (USER Admin Denied)", resp_g1.status_code == 403 and resp_g2.status_code == 403, f"/certificates={resp_g1.status_code}, /admin-api/certificates={resp_g2.status_code}")

    # TEST H: Revoke USER certificate via OWNER
    with httpx.Client(cert=(owner_crt, owner_key), verify=False) as owner_client:
        resp_h = owner_client.post(f"{GATEWAY_URL}/admin-api/certificates/{user_id}/revoke")
        revoked_cert = resp_h.json()
        print_result("TEST H (Revoke USER Cert)", resp_h.status_code == 200 and revoked_cert["status"] == "REVOKED", f"Revoked at {revoked_cert.get('revoked_at')}")

    # TEST I: Revoked USER access -> 403 Forbidden
    with httpx.Client(cert=(user_crt, user_key), verify=False) as user_client:
        resp_i = user_client.get(f"{GATEWAY_URL}/")
        print_result("TEST I (Revoked USER Denied)", resp_i.status_code == 403, f"Status code = {resp_i.status_code}")

    # TEST J: Revoke OWNER certificate protection -> 403 Forbidden
    with httpx.Client(cert=(owner_crt, owner_key), verify=False) as owner_client:
        resp_j = owner_client.post(f"{GATEWAY_URL}/admin-api/certificates/owner/revoke")
        print_result("TEST J (OWNER Revoke Protection)", resp_j.status_code == 403, f"Status code = {resp_j.status_code}")

    # TEST K: Persistence verification
    with open(os.path.join(AUTH_DIR, "registry.json"), "r", encoding="utf-8") as rf:
        registry = json.load(rf)
    cert_map = {c["id"]: c for c in registry}
    persisted_user = cert_map.get(user_id)

    persisted_owner = cert_map.get("owner")
    persisted_ok = (persisted_user is not None and persisted_user.get("status") == "REVOKED" and
                    persisted_owner is not None and persisted_owner.get("status") == "ACTIVE" and
                    persisted_owner.get("is_owner") is True)
    print_result("TEST K (Persistence Check)", persisted_ok, "Registry & key states verified on disk")

    # TEST L: Direct header bypass attempt without client certificate

    with httpx.Client(verify=False) as bypass_client:
        forged_headers = {
            "X-Client-Verified": "SUCCESS",
            "X-Client-Is-Owner": "1",
            "X-Auth-Verified": "true",
            "X-Auth-Is-Owner": "true",
            "X-Client-DN": "CN=OWNER,O=Technoreboot",
            "X-Client-Serial": "CDC5645E6C3FC238CE21EA41195DFC0277F9D7F",
        }
        resp_l = bypass_client.get(f"{GATEWAY_URL}/certificates", headers=forged_headers)
        # Gateway must drop connection or reject with 403 at TLS level regardless of headers
        print_result("TEST L (Header Bypass Blocked)", resp_l.status_code == 403, f"Status code = {resp_l.status_code} (rejected)")

    # TEST M: Raw module ports do not allow admin/certificate bypass
    with httpx.Client() as direct_client:
        # Check Core (8000) doesn't expose /certificates or /admin-api/certificates
        try:
            resp_m_core = direct_client.get("http://127.0.0.1:8000/certificates")
            core_blocked = resp_m_core.status_code in [404, 405]
        except Exception:
            core_blocked = True
        # Check Admin-Shell host port 8011 (internal service) doesn't bypass mTLS if reached directly without gateway headers
        try:
            resp_m_admin = direct_client.get("http://127.0.0.1:8011/certificates")
            # Without gateway injection, X-Client-Verified header is missing -> 403
            admin_blocked = resp_m_admin.status_code == 403
        except Exception:
            admin_blocked = True
        print_result("TEST M (Raw Port Bypass Blocked)", core_blocked and admin_blocked, f"Core={resp_m_core.status_code if 'resp_m_core' in locals() else 'N/A'}, Admin={resp_m_admin.status_code if 'resp_m_admin' in locals() else 'N/A'}")

    print("=== ALL TESTS A - M PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()

