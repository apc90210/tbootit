# Stage 07B-R5-R2: Avito Strict High-Quality Photo Extraction Architecture & Documentation

## Overview
This document specifies the strict photo extraction and high-quality download pipeline implemented in Technoreboot Avito Extension v0.2.45 (`chrome-extension/technoreboot-avito`).

The implementation addresses the core deficiencies identified in earlier versions:
1. Extraction leakage of non-listing assets (recommendations, similar items, seller listings, avatars, delivery icons, logos, trackers, and map cursors).
2. Fabricated HQ image URLs caused by blind string replacement (`/640x480/` -> `/1280x960/`) leading to 404/broken links.
3. Photo ordering loss across multi-resolution sources.
4. Missing service worker background download pipeline with content-type verification and cryptographic SHA-256 integrity.

---

## Architecture Components

### 1. Manifest Permissions & Scope (`manifest.json`)
- **Version:** `0.2.45`
- **Host Permissions:** Explicitly includes `"https://*.img.avito.st/*"` allowing the Service Worker to fetch binary image streams directly from Avito's CDN without CORS or page-context CSP restrictions.

### 2. URL Sanitization & Scope Enforcement (`validateListingImageUrl`)
- Enforces strict hostname check: MUST match `^[a-zA-Z0-9_\-\.]*img\.avito\.st$`.
- Rejects foreign asset paths:
  - Excludes tracking pixels (e.g. `adriver`, `counter`, `pixel`, `tracker`).
  - Excludes UI assets (e.g. `avatar`, `logo`, `badge`, `icon`, `delivery`, `cursor`, `banner`).
  - Excludes non-Avito CDNs (e.g. Yandex maps, static avito UI bundles).

### 3. Gallery Root DOM Scoping (`findGalleryRootElement` & `extractPhotosFromDom`)
- Searches specifically for genuine gallery containers:
  - `[data-marker="item-view/gallery"]`
  - `[data-marker="image-frame/image-wrapper"]`
  - `ul[data-marker="gallery/list"]`
- Strictly bounds DOM extraction to elements inside the resolved gallery root.
- Rejects recommendation blocks, carousels, similar items, and seller listings via `isInsideExcluded()`.
- Parses `srcset` attributes with numeric descriptor parsing (`w` and `x` units) into ranked candidate lists.

### 4. Structured State Parsing (`extractPhotosFromEmbeddedState`)
- Replaces unscoped full-document regex scans with scoped object traversal.
- Parses only listing-associated state nodes (`item`, gallery widgets).
- Explicitly ignores keys matching recommendation, similar, and seller keys (`EXCLUDED_DATA_KEYS`).

### 5. Genuine Quality Selection Without Fabrication (Anti-Fabrication Rule)
- Disables blind upscale regex replacement (`replace('/640x480/', '/1280x960/')`).
- Groups candidate URLs by canonical image identity (`getCanonicalAvitoImageIdentity`).
- Ranks genuine candidates by quality score based on authentic `srcset` widths and verified URL structure.

### 6. Service Worker Download Pipeline (`service_worker.js`)
- Handler for `download_photo_candidate`:
  1. Validates CDN domain (`*.img.avito.st`).
  2. Executes `fetch(url, { credentials: 'omit' })`.
  3. Enforces response status `200 OK` and `Content-Type: image/*`.
  4. Enforces maximum size limit (15 MB).
  5. Computes SHA-256 digest via `crypto.subtle.digest("SHA-256", arrayBuffer)`.
  6. Encodes binary to base64 using chunking (`chunkSize = 8192`) to prevent stack overflow on large files.
  7. Implements graceful candidate fallback if a higher-resolution candidate fails or returns 404.

### 7. Deduplication & Ordering
- Retains exact Avito gallery order (`0..N-1`).
- Eliminates duplicate entries across thumbnail list, main image frame, and structured data.
- Accurately counts genuine listing photos (e.g. exactly 6 photos for target listing `8355529554`).

---

## Verification & Diagnostics Contract
Diagnostics are recorded on extraction and accessible via `window.__technoreboot_photo_diagnostics` or message action `get_photo_diagnostics`:
```json
{
  "listing_id": "8355529554",
  "expected_photo_count": 6,
  "extracted_photo_count": 6,
  "gallery_root_strategy": "gallery_container",
  "photos": [
    {
      "index": 0,
      "candidate_count": 2,
      "selected_source": "gallery_srcset",
      "selected_quality_hint": "thumb_1280w",
      "download_ok": true,
      "bytes": 62450,
      "content_type": "image/jpeg"
    }
  ],
  "foreign_images_rejected": 5,
  "duplicates_rejected": 8
}
```
