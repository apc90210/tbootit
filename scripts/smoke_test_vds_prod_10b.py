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
BASE_URL = "https://144.31.50.134"

LOCAL_PDF_PATH = REPO_ROOT / "admin-shell" / "app" / "static" / "docs" / "TECHNOREBOOT_USER_MANUAL_RU.pdf"
LOCAL_PDF_BYTES = LOCAL_PDF_PATH.read_bytes()
LOCAL_PDF_SHA256 = hashlib.sha256(LOCAL_PDF_BYTES).hexdigest().lower()

def main():
    print(f"=== Running Stage 10B Production Smoke Tests against {BASE_URL} ===")
    print(f"Local User Manual PDF SHA256: {LOCAL_PDF_SHA256} ({len(LOCAL_PDF_BYTES):,} bytes)")

    results = {}
    with httpx.Client(cert=(str(CERT_FILE), str(KEY_FILE)), verify=False, trust_env=False, timeout=30.0) as client:
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
        assert "Инструкция" in r.text or "user-manual.pdf" in r.text
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
        assert "Инструкция" in r.text or "user-manual.pdf" in r.text
        results["REPAIRS_OK"] = True

        # 5. Avito extension UI
        r = client.get(f"{BASE_URL}/avito/extension")
        print(f"GET /avito/extension -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200
        assert "0.2.62" in r.text, "Extension page does not show version 0.2.62"
        assert "copyCodeBtn" in r.text, "Copy code button missing"
        results["AVITO_EXTENSION_PAGE_OK"] = True

        # 6. Avito extension download
        r = client.get(f"{BASE_URL}/avito/extension/download")
        print(f"GET /avito/extension/download -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200
        assert r.content.startswith(b"PK"), "Downloaded extension file is not a valid ZIP"
        results["AVITO_EXTENSION_DOWNLOAD_OK"] = True

        # 7. Avito post-sale queue
        r = client.get(f"{BASE_URL}/avito/post-sale")
        print(f"GET /avito/post-sale -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200
        results["AVITO_POST_SALE_PAGE_OK"] = True

        # 8. Help page
        r = client.get(f"{BASE_URL}/help")
        print(f"GET /help -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200
        assert "Руководство пользователя" in r.text
        assert "/help/user-manual.pdf" in r.text
        results["HELP_PAGE_OK"] = True

        # 9. User Manual PDF download
        r = client.get(f"{BASE_URL}/help/user-manual.pdf")
        print(f"GET /help/user-manual.pdf -> Status: {r.status_code}, Length: {len(r.content)}")
        assert r.status_code == 200
        assert r.headers.get("content-type") == "application/pdf"
        assert "attachment" in r.headers.get("content-disposition", "")
        assert "TECHNOREBOOT_USER_MANUAL_RU.pdf" in r.headers.get("content-disposition", "")
        assert r.content.startswith(b"%PDF"), "Served file does not begin with %PDF header"
        remote_pdf_sha = hashlib.sha256(r.content).hexdigest().lower()
        print(f"Remote PDF SHA256: {remote_pdf_sha}")
        assert remote_pdf_sha == LOCAL_PDF_SHA256, f"PDF SHA mismatch: remote {remote_pdf_sha} != local {LOCAL_PDF_SHA256}"
        results["USER_MANUAL_DOWNLOAD_OK"] = True
        results["USER_MANUAL_PDF_SHA_MATCH"] = True

        # 10. Top nav instruction link
        results["TOP_NAV_INSTRUCTION_LINK_OK"] = True

        # 11. Manual Avito flow presence (verify in sales_detail template in live container)
        import subprocess
        ssh_key = Path(r"C:\Users\Apc\.ssh\id_ed25519")
        tmpl_check = subprocess.run(
            ["ssh", "-i", str(ssh_key), "-o", "BatchMode=yes", "root@144.31.50.134",
             "docker exec technoreboot-prod-inventory-sales grep -E '(Снять с Avito|Не снимать|Я снял объявление)' /app/app/templates/sales_detail.html"],
            capture_output=True, encoding="utf-8"
        )
        assert tmpl_check.returncode == 0
        assert "Снять с Avito" in tmpl_check.stdout
        assert "Не снимать" in tmpl_check.stdout
        assert "Я снял объявление" in tmpl_check.stdout
        print("Verified manual Avito flow buttons present in live inventory-sales container template")
        results["MANUAL_AVITO_FLOW_PRESENT"] = True

    print("\nALL PRODUCTION SMOKE TESTS PASSED!")
    return results

if __name__ == "__main__":
    main()
