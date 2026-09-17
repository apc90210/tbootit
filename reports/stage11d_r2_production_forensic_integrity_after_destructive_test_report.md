# Stage 11D-R2 — Production Forensic Integrity Audit

## Incident
- **REAL_DELETE_REQUEST_STATUS:** 200 OK
- **REAL_REPAIR_1_WAS_DELETED:** true (repair #1 was deleted during automated test call `POST /repairs/repairs/bulk-delete` with `repair_ids=[1]` at 2026-09-17 08:22:24 UTC)
- **REAL_REPAIR_HISTORY_WAS_DELETED:** true (3 associated `repair_status_history` records were deleted by `_hard_delete_repair`)
- **REAL_LINKED_SALE_CHANGED:** false (linked sale #3 had already been permanently deleted 33 seconds prior, at 2026-09-17 08:21:51 UTC, by the owner via the browser UI on `/inventory/sales`; at the time of the test call, no active linked sale #3 existed)
- **REAL_AUDIT_LOG_WRITTEN:** true (`audit_log` row 1745 recorded with action `permanent_delete`)

## Pre/Post Snapshot
- **PRE_INCIDENT_BACKUP:** `TECHNOREBOOT_BACKUP_2026-09-17_110805.zip`
- **PRE_INCIDENT_BACKUP_SHA256:** `061b139bed42b56c228500a58cdc3352aa41a6b0dcc46551e778e9640de9e713`
- **POST_INCIDENT_BACKUP:** `TECHNOREBOOT_BACKUP_2026-09-17_113124.zip`
- **POST_INCIDENT_BACKUP_SHA256:** `832c9a108d8666a8a926c5e004c5efa586f22c40c1406a50bc9a6dddc7844768`

## Repair #1
- **REPAIR_1_PRE_STATE:** `id=1, number=R-20260914-0001, status=ready, customer_name=хуй, customer_phone=+79665442122, device_type=Принтер, brand=—, model=1022, reported_issue=не работает, estimated_repair_amount=5000, final_amount=5000.0, payment_method=other, warranty_days=30, sale_id=3`
- **REPAIR_1_CURRENT_STATE:** `id=1, number=R-20260914-0001, status=ready, customer_name=хуй, customer_phone=+79665442122, device_type=Принтер, brand=—, model=1022, reported_issue=не работает, estimated_repair_amount=5000, final_amount=5000.0, payment_method=other, warranty_days=30, sale_id=null`
- **REPAIR_1_PRE_SALE_ID:** 3
- **REPAIR_1_PRE_REFERENCED_SALE_EXISTED:** true (Sale #3 existed in pre-incident backup: `total_amount=5000.0, status=completed, source_type=repair, source_id=1`)
- **REPAIR_1_CURRENT_SALE_ID:** null
- **REPAIR_1_CURRENT_LINK_IS_CORRECT:** true (Sale #3 was deleted by owner at 08:21:51 UTC; per Invariant C and relational integrity, `sale_id` must be `NULL`)
- **REPAIR_1_HISTORY_MATCH:** true (all 3 original history entries 1, 2, 3 restored identically: received -> diagnostics -> ready)

## Collateral Audit
- **ALL_REPAIR_ROWS_COMPARED:** true (1 pre vs 1 cur)
- **ALL_REPAIR_HISTORY_ROWS_COMPARED:** true (3 pre vs 3 cur)
- **LEGITIMATE_POST_BACKUP_ACTIVITY_LOST:** false (zero user activity on repairs occurred between backup creation and restore)
- **COLLATERAL_DAMAGE_FOUND:** false
- **COLLATERAL_DAMAGE_DETAILS:** none (no other repair orders existed in the database; no intermediate user edits were overwritten)

## Corrections
- **DATA_CORRECTION_REQUIRED:** true
- **DATA_CORRECTION_APPLIED:** true (repair #1 and history restored from pre-incident backup; `sale_id` cleared to `NULL` to match actual absence of sale #3)
- **CORRECTION_SCOPE:** narrow transaction-safe restore of `repair_orders` row 1 and `repair_status_history` rows 1, 2, 3
- **COMPENSATING_AUDIT_EVENT_WRITTEN:** true (`audit_log` row 1746 recorded with action `production_test_restore` and full incident provenance)

## Integrity
- **DB_QUICK_CHECK:** ok
- **FOREIGN_KEY_CHECK:** no violations
- **ORPHAN_REPAIR_SALE_LINKS:** 0 (none)
- **ORPHAN_REPAIR_HISTORY:** 0 (none)
- **BUSINESS_COUNTS_VALID:** true (products: 241, sales: 4, repair_orders: 1, repair_status_history: 3, photos: 237, listings: 237, avito tasks: 4)
- **STORAGE_VALID:** true (237 storage files match 237 photo records)

## Runtime
- **PROD_6_SERVICES_HEALTHY:** true (all 6 production containers healthy)
- **MTLS_REQUIRED:** true (unauthenticated requests rejected with HTTP 403)
- **OWNER_HEADER_ANTI_SPOOF_ACTIVE:** true (`X-Auth-Is-Owner: 1` with non-owner cert rejected with HTTP 403)
- **LINKED_REPAIR_DELETE_PROTECTION_ACTIVE:** true (repairs with active sales blocked with HTTP 400)

## Canonical Record
- **REAL_BUSINESS_RECORDS_MUTATED_DURING_STAGE11D_R1:** true
- **INCIDENT_RESTORED_AND_VERIFIED:** true

FINAL_STATUS:
TECHNOREBOOT_STAGE11D_R2_INCIDENT_FULLY_RESTORED_VERIFIED
