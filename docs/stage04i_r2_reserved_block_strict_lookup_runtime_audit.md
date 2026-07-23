# Stage 04I-R2 Reserved Block, Strict Barcode Lookup and Runtime Audit Documentation

## Overview
This document describes the fixes and runtime audit results for Stage 04I-R2 of project "Technoreboot", addressing the rejection of Stage 04I due to reserved item sellability in scanner flow and loose fallback matching in the `by-barcode` endpoint.

---

## 1. Strict Barcode Lookup Endpoint
- **Endpoint:** `GET /api/products/by-barcode/{barcode}`
- **Constraint:** Strictly matches `Product.barcode == barcode`.
- **Exclusions:** Does **NOT** search or match `Product.id`, `Product.sku`, `title`, `brand`, `model`, or `serial_number`.
- **404 Behavior:** Returns HTTP 404 with Russian error detail: `"Товар с таким штрихкодом не найден ({barcode})."` if no exact barcode match exists.
- **Generic Search (`GET /api/products/?q=...`):** Retains full search capability by SKU, ID, title, brand, model, and serial number.

---

## 2. Scanner Sellability Rules (`POST /cart/scan`)
When a barcode is scanned on `/cart`:
- **Allowed:** `status in ['in_stock', 'available']`, `quantity > 0`, store storage location.
- **Blocked Statuses:**
  - `reserved`: `"Товар найден, но зарезервирован и недоступен для продажи."`
  - `sold`: `"Товар уже продан и недоступен для продажи."`
  - `draft`: `"Товар ещё не готов к продаже."`
  - `quantity <= 0`: `"Товар найден, но отсутствует в остатках."`
  - Non-store storage location: `"Товар находится в локации '{location}' и недоступен для продажи из магазина."`
  - Unknown / SKU / ID entered in scanner: `"Товар с таким штрихкодом не найден ({input})."`

---

## 3. Empirical Live Runtime Audit Results

### A. Barcode Counts & Bulk Generation Idempotency
- `TOTAL_PRODUCTS`: 53
- `WITH_BARCODE_BEFORE`: 1
- `WITHOUT_BARCODE_BEFORE`: 52
- `DUPLICATES_BEFORE`: 0
- `SINGLE_GEN`: PRODUCT_ID=1, BARCODE_AFTER=200000000054, GENERATED=True
- `SINGLE_GEN_REPEAT`: BARCODE=200000000054, GENERATED=False
- `BULK_RUN1`: processed=51, generated=51, skipped=0, errors=0
- `WITHOUT_BARCODE_AFTER_FIRST`: 0
- `DUPLICATES_AFTER_FIRST`: 0
- `BULK_RUN2` (Idempotency): generated=0, skipped=0, errors=0
- `DUPLICATES_AFTER_SECOND`: 0

### B. Strict Lookup Live Results
- `/api/products/by-barcode/{barcode}`: HTTP 200 (Exact match)
- `/api/products/by-barcode/{sku}`: HTTP 404
- `/api/products/by-barcode/{id}`: HTTP 404
- `/api/products/?q={sku}`: HTTP 200 (Found)
- `/api/products/?q={id}`: HTTP 200 (Found)

### C. Live Scanner Behavior
- `in_stock` barcode -> Item added to cart (HTTP 200 / 303)
- `reserved` barcode -> Blocked (HTTP 200 with Russian error message)
- `sold` barcode -> Blocked (HTTP 200 with Russian error message)
- `draft` barcode -> Blocked (HTTP 200 with Russian error message)
- `unknown` barcode -> Blocked (HTTP 200 with Russian error message)
- `SKU` in scanner input -> Blocked (HTTP 200 with Russian error message)
- `ID` in scanner input -> Blocked (HTTP 200 with Russian error message)

### D. Price Tag Immutability
- `PRODUCT_ID`: 48
- `PRICE_BEFORE`: 0.0 ₽
- Custom print preview requested with `print_price=99999.0`
- `PRICE_AFTER`: 0.0 ₽ (UNCHANGED in Core DB)

### E. Stage 04H & 04G Regression Audits
- Stage 04H (Sale -> Cancel -> Stock return -> Reissue): PASS
- Stage 04G Quick Filters (`today`, `week`, `month`, `year`): PASS (HTTP 200)

---

## 4. Test Suite Summary
- **Core API (`core`):** 111 passed
- **Inventory Sales UI (`inventory-sales-module`):** 88 passed
- **Avito Module (`avito-module`):** 12 passed
