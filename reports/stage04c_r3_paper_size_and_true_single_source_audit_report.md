# Stage 04C-R3: Paper Size & True Single-Source Receipt Audit Report

## 1. Executive Summary

Stage 04C-R3 definitively resolves the two outstanding architectural questions on canonical receipt printing:
1. **Paper Size Confirmation & Drift Prevention:** Proved via physical measurement with `pypdf` on real Core endpoint output that the canonical receipt printable artifact is **A4 (210 × 297 mm / 595.28 × 841.89 pt, portrait)**. Android `ReceiptPrintHelper` strictly configures `PrintAttributes.MediaSize.ISO_A4` and desktop print action proxies this exact same canonical Core PDF. All references to 80mm thermal receipt formats are resolved and automated regression tests in Core (`test_stage04c_r3_page_size.py`) and Android unit tests prevent future silent drift.
2. **True Single-Source Presentation Architecture:** Removed all duplicated literals (organization defaults, cashier labels, warranty legal text, signature headers, status banners) and duplicated derivation logic (`build_receipt_document_data`) from `inventory-sales-module`. `inventory-sales-module/app/services/receipt_presentation.py` is now strictly a thin transport DTO (`ReceiptDocumentData`, `ReceiptDocumentItem`) and consumer adapter (`parse_receipt_document_data`). `inventory-sales-module` desktop preview consumes Core's `GET /api/sales/{sale_id}/receipt/data` endpoint directly, proven by a dedicated contract test (`test_stage04c_r3_receipt_contract.py`).

---

## 2. 37-Point Verification Matrix

| # | Item | Status / Value | Description & Evidence |
|---|---|---|---|
| 1 | **FINAL_STATUS** | **PASS** | All acceptance criteria satisfied, zero regressions, DB untouched. |
| 2 | **Baseline HEAD** | `929832df72d8016f7e5fdaf0fb7ff510a3111880` | Stage 04C-R2 baseline commit. |
| 3 | **Final R3 commit** | `99323d292b962d6b37a9e47683387908a4acfb78` | Commit: `fix: align canonical receipt page size and source`. |
| 4 | **Actual PDF width/height points** | **595.28 pt × 841.89 pt** | Measured via `pypdf.PdfReader` on `GET /api/sales/12/receipt/print`. |
| 5 | **Actual PDF width/height mm** | **210.0 mm × 297.0 mm** | Exact ISO 216 A4 standard dimensions. |
| 6 | **Canonical paper size** | **A4 (ISO 216 / 210 × 297 mm)** | Sole canonical paper size across desktop and mobile. |
| 7 | **Android MediaSize** | `PrintAttributes.MediaSize.ISO_A4` | Declared in `android-app/.../ReceiptPrintHelper.kt`. |
| 8 | **Android scaling/margins** | Native 1:1 stream / printer default margins | `PdfPrintDocumentAdapter` streams canonical A4 PDF to Android Print Framework. |
| 9 | **Desktop print artifact** | Canonical Core ReportLab PDF | `#print-btn` opens `/sales/{sale_id}/receipt/print` proxying Core PDF (50460 bytes). |
| 10 | **A4/80mm contradiction resolved** | **YES** | Proven A4; 80mm was legacy CSS reference, eliminated from receipt models. |
| 11 | **Core canonical presentation owner** | `core/app/services/receipt_presentation.py` | Sole owner of `ReceiptDocumentData` and `build_receipt_document_data()`. |
| 12 | **Inventory presentation role** | Transport DTO / consumer adapter only | Thin Pydantic schemas; zero business derivations or literals. |
| 13 | **Duplicated business mappings removed** | **YES** | Stripped from inventory `receipt_presentation.py`. |
| 14 | **Payment label source** | Core (`core.app.services.receipt_presentation`) | Mapped via Core `PAYMENT_METHODS_LABELS`. |
| 15 | **Warranty text source** | Core (`core.app.services.receipt_presentation`) | Formatted/split into headline & body via Core presentation builder. |
| 16 | **Signature labels source** | Core (`core.app.services.receipt_presentation`) | Centralized in Core document schema. |
| 17 | **Status banner source** | Core (`core.app.services.receipt_presentation`) | Cancelled/superseded/reissued banners generated in Core. |
| 18 | **Receipt title/date source** | Core (`core.app.services.receipt_presentation`) | Formatted in Core (`receipt_title`, `date_formatted`). |
| 19 | **Total formatting source** | Core (`core.app.services.receipt_presentation`) | `total_amount_formatted`, `prepayment_formatted`, `to_pay_formatted`. |
| 20 | **Page-size regression test** | **PASS** | `core/tests/test_stage04c_r3_page_size.py` (3/3 passed). |
| 21 | **Core receipt tests** | **PASS (26 passed)** | `test_stage04c_receipt_printing.py` (15), `test_stage04c_r2_receipt_parity.py` (8), `test_stage04c_r3_page_size.py` (3). |
| 22 | **Inventory receipt tests** | **PASS (19 passed)** | `test_stage04c_r3_receipt_contract.py` (1), `test_receipt_template.py` (1), `test_receipt_print_action.py` (2), `test_receipt_organization_and_warranty_text.py` (3), `test_reissued_status_ui.py` (3), `test_sale_corrections_ui.py` (6), `test_sales_payment_channels_ui.py` (3). |
| 23 | **Admin-shell mobile print tests** | **PASS (8 passed)** | `admin-shell/tests/test_stage04c_mobile_receipt_printing.py`. |
| 24 | **Android tests** | **PASS (117 passed)** | `.\gradlew.bat testDebugUnitTest` -> BUILD SUCCESSFUL in 26s. |
| 25 | **assembleDebug** | **PASS** | `.\gradlew.bat assembleDebug` -> BUILD SUCCESSFUL in 13s. |
| 26 | **lintDebug** | **PASS (0 errors)** | `.\gradlew.bat lintDebug` -> BUILD SUCCESSFUL in 33s. |
| 27 | **Sales count before/after** | **14 / 14** | Strictly unchanged. |
| 28 | **Stock movements before/after** | **13 / 13** | Strictly unchanged. |
| 29 | **Product stock before/after** | **Product 229: 65 / 65** | Strictly unchanged. |
| 30 | **DB quick_check** | `ok` | Passed SQLite quick_check. |
| 31 | **DB foreign_key_check** | `[]` | Zero foreign key violations. |
| 32 | **OWNER physical PASS reused/repeated** | **REUSED** | Physical printed layout and text remain materially equivalent. |
| 33 | **Files changed** | **12 files** | Listed in Section 3 below. |
| 34 | **git status** | Clean working tree | Only pre-existing untracked report files. |
| 35 | **Production/VDS touched** | **NO** | Local/dev only; production untouched. |
| 36 | **Stage04C accepted** | **YES** | All acceptance criteria satisfied. |
| 37 | **Ready for Stage04D** | **YES** | Platform is ready for next milestone. |

---

## 3. Committed Files (Commit `99323d292b962d6b37a9e47683387908a4acfb78`)

1. `android-app/app/src/test/java/com/technoreboot/mobile/ReceiptPrintTest.kt` (added test 16 validating canonical media size)
2. `core/tests/test_stage04c_r3_page_size.py` (new automated page size regression test)
3. `inventory-sales-module/app/routers/sales.py` (sale_receipt consumes Core receipt data endpoint directly)
4. `inventory-sales-module/app/services/receipt_presentation.py` (stripped duplicate business literals and derivation logic)
5. `inventory-sales-module/app/templates/sale_receipt_preview.html` (cleaned window.print comment)
6. `inventory-sales-module/tests/test_stage04c_r3_receipt_contract.py` (new contract test verifying desktop consumes Core DTO directly)
7. `inventory-sales-module/tests/test_receipt_organization_and_warranty_text.py` (aligned with Core DTO)
8. `inventory-sales-module/tests/test_receipt_print_action.py` (aligned with Core DTO)
9. `inventory-sales-module/tests/test_receipt_template.py` (aligned with Core DTO and canonical PDF print route)
10. `inventory-sales-module/tests/test_reissued_status_ui.py` (aligned with Core DTO)
11. `inventory-sales-module/tests/test_sale_corrections_ui.py` (aligned with Core DTO)
12. `inventory-sales-module/tests/test_sales_payment_channels_ui.py` (aligned with Core DTO)
