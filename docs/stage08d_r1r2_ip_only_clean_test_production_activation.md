# Stage 08D-R1R2: IP-Only Clean Test-Production Activation

**Document Date:** 2026-09-12  
**Canonical Production URL:** `https://144.31.50.134`  
**Domain Status:** Deferred / Not Required  
**Local Status:** DEV / TEST Sandbox (`https://localhost:8443`)  
**VDS Status:** Canonical Real-User Test-Production Active  

---

## 1. Operating Model & Executive Summary

In Stage 08D-R1R2, the Project Owner directed that DNS/domain activation (`atanov821.serv.host`) be deferred and that the production environment be activated directly on the VDS IP address:
```text
CURRENT_PRODUCTION_URL = https://144.31.50.134
DOMAIN_NAME = deferred / not required
LOCAL = DEV / TEST
VDS = canonical real-user data
FUTURE_DEPLOYS = code only
LOCAL BUSINESS DATA MUST NEVER BE RESTORED TO VDS
```

Both environments run simultaneously:
- **Local:** DEV / TEST sandbox with existing test/demo data (50 products, 52 sales, 66 repairs).
- **VDS:** Clean real-user production starting from zero business records (0 products, 0 sales, 0 repairs, 0 photos).

---

## 2. IP-Only Public TLS via Let's Encrypt

Using an isolated environment on Debian VDS (`/opt/certbot-venv`), Certbot 5.8.0 was installed to utilize the new Let's Encrypt IP address certificate issuance feature with the short-lived profile:
- **Command:** `certbot certonly --standalone --preferred-profile shortlived --ip-address 144.31.50.134`
- **Issuer:** Let's Encrypt (`C=US, O=Let's Encrypt, CN=YE2`)
- **SAN:** `IP Address:144.31.50.134`
- **Validity:** Short-lived profile (6 days, auto-renewed bi-daily)
- **Public Trust:** Accepted natively by operating systems and standard HTTP clients without custom CA flags (`verify=True`).
- **Automated Renewal:** Systemd timer `certbot.timer` active; deploy renewal hook `/etc/letsencrypt/renewal-hooks/deploy/technoreboot_reload.sh` copies updated certificates and reloads Nginx automatically.
- **Dry-Run:** `certbot renew --dry-run --no-random-sleep-on-renew` PASSED.

---

## 3. Clean VDS Data Reset Execution

With the VDS stack stopped and the pre-reset backup verified (`TECHNOREBOOT_PRE_RESET_BACKUP_2026-09-12_081617.zip`, SHA256 `4362991c...`), live business data was reset to zero:

### Database Invariants After Reset
| Table | Pre-Reset | Post-Reset | Classification |
| :--- | :--- | :--- | :--- |
| `products` | 50 | **0** | BUSINESS |
| `sales` | 52 | **0** | BUSINESS |
| `sale_items` | 53 | **0** | BUSINESS |
| `repair_orders` | 66 | **0** | BUSINESS |
| `repair_status_history` | 153 | **0** | BUSINESS |
| `product_photos` | 50 | **0** | BUSINESS |
| `product_external_listings` | 50 | **0** | BUSINESS |
| `product_events` | 32 | **0** | BUSINESS |
| `stock_movements` | 35 | **0** | BUSINESS |
| `customers` | 28 | **0** | BUSINESS |
| `product_avito_attribute_values` | 7 | **0** | BUSINESS |
| `audit_log` | 2098 | **2** | TECHNICAL (2 system seed rows) |
| `categories` | 47 | **47** | REFERENCE (Preserved) |
| `organization_settings` | 1 | **1** | REFERENCE (Preserved) |
| `avito_categories` | 45 | **45** | REFERENCE (Preserved) |
| `avito_canonical_categories` | 15 | **15** | REFERENCE (Preserved) |
| `avito_canonical_fields` | 101 | **101** | REFERENCE (Preserved) |
| `avito_attribute_definitions` | 211 | **211** | REFERENCE (Preserved) |
| `avito_attribute_options` | 234 | **234** | REFERENCE (Preserved) |
| `avito_observed_field_mappings` | 101 | **101** | REFERENCE (Preserved) |

### Media Storage & Avito State
- **Live Media Files:** `/srv/technoreboot/data/storage/` -> **0 files** (`LIVE_STORAGE_BUSINESS_FILES = 0`).
- **Avito State:** Removed `ads/`, `import_runs/`, `runs/`, and listing JSON caches. Preserved pairing infrastructure (`profiles/`, `profiles.json`, `extension_pair_codes.json`, `extension_tokens.json`).

---

## 4. Runtime & mTLS Verification

All 6 production services started healthy on VDS. Verified from Owner workstation via HTTPS (`https://144.31.50.134`):
1. **HTTP -> HTTPS Redirect:** `http://144.31.50.134/` -> 301 -> `https://144.31.50.134/`.
2. **Public Trust:** Accepted by standard Python `httpx.Client(verify=True)` with zero SSL certificate errors.
3. **mTLS Enforcement:** Requests without client certificate rejected with HTTP 403.
4. **Owner Access:** Accepted on all 10 canonical routes (`/`, `/inventory/products`, `/products/json`, `/inventory/sales`, `/inventory/cart`, `/inventory/reports/sales`, `/repairs/repairs`, `/avito/extension`, `/backups`, `/certificates`).
5. **User RBAC:** Allowed on operational routes; rejected with HTTP 403 on `/backups` and `/certificates`.
6. **Revocation Registry:** Revoked client certificate (`0bcc72bc7c81`) rejected with HTTP 403.
7. **Empty UI State:** 0 products, 0 sales, empty cart, 0 repairs, today/week/year reports = 0.
8. **Multi-Environment Support:** The same Owner client certificate works seamlessly on both Local (`https://localhost:8443`) and VDS (`https://144.31.50.134`).

---

## 5. Code-Only Deployment Self-Test

Executed `deploy/production/update_code_only.sh origin/main` on the live VDS:
- Verified data guard `/srv/technoreboot/data/.technoreboot_production_data`.
- Automatically created pre-update backup `TECHNOREBOOT_BACKUP_2026-09-12_084427.zip`.
- Pulled latest Git commit, built container images from source, and recreated containers.
- Polled healthchecks until all 6 services became healthy.
- Verified business row counts remained exactly 0 before and after deployment (`PRE_COUNTS == POST_COUNTS`).

---

## 6. Clean Baseline Production Backup

Created post-activation baseline backup on VDS:
- **Archive File:** `/srv/technoreboot/data/backups/TECHNOREBOOT_CLEAN_IP_TEST_PRODUCTION_BASELINE_2026-09-12.zip`
- **SHA256:** `e6892f9921de3b62f7de25c8780f554c39002cb681b7d7edf8aa6fd36062a6b0`
- **Integrity:** Valid manifest, 0 products, 0 sales, 0 repairs, 0 photos, client CA preserved (`32CEFDD1...`).
