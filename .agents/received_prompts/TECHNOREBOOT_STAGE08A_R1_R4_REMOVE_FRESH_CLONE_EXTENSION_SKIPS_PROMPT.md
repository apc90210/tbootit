# TECHNOREBOOT — Stage 08A-R1-R4
## Remove fresh-clone Chrome Extension skips and make extension tests fully self-contained

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 08A-R1-R4 — Self-Contained Chrome Extension Regression Fixtures`

# 0. WHY THIS REVISION EXISTS

Stage08A is NOT accepted yet.

Stage08A-R1-R3 successfully made the `avito-module` suite self-contained:

```text
fresh clone without data/
pytest avito-module\tests
=> 154 passed, 0 failed, 0 skipped
```

However the Chrome Extension suite in the same clean clone still reports:

```text
124 passed, 2 skipped, 0 failed
```

The two skips occur because tests still depend on this untracked historical runtime artifact:

`data/avito-module/ads/8355529554.json`

The tests were changed to skip when that file is absent.

That is the same class of problem we just removed from the Avito-module tests.

A clean Git checkout must run the entire extension regression suite without:
- `data/`;
- historical ad captures;
- Owner runtime data;
- manually preserved JSON artifacts.

Do NOT simply keep the skips.
Do NOT commit the real historical ad JSON into Git.
Do NOT weaken the assertions.
Do NOT touch live business data.
Do NOT deploy VDS.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08A_R1_R4_REMOVE_FRESH_CLONE_EXTENSION_SKIPS_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08A_R1_R4_REMOVE_FRESH_CLONE_EXTENSION_SKIPS_PROMPT.md`

# 1. PREFLIGHT

Record:

```text
HEAD:
BRANCH:
GIT_STATUS:
EXTENSION_VERSION:
LIVE_PRODUCTS:
LIVE_SALES:
LIVE_REPAIRS:
LIVE_PHOTOS:
LIVE_AVITO_LINKS:
```

Capture exact ID sets before test execution:
- products;
- sales;
- repairs;
- photos;
- external listings.

No live record may change.

# 2. IDENTIFY THE TWO FRESH-CLONE SKIPS

Audit all extension tests for runtime-data dependencies.

At minimum inspect:

- `chrome-extension/technoreboot-avito/tests/test_stage07b_r5_r2_strict_hq_photos.py`
- `chrome-extension/technoreboot-avito/tests/test_stage07b_r5_r3_full_gallery.py`

For each current skip report:

```text
TEST_NAME:
RUNTIME_FILE_DEPENDENCY:
INTENDED_REGRESSION:
WHY_SKIP_IS_NOT_ACCEPTABLE:
NEW_FIXTURE_STRATEGY:
```

Also search the entire extension test tree for:

```text
data/
avito-module/ads
8355529554
pytest.skip
C:\tbootit
```

Report every external runtime dependency.

# 3. REPLACE HISTORICAL AD FILE WITH SYNTHETIC FIXTURE

Build a minimal synthetic JSON fixture entirely in test code or as a small Git-tracked non-sensitive fixture under:

`chrome-extension/technoreboot-avito/tests/fixtures/`

The fixture must contain only the fields required to reproduce the historical regression.

Do NOT include:
- real seller/customer data;
- cookies;
- auth tokens;
- personal addresses;
- unrelated production payload.

The synthetic fixture must preserve the original behavior being tested.

## Strict HQ photo regression
Prove:
- low-resolution candidates are not incorrectly preferred;
- valid HQ image candidates are recognized;
- photo candidate filtering remains strict.

## Full gallery regression
Prove:
- multiple valid gallery images are parsed;
- expected ordering/deduplication is preserved;
- no regression back to single-photo-only behavior inside the parser test.

Do not make the fixture so trivial that the test cannot catch the original bug.

# 4. REMOVE SKIP-ON-MISSING-RUNTIME-DATA BEHAVIOR

Tests must no longer contain logic equivalent to:

```python
if not historical_runtime_file.exists():
    pytest.skip(...)
```

for required regression coverage.

If an optional platform-specific test legitimately must skip, justify it separately.

Required:

```text
RUNTIME_DATA_DEPENDENT_SKIPS_AFTER: 0
```

# 5. ZIP / DIST SELF-CONTAINMENT

Keep the recent on-demand extension ZIP build behavior.

A clean clone may have no `dist/*.zip`.

Tests must:
- build ZIP on demand from repository files;
- verify manifest version dynamically;
- never require an untracked ZIP artifact.

Confirm:

```text
DIST_PREEXISTING_REQUIRED: false
```

# 6. CLEAN-CLONE PROOF

After committing fixture/test changes:

1. create a brand-new clone from `origin/main`;
2. confirm `data/` does not exist;
3. confirm historical ad JSON does not exist;
4. confirm `dist/technoreboot-avito-extension-*.zip` does not need to preexist;
5. run:

```text
pytest avito-module\tests
pytest chrome-extension\technoreboot-avito\tests
```

Required:

```text
AVITO_MODULE: 0 failed, 0 skipped
EXTENSION: 0 failed, 0 skipped
```

If any extension test skips because runtime data is absent, return BLOCKED.

# 7. FOCUSED EXTENSION REGRESSION

Run focused assertions for:
- strict HQ photo selection;
- full-gallery parsing;
- zero-of-50 thumbnail regression;
- card-boundary isolation;
- src/srcset/picture/background extraction;
- manifest/package consistency;
- ZIP contents;
- current manifest version;
- no accidental publish/payment action.

Report PASS/FAIL individually.

# 8. LIVE DATA SAFETY

Before and after all tests verify exact equality:

```text
PRODUCT_IDS
SALE_IDS
REPAIR_IDS
PHOTO_IDS
EXTERNAL_LISTING_IDS
```

Required:

```text
PRODUCT_IDS_UNCHANGED: true
SALE_IDS_UNCHANGED: true
REPAIR_IDS_UNCHANGED: true
PHOTO_IDS_UNCHANGED: true
EXTERNAL_LISTING_IDS_UNCHANGED: true
REAL_PRODUCTS_DELETED: 0
```

# 9. RELEASE READINESS

Do not add features.

If all suites are clean, keep:

```text
P0 = 0
P1 = 0
P2 = 6
P3 = 3
VDS_BLOCKERS = 0
```

Only change counts if a real defect is discovered.

# 10. DOCUMENTATION

Create:

`reports/stage08a_r1_r4_self_contained_extension_tests_report.md`

Update:

`reports/stage08a_r1_full_owner_workflow_audit_report.md`

`docs/stage08a_r1_full_owner_workflow_audit.md`

`logs/2026-09-11.md`

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE08A_R1_R4_REMOVE_FRESH_CLONE_EXTENSION_SKIPS_PROMPT.md`

# 11. GIT / SAFETY

Do not commit:
- live DB;
- historical real ad JSON;
- backup ZIP;
- real photos;
- cert private keys;
- cookies/session;
- secrets.

Commit only synthetic fixture/code/tests/docs.

Push `origin/main`.
Verify clean worktree.

# 12. FINAL REPORT CONTRACT

Return:

```text
# Stage 08A-R1-R4 — Self-Contained Chrome Extension Regression Fixtures

## Preflight
HEAD:
EXTENSION_VERSION:

## Dependency Audit
RUNTIME_DATA_REFERENCES_BEFORE:
RUNTIME_DATA_REFERENCES_AFTER:
RUNTIME_DATA_DEPENDENT_SKIPS_BEFORE:
RUNTIME_DATA_DEPENDENT_SKIPS_AFTER:

## Synthetic Fixture
FIXTURE_PATH:
FIXTURE_TYPE:
REAL_PRODUCTION_DATA_INCLUDED: false
STRICT_HQ_REGRESSION_PRESERVED:
FULL_GALLERY_REGRESSION_PRESERVED:

## Clean Clone Proof
FRESH_CLONE_PATH:
FRESH_CLONE_HEAD:
DATA_DIRECTORY_EXISTS:
HISTORICAL_AD_JSON_EXISTS:
PREBUILT_DIST_ZIP_REQUIRED:

## Test Results
AVITO_MODULE_PASSED:
AVITO_MODULE_FAILED:
AVITO_MODULE_SKIPPED:
EXTENSION_PASSED:
EXTENSION_FAILED:
EXTENSION_SKIPPED:

## Focused Extension Regression
STRICT_HQ:
FULL_GALLERY:
ZERO_OF_50:
CARD_BOUNDARY:
PHOTO_EXTRACTION:
PACKAGE_CONTENTS:
MANIFEST_VERSION:
NO_PUBLISH_OR_PAYMENT_ACTION:

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
TECHNOREBOOT_STAGE08A_R1_R4_EXTENSION_TESTS_FULLY_SELF_CONTAINED

PRODUCTION_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If clean-clone extension suite has any skip caused by missing runtime data, return BLOCKED.

If fixture includes real production/personal data, return BLOCKED.

# 13. STOP

After fixture refactor, clean-clone proof, tests, docs, commit/push and report:

STOP.

Do not deploy VDS.
Wait for Owner acceptance.
