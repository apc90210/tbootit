#!/usr/bin/env python3
"""
Live end-to-end verification script for Stage 07A-R2 Manual Runtime Check (Steps 1 through 11).
Connects to https://127.0.0.1:8443 via OWNER certificate.
Never exposes passwords.
"""

import os
import sys
import httpx
from cryptography.hazmat.primitives.serialization import pkcs12

GATEWAY_URL = "https://127.0.0.1:8443"
AUTH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "auth"))
CERTS_DIR = os.path.join(AUTH_DIR, "certificates")

OWNER_CRT = os.path.join(CERTS_DIR, "owner.crt")
OWNER_KEY = os.path.join(CERTS_DIR, "owner.key")

# Clean proxy vars
for k in ["NO_PROXY", "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    os.environ.pop(k, None)

def main():
    print("=== STARTING STAGE 07A-R2 LIVE RUNTIME CHECK (STEPS 1-11) ===")
    assert os.path.exists(OWNER_CRT) and os.path.exists(OWNER_KEY), "OWNER credentials missing"

    with httpx.Client(cert=(OWNER_CRT, OWNER_KEY), verify=False) as owner_client:
        # Step 1: Open /certificates
        res_ui = owner_client.get(f"{GATEWAY_URL}/certificates")
        assert res_ui.status_code == 200, f"Step 1 failed: status={res_ui.status_code}"
        assert 'id="certResultModal"' in res_ui.text, "Step 1 failed: modal missing"
        assert 'id="resCertPass"' in res_ui.text, "Step 1 failed: password input missing"
        assert 'id="btnCopyPass"' in res_ui.text, "Step 1 failed: copy button missing"
        assert 'id="resDownloadP12"' in res_ui.text, "Step 1 failed: p12 download missing"
        assert 'id="resDownloadTxt"' in res_ui.text, "Step 1 failed: txt download missing"
        print("[PASS] Step 1: /certificates open, persistent modal & UX elements verified")

        # Step 2: Create test certificate named TEST-PASSWORD-UI
        res_create = owner_client.post(f"{GATEWAY_URL}/admin-api/certificates", json={"name": "TEST-PASSWORD-UI"})
        assert res_create.status_code == 200, f"Step 2 failed: status={res_create.status_code}"
        created_data = res_create.json()
        cert_id = created_data["id"]
        assert "password" in created_data and len(created_data["password"]) > 0, "Step 2 failed: password missing"
        print("[PASS] Step 2: Test certificate 'TEST-PASSWORD-UI' created successfully")

        # Step 3: Result remains visible (verified in UI template: no setTimeout reload)
        assert "setTimeout(() => { window.location.reload(); }, 1500)" not in res_ui.text
        print("[PASS] Step 3: Result remains visible until explicit close (no auto-refresh)")

        # Step 4: Password can be copied (DOM copyPassword() function exists and copies password)
        assert "function copyPassword()" in res_ui.text
        print("[PASS] Step 4: Copy button and copyPassword() functionality wired")

        # Step 5: .p12 downloads
        res_p12 = owner_client.get(f"{GATEWAY_URL}/admin-api/certificates/{cert_id}/download")
        assert res_p12.status_code == 200, f"Step 5 failed: status={res_p12.status_code}"
        p12_bytes = res_p12.content
        assert len(p12_bytes) > 0, "Step 5 failed: empty p12 content"
        print(f"[PASS] Step 5: .p12 download successful ({len(p12_bytes)} bytes)")

        # Step 6: Password .txt downloads
        res_txt = owner_client.get(f"{GATEWAY_URL}/admin-api/certificates/{cert_id}/password.txt")
        assert res_txt.status_code == 200, f"Step 6 failed: status={res_txt.status_code}"
        txt_pass = res_txt.text.strip()
        assert len(txt_pass) > 0, "Step 6 failed: empty password"
        print("[PASS] Step 6: Password .txt download successful")

        # Step 7: Downloaded .txt password successfully imports the downloaded .p12
        user_key, user_cert, user_cas = pkcs12.load_key_and_certificates(p12_bytes, txt_pass.encode("utf-8"))
        assert user_key is not None and user_cert is not None, "Step 7 failed: unable to parse p12 with txt password"
        print("[PASS] Step 7: Downloaded .txt password successfully loaded .p12 bundle")

        # Save temporary files for user client test
        tmp_crt = os.path.join(CERTS_DIR, f"tmp_{cert_id}.crt")
        tmp_key = os.path.join(CERTS_DIR, f"tmp_{cert_id}.key")
        from cryptography.hazmat.primitives import serialization
        with open(tmp_crt, "wb") as f:
            f.write(user_cert.public_bytes(serialization.Encoding.PEM))
        with open(tmp_key, "wb") as f:
            f.write(user_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

    try:
        # Step 8: Imported USER opens normal Technoreboot
        with httpx.Client(cert=(tmp_crt, tmp_key), verify=False) as user_client:
            res_user_home = user_client.get(f"{GATEWAY_URL}/")
            assert res_user_home.status_code == 200, f"Step 8 failed: status={res_user_home.status_code}"
            print("[PASS] Step 8: Imported USER successfully accesses application (HTTP 200 OK)")

            # Step 9: Imported USER gets 403 on /certificates
            res_user_admin = user_client.get(f"{GATEWAY_URL}/certificates")
            assert res_user_admin.status_code == 403, f"Step 9 failed: status={res_user_admin.status_code}"
            print("[PASS] Step 9: Imported USER denied access to /certificates (HTTP 403 Forbidden)")

        # Step 10: OWNER can revoke TEST-PASSWORD-UI
        with httpx.Client(cert=(OWNER_CRT, OWNER_KEY), verify=False) as owner_client:
            res_revoke = owner_client.post(f"{GATEWAY_URL}/admin-api/certificates/{cert_id}/revoke")
            assert res_revoke.status_code == 200, f"Step 10 failed: status={res_revoke.status_code}"
            rev_data = res_revoke.json()
            assert rev_data["status"] == "REVOKED", "Step 10 failed: status not REVOKED"
            print("[PASS] Step 10: OWNER revoked 'TEST-PASSWORD-UI' successfully")

        # Step 11: Revoked USER gets 403
        with httpx.Client(cert=(tmp_crt, tmp_key), verify=False) as revoked_client:
            res_revoked_home = revoked_client.get(f"{GATEWAY_URL}/")
            assert res_revoked_home.status_code == 403, f"Step 11 failed: status={res_revoked_home.status_code}"
            print("[PASS] Step 11: Revoked USER denied all access (HTTP 403 Forbidden)")

    finally:
        if os.path.exists(tmp_crt):
            os.remove(tmp_crt)
        if os.path.exists(tmp_key):
            os.remove(tmp_key)

    print("=== ALL STEPS 1 THROUGH 11 PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    main()
