# TECHNOREBOOT — Stage 13D LOCAL
## Recover proven full-gallery extraction, remove fast/deep race, make page-state media the primary source

**Project:** ТехноРебут  
**Workspace:** `C:\tbootit`  
**Environment:** LOCAL FIRST  
**Canonical production VDS:** `144.31.15.88` — DO NOT DEPLOY  
**Current extension baseline:** v0.2.65  
**Target extension version:** v0.2.66

# 0. IMPORTANT CONTEXT — THIS IS A REGRESSION RECOVERY, NOT A NEW BLIND EXPERIMENT

The current v0.2.65 still imports only one photo from real Avito listings.

Do NOT continue adding random DOM selectors.

We already have historical proof that this project successfully imported a real multi-photo Avito listing.

Known proven historical stage:

```text
Stage07B-R5-R3
commit: bd7bdc75c765e74c00994e9c4f6f9053b879535a
extension: v0.2.46
real listing id: 8355529554
visible gallery count: 6
initial DOM photo count: 1
initialData found: true
@avito/bx-item-view found: true
buyerItem.galleryInfo.media count: 6
final imported/persisted photo count: 6
foreign photos: 0
duplicates: 0
```

Historical working primary source:

```text
initialData
  -> matching @avito/bx-item-view block
  -> buyerItem.galleryInfo.media
```

Historical result explicitly stated that DOM traversal was NOT needed on that real listing because the structured page state already contained all six photos.

Therefore Stage13D must first answer:

```text
What changed between working v0.2.46 / commit bd7bdc7
and current v0.2.65 that regressed full-gallery extraction to one photo?
```

Then restore the proven architecture in a modernized, deterministic form.

# 1. PROMPT PRESERVATION

Copy this prompt unchanged from:

```text
C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE13D_AVITO_FULL_GALLERY_REGRESSION_RECOVERY_PROMPT.md
```

to:

```text
C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE13D_AVITO_FULL_GALLERY_REGRESSION_RECOVERY_PROMPT.md
```

# 2. SAFETY

LOCAL only.

Do NOT:
- deploy to `144.31.15.88`;
- change production DB/media;
- publish/edit/favorite/message/remove Avito listings;
- use destructive production tests;
- add `chrome.debugger` permission;
- add broad scary permissions merely to simulate trusted clicks;
- guess/fabricate Avito HQ URLs.

Automatic post-sale Avito deactivation remains disabled.

# 3. PREFLIGHT

Record:

```text
git status
git branch --show-current
git rev-parse HEAD
docker compose ps
```

Read:
```text
reports/stage13a_avito_photo_import_diagnostic_report.md
reports/stage13b_avito_exact_n_hq_gallery_import_report.md
reports/stage13c_avito_single_photo_anomaly_diagnostic_report.md
```

Also inspect historical Stage07B-R5-R3 report/docs/logs.

# 4. MANDATORY GIT REGRESSION ARCHAEOLOGY

Before changing code, compare the exact historical working implementation with current code.

Use:

```text
git show bd7bdc75c765e74c00994e9c4f6f9053b879535a:chrome-extension/technoreboot-avito/content.js
git show bd7bdc75c765e74c00994e9c4f6f9053b879535a:chrome-extension/technoreboot-avito/popup.js
git diff bd7bdc75c765e74c00994e9c4f6f9053b879535a..HEAD -- chrome-extension/technoreboot-avito/content.js
git diff bd7bdc75c765e74c00994e9c4f6f9053b879535a..HEAD -- chrome-extension/technoreboot-avito/popup.js
```

Find and document the historical/current versions of at least:

```text
triggerInitialDataCapture
extractPhotosFromEmbeddedState
extractGalleryFromInitialData
extractListingData
extractListingDataMultiPass
walkAndCollectAllGalleryPhotos
extract_current_page message handler
popup scan / import button flow
```

Create a regression matrix:

| function/path | v0.2.46 behavior | v0.2.65 behavior | regression? | fix |
|---|---|---|---|---|

Do NOT implement until this matrix explains why the proven six-photo path stopped being authoritative.

# 5. CORRECT THE STAGE13C ASSUMPTION ABOUT SYNTHETIC EVENTS

Do not write in code/comments/reports that “React 18 ignores synthetic clicks” as a general fact.

Facts:
- programmatically dispatched/click-generated events are untrusted (`isTrusted=false`);
- a specific site handler MAY ignore them;
- this must be proven on the current Avito gallery rather than attributed generically to React.

Therefore:
- DOM navigation is fallback only;
- do not spend this stage trying ever-more-complex PointerEvent/KeyboardEvent sequences as the primary architecture.

# 6. PRIMARY ARCHITECTURE: STRUCTURED PAGE STATE FIRST

The full gallery must be extracted from Avito page state whenever available.

Implement a robust page-state collector with multiple safe sources.

Priority A — historical proven source:
```text
__initialData__
```

Search serialized data for the block representing the CURRENT listing:

```text
key contains @avito/bx-item-view
buyerItem
buyerItem.galleryInfo
buyerItem.galleryInfo.media
```

Mandatory:
- match current listing ID from page URL / extracted listing ID;
- do not accept a bx-item-view for another listing;
- preserve media array order;
- skip `isVideo === true`.

Priority B — modern Avito MFE serialized state:
inspect page-owned `<script>` blocks such as:

```css
script[type="mime/invalid"][data-mfe-state="true"]
script[data-mfe-state="true"]
```

Parse JSON/HTML-unescape where required.

Search only parsed structured objects for the CURRENT listing and a gallery/media collection.

Do not use uncontrolled regex to collect every img.avito.st URL from the entire document as the final gallery.

Priority C — MAIN-world runtime state:
if the data exists only as a page JavaScript variable, use an explicit MAIN-world bridge.

Preferred MV3 mechanism:
```text
chrome.scripting.executeScript({
  target: { tabId },
  world: "MAIN",
  func: ...
})
```

or a manifest content script configured for MAIN world if architecture makes that cleaner.

The MAIN-world function must:
- READ only;
- return JSON-serializable sanitized gallery metadata;
- not expose extension secrets/tokens to the page;
- not mutate Avito runtime state.

# 7. IMPORTANT: MAIN WORLD IS FOR PAGE JS STATE, NOT FOR EXTENSION SECRETS

Never pass:
- extension token;
- TechnoReboot auth credentials;
- pairing code;
- local server secret;
- private keys

into MAIN world.

MAIN-world collector input may contain only:
- current listing ID;
- simple extraction options.

Output may contain only sanitized public listing media metadata:
- listing ID;
- position;
- media type;
- URLs/dimensions.

# 8. PAGE-STATE MEDIA NORMALIZATION

Normalize every structured gallery media item into one logical slot:

```js
{
  slot_index: 0,
  canonical_id: "...",
  variants: [
    { url: "...", width: 1280, height: 960, source: "initialData" }
  ],
  best_url: "...",
  source: "initialData|mfeState|mainWorld"
}
```

If media item has a map like:

```text
urls["140x105"]
urls["640x480"]
urls["1280x960"]
```

parse numeric dimensions and select the largest actual area.

Do NOT assume lexical order.

Do NOT fabricate URLs by replacing size tokens.

One media object = one logical photo.

# 9. FULL-GALLERY SOURCE CONTRACT

Implement an explicit source result:

```js
{
  source: "initialData" | "mfeState" | "mainWorld" | "domTraversal" | "heroOnly",
  listingId: "...",
  expectedCount: N | null,
  photos: [...],
  complete: true|false,
  diagnostics: {}
}
```

The primary extractor must stop falling through to DOM if structured page state already provides a complete gallery.

Example:

```text
initialData media count = 6
visible/count evidence = 6
=> complete=true
=> DO NOT traverse DOM
=> DO NOT replace with fast hero-only result
```

# 10. ELIMINATE THE POPUP FAST/DEEP RACE

This is mandatory.

Current Stage13C report shows:
- popup sends `deepScan:false`;
- gets synchronous hero-only result;
- enables import;
- `deepScan:true` runs later.

That architecture allows a one-photo provisional result to become the actual import payload.

Fix it.

There must be exactly ONE authoritative data object eligible for import.

Allowed UX:

## Option A — preferred
On popup open:
1. run cheap scan only for title/basic preview;
2. start full scan immediately;
3. show `Сканирование галереи…`;
4. IMPORT button remains disabled;
5. only when full scan resolves does the popup set `authoritativeListingData = fullScanResult`;
6. import button becomes enabled.

## Option B
Do only full scan and wait.

Forbidden:
```text
fast result -> import enabled -> deep result may arrive later
```

The provisional fast result must NEVER be passed to `sendListingPayload()`.

# 11. SINGLE PROMISE / REQUEST ID TO PREVENT STALE RESPONSES

Introduce request correlation.

Conceptually:

```text
scanRequestId = random/incrementing ID
```

When a full scan starts:
- mark it active;
- ignore any result whose request ID is older;
- navigating to another Avito listing invalidates previous scan;
- popup close/reopen must not accidentally reuse stale data from another listing.

Import payload must verify:

```text
payload.listingId === activeTab listingId
payload.scanRequestId === current completed scan
payload.scanState === COMPLETE
```

# 12. DO NOT TRUST `__NEXT_DATA__` AS AN ASSUMPTION

The current agent report suggests `window.__initialData__ / __NEXT_DATA__`.

Do NOT assume `__NEXT_DATA__` exists or contains gallery media.

Inspect it if present, but only adopt it if a real current Avito page proves:
- it exists;
- it belongs to current listing;
- it contains all N photo media records.

Historical `__initialData__` / `@avito/bx-item-view` is proven in this project and has priority.

# 13. PAGE-STATE DISCOVERY DIAGNOSTICS

For one real current listing, record:

```text
LISTING_ID
VISIBLE_GALLERY_COUNT
INITIAL_DOM_IMG_COUNT
__initialData__ present?
@avito/bx-item-view present?
matching current listing block found?
galleryInfo.media count?
data-mfe-state script count?
matching MFE gallery array found?
MAIN-world gallery found?
chosen source?
chosen photo count?
```

Do not claim a source exists without real browser evidence.

# 14. DOM TRAVERSAL IS FALLBACK ONLY

If all structured-state methods fail, `domTraversal` may run.

But it must:
- be scoped to the current listing gallery;
- never use page-wide image scans;
- collect canonical IDs;
- compare against authoritative count if available;
- use click/navigation only as best-effort fallback.

If programmatic navigation does not change the active image:
- report that fact;
- stop bounded traversal;
- do not loop indefinitely;
- never pretend it succeeded.

# 15. HERO-ONLY IS LAST-RESORT DEGRADED MODE

If only the active hero can be obtained:

```text
source = "heroOnly"
complete = false
```

Popup must clearly say:

```text
Найдена только 1 фотография из галереи.
Полный импорт фото не готов.
```

For a known multi-photo listing, do NOT silently present this as a successful complete scan.

Owner may still be allowed to import product data with one photo only if existing UX requires it, but this must be explicit and not masquerade as full gallery success.

# 16. COUNT CONSISTENCY

If any of these give N:
- structured media length;
- gallery visual counter;
- unique thumbnails;

compare them.

Example:
```text
structured media = 6
counter = 6
=> strong complete result
```

Mismatch:
```text
structured media = 1
counter = 6
=> incomplete; do not call complete
```

Diagnostic must expose the mismatch.

# 17. SERVICE WORKER / CORE

Keep Stage13B good work:
- canonical ID V2;
- one logical slot -> one download;
- HQ first, same-slot fallback;
- Content-Type validation;
- Core defensive dedupe;
- no HQ + low double append.

Do not regress those fixes.

Structured page-state photo list should feed into the same normalized logical-slot/download pipeline.

# 18. HISTORICAL REGRESSION TEST — MANDATORY

Create a test fixture from the historical proven shape:

```text
@avito/bx-item-view
buyerItem.galleryInfo.media
6 photos
each with multiple urls sizes
one video variant optionally included
```

Test:
```text
input media logical count = 6
video excluded
output photo count = 6
order preserved
best real resolution selected
no DOM traversal invoked
```

# 19. CURRENT MFE STATE TEST — MANDATORY IF FOUND LIVE

If current Avito real page exposes `data-mfe-state` gallery data:
- save a sanitized minimal fixture containing only schema shape/public fake URLs;
- test extraction;
- no real copyrighted image bytes.

If not found:
- report `MFE_STATE_GALLERY_NOT_FOUND_ON_TEST_PAGE`;
- do not invent the test.

# 20. POPUP RACE TESTS — MANDATORY

Tests must prove:

1. fast provisional returns 1 photo first;
2. import remains disabled;
3. deep structured scan later returns 6;
4. import becomes enabled only after deep complete result;
5. `sendListingPayload()` receives 6, never 1.

Also:
6. stale deep result from previous listing is ignored;
7. switching tab/listing invalidates prior scan;
8. scan failure displays degraded/error state;
9. import button cannot fire while scan pending.

# 21. REAL BROWSER VALIDATION — REQUIRED, NOT A FIXTURE

This stage cannot be accepted from unit tests alone.

Use Chrome / real installed extension against a live Avito listing with multiple visible photos.

Preferred:
- the same historical owner listing `8355529554` if still available;
- otherwise any real listing with a clearly visible count >= 4.

Capture evidence:

```text
REAL_LISTING_ID:
VISIBLE_COUNT:
INITIAL_DOM_COUNT:
STRUCTURED_SOURCE_USED:
STRUCTURED_MEDIA_COUNT:
FINAL_EXTENSION_COUNT:
PERSISTED_LOCAL_COUNT:
HQ_COUNT:
FOREIGN_COUNT:
```

The report must distinguish `REAL_BROWSER` from `FIXTURE / PLAYWRIGHT / SYNTHETIC`.

Do not label fixture simulation as live evidence.

# 22. EXPECTED ACCEPTANCE FOR A REAL 4+ PHOTO LISTING

For a real listing that visibly has N photos:

```text
FINAL_EXTENSION_COUNT == N
PERSISTED_LOCAL_COUNT == N
FOREIGN_COUNT == 0
```

HQ:
- choose largest actual structured URL for each slot;
- if structured state provides HQ for all N, expect HQ_COUNT=N;
- otherwise same-slot fallback is acceptable, but count must remain exact.

# 23. VERSION / BUILD

Bump:
```text
0.2.65 -> 0.2.66
```

Update all version references consistently.

Build canonical ZIP.

Verify:
- manifest;
- syntax;
- CSP;
- ZIP SHA256;
- admin-shell download copy byte-identical.

LOCAL only.

# 24. TESTS

Run at minimum:

```text
pytest chrome-extension/technoreboot-avito/tests/
python scripts/run_targeted_tests.py
python scripts/db_schema_contract.py verify
```

Plus new regression tests for:
- historical initialData 6-photo extraction;
- popup fast/deep race;
- current structured source;
- exact-N persistence.

# 25. REPORT

Create:

```text
reports/stage13d_avito_full_gallery_regression_recovery_report.md
```

Include:
- exact diff explanation from bd7bdc7 to current;
- which previously working path was lost/bypassed;
- what structured source exists TODAY on the tested listing;
- primary source/fallbacks;
- popup synchronization;
- real browser proof.

# 26. FINAL CONTRACT

Return:

```text
# Stage 13D — Avito Full Gallery Regression Recovery

## Regression Archaeology
HISTORICAL_WORKING_COMMIT: bd7bdc75c765e74c00994e9c4f6f9053b879535a
HISTORICAL_VERSION: 0.2.46
HISTORICAL_REAL_LISTING_ID: 8355529554
HISTORICAL_REAL_COUNT: 6
REGRESSION_ROOT_CAUSE:
INITIALDATA_PATH_STILL_PRESENT_BEFORE_FIX:
INITIALDATA_PATH_WAS_BYPASSED_OR_BROKEN:
POPUP_FAST_DEEP_RACE_CONFIRMED:

## Current Page State
REAL_BROWSER_TEST_PERFORMED:
REAL_LISTING_ID:
VISIBLE_GALLERY_COUNT:
INITIAL_DOM_IMG_COUNT:
INITIALDATA_PRESENT:
BX_ITEM_VIEW_PRESENT:
MATCHING_GALLERY_MEDIA_COUNT:
MFE_STATE_PRESENT:
MFE_GALLERY_MEDIA_COUNT:
MAIN_WORLD_REQUIRED:
CHOSEN_PRIMARY_SOURCE:

## Architecture
STRUCTURED_STATE_PRIMARY:
DOM_TRAVERSAL_FALLBACK_ONLY:
HERO_ONLY_LAST_RESORT:
ONE_AUTHORITATIVE_IMPORT_RESULT:
IMPORT_DISABLED_DURING_SCAN:
STALE_SCAN_PROTECTION:
LISTING_ID_MATCH_REQUIRED:

## Photos
FINAL_EXTENSION_PHOTO_COUNT:
PERSISTED_LOCAL_PHOTO_COUNT:
HQ_PHOTO_COUNT:
FALLBACK_PHOTO_COUNT:
FOREIGN_PHOTO_COUNT:
ORDER_PRESERVED:
CORE_DOUBLE_APPEND_STILL_FIXED:

## Tests
HISTORICAL_6_PHOTO_REGRESSION_TEST:
POPUP_RACE_TESTS:
EXTENSION_TESTS:
TARGETED_SUITE:
SCHEMA_GUARD:

## Build
EXTENSION_VERSION: 0.2.66
EXTENSION_ZIP:
EXTENSION_ZIP_SHA256:
ADMIN_DOWNLOAD_HASH_MATCH:

## Safety
PRODUCTION_TOUCHED: false
PRODUCTION_DB_CHANGED: false
AVITO_BUSINESS_ACTIONS_PERFORMED: false
AUTO_AVITO_DEACTIVATION_DISABLED: true

FINAL_STATUS:
TECHNOREBOOT_STAGE13D_LOCAL_READY_FOR_OWNER_ACCEPTANCE
```

# 27. STOP

STOP after LOCAL implementation + automated tests + REAL BROWSER validation.

Do NOT deploy to production.
Wait for Owner acceptance.
