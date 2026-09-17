# TECHNOREBOOT — Stage 13B LOCAL
## Avito Extension: exact-N gallery import + per-photo HQ activation

**Project:** ТехноРебут  
**Workspace:** `C:\tbootit`  
**Environment:** LOCAL FIRST  
**Canonical production VDS:** `144.31.15.88` — DO NOT DEPLOY  
**Baseline extension:** v0.2.63  
**Expected next extension version:** v0.2.64 unless project versioning requires another patch.

# 0. OWNER GOAL

Fix Avito photo import so a listing with N real gallery photos imports:

```text
exactly N photos
only photos belonging to this listing
in gallery order
at the highest reliably available quality
```

Priority order is strict:

```text
1. EXACTNESS — no foreign / unrelated photos
2. COMPLETENESS — get all N listing photos
3. QUALITY — upgrade each of those exact N photos to HQ
```

If there are 4 photos in the listing, the final imported product must have exactly 4 Avito photos — not 9 candidates, not 1 HQ + unrelated extras.

The primary HQ strategy accepted from Stage13A is:

```text
identify the exact gallery slots
-> activate each thumbnail like a user
-> wait until the hero image really switches to that same logical photo
-> capture the highest-quality hero currentSrc/srcset
-> continue to the next exact slot
```

# 1. STAGE13A EVIDENCE — TREAT AS BASELINE

Read first:

```text
reports/stage13a_avito_photo_import_diagnostic_report.md
```

The diagnostic established these current defects:

1. `extractPhotosFromDom()` performs a document-wide thumbnail search instead of restricting candidates to the listing gallery root.
2. `[data-marker*="preview"]` is too broad and can collect sticky UI, recently-viewed items, review attachments, etc.
3. `isInsideExcluded` exists but is effectively dead/not applied to the problematic path.
4. `expectedPhotoCount=N` is detected but not enforced on final candidate slots.
5. current canonical identity logic has collisions/incorrect grouping on observed Avito CDN URL forms.
6. Core can persist both HQ and low-quality variants for one logical photo instead of selecting one best variant.
7. only active hero photo is HQ by default; non-active photos remain thumbnail quality until activated.
8. thumbnail activation causes the matching hero photo to load in higher quality.

Do not repeat exploratory Stage13A.
Implement the evidence-backed fix.

# 2. PROMPT PRESERVATION

Copy this prompt unchanged from:

```text
C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE13B_AVITO_EXACT_N_HQ_GALLERY_IMPORT_PROMPT.md
```

to:

```text
C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE13B_AVITO_EXACT_N_HQ_GALLERY_IMPORT_PROMPT.md
```

# 3. SAFETY / LOCAL ONLY

Before work:

```text
git status
git branch --show-current
git rev-parse HEAD
docker compose ps
```

Preserve uncommitted work.

Do NOT:
- deploy to `144.31.15.88`;
- mutate production DB/media;
- touch legacy VDS;
- publish/edit/favorite/message/remove any Avito listing;
- resurrect automatic Avito post-sale deactivation;
- use destructive production tests.

This stage may read public Avito listing pages through the browser extension for LOCAL verification.

# 4. NO MORE DOCUMENT-WIDE IMAGE COLLECTION FOR LISTING PHOTOS

The listing gallery must become the authority.

Primary gallery root:

```css
[data-marker="item-view/gallery"]
```

Within that root use stable semantic markers where present, including:

```css
[data-marker="image-frame"]
[data-marker="image-frame/image-wrapper"]
[data-marker="image-frame/counter"]
ul[data-marker="gallery/list"]
[data-marker="image-frame/next-button"]
```

Do NOT use these as primary listing-photo discovery:

```css
document.querySelectorAll('[data-marker*="preview"]')
document-wide img scans
hashed CSS classes
recommendation/history/review image regions
```

Fallback selectors are allowed only if:
- they are scoped to a confidently identified listing gallery root;
- tests prove they do not leak foreign page images.

# 5. EXPLICIT GALLERY MODEL

Introduce one internal normalized model for the current listing gallery.

Conceptually:

```js
GalleryPhotoSlot = {
  index: 0,
  canonicalId: "...",
  thumbnailUrl: "...",
  bestKnownUrl: "...",
  hqUrl: null,
  source: "thumbnail|hero|traversal",
  qualityTier: "low|mid|hq",
  width: null,
  height: null
}

GalleryExtraction = {
  expectedCount: N,
  countSource: "counter|thumbnail_count|traversal",
  galleryRootFound: true,
  slots: [ ... exactly N logical slots ... ],
  hqCount: X,
  degraded: false,
  diagnostics: [...]
}
```

Use current project style/naming; this conceptual shape is not a mandatory external API.

The extension must reason in LOGICAL PHOTO SLOTS, not arbitrary URL candidates.

# 6. AUTHORITATIVE PHOTO COUNT N

Implement deterministic count resolution.

Priority:

## A. Primary
Read gallery counter within gallery root:

```css
[data-marker*="counter"]
```

Parse formats such as:

```text
1 из 4
1 / 4
1 of 4
```

Use locale-tolerant numeric extraction.

## B. Secondary
If no reliable counter:
- count unique logical gallery thumbnail items strictly inside `ul[data-marker="gallery/list"]`;
- dedupe by canonical image identity.

## C. Traversal fallback
If thumbnails appear virtualized/incomplete:
- navigate gallery safely and collect unique logical identities until:
  - counter N is reached, or
  - a complete cycle/no-progress condition is detected.

Never infer N from a page-wide number of image candidates.

# 7. CANONICAL AVITO IMAGE IDENTITY V2

Replace/fix current canonical identity logic using the Stage13A-tested V2 behavior.

Requirements:

- host shard differences must not create different logical photos;
- query strings must not create different logical photos;
- responsive size/version suffixes for one Avito photo must collapse together;
- two genuinely different listing photos must never collapse together;
- numeric-path CDN formats must not all become the same generic key;
- preserve an explicit fallback identity when an unfamiliar CDN form appears.

Use Stage13A fixture examples and `scripts/test_canonical_v2.py` as starting evidence, but move the final implementation into production extension code and proper tests.

Do not rely only on filename extension such as `.jpg/.webp`.

Required tests:
- 10 responsive variants of 4 photos -> exactly 4 IDs;
- same photo across `00.img.avito.st`, `01...`, etc. -> one ID;
- two distinct photos with similar prefixes -> two IDs;
- unfamiliar URL form -> stable non-empty fallback identity.

# 8. PHASE 1 — EXACT SLOT DISCOVERY

Implement exact logical slots before HQ traversal.

Algorithm target:

```text
galleryRoot = find exact listing gallery
N = determine expected count
thumbCandidates = collect only inside galleryRoot
canonicalize/dedupe
preserve visual order
produce N logical slots
```

Rules:

- slot order must match Avito visual gallery order;
- hero image may enrich slot #0 but must not become an extra slot;
- src/srcset/currentSrc variants are quality variants, not extra photos;
- no item outside gallery root may create a slot;
- if the DOM contains more scoped candidates than N, truncate only after canonical dedupe and stable order;
- if fewer than N thumbnails are mounted, use traversal fallback — do not pull foreign page images to “fill” missing slots.

# 9. PHASE 2 — HQ ACQUISITION PER EXACT SLOT

For every exact slot `i`:

## Step A — use already available best URL
Inspect within the exact thumbnail/active hero context:

```text
currentSrc
src
srcset
picture > source[srcset]
data-src / lazy source only if scoped and proven relevant
```

Parse `srcset` descriptors correctly and choose the largest candidate by numeric `w` (or density if no width descriptors).

Do NOT assume the last string in `srcset` is always largest without parsing it.

## Step B — activate thumbnail if HQ not already known
For slot `i`:

1. locate the thumbnail representing that slot;
2. `scrollIntoView({block: "nearest", inline: "nearest"})` if needed;
3. invoke the safest normal click path;
4. observe hero image inside:
   ```css
   [data-marker="image-frame/image-wrapper"] img
   ```
5. wait until the hero's canonical ID equals the slot canonical ID;
6. only after identity match, inspect `currentSrc/srcset`;
7. choose highest-quality URL;
8. store it as `hqUrl`.

Do not sample hero URL merely after a fixed sleep.

# 10. WAIT CONDITION — IDENTITY FIRST, LOAD SECOND

Use an event/condition-based wait.

Preferred:
- `MutationObserver` on hero wrapper attributes/subtree;
- image `load` event;
- polling as a bounded fallback.

Success condition:

```text
canonical(hero.currentSrc/src/srcset-best) == slot.canonicalId
AND
hero has a non-empty usable image URL
```

Optional additional readiness:
- `naturalWidth > 0`;
- `complete === true`.

Timing:
- Stage13A observed ~80–180 ms on sample;
- do not hardcode 100 ms;
- use a practical bounded timeout, e.g. ~1–1.5 s with one retry, configurable constant;
- log timeout per slot in diagnostics.

No arbitrary multi-second sleep per photo unless evidence proves it necessary.

# 11. VIRTUALIZED / LONG GALLERIES

Do not assume all N thumbnails are simultaneously mounted.

For long galleries:

1. try direct thumbnail slot when mounted;
2. if next needed slot is not mounted:
   - use gallery next control inside exact gallery;
   - after each step collect the active logical photo identity;
   - continue until desired slot is reached or N unique identities collected;
3. prevent wraparound infinite loops:
   - track canonical IDs;
   - track step count;
   - stop after bounded `N + safetyMargin` transitions;
   - stop on no-progress.

Do not use lightbox as primary method.

Lightbox is allowed only as an optional final fallback if:
- exact gallery identity is preserved;
- it can be entered/exited reliably;
- tests prove no modal state is left behind.

Prefer thumbnail/inline carousel traversal.

# 12. RESTORE PAGE STATE

After traversal:
- return gallery to original active slot when practical;
- avoid leaving a lightbox open;
- do not leave body scroll locked;
- do not scroll page to an unexpected remote position if it can be restored cheaply.

This is UX hygiene; extraction correctness remains priority.

# 13. EXACT-N INVARIANT

Before payload submission:

```text
slots are ordered
slots are unique by canonicalId
slots belong to listing gallery
slots.length == expectedCount
```

If `expectedCount` is reliable and the algorithm cannot resolve all N slots:

DO NOT fill missing slots from unrelated document images.

Use this degradation policy:

1. retry gallery traversal once;
2. if all N logical slots exist but some HQ upgrades fail:
   - keep exact thumbnail/mid-quality URL for those slots;
   - import exactly N correct photos;
3. if fewer than N logical slots can be confidently identified:
   - import only confidently gallery-bound photos OR preserve current safe main-photo fallback according to existing import contract;
   - mark extraction as degraded in diagnostics;
   - never invent/pad with page-wide candidates.

For Owner acceptance sample with 4 photos, expected result is exactly 4/4.

# 14. QUALITY SELECTION

For each slot, maintain candidate URLs only for that canonical ID.

Rank by real evidence:

1. active hero largest parsed srcset/currentSrc;
2. active hero src;
3. scoped thumbnail largest srcset;
4. thumbnail src.

If dimensions are available:
- use pixel area as primary quality score;
- never prefer a larger byte-string URL merely because text looks “HQ”.

If dimensions are not available in extension:
- use parsed width descriptor;
- server can validate decoded dimensions after download if current architecture supports it.

# 15. SERVICE WORKER DOWNLOAD CONTRACT

Update `service_worker.js` so each logical slot causes at most one final imported photo.

For each slot:

```text
try hqUrl
if fetch succeeds with valid image:
    use it
else:
    try bestKnownUrl / thumbnailUrl
```

Do not submit both HQ and fallback for the same logical slot.

Requirements:
- validate HTTP status;
- validate `Content-Type` begins with `image/`;
- preserve slot order;
- preserve canonical ID in diagnostics/payload if backward-compatible;
- no cross-slot fallback.

If existing payload schema cannot carry logical-slot metadata, extend it minimally and backward-compatibly.

# 16. FIX CORE DOUBLE-APPEND BUG

Audit and fix the Stage13A finding in:

```text
core/app/routers/integrations.py
```

Current bad behavior conceptually:
- HQ variant appended;
- low-res variant for same logical photo also appended.

New rule:

```text
ONE logical Avito photo -> ONE persisted ProductPhoto
```

Preferred server behavior:
- choose HQ if successfully provided/validated;
- otherwise choose fallback;
- dedupe again defensively using canonical identity and/or content hash;
- preserve gallery order;
- repeated import must remain idempotent under existing Avito product identity rules.

Do not rely solely on the client to prevent duplicates.

# 17. BACKWARD COMPATIBILITY

Existing older extension payloads must not break if reasonably possible.

Core should continue accepting current photo structures while selecting one best variant per logical photo.

Do not require a DB migration unless absolutely necessary.
No new photo table should be created merely for this.

# 18. DIAGNOSTIC TELEMETRY — SAFE AND MINIMAL

Add useful non-secret extraction diagnostics, e.g.:

```text
expected_photo_count
logical_slots_count
hq_photo_count
fallback_photo_count
foreign_candidates_rejected
traversal_timeouts
count_source
```

Do NOT log:
- extension token;
- pairing code;
- auth secrets;
- image binary/base64;
- private user data not already needed.

These diagnostics may appear in extension console / structured import response / report.

Do not clutter normal popup unless existing status UI already has a natural compact place.

# 19. TEST FIXTURE: EXACT 4 -> EXACT 4

Create a deterministic fixture modeling the diagnosed failure:

```text
4 true gallery photos
+ active hero HQ variant
+ responsive duplicates
+ 2 sticky preview nodes
+ recently-viewed preview
+ review attachment
= old extractor sees 9-ish logical candidates
```

New extractor must output:

```text
expectedCount = 4
slots.length = 4
foreign = 0 imported
order = [1,2,3,4]
```

This test is mandatory.

# 20. AUTOMATED TEST MATRIX

Add tests for at least:

### Exactness
1. 4 real + 5 foreign -> exactly 4.
2. seller avatar/review/recent/sticky never imported.
3. hero + thumbnail same photo -> one slot.
4. responsive srcset variants -> one slot.

### Count
5. counter `1 из 4` -> N=4.
6. alternate `1 / 4` -> N=4.
7. no counter -> thumbnail unique count fallback.
8. virtualized thumbnails -> traversal reaches N.

### HQ
9. first hero already HQ.
10. click thumbnail #2 -> waits for matching hero identity before capture.
11. stale hero for 100ms does not get assigned to next slot.
12. largest parsed srcset width selected.
13. HQ timeout -> exact thumbnail fallback for same slot.
14. one failed HQ fetch -> fallback same slot, still N photos.

### Identity
15. Stage13A V2 canonical tests.
16. host shard variants dedupe.
17. unfamiliar URL gets safe identity.

### Server
18. HQ + low fallback for one logical photo -> one ProductPhoto.
19. repeated same payload -> no duplicate photo rows.
20. four logical photos -> exactly four persisted rows.
21. order preserved if current data model supports ordering; otherwise document limitation.

### Regression
22. single-photo listing still works.
23. listing without gallery does not crash.
24. single-item/profile import regressions pass.
25. pairing/switching v0.2.63+ behavior remains intact.
26. reverse browser-assisted flow remains intact.
27. automatic Avito deactivation remains disabled.

Run:
```text
pytest chrome-extension/technoreboot-avito/tests/
python scripts/run_targeted_tests.py
```

plus any Core tests added for photo persistence.

# 21. REAL LOCAL BROWSER VALIDATION — REQUIRED

Synthetic tests alone are NOT sufficient.

After automated tests and build, leave LOCAL running:

```text
https://localhost:8443
```

Use a real Avito listing with a known visible gallery count.

Prefer a listing with exactly 4 photos to reproduce Owner's original case.

Do NOT claim real-browser PASS unless the extension was actually exercised against a live Avito page.

For real validation capture:

```text
LISTING_ID
VISIBLE_COUNT=N
EXTRACTED_LOGICAL_COUNT
HQ_COUNT
FALLBACK_COUNT
IMPORTED_PRODUCT_ID
PERSISTED_PHOTO_COUNT
```

Expected on 4-photo sample:

```text
VISIBLE_COUNT=4
EXTRACTED_LOGICAL_COUNT=4
PERSISTED_PHOTO_COUNT=4
foreign photos=0
```

If all four hero activations expose HQ:

```text
HQ_COUNT=4
```

If one HQ activation fails but exact fallback works:

```text
PERSISTED_PHOTO_COUNT must still be 4
foreign photos must still be 0
```

# 22. OWNER BROWSER ACCEPTANCE FLOW

Prepare simple browser-only instructions:

1. Update/load extension v0.2.64 from LOCAL build.
2. Pair it to `https://localhost:8443`.
3. Open an Avito listing that visibly has 4 photos.
4. Open extension and import the listing once.
5. Observe that the extension may briefly traverse the gallery thumbnails.
6. Open imported product in LOCAL TechnoReboot.
7. Verify:
   - exactly 4 photos;
   - all 4 belong to that listing;
   - order matches Avito;
   - no sticky/recent/review images;
   - visually each photo is good quality.
8. Repeat with a 1-photo listing.
9. If available, repeat with a listing containing >10 photos to test virtualization/traversal.

No CMD/PowerShell for Owner.

# 23. EXTENSION VERSION / BUILD

Bump extension patch version from:

```text
0.2.63
```

to:

```text
0.2.64
```

unless repository versioning requires another patch.

Update all current version references consistently.

Build canonical ZIP with existing script.

Verify:
- manifest syntax;
- service worker syntax;
- CSP;
- package contents;
- ZIP SHA256;
- admin-shell download copy matches build byte-for-byte.

Do NOT deploy to production.

# 24. PERFORMANCE LIMITS

Avoid making import painfully slow.

Target:
- no fixed multi-second delay per photo;
- condition-based wait;
- sequential traversal is acceptable because correctness is primary;
- cap retries/timeouts.

Report elapsed gallery traversal time for:
- 1 photo;
- 4 photos;
- larger sample if available.

# 25. NO URL “MAGIC” AS PRIMARY HQ STRATEGY

Do not construct guessed HQ CDN URLs by arbitrary string replacement as the primary method.

Allowed:
- use actual hero/currentSrc/srcset URLs exposed by Avito;
- use an observed, tested URL normalization only for identity/dedupe;
- use URL upgrading only as a fallback if it is proven on current CDN format and validated by successful image fetch/dimensions.

The source of truth for HQ should be what the active Avito gallery actually loads.

# 26. DOCUMENTATION

Create:

```text
reports/stage13b_avito_exact_n_hq_gallery_import_report.md
```

Update:

```text
docs/production_status.md
logs/<current-date>.md
```

Report:
- old failure;
- new exact-N algorithm;
- canonical ID V2;
- traversal/wait implementation;
- server dedupe fix;
- test counts;
- real-browser evidence;
- extension ZIP/hash.

# 27. GIT

Commit tracked code/tests/docs only.

Never commit:
- production DB/media;
- downloaded Avito image binaries from real listings;
- tokens;
- pairing codes;
- browser profile;
- private keys.

Push `main` after LOCAL tests pass.

# 28. FINAL REPORT CONTRACT

Return:

```text
# Stage 13B — Exact-N HQ Avito Gallery Import

## Extension
EXTENSION_VERSION:
GALLERY_ROOT_SELECTOR:
PHOTO_COUNT_SOURCE:
CANONICAL_ID_V2:
DOCUMENT_WIDE_PREVIEW_SCAN_REMOVED:
SLOT_MODEL_IMPLEMENTED:

## Exactness
FOUR_REAL_FIVE_FOREIGN_TEST:
EXPECTED_N_ENFORCED:
FOREIGN_IMAGES_IMPORTED:
ORDER_PRESERVED:
VIRTUALIZED_GALLERY_HANDLED:

## HQ Traversal
PRIMARY_METHOD:
HERO_IDENTITY_WAIT:
WAIT_TIMEOUT:
RETRY_POLICY:
SRCSET_MAX_SELECTION:
HQ_FALLBACK:
PAGE_STATE_RESTORED:

## Client Download
ONE_DOWNLOAD_PER_LOGICAL_SLOT:
HQ_FETCH_FALLBACK:
CONTENT_TYPE_VALIDATED:
SLOT_ORDER_PRESERVED:

## Server
CORE_DOUBLE_APPEND_FIXED:
ONE_LOGICAL_PHOTO_ONE_PRODUCTPHOTO:
SERVER_DEFENSIVE_DEDUPE:
REPEAT_IMPORT_NO_DUPLICATE:

## Automated Tests
EXTENSION_TESTS:
CORE_PHOTO_TESTS:
TARGETED_SUITE:
SYNTAX_CHECK:
BUILD_CHECK:

## Real Browser Evidence
LIVE_AVITO_TEST_PERFORMED:
TEST_LISTING_ID:
VISIBLE_REAL_PHOTO_COUNT:
EXTRACTED_LOGICAL_COUNT:
HQ_COUNT:
FALLBACK_COUNT:
PERSISTED_PHOTO_COUNT:
FOREIGN_PHOTO_COUNT:
TRAVERSAL_ELAPSED_MS:

## Build
EXTENSION_ZIP:
EXTENSION_ZIP_SHA256:
ADMIN_DOWNLOAD_HASH_MATCH:

## Safety
PRODUCTION_TOUCHED: false
PRODUCTION_DB_CHANGED: false
AVITO_BUSINESS_ACTIONS_PERFORMED: false
AUTO_AVITO_DEACTIVATION_DISABLED: true

FINAL_STATUS:
TECHNOREBOOT_STAGE13B_LOCAL_READY_FOR_OWNER_ACCEPTANCE
```

# 29. STOP

STOP after:
- LOCAL implementation;
- automated tests;
- extension build;
- real LOCAL/live-Avito validation if possible;
- LOCAL smoke.

Do NOT deploy to `144.31.15.88`.

Wait for Owner browser acceptance.
