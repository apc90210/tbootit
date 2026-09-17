# Stage 11D-R1 — Runtime Verification + Delete Invariants

## Runtime Proof
- **LOCAL_HEAD:** `ac115b08721f04dcaba3809015025f576e32ea7b`
- **PROD_WORKTREE_HEAD:** `ac115b08721f04dcaba3809015025f576e32ea7b`
- **PROD_RUNNING_CODE_STAGE11D_CONFIRMED:** true
- **REBUILD_REQUIRED:** true
- **REBUILD_PERFORMED:** true
- **PROD_CORE_IMAGE_ID:** `sha256:237ff077b400f85bb8e9ed20f9e4b0c71a828d49c2111d96f0503379e710a5da`
- **PROD_ADMIN_IMAGE_ID:** `sha256:0bcc827b6307d599bf296291974632cc68736e5c6394bdbad723d4e1d863ac2d`
- **PROD_INVENTORY_IMAGE_ID:** `sha256:e7a8fdcea8e39f2cb26df3b47ad742630c29630a7f35b98fb97cdc25fceacbaa`
- **PROD_REPAIRS_IMAGE_ID:** `sha256:f91c41abe2820a5b70f166340d31e65a8a7889be731a37416233a41c394e3c3a`

## Stage11D Features
- **LINKED_SALE_URL_FIXED:** true (`/sales/{sale_id}` canonical link verified in template, proxy normalizer prevents duplicate `/sales/sales/` path prefixes)
- **READY_FROM_ALL_ACTIVE_STATES:** true (status `ready` is reachable from `received`, `diagnostics`, `waiting_customer`, `waiting_parts`, `in_repair`, `unrepairable`)
- **READY_PRICE_EDIT_AVAILABLE:** true (price field displayed on all active stages; allows 0 ₽ for warranty/free repair)
- **OWNER_BULK_DELETE_UI:** true (owner certificate sees row checkboxes, select-all control, selection counter, and red bulk delete action bar with confirmation modal)
- **OWNER_BULK_DELETE_API:** true (authenticated owner certificate requests successfully authorized; non-owner requests rejected with 403)

## Security
- **NON_OWNER_UI_HIDDEN:** true (regular user/employee certificate does not see checkboxes or bulk action bar in `/sales` or `/repairs/repairs`)
- **NON_OWNER_API_403:** true (`POST /sales/bulk-delete` and `POST /repairs/bulk-delete` without owner role return HTTP 403 Forbidden)
- **SPOOFED_OWNER_HEADER_403:** true (sending `X-Auth-Is-Owner: 1` with non-owner certificate identity is sanitized and overwritten by gateway/reverse-proxy, resulting in HTTP 403 Forbidden)
- **MTLS_REQUIRED:** true (unauthenticated requests rejected at Nginx gateway with HTTP 403)
- **INTERNAL_PORTS_PRIVATE:** true (only ports 80/443 exposed on public host; core, admin-shell, inventory-sales, repairs, avito have no host port bindings)

## Delete Invariants
- **ACTIVE_SALE_DELETE_STOCK_RESTORED_ONCE:** true (deleting completed sale restores sold product quantity exactly once and switches status back to `in_stock`; cascaded deletion of sale_items, sale_revisions, stock_movements, avito_post_sale_tasks)
- **CANCELED_SALE_NO_DOUBLE_RESTORE:** true (deleting a sale with status `canceled` or `cancelled` skips inventory restoration to avoid double-crediting stock)
- **REPAIR_LINKED_SALE_DELETE_COHERENT:** true (deleting a repair-linked sale resets the surviving repair order from `issued` to coherent `ready` state, clears `sale_id`, `final_amount`, `payment_method`, `warranty_days`, `issued_at`, `closed_at`, logs `RepairStatusHistory` event and audit log)
- **REPAIR_WITH_ACTIVE_SALE_NOT_SILENTLY_ORPHANED:** true (attempting to delete a repair order with an active linked sale is rejected with HTTP 400 and explicit guidance: `Невозможно удалить ремонт {number}: сначала удалите связанную продажу №{sale_id}`)
- **MULTI_DELETE_ATOMIC_OR_EXPLICIT:** true (pre-validation phase verifies all items in bulk request; if any repair has an active linked sale, zero items are deleted and all blocking records are reported)
- **PERMANENT_DELETE_AUDIT:** true (audit event with action `permanent_delete`, entity type, entity ID, actor, and summary comments recorded in immutable `AuditLog` table)

## Tests
- **STAGE11A:** 15/15 passed (`tests/test_stage11a_sale_corrections.py`)
- **STAGE11B:** 16/16 passed (`tests/test_stage11b_repair_issue.py`)
- **STAGE11D:** 10/10 passed (`tests/test_stage11d_owner_bulk_delete.py`)
- **TARGETED_SUITE:** 164/164 passed (`scripts/run_targeted_tests.py`: 27 core + 28 admin-shell + 109 root)
- **SCHEMA_GUARD:** SAFE (`scripts/db_schema_contract.py verify` & `compare`)

## Production
- **PRODUCTION_VDS:** 144.31.15.88
- **LEGACY_VDS_TOUCHED:** false
- **REAL_BUSINESS_RECORDS_DELETED_DURING_TEST:** false
- **BUSINESS_COUNTS_UNCHANGED_BY_AUDIT:** true (241 products, 4 sales, 1 repair order, 237 photos, 237 listings, 3 avito post-sale tasks intact)
- **PROD_6_SERVICES_HEALTHY:** true (core, admin-shell, inventory-sales, repairs, gateway, avito all Up & healthy)

## Safety & Backup
- **Pre-Update Safety Backup:** `/srv/technoreboot/data/backups/TECHNOREBOOT_BACKUP_2026-09-17_110805.zip`
- **SHA256:** `061b139bed42b56c228500a58cdc3352aa41a6b0dcc46551e778e9640de9e713`
- **Size:** 8,886,846 bytes

FINAL_STATUS:
TECHNOREBOOT_STAGE11D_R1_VERIFIED
