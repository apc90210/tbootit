# TECHNOREBOOT — Stage 07F-R1-R3-R1
## Restore accidentally deleted real Avito products + verify bulk price/photo fix safely

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07F-R1-R3-R1 — Restore Real Avito Products and Verify Bulk Fix`

---

# 0. EXECUTION CONTRACT

Stage 07F-R1-R3 is NOT accepted.

The previous implementation report states that during cleanup it deleted:

```text
158 products with id >= 171
= 123 synthetic live_07f_* products
+ 35 real Avito-imported products with incorrectly parsed prices
```

That violates the stage requirement.

The prior prompt explicitly required:
- remove ONLY proven synthetic Stage07F live-test records;
- REAL_PRODUCTS_REMOVED: 0;
- repair already imported real Avito products by re-running/updating the same Avito IDs.

Instead, 35 real Avito products were deleted.

The report also states that before deletion a full SQLite backup was created:

`data/db/technoreboot.db.bak_before_cleanup_20260910`

This stage must recover those real Avito products safely WITHOUT rolling back the entire current database and WITHOUT losing any legitimate changes made after that backup.

Do NOT replace the live DB wholesale with the backup.
Do NOT delete any additional real products.
Do NOT start VDS deployment.
Do NOT reopen full-gallery photo extraction.
No Owner CLI workflow.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07F_R1_R3_R1_RESTORE_REAL_AVITO_PRODUCTS_AND_VERIFY_BULK_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R3_R1_RESTORE_REAL_AVITO_PRODUCTS_AND_VERIFY_BULK_FIX_PROMPT.md`

---

# 1. FIRST — PROVE EXACTLY WHAT WAS DELETED

Compare:

- current live DB;
- `data/db/technoreboot.db.bak_before_cleanup_20260910`;
- Stage07F live-test identifier rules;
- committed verification scripts.

Classify every product present in backup but absent from current DB into:

```text
SYNTHETIC_STAGE07F
REAL_AVITO_PRODUCT
OTHER
```

Synthetic classification MUST use deterministic evidence such as:
- `external_item_id` / SKU prefix `live_07f_`;
- title pattern from committed fixture tied to same deterministic ID;
- exact creation source from known test script.

Do NOT classify a product as synthetic merely because:
- id >= 171;
- status = draft;
- source = Avito;
- price was wrong.

Report:

```text
BACKUP_PRODUCT_COUNT:
CURRENT_PRODUCT_COUNT:
MISSING_FROM_CURRENT_COUNT:
PROVEN_SYNTHETIC_COUNT:
PROVEN_REAL_AVITO_COUNT:
OTHER_COUNT:
```

And list all recovered real Avito products:

```text
PRODUCT_ID:
AVITO_ID:
SKU:
TITLE:
OLD_BAD_PRICE:
```

---

# 2. RESTORE ONLY THE 35 REAL AVITO PRODUCTS

Recover all real Avito products that were deleted by the previous cleanup.

Preferred recovery method:
- read missing real rows from the backup DB;
- insert them into the live DB through a dedicated safe one-off migration/recovery script or controlled application service;
- restore required dependent rows from the backup.

Do NOT restore the 123 synthetic test products.

Do NOT overwrite unrelated current rows.

Dependent data to inspect/restore where applicable:

- `products`
- `product_external_listings`
- `product_avito_attribute_values`
- `product_photos`
- any source metadata tables
- any other actual FK-owned rows required for those products

For each restored product:
- preserve the original Avito item identity;
- preserve title;
- preserve SKU if safe/unique;
- preserve source URL;
- preserve any description/characteristics present in backup;
- preserve photo metadata if any;
- preserve current intended DRAFT/state semantics.

If an original numeric product ID can be restored safely without collision, prefer preserving it.
If an ID is now occupied, use a safe new ID while preserving Avito identity and report the mapping.

---

# 3. VERIFY NO BUSINESS DATA WAS LOST

For the restored set, compare backup vs restored live DB.

Required:

```text
REAL_PRODUCTS_EXPECTED_TO_RESTORE:
REAL_PRODUCTS_RESTORED:
REAL_PRODUCTS_FAILED:
DUPLICATES_CREATED:
```

Must be:

```text
REAL_PRODUCTS_FAILED = 0
DUPLICATES_CREATED = 0
```

Do not proceed to acceptance otherwise.

---

# 4. KEEP THE v0.2.51 PRICE FIX

Do NOT undo the new scoped price extraction.

Verify the actual parser logic still follows:

1. structured/meta price;
2. dedicated Avito price marker;
3. dedicated price node;
4. narrow currency-bearing fallback.

Never parse price from the whole card text.

Mandatory regression examples:

```text
HP LaserJet P2055 + 3 500 ₽ -> 3500
HP LaserJet 1022 + 3 550 ₽ -> 3550
Intel Xeon E3-1220 + 665 ₽ -> 665
HP LaserJet 3055 + 4 850 ₽ -> 4850
Zebra CC600 + 5 900 ₽ -> 5900
```

---

# 5. REPAIR RESTORED REAL PRODUCTS BY RE-IMPORT, NOT DELETE/RECREATE

After restoring the 35 real Avito products, use the current v0.2.51 bulk upsert path or equivalent controlled fixture to prove:

For the same Avito ID:
- existing product is UPDATED;
- wrong price is corrected;
- no duplicate is created;
- existing richer fields remain;
- thumbnail is added only when product has zero photos.

Do not solve bad price by deleting and recreating the product.

---

# 6. THUMBNAIL PHOTO VERIFICATION

Retain the v0.2.51 thumbnail feature.

For a real/captured listing card with an image:

- extract correct card image;
- pass through bulk payload;
- persist using canonical ProductPhoto storage;
- make it main only if no existing photos;
- product list shows the thumbnail;
- repeat import creates no duplicate photo.

If a valid thumbnail cannot be downloaded due to Avito CDN restrictions:
- product import still succeeds;
- return photo warning;
- do not fabricate success;
- document the actual failure.

---

# 7. FUTURE TEST CLEANUP MUST TARGET ONLY TEST DATA

Replace any cleanup rule based on:

```text
id >= N
```

or other broad business-data range.

Future verification cleanup may delete only entities created during that exact test run.

Preferred:
- record created product IDs during test;
- delete only those IDs in `finally`;
- or run against isolated disposable DB.

Required invariant:

```text
REAL_PRODUCT_SET_BEFORE == REAL_PRODUCT_SET_AFTER
```

not only product count.

A count can match while the wrong products were deleted/replaced.

---

# 8. ADD SAFETY TEST AGAINST THIS EXACT INCIDENT

Add regression test:

Given:
- 3 synthetic `live_07f_*` products;
- 2 real Avito products created in same high-ID range;

cleanup must:
- remove exactly 3 synthetic;
- preserve exactly 2 real.

Test must fail if cleanup uses only `id >= threshold`.

Also test that cleanup cannot remove any row lacking the deterministic test-run identity.

---

# 9. AUDIT COUNT INCONSISTENCY

The previous report contains inconsistent wording:

```text
"Сохранены все 160 оригинальных товаров"
```

and later:

```text
"исходный чистый счетчик активных товаров: 162"
```

Resolve this precisely.

Report:
- total physical product rows;
- active/non-archived count if different;
- count by status;
- count by source_origin/source_type;
- count of restored real Avito products.

Do not use ambiguous "оригинальные" wording.

---

# 10. REQUIRED TESTS

## TEST A
Backup DB exists and is readable.

## TEST B
Backup/current diff correctly identifies all missing products.

## TEST C
Synthetic vs real classification uses deterministic identifiers.

## TEST D
All accidentally deleted real Avito products are restored.

## TEST E
No synthetic `live_07f_*` products are restored.

## TEST F
No unrelated current product is overwritten.

## TEST G
No duplicate Avito IDs after restore.

## TEST H
Dependent external listing rows restored.

## TEST I
Dependent characteristics restored where present.

## TEST J
Dependent photo rows/files restored where present and available.

## TEST K
Price parser still passes model-number cases.

## TEST L
Re-import updates same restored product.

## TEST M
Re-import corrects price without recreation.

## TEST N
Thumbnail persists on zero-photo product.

## TEST O
Repeat import does not duplicate thumbnail.

## TEST P
Existing/manual photos preserved.

## TEST Q
Future test cleanup removes only IDs created by the test itself.

## TEST R
High-ID real Avito products survive cleanup regression test.

## TEST S
Real product identity set before/after live test is unchanged.

## TEST T
Pairing works.

## TEST U
Bulk current-page endpoint works.

## TEST V
Bulk all-pages regression works.

## TEST W
Detailed enrichment works.

## TEST X
JSON import/export works.

## TEST Y
Product editor works.

## TEST Z
Core / Avito / Inventory / Admin relevant full suites pass.

Report exact totals.

---

# 11. OWNER MANUAL CHECK

Browser-only.

1. Open `Товары`.
2. Search for several real Avito products that disappeared after the previous cleanup, including:
   - `Лазерный принтер HP LaserJet 1022`
   - `Лазерный принтер hp laserjet p2055`
   - `Процессор Intel Xeon E3-1220`
   - `Информационный киоск Zebra CC600`
3. Confirm they are present again.
4. Update/install extension v0.2.51 if not already installed.
5. Open the same Avito listings page.
6. Run `Импортировать текущую страницу`.
7. Confirm the same products are UPDATED, not duplicated.
8. Verify their prices now match Avito.
9. Verify thumbnails appear where the Avito card has an image.
10. Confirm synthetic rows `AVITO-live_07f_*` remain absent.

No terminal.

---

# 12. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R3_R1_RESTORE_REAL_AVITO_PRODUCTS_AND_VERIFY_BULK_FIX_PROMPT.md`

Create/update:

`docs\stage07f_r1_r3_r1_restore_real_avito_products.md`

`reports\stage07f_r1_r3_r1_restore_real_avito_products_report.md`

`logs\2026-09-10.md`

If creating a one-off recovery script, keep it under a clearly named safe ops/scripts path and document whether it is reusable or historical-only.

---

# 13. GIT / SAFETY

The backup DB and live DB are runtime data.

Do NOT commit:
- backup DB;
- live DB;
- recovered Owner data;
- real photos;
- auth secrets;
- Avito cookies/session;
- backup archives.

Commit source/tests/docs only.

Push `origin/main`.

Verify clean worktree.

---

# 14. FINAL REPORT CONTRACT

Return:

```text
# Stage 07F-R1-R3-R1 — Restore Real Avito Products and Verify Bulk Fix

## Incident Audit
BACKUP_PRODUCT_COUNT:
CURRENT_PRODUCT_COUNT_BEFORE_RESTORE:
MISSING_FROM_CURRENT_COUNT:
PROVEN_SYNTHETIC_COUNT:
PROVEN_REAL_AVITO_COUNT:
OTHER_COUNT:

## Recovery
REAL_PRODUCTS_EXPECTED_TO_RESTORE:
REAL_PRODUCTS_RESTORED:
REAL_PRODUCTS_FAILED:
SYNTHETIC_PRODUCTS_RESTORED:
DUPLICATES_CREATED:
ID_COLLISIONS:
ID_MAPPING_IF_ANY:

## Restored Dependencies
EXTERNAL_LISTINGS:
CHARACTERISTICS:
PHOTOS:
OTHER:

## Price Fix
MODEL_NUMBER_CASES:
PRICE_SCOPING:
REIMPORT_CORRECTS_EXISTING_PRODUCTS:
DELETE_RECREATE_NOT_USED:

## Thumbnail
EXTRACTED:
PERSISTED:
PRODUCT_LIST_PREVIEW:
REPEAT_NO_DUPLICATE:
EXISTING_PHOTOS_PRESERVED:

## Test Cleanup Safety
OLD_BROAD_CLEANUP_REMOVED:
NEW_CLEANUP_METHOD:
HIGH_ID_REAL_PRODUCTS_PRESERVED:
REAL_PRODUCT_IDENTITY_SET_UNCHANGED:

## Counts
TOTAL_PRODUCTS:
ACTIVE_PRODUCTS:
BY_STATUS:
BY_SOURCE:

## Regression
PAIRING:
BULK_CURRENT_PAGE:
BULK_ALL_PAGES:
ENRICHMENT:
JSON:
PRODUCT_EDITOR:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only numbered steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07F_R1_R3_R1_REAL_PRODUCT_RECOVERY_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If any of the 35 real Avito products cannot be recovered from the pre-cleanup backup, return BLOCKED.

If cleanup logic can still delete real products based merely on numeric ID range, return BLOCKED.

---

# 15. STOP

After recovery, verification, tests, docs, commit/push and report:

STOP.

Do not deploy to VDS.
Wait for Owner acceptance.
