# Stage 04I-R3 Final Runtime Acceptance Validation Documentation

## Overview
This document records the final live runtime acceptance validation results for Stage 04I-R3 of project "Technoreboot", confirming non-store location scanner blocking, Stage 04G money integrity, report quick filters, strict barcode lookup, status scanner sellability, and price tag price immutability.

---

## 1. Wrong Storage Location Runtime Validation
- **Requirement:** Products with `storage_location != store` (e.g. `warehouse_north`) scanned via `POST /cart/scan` must be blocked from addition to cart with HTTP 200 (not HTTP 500) and display a clear Russian error message.
- **Runtime Proof:**
  - `PRODUCT_ID`: 65
  - `BARCODE`: `200000000110`
  - `STATUS`: `in_stock`
  - `QUANTITY`: 5
  - `STORAGE_LOCATION`: `warehouse_north`
  - `HTTP Status`: 200
  - `UI Error Message`: *"Товар находится в локации 'warehouse_north' и недоступен для продажи из магазина."*
  - `Cart State`: Unchanged (item not added)
  - `Product Quantity in Core`: Unchanged (5)
  - `Product Status in Core`: Unchanged (`in_stock`)

---

## 2. Stage 04G Money & Count Integrity Validation
Full lifecycle sale -> cancel -> reissue test performed against live API:
- `PRODUCT_ID`: 66 (`BARCODE`: `200000000111`, `SALE_PRICE`: 7500.0 ₽)
- **Before Sale:**
  - `REPORT_TOTAL_BEFORE`: 58,750.0 ₽
  - `PAYMENT_BUCKET_BEFORE` (cash): 27,000.0 ₽
  - `SALES_COUNT_BEFORE`: 25
  - `ITEMS_COUNT_BEFORE`: 25
- **After Sale (ID 42):**
  - `REPORT_TOTAL_AFTER_SALE`: 66,250.0 ₽ (+7,500.0 ₽)
  - `PAYMENT_BUCKET_AFTER_SALE` (cash): 34,500.0 ₽ (+7,500.0 ₽)
  - `SALES_COUNT_AFTER_SALE`: 26 (+1)
  - `ITEMS_COUNT_AFTER_SALE`: 26 (+1)
- **After Cancel (Sale 42 canceled):**
  - `SALE_STATUS`: `canceled`
  - `PRODUCT_STATUS`: `in_stock` (quantity restored to 10)
  - `REPORT_TOTAL_AFTER_CANCEL`: 58,750.0 ₽ (Restored to BEFORE)
  - `PAYMENT_BUCKET_AFTER_CANCEL` (cash): 27,000.0 ₽ (Restored to BEFORE)
  - `SALES_COUNT_AFTER_CANCEL`: 25 (Restored to BEFORE)
  - `ITEMS_COUNT_AFTER_CANCEL`: 25 (Restored to BEFORE)
- **After Reissue (Reissued Sale ID 43):**
  - `REISSUED_SALE_ID`: 43
  - `ORIGINAL_STATUS`: `superseded` (excluded from revenue)
  - `REISSUED_STATUS`: `reissued` (included in revenue)
  - `SOURCE_SALE_ID`: 42
  - `SUPERSEDED_BY_SALE_ID`: 43
  - `REPORT_TOTAL_AFTER_REISSUE`: 66,250.0 ₽ (+7,500.0 ₽)
  - `PAYMENT_BUCKET_AFTER_REISSUE` (card): 22,000.0 ₽ (+7,500.0 ₽)
  - `SALES_COUNT_AFTER_REISSUE`: 26 (+1)
  - `ITEMS_COUNT_AFTER_REISSUE`: 26 (+1)

---

## 3. Report Filter Validation
Verified `/reports/sales` across all period filters:
- Default (YTD): HTTP 200, Date Range: Jan 1 to Today
- Today: HTTP 200, Date Range: Today to Today
- Week: HTTP 200, Date Range: Monday to Today
- Month: HTTP 200, Date Range: 1st of Month to Today
- Year: HTTP 200, Date Range: Jan 1 to Today

---

## 4. Test Suite Summary
- **Core API (`core`):** 111 passed
- **Inventory Sales UI (`inventory-sales-module`):** 88 passed
- **Avito Module (`avito-module`):** 12 passed
