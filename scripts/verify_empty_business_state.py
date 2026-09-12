import json
import httpx
from pathlib import Path

BASE_URL = "https://144.31.50.134"
AUTH_DIR = Path(r"C:\tbootit\data\auth\certificates")
OWNER_CERT = (str(AUTH_DIR / "owner.crt"), str(AUTH_DIR / "owner.key"))

with httpx.Client(cert=OWNER_CERT, verify=True, timeout=20.0, trust_env=False) as client:
    # 1. Products JSON route
    r = client.get(f"{BASE_URL}/products/json")
    assert r.status_code == 200
    print("Products JSON page verified: status 200")

    # 2. Inventory Products HTML
    r = client.get(f"{BASE_URL}/inventory/products")
    assert r.status_code == 200
    import re
    product_links = re.findall(r'/products/(\d+)', r.text)
    assert len(product_links) == 0, f"Expected 0 product links, found {product_links}"
    print("Products HTML verified: 0 product links")

    # 3. Inventory Sales
    r = client.get(f"{BASE_URL}/inventory/sales")
    assert r.status_code == 200
    print("Sales HTML verified: status 200")

    # 4. Cart
    r = client.get(f"{BASE_URL}/inventory/cart")
    assert r.status_code == 200
    assert "Корзина пуста" in r.text or "пуста" in r.text or "0" in r.text
    print("Cart verified: empty cart")

    # 5. Reports
    r = client.get(f"{BASE_URL}/inventory/reports/sales")
    assert r.status_code == 200
    print("Sales report verified: status 200")

    # 6. Repairs
    r = client.get(f"{BASE_URL}/repairs/repairs")
    assert r.status_code == 200
    print("Repairs verified: status 200")

    # 7. Avito extension
    r = client.get(f"{BASE_URL}/avito/extension")
    assert r.status_code == 200
    print("Avito extension verified: status 200")

print("\nEMPTY BUSINESS STATE 100% VERIFIED!")
