# Stage 13C Diagnostic Report: Single-Photo Anomaly in Avito Extension

**Date:** 2026-09-21  
**Target:** Chrome Extension `technoreboot-avito` (v0.2.64 / v0.2.65)  
**Environment:** Local Development (`https://localhost:8443` / `http://127.0.0.1:8011`)  
**Status:** BLOCKED / AWAITING SUPERVISOR GUIDANCE  

---

## 1. Executive Summary

Following the deployment of Stage 13B (exact-N gallery extraction and per-photo HQ activation), live testing on real Avito listing pages revealed that the extension consistently detects and imports **only 1 photo**, even on ads with 5–15 high-quality photos.

An initial remediation (v0.2.65) was implemented to widen thumbnail selectors, prevent gallery root scope isolation, and allow next-button walking without text counters. However, user verification confirms that **v0.2.65 still detects only 1 photo** on live listings.

This report details:
1. What was implemented and why it did not resolve the live behavior.
2. The core architectural disconnect discovered between `popup.js` and `content.js`.
3. Technical hypotheses regarding live Avito DOM and React event delegation.
4. Specific questions and investigation vectors for the supervisor.

---

## 2. What Was Analyzed & Implemented in v0.2.65

### 2.1 The Four Hypothesized Root Causes (v0.2.65)
During the Stage 13C preflight, the following static DOM flaws were identified and fixed:
1. **Gallery Root Isolation (`findGalleryRootElement`):**
   - *Problem:* Falling back to `[data-marker="image-frame"]` isolated the query scope so sibling thumbnails (`gallery/list`) were invisible.
   - *Fix:* Prioritized outer gallery layout containers (`.gallery-root`, `.gallery-layout`, `item-view/gallery`, `item-view/main`) and climbed up to the enclosing parent if anchored on `image-frame`.
2. **Over-Pruned Thumbnail Selectors (`GALLERY_THUMB_SELECTORS`):**
   - *Problem:* Restricted exclusively to `ul[data-marker="gallery/list"] li`, missing carousel tracks and variant class wrappers (`div[class*="gallery-list"] > *`, `div[class*="style-gallery-list"] li`, `[data-marker="gallery/image"]`, etc.).
   - *Fix:* Created `findGalleryThumbnailElements(scope)` querying all known Avito preview variants, deduplicating nested elements, and strictly filtering foreign widgets (`sticky`, `history`, `review`, `seller`, `similar`).
3. **Gating Behind Missing Text Counter (`targetN > 0`):**
   - *Problem:* In `walkAndCollectAllGalleryPhotos`, next-button traversal was guarded by `if (targetN > 0 && slots.length < targetN)`. On desktop Avito, the text counter ("1 из 8") is not rendered in the DOM by default (only on hover/modal), so `targetN === 0` prevented the next button from ever being clicked.
   - *Fix:* Enabled `shouldWalkNext` when `(targetN > 0 && slots.length < targetN) || (slots.length <= 1) || (targetN === 0 && slots.length < 15)`.
4. **False-Positive Truncation Guard:**
   - *Problem:* `chosenSlots.slice(0, expectedPhotoCount)` clamped results when `expectedPhotoCount === 1`.
   - *Fix:* Replaced with `effectiveTargetN` to prevent truncating multiple genuine traversed slides.

### 2.2 Test Results for v0.2.65
- `chrome-extension/technoreboot-avito/tests/`: **168 passed** (100% pass rate).
- `scripts/run_targeted_tests.py`: **164 passed**, 0 failed.
- `admin-shell/tests/`: **103 passed**, 1 skipped, 0 failed.
- Archive `technoreboot-avito-extension-0.2.65.zip` was built and verified.

---

## 3. Why It Still Fails on Live Avito (Root-Cause Analysis)

Despite passing all 168 synthetic tests, live behavior in Chrome still results in 1 photo. Analysis reveals two critical systemic blockers:

### Blocker 1: The Asynchronous Communication Split in `popup.js` vs `content.js`

In `chrome-extension/technoreboot-avito/content.js`:
```javascript
if (request.action === "extract_current_page") {
    if (pageType === "my_listings") {
        ...
    } else if (request.deepScan) {
        extractListingDataMultiPass()
            .then(data => sendResponse(data || extractListingData()))
            .catch(() => sendResponse(extractListingData()));
        return true;
    } else {
        sendResponse(extractListingData()); // <--- SYNCHRONOUS, extraPhotos = []
    }
}
```

In `chrome-extension/technoreboot-avito/popup.js`:
1. On popup open (`DOMContentLoaded`), `popup.js` line 1466 calls:
   ```javascript
   sendMessageToTabWithAutoInject(activeTab.id, { action: "extract_current_page", deepScan: false }, response => {
       setupSingleListingSection(activeTab, response);
   });
   ```
2. Because `deepScan: false`, `content.js` immediately executes `extractListingData()` **without multi-pass traversal**!
3. `setupSingleListingSection` immediately renders the UI based on `response`:
   ```javascript
   const detectedPhotosCount = (item.photos && item.photos.length) || 0;
   const visibleCount = (response.diagnostics && response.diagnostics.visible_gallery_count) || 0;
   const initialDisplayCount = Math.max(detectedPhotosCount, visibleCount);
   // Renders: "Обнаружено фото: 1 (сканирование HD...)"
   ```
4. Only *after* rendering does `popup.js` issue a second message with `deepScan: true` (line 1163).
5. If the user clicks **«Доимпортировать данные»** before `deepResponse` resolves (or if `deepScan` fails / times out silently), the payload sent to Core is the **initial synchronous payload containing only 1 photo**!

### Blocker 2: Live Avito DOM Hydration & Event Delegation

Why does `extractPhotosFromDom()` (synchronous pass) only find 1 photo?
- On real Avito (desktop 2026), listings are rendered via Next.js / React SSR + hydration.
- The hero image (`[data-marker="image-frame"] img`) is rendered immediately.
- However, the thumbnails strip or carousel track is frequently:
  - Inside a virtualized slider where non-active thumbnails do not render full `<img>` tags or valid URLs until interaction.
  - Or styled with CSS-module classes that change between builds, while `[data-marker="gallery/list"]` has been deprecated or refactored by Avito into an un-marked flex container.
  - Or thumbnails use lazy-loading placeholder attributes (e.g. `data-src` without `src`) that might fail image validation.

Why does `walkAndCollectAllGalleryPhotos` (active traversal) fail or return 1 photo on live pages?
- In `walkAndCollectAllGalleryPhotos`, slide progression relies on:
  ```javascript
  nextBtn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  if (typeof nextBtn.click === 'function') nextBtn.click();
  ```
- Modern React 18+ attaches event listeners at the root document node using `PointerEvent` / synthetic event pools. Synthetic `MouseEvent('click')` dispatched on an element often does **not** trigger React component state transitions (`setActiveIndex(prev => prev + 1)`).
- If the click does not cause React to update the DOM, `newId === prevId` triggers `consecutiveNoChange >= 3` and the loop aborts after 1.2 seconds, leaving `slots` with only the initial hero photo (#0).

---

## 4. Proposed Architectural Solutions for Supervisor Review

### Option A: Unified Async Extraction (Eliminate Synchronous Shallow Scan)
Make `extract_current_page` always run `extractListingDataMultiPass()` asynchronously.
- The popup displays a spinner: *"Сканирование галереи объявления (поиск всех фото)..."*
- The "Импортировать" button remains disabled until the scan finishes and the true photo count is confirmed.
- Eliminates race conditions where shallow scan (1 photo) is transferred before deep scan completes.

### Option B: Robust Live DOM Navigation / React Event Simulation
To reliably trigger Avito's slider in React 18:
1. Dispatch full pointer lifecycle: `pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click` on `nextBtn`.
2. Target the exact interactive child: `nextBtn.querySelector('button, svg') || nextBtn`.
3. Direct keypress navigation: dispatch `ArrowRight` KeyboardEvent on the gallery container (Avito galleries natively respond to keyboard arrow navigation).

### Option C: Direct Extraction from Window State / Next.js Hydration Script
Instead of relying on DOM clicking:
1. Inspect `<script id="__NEXT_DATA__">` or script tags containing `item` / `gallery` objects directly.
2. In Stage 13A, `extractGalleryFromInitialData` was written, but often `pageInitialData` is undefined because Chrome Extension Content Scripts run in an isolated world and cannot access `window.__initialData__` directly without script injection into the main world (`world: "MAIN"`).
3. Using `chrome.scripting.executeScript({ world: "MAIN", func: ... })` or a DOM bridge script to extract the complete image URL array from the page's React state guarantees 100% of photos without any DOM clicking.

---

## 5. Specific Questions for the Supervisor

1. **Main World Access vs DOM Traversal:**
   Can we inject a small probe script into the `MAIN` world (via `script` tag injection in `content.js`) to extract the exact array of image URLs from `window.__initialData__` or React internal fibers? This would bypass all DOM carousel clicking, lazy loading, and React event delegation issues.
2. **Keyboard Navigation Fallback:**
   Should we add `KeyboardEvent('keydown', { key: 'ArrowRight', keyCode: 39 })` on the gallery root as a secondary traversal mechanism when `nextBtn` clicks fail to advance slides?
3. **Popup UX & Gating:**
   Should the extension popup block the "Доимпортировать" button with a loading state until the deep scan has either reached $N$ photos or timed out, preventing premature transmission of 1-photo payloads?
4. **Live DOM Sample:**
   Can the supervisor provide a saved HTML snapshot or DevTools inspection of the gallery container from the specific Avito listing URL currently being tested?

---

*Report prepared for supervisor review. Extension codebase remains clean on `main` at `cd360f5`.*
