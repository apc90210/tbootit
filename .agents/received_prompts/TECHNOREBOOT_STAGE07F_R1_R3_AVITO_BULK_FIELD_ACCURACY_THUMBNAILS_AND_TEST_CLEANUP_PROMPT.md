# TECHNOREBOOT — Stage 07F-R1-R3
## Real Avito bulk import: correct field extraction + thumbnail photos + cleanup test pollution

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07F-R1-R3 — Bulk Field Accuracy, Thumbnails and Test Cleanup`

# 0. EXECUTION CONTRACT

Stage 07F bulk import is NOT accepted yet.

The real Owner test now reaches Avito listing cards and creates Technoreboot products, but imported data is visibly wrong for some products and rows have no useful image preview.

Observed examples from the real product list:

```text
AVITO-8281659634  Связка Msi 760GM-P23 + Процессор fx4100       41002200 ₽
AVITO-7929825930  Информационный киоск Zebra CC600              6005900 ₽
AVITO-8273486853  Моноблок Lenovo C340 i3-3220/...              6155900 ₽
AVITO-4889848898  Процессор Intel Xeon E3-1220                  1220665 ₽
AVITO-4761652380  Материнская плата Asus F1A55 + Athlon...      46411520 ₽
AVITO-8274380044  Лазерное МФУ HP LaserJet 3055                 30554850 ₽
AVITO-8335505137  Лазерный принтер HP LaserJet 1022             10223550 ₽
AVITO-8250874053  Лазерный принтер HP LaserJet P2055            20553500 ₽
```

This strongly suggests price extraction is mixing model/title digits with actual price. PROVE the exact cause.

The product list also shows `—` instead of a product image. Owner wants at least one Avito card thumbnail, even low-resolution, so products can be visually recognized.

The previous live verification also left synthetic records such as:

```text
AVITO-live_07f_r2_p2_...
AVITO-live_07f_r2_p3_...
Товар со страницы 2 #...
Товар со страницы 3 #...
```

This stage must:
1. fix lightweight field extraction, especially price;
2. import/persist one listing thumbnail when available;
3. remove ONLY known synthetic Stage07F test pollution;
4. make future live tests clean up after themselves.

Do NOT redesign architecture.
Do NOT use official Avito API.
Do NOT reopen full-gallery extraction.
Do NOT start VDS deployment.
No Owner CLI.

First copy this exact prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07F_R1_R3_AVITO_BULK_FIELD_ACCURACY_THUMBNAILS_AND_TEST_CLEANUP_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R3_AVITO_BULK_FIELD_ACCURACY_THUMBNAILS_AND_TEST_CLEANUP_PROMPT.md`

# 1. AUDIT REAL IMPORTED PRODUCTS

Before changes, inspect the real imported rows above and trace them to extraction logic.

For representative bad-price items report:

```text
AVITO_ID:
TITLE:
CURRENT_BAD_PRICE:
RAW_CARD_PRICE_TEXT:
RAW_CARD_TITLE_TEXT:
PRICE_NODE_SELECTOR:
EXTRACTED_PRICE_BEFORE:
EXPECTED_PRICE:
```

Use actual Avito price DOM/structured value to determine expected price.

# 2. FIX PRICE EXTRACTION

Bulk price extraction must use a dedicated price field/node.

Priority:
1. structured/meta price value (`itemprop="price"`, `content`, current stable Avito attribute);
2. stable Avito price `data-marker`;
3. dedicated price node text;
4. narrowly scoped fallback inside price container.

Forbidden:
`card.innerText -> strip non-digits -> Number(...)`
or equivalent parsing of whole card text.

Mandatory cases:

```text
HP LaserJet 3055 + 4 850 ₽ -> 4850
HP LaserJet 1022 + 3 550 ₽ -> 3550
Intel Xeon E3-1220 + 665 ₽ -> 665
Zebra CC600 + 5 900 ₽ -> 5900
```

If no reliable price:
- send `price: null`;
- do not invent;
- do not drop listing.

# 3. FIELD SCOPING

For each card:
- Avito ID from listing-specific data/link;
- URL from listing link;
- title from title/link node;
- price from price node;
- location/status/photo from their own nodes.

Deduplicate by Avito ID.

# 4. THUMBNAIL PHOTO REQUIRED

Extract the best image belonging to the same listing card:

Priority as appropriate:
- `img.currentSrc`;
- `src`;
- best suitable `srcset` candidate;
- stable image data attribute;
- CSS background only as fallback.

Do not select avatar, seller logo, icons, placeholders, or unrelated images.

Report:

```text
CARD_THUMBNAIL_SOURCE:
BULK_PAYLOAD_PHOTO_FIELD:
SERVER_PHOTO_INGEST_PATH:
PERSISTENT_PRODUCT_PHOTO_PATH:
```

# 5. PERSIST THUMBNAIL LOCALLY

Remote Avito CDN URL alone is not durable.

For a new bulk product with a thumbnail:
- use existing safe photo ingestion service;
- persist into canonical product photo storage;
- create normal `ProductPhoto`;
- set as main when it is the only photo;
- make it visible in product list/detail.

No `/tmp` durable success.

Thumbnail failure must not fail the product import; return a photo warning instead.

# 6. PHOTO IDEMPOTENCY

If product has zero photos:
- add thumbnail if available.

If product already has photos:
- do not delete/reorder;
- do not replace a manually selected main photo;
- normally do not add another low-quality thumbnail.

Repeated bulk import must not duplicate photos.

Later detailed Avito enrichment remains supported and local manual photos remain intact.

# 7. PRODUCT LIST PREVIEW

Verify the existing inventory list uses the product's standard main photo.

For newly imported items with an Avito card image, the current `—` image cell must show a thumbnail.

Do not create a separate image system.

# 8. REPAIR ALREADY IMPORTED REAL AVITO PRODUCTS

On re-running bulk import for the same Avito IDs:
- update SAME product;
- correct bad price;
- add thumbnail if product has no photos;
- preserve SKU, purchase price, storage location, description, characteristics, manual photos;
- create no duplicate.

This must repair today's already-imported bad rows automatically.

# 9. REMOVE KNOWN SYNTHETIC TEST POLLUTION

Audit DB for deterministic Stage07F test records.

Known prefixes/patterns include:
```text
live_07f_
AVITO-live_07f_
```
and titles created by those exact fixtures such as:
```text
Товар со страницы 2 #...
Товар со страницы 3 #...
```

Before deletion:
- list exact matched IDs/titles/count;
- prove each belongs to Stage07F test fixtures;
- match using deterministic test identifiers, NOT broad business-field text.

Delete ONLY proven synthetic products and their owned dependent test rows/photos.

Report:
```text
SYNTHETIC_MATCH_RULE:
SYNTHETIC_PRODUCTS_FOUND:
SYNTHETIC_PRODUCTS_REMOVED:
REAL_PRODUCTS_REMOVED: 0
```

# 10. FUTURE LIVE TESTS CLEAN UP

Fix live verification so it:
- creates uniquely prefixed disposable records;
- cleans them in `finally`;
- cleans dependent rows/photos;
- leaves real product count unchanged.

Invariant:
```text
product_count_after_live_test == product_count_before_live_test
```

Prefer isolated DB fixtures where practical.

# 11. CATEGORY POLICY

Do not infer category from title in the lightweight extension if category is not reliably present.

If unavailable:
- leave unknown/default according to current system policy.

Detailed single-listing enrichment can fill category later.

# 12. REQUIRED TESTS

A. Model digits do not contaminate price.  
B. `HP LaserJet 1022` + `3 550 ₽` -> `3550`.  
C. `Intel Xeon E3-1220` + `665 ₽` -> `665`.  
D. Missing reliable price -> null.  
E. Correct card thumbnail extracted.  
F. Avatar/unrelated images ignored.  
G. New bulk product + thumbnail -> persistent ProductPhoto.  
H. Media route for thumbnail -> HTTP 200.  
I. Product list renders thumbnail.  
J. Repeat bulk import does not duplicate photo.  
K. Existing local/main photos preserved.  
L. Re-import corrects bad price on same Avito ID.  
M. No duplicate product on re-import.  
N. Description/characteristics/manual fields preserved.  
O. Known `live_07f_*` records identified exactly.  
P. Only synthetic records removed; real removed = 0.  
Q. Live verification restores DB product count.  
R. 50-card real DOM detection remains working.  
S. 3-page traversal regression passes.  
T. Pairing passes.  
U. Detailed enrichment passes.  
V. JSON import/export passes.  
W. Product editor/photo manager passes.  
X. Core full suite passes.  
Y. Avito module full suite passes.  
Z. Inventory/Admin Shell relevant suites pass.

# 13. EXTENSION VERSION

Bump:
`0.2.50` -> `0.2.51`

Update all version surfaces and rebuild downloadable ZIP.

# 14. OWNER MANUAL CHECK

Browser-only:

1. Download/update extension v0.2.51.
2. Open same Avito own-listings page.
3. Confirm listing count/page count still correct.
4. Pick 3 visible listings whose titles contain digits/model numbers and note visible Avito prices.
5. Click `Импортировать текущую страницу`.
6. Open Technoreboot `Товары`.
7. Verify those products:
   - titles correct;
   - prices exactly match Avito;
   - at least one thumbnail where Avito card had an image.
8. Re-run same page.
9. Confirm no duplicate products and no duplicate thumbnails.
10. Open one listing and use `Доимпортировать данные`.
11. Confirm same product is enriched.
12. Confirm synthetic `AVITO-live_07f_*` rows are gone.

No terminal.

# 15. PROJECT RECORDS

Preserve:
`.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R3_AVITO_BULK_FIELD_ACCURACY_THUMBNAILS_AND_TEST_CLEANUP_PROMPT.md`

Create/update:
`docs\stage07f_r1_r3_avito_bulk_field_accuracy_thumbnails_and_test_cleanup.md`
`reports\stage07f_r1_r3_avito_bulk_field_accuracy_thumbnails_and_test_cleanup_report.md`
`logs\2026-09-10.md`

# 16. GIT / SAFETY

Do not commit Owner Avito data/cookies/session, runtime DB, real photos, auth secrets, backups.

Sanitize DOM fixtures.

Commit source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

# 17. FINAL REPORT CONTRACT

Return:

```text
# Stage 07F-R1-R3 — Bulk Field Accuracy, Thumbnails and Test Cleanup

## Proven Root Cause
PRICE_EXTRACTION_BEFORE:
BAD_PRICE_EXAMPLES:
PROVEN_ROOT_CAUSE:

## Correct Extraction
PRICE_SELECTOR_PRIORITY:
TITLE_SOURCE:
AVITO_ID_SOURCE:
URL_SOURCE:
NULL_PRICE_POLICY:

## Thumbnail
THUMBNAIL_SELECTOR_PRIORITY:
PAYLOAD_FIELD:
PERSISTED_LOCALLY:
PRODUCT_PHOTO_CREATED:
MAIN_PHOTO_POLICY:
REPEAT_IMPORT_NO_DUPLICATE_PHOTO:
PRODUCT_LIST_PREVIEW:

## Existing Real Products
BAD_PRICE_PRODUCTS_REPAIRED_BY_REIMPORT:
SAME_PRODUCT_IDS:
RICH_DATA_PRESERVED:

## Synthetic Test Cleanup
SYNTHETIC_MATCH_RULE:
SYNTHETIC_PRODUCTS_FOUND:
SYNTHETIC_PRODUCTS_REMOVED:
REAL_PRODUCTS_REMOVED:
LIVE_TEST_CLEANUP_INVARIANT:

## Real Browser/DOM
CURRENT_PAGE_COUNT:
TOTAL_PAGES:
MODEL_NUMBER_PRICE_CASES_VERIFIED:
THUMBNAIL_CASES_VERIFIED:

## Regression
PAIRING:
BULK_CURRENT_PAGE:
BULK_ALL_PAGES:
SECOND_RUN_NO_DUPLICATES:
ENRICHMENT:
JSON:
PRODUCT_EDITOR:

## Extension
VERSION_AFTER:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser-only numbered steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07F_R1_R3_BULK_ACCURACY_AND_THUMBNAILS_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If model/title digits can still contaminate price, return BLOCKED.
If a valid Avito card thumbnail still produces no product preview, return BLOCKED.
If live verification still pollutes Owner DB, return BLOCKED.

# 18. STOP

After fix, cleanup, tests, extension package/version update, docs, commit/push and report:

STOP.

Do not deploy to VDS.
Wait for Owner acceptance.
