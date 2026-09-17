# TECHNOREBOOT — Stage 11D-R1 PRODUCTION AUDIT / CORRECTIVE
## Verify real production runtime after Stage11D + hard-delete relational invariants

**Project:** ТехноРебут  
**LOCAL workspace:** `C:\tbootit`  
**Canonical production VDS:** `144.31.15.88`  
**Legacy VDS:** `144.31.50.134` — DO NOT TOUCH

# 0. WHY THIS REVISION EXISTS

Stage11D report claims that three owner-requested fixes are already synchronized to production:

1. fixed linked-sale URL from repair;
2. `Готов` is reachable from any active repair stage with editable price;
3. OWNER-only bulk permanent deletion for Sales and Repairs.

But the supplied execution trace ends with:

```text
git pull origin main
```

on production and does not prove that production Docker images/containers were rebuilt/recreated from the new code.

A Git worktree update is NOT sufficient evidence when production containers run code baked into images.

Also audit the relational invariants of permanent deletion so we do not leave impossible business states.

Do not add new product features in this revision.

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE11D_R1_PRODUCTION_RUNTIME_VERIFY_AND_DELETE_INVARIANTS_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE11D_R1_PRODUCTION_RUNTIME_VERIFY_AND_DELETE_INVARIANTS_PROMPT.md`

# 2. PREFLIGHT

LOCAL:

```text
git status
git branch --show-current
git rev-parse HEAD
```

PRODUCTION:

```text
ssh root@144.31.15.88
cd /srv/technoreboot/app
git status
git rev-parse HEAD
docker ps
docker inspect relevant containers
```

Record:

```text
LOCAL_HEAD:
PROD_WORKTREE_HEAD:
PROD_CORE_IMAGE_ID:
PROD_ADMIN_IMAGE_ID:
PROD_INVENTORY_IMAGE_ID:
PROD_REPAIRS_IMAGE_ID:
PROD_CONTAINER_CREATED_TIMES:
```

Do NOT touch the legacy VDS.

# 3. PROVE WHAT CODE IS ACTUALLY RUNNING

Do not infer runtime version from `/srv/technoreboot/app/.git`.

Prove the live containers include Stage11D behavior.

At minimum test production runtime through actual HTTP/mTLS:

## Linked sale URL
Open/read repair detail containing linked sale and verify generated href is canonical:

```text
/sales/<id>
```

not:

```text
/sales/sales/<id>
```

## Repair Ready flow
Verify the live production repair page/API exposes `ready` from all intended active states:

```text
received
waiting_customer
waiting_parts
in_repair/current equivalent
unrepairable
```

and the price field is available/required as specified.

Do not mutate real repair records for this proof.

## OWNER bulk-delete UI/API
Verify live runtime:
- OWNER sees row checkboxes and permanent-delete control;
- normal USER does not;
- normal USER POST to bulk-delete returns 403;
- endpoints exist in the running Core.

Use safe read-only/template/API inspection where possible.
Do not delete real records.

Record:

```text
LIVE_STAGE11D_LINK_FIX_PRESENT:
LIVE_STAGE11D_READY_FLOW_PRESENT:
LIVE_STAGE11D_OWNER_BULK_DELETE_PRESENT:
```

# 4. IF RUNTIME IS STALE — DEPLOY IT PROPERLY

If worktree contains Stage11D but live containers do not:

1. create/verify current production backup/checkpoint;
2. use existing production compose file;
3. rebuild affected services;
4. recreate containers safely;
5. keep existing production DB/media;
6. do NOT run unnecessary migrations.

Typical affected services:

```text
core
admin-shell
inventory-sales
repairs
```

Avito/gateway only if dependency/config actually changed.

After deployment verify all six services are healthy.

# 5. SECURITY AUDIT — OWNER HEADER

Audit the full path of:

```text
X-Auth-Is-Owner
```

Requirement:
A client must NOT be able to grant themselves owner privileges by sending this HTTP header manually.

Verify:
- gateway derives/overwrites owner identity from authenticated mTLS certificate;
- client-supplied `X-Auth-Is-Owner` cannot survive as trusted owner state;
- internal modules only trust a header that the trusted gateway/admin-shell sets;
- Core/internal ports remain non-public.

Add an automated test for spoofing if not already present:

```text
non-owner certificate + X-Auth-Is-Owner: 1
=> still HTTP 403
```

If spoofing is possible, fix immediately.

# 6. HARD DELETE — BUSINESS INVARIANT AUDIT

Permanent deletion is intentionally OWNER-only, but it must not leave contradictory surviving entities.

Audit actual code and tests for these cases.

## A. Delete ordinary completed sale
Expected:
- sale deleted;
- sale_items deleted;
- sale_revisions deleted;
- related post-sale/manual tasks handled consistently;
- stock restored exactly once for physical items;
- no negative/double quantity.

## B. Delete canceled sale
Do NOT restore stock twice if cancellation already restored it.

## C. Delete repair-linked sale
The surviving RepairOrder must NOT remain in an impossible state like:

```text
status = issued
sale_id = NULL
```

while still semantically claiming a completed paid issue.

Choose the minimal invariant-preserving behavior based on current model.

Preferred behavior:
- if deleting the linked sale only, reset the repair to a coherent pre-payment state (`ready`) and clear issue-payment linkage/fields that exist only because of issue;
- preserve historical repair text/status audit as appropriate or add an explicit OWNER deletion/reset audit event if the retained repair supports history.

Do not fabricate a new sale.

## D. Delete repair that has a linked sale
Do NOT silently convert its linked repair sale into an unexplained ordinary sale by merely nulling `source_type/source_id`.

Use one explicit safe rule:

Preferred:
- block deletion of a repair with a linked active sale and return a clear message:
  `Сначала удалите связанную продажу №...`

This keeps financial deletion explicit and prevents accidental revenue deletion.

If the existing UX already has an explicit checked/confirmed "delete linked sale too" option, that may be retained, but it must be obvious and atomic.

## E. Multiple selected rows
Whole bulk operation should be atomic where practical:
- validation first;
- if one linked/ineligible record blocks the operation, return a clear list;
- do not partially delete an arbitrary subset unless UI explicitly reports per-row outcomes.

# 7. DELETE AUDIT

The Owner requested permanent deletion, so business rows may be removed.

Nevertheless preserve a minimal immutable operational audit outside the deleted business entity tables using the project's existing audit/event/log architecture if available.

At minimum record:

```text
timestamp
actor = owner
entity type
entity id/number
action = permanent_delete
linked entity impact
```

Do not store sensitive full snapshots unnecessarily.

If no canonical persistent audit subsystem exists, document the limitation instead of inventing a large new subsystem in this revision.

# 8. TESTS

Add/verify tests for:

1. non-owner cannot see bulk controls;
2. non-owner API bulk delete => 403;
3. spoofed `X-Auth-Is-Owner: 1` with non-owner identity => 403;
4. owner ordinary sale delete restores stock once;
5. canceled sale delete does not restore stock twice;
6. repair-linked sale delete leaves repair in coherent state;
7. repair with linked active sale cannot be silently orphaned;
8. multi-delete validation does not cause unintended partial corruption;
9. linked repair -> sale URL canonical;
10. Ready transition availability from all intended active statuses;
11. Ready price validation including 0 ₽;
12. existing Stage11A/11B regression tests remain green.

Run:
- Stage11A tests;
- Stage11B tests;
- Stage11D tests;
- official targeted suite;
- Schema Guard.

# 9. PRODUCTION DATA SAFETY

Do NOT:
- replace production DB;
- copy LOCAL DB/media to production;
- delete any real sale/repair during smoke testing;
- touch legacy VDS.

Before any runtime redeploy:
- fresh backup/checkpoint if one is not already current for this change.

Production smoke must be non-destructive.

# 10. FINAL PRODUCTION VERIFICATION

On `144.31.15.88` verify:

```text
all 6 containers healthy
mTLS still required
internal ports private
root/products/sales/repairs/avito/help HTTP 200 with OWNER cert
USER cannot bulk-delete
OWNER UI contains bulk-delete
linked sale URL canonical
Ready workflow present
```

Record actual running image/container IDs after any rebuild.

# 11. DOCUMENTATION

Create:

```text
reports/stage11d_r1_production_runtime_verify_and_delete_invariants_report.md
```

Update:

```text
docs/production_status.md
logs/<current-date>.md
```

Do not rewrite historical reports.

# 12. GIT

Commit tracked code/tests/docs only.

Never commit:
- DB;
- media;
- backups;
- credentials;
- private keys.

Push `main`.

# 13. FINAL REPORT CONTRACT

Return:

```text
# Stage 11D-R1 — Runtime Verification + Delete Invariants

## Runtime Proof
LOCAL_HEAD:
PROD_WORKTREE_HEAD:
PROD_RUNNING_CODE_STAGE11D_CONFIRMED:
REBUILD_REQUIRED:
REBUILD_PERFORMED:
PROD_CORE_IMAGE_ID:
PROD_ADMIN_IMAGE_ID:
PROD_INVENTORY_IMAGE_ID:
PROD_REPAIRS_IMAGE_ID:

## Stage11D Features
LINKED_SALE_URL_FIXED:
READY_FROM_ALL_ACTIVE_STATES:
READY_PRICE_EDIT_AVAILABLE:
OWNER_BULK_DELETE_UI:
OWNER_BULK_DELETE_API:

## Security
NON_OWNER_UI_HIDDEN:
NON_OWNER_API_403:
SPOOFED_OWNER_HEADER_403:
MTLS_REQUIRED:
INTERNAL_PORTS_PRIVATE:

## Delete Invariants
ACTIVE_SALE_DELETE_STOCK_RESTORED_ONCE:
CANCELED_SALE_NO_DOUBLE_RESTORE:
REPAIR_LINKED_SALE_DELETE_COHERENT:
REPAIR_WITH_ACTIVE_SALE_NOT_SILENTLY_ORPHANED:
MULTI_DELETE_ATOMIC_OR_EXPLICIT:
PERMANENT_DELETE_AUDIT:

## Tests
STAGE11A:
STAGE11B:
STAGE11D:
TARGETED_SUITE:
SCHEMA_GUARD:

## Production
PRODUCTION_VDS: 144.31.15.88
LEGACY_VDS_TOUCHED: false
REAL_BUSINESS_RECORDS_DELETED_DURING_TEST: false
BUSINESS_COUNTS_UNCHANGED_BY_AUDIT: true
PROD_6_SERVICES_HEALTHY:

FINAL_STATUS:
TECHNOREBOOT_STAGE11D_R1_VERIFIED
```

# 14. STOP

STOP after verification/fix and non-destructive production smoke.

Wait for Owner/supervisor acceptance.
