import httpx

def run():
    print("Testing admin-shell (8011)...")
    try:
        r1 = httpx.delete("http://localhost:8011/admin-api/products/99999", headers={"x-auth-is-owner": "1"})
        print("admin-shell 8011 delete:", r1.status_code)
    except Exception as e:
        print(e)
        
    print("Testing inventory (8030)...")
    try:
        r2 = httpx.post("http://localhost:8030/inventory/products/99999/delete", headers={"x-auth-is-owner": "1"})
        print("inventory 8030 delete:", r2.status_code)
    except Exception as e:
        print(e)
        
    print("Testing core (8000)...")
    try:
        r3 = httpx.delete("http://localhost:8000/api/products/99999", headers={"x-auth-is-owner": "1"})
        print("core 8000 delete:", r3.status_code)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    run()
