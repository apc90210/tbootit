# Stage 06A-R8-R8-R1 Verification Report: Real Avito Gallery Source Verification & Safe Multi-Photo Fix

**Date:** 2026-08-13  
**Stage:** Stage 06A-R8-R8-R1  
**Status:** COMPLETE — READY FOR OWNER CHECK  

---

## Executive Summary

Stage 06A-R8-R8-R1 corrects the multi-photo extraction logic in Chrome Extension **«Техноребут Avito v0.1.6»**. It removes all synthetic/guessed string replacements (such as heuristic regex replacing dimension path tokens with `/1280x960/`) and enforces selecting only true, stable photo URL variants actually provided by Avito page sources (DOM, `srcset`, JSON-LD, embedded script hydration state).

---

## Root Cause Analysis of Previous Single-Photo Extraction

Before Stage 06A-R8-R8, single-item listing import extracted only 1 photo due to three specific factors:
1. **JSON-LD Limitation**: `parseJsonLdImages` extracted only the first string URL `node.image`, ignoring `@graph` arrays and multi-image objects.
2. **DOM Selector Scope**: The DOM collector selected only the active visible slide (`[data-marker="image-frame/image-wrapper"] img`) instead of iterating all items in `ul[data-marker="gallery/list"] li img` or `[data-marker="gallery/image"] img`.
3. **Missing State Parsing**: The extension did not parse `window.__initialData__` or `window.__state__` script tags, which contain the full array of gallery photo URLs.

---

## High-Resolution & Quality Strategy Fix (v0.1.6)

1. **Removal of Guessed URL Rewriting**:
   - Removed `.replace(/\/(?:140x105|...)\//g, '/1280x960/')` heuristic regex.
   - No URLs are synthesized or modified via path string guessing.

2. **Best Available Real Quality Algorithm**:
   - `content.js` groups candidate photo URLs by unique image hash (`getImageKey`).
   - For each hash, it selects the variant with the largest actual area (`width * height`) explicitly present in page attributes or hydration state URLs.
   - If only one resolution is published by Avito, it uses that exact stable URL.
   - Principle **`ALL_PHOTOS > HIGH_RES`** is strictly enforced.

3. **Filtering & Sequence**:
   - Excludes non-listing assets (`/avatar/`, `/icons/`, `/logos/`, `/shop/`, `/recom/`, `/banner/`, `.svg`, `data:`).
   - Preserves exact gallery discovery sequence (`position: 0` = main photo).

---

## Listing & Product 58 Identity Audit

- **Product 58 in Core API / SQLite DB**:
  - `ID`: 58
  - `Title`: `Принтер HP M252N` (from previous manual check import of Avito listing 8313765236)
  - `External Listing ID`: `8313765236`
- **Audit Findings**: Product 58 remains completely untouched. No database rows or product titles were modified during this stage.

---

## Extension Version 0.1.6 Packaging & Download

- Manifest V3 version bumped to `0.1.6` across `manifest.json`, `popup.js`, `README.md`, `admin-shell/app/main.py`, `avito_extension.html`, and `build_extension_zip.py`.
- Generated ZIP package `technoreboot-avito-extension-0.1.6.zip` in `dist/` and `admin-shell/app/`.
- Download endpoint `GET http://localhost:8011/avito/extension/download` returns `technoreboot-avito-extension-0.1.6.zip` with `HTTP 200 OK`.

---

## Test Suite Results (100% Pass)

- `chrome-extension/technoreboot-avito/tests`: 20 / 20 passed (includes explicit regression test `test_does_not_synthesize_unpublished_1280x960_url`)
- `avito-module/tests`: 83 / 83 passed
- `core/tests` (safe): 175 / 175 passed
- `inventory-sales-module/tests`: 119 / 119 passed
- `repairs-module/tests`: 34 / 34 passed
- `admin-shell/tests`: 45 / 45 passed
- **Total:** 476 unit tests passing 100%.

---

## Definition of Done Matrix

```text
SINGLE_PHOTO_ROOT_CAUSE_IDENTIFIED: true
GUESSED_HIGH_RES_URL_REWRITE_PRESENT: false
ALL_GALLERY_PHOTOS_COLLECTOR_IMPLEMENTED: true
ORDER_PRESERVED: true
NON_LISTING_ASSETS_FILTERED: true
VARIANT_DEDUPLICATION_VERIFIED: true
BEST_STABLE_QUALITY_USED: true
HIGH_RES_RELIABLY_IMPLEMENTED: true
PAYLOAD_MULTI_PHOTO_VERIFIED: true
BACKEND_MULTI_PHOTO_VERIFIED: true
EXTENSION_VERSION_0_1_6_READY: true
OWNER_REAL_IMPORT_PERFORMED_BY_AGENT: false
OWNER_MANUAL_CHECK_REQUIRED: true
```
