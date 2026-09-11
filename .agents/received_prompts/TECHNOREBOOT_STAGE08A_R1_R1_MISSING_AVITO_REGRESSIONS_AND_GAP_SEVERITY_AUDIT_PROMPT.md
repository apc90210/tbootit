# TECHNOREBOOT — Stage 08A-R1-R1
## Missing Avito regressions + release-gap severity audit

**Project:** ТехноРебут  
**Workspace:** `C:\tbootit`  
**Stage:** `Stage 08A-R1-R1 — Missing Avito Regressions and Gap Severity Audit`

# 0. WHY THIS REVISION EXISTS

Stage08A-R1 is NOT accepted yet.

The workflow audit report is broadly successful, but it did not satisfy one explicit test-contract requirement:

> Run full relevant suites for:
> - core
> - inventory-sales-module
> - admin-shell
> - repairs-module
> - **avito-module**
> - **Chrome extension tests where available**

The Stage08A-R1 report lists:

```text
admin-shell: 83 passed, 1 skipped
inventory-sales-module: 154 passed
repairs-module: 34 passed
core: 255 passed
total: 526 passed
```

but does NOT report:
- avito-module full test suite;
- Chrome extension test suite.

Because Avito import is a core production workflow, release audit is incomplete until these are run.

Also re-check release-gap severity. Current report classifies these as P1:

- automatic nightly backups;
- Avito webhooks/background sync;
- direct ESC/POS printer driver.

These are useful improvements, but if current browser/manual workflows work correctly, they are not necessarily **P1 = core workflow broken**.

Do NOT add those features now.
Only normalize severity based on the agreed definition.

No VDS deployment.
No business-data reset.
No architecture redesign.

First copy this prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08A_R1_R1_MISSING_AVITO_REGRESSIONS_AND_GAP_SEVERITY_AUDIT_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08A_R1_R1_MISSING_AVITO_REGRESSIONS_AND_GAP_SEVERITY_AUDIT_PROMPT.md`

---

# 1. PREFLIGHT

Record:

```text
HEAD:
BRANCH:
GIT_STATUS:
DOCKER_STATUS:
EXTENSION_VERSION:
```

Preserve all live business data.

Before/after verify:

```text
PRODUCT_IDS unchanged
SALE_IDS unchanged
REPAIR_IDS unchanged
PHOTO_IDS unchanged
```

No synthetic test records may remain.

---

# 2. RUN FULL AVITO-MODULE TEST SUITE

Run the actual complete Avito module test suite from the project/container in the normal supported way.

Do not run only a selected subset.

Report:

```text
AVITO_MODULE_TEST_COMMAND:
AVITO_MODULE_PASSED:
AVITO_MODULE_FAILED:
AVITO_MODULE_SKIPPED:
```

If any test fails:
- determine whether test is stale or production code is broken;
- make only a narrow fix;
- add/update regression test;
- rerun full suite.

---

# 3. RUN CHROME EXTENSION TEST SUITE

Locate the actual extension automated tests.

Current extension accepted version should be consistent with the deployed/downloadable package.

Run all available extension tests.

Report:

```text
EXTENSION_VERSION_SOURCE:
EXTENSION_TEST_COMMAND:
EXTENSION_TESTS_AVAILABLE: true/false
EXTENSION_PASSED:
EXTENSION_FAILED:
EXTENSION_SKIPPED:
```

If no extension tests exist, prove that with repository search and report it honestly.

Do NOT claim PASS from fixtures that are not actually part of the test suite.

---

# 4. FOCUSED AVITO REGRESSION CHECKS

Confirm these already accepted rules still pass:

## Identity
- one Avito ID -> one Product;
- lookup across all statuses;
- SKU fallback repairs missing external relation;
- no duplicate Product.

## Bulk import
- current-page batch payload works;
- all-pages aggregation logic works;
- accounting is correct;
- errors cannot end in false green success.

## Thumbnails
- thumbnail extraction regression tests pass;
- photo payload can persist;
- richer/manual gallery is not overwritten by lower-quality thumbnail.

## Reactivation
- `sold/archive/0 + deliberate active import`
  -> same Product
  -> `in_stock/store/1`;
- repeated active import does not increment quantity above 1.

## Remote inactive state
- `closed/blocked/removed/archived`
  does not zero physical inventory.

No real Avito browsing is required for this revision because Owner already manually verified the real import/reactivation behavior.

---

# 5. GAP-SEVERITY NORMALIZATION

Re-open:

`reports/release_gap_list.md`

Use exactly:

```text
P0 = blocks production / data-loss / serious security risk
P1 = existing core daily workflow is broken or unreliable
P2 = important operational/usability improvement; workaround exists
P3 = polish / future feature / optional automation
```

Reassess all existing gap items.

Important:
- do NOT implement them;
- do NOT inflate severity because a feature would be convenient;
- a missing optional automation is not P1 if the supported manual/browser workflow is operational.

For each gap report:

```text
OLD_SEVERITY:
NEW_SEVERITY:
RATIONALE:
BLOCKS_VDS_DEPLOYMENT:
```

If severity remains P1, explicitly identify the currently broken daily workflow.

---

# 6. RELEASE READINESS DECISION

After missing test suites and severity normalization, produce one clear result.

Allowed outcomes:

## READY_FOR_OWNER_CHECK

Only if:
- all required module/extension test suites pass;
- no P0;
- no P1 that breaks a current core workflow;
- live data unchanged.

## READY_FOR_FIX

If:
- a core Avito/extension workflow regression exists;
- a genuine P1 remains.

## BLOCKED

If:
- data loss/security issue;
- release audit cannot be completed.

---

# 7. DOCUMENTATION

Update:

`reports/release_gap_list.md`

`reports/stage08a_r1_full_owner_workflow_audit_report.md`

`docs/stage08a_r1_full_owner_workflow_audit.md`

`logs/2026-09-11.md`

Create:

`reports/stage08a_r1_r1_missing_avito_regressions_and_gap_severity_report.md`

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE08A_R1_R1_MISSING_AVITO_REGRESSIONS_AND_GAP_SEVERITY_AUDIT_PROMPT.md`

---

# 8. GIT / SAFETY

Do not commit:
- runtime DB;
- backups;
- real photos;
- cert private keys;
- cookies/session;
- secrets.

Commit source/tests/docs only if necessary.
Push `origin/main`.
Verify clean worktree.

---

# 9. FINAL REPORT CONTRACT

Return:

```text
# Stage 08A-R1-R1 — Missing Avito Regressions and Gap Severity Audit

## Preflight
HEAD:
GIT_STATUS:
EXTENSION_VERSION:

## Avito Module
COMMAND:
PASSED:
FAILED:
SKIPPED:

## Chrome Extension
TESTS_AVAILABLE:
COMMAND:
PASSED:
FAILED:
SKIPPED:

## Focused Avito Regression
IDENTITY:
BULK_CURRENT_PAGE:
BULK_ALL_PAGES:
ACCOUNTING:
THUMBNAILS:
PHOTO_PERSISTENCE:
RICH_GALLERY_PRESERVED:
ARCHIVE_REACTIVATION:
NO_QUANTITY_INFLATION:
INACTIVE_REMOTE_STOCK_SAFETY:

## Gap Severity
P0_COUNT:
P1_COUNT:
P2_COUNT:
P3_COUNT:
VDS_BLOCKERS:
CHANGED_CLASSIFICATIONS:

## Full Required Test Totals
CORE:
ADMIN:
INVENTORY:
REPAIRS:
AVITO_MODULE:
EXTENSION:
TOTAL:

## Data Safety
PRODUCT_IDS_UNCHANGED:
SALE_IDS_UNCHANGED:
REPAIR_IDS_UNCHANGED:
PHOTO_IDS_UNCHANGED:
REAL_PRODUCTS_DELETED: 0

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08A_R1_R1_READY_FOR_OWNER_CHECK
or
TECHNOREBOOT_STAGE08A_R1_R1_READY_FOR_FIX
or
BLOCKED

PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

# 10. STOP

After tests, severity audit, docs, commit/push and report:

STOP.

Do not deploy VDS.
Wait for Owner acceptance.
