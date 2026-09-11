# TECHNOREBOOT — Stage 08A-R1
## Full Owner workflow audit and release gap list

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 08A-R1 — Full Owner Workflow Audit and Release Gap List`

# 0. EXECUTION CONTRACT

Stage07E disaster recovery is accepted.

Current system has proven:
- web backup/restore;
- fresh-server disaster recovery from Git + backup ZIP;
- OWNER mTLS continuity;
- Avito bulk import and same-ID reactivation;
- product editor / JSON import-export;
- inventory and sales;
- repairs module;
- reports;
- batch operations.

Before production hardening and VDS deployment, perform one complete end-to-end audit of the real Owner workflows.

This stage is primarily AUDIT + narrow corrective fixes only.

Do NOT redesign architecture.
Do NOT deploy VDS.
Do NOT change business rules unless a real workflow is broken.
Do NOT invent large new features.
Do NOT reset/replace live DB.
Normal Owner acceptance is browser-only.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08A_R1_FULL_OWNER_WORKFLOW_AUDIT_AND_RELEASE_GAP_LIST_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08A_R1_FULL_OWNER_WORKFLOW_AUDIT_AND_RELEASE_GAP_LIST_PROMPT.md`

# 1. PREFLIGHT

Record:
- branch;
- HEAD;
- git status;
- docker compose status;
- live gateway URL;
- current product/sale/repair counts;
- current extension version;
- current backup format version.

Preserve all existing business data.

Any synthetic test data created by this stage must be uniquely identified and removed in `finally`.

Required invariant:

```text
REAL_PRODUCT_ID_SET_AFTER == REAL_PRODUCT_ID_SET_BEFORE
REAL_SALE_ID_SET_AFTER == REAL_SALE_ID_SET_BEFORE
REAL_REPAIR_ID_SET_AFTER == REAL_REPAIR_ID_SET_BEFORE
```

unless the workflow intentionally creates a specifically documented temporary record that is then removed safely.

# 2. AUDIT SCOPE

Audit the following Owner workflows through the actual Gateway/API/UI stack.

## A. Authentication / roles
- OWNER certificate login;
- no-cert rejection;
- OWNER-only `/backups`;
- OWNER-only `/certificates`;
- USER access to normal allowed product workflows;
- USER forbidden from OWNER-only pages.

## B. Product catalog
- `/inventory/products` loads;
- search works;
- quick filters work;
- product detail opens;
- create manual product;
- edit title/price/description;
- edit category characteristics;
- barcode/SKU retained;
- photo upload;
- main photo display;
- deletion/removal behavior only if already supported and safe.

## C. JSON product workflow
- `/products/json`;
- copy/download AI prompt;
- import pasted JSON;
- import file;
- update existing by ID;
- create new without ID;
- selected export;
- all export;
- created/updated result links open correct product;
- no fake zero-result summaries.

## D. Avito extension
- extension download page;
- version consistent;
- pairing;
- own-listings detection;
- page count;
- `Фото найдено: X из N`;
- current-page import;
- all-pages import logic regression;
- same Avito ID updates same Product;
- sold/archive/0 + deliberate active import -> same Product in_stock/store/1;
- repeat import does not increase quantity;
- low-res thumbnail does not overwrite richer/manual gallery;
- per-listing enrichment route still works.

Use sanitized fixture/isolated test where browser automation of real Avito is not possible, but distinguish synthetic evidence from Owner-real evidence.

## E. Batch inventory operations
- checkbox selection;
- Shift range;
- select all shown;
- combined status/location update;
- no-op validation;
- batch price tags 58×40;
- batch add to sale.

## F. Sales
- create sale;
- multiple items;
- payment method handling;
- receipt/detail;
- stock decrement;
- unique item reaching zero -> sold/archive/0;
- canceled sale restores stock;
- reissue/supersede behavior;
- canceled/superseded sales excluded correctly from revenue;
- reports remain financially consistent.

## G. Reports
- Today;
- Week;
- Year;
- explicit date range if supported;
- payment breakdown;
- canceled sales excluded;
- totals match source sales data.

## H. Repairs
Audit real current repair workflow end-to-end:
- repair list;
- create repair;
- customer/device fields;
- status transitions;
- price/cost fields;
- edit/update;
- close/complete;
- reopen/cancel if supported;
- search/filter;
- repair detail;
- any printable/customer-facing document if currently supported.

Do NOT create missing features in this stage; list real gaps separately unless a tiny fix is required for a broken existing workflow.

## I. Backup / restore UI
- `/backups` loads;
- create/download backup;
- upload validation path;
- normal web restore still preserves live auth;
- do NOT perform destructive restore of current live data during audit unless isolated.

## J. Certificates
- list certificates;
- OWNER issuance workflow page;
- USER certificate issuance workflow if supported;
- revoke behavior;
- revoked access rejected.

# 3. UI / NAVIGATION AUDIT

For all primary pages check:
- navigation links work;
- no 404/422/500;
- no stale links;
- no route redirects to wrong port/scheme;
- Russian UI remains coherent;
- obvious duplicate/obsolete controls are absent;
- dangerous actions have reasonable confirmation where already designed;
- mobile perfection is NOT required, but desktop layout must be usable.

Record every broken link or route.

# 4. DATA CONSISTENCY AUDIT

Check:
- one Avito ID -> one Product;
- no duplicate SKU where uniqueness required;
- no product_photos rows pointing to missing local files;
- no sale items pointing to missing products where schema expects product;
- no orphan critical external listing links;
- sold/archive/quantity relationships are internally consistent;
- local-only products without Avito ID remain valid;
- completed/canceled/superseded/reissued sale statuses are internally consistent;
- repair records retain referential integrity.

Do NOT broadly clean data in this stage.
List ambiguous anomalies separately.

# 5. LOGGING / ERROR HANDLING AUDIT

Trigger only safe failures:
- invalid JSON;
- duplicate/invalid barcode;
- malformed Avito batch payload;
- unauthorized OWNER route;
- missing product ID;
- invalid sale operation.

Verify:
- user sees understandable error;
- server does not expose secrets/tracebacks;
- logs contain enough context to diagnose.

# 6. NARROW FIX POLICY

If a workflow is broken by a small localized bug:
- fix it;
- add regression test;
- re-run affected workflow.

If fixing requires a new subsystem, schema redesign, or major feature:
- DO NOT implement;
- put it in Release Gap List with severity.

Severity:

```text
P0 = blocks production / risks data loss/security
P1 = core workflow broken
P2 = important usability/operational problem
P3 = polish/deferred
```

# 7. REQUIRED RELEASE GAP LIST

Create:

`reports/release_gap_list.md`

Each item:

```text
ID:
SEVERITY:
MODULE:
WORKFLOW:
PROBLEM:
BUSINESS_IMPACT:
REPRODUCTION:
RECOMMENDED_STAGE:
BLOCKS_VDS_DEPLOYMENT: true/false
```

At the end provide:

```text
P0_COUNT:
P1_COUNT:
P2_COUNT:
P3_COUNT:
VDS_BLOCKERS:
```

# 8. REQUIRED TESTS

Run full relevant suites:
- core;
- inventory-sales-module;
- admin-shell;
- repairs-module;
- avito-module;
- Chrome extension tests where available.

Also run focused live mTLS smoke tests through Gateway.

Report exact totals.

# 9. OWNER MANUAL CHECK

Prepare a browser-only checklist, maximum 12 practical steps.

Do not ask Owner to test every edge case.

Manual acceptance should cover only the most important real workflows:
1. product list/detail/edit;
2. one Avito import/re-import;
3. one sale and cancel if practical;
4. reports;
5. repairs;
6. backup page.

If automated evidence fully covers a destructive path, do not ask Owner to repeat destructive actions.

# 10. DOCUMENTATION

Create/update:

`docs/stage08a_r1_full_owner_workflow_audit.md`

`reports/stage08a_r1_full_owner_workflow_audit_report.md`

`reports/release_gap_list.md`

`logs/2026-09-11.md`

Preserve:

`.agents/received_prompts/TECHNOREBOOT_STAGE08A_R1_FULL_OWNER_WORKFLOW_AUDIT_AND_RELEASE_GAP_LIST_PROMPT.md`

# 11. GIT / SAFETY

Do not commit:
- runtime DB;
- backups;
- real photos;
- cert private keys;
- cookies/session;
- secrets.

Commit source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

# 12. FINAL REPORT CONTRACT

Return:

```text
# Stage 08A-R1 — Full Owner Workflow Audit and Release Gap List

## Preflight
HEAD:
GIT_STATUS:
CONTAINERS:
LIVE_COUNTS:

## Workflow Results
AUTH:
PRODUCTS:
JSON:
AVITO:
BATCH:
SALES:
REPORTS:
REPAIRS:
BACKUPS:
CERTIFICATES:

## Data Consistency
AVITO_ID_DUPLICATES:
SKU_DUPLICATES:
MISSING_LOCAL_PHOTOS:
BROKEN_SALE_REFERENCES:
BROKEN_REPAIR_REFERENCES:
STATE_INCONSISTENCIES:

## Narrow Fixes Applied
FIXES:

## Release Gaps
P0_COUNT:
P1_COUNT:
P2_COUNT:
P3_COUNT:
VDS_BLOCKERS:
REPORT_PATH: reports/release_gap_list.md

## Exact Test Results

## Live Gateway Smoke Results

## Data Safety
REAL_PRODUCT_IDS_UNCHANGED:
REAL_SALE_IDS_UNCHANGED:
REAL_REPAIR_IDS_UNCHANGED:
REAL_PRODUCTS_DELETED: 0

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only numbered steps, max 12.

FINAL_STATUS:
TECHNOREBOOT_STAGE08A_R1_FULL_WORKFLOW_AUDIT_READY_FOR_OWNER_CHECK

PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If any P0 exists, do not claim release-ready.

If a P1 blocks a core daily workflow, return READY_FOR_FIX, not READY_FOR_OWNER_CHECK.

# 13. STOP

After audit, narrow fixes, tests, gap list, docs, commit/push and report:

STOP.

Do not deploy VDS.
Wait for Owner acceptance.
