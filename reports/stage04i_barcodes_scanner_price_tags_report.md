# Stage 04I Barcodes, Scanner Search and 58×40 Price Tags Report

## STATUS
READY_FOR_OWNER_CHECK

## OWNER_REQUIREMENTS
1. Each product can have a unique barcode.
2. Older products without barcode can have barcodes generated manually or via bulk missing barcode generation.
3. Product search works by barcode, SKU, ID, or title.
4. Sales/Cart scanner input field auto-adds scanned product to cart, clears field, and returns focus.
5. Clear Russian error messages when product is unknown or unavailable (sold, reserved, quantity=0).
6. 58×40 mm price tag action button on each product.
7. Price tag displays title, price, barcode SVG, digits, warranty, condition (Б/У).
8. Manual print price adjustment in price tag preview does NOT alter `Product.price` in Core DB.

## ARCHITECTURE
- Core API + DB manages `Product.barcode`, lookup, generation, audit events.
- `inventory-sales-module` interacts strictly via HTTP Core API without direct DB access.

## BARCODE_FORMAT
- Format: 12-digit numeric code with prefix `200` (`200000000001` - `200999999999`).
- Symbology: Code128 rendered as crisp vector SVG.

## DATA_MODEL
- Added `barcode` column (`VARCHAR`, `unique=True`, `index=True`, `nullable=True`) to `Product` model and `products` table in Core DB.
- Idempotent migration creates unique index `ix_products_barcode`.

## API
- `GET /api/products/by-barcode/{barcode}`
- `POST /api/products/{product_id}/barcode/generate`
- `POST /api/products/barcodes/generate-missing`
- `GET /api/products?q=...` (searches barcode/sku/id/title with exact barcode prioritization)

## SCANNER_FLOW
- Input field `id="scanner-input"` with `autofocus` on `/cart`.
- Enter key submits `POST /cart/scan`.
- Valid item added to cart; field cleared; focus restored.
- Russian error banners rendered on failure.

## CART_BEHAVIOR
- Available item (`in_stock`/`reserved`, `quantity > 0`) added to cart (increments quantity if already present).
- Unavailable item (`sold`, `draft`, `quantity <= 0`) blocked with descriptive Russian error.

## PRICE_TAG_58X40
- Route: `GET /products/{product_id}/price-tag/58x40`
- CSS `@page { size: 58mm 40mm; margin: 0; }`
- Pre-print control form allows editing `print_price`, `warranty_text`, `condition_text`.
- Verified that changing `print_price` does NOT mutate `Product.price` in Core DB.

## TESTS
- **Core pytest:** `110 passed` (including `test_product_barcodes.py`, `test_product_search.py`)
- **Inventory pytest:** `85 passed` (including `test_barcode_scanner_ui.py`, `test_price_tag_58x40.py`, `test_price_tag_print_action.py`)
- **Avito pytest:** `12 passed`

## RUNTIME_SMOKE
- Single barcode generation: PASS
- Bulk missing barcode generation: PASS
- Scanner cart lookup and add: PASS
- Unknown barcode 404 & Russian error: PASS
- Sold product block: PASS
- 58x40 mm price tag preview rendering: PASS
- Core `Product.price` immutability check: PASS

## PRINT_CHECK
- `@page { size: 58mm 40mm; margin: 0; }`
- Single page layout without clipping or second empty page.
- Print control buttons hidden in `@media print`.

## SAFETY_SCAN
- DB/Cache/Temp files: PASSED (0 matches)
- Direct DB access in inventory-sales-module: PASSED
- Destructive SQL statements: PASSED
- Sensitive keys/env files: PASSED

## FILES_CHANGED
- `core/app/models.py`
- `core/app/schemas.py`
- `core/app/main.py`
- `core/app/routers/products.py`
- `core/app/services/barcodes.py`
- `core/tests/test_product_barcodes.py`
- `core/tests/test_product_search.py`
- `core/requirements.txt`
- `inventory-sales-module/app/core_client.py`
- `inventory-sales-module/app/barcode_utils.py`
- `inventory-sales-module/app/routers/products.py`
- `inventory-sales-module/app/routers/cart.py`
- `inventory-sales-module/app/templates/cart.html`
- `inventory-sales-module/app/templates/products.html`
- `inventory-sales-module/app/templates/product_detail.html`
- `inventory-sales-module/app/templates/price_tag_preview.html`
- `inventory-sales-module/tests/test_barcode_scanner_ui.py`
- `inventory-sales-module/tests/test_price_tag_58x40.py`
- `inventory-sales-module/tests/test_price_tag_print_action.py`
- `inventory-sales-module/requirements.txt`
- `docs/stage04i_barcodes_scanner_price_tags.md`
- `reports/stage04i_barcodes_scanner_price_tags_report.md`
- `logs/2026-07-23.md`
- `.agents/received_prompts/TECHNOREBOOT_STAGE04I_BARCODES_SCANNER_PRICE_TAGS_PROMPT.md`

## COMMIT
- Branch: `main`
- Commit Message: `"Implement product barcodes scanner flow and 58x40 price tags"`

## PUSH
- Destination: `origin/main`

## FINAL_GIT_STATUS
- Clean working tree

## OWNER_CHECK_GUIDE
1. Open Products list: `http://localhost:8030/products`.
2. Click "Сгенерировать отсутствующие штрихкоды" button at top.
3. Open product details `/products/{id}` -> verify barcode value and SVG display.
4. Click "Ценник 58×40" -> test changing print price in preview form and click "Печать". Verify Core `Product.price` remains unchanged.
5. Open Cart `/cart` -> scan or enter barcode in "Сканировать штрихкод" input field -> verify product is added and field auto-focuses.
6. Enter invalid barcode or barcode for a sold item -> verify Russian error banner.

## FINAL_STATUS
TECHNOREBOOT_STAGE04I_BARCODES_SCANNER_PRICE_TAGS_READY_FOR_OWNER_CHECK
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
