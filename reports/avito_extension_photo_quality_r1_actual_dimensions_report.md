# Hotfix Report: Avito Extension Photo Quality Selection (R1 Actual Dimensions)

## Executive Summary
This hotfix resolves the issue where Chrome Extension photo extraction intermittently recorded low-resolution thumbnails (e.g., 208x156 or 140x105) or medium-resolution images (640x480) into product cards when higher-resolution variants (1280x960, master CDN assets) were available.

By transitioning from artificial scoring offsets to an objective resolution evidence model based on `pixelArea = width * height`, tie-breakers, and canonical identity grouping (`getCanonicalAvitoImageIdentity`), every physical photo in an Avito listing consistently selects its highest available resolution variant without altering photo order or skipping lower-quality standalone photos.

---

## Key Technical Changes
1. **Content Script (`chrome-extension/technoreboot-avito/content.js`)**:
   - Updated `getImageQualityScore(candidateInput)` to calculate quality based on explicit image resolution (`pixelArea = width * height`), `srcset` descriptors (`1280w`), `La` descriptor tokens (`La4+` -> 1280x960, `La3` -> 640x480, `La2` -> 208x156, `La1` -> 140x105), and master CDN paths (`.img.avito.st/image/1/`).
   - Added tie-breakers (`+ v * 10` for `La` version and `+ 5` for explicit resolution path segments) to ensure explicit high-res master URLs win over intermediate candidates.
   - Updated `extractAllPhotos(jsonLd)` to evaluate candidate variants for each canonical identity group by `getImageQualityScore`, preserving exact gallery order and main photo placement (position 0).

2. **Core Router (`core/app/routers/integrations.py`)**:
   - Replaced artificial `La3` bonus with exact matching objective `_get_avito_quality_score(url)` formula.

3. **Extension Package & Build (`v0.1.12`)**:
   - Bumped extension version to `0.1.12` in `manifest.json`, `content.js`, `build_extension_zip.py`, `admin-shell/app/main.py`, and templates.
   - Rebuilt `technoreboot-avito-extension-0.1.12.zip` and verified package integrity.

---

## Verification & Test Results
- **Chrome Extension Tests**: 36/36 passed (`pytest chrome-extension/technoreboot-avito/tests`).
- **Core Unit Tests**: 185/185 passed (`scripts/test_core_safe.ps1`).
- **Inventory Sales Module**: 119/119 passed.
- **Avito Module**: 83/83 passed.
- **Repairs Module**: 34/34 passed.
- **Admin Shell Tests**: 55/55 passed.
- **Total Repository Test Suite**: **512 / 512 tests passed**.
