# TECHNOREBOOT — Stage 07F-R1-R3-R3
## Fix real Avito thumbnail extraction: `Фото найдено: 0 из 50`

**Project:** ТехноРебут  
**Workspace:** `C:\tbootit`  
**Stage:** `Stage 07F-R1-R3-R3 — Real Avito 0/50 Thumbnail DOM Fix`

---

# 0. EXECUTION CONTRACT

Stage 07F is NOT accepted.

Owner manually tested the REAL Avito own-listings page with extension v0.2.52.

Confirmed real result:

```text
Список объявлений Avito

Найдено объявлений: 50
Страница: 1 из 3
Фото найдено: 0 из 50

⚠️ Внимание: фото не найдены в карточках объявлений на этой странице (0 из 50).
Импорт товаров возможен без фото.
```

This proves:

- listing card detection works;
- pagination detection works;
- photo extraction fails BEFORE the backend;
- server-side ProductPhoto logic is irrelevant until the extension extracts at least one real thumbnail URL/blob.

This stage must focus ONLY on the real Avito thumbnail DOM extraction path and then verify the full chain once extraction becomes non-zero.

Do NOT redesign bulk import.
Do NOT use official Avito API.
Do NOT reopen full-gallery extraction.
One low-resolution preview image per listing is sufficient.
Do NOT start VDS deployment.
No Owner CLI.

First copy this exact prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07F_R1_R3_R3_REAL_AVITO_ZERO_OF_50_THUMBNAIL_DOM_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R3_R3_REAL_AVITO_ZERO_OF_50_THUMBNAIL_DOM_FIX_PROMPT.md`

---

# 1. REPRODUCE THE EXACT REAL FAILURE

Use the SAME real page type:

`https://www.avito.ru/profile/items`

or the exact current Owner URL pattern.

Required reproduction:

```text
LISTINGS_FOUND = 50
TOTAL_PAGES = 3
THUMBNAILS_FOUND = 0
```

Do not proceed with synthetic-only analysis.

Report:

```text
REAL_PAGE_URL_PATTERN:
REAL_PAGE_TYPE:
LISTINGS_FOUND:
VISIBLE_IMAGES_IN_PAGE:
THUMBNAILS_FOUND_BEFORE:
```

---

# 2. INSPECT THE ACTUAL IMAGE MARKUP ON REAL CARDS

For at least 5 visible listing cards that clearly show a picture in the browser, capture the DOM facts.

For each card report:

```text
AVITO_ID:
TITLE:
CARD_ROOT_SELECTOR:
VISIBLE_IMAGE_ELEMENT_TAG:
VISIBLE_IMAGE_ELEMENT_CLASSES:
VISIBLE_IMAGE_DATA_MARKER:
IMG_SRC:
IMG_CURRENT_SRC:
IMG_SRCSET:
IMG_DATA_SRC:
IMG_DATA_SRCSET:
PICTURE_SOURCE_SRCSET:
BACKGROUND_IMAGE:
BACKGROUND_IMAGE_SET:
OTHER_IMAGE_ATTRIBUTE:
ANCESTOR_PATH_FROM_CARD_ROOT:
```

If no `<img>` is present, determine exactly how Avito renders the preview:
- CSS background;
- `<picture>`;
- lazy placeholder replacement;
- nested carousel;
- pseudo-element;
- `image-set(...)`;
- inline style;
- data attribute;
- other current markup.

Do not guess.

---

# 3. PROVE WHY v0.2.52 RETURNS 0/50

Trace the current code for one real card:

```text
findCardContainer(...)
extractCardThumbnailPhoto(...)
extractBestUrlFromSrcset(...)
filter/reject logic
normalization
final return
```

Report:

```text
REAL_VISIBLE_IMAGE_FOUND_BY_QUERYSELECTOR:
CANDIDATE_URL_BEFORE_FILTER:
FILTER_REJECT_REASON:
NORMALIZED_URL:
FINAL_THUMBNAIL_URL:
PROVEN_ROOT_CAUSE:
```

Potential causes to inspect, not assume:
- image is outside the card root selected by current `findCardContainer`;
- image exists in sibling/ancestor wrapper;
- Avito uses `data-marker`/carousel wrapper not covered;
- image is lazy and `src` is a placeholder while real URL lives elsewhere;
- `srcset` parser rejects Avito format;
- URL filter rejects valid `avito.st` / `img.avito.st`;
- image uses CSS `image-set(...)`;
- image is in `<source>`;
- card has multiple nested links and wrong ancestor is selected;
- URL has query params/format that current validation treats as invalid;
- thumbnail appears only after intersection/lazy render;
- visible image exists as `blob:` URL.

---

# 4. FIX THE REAL DOM EXTRACTION

Implement the smallest robust fix that works on the current real Owner page.

The extractor should search from the REAL listing card context in this practical order:

1. visible `<img>` / `currentSrc`;
2. `img[srcset]` / `img[data-srcset]`;
3. `<picture><source srcset>`;
4. `img[src]` / `data-src` / `data-origin-src`;
5. known Avito listing image/carousel descendants;
6. CSS `background-image`;
7. CSS `image-set(...)`;
8. nearby image wrapper inside the listing's own ancestor container.

If current card root excludes the image:
- fix the card root resolution;
- do NOT globally scan the whole page and randomly pair images with products.

Image must be tied to the same Avito ID/card.

---

# 5. SUPPORT LAZY-LOADED REAL IMAGES

If Avito only populates preview URLs when cards enter the viewport:

- detect this proven behavior;
- use a bounded browser-side strategy;
- do not require Owner to manually scroll 50 cards one by one.

Acceptable:
- inspect lazy attributes before render;
- programmatically scroll card/container into view in controlled increments;
- wait for image attributes to populate;
- collect thumbnail;
- continue.

Limits:
- finite timeout;
- finite scroll attempts;
- no infinite loop;
- preserve current page position where practical.

The popup diagnostic must update after the wait/scan.

---

# 6. `blob:` URL FALLBACK

If the browser-visible thumbnail is only available as `blob:` and no durable Avito CDN URL can be extracted:

Use browser-side fetch of ONLY the displayed low-resolution thumbnail.

Then send the image to Technoreboot using the smallest existing authenticated photo-upload path.

Constraints:
- one thumbnail per listing;
- JPEG/PNG/WebP;
- reasonable size cap;
- no cookies stored server-side;
- no full-gallery scraping;
- no giant all-images base64 payload if an upload endpoint can be reused.

Do this only if proven necessary.

---

# 7. PHOTO DIAGNOSTIC MUST BECOME REAL

Keep:

```text
Фото найдено: X из N
```

After the fix, on the same real page where Avito visibly shows images:

```text
N = 50
X > 0
```

Preferred if all 50 cards have images:

```text
Фото найдено: 50 из 50
```

But acceptance only requires that X accurately reflects real visible/extractable thumbnails.

If the page visibly has 50 thumbnails and X remains 0, return BLOCKED.

---

# 8. ONLY AFTER X > 0 — VERIFY FULL CHAIN

Once the real extension extracts actual thumbnails, then verify:

```text
content.js
-> popup bulk payload
-> service_worker
-> avito-module
-> Core
-> ProductPhoto
-> persistent file
-> main_photo_url
-> inventory list <img>
```

For at least 5 real Avito IDs report:

```text
AVITO_ID:
EXTRACTED_THUMBNAIL:
PAYLOAD_THUMBNAIL:
CORE_RECEIVED:
DOWNLOAD_STATUS:
PRODUCT_PHOTO_ID:
LOCAL_FILE:
MAIN_PHOTO_URL:
INVENTORY_RENDERED:
```

---

# 9. DO NOT DAMAGE EXISTING PRODUCTS

Bulk re-import must:
- update same Avito product;
- preserve correct prices;
- preserve description/characteristics;
- preserve existing/manual photos;
- add thumbnail only when product has zero photos;
- create no duplicate product;
- create no duplicate photo.

---

# 10. REQUIRED TESTS

## TEST A
Real/captured current Owner card visibly has image and extractor returns non-empty thumbnail.

## TEST B
At least 5 real cards produce thumbnails.

## TEST C
Thumbnail belongs to correct Avito ID.

## TEST D
No avatar/logo pairing.

## TEST E
`currentSrc` works.

## TEST F
`srcset` works.

## TEST G
`picture/source` works.

## TEST H
lazy attributes work.

## TEST I
CSS `background-image` / `image-set` works if current Avito uses it.

## TEST J
Card root resolution includes image area.

## TEST K
Diagnostic `Фото найдено: X из N` matches extracted data.

## TEST L
Real page no longer reports `0 из 50` when visible images exist.

## TEST M
Bulk payload preserves thumbnail.

## TEST N
Core creates ProductPhoto.

## TEST O
Persistent file exists.

## TEST P
Media URL returns 200.

## TEST Q
Inventory list displays thumbnail.

## TEST R
Repeat import creates no duplicate photo.

## TEST S
Existing manual/main photo preserved.

## TEST T
Price parser regression remains correct.

## TEST U
Pairing remains working.

## TEST V
Bulk current-page remains working.

## TEST W
Bulk all-pages regression remains working.

## TEST X
Detailed enrichment remains working.

## TEST Y
JSON/product editor regressions pass.

## TEST Z
Core / Avito / Inventory / Admin relevant suites pass.

Report exact totals.

---

# 11. EXTENSION VERSION

Bump:

`0.2.52` -> `0.2.53`

Update:
- `manifest.json`;
- popup version;
- service worker version;
- content script version markers;
- avito-module default extension version;
- admin-shell download/version label;
- tests;
- downloadable ZIP.

Verify the downloaded ZIP manifest is actually `0.2.53`.

---

# 12. OWNER MANUAL CHECK

Browser-only.

1. Download/update extension v0.2.53.
2. Open the SAME Avito page that currently shows:
   `Фото найдено: 0 из 50`.
3. Open extension.
4. Confirm:
   - listings = 50;
   - page = 1 of 3;
   - `Фото найдено: X из 50`, where `X > 0`.
5. Do NOT proceed if X remains 0.
6. Click `Импортировать текущую страницу`.
7. Open Technoreboot `Товары`.
8. Verify at least 5 products show a thumbnail.
9. Repeat current-page import.
10. Confirm no duplicate products/photos.

No terminal.

---

# 13. PROJECT RECORDS

Preserve:

`.agents\received_prompts\TECHNOREBOOT_STAGE07F_R1_R3_R3_REAL_AVITO_ZERO_OF_50_THUMBNAIL_DOM_FIX_PROMPT.md`

Create/update:

`docs\stage07f_r1_r3_r3_real_avito_zero_of_50_thumbnail_fix.md`

`reports\stage07f_r1_r3_r3_real_avito_zero_of_50_thumbnail_fix_report.md`

`logs\2026-09-10.md`

---

# 14. GIT / SAFETY

Do not commit:
- Owner cookies/session;
- unsanitized private Avito HTML;
- runtime DB;
- real photos;
- auth secrets;
- backups.

Sanitize any real DOM fixture.

Commit source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

---

# 15. FINAL REPORT CONTRACT

Return:

```text
# Stage 07F-R1-R3-R3 — Real Avito 0/50 Thumbnail DOM Fix

## Reproduction
REAL_PAGE_URL_PATTERN:
LISTINGS_FOUND:
TOTAL_PAGES:
VISIBLE_IMAGES_IN_BROWSER:
THUMBNAILS_BEFORE:

## Proven Root Cause
CARD_ROOT_BEFORE:
REAL_IMAGE_MARKUP:
CANDIDATE_URL:
REJECT_REASON_OR_MISSED_SELECTOR:
PROVEN_ROOT_CAUSE:

## Fix
CARD_ROOT_AFTER:
THUMBNAIL_EXTRACTION_STRATEGY:
LAZY_LOAD_HANDLING:
BLOB_FALLBACK_USED:
VERSION_AFTER:

## Real Result
LISTINGS_AFTER:
THUMBNAILS_AFTER:
PHOTO_DIAGNOSTIC:
REAL_AVITO_IDS_VERIFIED:

## End-to-End
PAYLOAD:
SERVICE_WORKER:
AVITO_MODULE:
CORE:
PRODUCT_PHOTO:
LOCAL_FILE:
MEDIA_200:
INVENTORY_RENDER:

## Idempotency
DUPLICATE_PRODUCTS_SECOND_RUN:
DUPLICATE_PHOTOS_SECOND_RUN:
EXISTING_PHOTOS_PRESERVED:

## Regression
PRICE_FIX:
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
TECHNOREBOOT_STAGE07F_R1_R3_R3_REAL_AVITO_THUMBNAIL_DOM_FIX_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If the same real page still shows `Фото найдено: 0 из 50`, return BLOCKED.

# 16. STOP

After real DOM fix, real thumbnail extraction proof, full chain verification, tests, package update, docs, commit/push and report:

STOP.

Do not deploy to VDS.
Wait for Owner acceptance.
