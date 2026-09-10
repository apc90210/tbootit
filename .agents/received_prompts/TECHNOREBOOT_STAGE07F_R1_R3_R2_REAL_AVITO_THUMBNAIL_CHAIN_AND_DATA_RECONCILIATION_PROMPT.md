# TECHNOREBOOT — Stage 07F-R1-R3-R2
## Real Avito thumbnail chain + DB reconciliation + remove remaining test fixtures if proven

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07F-R1-R3-R2 — Real Thumbnail Chain and Data Reconciliation`

# 0. EXECUTION CONTRACT

Stage 07F is still NOT accepted.

Previous stage restored the real Avito products and kept v0.2.51 price parsing fixes. However, Owner's real-world observation before this recovery stage was:

- bulk listing cards are being parsed;
- photos are NOT appearing from the real Avito profile import.

The latest report claims the photo bug is fixed by adding `extractBestUrlFromSrcset()`, but it does NOT prove the complete real chain on Owner's actual Avito cards:

```text
real Avito card
-> thumbnail extracted in content.js
-> thumbnail present in bulk payload
-> service worker forwards it
-> avito-module receives/forwards it
-> Core downloads/imports it
-> ProductPhoto row created
-> persistent local media exists
-> main_photo_url returned
-> inventory list displays <img>
```

This stage must prove and, if necessary, fix THAT exact chain.

Also reconcile the report's DB-count ambiguity and audit the remaining `AVITO-111` / `AVITO-222` records.

Do NOT redesign the whole bulk importer.
Do NOT use official Avito API.
Do NOT reopen full-gallery extraction.
One thumbnail per product is sufficient.
Do NOT start VDS deployment.
No Owner CLI.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07F_R1_R3_R2_REAL_AVITO_THUMBNAIL_CHAIN_AND_DATA_RECONCILIATION_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R3_R2_REAL_AVITO_THUMBNAIL_CHAIN_AND_DATA_RECONCILIATION_PROMPT.md`

# 1. RECONCILE THE PREVIOUS REPORT'S COUNTS

The previous report states:

```text
BACKUP_PRODUCT_COUNT: 318
CURRENT_PRODUCT_COUNT_BEFORE_RESTORE: 195
MISSING_FROM_CURRENT_COUNT: 123
PROVEN_SYNTHETIC_COUNT: 123
PROVEN_REAL_AVITO_COUNT: 35
```

These labels are ambiguous because:
- if exactly 123 rows were missing and all 123 were synthetic, then the 35 real Avito rows were apparently already present at that specific comparison point;
- yet the same report says 35 real products were restored.

Resolve this precisely with a timeline.

Report:

```text
COUNT_AFTER_BAD_CLEANUP:
COUNT_BEFORE_RECOVERY_SCRIPT:
COUNT_AFTER_RECOVERY_SCRIPT:
BACKUP_COUNT:
ROWS_MISSING_BEFORE_RECOVERY:
ROWS_RESTORED_BY_RECOVERY:
SYNTHETIC_ROWS_INTENTIONALLY_NOT_RESTORED:
```

Do not use ambiguous terms such as "original products".

# 2. AUDIT AVITO-111 AND AVITO-222

The previous report calls:

```text
id=171 | AVITO-111 | Товар 1
id=172 | AVITO-222 | Товар 2
```

"служебные позиции", but counts them inside the 35 "real" recovered products.

Determine their provenance from:
- git history;
- committed tests;
- verification scripts;
- backup timestamps/source metadata.

If they are test fixtures:
- remove ONLY these proven test fixtures and dependencies;
- do not count them as business/real Avito products.

If they are real business records:
- preserve them and prove why.

Report:

```text
AVITO_111_PROVENANCE:
AVITO_222_PROVENANCE:
ACTION:
```

# 3. REAL THUMBNAIL CHAIN — INSTRUMENT EVERY HOP

Use a CURRENT real/sanitized Owner Avito listing DOM capture or the actual browser-assisted page.

For at least 5 real listing cards with visible images capture:

```text
AVITO_ID:
TITLE:
VISIBLE_IMAGE_IN_BROWSER: true/false
IMG_CURRENT_SRC:
IMG_SRC:
IMG_SRCSET:
PICTURE_SOURCE_SRCSET:
DATA_SRC:
DATA_SRCSET:
CSS_BACKGROUND_IMAGE:
EXTRACTED_THUMBNAIL_URL:
```

Then trace the same item through:

```text
CONTENT_EXTRACTED_PHOTO:
POPUP_BATCH_PHOTO:
SERVICE_WORKER_PHOTO:
AVITO_MODULE_PHOTO:
CORE_IMPORT_PHOTO:
DOWNLOAD_HTTP_STATUS:
PRODUCT_PHOTO_ROW:
LOCAL_FILE_EXISTS:
MAIN_PHOTO_URL:
INVENTORY_IMG_RENDERED:
```

Do not claim PASS until the real chain is proven.

# 4. SUPPORT CURRENT REAL AVITO IMAGE MARKUP

The extractor must support the actual current card markup, including as applicable:

- `img.currentSrc`
- `img.src`
- `img.srcset`
- `<picture><source srcset>`
- `data-src`
- `data-srcset`
- lazy-loaded image attributes
- CSS background-image fallback if Avito currently uses it

Prefer the image belonging to the listing card.

Reject:
- avatars;
- seller logos;
- icons;
- placeholders;
- SVG/data placeholders;
- unrelated recommendation images.

# 5. ADD VISIBLE PHOTO DIAGNOSTICS TO EXTENSION

For bulk list pages show a small diagnostic line:

```text
Фото найдено: X из N
```

where:
- `N` = extracted listings on current page;
- `X` = listings for which a valid thumbnail URL was extracted.

This is useful for Owner acceptance and future Avito DOM changes.

If N > 0 and X == 0:
- show a warning;
- bulk product import may still proceed if Owner chooses;
- do NOT claim the thumbnail feature is working.

# 6. SERVER DOWNLOAD / CDN FAILURE

If the browser extractor has a valid thumbnail URL but Core cannot download it, prove why.

Capture:
- requested URL host;
- HTTP status;
- redirect behavior;
- content type;
- failure class.

If direct server-side Avito CDN fetching works, keep it.

If it fails due to CDN/hotlink/session restrictions, implement the smallest robust fallback:

Preferred fallback:
- extension/browser fetches ONLY the already displayed low-resolution thumbnail;
- sends/uploads that image through the existing authenticated extension bridge;
- Core stores it through the existing ProductPhoto pipeline.

Constraints:
- one thumbnail only;
- cap image size reasonably;
- JPEG/WebP/PNG only;
- no 50-image giant base64 JSON blob if avoidable;
- no cookies/session persisted on server;
- no new general-purpose file transfer architecture.

# 7. PHOTO PERSISTENCE / UI

For a product with zero photos:
- save one thumbnail persistently;
- create ProductPhoto;
- set main photo.

For product with existing photos:
- preserve them;
- do not replace manual main photo;
- do not add duplicate low-res thumbnail.

Verify:
- media URL returns HTTP 200;
- `main_photo_url` returned by Core;
- inventory product list displays actual thumbnail;
- product detail displays same photo.

# 8. REPEAT IMPORT

Run the same current page twice.

Expected:
- same product IDs;
- second run creates zero duplicate products;
- second run creates zero duplicate thumbnails;
- prices remain correct;
- richer existing data remains intact.

# 9. DO NOT POLLUTE OWNER DB DURING TESTING

Any live test record created by this stage must be:
- uniquely identified;
- recorded at creation;
- removed in `finally`.

Required stronger invariant:

```text
BUSINESS_PRODUCT_IDS_AFTER == BUSINESS_PRODUCT_IDS_BEFORE
```

and not only equal counts.

No cleanup by `id >= N`.

# 10. REQUIRED TESTS

A. Current real/sanitized card with `<img src>` -> thumbnail extracted.  
B. `srcset` -> best valid candidate extracted.  
C. `<picture><source srcset>` -> candidate extracted.  
D. lazy `data-src`/`data-srcset` -> candidate extracted.  
E. avatar/logo ignored.  
F. 5 real visible-image cards -> photo extraction count > 0.  
G. payload preserves photo URL.  
H. service worker preserves photo URL.  
I. avito-module preserves photo URL.  
J. Core persists photo.  
K. local file exists.  
L. media route returns 200.  
M. inventory list renders `<img>`.  
N. repeat bulk import does not duplicate photo.  
O. existing manual photo remains main.  
P. price model-number regression stays fixed.  
Q. same Avito ID updates same product.  
R. `AVITO-111`/`AVITO-222` provenance determined.  
S. any proven test fixture among them safely removed.  
T. product identity set unchanged by live verification.  
U. pairing passes.  
V. bulk current-page passes.  
W. all-pages regression passes.  
X. detailed enrichment passes.  
Y. JSON/product editor regressions pass.  
Z. Core/Avito/Inventory/Admin relevant suites pass.

Report exact totals.

# 11. EXTENSION VERSION

If code changes are required, bump:

`0.2.51` -> `0.2.52`

Update all version surfaces and rebuild downloadable ZIP.

If no extension code changes are required, keep 0.2.51 and explicitly justify.

# 12. OWNER MANUAL CHECK

Browser-only:

1. Update/install the reported extension version.
2. Open the same Avito own-listings page.
3. Open extension.
4. Confirm:
   - listing count is non-zero;
   - page count is correct;
   - new line shows `Фото найдено: X из N`.
5. If visible Avito cards have photos, `X` must be > 0.
6. Click `Импортировать текущую страницу`.
7. Open Technoreboot `Товары`.
8. Verify at least 5 imported/re-imported products:
   - correct title;
   - correct price;
   - visible thumbnail in the Фото column.
9. Re-run current page.
10. Confirm no duplicate products/photos.
11. Search `AVITO-111`, `AVITO-222` only if report says they were fixtures; confirm removed if appropriate.
12. Search `live_07f`; must return none.

No terminal.

# 13. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R3_R2_REAL_AVITO_THUMBNAIL_CHAIN_AND_DATA_RECONCILIATION_PROMPT.md`

Create/update:

`docs\stage07f_r1_r3_r2_real_avito_thumbnail_chain.md`

`reports\stage07f_r1_r3_r2_real_avito_thumbnail_chain_report.md`

`logs\2026-09-10.md`

# 14. GIT / SAFETY

Do not commit:
- Owner cookies/session;
- unsanitized private Avito HTML;
- runtime DB;
- real photos;
- auth secrets;
- backups.

Commit source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

# 15. FINAL REPORT CONTRACT

Return:

```text
# Stage 07F-R1-R3-R2 — Real Thumbnail Chain and Data Reconciliation

## DB Timeline
COUNT_AFTER_BAD_CLEANUP:
COUNT_BEFORE_RECOVERY_SCRIPT:
COUNT_AFTER_RECOVERY_SCRIPT:
BACKUP_COUNT:
ROWS_MISSING_BEFORE_RECOVERY:
ROWS_RESTORED_BY_RECOVERY:
SYNTHETIC_NOT_RESTORED:

## AVITO-111 / AVITO-222
AVITO_111_PROVENANCE:
AVITO_222_PROVENANCE:
ACTION:

## Real Thumbnail Extraction
REAL_CARDS_CHECKED:
VISIBLE_IMAGE_CARDS:
THUMBNAILS_EXTRACTED:
THUMBNAIL_MARKUP_TYPES:
PHOTO_DIAGNOSTIC_UI:

## End-to-End Photo Chain
CONTENT_EXTRACTED:
POPUP_PAYLOAD:
SERVICE_WORKER:
AVITO_MODULE:
CORE:
DOWNLOAD_STATUS:
PRODUCT_PHOTO:
LOCAL_FILE:
MAIN_PHOTO_URL:
INVENTORY_RENDER:

## Idempotency
SECOND_RUN_DUPLICATE_PRODUCTS:
SECOND_RUN_DUPLICATE_PHOTOS:
EXISTING_PHOTOS_PRESERVED:

## Regression
PRICE_FIX:
PAIRING:
BULK_CURRENT_PAGE:
BULK_ALL_PAGES:
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
TECHNOREBOOT_STAGE07F_R1_R3_R2_REAL_THUMBNAIL_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If real Avito cards visibly contain images but `THUMBNAILS_EXTRACTED == 0`, return BLOCKED.

If thumbnail URL reaches Core but no ProductPhoto/local file is produced, return BLOCKED.

# 16. STOP

After reconciliation, real thumbnail verification/fix, tests, package update if needed, docs, commit/push and report:

STOP.

Do not deploy to VDS.
Wait for Owner acceptance.
