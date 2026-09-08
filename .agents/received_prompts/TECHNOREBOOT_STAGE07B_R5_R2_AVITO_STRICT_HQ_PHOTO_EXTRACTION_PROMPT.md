# TECHNOREBOOT — Stage 07B-R5-R2
## Strict Avito listing photo extraction: ALL listing photos, correct order, highest available quality, no foreign images

**Project:** ТехноРебут  
**Workspace:** `C:\tbootit`  
**Stage:** `Stage 07B-R5-R2 — Strict HQ Avito Photo Extraction`

---

# 0. EXECUTION CONTRACT

A new Owner-visible defect remains in the accepted Avito import flow:

- the Chrome Extension is able to read/import an Avito listing;
- but photo extraction is currently not trustworthy;
- the extractor may collect unrelated images from the page and/or wrong image variants;
- the required behavior is to import **only the actual photos belonging to the current Avito listing**, **all of them**, **in original gallery order**, at the **highest real quality made available by Avito to the browser**, and persist them in Technoreboot.

This stage is deliberately focused on **photo discovery, selection, download, transfer, persistence and verification**.

Do NOT redesign general Avito parsing.
Do NOT redesign product schema.
Do NOT change mTLS.
Do NOT change backup UI.
Do NOT start Internet deployment.
Do NOT add server-side Avito scraping.
Do NOT depend on an external paid scraper.
Do NOT scrape search/recommendation cards as a source of listing photos.
Do NOT invent image URLs by blind string replacement.

First copy this exact prompt:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE07B_R5_R2_AVITO_STRICT_HQ_PHOTO_EXTRACTION_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE07B_R5_R2_AVITO_STRICT_HQ_PHOTO_EXTRACTION_PROMPT.md`

Treat the copied prompt as authoritative.

---

# 1. PRIMARY REAL-LISTING TEST CASE

Use this Owner-provided Avito listing as the main real-world test case:

`https://www.avito.ru/ekaterinburg/noutbuki/noutbuk_acer_aspire_5690_pod_vosstanovlenie_8355529554`

Listing ID:

`8355529554`

The implementation must be validated against the actual live page in Chrome / the same browser context where the Technoreboot extension operates.

Do not infer the number of photos from old fixtures.

Determine the real current gallery count from the page itself.

---

# 2. RESEARCH-BACKED RULES

The implementation must follow these rules.

## 2.1 Modern Avito photo URLs

Current public Avito scraper implementations expose listing photo galleries as URLs on Avito image CDN hosts, commonly in the modern form:

`https://NN.img.avito.st/image/1/...`

Do not require `.jpg` in the URL.

Do not assume legacy `/640x480/...jpg` URL format.

Legacy Avito URLs historically exposed explicit resolution paths such as `640x480` and `1280x960`, but this is not a safe universal rule for modern `image/1/...` URLs.

Therefore:

**Never create “high-resolution” URLs simply by replacing `640x480` with `1280x960` unless that exact candidate is actually present or is fetched and explicitly verified.**

## 2.2 `srcset`

HTML `srcset` is explicitly designed to expose multiple resolution candidates.

If Avito provides multiple candidates in `srcset`, parse every candidate and its descriptor.

For width descriptors (`320w`, `640w`, `1280w`, etc.), prefer the candidate with the largest width for that SAME photo.

Do not assume the last string is always the biggest without parsing the descriptors.

## 2.3 `currentSrc`

`HTMLImageElement.currentSrc` identifies the actual image resource selected by Chrome.

Capture it, but do not assume it is the maximum available quality: Chrome may select a smaller resource based on viewport/device pixel ratio.

`currentSrc` is a candidate, not the only source.

## 2.4 Cross-origin image fetch

Content scripts are still constrained by the web page's origin for cross-origin requests.

Image byte downloads from `*.img.avito.st` must be performed from the **extension service worker / extension origin**, with the required explicit `host_permissions`.

Do not solve this with page-injected unsafe fetch hacks.

---

# 3. FIRST — AUDIT CURRENT EXTENSION

Before changing code, inspect the current accepted Chrome Extension v0.2.43 (or whatever current HEAD actually contains).

Record:

- manifest version;
- extension version;
- content scripts;
- service worker;
- current listing extraction function(s);
- current photo extraction selectors;
- current photo URL normalization;
- current deduplication;
- current payload shape;
- whether photos are transferred as URL, base64, blob-derived data, or another representation;
- current Avito module/Core expectations;
- current maximum photo byte limits;
- current persistent storage path.

Find exactly why it is “copying everything”.

Look specifically for dangerous patterns such as:

- `document.querySelectorAll('img')`;
- scanning all `img.avito.st` resources on the whole document;
- accepting recommendation-card images;
- seller avatar/logo images;
- banners;
- map tiles;
- navigation thumbnails from unrelated listings;
- video poster frames;
- service UI icons;
- hidden/preloaded recommendation images;
- duplicate thumbnail + main image variants.

Document exact root cause before rewriting.

---

# 4. STRICT GALLERY SCOPE — MOST IMPORTANT RULE

Photo extraction must begin from the **current listing's gallery root**, not from the document globally.

Discover the current live gallery structure on listing `8355529554`.

Use stable semantic anchors where available, in this preference order:

1. listing-specific structured data / embedded state containing the photo gallery;
2. semantic `data-marker` / accessibility-labelled gallery container;
3. the main listing media/gallery section identified structurally relative to the listing content;
4. controlled active-gallery traversal fallback.

Never make a broad document-wide Avito-CDN scan the primary algorithm.

The following must be excluded even if they are hosted on `img.avito.st`:

- seller avatar;
- seller/company logo;
- recommendation cards;
- “similar listings” cards;
- recently viewed listings;
- advertisements/banners;
- icons;
- video thumbnails/posters unless the current product contract explicitly treats them as photos;
- chat images;
- any image outside the current listing gallery.

---

# 5. MULTI-SOURCE GALLERY DISCOVERY

Implement gallery discovery as a layered strategy, not one brittle selector.

For every discovered photo retain provenance:

```text
source_type:
- structured_data
- gallery_srcset
- gallery_picture_source
- gallery_img_src
- gallery_current_src
- active_gallery_traversal
- fallback

gallery_index:
0..N-1

candidate_url:
...

quality_hint:
...
```

## Layer A — structured listing data

Inspect page `<script>` blocks and any safely accessible current listing state for an array of listing photos.

Only accept it when it can be tied to the CURRENT listing ID / current detail page.

Do not parse recommendation-state photos into the product.

If structured data contains the complete ordered photo list, use that as the canonical order and then enrich each item with higher-quality DOM candidates when available.

## Layer B — gallery DOM

Within the verified listing gallery root collect:

- `img.srcset`;
- `img.currentSrc`;
- `img.src`;
- `<picture><source srcset>`;
- image links/hrefs only if they represent gallery media;
- lazy-load attributes actually present in the current Avito DOM.

## Layer C — active gallery traversal

Avito may lazily materialize only visible slides.

If the initial DOM/structured state yields fewer photos than the gallery counter/thumbnail count:

- traverse the actual gallery;
- move next one photo at a time;
- wait for the slide image to materialize/load;
- collect candidates;
- stop on wrap-around / duplicate first photo / expected count reached;
- restore the original slide if practical.

Do not generate uncontrolled clicks elsewhere on the page.

---

# 6. DETERMINE EXPECTED PHOTO COUNT

The extractor must know when it has “all” photos.

Determine `expected_photo_count` from the strongest available source:

1. structured gallery array count;
2. gallery thumbnail count;
3. visible gallery counter (for example X / N);
4. unique slides discovered through controlled traversal.

Store both:

```text
expected_photo_count
extracted_photo_count
```

If expected count is known and extracted count does not match, do NOT silently report full success.

Return a diagnostic warning / partial status.

Example:

`Ожидалось 8 фотографий объявления, получено 6.`

---

# 7. PHOTO IDENTITY AND DEDUPLICATION

A single Avito photo may appear as:

- thumbnail;
- main gallery image;
- alternate `srcset` size;
- same URL with different query parameters;
- same CDN object from a different DOM element.

Deduplicate per underlying listing photo, not per raw URL.

Implement a deterministic canonical key.

For modern Avito CDN URLs:

- normalize host to lowercase;
- ignore URL fragment;
- query parameters may be ignored for identity ONLY after confirming they are transformation/cache parameters and not part of image identity;
- preserve the original URL for fetching.

For legacy explicit-size URLs:

- resolution segment may be normalized ONLY FOR THE DEDUP KEY;
- do not mutate the actual fetch URL blindly.

If uncertain, use:
- gallery index,
- canonical path,
- structured photo identity,
- content hash after download

to prevent false merges.

Do not deduplicate two genuinely different photos merely because dimensions/filesize are equal.

---

# 8. HIGHEST AVAILABLE QUALITY SELECTION

For each gallery photo, aggregate all candidates belonging to that photo.

Rank candidates using actual evidence:

1. explicit `srcset` width descriptor;
2. structured-data original/full candidate if clearly identified;
3. candidate observed when full gallery viewer is active;
4. `currentSrc` + known natural dimensions;
5. plain `src` fallback.

Never choose based on filename text alone when stronger evidence exists.

## Important

“Highest quality” means:

**the highest real candidate Avito exposes to the current page/browser and that can be successfully fetched as an image.**

It does NOT mean:
- fabricating an undocumented URL;
- upscaling;
- taking a screenshot;
- using the thumbnail because it loaded first.

---

# 9. DOWNLOAD VALIDATION IN SERVICE WORKER

The content script should discover/describe the photo candidates.

The service worker should perform the actual CDN download.

Ensure manifest `host_permissions` covers the required Avito image CDN, preferably narrowly:

`https://*.img.avito.st/*`

Do not request broad `https://*/*` if unnecessary.

For each selected photo:

1. `fetch(candidateUrl)`;
2. require `response.ok`;
3. validate `Content-Type` starts with `image/`;
4. enforce safe maximum bytes consistent with Core limits;
5. read bytes;
6. compute SHA-256 or another stable content hash if practical;
7. transfer image bytes using the existing accepted payload mechanism;
8. preserve original source URL as metadata.

If a chosen top candidate fails:
- try the next lower verified candidate for the SAME gallery photo;
- do not substitute an unrelated page image.

Record quality fallback in diagnostics.

---

# 10. ORDER MUST MATCH AVITO GALLERY

Persist photos in exact Avito gallery order.

The first Avito gallery photo must become position `0`.

Then `1`, `2`, etc.

Do not sort by:
- URL;
- file size;
- DOM load time;
- hash;
- CDN hostname.

Order comes from the listing gallery.

Core `product_photos.position` (or current equivalent) must reflect this.

---

# 11. PERSISTENCE CONTRACT

For every successfully imported Avito photo:

- bytes must be stored under persistent Technoreboot photo storage;
- DB row must point to the real persistent file;
- source Avito URL must be retained as provenance if the schema supports it;
- file must survive Core/container restart;
- file must be included by backup;
- `/media/...` must serve it successfully.

Do NOT count a remote-only URL as a successfully persisted local photo.

Do NOT use `/tmp` as durable success.

---

# 12. DIAGNOSTIC MODE

Add a developer diagnostic mode that can be used in tests without polluting normal Owner UI.

For the current listing return/log a sanitized structure similar to:

```json
{
  "listing_id": "8355529554",
  "expected_photo_count": 0,
  "gallery_root_strategy": "...",
  "photos": [
    {
      "index": 0,
      "candidate_count": 0,
      "selected_source": "...",
      "selected_quality_hint": "...",
      "download_ok": true,
      "bytes": 0,
      "content_type": "image/jpeg"
    }
  ],
  "foreign_images_rejected": 0,
  "duplicates_rejected": 0
}
```

Do NOT log:
- extension token;
- auth secrets;
- full base64;
- private data.

---

# 13. REAL TEST ON OWNER-PROVIDED LISTING

Mandatory real test:

`https://www.avito.ru/ekaterinburg/noutbuki/noutbuk_acer_aspire_5690_pod_vosstanovlenie_8355529554`

Procedure:

1. Open listing in Chrome with extension active.
2. Determine real gallery count N.
3. Run extraction.
4. Confirm exactly N listing photos are selected.
5. Confirm no unrelated page images are selected.
6. Confirm order matches Avito visually.
7. For each selected photo record:
   - candidate source;
   - selected candidate;
   - quality evidence;
   - byte size;
   - content type.
8. Import into Technoreboot.
9. Open the product card.
10. Compare photo 1..N against Avito gallery 1..N.
11. Restart Core.
12. Re-open product card and verify all N photos remain.

Do not state PASS without real comparison.

---

# 14. SECONDARY REGRESSION CASES

Also test at least:

- one listing with only 1 photo;
- one listing with multiple photos;
- if available, one listing with a video/media tile so video poster is not accidentally imported as a still photo unless explicitly intended.

Prefer Technoreboot-relevant categories:
- laptop;
- printer/MFP;
- monitor;
- PC/components.

---

# 15. DO NOT HARD-CODE ONE AVITO DOM SNAPSHOT

Avito changes generated class names frequently.

Avoid selectors based only on obfuscated CSS module class names.

Prefer:

- `data-marker`;
- semantic attributes;
- ARIA labels/roles;
- structured state;
- verified gallery relationships.

If a generated class is needed as a fallback, isolate it behind a fallback strategy and test the stronger strategies first.

---

# 16. CURRENT EXTENSION VERSION

Inspect current HEAD.

If extension source changes, version bump is REQUIRED.

Expected process:

1. increment patch version once;
2. source `manifest.json` version matches;
3. rebuilt downloadable ZIP manifest matches;
4. Admin Shell UI version matches;
5. tests expect the new version;
6. package contains updated service worker/content script.

Do not report old v0.2.43 if source was changed.

---

# 17. REQUIRED TESTS

## TEST A — Listing scope
Only current listing gallery photos are extracted.

## TEST B — Foreign images
Seller avatar, recommendations, logos and other page images are rejected.

## TEST C — All photos
`extracted_photo_count == expected_photo_count` on listing `8355529554`.

## TEST D — Ordering
Imported order exactly matches gallery order.

## TEST E — srcset
Multiple candidates are parsed correctly; largest actual width candidate wins.

## TEST F — modern Avito URLs
Modern `https://NN.img.avito.st/image/1/...` URLs work without requiring file extension.

## TEST G — no fabricated HQ
No blind `640x480 -> 1280x960` rewrite is used.

## TEST H — CDN fetch
Service worker with host permission successfully fetches selected CDN images.

## TEST I — invalid candidate
Non-image / failed highest candidate falls back only to next candidate for same photo.

## TEST J — dedupe
Thumbnail/main/srcset duplicates produce one photo.

## TEST K — persistent storage
Every successful photo has a real persistent local file.

## TEST L — restart persistence
Photos survive Core restart.

## TEST M — backup
Backup contains imported photos.

## TEST N — web restore
Restore does not break photo-storage bind mount.

## TEST O — extension pairing
Pairing and heartbeat remain working.

## TEST P — product import
Full Avito product import succeeds.

## TEST Q — relevant Core tests
Pass.

## TEST R — relevant Avito module tests
Pass.

## TEST S — Chrome extension tests
Pass.

## TEST T — Owner mTLS regression
`/`, `/certificates`, `/backups` remain working for OWNER.

Report exact totals.

---

# 18. OWNER MANUAL CHECK

Browser/extension only.

Final Owner instructions must be:

1. Open the provided Avito listing.
2. Visually note the number and order of listing photos.
3. Click `Передать в Техноребут`.
4. Open imported product.
5. Confirm the same number of photos exists.
6. Confirm photo order is the same.
7. Confirm there are no seller/recommendation/foreign images.
8. Confirm photos are visually high quality, not thumbnails.
9. Refresh/reopen the product and confirm photos remain.

No terminal instructions for Owner.

---

# 19. PROJECT RECORDS

Preserve prompt:

`.agents\received_prompts\TECHNOREBOOT_STAGE07B_R5_R2_AVITO_STRICT_HQ_PHOTO_EXTRACTION_PROMPT.md`

Create/update:

`docs\stage07b_r5_r2_avito_strict_hq_photo_extraction.md`

`reports\stage07b_r5_r2_avito_strict_hq_photo_extraction_report.md`

`logs\2026-09-08.md`

Report:

- current actual Avito DOM/gallery discovery strategy;
- exact photo count on listing `8355529554`;
- exact root cause of previous over-collection;
- selected quality strategy;
- rejected foreign image counts;
- final extension version;
- actual persisted photo count;
- exact tests.

Do not include tokens/secrets/base64 blobs.

---

# 20. GIT / SAFETY

Before commit:

- no runtime DB;
- no downloaded owner product photos;
- no backup archives;
- no auth keys;
- no extension tokens;
- no pairing codes.

Commit safe source/tests/docs only.

Push `origin/main`.

---

# 21. FINAL REPORT CONTRACT

Return:

```text
# Stage 07B-R5-R2 — Strict HQ Avito Photo Extraction

## Research / Live Page
TEST_LISTING_ID:
TEST_LISTING_URL:
REAL_GALLERY_COUNT:
GALLERY_ROOT_STRATEGY:
STRUCTURED_DATA_USED:
DOM_GALLERY_USED:
ACTIVE_TRAVERSAL_USED:

## Previous Defect
PROVEN_OVER_COLLECTION_ROOT_CAUSE:
FOREIGN_IMAGE_TYPES_PREVIOUSLY_INCLUDED:

## Extraction Contract
EXPECTED_PHOTO_COUNT:
EXTRACTED_PHOTO_COUNT:
ORDER_MATCHES:
ALL_FOREIGN_IMAGES_REJECTED:
DEDUP_OK:

## Quality
MODERN_IMAGE_URLS_SUPPORTED:
SRCSET_PARSED:
HIGHEST_ACTUAL_CANDIDATE_SELECTED:
BLIND_URL_UPSCALE_USED: false
CDN_FETCH_VALIDATED:
PHOTO_BYTE_SIZES:
PHOTO_CONTENT_TYPES:

## Persistence
LOCAL_FILES_CREATED:
PERSISTENT_STORAGE_ONLY:
SURVIVES_CORE_RESTART:
BACKUP_CONTAINS_PHOTOS:
RESTORE_MOUNT_OK:

## Extension
EXTENSION_CHANGED:
VERSION_BEFORE:
VERSION_AFTER:
ZIP_VERSION_MATCHES:

## Runtime Verification
TEST A:
...
TEST T:

## Exact Test Results

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

## Owner Manual Check
Browser/extension-only steps.

FINAL_STATUS:
TECHNOREBOOT_STAGE07B_R5_R2_AVITO_STRICT_HQ_PHOTO_EXTRACTION_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
INTERNET_DEPLOYMENT_NOT_STARTED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

If the extractor cannot prove it got all listing photos and rejected foreign images, return BLOCKED.

---

# 22. STOP

After implementation, real-page verification, docs, tests, commit/push and final report:

STOP.

Do not start JSON import/export stage.
Do not start Internet deployment.
Wait for Owner acceptance.
