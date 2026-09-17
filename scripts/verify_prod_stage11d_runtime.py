import httpx
import urllib3
urllib3.disable_warnings()

cert_owner = ('data/auth/certificates/owner.crt', 'data/auth/certificates/owner.key')
cert_user = ('data/auth/certificates/6be6165efedf.crt', 'data/auth/certificates/6be6165efedf.key')
base_url = 'https://144.31.15.88'

print('=== 1. Testing without cert ===')
try:
    with httpx.Client(verify=False, trust_env=False, timeout=10.0) as client:
        r = client.get(f'{base_url}/')
        print(f'No cert status: {r.status_code}')
except Exception as e:
    print(f'No cert error: {e}')

print('\n=== 2. Testing with user cert ===')
with httpx.Client(cert=cert_user, verify=False, trust_env=False, timeout=10.0) as client:
    r_sales = client.get(f'{base_url}/sales')
    has_bar_sales = "ownerBulkBar" in r_sales.text
    print(f'User GET /sales: {r_sales.status_code}, ownerBulkBar present: {has_bar_sales}')
    
    r_repairs = client.get(f'{base_url}/repairs/repairs')
    has_bar_rep = "ownerBulkBar" in r_repairs.text
    print(f'User GET /repairs/repairs: {r_repairs.status_code}, ownerBulkBar present: {has_bar_rep}')
    
    r_del_sales = client.post(f'{base_url}/sales/bulk-delete', json={'sale_ids': [9999]})
    print(f'User POST /sales/bulk-delete: {r_del_sales.status_code}, detail: {r_del_sales.text[:120]}')
    
    r_del_rep = client.post(f'{base_url}/repairs/repairs/bulk-delete', json={'repair_ids': [9999]})
    print(f'User POST /repairs/bulk-delete: {r_del_rep.status_code}, detail: {r_del_rep.text[:120]}')

    # Spoof test: non-owner certificate + X-Auth-Is-Owner: 1
    r_spoof = client.post(f'{base_url}/sales/bulk-delete', json={'sale_ids': [9999]}, headers={'x-auth-is-owner': '1'})
    print(f'User SPOOF POST /sales/bulk-delete: {r_spoof.status_code}, detail: {r_spoof.text[:120]}')

    r_spoof_rep = client.post(f'{base_url}/repairs/repairs/bulk-delete', json={'repair_ids': [9999]}, headers={'x-auth-is-owner': '1'})
    print(f'User SPOOF POST /repairs/bulk-delete: {r_spoof_rep.status_code}, detail: {r_spoof_rep.text[:120]}')

print('\n=== 3. Testing with owner cert ===')
with httpx.Client(cert=cert_owner, verify=False, trust_env=False, timeout=10.0) as client:
    r_sales = client.get(f'{base_url}/sales')
    has_bar_sales = "ownerBulkBar" in r_sales.text
    print(f'Owner GET /sales: {r_sales.status_code}, ownerBulkBar present: {has_bar_sales}')
    
    r_repairs = client.get(f'{base_url}/repairs/repairs')
    has_bar_rep = "ownerBulkBar" in r_repairs.text
    print(f'Owner GET /repairs/repairs: {r_repairs.status_code}, ownerBulkBar present: {has_bar_rep}')
    
    # Authorized empty list requests should return 400 (not 403!)
    r_auth_del_sales = client.post(f'{base_url}/sales/bulk-delete', json={'sale_ids': []})
    print(f'Owner POST /sales/bulk-delete (empty): {r_auth_del_sales.status_code}, detail: {r_auth_del_sales.text[:120]}')
    
    r_auth_del_rep = client.post(f'{base_url}/repairs/repairs/bulk-delete', json={'repair_ids': []})
    print(f'Owner POST /repairs/bulk-delete (empty): {r_auth_del_rep.status_code}, detail: {r_auth_del_rep.text[:120]}')

    # Read repair 1
    r_rep1 = client.get(f'{base_url}/repairs/repairs/1')
    print(f'Owner GET /repairs/repairs/1: {r_rep1.status_code}')
    if r_rep1.status_code == 200:
        has_canonical = '/sales/3' in r_rep1.text
        has_broken = '/sales/sales/3' in r_rep1.text
        has_ready = 'value="ready"' in r_rep1.text
        print(f'Linked sale canonical href /sales/3 present: {has_canonical}')
        print(f'Broken href /sales/sales/3 present: {has_broken}')
        print(f'Ready status option present: {has_ready}')

    # Read repair list
    r_rep_list = client.get(f'{base_url}/repairs/repairs')
    print(f'Owner repairs list: {r_rep_list.status_code}')
