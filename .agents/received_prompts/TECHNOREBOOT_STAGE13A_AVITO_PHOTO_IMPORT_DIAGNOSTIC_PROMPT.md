# TECHNOREBOOT — Stage 13A DIAGNOSTIC ONLY
## Avito photo import: exact current implementation, false candidates, and HQ gallery behavior

Project: ТехноРебут
Workspace: C:\tbootit
Environment: LOCAL / diagnostic only
Canonical production VDS: 144.31.15.88 — DO NOT DEPLOY
Current extension baseline: v0.2.63

# 0. PURPOSE

Do NOT implement the new photo importer yet.

This stage exists only to document exactly how Avito photo discovery/import works now, why a listing with 4 real photos can produce 9 detected candidates, and what browser/DOM data is available for a robust next-stage implementation.

Owner’s observed behavior:
- at least one main photo can already be imported in high quality;
- extension can see additional photo candidates;
- example: listing has exactly 4 real photos, but extension reports 9 candidates;
- target later:
  1) first reliably get exactly the listing’s own N photos, even if initially lower quality;
  2) then get exactly those same N photos in high quality;
  3) a possible strategy is to iterate gallery thumbnails like a human, activate each image, wait until the large image loads, capture its highest-quality URL, then move to the next thumbnail.

This prompt is DIAGNOSTIC ONLY.

# 1. PRESERVE PROMPT

Copy unchanged from:

C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE13A_AVITO_PHOTO_IMPORT_DIAGNOSTIC_PROMPT.md

to:

C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE13A_AVITO_PHOTO_IMPORT_DIAGNOSTIC_PROMPT.md

# 2. PREFLIGHT

Record:
- git status
- branch
- HEAD
- docker compose ps
- extension version

Do not modify production.
Do not change production DB/media.
Do not deploy.
Do not change Avito listing state.

# 3. MAP THE CURRENT PHOTO PIPELINE

Inspect every code path involved in Avito listing photo extraction/import.

At minimum identify:
- content script / injected script;
- popup code if involved;
- service worker;
- any page-world bridge;
- Avito parser helpers;
- server upload/import endpoint;
- image downloading/storage code;
- current photo DTO/JSON contract;
- current main-photo fallback.

Return exact file names, function names, and call chain.

Example format:

page DOM
 -> function A()
 -> candidate collection B()
 -> URL normalization C()
 -> message to service worker D()
 -> server request E()
 -> server media storage F()

# 4. CURRENT CANDIDATE DISCOVERY — EXACT DETAILS

For every selector / extraction strategy currently used, report:

- selector or DOM query;
- whether it scans whole document or gallery subtree;
- attributes read:
  - src
  - srcset
  - currentSrc
  - picture/source
  - data-src
  - style/background-image
  - href
  - JSON/script state
- whether hidden/lazy/preloaded elements are included;
- whether duplicate responsive variants are included;
- whether recommendation/sidebar/carousel images can be included;
- whether seller avatar/logo can be included;
- whether thumbnails and active large image are both included;
- whether mobile/desktop duplicate markup can be included.

Do not summarize vaguely. Quote the exact relevant code snippets in the report, within reasonable length.

# 5. REPRODUCE THE “4 REAL PHOTOS -> 9 CANDIDATES” CASE

Use a live/safe Avito listing that reproduces the mismatch if available.

Do not modify the listing.

For one concrete example where the visible listing gallery has N real photos but the current code finds M>N candidates, build a candidate table.

Required columns:

| # | source selector | DOM role | URL/currentSrc | dimensions if known | visible? | inside listing gallery root? | canonical media identity | duplicate of | should import? | reason |

The report must explain all extra candidates.

If the exact owner listing is not available, reproduce the same class of problem on another listing and clearly say so.

# 6. FIND THE TRUE GALLERY BOUNDARY

Determine the narrowest stable DOM root that represents ONLY the current listing’s own photo gallery.

Investigate:
- data-marker attributes;
- ARIA labels/roles;
- gallery/carousel wrappers;
- thumbnail strip;
- active hero image;
- next/previous controls;
- photo counter like `1 / 4`;
- modal/lightbox gallery if Avito opens one.

Report:
- candidate root selectors;
- which selector is most stable;
- which selectors appear hashed/unstable CSS classes and should NOT be trusted;
- whether data-marker / semantic attributes are available.

# 7. DETERMINE TRUE PHOTO COUNT

Find every trustworthy source for the listing’s real gallery photo count.

Investigate:
- visible photo counter;
- thumbnail count;
- gallery slide count;
- embedded page JSON/state;
- preload data;
- script[type=...] state;
- network-loaded gallery metadata if accessible from page context.

Rank each source:
1. strongest/canonical
2. fallback
3. weak heuristic

For the reproduced listing compare:
- visible real count;
- thumbnail count;
- metadata count;
- current candidate count.

# 8. MEDIA IDENTITY / DEDUPLICATION

Analyze Avito CDN URLs.

Determine whether multiple URLs for the same underlying photo differ only by:
- host shard (`00.img.avito.st`, `01...`);
- resize suffix;
- width/height;
- crop mode;
- query string;
- format/webp/avif;
- thumbnail vs hero size.

Design, but DO NOT yet implement, a canonical image identity function.

Report examples:

URL A -> canonical id X
URL B -> canonical id X
URL C -> canonical id Y

Goal:
different responsive variants of one photo must dedupe to one logical photo without merging two distinct listing photos.

# 9. HOW THE CURRENT “ONE HQ PHOTO” WORKS

This is critical.

Identify exactly why/how the current main photo can be imported in high quality.

Report:
- source DOM element;
- attribute used;
- exact URL form before/after normalization;
- original image dimensions if measurable;
- downloaded file dimensions and bytes;
- whether URL is directly present in DOM or produced after user/gallery interaction;
- whether `currentSrc` differs from `src`;
- whether `srcset` exposes a larger candidate.

If there is existing URL “upgrade” logic, document it exactly.

# 10. THUMBNAIL -> ACTIVE HQ EXPERIMENT

Without committing product changes, experimentally test the Owner’s proposed strategy.

For a listing with multiple photos:

1. identify each true gallery thumbnail;
2. click thumbnail #1;
3. wait for gallery state to settle;
4. inspect active/hero image:
   - src
   - currentSrc
   - srcset
   - picture/source
   - naturalWidth/naturalHeight
5. repeat for #2 ... #N.

Record for each photo:

| photo index | thumbnail identity/url | active image URL | currentSrc | largest srcset URL | natural WxH | unique canonical id | load delay |

Test:
- whether clicking every thumbnail causes a higher-resolution URL to appear;
- whether all N photos can be visited deterministically;
- whether the active hero image changes synchronously or needs MutationObserver/load wait;
- whether clicking thumbnails has side effects;
- whether keyboard/next-arrow navigation is more reliable than direct thumbnail clicks;
- whether opening the full-screen gallery/lightbox exposes better URLs.

Do not publish, edit, favorite, message seller, or perform any business action.

# 11. LIGHTBOX / FULLSCREEN EXPERIMENT

If Avito supports clicking the large photo to open a full gallery/lightbox:

Investigate whether this produces:
- a cleaner exact set of N slides;
- larger image URLs;
- preload of adjacent photos;
- stable semantic selectors;
- reliable next/previous navigation.

Compare:
A. thumbnail strip traversal
B. fullscreen/lightbox traversal
C. direct DOM/srcset extraction without clicks

Rank them for:
- exactness of N;
- HQ quality;
- stability;
- implementation complexity;
- risk of UI timing failures.

# 12. EMBEDDED STATE / NETWORK DATA

Inspect page source/runtime for listing data that may already contain the complete photo array.

Search safely for:
- listing/item ID;
- image/photo arrays;
- `img.avito.st`;
- embedded JSON;
- `data-mfe-state`;
- hydration state;
- JSON-LD;
- preload links.

If a clean N-photo array exists, document:
- location;
- path/key;
- sample sanitized structure;
- URL quality;
- whether it is available without extra network calls.

Do NOT build a server-side scraper in this stage.

# 13. DOWNLOAD QUALITY MEASUREMENT

For a few variants of the same photo, measure:
- HTTP status;
- Content-Type;
- bytes;
- decoded pixel dimensions;
- obvious thumbnail vs HQ.

Create a table:

| logical photo | URL source | bytes | WxH | quality tier |

Do not rely on URL text alone if pixel dimensions can be measured.

# 14. FAILURE / TIMING ANALYSIS

Document:
- lazy loading;
- virtualized thumbnails;
- images not yet in DOM;
- duplicate desktop/mobile nodes;
- carousel preloading;
- transitions/animations;
- stale active image after click;
- MutationObserver options;
- timeout/retry requirements.

Estimate safe waits from observed behavior rather than arbitrary long sleeps.

# 15. RECOMMENDED NEXT-STAGE ALGORITHM — NO IMPLEMENTATION

Based on evidence, propose a ranked algorithm.

The preferred architecture should likely separate:

A. exact logical gallery discovery
B. canonical dedupe/order
C. HQ resolution acquisition
D. download/upload

Provide pseudocode only.

Example conceptual target:

1. locate exact gallery root
2. derive authoritative photoCount=N
3. enumerate N logical gallery items in visual order
4. assign canonical identity per photo
5. for each logical photo:
   - obtain largest direct srcset/currentSrc if already available
   - otherwise activate that thumbnail/slide
   - wait for active hero image to represent the same canonical photo
   - select highest-resolution URL
6. assert exactly N unique logical photos
7. only then send/import them
8. if HQ resolution fails for one item, retain exact-photo fallback URL rather than importing unrelated images

Do not assume this is correct unless diagnostics support it.

# 16. IMPORTANT ACCEPTANCE PRINCIPLE FOR NEXT STAGE

The next implementation must prioritize:

FIRST:
```text
exactly N listing photos, no foreign photos
```

THEN:
```text
maximize quality for those exact N photos
```

It is better to import exactly 4 correct medium-quality photos than:
- 4 correct + 5 unrelated photos;
- or 1 HQ + incorrect extras.

# 17. DIAGNOSTIC ARTIFACTS

Create:

reports/stage13a_avito_photo_import_diagnostic_report.md

Optionally create ignored diagnostic JSON/text artifacts with:
- candidate URLs;
- canonical IDs;
- dimensions;
- selectors;
- timestamps.

Do not commit copyrighted image binaries or user media.

Screenshots may be referenced in report if useful but do not commit large diagnostic dumps unless project convention permits it.

# 18. TESTS

Do not change product implementation.

You may create diagnostic-only scripts/tests that do not alter runtime behavior.

Run existing extension regression tests afterward and prove no runtime code was changed.

# 19. GIT

Commit only:
- prompt receipt;
- diagnostic report;
- diagnostic scripts if useful;
- log/docs update.

Do NOT commit functional photo-import changes in Stage13A.

Push main.

# 20. FINAL REPORT CONTRACT

Return:

# Stage 13A — Avito Photo Import Diagnostic

## Current Pipeline
EXTENSION_VERSION:
PHOTO_EXTRACTION_FILES:
PHOTO_EXTRACTION_FUNCTIONS:
FULL_CALL_CHAIN:
CURRENT_MAIN_HQ_METHOD:

## Reproduction
TEST_LISTING_URL:
TEST_LISTING_ID:
VISIBLE_REAL_PHOTO_COUNT:
CURRENT_CANDIDATE_COUNT:
FALSE_CANDIDATE_COUNT:
FALSE_CANDIDATES_EXPLAINED:

## Gallery Boundary
BEST_GALLERY_ROOT:
STABLE_SEMANTIC_SELECTORS:
UNSTABLE_SELECTORS_TO_AVOID:
TRUE_PHOTO_COUNT_SOURCE:

## Candidate Analysis
THUMBNAILS_INCLUDED:
HERO_INCLUDED:
RESPONSIVE_DUPLICATES_INCLUDED:
SIDEBAR_OR_RECOMMENDATION_IMAGES_INCLUDED:
SELLER_OR_OTHER_IMAGES_INCLUDED:

## Canonical Identity
CANONICAL_IMAGE_ID_STRATEGY:
DEDUPE_PROVEN_ON_SAMPLE:

## HQ
MAIN_HQ_SOURCE:
SRCSET_HAS_HQ:
CURRENTSRC_HAS_HQ:
CLICK_THUMBNAIL_PRODUCES_HQ:
LIGHTBOX_PRODUCES_HQ:
EMBEDDED_STATE_HAS_FULL_PHOTO_ARRAY:

## Traversal Experiment
THUMBNAIL_TRAVERSAL_RESULT:
NEXT_ARROW_TRAVERSAL_RESULT:
LIGHTBOX_TRAVERSAL_RESULT:
BEST_TRAVERSAL_METHOD:
REQUIRED_WAIT_CONDITION:

## Quality Measurements
PHOTO_VARIANTS_MEASURED:
BEST_OBSERVED_RESOLUTION:
BEST_OBSERVED_SOURCE:

## Recommended Algorithm
PRIMARY_STRATEGY:
FALLBACK_STRATEGY:
EXACT_N_GUARANTEE:
HQ_UPGRADE_STRATEGY:
MAJOR_RISKS:

## Safety
PRODUCT_CODE_CHANGED: false
PRODUCTION_TOUCHED: false
AVITO_BUSINESS_ACTIONS_PERFORMED: false

FINAL_STATUS:
TECHNOREBOOT_STAGE13A_DIAGNOSTIC_COMPLETE
