# Stage 06A-R8 Chrome Extension Avito Photo Import Architecture & Fixes

## Overview

This document specifies the technical design, payload contracts, remote photo downloading mechanism, security boundaries, and idempotency guarantees for photo import from Avito listings into Technoreboot via Chrome Extension.

## Baseline Root Cause

Before Stage 06A-R8-R6, single-item listing import succeeded for core text fields (title, price, description), but photos failed to render in the UI (Product 58 photos remained 0 / unrendered).

Detailed analysis uncovered three contributing root causes across the pipeline:

1. **Extension DOM Extraction (`content.js`)**:
   - `parseJsonLd()` ignored `jsonLd.image` when formatted as a single object `{"url": "https://..."}` or when contained inside nested `@graph` arrays.
   - Gallery extraction only read `src`/`data-src` attributes, missing high-res images provided in `srcset`/`data-srcset` attributes or embedded `window.__initialData__` state.
   - Photos were sent as unvalidated primitive string arrays rather than position-aware objects.

2. **Bridge Schema & Contract Validation (`avito-module`)**:
   - `isinstance(url, str)` filter dropped dict objects when object arrays were passed.
   - Diagnostic counters (`photos_received`, `photos_forwarded`, `photos_imported`) were not captured in `extension_last_ingest.json`.

3. **Core API Remote Photo Downloading (`core/app/routers/integrations.py`)**:
   - When receiving photo objects without `content_base64`, Core API created 146-byte dummy 1x1 JPEG placeholder files on disk instead of downloading real image bytes from remote HTTPS CDN URLs.
   - On subsequent imports, SHA256 content hashes matched the dummy 146-byte files and skipped photo downloads.

---

## Technical Solution

### 1. Robust Photo Extraction (`content.js` v0.1.4)
- **JSON-LD**: Parses strings, string arrays, `{"url": "..."}`, `[{"url": "..."}]`, and `@graph` nodes.
- **Embedded State**: Parses `window.__initialData__` and `window.__state__` script tags for Avito CDN URLs (`*.img.avito.st`).
- **DOM & Srcset**: Evaluates `srcset` and `data-srcset` descriptors to select the maximum resolution variant (e.g. 1280x960).
- **Normalization**: Strips duplicate URLs while preserving original gallery order (`position: 0` = main photo).

### 2. Core-Owned Remote Photo Persistence
- **SSRF Safety**: Validates all incoming image URLs with `is_safe_remote_url(url)`. Blocks `localhost`, `127.0.0.1`, `::1`, private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local (`169.254.0.0/16`), `file://`, and `ftp://`.
- **Remote Fetcher**: Uses `httpx.Client(trust_env=False, timeout=10.0, follow_redirects=True)` with a desktop User-Agent to fetch public HTTPS images directly from Avito CDN without requiring browser cookies or session tokens.
- **Content-Type & Size Validation**: Enforces `Content-Type: image/*` and a maximum file size limit of 10 MB per photo.
- **Dummy Placeholder Upgrade**: Automatically detects and replaces existing 146-byte dummy placeholder files with actual downloaded photo bytes.

### 3. Partial Failure & Popup UI Semantics
- If Product text fields are updated but photo import yields 0 photos when photos were received:
  - Status returned: `"partial"`.
  - Extension popup warning: `"Основные данные обновлены, но фотографии импортировать не удалось."`.
- Popup shows success ONLY when photos pass:
  `"✓ Объявление импортировано.\nProduct ID: 58\nФотографий: N"`.

### 4. Owner Product Photo UI & Admin Shell Media Proxy (Stage 06A-R8-R7)
- **Inventory Product Detail UI**: Displays a dedicated **«🖼️ Фотографии»** block on `http://localhost:8011/inventory/products/{id}`.
  - Photos render as gallery thumbnails sorted by `sort_order` with the main photo marked by a badge.
  - Clickable thumbnails open the full-resolution image in a new tab.
  - Products with 0 photos cleanly show notice **«Фотографий нет»**.
- **Same-Origin Media Reverse Proxy**: Admin Shell (`admin-shell/app/main.py`) proxies `/media/{path:path}` to Core API (`http://localhost:8000/media/{path}`), ensuring all media URLs resolve on origin `localhost:8011`.

### 5. Multi-Photo & Best Quality Extraction (Stage 06A-R8-R8 — Extension v0.1.5)
- **All Photos & Quality Upgrades**: Replaces Avito image URL dimension tokens (`140x105`, `208x156`, `480x360`, `640x480`) with high-resolution `1280x960` CDN URLs.
- **Non-Listing Asset Filtering**: Filters out non-listing images (`/avatar/`, `/icons/`, `/logos/`, `/shop/`, `/recom/`, `/banner/`, `.svg`, `data:`).
- **Image Hash Deduplication**: Groups image variants by unique Avito hash to avoid duplicates while preserving exact gallery position order (`position: 0, 1, 2, ...`).
- **Packaging & Delivery**: Extension v0.1.5 packaged into `technoreboot-avito-extension-0.1.5.zip` served at `http://localhost:8011/avito/extension/download`.


