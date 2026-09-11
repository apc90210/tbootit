# TECHNOREBOOT — Stage 08A-R1-R2
## Remove live-DB-coupled Avito test skips and make regression suite deterministic

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 08A-R1-R2 — Deterministic Avito Regression Tests`

# 0. WHY THIS REVISION EXISTS

Stage08A-R1-R1 is NOT accepted yet.

The reported Avito/extension suites are almost complete, but the Avito suite was made to pass by modifying historical tests to skip when the current live catalog does not match an old expected business-data snapshot.

Reported changes include logic equivalent to:

```text
if total_cur != 193:
    pytest.skip(...)
```

and changing a historical invariant to:

```text
>= 50
```

This is not a valid release-regression strategy.

Automated tests must not depend on:
- current Owner product count;
- historical live DB snapshots;
- whether the Owner manually cleared/imported the catalog.

A regression test must either:
- use isolated fixtures / temp DB / mocks; or
- create uniquely named temporary data and clean it in `finally`.

Do NOT simply remove coverage.
Do NOT broadly rewrite Avito functionality.
Do NOT touch live business data.
Do NOT deploy VDS.

First copy this prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08A_R1_R2_REMOVE_LIVE_DB_COUPLED_TEST_SKIPS_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08A_R1_R2_REMOVE_LIVE_DB_COUPLED_TEST_SKIPS_PROMPT.md`

---

# 1. PREFLIGHT

Record:

```text
HEAD:
BRANCH:
GIT_STATUS:
LIVE_PRODUCTS:
LIVE_SALES:
LIVE_REPAIRS:
LIVE_PHOTOS:
EXTENSION_VERSION:
```

Capture exact ID sets before test execution:
- products;
- sales;
- repairs;
- photos.

No test may alter those sets.

---

# 2. AUDIT THE 5 SKIPPED AVITO TESTS

Identify all 5 skipped tests from:

`pytest avito-module\tests`

For each skipped test report:

```text
TEST_NAME:
CURRENT_SKIP_REASON:
WHY_IT_DEPENDS_ON_LIVE_DATA:
INTENDED_REGRESSION:
NEW_ISOLATION_STRATEGY:
```

Do not leave a skip merely because current product count is not the historical count.

---

# 3. REMOVE LIVE-CATALOG ASSUMPTIONS

Refactor those tests so they are deterministic.

Allowed patterns:

## A. Pure unit fixture
Use in-memory/temp models/fixtures and test the transformation/merge logic without live DB.

## B. Mock Core
If the test is for Avito-module request behavior, mock Core HTTP responses and assert payloads/calls.

## C. Isolated temp DB
If actual Core persistence must be tested, use a disposable test DB/container or test application fixture not mounted to `C:\tbootit\data\db\technoreboot.db`.

## D. Unique temporary records
Only if unavoidable:
- unique prefix;
- create;
- assert;
- remove in `finally`;
- prove live ID set restored exactly.

Preferred order: A -> B -> C -> D.

---

# 4. PRESERVE THE INTENDED REGRESSIONS

Do not weaken the old Stage07F tests.

Keep coverage for:

- recovery/restoration logic that was originally being tested;
- one Avito ID -> one Product;
- no accidental deletion of real/business products;
- zero-of-50 thumbnail parser regression;
- card boundary/image extraction behavior;
- no catalog-wide destructive cleanup;
- no duplicate products.

The fact that the Owner currently has 50 products must be irrelevant to the test result.

---

# 5. REMOVE MAGIC BUSINESS COUNTS

No test should contain hard-coded assumptions such as:

```text
current live catalog == 193
current live catalog >= 50
```

unless the number belongs to a synthetic fixture created inside that test.

Search all Avito-module tests for business-count coupling.

Report:

```text
LIVE_COUNT_ASSUMPTIONS_FOUND:
LIVE_COUNT_ASSUMPTIONS_REMOVED:
```

---

# 6. RUN FULL TEST SUITES

Run:

```text
pytest avito-module\tests
pytest chrome-extension\technoreboot-avito\tests
```

Expected:

```text
AVITO_MODULE_FAILED = 0
AVITO_MODULE_SKIPPED = 0
EXTENSION_FAILED = 0
```

If any skip remains, it must be a genuine platform/environment skip unrelated to current Owner data and must be explicitly justified.

Also run focused Avito regression verification.

---

# 7. LIVE DATA SAFETY

Before and after all tests verify exact equality:

```text
PRODUCT_IDS
SALE_IDS
REPAIR_IDS
PHOTO_IDS
AVITO_EXTERNAL_LISTING_IDS
```

Also compare counts.

Required:

```text
REAL_PRODUCT_IDS_UNCHANGED: true
REAL_SALE_IDS_UNCHANGED: true
REAL_REPAIR_IDS_UNCHANGED: true
REAL_PHOTO_IDS_UNCHANGED: true
REAL_EXTERNAL_LISTING_IDS_UNCHANGED: true
```

No real product may be deleted or created by tests.

---

# 8. RELEASE GAP LIST

Do NOT add new feature work.

Keep the normalized severity model from Stage08A-R1-R1 unless this test audit discovers a real core-flow defect.

Expected current state if no new defect appears:

```text
P0 = 0
P1 = 0
P2 = 6
P3 = 3
VDS_BLOCKERS = 0
```

---

# 9. DOCUMENTATION

Update:

`reports/stage08a_r1_full_owner_workflow_audit_report.md`

`reports/stage08a_r1_r1_missing_avito_regressions_and_gap_severity_report.md`

Create:

`reports/stage08a_r1_r2_deterministic_avito_tests_report.md`

Update:

`docs/stage08a_r1_full_owner_workflow_audit.md`

`logs/2026-09-11.md`

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE08A_R1_R2_REMOVE_LIVE_DB_COUPLED_TEST_SKIPS_PROMPT.md`

---

# 10. GIT / SAFETY

Do not commit:
- runtime DB;
- backups;
- real photos;
- cert private keys;
- cookies/session;
- secrets.

Commit tests/source/docs only.
Push `origin/main`.
Verify clean worktree.

---

# 11. FINAL REPORT CONTRACT

Return:

```text
# Stage 08A-R1-R2 — Deterministic Avito Regression Tests

## Preflight
HEAD:
GIT_STATUS:
EXTENSION_VERSION:

## Skipped-Test Audit
SKIPPED_TESTS_BEFORE:
LIVE_DATA_DEPENDENT_SKIPS_BEFORE:
SKIPPED_TESTS_AFTER:
LIVE_DATA_DEPENDENT_SKIPS_AFTER:

## Isolation
LIVE_COUNT_ASSUMPTIONS_FOUND:
LIVE_COUNT_ASSUMPTIONS_REMOVED:
TEST_DB_OR_MOCK_STRATEGY:

## Avito Module
COMMAND:
PASSED:
FAILED:
SKIPPED:

## Chrome Extension
COMMAND:
PASSED:
FAILED:
SKIPPED:

## Focused Regression
IDENTITY:
NO_DESTRUCTIVE_CLEANUP:
ZERO_OF_50_THUMBNAIL:
CARD_BOUNDARY:
PHOTO_EXTRACTION:
ARCHIVE_REACTIVATION:
NO_QUANTITY_INFLATION:
INACTIVE_REMOTE_STOCK_SAFETY:

## Data Safety
PRODUCT_IDS_UNCHANGED:
SALE_IDS_UNCHANGED:
REPAIR_IDS_UNCHANGED:
PHOTO_IDS_UNCHANGED:
EXTERNAL_LISTING_IDS_UNCHANGED:
REAL_PRODUCTS_DELETED: 0

## Release Readiness
P0_COUNT:
P1_COUNT:
P2_COUNT:
P3_COUNT:
VDS_BLOCKERS:

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08A_R1_R2_DETERMINISTIC_TESTS_READY_FOR_OWNER_CHECK

PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If any Avito test still skips because of the current live catalog state, return BLOCKED.

If tests alter real business ID sets, return BLOCKED.

# 12. STOP

After deterministic test refactor, full test runs, data-safety verification, docs, commit/push and report:

STOP.

Do not deploy VDS.
Wait for Owner acceptance.
