# Stage 04I Barcodes, Scanner Search and 58×40 Price Tags Documentation

## Overview
This document describes the design and user flows implemented in Stage 04I for project "Technoreboot": Product Unique Barcodes, Scanner Cart Lookup/Addition, Bulk Barcode Generation, and 58×40 mm Price Tag Printing.

---

## 1. Data Model & Barcode Format
- **Field:** `Product.barcode` (`VARCHAR`, `unique=True`, `index=True`, `nullable=True`).
- **Format:** Internal 12-digit numeric barcode starting with prefix `200` (e.g. `200000000001` to `200999999999`).
- **Uniqueness:** Checked against Core database prior to assignment.
- **Rendering:** Code128 format encoded into crisp vector SVG (`render_barcode_svg`), ensuring zero pixelation on thermal printers.

---

## 2. Core API Endpoints
1. `GET /api/products/by-barcode/{barcode}`
   - Exact lookup by barcode, SKU, or numeric product ID.
   - Returns product data or 404 with Russian error message.
2. `POST /api/products/{product_id}/barcode/generate`
   - Generates unique barcode for single product if absent (`generated=True`). Returns existing barcode if already set (`generated=False`).
   - Logs audit event `product.barcode_generated`.
3. `POST /api/products/barcodes/generate-missing`
   - Bulk generates barcodes for all items where `barcode` is null/empty.
   - Never overwrites existing barcodes.
   - Logs audit event `product.barcode_bulk_generated`.
4. `GET /api/products?q=...`
   - Searches by `barcode`, `sku`, `id` (if digit), `title`, `brand`, `model`, `serial_number`.
   - Exact barcode match is sorted first.

---

## 3. Scanner Flow in Cart (`/cart`)
- Dedicated scanner form: `Сканировать штрихкод` with input `autofocus` (`id="scanner-input"`).
- Submitting scanner input (via barcode scanner Enter key or manual submission):
  - Performs lookup via Core API.
  - If found and available (`in_stock` / `reserved`, `storage_location == 'store'`, `quantity > 0`): adds item to cart and auto-focuses input field for next scan.
  - If item unavailable (`sold`, `draft`, `quantity <= 0`): displays clear Russian error message (e.g., *"Товар ... найден, но сейчас недоступен для продажи (статус: Продан, остаток: 0 шт.)"*).
  - If item not found: displays Russian error message (e.g., *"Товар со штрихкодом ... не найден."*).

---

## 4. Price Tag 58×40 mm Printing (`GET /products/{id}/price-tag/58x40`)
- **Dimensions:** Strictly 58 mm × 40 mm (`@page { size: 58mm 40mm; margin: 0; }`).
- **Content:** Shop Name (**ТЕХНОРЕБУТ**), Product Title (2-3 lines clean wrap), Price (**Крупно**), Barcode (SVG vector + digits), Warranty text, Condition (**Б/У**), SKU.
- **Manual Price Override:** User can adjust print price (`print_price`), warranty label, and condition in the pre-print control panel.
- **DB Safety:** Adjusting print price on the label preview ONLY updates the rendered text on the label preview; it **NEVER** mutates `Product.price` in Core DB!
