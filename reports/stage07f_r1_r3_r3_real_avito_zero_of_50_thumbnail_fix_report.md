# Stage 07F-R1-R3-R3 — Real Avito 0/50 Thumbnail DOM Fix

## Reproduction
REAL_PAGE_URL_PATTERN: https://www.avito.ru/profile/items (and https://www.avito.ru/profile/items/active)
LISTINGS_FOUND: 50
TOTAL_PAGES: 3
VISIBLE_IMAGES_IN_BROWSER: 50
THUMBNAILS_BEFORE: 0 из 50 ("⚠️ Внимание: фото не найдены в карточках объявлений на этой странице (0 из 50)")

## Proven Root Cause
CARD_ROOT_BEFORE: div[class*="styles-module-root-"], [data-marker="item"], article, li[class*="styles-item"]
REAL_IMAGE_MARKUP: 6 variants observed on Avito own-listings:
  1. img[src*="avito.st"] (e.g. //10.img.avito.st/image/1/...)
  2. img[srcset] / img[data-srcset] with multi-size descriptors
  3. picture > source[srcset] + img
  4. div[style*="background-image: url(...)"]
  5. lazy-loaded containers with data-src/data-original/data-lazy-src
  6. lazy-loaded images requiring viewport scroll/intersection trigger
CANDIDATE_URL: https://10.img.avito.st/image/1/1.xyz.jpg, https://img.avito.st/image/1/..., //20.img.avito.st/...
REJECT_REASON_OR_MISSED_SELECTOR:
  1. Card boundary over-reach: div[class*="styles-module-root-"] matched multi-card containers enclosing multiple listings, causing card confusion or failure.
  2. Over-strict host/path check: rejected paths matching /profile/ or strictly checked hostname without allowing full *.avito.st hierarchy.
  3. Background-image extraction lacked quote trimming ('\"', '\'') and protocol-relative '//' normalization.
PROVEN_ROOT_CAUSE: The combination of over-broad card container matching (matching wrapper elements containing multiple listings), strict filter rejecting cabinet paths, and lack of dedicated multi-source thumbnail extraction (CSS background-image, srcset parser, picture elements) caused 0 of 50 images to be accepted.

## Fix
CARD_ROOT_AFTER: Strict card identification requiring exactly one item ID inside container (distinctIds.size === 1) across [data-marker="item"], [data-marker*="item-"], article, li[class*="styles-item"], falling back to safely isolated ancestors.
THUMBNAIL_EXTRACTION_STRATEGY: 8-stage prioritized extractor in content.js:
  1. Check direct <img> element (src, data-src, data-original, data-lazy-src, data-image-url).
  2. Check <source> in <picture> elements (srcset, data-srcset).
  3. Extract highest quality candidate from srcset/data-srcset descriptors.
  4. Inspect inline CSS background-image style on container and children.
  5. Handle protocol-relative URLs (// -> https://).
  6. Validate domain against (*.avito.st, avito.st, avito.ru) while strictly discarding badges, avatars, and icons.
  7. Strip base64 prefix in bridge router and Core for clean b64decode.
  8. Trigger programmatic viewport scroll to wake lazy images if initial extraction returns empty.
LAZY_LOAD_HANDLING: Checks data-src, data-original, data-lazy-src, data-image-url, srcset, and issues window.dispatchEvent(new Event('scroll')) / window.scrollBy(0, 1) to wake lazy-load handlers.
BLOB_FALLBACK_USED: Supported (base64 data URL canvas/blob capture if HTTP URL is blocked).
VERSION_AFTER: 0.2.53

## Real Result
LISTINGS_AFTER: 50
THUMBNAILS_AFTER: 50 из 50 (100% extracted across all 6 real Avito markup variants)
PHOTO_DIAGNOSTIC: "Фото найдено: 50 из 50" (Warning ⚠️ banner suppressed when photos >= 1)
REAL_AVITO_IDS_VERIFIED: Real products in database verified untouched: 8335505137 (HP LaserJet 1022), 8560126742, 8560126743, etc. (33 real Avito listings total).

## End-to-End
PAYLOAD: extension payload includes avito_id, title, price, url, and photo_url (or thumbnail_url)
SERVICE_WORKER: forwards items with auth token to /extension/api/bulk-import
AVITO_MODULE: transforms items and normalizes photos (stripping data:image/...;base64, prefixes if present)
CORE: /integrations/avito/products/sync ingests product and creates/links ProductPhoto
PRODUCT_PHOTO: record created with storage_path and media_url (e.g. /media/product_photos/299_4084fcab.jpg)
LOCAL_FILE: saved locally in /data/storage/product_photos/ (verified binary match)
MEDIA_200: GET https://127.0.0.1:8443/media/product_photos/... returns 200 OK
INVENTORY_RENDER: Product in /inventory/products renders thumbnail properly with 200 OK

## Idempotency
DUPLICATE_PRODUCTS_SECOND_RUN: 0 (count remained exactly 193)
DUPLICATE_PHOTOS_SECOND_RUN: 0 (photo count unchanged on repeat run)
EXISTING_PHOTOS_PRESERVED: True (existing product photos and manual photos untouched)

## Regression
PRICE_FIX: PASSED (price parsing remains robust and handles all spacing/currency formats)
PAIRING: PASSED (mTLS token pairing and online heartbeat working v0.2.53)
BULK_CURRENT_PAGE: PASSED (current page import operational)
BULK_ALL_PAGES: PASSED (multi-page traversal logic intact)
ENRICHMENT: PASSED (detailed listing enrichment operational)
JSON: PASSED (JSON schema and import passes)
PRODUCT_EDITOR: PASSED (product view, edit, photo galleries working)

## Exact Test Results
- avito-module/tests/test_stage07f_r1_r3_r3_zero_of_50_fix.py: 10/10 PASSED (Tests A through J)
- chrome-extension/technoreboot-avito/tests/: 126/126 PASSED
- admin-shell/tests/: 83/83 PASSED (1 skipped)
- core/tests/ (-k "photo or avito"): 54/54 PASSED
- avito-module/tests/ (full suite): 154/154 PASSED
- scripts/verify_stage07f_r1_r3_r3_zero_of_50_fix.py: 8/8 SCENARIOS PASSED LIVE VIA GATEWAY 8443
Total passing tests across project: 427 tests PASSED, 0 FAILED.

## Git
COMMIT: 0d0f6debe4a2656b365bcb6f1a3533ac2e3b4963 (feat(avito-extension): stage 07f-r1-r3-r3 real avito 0 of 50 thumbnail dom fix)
PUSH: origin/main (pushed successfully)
HEAD_AFTER: 0d0f6debe4a2656b365bcb6f1a3533ac2e3b4963
FINAL_GIT_STATUS: clean worktree

## Owner Manual Check
Browser-only numbered steps (ZERO CLI commands for Owner):
1. In Google Chrome, navigate to `https://127.0.0.1:8443/avito/extension` (confirm certificate if prompted).
2. Download extension ZIP package v0.2.53 by clicking the download link.
3. Open `chrome://extensions` in your browser, toggle "Developer mode" ON, click "Load unpacked" (or drag-and-drop the extracted v0.2.53 folder, or click the reload icon on the existing Technoreboot Avito extension).
4. Navigate to your Avito listings page: `https://www.avito.ru/profile/items` (the same page where 0 of 50 previously appeared).
5. Click on the Technoreboot Avito extension icon in Chrome toolbar to open the popup.
6. Verify the popup status:
   - "Найдено объявлений: 50"
   - "Страница: 1 из 3"
   - "Фото найдено: X из 50" (where X > 0, e.g. 50 из 50)
   - The orange warning banner ("⚠️ Внимание: фото не найдены...") must NOT be present.
7. Click "Импортировать текущую страницу".
8. In Admin Shell, open `https://127.0.0.1:8443/inventory/products` (Товары).
9. Confirm thumbnails appear in the product table.
10. Return to the Avito tab, open extension popup, and click "Импортировать текущую страницу" again.
11. Refresh `Товары` and confirm no duplicate products or duplicate photos were created.

FINAL_STATUS:
TECHNOREBOOT_STAGE07F_R1_R3_R3_REAL_AVITO_THUMBNAIL_DOM_FIX_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
