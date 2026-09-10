# Stage 07F-R1-R1 — Real Avito Profile Zero Listings Fix

## 1. Context & Problem Statement
During real-world browser testing of Chrome Extension v0.2.48 on the Owner's Avito cabinet page (`/profile/items`), the extension identified the page as a listings page, but DOM extraction reported:
```text
Найдено объявлений на странице: 0
Страница: 1 из 1
...
✓ Импорт успешно завершен!
Страниц обработано: 1, объявлений: 0
```
This failure stemmed from four root causes:
1. **Narrow Card Selectors**: The existing selectors (`.iva-item-root`, `[data-marker="catalog-serp/item"]`, `.item-snippet`) target desktop search catalog grids and failed to match Avito's personal cabinet / profile DOM markup (`[data-marker="item-root"]`, `[data-marker^="item-"]`, dynamic React CSS module classes).
2. **Missing Fallback Strategy**: If container selectors yielded zero nodes, the extension gave up and did not attempt to scan anchor links pointing to Avito item IDs.
3. **Premature Extraction on Dynamic Pages**: Fast popup inspection occurred before client-side React hydration completed, immediately returning zero cards.
4. **False Positive UI**: When zero items were extracted, the bulk import loop unconditionally displayed `✓ Импорт успешно завершен!`.

---

## 2. Technical Solution

### 2.1 Layered DOM Extraction & Anchor Fallback (`content.js`)
- **Layer 1: Broad Multi-Selector**: Matches cards across both personal cabinet and public seller profiles:
  `[data-marker="item"], [data-marker^="item-"], [data-marker="item-root"], [data-marker="item-snippet"], [data-marker^="item-snippet"], [data-marker="catalog-serp/item"], [data-marker^="profile-item"], [data-marker^="extended-item"], [data-marker="profile/item"], [data-marker*="snippet"], [data-item-id], div[class*="item-snippet"], div[class*="ItemSnippet"], div[class*="snippet-"], div[class*="Snippet-"], div[class*="styles-root-"], div[class*="styles-module-root-"], .iva-item-root, .items-item, article`
- **Layer 2: Anchor Fallback**: Scans all `a[href]` on the page for Avito item URL patterns (`_(\d{8,14})`, `item_?id=(\d{8,14})`, `/(?:item|items)/(\d{8,14})`). For every matched anchor:
  - Finds enclosing card boundary via `findCardContainerForAnchor()`.
  - Extracts title, price, status, location, thumbnail.
  - Deduplicates items strictly by `avito_id`.
- **Missing Price Resilience**: If a price cannot be extracted (e.g. "Цена договорная"), price is preserved as `null` without dropping the listing.

### 2.2 Bounded Asynchronous Rendering Wait (`content.js`)
- Implemented `extractMyListingsDataAsync(maxWaitMs = 10000)`:
  - If cards are present immediately, resolves synchronously (0ms delay).
  - If zero cards are found, establishes a `MutationObserver` on the DOM and polls every 250ms.
  - Terminates immediately as soon as cards appear or after bounded timeout (10s).

### 2.3 Page Type Classification (`content.js`)
- `detectPageType()` deterministically separates:
  - Personal cabinet / seller profile (`/profile`, `/my/items`, `/user/`, `sellerId=`).
  - Single listing view (`item-view/title-info`, single item URL slug).
  - Catalog SERP pages.

### 2.4 Zero-Result Warning UI Policy (`popup.js`)
- When `items.length === 0`:
  - `bulkImportAllBtn` and `bulkImportCurrentBtn` are disabled.
  - Displays warning: `«Объявления не найдены. Проверьте, что список объявлений загрузился полностью.»`.
  - Adds an interactive «Повторить поиск» re-scan link.
- In `bulkImportAllBtn`:
  - When `totalProcessed === 0`, displays a warning banner (`msg msg-warning`) and NEVER green success.

### 2.5 Multi-Page Traversal & Loop Protection
- `extractPaginationInfo()` detects cabinet pagination buttons, page links, next buttons, and infinite scroll triggers.
- Protected by `MAX_PAGES = 50`, `visitedUrls` set, and `seenAvitoIds` set.

### 2.6 Version Bump to 0.2.49
- Bumper version `0.2.48` -> `0.2.49` across:
  - `chrome-extension/technoreboot-avito/manifest.json`
  - `chrome-extension/technoreboot-avito/popup.html`
  - `chrome-extension/technoreboot-avito/popup.js`
  - `chrome-extension/technoreboot-avito/content.js`
  - `chrome-extension/technoreboot-avito/service_worker.js`
  - `avito-module/app/routers/extension_bridge.py`
  - `admin-shell/app/templates/avito_extension.html`
  - `admin-shell/app/main.py`
  - Extension zip: `dist/technoreboot-avito-extension-0.2.49.zip`
