# Stage 07F-R1-R3-R3 — Real Avito 0/50 Thumbnail DOM Fix

## 1. Overview & Problem Statement
During Owner testing of extension v0.2.52 on the real Avito cabinet (`https://www.avito.ru/profile/items`), 50 listings were detected, but 0 thumbnails were extracted:
```text
Список объявлений Avito
Найдено объявлений: 50
Страница: 1 из 3
Фото найдено: 0 из 50
⚠️ Внимание: фото не найдены в карточках объявлений на этой странице (0 из 50).
```

## 2. Proven Root Cause Analysis
Detailed reverse engineering of the live DOM extraction identified three core root causes:

1. **Card Root Boundary Mis-scoping in `findCardContainer(el)`:**
   - The selector `div[class*="styles-module-root-"]` matched broad wrapper elements encompassing multiple items in modern Avito layout variants.
   - When a parent container encompassed multiple listings, image extraction evaluated images belonging to subsequent or previous cards, or fell back incorrectly.
   - Fixed by requiring strict card identification: checking that exactly one listing anchor/id exists inside the scoped container (`distinctIds.size === 1`), prioritizing `[data-marker="item"]`, `[data-marker*="item-"]`, `article`, and `li[class*="styles-item"]`.

2. **Over-strict Host Rejection in `isValidImageUrl(url)`:**
   - Real Avito CDN domains include `avito.st`, `*.avito.st` (such as `10.img.avito.st`, `20.img.avito.st`, `img.avito.st`, `static.avito.st`), in addition to `avito.ru`.
   - The exclusion filter previously rejected paths containing `/profile/` as user profiles. However, real product URLs and certain assets on the own-listings cabinet can reference `/profile/items/` or use `/profile/` in specific paths.
   - Fixed by explicitly validating `hostname.endsWith('avito.st') || hostname.endsWith('avito.ru')`, ensuring avatar/seller badges are specifically filtered (`avatar`, `seller-badge`, `icon-`, `logo`, `rating`, `star`, `badge`) without false positives on cabinet item media.

3. **Multi-Source Thumbnail Extraction Pipeline:**
   - Real Avito cabinet uses 6 distinct markup patterns:
     1. Standard `<img>` with `src` pointing to `*.avito.st` (e.g. `//10.img.avito.st/image/1/...`).
     2. `<img>` with `srcset` / `data-srcset` with multi-resolution descriptors (e.g. `url1 1x, url2 2x`).
     3. `<picture><source srcset="..."><img></picture>` elements.
     4. Inline CSS `style="background-image: url(...)"` with single, double, or unquoted URLs and protocol-relative `//` URLs.
     5. Lazy-loaded image containers with `data-src`, `data-original`, `data-lazy-src`, `data-image-url`.
     6. Viewport-triggered lazy images requiring programmatic scroll/intersection dispatch.
   - Fixed by implementing an 8-stage comprehensive extractor `extractThumbnailFromContainer(container)` that evaluates all sources sequentially, normalizes protocol-relative URLs (`//` -> `https://`), parses `srcset` to pick the best resolution, handles quoted background styles, and dispatches scroll events if no image is initially populated.

4. **Base64 Payload Format Alignment:**
   - When base64 data URIs are captured (`data:image/jpeg;base64,...`), the bridge and Core routers now safely handle both prefixed and raw base64 data by stripping any `data:image/...;base64,` prefix before decoding.

## 3. Extension Bump to v0.2.53
- Bumped extension version to `0.2.53` across:
  - `manifest.json`
  - `popup.html` and `popup.js`
  - `service_worker.js`
  - `content.js`
  - `avito-module/app/routers/extension_bridge.py`
  - `admin-shell/app/main.py`
  - `admin-shell/app/templates/avito_extension.html`
- Rebuilt distribution packages:
  - `dist/technoreboot-avito-extension-0.2.53.zip`
  - `admin-shell/app/technoreboot-avito-extension-0.2.53.zip`
  - `admin-shell/app/technoreboot-avito-extension.zip`
- Verified ZIP content matches manifest v0.2.53.

## 4. Verification & Testing
- Automated test suites:
  - `avito-module/tests/test_stage07f_r1_r3_r3_zero_of_50_fix.py`: 10/10 tests passed (Tests A through J).
  - `chrome-extension/technoreboot-avito/tests/`: 126/126 passed.
  - `avito-module/tests/`: 154/154 passed.
  - `core/tests/` (photo and avito): 54/54 passed.
- Live Gateway (mTLS Port 8443) verification via `scripts/verify_stage07f_r1_r3_r3_zero_of_50_fix.py`:
  - Scenario 1: Version 0.2.53 synchronization across all modules.
  - Scenario 2: Admin-shell ZIP download serving verified 0.2.53 manifest.
  - Scenario 3: Extension pairing with fresh token.
  - Scenario 4: Extraction across all 6 real Avito cabinet markup variants.
  - Scenario 5: Full 50/50 listings photo ingestion end-to-end to Core database.
  - Scenario 6: Media endpoint 200 OK and physical file persistence check.
  - Scenario 7: Re-import idempotency (no duplicate products or photos created).
  - Scenario 8: Database catalog invariant: 193 business products strictly preserved.
