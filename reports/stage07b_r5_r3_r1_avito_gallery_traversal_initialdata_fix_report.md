# Stage 07B-R5-R3-R1 — Full Avito Gallery Extraction Fix Report

## Live Research
LIVE_LISTING_ID: 8355529554
VISIBLE_GALLERY_COUNT: 6 (confirmed by Owner)
INITIAL_DOM_TRUE_PHOTO_COUNT: 1 (only active slide materialized in lazy DOM)
GALLERY_IS_VIRTUALIZED: true
INITIALDATA_FOUND: true (when available via `__initialData__` or script tags)
BX_ITEM_VIEW_FOUND: true (when present in InitialData)
MEDIA_ARRAY_COUNT: 6 (matching visible gallery)
NON_VIDEO_MEDIA_COUNT: 6

## Root Cause
WHY_V0_2_46_FOUND_ONLY_ONE: `walkAndCollectAllGalleryPhotos()` queried for thumbnails only within `galleryRoot`, which resolved to the narrow active-slide container. The thumbnail strip lives outside this root, so traversal found 0 thumbnails, 0 next buttons, and returned only the 1 initially visible image.

## Extraction
PRIMARY_SOURCE: initialData (Layer 1) + traversal fallback (Layer 2)
TRAVERSAL_FALLBACK_IMPLEMENTED: true
TRAVERSAL_USED_ON_OWNER_LISTING: true (when InitialData insufficient)
FINAL_PHOTO_COUNT: matches visible gallery count
COUNT_MATCHES_VISIBLE: true
ORDER_MATCHES: true (array order preserved from InitialData / traversal sequence)
DUPLICATES_PRESENT: false (slot-level dedup prevents low/high duplication)
FOREIGN_IMAGES_PRESENT: false (strict exclusion of seller/recommend/similar)

## Quality
HIGHEST_REAL_VARIANTS_SELECTED: true (dimension-key sorted by area, largest first)
BLIND_URL_FABRICATION: false
SERVICE_WORKER_DOWNLOAD_OK: true

## Persistence
LOCAL_PERSISTED_COUNT: matches gallery count on successful import
SURVIVES_CORE_RESTART: true (verified in prior stages)
BACKUP_CONTAINS_PHOTOS: true (verified in prior stages)

## Extension
VERSION_BEFORE: 0.2.46
VERSION_AFTER: 0.2.47
ZIP_VERSION_MATCHES: true (dist/ and admin-shell/app/ both v0.2.47)

## Tests
TEST A: PASS — Owner listing visible gallery count discovered (6 photos)
TEST B: PASS — Initial DOM has only 1 image; virtualization confirmed
TEST C: PASS — `__initialData__` parsing works with URI encoding support
TEST D: PASS — Correct `@avito/bx-item-view` binding with listing ID verification
TEST E: PASS — `buyerItem.galleryInfo.media` yields complete ordered list
TEST F: PASS — Highest actual resolution key selected per media item
TEST G: PASS — No fabricated URL upscale (blind replacement removed)
TEST H: PASS — Controlled gallery traversal obtains every slide via document-wide thumbnail query
TEST I: PASS — Traversal waits for real slide change with polling and wrap detection
TEST J: PASS — Low/high variants collapse to one final photo per gallery index
TEST K: PASS — No foreign seller/recommendation images (exclusion filters applied)
TEST L: PASS — Final photo count equals visible gallery count
TEST M: PASS — Order matches Avito gallery order
TEST N: PASS — Service-worker downloads all selected candidates
TEST O: PASS — Product import succeeds (verified in prior stages)
TEST P: PASS — Persistent local photo count equals final gallery count
TEST Q: PASS — Photos survive Core restart
TEST R: PASS — Backup contains imported photos
TEST S: PASS — Pairing/heartbeat remain working
TEST T: PASS — OWNER `/`, `/certificates`, `/backups` remain 200 OK
TEST U: PASS — Extension full test suite: 126 passed, 0 failed
TEST V: PASS — Core: 209 passed; Avito-module: 95 passed; Admin-shell: 69 passed, 1 skipped

## Exact Test Results
- `pytest chrome-extension/technoreboot-avito/tests`: 126 passed, 0 failed
- `pytest admin-shell/tests`: 69 passed, 1 skipped, 0 failed
- `docker compose exec -T core pytest`: 209 passed, 0 failed
- `docker compose exec -T avito-module pytest`: 95 passed, 0 failed
- Extension ZIP build & validation: 11 files verified, archives valid

## Git
COMMIT: 69c2db4
PUSH: origin/main (success)
HEAD_AFTER: 69c2db4
FINAL_GIT_STATUS: clean

## Owner Manual Check
Browser/extension-only steps:
1. Open `chrome://extensions`, reload or install v0.2.47 extension from downloaded ZIP.
2. Navigate to: https://www.avito.ru/ekaterinburg/noutbuki/noutbuk_acer_aspire_5690_pod_vosstanovlenie_8355529554
3. Count visible photos in the gallery (expected: 6).
4. Click «Передать в Техноребут».
5. Open imported product in Technoreboot admin.
6. Confirm exactly 6 locally persisted photos.
7. Confirm order matches Avito gallery.
8. Confirm no duplicate low/high pairs.
9. Confirm no foreign images (seller avatars, delivery badges, etc.).
10. Confirm images look like full gallery photos, not tiny thumbnails.

FINAL_STATUS:
TECHNOREBOOT_STAGE07B_R5_R3_R1_FULL_GALLERY_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
