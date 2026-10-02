# Stage 04C-R2: Canonical Receipt Single Source & Clean Build Audit Report

## 1. Executive Summary

Stage 04C-R2 architecturally unifies the receipt presentation layer across the Technoreboot platform, resolves duplicate business-text literals, establishes **Option A** (PDF as the sole canonical printable layout), guarantees clean Docker container reproducibility from repository requirements without runtime mutations, removes redundant dependencies and font assets from `admin-shell`, and establishes automated parity verification.

## 2. Receipt Elements Audit Table

| Receipt element | HTML source | PDF source | Same canonical value source? | Single canonical resolution in R2 |
|---|---|---|---|---|
| Organization name | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Previously duplicate fallback strings | Unified `ReceiptDocumentData.organization_name` via `core.app.services.receipt_presentation` |
| INN | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Previously duplicate fallback strings | Unified `ReceiptDocumentData.inn` |
| Address | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Previously duplicate fallback strings | Unified `ReceiptDocumentData.address` |
| Phone | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Previously duplicate fallback strings | Unified `ReceiptDocumentData.phone` |
| Receipt number/date | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Formatted independently | Unified `ReceiptDocumentData.receipt_number`, `receipt_title`, `date_formatted` |
| Cashier | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Duplicated fallback literal `"Продавец"` | Unified `ReceiptDocumentData.cashier_name` |
| Item title | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Slight title fallback discrepancy | Unified `ReceiptDocumentItem.title` with standardized fallback |
| Quantity | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Evaluated independently | Unified `ReceiptDocumentItem.quantity` |
| Unit price | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Formatted independently | Unified `ReceiptDocumentItem.price_formatted` (`{val:.2f}`) |
| Line total | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Calculated in Jinja vs Python | Unified `ReceiptDocumentItem.line_total_formatted` |
| Grand total | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Formatted independently | Unified `ReceiptDocumentData.total_amount_formatted` |
| Payment method | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Two distinct dictionaries (`PAYMENT_METHODS` vs `PAYMENT_METHODS_LABELS`) | Unified `ReceiptDocumentData.payment_method_label` mapped canonically |
| Warranty term | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Template logic vs Python fallback | Unified `ReceiptDocumentData.warranty_days` |
| Warranty/return text | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Template stripped line 0 (`split('\n')[1:]`), PDF did not | Unified `ReceiptDocumentData.warranty_headline`, `warranty_body_text`, `warranty_full_text` |
| Buyer acknowledgement | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Hardcoded separately in HTML and Python | Unified `ReceiptDocumentData.buyer_acknowledgement_prompt` |
| Seller signature label | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Hardcoded separately | Unified `ReceiptDocumentData.seller_signature_title`, `seller_signature_actor` |
| Buyer signature label | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Hardcoded separately | Unified `ReceiptDocumentData.buyer_signature_title`, `buyer_signature_actor` |
| Status banners | `sale_receipt_preview.html` | `receipt_pdf_service.py` | Duplicated banner strings in HTML & Python | Unified `ReceiptDocumentData.status_banner_text`, `status_banner_bg_color`, `revision_notice` |
| Desktop print action | `sale_receipt_preview.html` | N/A | Previously invoked raw `window.print()` | Bound to `/sales/{sale_id}/receipt/print` streaming the canonical PDF |
| Android print endpoint | N/A | `/api/sales/{sale_id}/receipt/print` | Core PDF endpoint | Core `/api/sales/{sale_id}/receipt/print` generates identical PDF via `ReceiptDocumentData` |

## 3. Architecture & Print Layout Ownership (Option A)

- **Chosen Architecture:** **Option A: PDF is the canonical printable artifact.**
- **Rationale:** ReportLab PDF generation has already been tested, validated, and approved with physical PASS on target hardware by the OWNER. Option B (generating PDF from browser HTML) would require installing heavy headless browser or HTML-to-PDF rendering engines (such as WeasyPrint with cairo/pango or headless Chrome), which would alter the approved printed layout and increase image size unnecessarily.
- **Workflow:**
  1. Desktop receipt preview (`GET /sales/{sale_id}/receipt`) renders HTML purely for operator inspection on screen, sourcing all text and figures from `ReceiptDocumentData`.
  2. Desktop receipt print action opens `/sales/{sale_id}/receipt/print`, which proxies Core's `/api/sales/{sale_id}/receipt/print`.
  3. Android print action calls `/api/mobile/sales/{sale_id}/receipt/print`, which proxies Core's `/api/sales/{sale_id}/receipt/print`.
  4. Both desktop and mobile produce the exact same byte-for-byte ReportLab PDF with zero layout drift.

## 4. 35-Point Verification Matrix

1. **FINAL_STATUS:** PASS
2. **Baseline Stage04C commit:** `aa788f4e64e5db779b151940f5f0dfd1b5743892`
3. **Final R2 commit:** `929832df72d8016f7e5fdaf0fb7ff510a3111880`
4. **Canonical receipt content source:** `core/app/services/receipt_presentation.py` (`ReceiptDocumentData`, `build_receipt_document_data`)
5. **Canonical printable layout owner:** `core/app/services/receipt_pdf_service.py` (`generate_sale_receipt_pdf`)
6. **Desktop preview source:** `inventory-sales-module/app/templates/sale_receipt_preview.html` consuming `ReceiptDocumentData`
7. **Desktop print source:** `GET /sales/{sale_id}/receipt/print` -> Core `GET /api/sales/{sale_id}/receipt/print` (canonical PDF)
8. **Android print source:** `GET /api/mobile/sales/{sale_id}/receipt/print` -> Core `GET /api/sales/{sale_id}/receipt/print` (canonical PDF)
9. **Duplicate business-text literals removed:** YES (all fallbacks, signature labels, status banners, and warranty normalization centralized in `receipt_presentation.py`)
10. **Receipt parity test result:** PASS (`core/tests/test_stage04c_r2_receipt_parity.py` - 8/8 tests passed)
11. **Long-title/multi-item parity result:** PASS (`test_long_cyrillic_and_multi_item_parity` passed)
12. **Status-banner parity result:** PASS (`test_canceled_status_banner_parity`, `test_superseded_status_banner_parity`, `test_reissued_status_banner_parity`, `test_revision_notice_parity` passed)
13. **Clean core image rebuild result:** PASS (`docker compose build core` completed with exit code 0)
14. **Clean admin-shell image rebuild result:** PASS (`docker compose build admin-shell` completed with exit code 0)
15. **Runtime pip install required:** NO (strictly prohibited and verified)
16. **ReportLab dependency location:** `core/requirements.txt` (`reportlab>=4.0.0`, `pillow>=10.0.0`, `charset-normalizer>=3.0.0`)
17. **Font asset location:** `core/app/static/fonts/` (`DejaVuSans.ttf`, `DejaVuSans-Bold.ttf`)
18. **Unnecessary duplicated assets removed:** YES (`reportlab` removed from `admin-shell/requirements.txt`, TTF font files removed from `admin-shell/app/static/fonts/`)
19. **Core print endpoint result:** PASS (`GET http://localhost:8000/api/sales/12/receipt/print` -> 200 OK, `application/pdf`, 50460 bytes, valid Cyrillic and ₽)
20. **Mobile print facade result:** PASS (`GET /api/mobile/sales/12/receipt/print` -> 200 OK, 8/8 mobile proxy tests passed)
21. **Desktop print regression:** PASS (18/18 inventory sales module tests passed, including `test_sale_receipt_page`, `test_receipt_print_action_preview`, `test_receipt_warranty_and_org_text`, `test_sale_corrections_ui`)
22. **Android tests:** PASS (`.\gradlew.bat testDebugUnitTest` -> BUILD SUCCESSFUL in 14s)
23. **assembleDebug:** PASS (`.\gradlew.bat assembleDebug` -> BUILD SUCCESSFUL in 13s)
24. **lintDebug:** PASS (`.\gradlew.bat lintDebug` -> BUILD SUCCESSFUL in 58s, 0 errors)
25. **Sales count before/after:** 14 / 14 (strictly unchanged)
26. **Stock movements before/after:** 13 / 13 (strictly unchanged)
27. **Product stock before/after:** Product 229: 65 / 65 (strictly unchanged)
28. **DB quick_check:** `ok`
29. **DB foreign_key_check:** `[]`
30. **OWNER physical PASS reused/repeated:** REUSED (printed layout and text remain materially equivalent; Section 10 rule satisfied without requesting redundant owner hardware action)
31. **Files changed:** 13 files:
    - `admin-shell/app/static/fonts/DejaVuSans-Bold.ttf` (deleted)
    - `admin-shell/app/static/fonts/DejaVuSans.ttf` (deleted)
    - `admin-shell/requirements.txt`
    - `core/app/routers/sales.py`
    - `core/app/schemas.py`
    - `core/app/services/receipt_pdf_service.py`
    - `core/app/services/receipt_presentation.py` (new)
    - `core/requirements.txt`
    - `core/tests/test_stage04c_r2_receipt_parity.py` (new)
    - `inventory-sales-module/app/core_client.py`
    - `inventory-sales-module/app/routers/sales.py`
    - `inventory-sales-module/app/services/receipt_presentation.py` (new)
    - `inventory-sales-module/app/templates/sale_receipt_preview.html`
32. **git status:** Clean working tree (only pre-existing untracked reports and prompt copies)
33. **Production/VDS touched:** NO (strictly prohibited, local/dev environment only)
34. **Stage04C accepted:** YES
35. **Ready for Stage04D:** YES
