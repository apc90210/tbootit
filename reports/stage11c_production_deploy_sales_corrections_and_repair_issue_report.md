# Stage 11C — Production Deployment Report: Sales Corrections & Canonical Repair Issue

**Date:** 2026-09-17  
**Canonical Production VDS:** `144.31.15.88`  
**Legacy VDS Touched:** `false` (`144.31.50.134` strictly untouched)  
**Deployment Type:** In-place Safe Additive Schema Migration & Code Update  
**Business Data Replacement:** `NONE` (Zero production business data overwritten or reseeded)  

---

## 1. Executive Summary

Stage 11C successfully deployed accepted features from Stage 11A and Stage 11B to the primary canonical production VDS (`144.31.15.88`). 

Key accomplishments:
1. **Preflight Verification:** Complete baseline audit conducted on `144.31.15.88` prior to any code or schema adjustments.
2. **Safety Backup & Release Checkpoint:** Full production backup archive created (`TECHNOREBOOT_BACKUP_2026-09-17_072006.zip`) and release checkpoint `checkpoint_20260917_072006_37768cb2` registered.
3. **Safe Additive In-Place Migration:** Applied Stage 11A (`sales.revision_count`, `sale_revisions` table) and Stage 11B (`repair_orders.final_amount`, `payment_method`, `warranty_days`, `sale_id`) migrations directly on `/srv/technoreboot/data/db/technoreboot.db` without table recreation or data deletion.
4. **Zero Fabrication of Historical Data:** No artificial sales or audit revisions were fabricated.
5. **Code Deployment & Container Rebuild:** Switched to accepted commit `ce7dec766445f4083ed81205023fb934d375bced`, rebuilt production containers, and restarted the stack.
6. **100% Invariant Preservation:** All 239 products, 7 sales, 1 repair order, 235 photos, 235 external listings, and 5 Avito post-sale tasks preserved identically.
7. **End-to-End Smoke Verification:** Verified mTLS enforcement (HTTP 403 without cert), HTTP port 80 redirect (HTTP 301), and HTTP 200 across all primary routes and new Stage 11A/11B features.

---

## 2. Environment & Git Commit Details

| Parameter | Value |
| :--- | :--- |
| **Local Repository** | `C:\tbootit` |
| **Local Branch** | `main` |
| **Local Accepted HEAD** | `ce7dec766445f4083ed81205023fb934d375bced` |
| **Production Target Host** | `root@144.31.15.88` |
| **Production HEAD Before** | `37768cb20dc7eca4a9539ce83ab9ba5b379c1232` |
| **Production HEAD After** | `ce7dec766445f4083ed81205023fb934d375bced` |
| **Legacy VDS 144.31.50.134** | Untouched (`OLD_VDS_ROUTINE_SUPPORT=false`) |

---

## 3. Safety Backup & Release Checkpoint

Prior to schema migration and container recreation, an immutable production backup and release checkpoint were created:

- **Backup Filename:** `TECHNOREBOOT_BACKUP_2026-09-17_072006.zip`
- **Backup Location (VDS):** `/srv/technoreboot/data/backups/TECHNOREBOOT_BACKUP_2026-09-17_072006.zip`
- **Backup File Size:** 8,785,804 bytes
- **Backup SHA256:** `12d1e309cf8f593fed7110f17c880ffb7e03ea322601b014e6766199163c9b81`
- **Backup Manifest OK:** `True` (tables: 24, total_rows: 3,116, storage files: 235, auth certs: 18)
- **Backup DB Quick Check:** `ok`
- **Checkpoint ID:** `checkpoint_20260917_072006_37768cb2`
- **Checkpoint Location (VDS):** `/srv/technoreboot/data/backups/release-checkpoints/checkpoint_20260917_072006_37768cb2.json`
- **Checkpoint Location (Local):** `scripts/vds_checkpoint_11c.json`

---

## 4. Schema Migration & Schema Guard

- **Migration Mode:** In-place safe additive migration only (`MIGRATION_TYPE: additive_only`).
- **Local DB Copied to Prod:** `false`
- **Local Media Copied to Prod:** `false`
- **Destructive Statements (DROP / TRUNCATE):** `0`
- **Stage 11A Migration:**
  - Added `sales.revision_count INTEGER NOT NULL DEFAULT '0'`.
  - Created `sale_revisions` table with indexes (`ix_sale_revisions_id`, `ix_sale_revisions_sale_id`).
- **Stage 11B Migration:**
  - Added `repair_orders.final_amount REAL`.
  - Added `repair_orders.payment_method VARCHAR`.
  - Added `repair_orders.warranty_days INTEGER`.
  - Added `repair_orders.sale_id INTEGER REFERENCES sales(id)`.
  - Created index `ix_repair_orders_sale_id`.
  - Linked existing repair #1 to existing repair sale #3 (`sale_id=3`, `final_amount=5000.0`, `payment_method=other`).
  - Verified no artificial sales or revenue fabricated.
- **Pre-Migration Schema Contract SHA256:** `ae36c0163d7dcd5fa4a4f8e977008566f84f1016b2aa3d686bd31228f43aa886`
- **Post-Migration Schema Contract SHA256:** `3b8d35d76ae6343f105925aa7c725c7ebc4b8613ed5f015bec61a27f491484dc`
- **DB Integrity Post-Migration (`PRAGMA quick_check`):** `ok`
- **Schema Guard (`db_schema_contract.py compare`):** `SAFE`

---

## 5. Business Data Invariant Validation

All business entities before and after deployment were counted and compared:

| Metric | Before Deployment | After Deployment | Delta | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Products (`products`)** | 239 | 239 | 0 | **EXACT MATCH** |
| **Sales (`sales`)** | 7 | 7 | 0 | **EXACT MATCH** |
| **Repairs (`repair_orders`)** | 1 | 1 | 0 | **EXACT MATCH** |
| **Product Photos (`product_photos`)** | 235 | 235 | 0 | **EXACT MATCH** |
| **External Listings (`product_external_listings`)** | 235 | 235 | 0 | **EXACT MATCH** |
| **Avito Post-Sale Tasks (`avito_post_sale_tasks`)** | 5 | 5 | 0 | **EXACT MATCH** |
| **Storage Files (`data/storage`)** | 235 | 235 | 0 | **EXACT MATCH** |
| **Sale Revisions (`sale_revisions`)** | 0 | 0 | 0 | **NO FABRICATION** |

**Business Data Preservation Verdict:** `100% PRESERVED`

---

## 6. Runtime Health & Security Invariants

All six services on `144.31.15.88` were verified healthy after deployment:

| Container | Image | Status | Ports |
| :--- | :--- | :--- | :--- |
| `technoreboot-prod-gateway` | `nginx:alpine` | Up (healthy) | `0.0.0.0:80->80/tcp`, `0.0.0.0:443->443/tcp` |
| `technoreboot-prod-admin-shell` | `production-admin-shell:latest` | Up (healthy) | Private (bridge) |
| `technoreboot-prod-inventory-sales` | `production-inventory-sales-module:latest` | Up (healthy) | Private (bridge) |
| `technoreboot-prod-repairs` | `production-repairs-module:latest` | Up (healthy) | `8040/tcp` (bridge) |
| `technoreboot-prod-core` | `production-core:latest` | Up (healthy) | Private (bridge) |
| `technoreboot-prod-avito` | `production-avito-module:latest` | Up (healthy) | Private (bridge) |

- **Crash Loops:** None (0 restarts).
- **Internal Ports Private:** Only gateway binds `80` and `443`.
- **mTLS Still Required:** Yes (HTTP 403 returned on requests without client certificate).
- **HTTP Port 80 Redirect:** HTTP 301 Moved Permanently to `https://144.31.15.88/`.
- **Avito Safety Invariant:** `AUTO_AVITO_DEACTIVATION_DISABLED: true`.

---

## 7. Read-Only Smoke Verification Results

Tested using valid owner mTLS client certificates against live production:

| Endpoint | HTTP Status | Response Size | Verification Note |
| :--- | :--- | :--- | :--- |
| `https://144.31.15.88/` | 200 OK | 797,293 B | Root navigation shell |
| `https://144.31.15.88/inventory/products` | 200 OK | 236,388 B | Product catalog |
| `https://144.31.15.88/sales/` | 200 OK | 18,156 B | Sales list |
| `https://144.31.15.88/sales/1` | 200 OK | 24,192 B | Sale detail renders "Изменить продажу" |
| `https://144.31.15.88/sales/1/edit` | 200 OK | 14,882 B | Correction form renders |
| `https://144.31.15.88/repairs/` | 200 OK | 12,990 B | Repair list |
| `https://144.31.15.88/repairs/1` | 200 OK | 22,014 B | Repair detail with `issueModal`, price & payment inputs |
| `https://144.31.15.88/repairs/repairs/1/receipt` | 200 OK | 8,869 B | Printable repair / warranty receipt |
| `https://144.31.15.88/avito/extension` | 200 OK | 19,529 B | Avito pairing & extension |
| `https://144.31.15.88/avito/post-sale` | 200 OK | 22,703 B | Avito manual post-sale queue |
| `https://144.31.15.88/help` | 200 OK | 11,092 B | Help documentation |
| `https://144.31.15.88/help/user-manual.pdf` | 200 OK | 2,470,296 B | User manual PDF |

---

## 8. Owner Browser Acceptance Instructions

The Owner should verify the deployed functionality in browser on `https://144.31.15.88`:

1. **Sales (`/sales`):**
   - Open any completed sale (e.g. `https://144.31.15.88/sales/1`).
   - Check presence of the **«Изменить продажу»** button.
   - Click it to view the correction form (`/sales/1/edit`) with item quantity/price and payment method inputs.
   - *(Optional: Do not modify unless desired)*.
2. **Repairs (`/repairs`):**
   - Open repair order #1 (`https://144.31.15.88/repairs/1`).
   - Observe status is **«Готов»** (`ready`).
   - Observe the **«Выдать клиенту»** action and payment finalization modal.
   - Observe receipt route: `https://144.31.15.88/repairs/repairs/1/receipt` renders the printable warranty receipt.

---

## 9. Final Status

`TECHNOREBOOT_STAGE11C_PRODUCTION_DEPLOY_READY_FOR_OWNER_ACCEPTANCE`
