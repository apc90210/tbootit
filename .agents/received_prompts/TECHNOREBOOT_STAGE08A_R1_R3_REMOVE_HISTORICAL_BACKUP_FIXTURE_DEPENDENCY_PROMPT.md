# TECHNOREBOOT — Stage 08A-R1-R3
## Remove historical local-backup dependency from Avito regression tests

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 08A-R1-R3 — Self-Contained Avito Regression Fixtures`

# 0. WHY THIS REVISION EXISTS

Stage08A-R1-R2 is NOT accepted yet.

R2 successfully removed coupling to the CURRENT live database and removed all 5 live-data-dependent skips.

However, the new deterministic tests still appear to depend on this local historical artifact:

`data/db/technoreboot.db.bak_before_cleanup_20260910`

The R2 report explicitly says the new fixture strategy copies `BAK_PATH` into `tmp_path`.

That file is a runtime/business backup artifact under `data/db`, not a valid self-contained test dependency for a clean Git checkout.

A fresh clone on another machine must be able to run the regression suite without:
- current live DB;
- old runtime DB;
- manually preserved historical backup;
- Owner business data.

The tests must be reproducible from repository source alone.

Do NOT weaken or remove the regression coverage.
Do NOT commit a real historical business DB into Git.
Do NOT touch current live data.
Do NOT deploy VDS.

First copy this prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08A_R1_R3_REMOVE_HISTORICAL_BACKUP_FIXTURE_DEPENDENCY_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08A_R1_R3_REMOVE_HISTORICAL_BACKUP_FIXTURE_DEPENDENCY_PROMPT.md`

---

# 1. PREFLIGHT

Record:

```text
HEAD:
BRANCH:
GIT_STATUS:
EXTENSION_VERSION:
HISTORICAL_BAK_PATH:
HISTORICAL_BAK_EXISTS:
HISTORICAL_BAK_GIT_TRACKED:
```

Explicitly run/check whether:

`data/db/technoreboot.db.bak_before_cleanup_20260910`

is tracked by Git.

Also search Avito and extension tests for:
- `data/db/`
- `technoreboot.db`
- `bak_before_cleanup`
- absolute `C:\tbootit`
- live Core URLs
- runtime backup paths.

Report all test-time external dependencies.

---

# 2. SELF-CONTAINED TEST FIXTURE

Replace historical DB dependency with a synthetic test fixture created entirely inside the test.

Preferred approach:

Create a helper/fixture that builds a temporary SQLite DB in `tmp_path` with only the minimal schema and records needed to prove the historical regression.

The fixture must model the important Stage07F scenario without copying real Owner data.

Include synthetic equivalents of:

```text
baseline products
test stub products
synthetic cleanup-target products
real-like Avito products that must survive cleanup
product_external_listings
photos/relations if required by the test
```

IDs may intentionally reproduce historical ranges if the regression itself depends on ranges, but the records must be synthetic and created by test code.

Example logical groups:

```text
BASELINE_IDS
TEST_STUB_IDS
SYNTHETIC_CLEANUP_IDS
REAL_AVITO_SURVIVOR_IDS
```

Avoid magic business totals like `193` unless the number is generated from the synthetic fixture constants and is part of the fixture itself.

---

# 3. PRESERVE THE ORIGINAL REGRESSION MEANING

The self-contained tests must still prove:

- cleanup identifies only explicitly synthetic records;
- unrelated baseline products are preserved;
- real-like Avito products outside cleanup target survive;
- external listing rows for surviving products remain;
- no duplicate Avito identity;
- no duplicate SKU;
- future cleanup removes only test-created IDs;
- product identity set before/after scoped cleanup is unchanged except for the intended temporary records;
- no catalog-wide destructive cleanup is possible.

Do NOT convert these into trivial assertions that cannot catch the original bug.

---

# 4. ZERO RUNTIME DATA DEPENDENCIES

After refactor, Avito-module tests must not require:

- `data/db/technoreboot.db`
- `data/db/technoreboot.db.bak_before_cleanup_20260910`
- any backup ZIP
- current Owner catalog counts
- live Gateway
- live Core
- local media files outside test fixtures

If a focused integration test intentionally uses HTTP, it must use a mock/test app or disposable isolated target, not the live system.

---

# 5. PROVE WITH THE HISTORICAL BACKUP HIDDEN

Before final test run:

1. If historical backup exists, temporarily rename/move it OUTSIDE the expected path.
2. Run the full Avito suite.
3. Run the full Chrome extension suite.
4. Run focused Avito regressions.
5. Restore the historical backup file to its original location unchanged.

Required proof:

```text
HISTORICAL_BAK_PRESENT_DURING_TEST_RUN: false
AVITO_SUITE_RESULT:
EXTENSION_SUITE_RESULT:
FOCUSED_REGRESSION_RESULT:
HISTORICAL_BAK_SHA_BEFORE == HISTORICAL_BAK_SHA_AFTER
```

Do not delete the historical backup.

---

# 6. FRESH-CLONE PROOF

Create a temporary fresh clone of `origin/main` AFTER committing the fixture refactor, or otherwise test from a clean detached checkout of the committed revision.

In that clean checkout:

- do NOT copy `data/`;
- do NOT copy historical backup;
- run at minimum the Avito-module test suite.

Required:

```text
FRESH_CLONE_PATH:
FRESH_CLONE_HEAD:
DATA_DIRECTORY_COPIED: false
HISTORICAL_BACKUP_AVAILABLE: false
AVITO_TESTS_FROM_FRESH_CLONE:
```

If full extension tests are practical there too, run them.

This is the decisive proof that the tests are repository-self-contained.

---

# 7. LIVE DATA SAFETY

Before and after:

```text
PRODUCT_IDS
SALE_IDS
REPAIR_IDS
PHOTO_IDS
EXTERNAL_LISTING_IDS
```

must be exactly equal.

Required:

```text
PRODUCT_IDS_UNCHANGED: true
SALE_IDS_UNCHANGED: true
REPAIR_IDS_UNCHANGED: true
PHOTO_IDS_UNCHANGED: true
EXTERNAL_LISTING_IDS_UNCHANGED: true
REAL_PRODUCTS_DELETED: 0
```

---

# 8. REQUIRED TESTS

A. No Avito test imports current live DB path.  
B. No Avito test imports historical runtime backup path.  
C. Synthetic fixture is created in temp directory.  
D. Cleanup-target records are removed correctly.  
E. Baseline records survive.  
F. Real-like Avito survivor records survive.  
G. External listings survive where intended.  
H. Duplicate Avito IDs remain impossible.  
I. Duplicate SKU invariant remains covered.  
J. Historical backup hidden -> Avito suite still passes.  
K. Historical backup hidden -> extension suite still passes.  
L. Focused regressions pass.  
M. Fresh clone without `data/` -> Avito suite passes.  
N. No live ID set changes.  
O. Release gap counts remain unchanged unless a real defect is discovered.

Expected if no new defect:

```text
P0 = 0
P1 = 0
P2 = 6
P3 = 3
VDS_BLOCKERS = 0
```

---

# 9. DOCUMENTATION

Create:

`reports/stage08a_r1_r3_self_contained_avito_fixtures_report.md`

Update:

`reports/stage08a_r1_full_owner_workflow_audit_report.md`

`docs/stage08a_r1_full_owner_workflow_audit.md`

`logs/2026-09-11.md`

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE08A_R1_R3_REMOVE_HISTORICAL_BACKUP_FIXTURE_DEPENDENCY_PROMPT.md`

---

# 10. GIT / SAFETY

Do not commit:
- live DB;
- historical real DB backup;
- backup ZIP;
- real photos;
- auth secrets;
- cookies/session.

Commit synthetic fixture code/tests/docs only.

Push `origin/main`.
Verify clean worktree.

---

# 11. FINAL REPORT CONTRACT

Return:

```text
# Stage 08A-R1-R3 — Self-Contained Avito Regression Fixtures

## Preflight
HEAD:
HISTORICAL_BAK_EXISTS:
HISTORICAL_BAK_GIT_TRACKED:

## Dependency Audit
LIVE_DB_REFERENCES_BEFORE:
HISTORICAL_BAK_REFERENCES_BEFORE:
LIVE_DB_REFERENCES_AFTER:
HISTORICAL_BAK_REFERENCES_AFTER:

## Synthetic Fixture
FIXTURE_STRATEGY:
BASELINE_RECORDS:
TEST_STUB_RECORDS:
SYNTHETIC_CLEANUP_RECORDS:
REAL_AVITO_SURVIVOR_RECORDS:
EXTERNAL_LISTING_RECORDS:

## Hidden-Backup Proof
HISTORICAL_BAK_PRESENT_DURING_TEST_RUN:
HISTORICAL_BAK_SHA_BEFORE:
HISTORICAL_BAK_SHA_AFTER:
AVITO_MODULE:
EXTENSION:
FOCUSED_REGRESSIONS:

## Fresh Clone Proof
FRESH_CLONE:
FRESH_CLONE_HEAD:
DATA_DIRECTORY_COPIED:
HISTORICAL_BACKUP_AVAILABLE:
AVITO_MODULE_FROM_FRESH_CLONE:
EXTENSION_FROM_FRESH_CLONE:

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
TECHNOREBOOT_STAGE08A_R1_R3_SELF_CONTAINED_TESTS_READY_FOR_OWNER_CHECK

PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If any Avito regression test still requires an untracked runtime DB/backup file, return BLOCKED.

If fresh clone without `data/` cannot run the Avito suite, return BLOCKED.

# 12. STOP

After self-contained fixture refactor, hidden-backup proof, fresh-clone proof, docs, commit/push and report:

STOP.

Do not deploy VDS.
Wait for Owner acceptance.
