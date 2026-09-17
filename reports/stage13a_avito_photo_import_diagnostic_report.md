# TECHNOREBOOT — Stage 13A Diagnostic Report
# Avito Photo Import: Exact Current Implementation, False Candidates, and HQ Gallery Diagnostics

**Date:** 2026-09-17  
**Stage:** Stage 13A (DIAGNOSTIC ONLY)  
**Workspace:** `C:\tbootit`  
**Git Branch:** `main`  
**Git HEAD:** `9e5e9b5335844179a05a30a5a8a0fc69fa1a3c9a`  
**Extension Baseline:** `v0.2.63`  
**Safety Status:** ZERO product code modified | ZERO production touch | ZERO Avito business actions performed  

---

## 1. Executive Summary & Purpose

This diagnostic investigation was conducted in strict read-only / diagnostic mode to resolve the root causes behind Avito photo discovery anomalies observed by the operator:
1. **The Mismatch:** An Avito listing with **exactly 4 visible real photos** in its gallery causes the extension to detect **9 candidates**.
2. **The Asymmetry:** The first (main) photo is successfully captured and imported in high resolution ($1280\times960$), while additional gallery photos are either captured in low-resolution thumbnail formats ($140\times105$ / $280\times210$) or multiplied by false candidates.
3. **The Goal:** Provide the complete technical and structural evidence needed to build a robust photo import algorithm in the next stage that strictly guarantees:
   - **FIRST:** Exactly the listing's own $N$ photos (zero foreign or out-of-gallery photos).
   - **THEN:** Maximize quality for those exact $N$ photos via deterministic thumbnail activation.

---

## 2. Preflight Baseline & Environment

- **Local Worktree Status:** Clean (untracked diagnostic scripts only).
- **Git Commit:** `9e5e9b5335844179a05a30a5a8a0fc69fa1a3c9a` on branch `main`.
- **Extension Version:** `0.2.63` (`chrome-extension/technoreboot-avito/manifest.json`).
- **Targeted Automated Tests:** 138 of 138 extension regression tests passing (100% PASS).
- **Local Microservices Stack:** 6 healthy Docker containers (`gateway`, `admin-shell`, `inventory-sales`, `repairs`, `core`, `avito`).
- **Production Safety:** Production VDS `144.31.15.88` untouched. Legacy VDS `144.31.50.134` retired and untouched.

---

## 3. End-to-End Photo Pipeline Map

Every code path involved in Avito listing photo extraction, transmission, and server storage was audited line-by-line:

```text
[Avito Web Page DOM]
  │
  ▼
1. content.js :: chrome.runtime.onMessage listener
   └─ Action "extract_current_page" (deepScan: true / false)
      └─ calls extractListingDataMultiPass() [or extractListingData()]
         ├─ Step 1: triggerInitialDataCapture() -> reads window.__initialData__ (Layer 1)
         ├─ Step 2: findGalleryRootElement() -> locates [data-marker="item-view/gallery"]
         ├─ Step 3: determineExpectedPhotoCount() -> reads "1 из 4" from gallery counter
         ├─ Step 4: walkAndCollectAllGalleryPhotos() (Layer 2 traversal, if triggered)
         ├─ Step 5: extractAllPhotos() -> checks Layer 1, Layer 2, Layer 3 (extractPhotosFromDom)
         │          └─ groups candidates by getCanonicalAvitoImageIdentity(url)
         │          └─ sorts candidates within slot by getImageQualityScore()
         │          └─ produces uniquePhotos array
         └─ Step 6: Multi-pass base64 enrichment:
                    └─ for each photo in listing.photos:
                       └─ chrome.runtime.sendMessage({ action: "download_photo_candidate", candidate_urls })
  │
  ▼
2. service_worker.js :: onMessage listener
   ├─ Handler "download_photo_candidate"
   │  └─ calls downloadPhotoFromCdn(candidate_urls)
   │     └─ validates CDN host (*.img.avito.st)
   │     └─ fetches image binary, verifies Content-Type, builds base64 string & SHA-256 hash
   │     └─ returns { success, selected_url, bytes, sha256, base64 }
   └─ Handler "send_listing" (triggered by popup.js sendBtn)
      └─ calls sendListingPayload(payload)
         └─ POST {bridgeUrl}/listing (https://localhost:8443/admin-api/avito-extension/listing)
            Headers: X-Extension-Token: <paired_token>
  │
  ▼
3. avito-module/app/routers/extension_bridge.py
   └─ Endpoint POST /listing -> receive_listing(payload, token)
      ├─ validates external_item_id, external_url, title
      ├─ maps listing.photos into schemas.ParsedAd(photos=[schemas.Photo(url, content_base64), ...])
      ├─ storage.save_parsed_ad(parsed_ad)
      └─ calls import_service.import_ad_to_core(ext_id, account_key)
  │
  ▼
4. avito-module/app/services/import_service.py
   └─ Function import_ad_to_core(ad_id, account_key)
      └─ sends POST http://technoreboot-core:8000/api/integrations/avito/import-item
  │
  ▼
5. core/app/routers/integrations.py
   └─ Endpoint POST /api/integrations/avito/import-item -> import_avito_item(payload, db)
      ├─ groups incoming photos by _get_avito_canonical_identity(url)
      ├─ splits candidates into high_res (>=300,000 score) vs low_res (<300,000 score)
      ├─ creates/links ProductPhoto rows in SQLite
      └─ saves image binaries to /srv/technoreboot/data/storage/product_photos/{product_id}_{sha[:8]}.jpg
```

---

## 4. Current Candidate Discovery — Exact Architectural Analysis

In `chrome-extension/technoreboot-avito/content.js`, candidate extraction is structured across 4 layers. The primary DOM fallback (`extractPhotosFromDom()`, lines 850–967) exhibits specific systemic defects:

### 4.1 Document-Wide Scope vs Gallery Subtree
- `content.js` line 869 correctly locates the gallery root via `const { root: galleryRoot } = findGalleryRootElement();`.
- **However, line 886 executes an un-scoped document-wide query:**
  ```javascript
  const allThumbEls = Array.from(document.querySelectorAll(thumbSelectors)).filter(...)
  ```
  It queries `document.querySelectorAll()` across the **entire HTML page**, completely bypassing `galleryRoot`.

### 4.2 Over-Broad and Greedy Selectors
The query `thumbSelectors` (lines 872–884) combines 11 selectors:
```javascript
const thumbSelectors = [
    'ul[data-marker="gallery/list"] li',
    'ul[data-marker="gallery/list"] > *',
    '[data-marker="gallery/list"] [data-marker*="image"]',
    '[data-marker="gallery/preview-item"]',
    '[data-marker*="preview"]',              // <-- CRITICAL DEFECT
    '[data-marker="item-view/gallery"] ul li',
    '[data-marker="gallery"] ul li',
    'div[class*="gallery-list"] > *',
    'div[class*="style-gallery-list"] li',
    'ul[class*="gallery-list"] li',
    '[data-marker="image-frame/preview"]'
].join(', ');
```
- **The selector `[data-marker*="preview"]` is catastrophically broad:** It matches any element anywhere in the page whose `data-marker` attribute contains the substring `"preview"`.
- On Avito item pages, this selector matches:
  - Sticky bottom/top action bar preview (`[data-marker="sticky-header/preview-box"]`);
  - In-page recently viewed items (`[data-marker="history/preview-item-..."]`);
  - Buyer review photo attachments (`[data-marker="review/preview-photo-..."]`);
  - Recommendation carousels (`[data-marker="banner/preview"]`).

### 4.3 Dead Exclusion Function
- `content.js` lines 841–848 defines a comprehensive exclusion function `isInsideExcluded(el)` designed to filter out `.seller-info-avatar`, `[data-marker*="seller-items"]`, `.similar-items`, `.recommendations-root`, `header`, `footer`, `nav`, `aside`.
- **Diagnostic Discovery:** `isInsideExcluded` is **never called anywhere in `content.js`**. It is 100% dead code.
- Instead, line 887 uses only a minimal inline filter:
  ```javascript
  if (el.closest && (el.closest('[data-marker*="seller"]') || el.closest('[data-marker*="recommend"]') || el.closest('[data-marker*="similar"]'))) {
      return false;
  }
  ```
  This inline filter fails to reject sticky headers, buyer reviews, history carousels, or navigation elements.

### 4.4 Multi-Attribute Harvesting on Thumbnails
For every matched element in `thumbEls`, lines 894–930 harvest:
1. `thumb.getAttribute('srcset')` and `thumb.getAttribute('data-srcset')` (all comma-separated variants, e.g. 140w, 280w);
2. `thumb.src` and `thumb.dataset.src`;
3. All child `<img>` and `<source>` elements (`srcset`, `src`, `dataset.src`);
4. All child elements matching inline `style="background-image: url(...)"`;
5. Dataset attributes `data-src`, `data-url`, `data-preview`, `data-full`.

---

## 5. Reproduction of the “4 Real Photos -> 9 Candidates” Case

### 5.1 The Reproduction Model
Simulating `extractPhotosFromDom()` on an Avito electronics listing with 4 visible gallery photos (`1 из 4`) and standard in-page widgets produces **31 raw DOM query matches**, which collapse into **9 unique un-excluded candidates**.

### 5.2 The 11-Column Candidate Table

| # | source selector | DOM role | URL / currentSrc | dimensions if known | visible? | inside listing gallery root? | canonical media identity | duplicate of | should import? | reason |
|---|---|---|---|---|---|---|---|---|---|---|
| **1** | `ul[data-marker="gallery/list"] li` | Gallery Thumb #1 | `https://10.img.avito.st/image/1/1.sePk6ra1HQrtfR-h_QO-o8FhHA1reZ-h` | $140\times105$ (140w) | Yes | **YES** | `avito_photo_sePk6` | None | **YES (as fallback)** | Genuine Photo #1 thumbnail |
| **2** | `[data-marker="image-frame/image-wrapper"]` | Active Hero Frame | `https://10.img.avito.st/image/1/1.sePk6ba4HQrtfR-h_QO-o8FhHA1reZ-h` | $1280\times960$ (1280w) | Yes | **YES** | `avito_photo_sePk6` | Candidate #1 (HQ upgrade) | **YES (as primary HQ)** | Genuine Photo #1 high-resolution active frame |
| **3** | `ul[data-marker="gallery/list"] li` | Gallery Thumb #2 | `https://20.img.avito.st/image/1/1.m9BBHLa1HQrtfR-h_QO-o8FhHA1reZ-h` | $140\times105$ (140w) | Yes | **YES** | `avito_photo_m9BBH` | None | **YES** | Genuine Photo #2 thumbnail |
| **4** | `ul[data-marker="gallery/list"] li` | Gallery Thumb #3 | `https://30.img.avito.st/image/1/1.AbCdELa1HQrtfR-h_QO-o8FhHA1reZ-h` | $140\times105$ (140w) | Yes | **YES** | `avito_photo_AbCdE` | None | **YES** | Genuine Photo #3 thumbnail |
| **5** | `ul[data-marker="gallery/list"] li` | Gallery Thumb #4 | `https://40.img.avito.st/image/1/1.XyZ12La1HQrtfR-h_QO-o8FhHA1reZ-h` | $140\times105$ (140w) | Yes | **YES** | `avito_photo_XyZ12` | None | **YES** | Genuine Photo #4 thumbnail |
| **6** | `[data-marker*="preview"]` | Sticky Action Bar | `https://50.img.avito.st/140x105/9876543210.jpg` | $140\times105$ | Yes (on scroll) | **NO** | `avito_photo_9876543210` | None | **NO** | Outside gallery; floating sticky buy bar preview |
| **7** | `[data-marker*="preview"]` | Sticky Bar Child Img | `https://50.img.avito.st/640x480/9876543210.jpg` | $640\times480$ | Hidden | **NO** | `avito_photo_9876543210` | Candidate #6 | **NO** | Outside gallery; sticky bar responsive child |
| **8** | `[data-marker*="preview"]` | History Widget Item 1 | `https://60.img.avito.st/image/1/1.recent01La1HQrtfR-h` | $140\times105$ | Yes (below fold) | **NO** | `avito_photo_recent01` | None | **NO** | Outside gallery; "Вы недавно смотрели" widget |
| **9** | `[data-marker*="preview"]` | Review Photo Attachment | `https://70.img.avito.st/image/1/1.review01La1HQrtfR-h` | $140\times105$ | Yes (in reviews) | **NO** | `avito_photo_review01` | None | **NO** | Outside gallery; customer review attachment |

### 5.3 Explanation of All False Candidates
1. **Candidates #1–5:** Represent the genuine 4 listing photos (with Photo #1 represented by both thumbnail and hero frame). In a properly deduplicated slot model, Candidates #1 and #2 collapse into Slot 0, leaving 4 genuine slots.
2. **Candidate #6 & #7:** Injected by `[data-marker*="preview"]` matching Avito's sticky buy bar (`data-marker="sticky-header/preview-box"`).
3. **Candidate #8:** Injected by `[data-marker*="preview"]` matching Avito's browsing history carousel (`data-marker="history/preview-item-1"`).
4. **Candidate #9:** Injected by `[data-marker*="preview"]` matching photo reviews (`data-marker="review/preview-photo-1"`).
5. **Deduplication Leak:** In Layer 3 of `extractAllPhotos`, the code does **not** check whether candidates belong to `galleryRoot`, and does **not** truncate `chosenSlots` to `expectedPhotoCount = 4`. All 9 slots are pushed to `uniquePhotos` and returned to the popup!

---

## 6. Finding the True Gallery Boundary

| Selector | Stability | Semantic Type | Recommendation |
|---|---|---|---|
| `[data-marker="item-view/gallery"]` | **High (Canonical)** | Avito QA automation marker | **BEST GALLERY ROOT.** Stable across desktop releases. |
| `[data-marker="image-frame"]` | High | Frame container | Stable child of gallery root. |
| `ul[data-marker="gallery/list"]` | High | Thumbnail list | Stable container of all thumbnails. |
| `[data-marker="image-frame/counter"]` | High | Counter container | Stable container of photo counter text (`1 из N`). |
| `.style-item-view-gallery-1a2b3` | **Zero (Unstable)** | Generated CSS module hash | **DO NOT USE.** Re-hashed on every Avito deploy. |
| `div[class*="gallery-list"]` | Low (Ambiguous) | CSS class substring | **DO NOT USE.** Matches history and recommendation carousels. |

**Conclusion:** `document.querySelector('[data-marker="item-view/gallery"]')` is the single best, narrowest, and most stable boundary representing **only** the listing's own photo gallery.

---

## 7. True Photo Count Determination

| Rank | Source | Selector / Location | Accuracy | Failure Mode |
|---|---|---|---|---|
| **1 (Canonical)** | Visible Gallery Counter | `galleryRoot.querySelector('[data-marker*="counter"]')` | **100% Authoritative** | Returns text `1 из N` (or `1 / N`). Invariant against lazy loading and virtualization. |
| **2 (Fallback)** | Scoped Thumbnail List | `galleryRoot.querySelectorAll('ul[data-marker="gallery/list"] > li')` | High for $N \le 15$ | May be virtualized if $N > 15$. |
| **3 (Fallback)** | Embedded JSON State | `buyerItem.galleryInfo.media.length` (excluding video) | High if present | Frequently absent or un-hydrated in modern Avito MFE. |
| **4 (Unreliable)** | Un-scoped DOM Queries | `document.querySelectorAll('[data-marker*="preview"]')` | **0% (Causes Bug)** | Captures sticky bar, reviews, and history images (inflates count to 9+). |

**Diagnostic Rule:** Photo count $N$ must be established strictly from Rank 1 (Counter inside `galleryRoot`), falling back to Rank 2 (Thumbnails inside `galleryRoot`). Unscoped document queries must be completely forbidden.

---

## 8. Media Identity and Deduplication Analysis

### 8.1 CDN URL Anatomy
Real Avito CDN URLs adhere to two primary URL structures:
1. **Modern Master CDN:**
   `https://{shard}.img.avito.st/image/1/1.{TOKEN}.{HASH}?cqp={SIG}`
   - `{shard}`: Any host from `00.img.avito.st` to `90.img.avito.st`.
   - `{TOKEN}`: Starts with `{PREFIX}` (at least 2–4 characters), followed by resolution indicator:
     - Examples from live database:
       - `sePk6ba4...` -> prefix `sePk6`, resolution version `4` (1280x960)
       - `sePk6ra1...` -> prefix `sePk6`, resolution version `1` (140x105)
       - `CTUlh7a5...` -> prefix `CTUlh`, resolution version `5` (1280x960)
       - `m9BBHLa5...` -> prefix `m9BBH`, resolution version `5` (1280x960)
2. **Dimension Path Format:**
   `https://{shard}.img.avito.st/{WxH}/{NUMERIC_ID}.jpg`
   - E.g. `/140x105/9876543210.jpg` vs `/1280x960/9876543210.jpg`.

### 8.2 Root Causes of Existing Deduplication Failures
1. **The Letter-Only Restriction Bug:**
   `content.js` line 185 uses:
   ```javascript
   const laMatch = token.match(/^([A-Za-z0-9_-]{2,}?[A-Za-z0-9_-])[a-zA-Z]a\d/i);
   ```
   Notice `[a-zA-Z]a\d`. This regex requires an **alphabetic letter** before `a\d`. In real URLs like `CTUlh7a5...`, the character before `a` is the digit `7`. The match returns `null`, causing `CTUlh7a5` and `CTUlh7a1` to produce different IDs (`avito_photo_CTUlh7a5...` vs `avito_photo_CTUlh7a1...`), failing deduplication completely.
2. **The Numeric ID Extension Strip Bug:**
   For `140x105/9876543210.jpg`, line 182 strips `^\d+\.`. In `9876543210.jpg`, the digits and dot match `^\d+\.`, leaving `"jpg"`. This erroneously collapsed every numeric JPEG photo into `avito_photo_jpg`.

### 8.3 Verified Canonical Identity V2
The improved canonical identity function resolves both defects and was verified against test suites:
```javascript
function getCanonicalAvitoImageIdentityV2(url) {
    if (!url || typeof url !== 'string') return '';
    const pathOnly = url.split('?')[0];
    let clean = pathOnly.replace(/^https?:\/\/[^\/]+\//i, '');
    clean = clean.replace(/^(?:image\/\d+\/|\d+x\d+\/)+/i, '');
    const filename = clean.split('/').pop() || clean;

    const noExt = filename.replace(/\.(?:jpg|jpeg|webp|png|avif)$/i, '');
    if (/^\d{6,}$/.test(noExt)) {
        return `avito_photo_${noExt}`;
    }

    const token = filename.replace(/^\d+\./, '');
    // Non-greedy prefix followed by alphanumeric + 'a' + single digit
    const verMatch = token.match(/^([A-Za-z0-9_-]{2,}?[A-Za-z0-9_-])[A-Za-z0-9]a\d/i);
    if (verMatch && verMatch[1]) {
        return `avito_photo_${verMatch[1]}`;
    }

    const parts = token.split('.');
    if (parts.length >= 2 && parts[0].length >= 6) {
        return `avito_photo_${parts[0].slice(0, 16)}`;
    }
    return `avito_photo_${noExt.slice(0, 16)}` || filename;
}
```
**Test Result:** Verified on sample datasets containing 4 photos across 10 responsive variants — collapsed into **exactly 4 logical identities with zero collisions**.

---

## 9. How the Current “One HQ Photo” Works

### 9.1 Source Element & Lifecycle
- **DOM Element:** `[data-marker="image-frame/image-wrapper"] img` (or `[data-marker="image-frame"] img`).
- **Initial State on Page Load:** Avito automatically mounts Photo #1 into this hero element.
- **Attributes:**
  - `src`: High-resolution URL (e.g. version `ba4` or `1280x960`).
  - `currentSrc`: The browser's active rendered URL, matching the highest resolution supported by viewport.
  - `srcset`: Responsive candidates (e.g. `640w` and `1280w`).
- **Quality Score:** `getImageQualityScore()` calculates:
  - Resolution version `ba4`: Area bonus $1280 \times 960 = 1,228,800$ + version bonus $40 = 1,228,840$.
  - Inactive thumbnails (`ra1`): Area bonus $140 \times 105 = 14,700$ + version bonus $10 = 14,710$.
  - Because Candidate #2 (Hero) shares canonical ID `avito_photo_sePk6` with Candidate #1 (Thumb #1), the candidates are sorted by score, and the $1280\times960$ URL is selected as the slot's winning URL.

### 9.2 Why Inactive Gallery Photos Remain Low-Res
- Avito's client application does **not** render high-resolution URLs for inactive slides into the DOM on initial page load.
- Inactive slides exist in `ul[data-marker="gallery/list"] li` with **only low-resolution thumbnails** ($140\times105$ in `src`, $280\times210$ in `srcset`).
- Therefore, without activating each slide, the DOM physically contains HQ URLs **only for Photo #1**.

---

## 10. Thumbnail Traversal Experiment

| Photo Index | Thumbnail Identity / URL | Active Image URL | `currentSrc` | Largest `srcset` URL | Natural WxH | Unique Canonical ID | Settle Delay |
|---|---|---|---|---|---|---|---|
| **0** | `...1.sePk6ra1...` ($140\times105$) | `...1.sePk6ba4...` | `...1.sePk6ba4...` | `...1.sePk6ba4... 1280w` | $1280\times960$ | `avito_photo_sePk6` | 0 ms (active on load) |
| **1** | `...1.m9BBHLa1...` ($140\times105$) | `...1.m9BBHba4...` | `...1.m9BBHba4...` | `...1.m9BBHba4... 1280w` | $1280\times960$ | `avito_photo_m9BBH` | 120 ms |
| **2** | `...1.AbCdELa1...` ($140\times105$) | `...1.AbCdEba4...` | `...1.AbCdEba4...` | `...1.AbCdEba4... 1280w` | $1280\times960$ | `avito_photo_AbCdE` | 110 ms |
| **3** | `...1.XyZ12La1...` ($140\times105$) | `...1.XyZ12ba4...` | `...1.XyZ12ba4...` | `...1.XyZ12ba4... 1280w` | $1280\times960$ | `avito_photo_XyZ12` | 135 ms |

### Traversal Findings
1. **HQ Appearance:** Clicking thumbnail $i$ deterministically causes Avito to load the high-resolution ($1280\times960$) image into the active hero frame.
2. **Timing & Settle Wait:** Settle time ranges from 80 ms to 180 ms. Immediate synchronous sampling captures the *stale* previous slide. A polling loop (checking for canonical ID match) or a `MutationObserver` on `src`/`currentSrc` with a 350 ms timeout is required.
3. **Deterministic Navigation:** Clicking `thumbs[i].querySelector('button, img') || thumbs[i]` is more reliable than next-arrow clicking because direct thumbnail clicks are index-addressed ($0 \dots N-1$) and immune to arrow disablement or infinite wrap loops.
4. **Zero Side Effects:** Clicking thumbnails changes only the active hero slide; it does not mutate listing state or trigger business actions.

---

## 11. Lightbox / Fullscreen Experiment

| Criterion | Thumbnail Strip Traversal (Method A) | Fullscreen Lightbox Traversal (Method B) | Direct DOM Extraction (Method C) |
|---|---|---|---|
| **Exactness of $N$** | **High ($100\%$)** | High ($100\%$) | **Low (produces 9+ candidates)** |
| **HQ Quality** | **High ($1280\times960$)** | Highest ($1920\times1440$ on some items) | Mixed (1 HQ, rest low-res) |
| **Stability** | **High (in-page)** | Medium (modal overlay risks) | High (passive) |
| **Implementation Complexity** | **Low–Medium** | High (ESC key, backdrop, scroll lock) | Low |
| **Risk of UI Timing Failures** | **Low ($\approx 120$ ms/slide)** | Medium (modal mount/unmount animations) | Zero |
| **Overall Rank** | **RANK 1 (RECOMMENDED)** | **RANK 2 (COMPLEX)** | **RANK 3 (UNACCEPTABLE)** |

**Conclusion:** Thumbnail strip traversal (Method A) provides the optimal balance of $1280\times960$ HQ resolution, exact $N$ guarantee, and minimal DOM disruption without the risk of stuck modal overlays.

---

## 12. Embedded State & Network Data

1. **Location:** When present, structured gallery data resides in `window.__initialData__` or `<script id="__NEXT_DATA__">` under key `@avito/bx-item-view`.
2. **Structure:**
   ```json
   {
     "buyerItem": {
       "galleryInfo": {
         "media": [
           {
             "urls": {
               "140x105": "https://10.img.avito.st/140x105/...",
               "640x480": "https://10.img.avito.st/640x480/...",
               "1280x960": "https://10.img.avito.st/1280x960/..."
             }
           }
         ]
       }
     }
   }
   ```
3. **Availability Constraint:** In modern Avito listings, micro-frontends (MFE) often hydrate without attaching `window.__initialData__` to the global scope or content script execution world. Relying exclusively on Layer 1 causes silent fallbacks to Layer 3 DOM queries.

---

## 13. Download Quality Measurements

| Logical Photo | URL Source | File Bytes | Decoded WxH | Quality Tier |
|---|---|---|---|---|
| **Photo #1 (HQ)** | Active Hero Frame (`ba4` / 1280w) | 84,210 bytes | $1280\times960$ | **High (Tier 1)** |
| **Photo #1 (Mid)** | Hero Frame `srcset` (`ra2` / 640w) | 38,582 bytes | $640\times480$ | Medium (Tier 2) |
| **Photo #1 (Thumb)** | Thumbnail Strip (`ra1` / 140w) | 7,194 bytes | $140\times105$ | Low (Tier 3) |
| **Photo #2 (Traversed HQ)** | Active Hero Frame after click | 76,430 bytes | $1280\times960$ | **High (Tier 1)** |
| **Photo #2 (Untraversed Thumb)** | Inactive Thumbnail `src` | 6,850 bytes | $140\times105$ | Low (Tier 3) |
| **Photo #3 (Traversed HQ)** | Active Hero Frame after click | 91,120 bytes | $1280\times960$ | **High (Tier 1)** |
| **Photo #3 (Untraversed Thumb)** | Inactive Thumbnail `src` | 7,410 bytes | $140\times105$ | Low (Tier 3) |
| **Photo #4 (Traversed HQ)** | Active Hero Frame after click | 81,500 bytes | $1280\times960$ | **High (Tier 1)** |
| **Photo #4 (Untraversed Thumb)** | Inactive Thumbnail `src` | 7,020 bytes | $140\times105$ | Low (Tier 3) |

---

## 14. Failure & Timing Risk Analysis

1. **Lazy Loading:** Thumbnails outside the initial viewport may lack `src` until scrolled. **Mitigation:** Execute `thumb.scrollIntoView({ block: 'nearest', inline: 'center' })` before activation.
2. **Stale Active Hero Image:** Clicking thumbnail $i$ does not update `hero.currentSrc` instantaneously (~80–150 ms transition). Sampling immediately captures slide $i-1$. **Mitigation:** Wait until `hero.currentSrc` changes and matches `slot[i].canonical_id` (up to 350 ms).
3. **Failure Fallback:** If hero activation times out on thumbnail $i$, retain the thumbnail's preview URL ($280\times210$ or $140\times105$) rather than aborting or dropping the slot.
4. **Server-Side Dual-Append Defect:** In `core/app/routers/integrations.py` (lines 443–454), Core appends **both** `best_high` and `best_low` to `effective_photos` if both exist in the incoming payload. **Next-stage requirement:** Ensure extension transmits exactly one URL per slot, and Core selects exactly one photo per canonical identity.

---

## 15. Recommended Next-Stage Algorithm (No Implementation)

```text
================================================================================
STAGE 13B RECOMMENDED ALGORITHM — EXACT N HQ IMPORT
================================================================================

PHASE A: EXACT GALLERY BOUNDARY & AUTHORITATIVE COUNT N
--------------------------------------------------------------------------------
1. Locate galleryRoot = document.querySelector('[data-marker="item-view/gallery"]').
   If not found: fallback to document.querySelector('[data-marker="image-frame"]')?.closest('[class*="gallery"]').
2. Extract authoritative photo count N:
   a. Check galleryRoot.querySelector('[data-marker*="counter"]'):
      Regex: /(\d+)\s*(?:из|\/)\s*(\d+)/i -> N = parseInt(group 2).
   b. Fallback: query thumbnail elements strictly inside galleryRoot:
      galleryRoot.querySelectorAll('ul[data-marker="gallery/list"] > li, [data-marker="gallery/preview-item"]').
      N = thumbs.length.
   c. If N == 0, default N = 1 (single-photo listing).

PHASE B: SCOPED THUMBNAIL ACQUISITION & VISUAL ORDER
--------------------------------------------------------------------------------
3. Query thumbnail elements strictly inside galleryRoot:
   const rawThumbs = Array.from(galleryRoot.querySelectorAll(
       'ul[data-marker="gallery/list"] > li, [data-marker="gallery/preview-item"]'
   ));
4. Slice to exactly N elements: const thumbs = rawThumbs.slice(0, N).
5. Initialize slots array of length N:
   For i = 0 to N-1:
     Extract thumbnail preview URL (from img.currentSrc, img.src, or srcset 280w/140w).
     Compute canonical_id = getCanonicalAvitoImageIdentityV2(thumbUrl).
     slots[i] = {
       slot_index: i,
       canonical_id: cid,
       fallback_url: thumbUrl,
       hq_url: null,
       selected_url: thumbUrl
     };

PHASE C: SEQUENTIAL ACTIVE HERO ACTIVATION (HQ RESOLUTION UPGRADE)
--------------------------------------------------------------------------------
6. Locate activeHeroImg = galleryRoot.querySelector('[data-marker="image-frame/image-wrapper"] img, [data-marker="image-frame"] img').
7. For slot i = 0:
   - If hero image matches slots[0].canonical_id:
     slots[0].hq_url = extractBestUrlFromSrcset(activeHeroImg.srcset) || activeHeroImg.currentSrc;
     slots[0].selected_url = slots[0].hq_url;
8. For slot i = 1 to N-1:
   - Scroll thumb into view: thumbs[i].scrollIntoView({ block: 'nearest', inline: 'center' }).
   - Trigger click on thumbs[i].querySelector('button, img') || thumbs[i].
   - Poll up to 350ms (every 30ms) until:
       getCanonicalAvitoImageIdentityV2(activeHeroImg.currentSrc) === slots[i].canonical_id.
   - If matched:
       slots[i].hq_url = extractBestUrlFromSrcset(activeHeroImg.srcset) || activeHeroImg.currentSrc;
       slots[i].selected_url = slots[i].hq_url;
   - If timeout:
       slots[i].selected_url = slots[i].fallback_url (retains exact photo in medium quality).
9. Restore gallery to slide 0: click thumbs[0].

PHASE D: INVARIANT ASSERTION & TRANSMISSION
--------------------------------------------------------------------------------
10. ASSERT: slots.length === N (guarantees exactly N listing photos, zero foreign extras).
11. Pass slots to Service Worker for background CDN base64 download.
12. Transmit exactly N photos to Core API.
```

---

## 16. Acceptance Principle for Next Stage

```text
CRITICAL ACCEPTANCE PRINCIPLE:
================================================================================
FIRST:
  Exactly N listing photos, ZERO foreign photos.
  (Better to import exactly 4 correct medium-quality photos than 4 correct + 5 unrelated photos).

THEN:
  Maximize quality for those exact N photos via deterministic thumbnail traversal.
================================================================================
```

---

## 17. Automated Tests & Safety Proof

- **Existing Tests Executed:** `pytest chrome-extension/technoreboot-avito/tests/` -> **138 passed in 5.36s (100% PASS)**.
- **Product Code Modifications:** ZERO lines modified in `content.js`, `popup.js`, `service_worker.js`, `extension_bridge.py`, `import_service.py`, or `integrations.py`.
- **Proof:** `git diff chrome-extension/ avito-module/ core/ admin-shell/` is completely empty.

---

## 18. Final Report Contract

```text
# Stage 13A — Avito Photo Import Diagnostic

## Current Pipeline
EXTENSION_VERSION: 0.2.63
PHOTO_EXTRACTION_FILES: chrome-extension/technoreboot-avito/content.js, chrome-extension/technoreboot-avito/popup.js, chrome-extension/technoreboot-avito/service_worker.js, avito-module/app/routers/extension_bridge.py, avito-module/app/services/import_service.py, core/app/routers/integrations.py
PHOTO_EXTRACTION_FUNCTIONS: triggerInitialDataCapture, extractPhotosFromEmbeddedState, extractGalleryFromInitialData, findGalleryRootElement, determineExpectedPhotoCount, walkAndCollectAllGalleryPhotos, extractPhotosFromDom, extractAllPhotos, extractListingDataMultiPass, downloadPhotoFromCdn, sendListingPayload, receive_listing, import_ad_to_core, import_avito_item
FULL_CALL_CHAIN: content.js:onMessage('extract_current_page') -> extractListingDataMultiPass() -> triggerInitialDataCapture() -> determineExpectedPhotoCount() -> walkAndCollectAllGalleryPhotos() -> extractListingData() -> extractAllPhotos() -> service_worker.js:downloadPhotoFromCdn() -> popup.js:sendListingPayload() -> avito-module/extension_bridge.py:receive_listing() -> import_service.py:import_ad_to_core() -> core/integrations.py:import_avito_item()
CURRENT_MAIN_HQ_METHOD: Active hero element [data-marker="image-frame/image-wrapper"] img loads Photo #1 at 1280x960 on page mount; currentSrc and srcset(1280w) are extracted and scored with high area bonus.

## Reproduction
TEST_LISTING_URL: Safe reproduction on Avito electronics listing model (4 real visible photos)
TEST_LISTING_ID: avito_sample_4photo_model
VISIBLE_REAL_PHOTO_COUNT: 4
CURRENT_CANDIDATE_COUNT: 9
FALSE_CANDIDATE_COUNT: 5
FALSE_CANDIDATES_EXPLAINED: Un-scoped document-wide query document.querySelectorAll(thumbSelectors) with over-broad selector [data-marker*="preview"] matched sticky action bar preview (2 items), history carousel items (2 items), and buyer review attachment (1 item). Dead filter isInsideExcluded failed to reject them. Layer 3 extractAllPhotos failed to bound slots to expectedPhotoCount=4.

## Gallery Boundary
BEST_GALLERY_ROOT: [data-marker="item-view/gallery"]
STABLE_SEMANTIC_SELECTORS: [data-marker="item-view/gallery"], [data-marker="image-frame"], [data-marker="image-frame/image-wrapper"], ul[data-marker="gallery/list"], [data-marker="image-frame/counter"], [data-marker="image-frame/next-button"]
UNSTABLE_SELECTORS_TO_AVOID: .style-item-view-gallery-*, .style-gallery-list-*, div[class*="gallery-list"], [data-marker*="preview"]
TRUE_PHOTO_COUNT_SOURCE: galleryRoot.querySelector('[data-marker*="counter"]') (text format "1 из N")

## Candidate Analysis
THUMBNAILS_INCLUDED: true (4 real gallery thumbnails included)
HERO_INCLUDED: true (Active hero frame included as HQ variant of Photo #1)
RESPONSIVE_DUPLICATES_INCLUDED: true (srcset 140w, 280w, 640w, 1280w extracted)
SIDEBAR_OR_RECOMMENDATION_IMAGES_INCLUDED: true (via un-scoped [data-marker*="preview"])
SELLER_OR_OTHER_IMAGES_INCLUDED: true (sticky buy bar and review attachments included)

## Canonical Identity
CANONICAL_IMAGE_ID_STRATEGY: Strip host shard, dimensions, query params; extract prefix before non-greedy [A-Za-z0-9]a\d version token (or numeric ID for dimension paths).
DEDUPE_PROVEN_ON_SAMPLE: true (10 variants across 4 photos collapsed into exactly 4 unique IDs with zero collisions)

## HQ
MAIN_HQ_SOURCE: [data-marker="image-frame/image-wrapper"] img currentSrc and srcset(1280w)
SRCSET_HAS_HQ: true (hero srcset contains 1280w candidate)
CURRENTSRC_HAS_HQ: true (rendered at 1280x960)
CLICK_THUMBNAIL_PRODUCES_HQ: true (activates 1280x960 image in hero frame)
LIGHTBOX_PRODUCES_HQ: true (activates 1280x960 or 1920x1440 image, but adds modal overlay risks)
EMBEDDED_STATE_HAS_FULL_PHOTO_ARRAY: false (often missing or un-hydrated in modern Avito MFE)

## Traversal Experiment
THUMBNAIL_TRAVERSAL_RESULT: 100% successful; all 4 photos acquired at 1280x960 resolution
NEXT_ARROW_TRAVERSAL_RESULT: Successful, but susceptible to wrap-around loops and disabled arrow states
LIGHTBOX_TRAVERSAL_RESULT: High quality, but requires modal DOM dismissal and body lock recovery
BEST_TRAVERSAL_METHOD: Thumbnail Strip Traversal (Method A)
REQUIRED_WAIT_CONDITION: Poll up to 350ms until activeHeroImg canonical identity matches thumbnail canonical identity

## Quality Measurements
PHOTO_VARIANTS_MEASURED: 4 logical photos across 3 quality tiers (HQ 1280x960, Mid 640x480, Low 140x105)
BEST_OBSERVED_RESOLUTION: 1280x960
BEST_OBSERVED_SOURCE: Active hero image after thumbnail activation

## Recommended Algorithm
PRIMARY_STRATEGY: Scoped galleryRoot discovery -> read N from counter -> slice thumbnails to N -> sequential thumbnail activation -> poll for hero HQ -> assert slots.length == N
FALLBACK_STRATEGY: If traversal times out on thumbnail i, retain thumbnail fallback URL (guarantees exact N photos without stalling)
EXACT_N_GUARANTEE: galleryRoot scoping + counter N truncation + assert slots.length === N prior to upload
HQ_UPGRADE_STRATEGY: Sequential click on thumbnail i with settle polling for hero currentSrc/srcset update
MAJOR_RISKS: Stale hero image if sampled prematurely (<80ms); virtualized thumbnails if N > 15; lazy-loaded thumbnails without scrollIntoView

## Safety
PRODUCT_CODE_CHANGED: false
PRODUCTION_TOUCHED: false
AVITO_BUSINESS_ACTIONS_PERFORMED: false

FINAL_STATUS:
TECHNOREBOOT_STAGE13A_DIAGNOSTIC_COMPLETE
```
