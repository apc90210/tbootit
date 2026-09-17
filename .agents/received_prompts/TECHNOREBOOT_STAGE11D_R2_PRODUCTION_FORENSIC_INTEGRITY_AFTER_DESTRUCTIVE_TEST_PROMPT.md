# TECHNOREBOOT — Stage 11D-R2 PRODUCTION CORRECTIVE
## Forensic integrity audit after accidental destructive production test

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`  
**Canonical production VDS:** `144.31.15.88`  
**Legacy VDS:** `144.31.50.134` — DO NOT TOUCH

# 0. INCIDENT

Stage11D-R1 is NOT accepted as cleanly completed.

The execution trace shows that a REAL production request was sent:

```text
POST https://144.31.15.88/repairs/repairs/bulk-delete
{"repair_ids": [1]}
```

After that, recovery commands were executed against the production database, including restoration of:

```text
repair_orders
repair_status_history
```

from backup:

```text
/srv/technoreboot/data/backups/TECHNOREBOOT_BACKUP_2026-09-17_110805.zip
```

and later this direct SQL was executed:

```sql
UPDATE repair_orders
SET sale_id = NULL
WHERE id = 1
AND (SELECT COUNT(*) FROM sales WHERE id = repair_orders.sale_id) = 0;
```

Therefore the final Stage11D-R1 claim:

```text
REAL_BUSINESS_RECORDS_DELETED_DURING_TEST: false
```

is contradicted by the execution trace.

This stage is a narrow forensic/data-integrity corrective stage.

Do NOT add new features.
Do NOT delete any real records.
Do NOT run bulk-delete against real production IDs again.

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE11D_R2_PRODUCTION_FORENSIC_INTEGRITY_AFTER_DESTRUCTIVE_TEST_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE11D_R2_PRODUCTION_FORENSIC_INTEGRITY_AFTER_DESTRUCTIVE_TEST_PROMPT.md`

# 2. IMMEDIATE SAFETY SNAPSHOT

Before any investigation or correction:

Create a NEW current production backup:

```text
CURRENT_POST_INCIDENT_BACKUP
```

Verify:
- SHA256;
- manifest;
- SQLite quick_check.

This protects the current post-incident state before any forensic comparison.

Do NOT overwrite or delete the existing pre-test backup:

```text
TECHNOREBOOT_BACKUP_2026-09-17_110805.zip
```

# 3. SOURCE OF TRUTH FOR FORENSIC COMPARISON

Use the pre-destructive-test backup:

```text
/srv/technoreboot/data/backups/TECHNOREBOOT_BACKUP_2026-09-17_110805.zip
```

as the primary PRE-INCIDENT reference.

Important:
Do not assume the whole current DB should equal the backup byte-for-byte, because legitimate production writes might have occurred after the backup.

Compare business rows and timestamps carefully.

# 4. DETERMINE EXACT RESULT OF THE REAL BULK-DELETE CALL

Recover from logs if possible:

```text
HTTP status
response body
timestamp
actor
repair_ids
```

for the real request:

```text
repair_ids=[1]
```

Determine exactly whether:
- repair #1 was actually deleted;
- repair history was deleted;
- any linked sale or sale linkage was changed;
- any AuditLog/permanent_delete entry was written;
- any other linked rows changed.

Return:

```text
REAL_DELETE_REQUEST_STATUS:
REAL_REPAIR_1_WAS_DELETED:
REAL_REPAIR_HISTORY_WAS_DELETED:
REAL_LINKED_SALE_CHANGED:
REAL_AUDIT_LOG_WRITTEN:
```

Do not hide or reclassify this as a “non-destructive test”.

# 5. FORENSIC ROW-LEVEL COMPARISON

Compare PRE-INCIDENT backup vs CURRENT production for all rows relevant to repair #1.

At minimum inspect:

```text
repair_orders WHERE id=1
repair_status_history WHERE repair_order_id=1
sales related by repair sale_id
sales WHERE source_type='repair' AND source_id=1
sale_items for related sale(s)
sale_revisions for related sale(s)
audit_logs / AuditLog entries for repair #1 and related sale(s)
stock_movements if any linked sale included stock
avito_post_sale_tasks if relevant
```

Use actual table/column names.

For each relevant row report:

```text
PRE_INCIDENT
CURRENT
DIFF
```

Do not compare only row counts.

# 6. CHECK FOR COLLATERAL DAMAGE FROM RESTORE SCRIPT

The trace shows a restore script that performed:

```text
DELETE FROM repair_orders
INSERT all repair_orders from backup

DELETE FROM repair_status_history
INSERT all repair_status_history from backup
```

This could theoretically overwrite legitimate repair changes that happened between backup creation and restore.

Therefore compare ALL repair-related rows, not only repair #1:

```text
repair_orders
repair_status_history
```

between:
- pre-incident backup;
- current production.

Identify any records with:
- changed timestamps;
- changed status;
- changed amount/payment/warranty;
- changed sale_id;
- missing/new history rows.

If any legitimate post-backup production repair activity was overwritten, reconstruct it only from trustworthy evidence:
- application logs;
- audit logs;
- request logs;
- later backups;
- current related sales.

Do not invent values.

# 7. SALE_ID NULL DIRECT SQL AUDIT

Explicitly determine:

1. What was `repair_orders.id=1.sale_id` in the PRE-INCIDENT backup?
2. Did that referenced sale exist in the PRE-INCIDENT backup?
3. Does it exist CURRENTLY?
4. Why was `sale_id=NULL` applied?
5. Is current `sale_id=NULL` logically correct or was a valid relationship lost?

Return:

```text
REPAIR_1_PRE_SALE_ID:
REPAIR_1_PRE_REFERENCED_SALE_EXISTED:
REPAIR_1_CURRENT_SALE_ID:
REPAIR_1_CURRENT_LINK_IS_CORRECT:
```

If the backup itself contained an orphan `sale_id`, document that explicitly.
If a valid sale relationship was lost, restore it safely.

# 8. AUDIT LOG CONSISTENCY

If a `permanent_delete` audit row was created by the accidental production test, DO NOT silently delete history.

Preserve it and append a compensating audit event, e.g.:

```text
action = production_test_restore
comment = real repair deletion was performed during Stage11D-R1 verification and restored from pre-test backup
```

Include:
- affected entity;
- original delete timestamp;
- restore/correction timestamp;
- actor/process.

If no persistent audit subsystem supports this safely, document the limitation.

# 9. CORRECTION RULE

Only change production data if forensic comparison proves a mismatch caused by Stage11D-R1.

Allowed corrections:
- restore exact pre-incident repair row/history values;
- restore a proven valid relation;
- repair a proven accidental null;
- append compensating audit record.

Forbidden:
- broad DB restore;
- replacing current DB with backup;
- replacing all current business data;
- touching unrelated newer production activity;
- deleting audit evidence.

All corrections must be narrow and transaction-safe.

# 10. VERIFY GLOBAL BUSINESS INTEGRITY

After forensic check/correction verify:

```text
PRAGMA quick_check = ok
PRAGMA foreign_key_check = no violations
```

Record counts:

```text
products
sales
repair_orders
repair_status_history
product_photos
product_external_listings
avito_post_sale_tasks
sale_revisions
audit_log
storage files
```

Also verify no orphan relationships:

```text
repair_orders.sale_id -> existing sales.id or NULL
repair-generated sales -> valid repair source when source_type='repair'
sale_items -> valid sale/product as applicable
repair_status_history -> valid repair_order
```

# 11. RUNTIME / FEATURE VERIFICATION

Do NOT rebuild unless code changed in this corrective stage.

Verify current production runtime remains:

```text
all 6 containers healthy
mTLS required
internal ports private
Stage11D owner anti-spoof fix active
bulk-delete linked repair protection active
```

Do NOT invoke destructive endpoints with real IDs.

Use automated LOCAL tests and read-only production checks.

# 12. FIX THE REPORTING RECORD

Update the Stage11D documentation truthfully.

Do not rewrite command history.

The corrected record must state that:
- a real production bulk-delete request was executed during verification;
- a production repair record/history required restoration;
- forensic verification was performed;
- final data integrity result.

The old false statement:

```text
REAL_BUSINESS_RECORDS_DELETED_DURING_TEST: false
```

must not remain as the current canonical status.

Use instead something like:

```text
REAL_BUSINESS_RECORDS_MUTATED_DURING_STAGE11D_R1: true
INCIDENT_RESTORED_AND_VERIFIED: <true/false>
```

# 13. DOCUMENTATION

Create:

```text
reports/stage11d_r2_production_forensic_integrity_after_destructive_test_report.md
```

Update:

```text
docs/production_status.md
logs/<current-date>.md
```

Preserve historical reports; add a correction/addendum rather than silently deleting evidence.

# 14. GIT

Commit only:
- forensic scripts;
- report/docs/log addendum;
- narrowly required code fix if one is discovered.

Never commit:
- production DB;
- backups;
- secrets;
- private keys.

Push main.

# 15. FINAL REPORT CONTRACT

Return exactly:

```text
# Stage 11D-R2 — Production Forensic Integrity Audit

## Incident
REAL_DELETE_REQUEST_STATUS:
REAL_REPAIR_1_WAS_DELETED:
REAL_REPAIR_HISTORY_WAS_DELETED:
REAL_LINKED_SALE_CHANGED:
REAL_AUDIT_LOG_WRITTEN:

## Pre/Post Snapshot
PRE_INCIDENT_BACKUP:
PRE_INCIDENT_BACKUP_SHA256:
POST_INCIDENT_BACKUP:
POST_INCIDENT_BACKUP_SHA256:

## Repair #1
REPAIR_1_PRE_STATE:
REPAIR_1_CURRENT_STATE:
REPAIR_1_PRE_SALE_ID:
REPAIR_1_PRE_REFERENCED_SALE_EXISTED:
REPAIR_1_CURRENT_SALE_ID:
REPAIR_1_CURRENT_LINK_IS_CORRECT:
REPAIR_1_HISTORY_MATCH:

## Collateral Audit
ALL_REPAIR_ROWS_COMPARED:
ALL_REPAIR_HISTORY_ROWS_COMPARED:
LEGITIMATE_POST_BACKUP_ACTIVITY_LOST:
COLLATERAL_DAMAGE_FOUND:
COLLATERAL_DAMAGE_DETAILS:

## Corrections
DATA_CORRECTION_REQUIRED:
DATA_CORRECTION_APPLIED:
CORRECTION_SCOPE:
COMPENSATING_AUDIT_EVENT_WRITTEN:

## Integrity
DB_QUICK_CHECK:
FOREIGN_KEY_CHECK:
ORPHAN_REPAIR_SALE_LINKS:
ORPHAN_REPAIR_HISTORY:
BUSINESS_COUNTS_VALID:
STORAGE_VALID:

## Runtime
PROD_6_SERVICES_HEALTHY:
MTLS_REQUIRED:
OWNER_HEADER_ANTI_SPOOF_ACTIVE:
LINKED_REPAIR_DELETE_PROTECTION_ACTIVE:

## Canonical Record
REAL_BUSINESS_RECORDS_MUTATED_DURING_STAGE11D_R1: true
INCIDENT_RESTORED_AND_VERIFIED:

FINAL_STATUS:
<one of>
TECHNOREBOOT_STAGE11D_R2_INCIDENT_FULLY_RESTORED_VERIFIED
BLOCKED_MANUAL_DATA_RECONCILIATION_REQUIRED
```

# 16. STOP

STOP after forensic verification and only necessary narrow correction.

Do not run any further destructive production tests.
