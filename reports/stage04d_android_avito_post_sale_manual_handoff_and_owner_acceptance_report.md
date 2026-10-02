# Stage 04D: Android Avito Post-Sale Manual Handoff & OWNER Acceptance Report

## 1. Executive Summary

Stage 04D (including sub-stages R1, R1B, R1C, R2, R2B, and R2C) implements and validates the complete **manual post-sale handoff to Avito** across the entire TechnoReboot platform stack:
1. **Zero-Side-Effect Canonical Backend Contract:**
   - Extended `sale_items` schema with immutable snapshot fields (`avito_item_id`, `avito_listing_url`) captured deterministically at checkout/reissue time without modifying original product definitions.
   - Core endpoint `GET /api/sales/{sale_id}/avito-handoff` implements a hardened canonical resolution cascade:
     - 1. Immutable sale snapshot (`sale_items.avito_item_id`, `sale_items.avito_listing_url`);
     - 2. Current active/published external listing mapping (`product_external_listings`);
     - 3. SKU pattern convention (`AVITO-<id>`).
   - Removed synthetic URL construction (`https://www.avito.ru/{id}`): URLs are strictly validated safe HTTPS Avito URLs originating from actual listings or snapshots; otherwise `can_open_avito = False` and the article ID is displayed with a neutral informational state.
   - Removed artificial suppressors: action is available regardless of remaining stock (`remaining_stock <= 0` or `> 0`) and regardless of remote status (`active`, `inactive`, etc.).
   - Admin-Shell proxy `GET /api/mobile/sales/{sale_id}/avito-handoff` strictly enforces TRMOBILE1 PoP device certificate authentication and path binding.
   - Zero external Avito API calls, zero database mutations, zero automated UI scraping/actions.
2. **Android UI & Deep Link Integration:**
   - Implemented dedicated handoff domain models and UI card components in `android-app`:
     - Rendered canonical section title **«Авито»**;
     - Rendered subtitle **«Артикул Avito: <id>»**;
     - Rendered actionable button **«Снять с Авито»** which safely fires standard Android `ACTION_VIEW` intent opening the real listing in the Avito app or browser;
     - Rendered neutral fallback text when URL is unavailable;
     - Displayed in both post-sale success dialog (`PosTerminalScreen`) and historical receipt details (`ReceiptDetailScreen`).
   - Complete architectural decoupling: `PosTerminalScreen` retains zero direct vendor keywords, preserving Stage 04B isolation invariants.
3. **Physical Device Deployment & Persistent Local Server Connectivity:**
   - Debug APK (`app-debug.apk`, 38,638,407 bytes, versionCode 6, versionName 1.5.0) compiled cleanly with `--rerun-tasks` and installed on physical Samsung Galaxy S22 Ultra (`RFCT70R6XVP`).
   - Resolved USB tunnel dropouts by introducing a persistent ADB reverse keepalive daemon (`scripts/adb_keepalive.py`), maintaining ports `8011` (Admin-Shell) and `8000` (Core) active over USB.
   - Official pairing code generated for OWNER parent certificate (`466237`).
4. **OWNER Physical Verification & Formal Acceptance:**
   - The OWNER conducted live manual physical testing on the Samsung Galaxy S22 Ultra:
     - Successfully navigated receipts, inspected active Avito items (Sale 63, Sale 53), verified non-Avito clean state (Sale 66), and tapped «Снять с Авито» to open external listings.
     - Formally accepted the stage with physical `PASS`.

---

## 2. 40-Point Verification Matrix

| # | Item | Status / Value | Description & Evidence |
|---|---|---|---|
| 1 | **FINAL_STATUS** | **PASS** | Formally accepted by OWNER after physical on-device testing. |
| 2 | **Baseline HEAD** | `99323d292b962d6b37a9e47683387908a4acfb78` | Stage 04C-R3 baseline commit. |
| 3 | **Implementation Commit (R2)** | `d9545eb7f8e5d7ca27b9bc805ed987c5d4c9b243` | `feat: add receipt-based Avito handoff`. |
| 4 | **Hardening Commit (R2B)** | `050af324a4e80762b5fb37c65b537e3a974da64a` | `fix: harden Avito URL resolver, remove synthetic fallback`. |
| 5 | **Active HEAD** | `050af324a4e80762b5fb37c65b537e3a974da64a` | All Stage 04D code cleanly committed. |
| 6 | **Core endpoint** | `GET /api/sales/{sale_id}/avito-handoff` | Implemented in `core/app/routers/avito_post_sale.py`. |
| 7 | **Admin-shell proxy endpoint** | `GET /api/mobile/sales/{sale_id}/avito-handoff` | Implemented in `admin-shell/app/main.py`. |
| 8 | **Mobile Authentication** | TRMOBILE1 PoP Challenge Protocol | Path-bound PoP ECDSA signature validation enforced. |
| 9 | **Database Schema Migration** | `models.SaleItem.avito_item_id`, `avito_listing_url` | Additive columns migrated idempotently at startup in `core/app/main.py`. |
| 10 | **Checkout Snapshot Capture** | `core/app/services/sale_service.py` | Snapshots captured at checkout and preserved on reissue. |
| 11 | **URL Resolution Cascade** | 1. Snapshot ➔ 2. External Listing ➔ 3. None | Deterministic, proven hierarchy. |
| 12 | **Synthetic URL construction** | **ELIMINATED** | No synthetic `avito.ru/{id}` URLs; strict whitelist validation only. |
| 13 | **Stock Filter Invariant** | Remaining stock > 0 does **NOT** hide action | Retained as informational field `remaining_stock`. |
| 14 | **Remote Status Invariant** | Remote status != active does **NOT** hide action | Retained as informational field `remote_status`. |
| 15 | **Domain Whitelist** | `avito.ru`, `www.avito.ru`, `m.avito.ru` | Non-whitelisted schemes/domains strictly rejected. |
| 16 | **Fallback UI State** | "Ссылка на объявление недоступна" | Non-clickable informational label when URL is absent. |
| 17 | **Android Section Title** | **«Авито»** | Consistent typography per design spec. |
| 18 | **Android Subtitle** | **«Артикул Avito: <id>»** | Displays external article identifier. |
| 19 | **Android Action Button** | **«Снять с Авито»** | Fires standard Android `Intent.ACTION_VIEW`. |
| 20 | **POS Decoupling** | Pure event-driven callback / separate composable | Zero Avito imports or keywords in `PosTerminalScreen.kt`. |
| 21 | **Android Historical Receipts** | Integrated in `ReceiptDetailScreen.kt` | Fetches and renders handoff card for past sales. |
| 22 | **Core Automated Tests** | **PASS (18 passed)** | `core/tests/test_stage04d_avito_handoff.py`. |
| 23 | **Admin-Shell Proxy Tests** | **PASS (9 passed)** | `admin-shell/tests/test_stage04d_mobile_avito_handoff.py`. |
| 24 | **Core Checkout Regressions** | **PASS (27 passed)** | `test_stage04b_canonical_checkout.py` + `test_stage04c_r3_page_size.py`. |
| 25 | **Android Unit Tests** | **PASS (137 passed)** | `.\gradlew.bat testDebugUnitTest` (including 16 Avito tests). |
| 26 | **assembleDebug** | **PASS** | `app-debug.apk` built fresh in 1m 23s (38,638,407 bytes). |
| 27 | **lintDebug** | **PASS (0 errors)** | Zero lint regressions across Android module. |
| 28 | **Target Physical Device** | Samsung Galaxy S22 Ultra (`RFCT70R6XVP`) | Android 14 / OneUI, model `SM-S908E`. |
| 29 | **APK Deployment** | Streamed install via ADB (`install -r`) | Successfully installed and verified via `pm path`. |
| 30 | **App Process PID** | PID `17045` running healthy | Zero crashes, zero unhandled exceptions. |
| 31 | **Reverse Tunnels** | `tcp:8011` & `tcp:8000` | Automated by persistent background daemon `adb_keepalive.py`. |
| 32 | **Device Network Health** | `200 OK` on both ports | Verified via `adb shell curl` from device namespace. |
| 33 | **Pairing Code** | `466237` (OWNER role) | Active with 24h+ TTL. |
| 34 | **Avito API External Mutation** | **ZERO** | Zero outbound requests to Avito servers. |
| 35 | **Database Invariants** | Sales count, stock movements, products unchanged | `PRAGMA quick_check: ok`, `foreign_key_check: []`. |
| 36 | **Unsupported ADB Actions** | **ZERO** | 0 `run-as`, 0 `UIAutomator`, 0 `adb input`, 0 file tampering. |
| 37 | **Production VDS Touched** | **NO** | Production host 144.31.15.88 completely untouched. |
| 38 | **OWNER Physical Verification** | **PASS** | Verified on device by user (audio confirmation). |
| 39 | **Stage 04D Accepted** | **YES** | All acceptance criteria fulfilled. |
| 40 | **Ready for Stage 04E** | **YES** | Ready for next stage. |

---

## 3. Summary of Committed Changes

### Commit `d9545eb7f8e5d7ca27b9bc805ed987c5d4c9b243` ("feat: add receipt-based Avito handoff")
1. `core/app/models.py`: Added additive columns `avito_item_id` and `avito_listing_url` to `SaleItem`.
2. `core/app/schemas.py`: Extended `SaleItemCreate`, `SaleItemUpdate`, `SaleItemResponse`, `CanonicalCheckoutItem`, and `CanonicalCheckoutItemResponse`.
3. `core/app/main.py`: Added startup migration inspecting SQLite `PRAGMA table_info(sale_items)` and performing additive `ALTER TABLE` if missing.
4. `core/app/services/sale_service.py`: Added snapshot capture logic linking active listing items to sale line items during canonical checkout and preservation during reissue.
5. `core/app/routers/sales.py`: Updated reissue flow to carry forward snapshot fields.
6. `core/app/routers/avito_post_sale.py`: Implemented canonical resolution cascade without hard stock/status suppression.
7. `core/tests/test_stage04d_avito_handoff.py`: 14 comprehensive test cases.
8. `admin-shell/app/main.py`: Implemented mobile proxy endpoint `/api/mobile/sales/{sale_id}/avito-handoff` with PoP verification.
9. `admin-shell/tests/test_stage04d_mobile_avito_handoff.py`: 9 PoP mobile security and proxy test cases.
10. `android-app/app/src/main/java/com/technoreboot/mobile/model/AvitoHandoff.kt`: Data models `AvitoHandoffItem`, `AvitoHandoffResponse`.
11. `android-app/app/src/main/java/com/technoreboot/mobile/handoff/AvitoHandoffUi.kt`: Composable UI card.
12. `android-app/app/src/main/java/com/technoreboot/mobile/handoff/PostSaleListingHandoff.kt`: Decoupled handoff controller.
13. `android-app/app/src/main/java/com/technoreboot/mobile/ui/reports/ReceiptDetailScreen.kt`: Historical receipt integration.
14. `android-app/app/src/test/java/com/technoreboot/mobile/AvitoHandoffTest.kt`: 11 Android unit test cases.

### Commit `050af324a4e80762b5fb37c65b537e3a974da64a` ("fix: harden Avito URL resolver, remove synthetic fallback")
1. `core/app/routers/avito_post_sale.py`: Removed synthetic `https://www.avito.ru/{id}` URL synthesis; strictly uses proven URLs or outputs `None` (`can_open_avito = False`).
2. `core/app/services/sale_service.py`: Snapshot capture strictly accepts valid URL sources only.
3. `android-app/app/src/main/java/com/technoreboot/mobile/handoff/AvitoHandoffUi.kt`: Displays neutral informational text when URL is unavailable.
4. `core/tests/test_stage04d_avito_handoff.py`: Added 4 new test cases (18 total).
5. `android-app/app/src/test/java/com/technoreboot/mobile/AvitoHandoffTest.kt`: Added 5 new test cases (16 total).

---

## 4. Physical Testing Evidence (Samsung Galaxy S22 Ultra)

- **Device Serial:** `RFCT70R6XVP` (Model: `SM-S908E`, OneUI / Android 14)
- **APK Package:** `com.technoreboot.mobile.debug` (Version: `1.5.0`, Code: `6`)
- **Tunnels:** `127.0.0.1:8011` (Admin-Shell) & `127.0.0.1:8000` (Core) continuously forwarded over USB.
- **Test Scenarios Verified by Owner:**
  1. **Sale 63 (Single Avito Item, Stock > 0):** Product 275 (*HP LaserJet p1102w*), remaining stock 1. Displayed **«Авито»**, **«Артикул Avito: 8479218283»**, and clickable button **«Снять с Авито»**. Tap successfully triggered the system intent for `https://www.avito.ru/ekaterinburg/orgtehnika_i_rashodniki/lazernyy_printer_hp_laserjet_p1102w._garantiya_8479218283`.
  2. **Sale 53 (Multi-Item Avito):** Products 342 & 346. Displayed two separate cards with independent article identifiers and action buttons.
  3. **Sale 66 (Non-Avito Product):** Product 404. Verified that no Avito cards or false positive buttons were rendered.
- **Physical Verification Outcome:** **PASS**.

---

## 5. Architectural & System Health

1. **Database Safety:**
   - Total sales count: 63 (unchanged)
   - Sale items count: 67 (unchanged)
   - Stock movements: 101 (unchanged)
   - Product stock levels: unchanged
   - `PRAGMA quick_check`: `ok`
   - `PRAGMA foreign_key_check`: `[]`
2. **Production Integrity:**
   - Production server (144.31.15.88) was not contacted or altered.
3. **Execution History:**
   - All steps, checkpoints, and final entries are fully recorded in [`logs/2026-10-02.md`](file:///c:/tbootit/logs/2026-10-02.md).

---

## 6. Conclusion & Recommendation

Stage 04D is **100% complete, fully tested, committed, and formally accepted by the OWNER**.
The system is ready to proceed to the next milestone (**Stage 04E**).
