# Stage 07B-R5-R3 — Full Avito Gallery Extraction (InitialData + Traversal Fallback)

## 1. Context & Objective

Stage 07B-R5-R2 introduced strict gallery root scoping and foreign asset filtering to eliminate tracker and avatar contamination. However, real-world testing by the Owner on listing `8355529554` ("Ноутбук Acer aspire 5690 под восстановление") revealed that only **one photo** was detected and imported.

The root cause was Avito's gallery virtualization: at initial page load, only the active slide image element exists inside the gallery DOM root. All other slides are unmounted or lack `<img>` elements until scrolled or clicked.

Stage 07B-R5-R3 implements a robust 3-layer extraction strategy that guarantees complete photo discovery while maintaining strict deduplication, quality selection, and foreign asset rejection.

---

## 2. Extraction Architecture (3 Layers)

### Layer 1: Embedded `__initialData__` State (Primary)
- Safely accesses the page initial data via main-world event bridge (`TechnorebootInitialData`) and `<script>` structured tags.
- Locates `@avito/bx-item-view` associated with the current listing ID (`buyerItem.galleryInfo.media`).
- Excludes video elements (`isVideo === true` or `type === 'video'`).
- Inspects the authentic `urls` map (keyed by dimensions like `640x480`, `1280x960`).
- Parses dimension keys (`WIDTHxHEIGHT`), calculates `area = width * height`, and orders candidates descending without URL fabrication.
- Groups candidates into ordered photo slots (`0..N-1`).

### Layer 2: Controlled Gallery Traversal (Fallback)
- Automatically invoked if Layer 1 is missing, malformed, or discovers fewer photos than the visible gallery count $N$.
- Determines visible photo count from counter elements (`X из N`), thumbnail items, or accessible attributes.
- Steps slide-by-slide through thumbnails or NEXT button clicks.
- Implements bounded polling (up to 350ms) to detect genuine active slide image changes before capturing candidates.
- Features wrap detection (terminates if returning to first slide) and restores the first slide upon completion.

### Layer 3: Scoped DOM Query (Last Fallback)
- Scoped strictly within `findGalleryRootElement()`.
- Captures `<source srcset>` and active `<img>` elements.
- Rejects foreign recommendation cards, seller avatars, and tracking pixels.

---

## 3. Photo-Slot Deduplication

To permanently eliminate the "2 copies each" issue (where low and high resolution variants of the same slide were previously captured as separate photos):
- Candidates are grouped by canonical image identity and assigned to their respective **photo slot** (`0..N-1`).
- Only **one** photo object per gallery slot is output in the final `listing.photos` array (`selected_candidate = candidates[0]`).
- Fallback candidates for the SAME slot are retained internally for Service Worker download resilience.
- Final photo count strictly equals visible gallery photo count $N$.

---

## 4. Diagnostics & Reporting (Section 10 Contract)

`lastExtractionDiagnostics` captures comprehensive audit metrics:
```json
{
  "listing_id": "8355529554",
  "visible_gallery_count": 6,
  "expected_photo_count": 6,
  "initial_data_found": true,
  "item_view_key_found": true,
  "media_array_count": 6,
  "non_video_media_count": 6,
  "initial_dom_gallery_image_count": 1,
  "gallery_root_strategy": "gallery_container",
  "traversal_used": false,
  "traversal_unique_slides": 0,
  "final_photo_count": 6,
  "extracted_photo_count": 6,
  "foreign_images_rejected": 0,
  "duplicates_rejected": 0,
  "photos": [
    {
      "index": 0,
      "source": "initialData",
      "candidate_count": 2,
      "selected_resolution": "1280x960",
      "download_ok": true,
      "bytes": 52180,
      "sha256": "..."
    }
  ]
}
```

---

## 5. Versioning & Package Distribution

- Extension Version: `0.2.46`
- Distribution Archives:
  - `dist/technoreboot-avito-extension-0.2.46.zip`
  - `admin-shell/app/technoreboot-avito-extension-0.2.46.zip`
- Admin Shell UI and download endpoints updated to serve `v0.2.46`.
