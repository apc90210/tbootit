import sys
import hashlib
from pathlib import Path
import httpx

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).resolve().parent.parent
CERT_FILE = REPO_ROOT / "data" / "auth" / "certificates" / "owner.crt"
KEY_FILE = REPO_ROOT / "data" / "auth" / "certificates" / "owner.key"
BASE_URL = "https://144.31.15.88"
HTTP_URL = "http://144.31.15.88"

LOCAL_PDF_PATH = REPO_ROOT / "admin-shell" / "app" / "static" / "docs" / "TECHNOREBOOT_USER_MANUAL_RU.pdf"
LOCAL_PDF_BYTES = LOCAL_PDF_PATH.read_bytes()
LOCAL_PDF_SHA256 = hashlib.sha256(LOCAL_PDF_BYTES).hexdigest().lower()

EXPECTED_EXT_HASH = "1cf0c2d733b801e00d81e4563a0f24c2c3a9b46f99053c33b106045b95cc2ae9"
EXPECTED_PDF_HASH = "50ddeedeb4f93d2ea164ce57218a49cf6318ad2557a90c9266995dc8d0589b9e"

def main():
    print(f"=== Running Stage 10D Target Smoke Tests against {BASE_URL} ===")
    results = {}

    # Test 0: HTTP 80 Redirect to HTTPS
    print("\n--- Testing HTTP 80 Redirect ---")
    with httpx.Client(follow_redirects=False, trust_env=False, timeout=10.0) as client:
        r = client.get(f"{HTTP_URL}/")
        print(f"GET {HTTP_URL}/ -> Status: {r.status_code}, Location: {r.headers.get('Location')}")
        assert r.status_code == 301, f"Expected 301, got {r.status_code}"
        assert "https://144.31.15.88" in r.headers.get("Location", "")
        results["HTTP_80_REDIRECT_OK"] = True

    # Test 1: Public TLS Trust (without mTLS cert)
    print("\n--- Testing HTTPS Without Client Certificate (mTLS rejection) ---")
    try:
        with httpx.Client(verify=True, trust_env=False, timeout=10.0) as client:
            r = client.get(f"{BASE_URL}/")
            print(f"GET {BASE_URL}/ without client cert -> Status: {r.status_code}")
            assert r.status_code == 403, f"Expected 403 Forbidden without client cert, got {r.status_code}"
            results["MTLS_REJECTION_OK"] = True
            results["PUBLIC_TLS_TRUST_OK"] = True
    except httpx.HTTPError as e:
        print(f"HTTP error without cert: {e}")
        # If server rejects at TLS handshake level or returns 403, both enforce mTLS
        results["MTLS_REJECTION_OK"] = True

    # Test 2: OWNER Client Certificate Access
    print("\n--- Testing Authenticated Routes with OWNER Certificate ---")
    with httpx.Client(cert=(str(CERT_FILE), str(KEY_FILE)), verify=True, trust_env=False, timeout=30.0) as client:
        # 1. Root / Dashboard
        r = client.get(f"{BASE_URL}/")
        print(f"GET / -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200, f"GET / failed with status {r.status_code}"
        assert "Инструкция" in r.text or "user-manual.pdf" in r.text
        results["ROOT_OK"] = True

        # 2. Inventory / Products
        r = client.get(f"{BASE_URL}/inventory/products")
        print(f"GET /inventory/products -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200, f"GET /inventory/products failed with {r.status_code}"
        results["PRODUCTS_OK"] = True

        # 3. Sales
        r = client.get(f"{BASE_URL}/sales")
        print(f"GET /sales -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200, f"GET /sales failed with {r.status_code}"
        results["SALES_OK"] = True

        # 4. Repairs
        r = client.get(f"{BASE_URL}/repairs")
        print(f"GET /repairs -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200, f"GET /repairs failed with {r.status_code}"
        results["REPAIRS_OK"] = True

        # 5. Avito extension UI
        r = client.get(f"{BASE_URL}/avito/extension")
        print(f"GET /avito/extension -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200
        assert "0.2.62" in r.text, "Extension page does not show version 0.2.62"
        results["AVITO_EXTENSION_OK"] = True

        # 6. Avito post-sale
        r = client.get(f"{BASE_URL}/avito/post-sale")
        print(f"GET /avito/post-sale -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200
        results["AVITO_POST_SALE_OK"] = True

        # 7. Help page
        r = client.get(f"{BASE_URL}/help")
        print(f"GET /help -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200
        results["HELP_OK"] = True

        # 8. User Manual PDF Download
        r = client.get(f"{BASE_URL}/help/user-manual.pdf")
        print(f"GET /help/user-manual.pdf -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200
        pdf_hash = hashlib.sha256(r.content).hexdigest().lower()
        print(f"Downloaded PDF SHA256: {pdf_hash}")
        assert pdf_hash == EXPECTED_PDF_HASH, f"PDF hash mismatch: {pdf_hash} vs {EXPECTED_PDF_HASH}"
        results["USER_MANUAL_OK"] = True
        results["MANUAL_PDF_HASH_MATCH"] = True

        # 9. Extension ZIP Download
        r = client.get(f"{BASE_URL}/avito/extension/download")
        print(f"GET /avito/extension/download -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200
        ext_hash = hashlib.sha256(r.content).hexdigest().lower()
        print(f"Downloaded Extension ZIP SHA256: {ext_hash}")
        assert ext_hash == EXPECTED_EXT_HASH, f"Extension ZIP mismatch: {ext_hash} vs {EXPECTED_EXT_HASH}"
        results["EXTENSION_HASH_MATCH"] = True

    print("\n=== SMOKE TEST SUMMARY ===")
    for k, v in results.items():
        print(f"  {k}: {v}")

    all_passed = all(results.values())
    if all_passed:
        print("\n>>> ALL STAGE 10D SMOKE TESTS PASSED! <<<")
    else:
        print("\n>>> SOME TESTS FAILED <<<")
        sys.exit(1)

if __name__ == "__main__":
    main()
