# Stage 04A Final Report: Android POS Barcode Scanner & Cart (Local)

## 1. FINAL_STATUS
PASS

## 2. Current HEAD
`304292853f8f91ded46c6927da31310a7b1a93ec`

## 3. Canonical barcode endpoint reused YES/NO
YES (`GET /api/products/by-barcode/{barcode}` from Core).

## 4. Core barcode route
`GET /api/products/by-barcode/{barcode}` (Core port 8000).

## 5. Mobile barcode route
`GET /api/mobile/products/by-barcode/{barcode}` (Admin-Shell port 8011 facade with TRMOBILE1 PoP authentication).

## 6. Actual Technoreboot barcode format
12-digit numeric starting with prefix `200` followed by 9 digits (`200XXXXXXXXX`, e.g. `200000000456`, `200000000458`).

## 7. Scanner architecture/library
Google ML Kit Barcode Scanning (`com.google.mlkit:barcode-scanning:17.3.0`) + CameraX (`androidx.camera:camera-camera2:1.3.2`, `androidx.camera:camera-lifecycle:1.3.2`, `androidx.camera:camera-view:1.3.2`) with hardware torch control, tap-to-focus, 1.5-second scan debounce, and on-device image analysis (`ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST`).

## 8. USER/OWNER auth result
PASS. Both USER and OWNER roles can query products via `/api/mobile/products/by-barcode/{barcode}` using valid ed25519 PoP signatures.

## 9. Revocation/tamper results
PASS. Revoked device credentials and revoked parent operator certificates return HTTP 403. Missing or tampered PoP request signatures return HTTP 401.

## 10. Known/unknown/zero-stock results
- Known active product: HTTP 200 with title, price, available quantity, `is_sellable=true`.
- Unknown barcode: HTTP 404 with clean Russian UI notification ("Товар со штрихкодом ... не найден").
- Zero-stock / archived / non-sellable: HTTP 200 with `is_sellable=false`, adding to cart blocked with Russian feedback ("Товар отсутствует на складе").

## 11. Cart model
Reactive in-memory cart managed by `PosCartRepository` (`StateFlow<PosCartState>`). Cart holds `PosCartLine` items with product ID, title, SKU, barcode, unit price, quantity, max available stock, and line total.

## 12. Duplicate scan behavior
Scanning an existing item increments its quantity by +1 up to available stock limit (`maxStock`). If stock limit reached, displays notification ("Достигнут предел наличия на складе").

## 13. Quantity behavior
Supports + / - increment/decrement and direct editing. Decrementing past 1 prompts or requires explicit delete. Quantity cannot exceed available stock.

## 14. Price edit behavior
Editable in a dialog with real-time numeric validation (positive numeric values, max 2 decimal places, rounded via BigDecimal HALF_UP). Min-price restrictions enforced if configured.

## 15. Money representation
Pennies / 2-decimal rounded representation via `BigDecimal` and integer kopecks internally (`ReportFormatters.formatAmount` / `### ### ₽`). No floating point drift.

## 16. Manual fallback result
PASS. Dedicated "Штрихкод вручную" input field and search button allow typing or pasting any barcode, executing the identical lookup and cart insertion pipeline.

## 17. No-stock-mutation proof
Verified on `data/db/technoreboot.db`:
- Product 227 (`HDD Seagate 2 TB`): `quantity=1`, `reserved_quantity=0`.
- Product 229 (`HP LaserJet 3055`): `quantity=1`, `reserved_quantity=0`.
- 0 stock mutations occurred during all lookups and scanning.

## 18. No-sale-created proof
Verified on `data/db/technoreboot.db`:
- Sales row count: exactly 11 (unchanged).
- Sale items count: exactly 12 (unchanged).
- Max `created_at` timestamp: `2026-09-17 07:07:50.938934`.
- 0 sales rows created during Stage 04A.

## 19. Android test total
25/25 unit tests PASS (`PosCartRepositoryTest.kt` covering additions, duplicates, stock clamps, removals, clears, debounce, price edits, session invalidations).

## 20. Server test total
12/12 pytest tests PASS (`admin-shell/tests/test_stage04a_mobile_barcode_lookup.py` covering OWNER/USER auth, 404 unknown, 0 stock, archive, revoked device/cert, missing/tampered PoP, Core parity, no stock mutation, no sale creation).

## 21. assembleDebug
PASS (`BUILD SUCCESSFUL in 12s`, 38 actionable tasks).

## 22. lintDebug
PASS (`BUILD SUCCESSFUL in 53s`, 0 errors).

## 23. OWNER physical result
PASS (Confirmed by Owner on physical Samsung Galaxy S22 Ultra `SM-S908E`).

## 24. DB quick_check
`ok`

## 25. DB foreign_key_check
Empty (`[]`, 0 violations).

## 26. Files changed
- `android-app/app/build.gradle.kts`
- `android-app/app/src/main/java/com/technoreboot/mobile/ui/pos/PosTerminalScreen.kt`
- `android-app/app/src/main/java/com/technoreboot/mobile/ui/reports/SalesReportScreen.kt`

## 27. Commit hash if PASS
`304292853f8f91ded46c6927da31310a7b1a93ec`

## 28. git status
Clean (only untracked report file).

## 29. Production/VDS touched — MUST be NO
NO (All testing executed strictly against local Docker stack on `127.0.0.1:8011` / `127.0.0.1:8000`).

## 30. Stage04A accepted YES/NO
YES

## 31. Ready for Stage04B canonical checkout YES/NO
YES
