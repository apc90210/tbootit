import os
import sys
import httpx

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CERT_PATH = os.path.join(REPO_ROOT, "data", "auth", "certificates", "owner.crt")
KEY_PATH = os.path.join(REPO_ROOT, "data", "auth", "certificates", "owner.key")

BASE_URL = "https://localhost:8443"

def main():
    print("=== Stage 10D-R1 LOCAL Smoke Test ===")
    assert os.path.exists(CERT_PATH), f"Missing cert: {CERT_PATH}"
    assert os.path.exists(KEY_PATH), f"Missing key: {KEY_PATH}"

    client = httpx.Client(
        cert=(CERT_PATH, KEY_PATH),
        verify=False,
        timeout=15.0,
        trust_env=False,
        follow_redirects=True
    )

    routes = [
        ("/", "Root index"),
        ("/inventory/products", "Inventory products"),
        ("/sales", "Sales"),
        ("/repairs", "Repairs"),
        ("/avito/extension", "Avito extension"),
        ("/avito/post-sale", "Avito post-sale"),
        ("/help", "Help"),
        ("/help/user-manual.pdf", "User manual PDF"),
    ]

    all_ok = True
    results = {}

    for path, desc in routes:
        url = f"{BASE_URL}{path}"
        try:
            resp = client.get(url)
            status = resp.status_code
            content_len = len(resp.content)
            is_good = (status == 200)
            if not is_good:
                all_ok = False
            results[path] = {
                "desc": desc,
                "status": status,
                "length": content_len,
                "ok": is_good
            }
            status_text = "PASS" if is_good else f"FAIL ({status})"
            print(f"[{status_text}] {path:<25} -> {status} ({content_len} bytes) - {desc}")
        except Exception as e:
            all_ok = False
            results[path] = {"desc": desc, "status": "ERROR", "error": str(e), "ok": False}
            print(f"[FAIL] {path:<25} -> ERROR: {e}")

    print("=" * 60)
    print(f"LOCAL SMOKE TEST RESULT: {'PASS' if all_ok else 'FAIL'}")
    print("=" * 60)

    if not all_ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
