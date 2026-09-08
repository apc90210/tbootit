# Stage 07B-R5-R3-R1 — Fix Avito Live Gallery Traversal & InitialData Extraction

## Summary

Extension v0.2.46 (Stage 07B-R5-R3) correctly implemented the 3-layer extraction architecture
(InitialData → Traversal → DOM) but the gallery traversal's thumbnail query was scoped too
narrowly — restricted to the gallery root element, which in Avito's lazy/virtualized UI only
contains the single active slide. As a result, `findGalleryRootElement()` found a narrow wrapper,
the thumbnail query returned 0 elements, and `walkAndCollectAllGalleryPhotos` exited without
advancing through gallery slides.

## Root Cause

`walkAndCollectAllGalleryPhotos()` in v0.2.46 queried for thumbnails strictly within
`galleryRoot` as returned by `findGalleryRootElement()`. On Avito's current DOM structure,
the gallery root resolved to the narrow `[data-marker="item-view/gallery"]` or
`[data-marker="image-frame"]` container, which only holds the main image frame — not the
thumbnail strip. The thumbnail strip exists elsewhere in the DOM hierarchy, outside the
strict gallery root.

## Changes in v0.2.47

### `content.js`
- **Broadened thumbnail discovery**: `walkAndCollectAllGalleryPhotos()` now queries the
  entire `document` for thumbnail selectors, using extensive CSS selector coverage:
  - `ul[data-marker="gallery/list"] li`
  - `[data-marker="gallery/preview-item"]`
  - `[data-marker*="preview"]`
  - `[data-marker="item-view/gallery"] ul li`
  - `div[class*="gallery-list"] > *`
  - And more, with deduplication by ancestor/descendant filtering.
- **Exclusion filters**: Thumbnails inside `[data-marker*="seller"]`, `[data-marker*="recommend"]`,
  `[data-marker*="similar"]` are explicitly excluded to prevent foreign image leakage.
- **Dual candidate collection**: Each traversal step collects candidates from both the main
  frame (`activeFrame`) and the clicked thumbnail, merging HD from main + preview from thumb.
- **Enhanced InitialData parsing**: Added support for URI-encoded `__initialData__` via
  `decodeURIComponent()`, double-JSON-parse, and `window.__initialData__` direct access as
  primary strategy before script tag scanning.
- **Robust JSON extraction**: Limited lookahead scan to 300 characters after `=` sign to
  prevent runaway regex matching on very long scripts.

### `popup.js`
- Updated initial photo count display to use `Math.max(detectedPhotosCount, visibleCount)`
  from diagnostics, showing the expected gallery count even before HD scanning completes.

### Version bump
- All files bumped from `0.2.46` to `0.2.47`:
  - `manifest.json`, `content.js`, `popup.js`
  - `admin-shell/app/main.py`
  - `admin-shell/app/templates/avito_extension.html`
  - All relevant test files

## Test Results

| Suite | Result |
|-------|--------|
| Extension tests | 126 passed, 0 failed |
| Admin-shell tests | 69 passed, 1 skipped, 0 failed |
| Core tests | 209 passed, 0 failed |
| Avito-module tests | 95 passed, 0 failed |
| Extension ZIP build | Valid, 11 files verified |
