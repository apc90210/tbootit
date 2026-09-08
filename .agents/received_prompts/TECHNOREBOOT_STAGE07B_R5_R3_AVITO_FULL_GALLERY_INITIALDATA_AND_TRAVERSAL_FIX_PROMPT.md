# TECHNOREBOOT — Stage 07B-R5-R3
## Fix Avito “only one photo found”: full gallery via __initialData__ + browser traversal fallback

**Project:** ТехноРебут
**Workspace:** `C:\tbootit`
**Stage:** `Stage 07B-R5-R3 — Full Avito Gallery Extraction`

---

# 0. EXECUTION CONTRACT

Stage 07B-R5-R2 is NOT accepted.

Owner manual check on the real Avito listing showed:

- Avito visually has multiple listing photos;
- Extension v0.2.45 detects/imports only ONE photo — the currently visible/main image;
- therefore the R5-R2 “strict gallery DOM scope” became too restrictive for Avito’s current lazy/virtualized gallery.

The Owner explicitly reports that an older approach was practically usable:
- extension/browser advanced through gallery photos;
- each next photo became visible;
- extractor collected photos as they materialized;
- it sometimes collected both low and high variants, causing duplicates;
- despite duplicates, it found ALL photos.

This stage must restore FULL-GALLERY discovery first, then deduplicate/select best quality safely.

Do NOT abandon the feature.
Do NOT assume all gallery images coexist in the DOM.
Do NOT use global document-wide `img` scraping as primary source.
Do NOT redesign unrelated Avito import.
Do NOT start Internet deployment.

First copy this exact prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07B_R5_R3_AVITO_FULL_GALLERY_INITIALDATA_AND_TRAVERSAL_FIX_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07B_R5_R3_AVITO_FULL_GALLERY_INITIALDATA_AND_TRAVERSAL_FIX_PROMPT.md`

Treat it as authoritative.

---

# 1. PRIMARY REAL TEST LISTING

Use the same Owner-provided listing:

`https://www.avito.ru/ekaterinburg/noutbuki/noutbuk_acer_aspire_5690_pod_vosstanovlenie_8355529554`

Listing ID:

`8355529554`

Owner reports this listing has multiple photos and v0.2.45 currently finds only one.

Do not hard-code the number from previous automated reports.

Determine the live count in Chrome.

---

# 2. RESEARCH FINDING — IMPORTANT

Current publicly maintained Avito extraction logic demonstrates that Avito detail pages can expose the complete media gallery in embedded page initial data.

A known working Avito extraction pattern is:

1. locate page data from `__initialData__`;
2. JSON.parse it;
3. find a top-level key containing:
   `@avito/bx-item-view`
4. read:
   `buyerItem.galleryInfo.media`
5. each media item may expose:
   `urls`
   keyed by real resolution strings such as:
   `640x480`, `1280x960`, etc.;
6. choose the largest REAL provided resolution for that media item.

This must be researched and tested on the current live Owner listing before relying on brittle gallery DOM enumeration.

The existing public extractor logic conceptually does:

```javascript
const data = ... __initialData__ ...
const dataJson = JSON.parse(data);

for (const key in dataJson) {
  if (key.includes('@avito/bx-item-view')) {
    media = dataJson[key].buyerItem.galleryInfo.media;
  }
}

for (const item of media) {
  if (item.isVideo) {
    // skip or separately handle video
    continue;
  }

  // item.urls contains real size -> URL variants
  // choose greatest width*height
}
```

Do not copy external code blindly.
Implement equivalent logic cleanly in our extension.

---

# 3. PROBABLE ROOT CAUSE TO VERIFY

Strong hypothesis:

Avito’s current gallery is lazy/virtualized.

Only the active/main slide image exists as a useful `<img>` inside the strict gallery root at extraction time.

Therefore R5-R2 correctly rejected foreign page images but unintentionally also rejected/unavailable all non-materialized gallery photos.

Expected evidence:

- visible gallery count N > 1;
- strict DOM query initially returns only 1 true gallery image;
- switching gallery slide causes a DIFFERENT image URL to appear in the same active image element.

You MUST prove or disprove this on listing `8355529554`.

Final report:

```text
GALLERY_IS_VIRTUALIZED:
INITIAL_TRUE_GALLERY_IMAGES_IN_DOM:
VISIBLE_GALLERY_COUNT:
```

---

# 4. NEW EXTRACTION STRATEGY — 3 LAYERS

Implement the strategy in this exact priority.

## LAYER 1 — Avito embedded `__initialData__` / item-view state

This is preferred when available.

### 4.1 Locate safely

Search page `<script>` / accessible initial state for current listing detail data.

Support both known forms:

- `<script ... id/name containing __initialData__ ...>JSON</script>`;
- JS assignment containing encoded `__initialData__`.

Do not execute arbitrary page script.

Extract text/data only.

### 4.2 Bind to current listing

Do NOT simply take the first `@avito/bx-item-view`.

Verify the state corresponds to the current detail page / current listing.

Use available current listing ID, item ID, canonical URL, buyer item ID or other strong evidence.

Never import recommendation-card media from another item state.

### 4.3 Read gallery

Look for:

`buyerItem.galleryInfo.media`

For each media object:

- preserve array order;
- skip video objects from photo list when `isVideo == true`;
- inspect `urls`;
- retain ALL real Avito-provided candidates;
- parse dimension keys `WIDTHxHEIGHT`;
- choose highest actual `width * height`;
- preserve lower candidates for fallback only.

Example internal form:

```json
{
  "index": 0,
  "source": "initialData.galleryInfo.media",
  "candidates": [
    {"width": 640, "height": 480, "url": "..."},
    {"width": 1280, "height": 960, "url": "..."}
  ],
  "selected": "..."
}
```

### 4.4 Do not fabricate URLs

If `1280x960` is present in `urls`, it may be used.

If it is NOT present, do not invent it by string replacement.

---

## LAYER 2 — controlled browser gallery traversal

If Layer 1 is unavailable, malformed, incomplete, or yields fewer photos than visible gallery count:

ACTIVELY WALK THE GALLERY.

This layer is mandatory as fallback because it previously worked in practice.

### 4.5 Determine gallery count

Use:
- visible `X / N` counter;
- thumbnail count;
- structured state count;
- accessible labels/buttons;
- controlled wrap detection.

### 4.6 Traverse

Algorithm:

1. Record current slide.
2. Capture current active image:
   - `srcset`;
   - `currentSrc`;
   - `src`;
   - `<picture><source srcset>`;
   - naturalWidth/naturalHeight if loaded.
3. Store candidates for current gallery index.
4. Find the gallery NEXT button using semantic/structural selectors.
5. Click NEXT exactly once.
6. Wait for actual image change:
   - URL/currentSrc change OR
   - content hash/image element load change OR
   - gallery counter changes.
7. Capture next slide.
8. Repeat until:
   - expected count N reached; OR
   - returned to first photo; OR
   - no new photo after bounded retries.

Important:
- do not click outside the gallery;
- do not click recommendation cards;
- do not trigger navigation away from listing;
- use short bounded waits;
- restore first slide at end when practical.

### 4.7 Fullscreen viewer is allowed

If clicking the main photo opens Avito’s full-screen/lightbox gallery and that viewer exposes higher-quality images more reliably:

- opening the gallery viewer is allowed;
- traverse its next-photo control;
- capture active image at each position;
- close viewer after extraction.

This matches the Owner-described previously working behavior.

Do not treat opening the gallery as a problem; it can be the robust fallback.

---

## LAYER 3 — scoped DOM only

Use R5-R2 strict DOM extraction only as the last fallback.

It must not be the sole source of truth when visible count > discovered count.

---

# 5. CRITICAL COMPLETENESS RULE

If Avito visibly reports N listing photos:

Successful extraction requires:

`unique_photo_slots == N`

Do not return full success with 1 when N > 1.

Return explicit partial diagnostic instead.

Example:

`Найдено только 1 из 6 фотографий объявления.`

The import may continue with a warning only if current system semantics allow partial import, but the extension must not claim “all photos imported”.

---

# 6. QUALITY SELECTION

For each PHOTO SLOT independently:

1. gather all real candidates from:
   - `galleryInfo.media[].urls`;
   - active fullscreen/current gallery `srcset`;
   - `currentSrc`;
   - normal `src`;
2. parse actual dimensions when known;
3. select the largest real candidate;
4. download via service worker;
5. if download fails:
   - try next smaller candidate for SAME photo slot;
6. never substitute another photo.

Preferred ranking:
- explicit size key from `galleryInfo.media.urls`;
- explicit `srcset` width;
- full-screen active candidate with verified natural dimensions;
- `currentSrc`;
- `src`.

---

# 7. DEDUPLICATION — DO NOT REPEAT THE OLD “2 COPIES EACH” PROBLEM

The Owner said old traversal found everything but often collected low+high variants separately.

Fix that at the PHOTO SLOT level.

One gallery position = one final Technoreboot photo.

Deduping rules:

- primary identity: `gallery_index` from media array/traversal;
- secondary: canonical Avito image identity/path;
- tertiary: downloaded content hash when variants decode to identical bytes.

Do not flatten all discovered URLs directly into the outgoing `photos[]`.

Instead:

```text
gallery slot 0
  -> low candidate
  -> high candidate
  -> choose one

gallery slot 1
  -> low candidate
  -> high candidate
  -> choose one
```

Final outgoing photo count should equal gallery photo count, not candidate count.

---

# 8. SERVICE WORKER DOWNLOAD

Keep R5-R2 service-worker approach.

Requirements:

- `host_permissions` for `https://*.img.avito.st/*`;
- fetch selected candidate;
- HTTP `response.ok`;
- `Content-Type: image/*`;
- <= current Core byte limit;
- Base64 through safe chunking;
- SHA-256/content hash;
- fallback only within same photo slot.

Do not move CDN downloading back into page content script.

---

# 9. PERSISTENCE

Keep R5-R1 persistence contract:

- final selected photo bytes saved under persistent Core storage;
- no `/tmp` durable success;
- DB path reflects actual persistent file;
- source URL retained as provenance if supported;
- photos survive Core restart;
- backup contains them.

---

# 10. LIVE DIAGNOSTICS ON LISTING 8355529554

For the real listing log/report a sanitized diagnostic:

```json
{
  "listing_id": "8355529554",
  "visible_gallery_count": 0,
  "initial_data_found": true,
  "item_view_key_found": true,
  "media_array_count": 0,
  "non_video_media_count": 0,
  "initial_dom_gallery_image_count": 0,
  "traversal_used": false,
  "traversal_unique_slides": 0,
  "final_photo_count": 0,
  "photos": [
    {
      "index": 0,
      "source": "initialData|traversal|dom",
      "candidate_count": 0,
      "selected_resolution": "1280x960",
      "download_ok": true,
      "bytes": 0,
      "sha256": "..."
    }
  ]
}
```

Do not include base64/tokens.

---

# 11. TEST OWNER-PROVIDED LISTING FOR REAL

Mandatory browser-equivalent test on:

`8355529554`

Requirements:

1. Open live listing.
2. Determine visible gallery count N.
3. Extract using new layered algorithm.
4. Verify final count = N.
5. Verify each image visually corresponds to gallery slot 1..N.
6. Verify order.
7. Verify no foreign images.
8. Verify highest real candidate used per slot when available.
9. Import product.
10. Open Technoreboot product.
11. Verify exactly N locally persisted photos.
12. Restart Core.
13. Verify photos remain.

If current listing becomes unavailable, use another live laptop/computer listing with multiple photos AND record the replacement URL/ID. But attempt Owner listing first.

---

# 12. SECONDARY TESTS

Test at least:

- one 1-photo listing;
- one multi-photo listing;
- one listing where not all slides are initially present in DOM;
- if possible, listing with video + photos to ensure video is not counted as a photo.

---

# 13. EXTENSION VERSION

Current owner-tested version: `0.2.45`.

This stage WILL modify extension source, so bump exactly once to:

`0.2.46`

unless current HEAD already advanced beyond 0.2.45.

Then use next patch version.

Verify:
- source manifest;
- downloadable ZIP;
- Admin Shell displayed version;
- package tests.

---

# 14. REQUIRED TESTS

## TEST A
Owner listing visible gallery count discovered.

## TEST B
Initial DOM image count documented; verify virtualization/lazy-loading hypothesis.

## TEST C
`__initialData__` parsing works when present.

## TEST D
Correct `@avito/bx-item-view` current listing state selected.

## TEST E
`buyerItem.galleryInfo.media` yields complete ordered photo list when present.

## TEST F
Highest actual resolution key selected per media item.

## TEST G
No fabricated URL upscale.

## TEST H
Controlled gallery traversal obtains every slide when initialData is missing/incomplete.

## TEST I
Traversal waits for real slide change and terminates safely.

## TEST J
Low/high variants collapse to one final photo per gallery index.

## TEST K
No foreign seller/recommendation images.

## TEST L
Final photo count equals visible gallery count on Owner listing.

## TEST M
Order matches Avito.

## TEST N
Service-worker downloads all selected candidates.

## TEST O
Product import succeeds.

## TEST P
Persistent local photo count equals final gallery count.

## TEST Q
Photos survive Core restart.

## TEST R
Backup contains imported photos.

## TEST S
Pairing/heartbeat remain working.

## TEST T
OWNER `/`, `/certificates`, `/backups` remain 200.

## TEST U
Extension full test suite passes.

## TEST V
Core/Avito/Admin relevant suites pass.

---

# 15. OWNER MANUAL CHECK

Browser/extension only:

1. Install/update extension to the new version.
2. Open:
   `https://www.avito.ru/ekaterinburg/noutbuki/noutbuk_acer_aspire_5690_pod_vosstanovlenie_8355529554`
3. Count photos visually.
4. Click `Передать в Техноребут`.
5. Open imported product.
6. Confirm Technoreboot contains the SAME number of photos.
7. Confirm order matches.
8. Confirm no duplicate low/high pairs.
9. Confirm no foreign images.
10. Confirm images look like full gallery photos, not tiny thumbnails.

No terminal instructions.

---

# 16. PROJECT RECORDS

Preserve prompt:

`.agents\received_prompts\TECHNOREBOOT_STAGE07B_R5_R3_AVITO_FULL_GALLERY_INITIALDATA_AND_TRAVERSAL_FIX_PROMPT.md`

Create/update:

`docs\stage07b_r5_r3_avito_full_gallery_initialdata_and_traversal_fix.md`

`reports\stage07b_r5_r3_avito_full_gallery_initialdata_and_traversal_fix_report.md`

`logs\2026-09-08.md`

The report MUST explicitly contain:

```text
LIVE_LISTING_ID:
VISIBLE_GALLERY_COUNT:
INITIAL_DOM_TRUE_PHOTO_COUNT:
INITIALDATA_FOUND:
BX_ITEM_VIEW_FOUND:
MEDIA_ARRAY_COUNT:
TRAVERSAL_USED:
FINAL_PHOTO_COUNT:
ORDER_OK:
DUPLICATES_OK:
FOREIGN_IMAGES_OK:
```

---

# 17. GIT / SAFETY

Before commit:
- no downloaded real product photos committed;
- no runtime DB;
- no backup archive;
- no tokens;
- no pairing codes;
- no auth secrets.

Commit safe source/tests/docs only.
Push `origin/main`.
Verify clean worktree.

---

# 18. FINAL REPORT CONTRACT

Return:

```text
# Stage 07B-R5-R3 — Full Avito Gallery Extraction

## Live Research
LIVE_LISTING_ID:
VISIBLE_GALLERY_COUNT:
INITIAL_DOM_TRUE_PHOTO_COUNT:
GALLERY_IS_VIRTUALIZED:
INITIALDATA_FOUND:
BX_ITEM_VIEW_FOUND:
MEDIA_ARRAY_COUNT:
NON_VIDEO_MEDIA_COUNT:

## Root Cause
WHY_V0_2_45_FOUND_ONLY_ONE:

## Extraction
PRIMARY_SOURCE:
TRAVERSAL_FALLBACK_IMPLEMENTED:
TRAVERSAL_USED_ON_OWNER_LISTING:
FINAL_PHOTO_COUNT:
COUNT_MATCHES_VISIBLE:
ORDER_MATCHES:
DUPLICATES_PRESENT:
FOREIGN_IMAGES_PRESENT:

## Quality
HIGHEST_REAL_VARIANTS_SELECTED:
BLIND_URL_FABRICATION: false
SERVICE_WORKER_DOWNLOAD_OK:

## Persistence
LOCAL_PERSISTED_COUNT:
SURVIVES_CORE_RESTART:
BACKUP_CONTAINS_PHOTOS:

## Extension
VERSION_BEFORE:
VERSION_AFTER:
ZIP_VERSION_MATCHES:

## Tests
TEST A:
...
TEST V:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser/extension-only steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07B_R5_R3_FULL_GALLERY_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If the live listing visually has N > 1 but final extraction still returns 1, return BLOCKED.

---

# 19. STOP

After implementation, live verification, tests, docs, commit/push and report:

STOP.

Do not start JSON import/export.
Do not start Internet deployment.
Wait for Owner acceptance.
