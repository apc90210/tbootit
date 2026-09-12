import ssl
import httpx
from pathlib import Path

BASE_URL = "https://144.31.50.134"
HTTP_URL = "http://144.31.50.134"

AUTH_DIR = Path(r"C:\tbootit\data\auth\certificates")
OWNER_CERT = (str(AUTH_DIR / "owner.crt"), str(AUTH_DIR / "owner.key"))
USER_CERT = (str(AUTH_DIR / "5419163337bd.crt"), str(AUTH_DIR / "5419163337bd.key"))

print("=== 1. HTTP to HTTPS redirect check ===")
with httpx.Client(follow_redirects=False, timeout=10.0, trust_env=False) as client:
    r = client.get(HTTP_URL)
    print("HTTP GET / status:", r.status_code)
    print("Location header:", r.headers.get("location"))
    assert r.status_code in [301, 308], f"Expected redirect, got {r.status_code}"
    assert "https://" in r.headers.get("location", ""), "Expected redirect to https"

print("\n=== 2. Public TLS trust check (default system CAs, NO verify=False) ===")
try:
    # Use standard default system root CAs (verify=True)
    with httpx.Client(verify=True, timeout=10.0, trust_env=False) as client:
        # Requesting without client cert should yield 400 Bad Request (SSL cert required)
        r = client.get(f"{BASE_URL}/")
        print("Response without client cert:", r.status_code, r.text[:100])
        assert r.status_code in [400, 403], f"Expected 400 or 403 (no cert), got {r.status_code}"
        print(f"NO_CLIENT_CERT = REJECTED (status {r.status_code})")
except ssl.SSLError as e:
    print("TLS Verification Error:", e)
    raise

print("\n=== 3. OWNER mTLS route checks ===")
owner_routes = [
    "/",
    "/inventory/products",
    "/products/json",
    "/inventory/sales",
    "/inventory/cart",
    "/inventory/reports/sales",
    "/repairs/repairs",
    "/avito/extension",
    "/backups",
    "/certificates",
]

with httpx.Client(cert=OWNER_CERT, verify=True, timeout=10.0, trust_env=False) as client:
    for route in owner_routes:
        url = f"{BASE_URL}{route}"
        r = client.get(url)
        print(f"OWNER GET {route} -> {r.status_code}")
        assert r.status_code == 200, f"Expected 200 on {route}, got {r.status_code}"

print("\n=== 4. USER mTLS RBAC checks ===")
with httpx.Client(cert=USER_CERT, verify=True, timeout=10.0, trust_env=False) as client:
    for route in ["/backups", "/certificates"]:
        url = f"{BASE_URL}{route}"
        r = client.get(url)
        print(f"USER GET {route} -> {r.status_code}")
        assert r.status_code == 403, f"Expected 403 on {route}, got {r.status_code}"
    
    # Operational routes should succeed
    for route in ["/", "/inventory/products"]:
        url = f"{BASE_URL}{route}"
        r = client.get(url)
        print(f"USER GET {route} -> {r.status_code}")
        assert r.status_code == 200, f"Expected 200 on {route}, got {r.status_code}"

print("\nALL VERIFICATIONS PASSED!")
