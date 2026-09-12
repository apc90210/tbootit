import ssl
import json
import httpx
import subprocess
from pathlib import Path

BASE_URL = "https://144.31.50.134"
AUTH_DIR = Path(r"C:\tbootit\data\auth\certificates")
OWNER_CERT = (str(AUTH_DIR / "owner.crt"), str(AUTH_DIR / "owner.key"))

print("==================================================================")
print("STAGE 08D-R1R3: END-TO-END VDS PAIRING PROOF")
print("Target:", BASE_URL)
print("==================================================================")

with httpx.Client(cert=OWNER_CERT, verify=True, timeout=15.0, trust_env=False) as client:
    # 1. Open production extension page
    print("\n[Step 1] Opening production extension page: /avito/extension")
    r_page = client.get(f"{BASE_URL}/avito/extension")
    assert r_page.status_code == 200, f"Page load failed: {r_page.status_code}"
    assert "v0.2.55" in r_page.text, "Page must display v0.2.55"
    assert "serverUrlDisplay" in r_page.text, "Page must contain serverUrlDisplay"
    assert "copyServerUrl" in r_page.text, "Page must contain copyServerUrl"
    print("  [PASS] Production extension page renders v0.2.55 with server URL guidance")

    # 1b. Verify download endpoint returns v0.2.55 zip
    print("\n[Step 1b] Verifying extension download package")
    r_dl = client.get(f"{BASE_URL}/avito/extension/download")
    assert r_dl.status_code == 200, f"Download failed: {r_dl.status_code}"
    disposition = r_dl.headers.get("content-disposition", "")
    assert "0.2.55" in disposition, f"Expected 0.2.55 in disposition: {disposition}"
    print(f"  [PASS] Download serves: {disposition}")

    # 2. Generate a new 6-digit code
    print("\n[Step 2] Generating fresh pairing code via /admin-api/avito-extension/pairing/generate")
    r_gen = client.post(f"{BASE_URL}/admin-api/avito-extension/pairing/generate")
    assert r_gen.status_code == 200, f"Generate failed: {r_gen.status_code} {r_gen.text}"
    gen_data = r_gen.json()
    pair_code = gen_data.get("pair_code")
    assert pair_code and len(pair_code) == 6 and pair_code.isdigit(), f"Invalid code: {pair_code}"
    print(f"  [PASS] Fresh pairing code created: {pair_code} (expires in {gen_data.get('expires_in_seconds')}s)")

# 3. Confirm code exists in canonical pairing storage on VDS
print("\n[Step 3] Checking canonical persistent storage on VDS...")
check_script = f"""
import json
from pathlib import Path

p = Path('/srv/technoreboot/data/avito-module/extension_pair_codes.json')
if not p.exists():
    print('NOT_FOUND')
else:
    data = json.loads(p.read_text('utf-8'))
    if '{pair_code}' in data:
        print('CODE_EXISTS:' + json.dumps(data['{pair_code}']))
    else:
        print('CODE_NOT_IN_STORAGE')
"""
res = subprocess.run(
    ["ssh", "-i", r"C:\Users\Apc\.ssh\id_ed25519", "root@144.31.50.134", "python3"],
    input=check_script,
    text=True,
    capture_output=True
)
print("  VDS Storage check:", res.stdout.strip())
assert "CODE_EXISTS" in res.stdout, f"Code {pair_code} missing from VDS storage: {res.stdout}"
print("  [PASS] Code confirmed present in /srv/technoreboot/data/avito-module/extension_pair_codes.json")

with httpx.Client(cert=OWNER_CERT, verify=True, timeout=15.0, trust_env=False) as client:
    # 4. Redeem exactly that code through the same HTTP/API path used by Chrome Extension
    print("\n[Step 4] Redeeming pairing code via /admin-api/avito-extension/pairing/pair")
    r_pair = client.post(
        f"{BASE_URL}/admin-api/avito-extension/pairing/pair",
        json={"pair_code": pair_code}
    )
    assert r_pair.status_code == 200, f"Pairing failed: {r_pair.status_code} {r_pair.text}"
    pair_result = r_pair.json()
    assert pair_result.get("status") == "paired", f"Unexpected status: {pair_result}"
    token = pair_result.get("extension_token")
    assert token and token.startswith("ext_tok_"), f"Unexpected token: {token}"
    print(f"  [PASS] Code successfully redeemed: status={pair_result.get('status')}")
    print(f"  Issued extension token: {token[:12]}... (SHA256 authenticated)")

    # 5. Verify extension connection state via /status endpoint
    print("\n[Step 5] Checking extension status with issued token")
    r_status = client.get(
        f"{BASE_URL}/admin-api/avito-extension/status",
        headers={"X-Extension-Token": token}
    )
    assert r_status.status_code == 200
    st_data = r_status.json()
    assert st_data.get("online") is True
    assert st_data.get("paired") is True
    assert st_data.get("token_valid") is True
    assert st_data.get("version") == "0.2.55"
    print(f"  [PASS] Extension status verified online & paired (v{st_data.get('version')})")

    # 6. Verify second unknown code returns 400
    print("\n[Step 6] Testing unknown code redemption")
    r_unknown = client.post(
        f"{BASE_URL}/admin-api/avito-extension/pairing/pair",
        json={"pair_code": "000000"}
    )
    assert r_unknown.status_code == 400, f"Expected 400, got {r_unknown.status_code}"
    assert "Код подключения не найден" in r_unknown.json().get("detail", "")
    print(f"  [PASS] Unknown code correctly rejected with HTTP 400: {r_unknown.json().get('detail')}")

    # 7. Verify one-time-use rejection on reused code
    print("\n[Step 7] Testing reused code rejection (one-time-use rule)")
    r_reused = client.post(
        f"{BASE_URL}/admin-api/avito-extension/pairing/pair",
        json={"pair_code": pair_code}
    )
    assert r_reused.status_code == 400, f"Expected 400 on reused code, got {r_reused.status_code}"
    assert "истёк" in r_reused.json().get("detail", "")
    print(f"  [PASS] Reused code correctly rejected with HTTP 400: {r_reused.json().get('detail')}")

print("\n==================================================================")
print("FINAL SUMMARY:")
print("FRESH_PAIRING_CODE_CREATED = true")
print("FRESH_PAIRING_CODE_REDEEMED = true")
print("PAIRING_HTTP_STATUS = 200")
print("UNKNOWN_CODE_HTTP_STATUS = 400")
print("REUSED_CODE_HTTP_STATUS = 400")
print("PRODUCTION_TARGET = https://144.31.50.134")
print("ALL RUNTIME PAIRING PROOFS PASSED ON VDS!")
print("==================================================================")
