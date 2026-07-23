# Stage04I-R3 Final Runtime Acceptance Validation Report

## STATUS
TECHNOREBOOT_STAGE04I_R3_FINAL_RUNTIME_ACCEPTANCE_READY_FOR_OWNER_CHECK

## PREFLIGHT
- Branch: `main`
- Initial HEAD: `f6a7100b54bdfc1e5bd6c2834a88b5f79119bfcc`
- Worktree clean: true
- Prompt: `TECHNOREBOOT_STAGE04I_R3_FINAL_RUNTIME_ACCEPTANCE_VALIDATION_PROMPT.md`
- PROMPT_SHA256: `DE4C5F88E9389F6DBDC69CAB86B5BE951B6F63296B4D7BC28393753C172CFB96`

## WRONG_STORAGE_LOCATION_RUNTIME
- PRODUCT_ID: 65
- BARCODE: 200000000110
- STATUS: in_stock
- QUANTITY: 5
- STORAGE_LOCATION: warehouse_north
- HTTP: 200
- MESSAGE: "Товар находится в локации 'warehouse_north' и недоступен для продажи из магазина."
- CART_CHANGED: no
- PRODUCT_QTY_UNCHANGED: true (5)
- PRODUCT_STATUS_UNCHANGED: true (in_stock)

## STAGE04G_MONEY_INTEGRITY

### Before sale
- PRODUCT_ID: 66
- BARCODE: 200000000111
- SALE_PRICE: 7500.0 ₽
- PAYMENT_METHOD: cash
- REPORT_TOTAL_BEFORE: 58750.0 ₽
- PAYMENT_BUCKET_BEFORE (cash): 27000.0 ₽
- SALES_COUNT_BEFORE: 25
- ITEMS_COUNT_BEFORE: 25

### After sale
- ORIGINAL_SALE_ID: 42
- REPORT_TOTAL_AFTER_SALE: 66250.0 ₽ (+7500.0 ₽)
- PAYMENT_BUCKET_AFTER_SALE (cash): 34500.0 ₽ (+7500.0 ₽)
- SALES_COUNT_AFTER_SALE: 26 (+1)
- ITEMS_COUNT_AFTER_SALE: 26 (+1)

### After cancel
- SALE_STATUS_AFTER_CANCEL: canceled
- PRODUCT_STATUS_AFTER_CANCEL: in_stock (quantity: 10)
- REPORT_TOTAL_AFTER_CANCEL: 58750.0 ₽ (Match to BEFORE)
- PAYMENT_BUCKET_AFTER_CANCEL (cash): 27000.0 ₽ (Match to BEFORE)
- SALES_COUNT_AFTER_CANCEL: 25 (Match to BEFORE)
- ITEMS_COUNT_AFTER_CANCEL: 25 (Match to BEFORE)
- CANCELED_SALE_EXCLUDED_FROM_REVENUE: true

### After reissue
- REISSUED_SALE_ID: 43
- ORIGINAL_STATUS_AFTER_REISSUE: superseded
- REISSUED_STATUS: reissued
- SOURCE_SALE_ID: 42
- SUPERSEDED_BY_SALE_ID: 43
- REPORT_TOTAL_AFTER_REISSUE: 66250.0 ₽ (+7500.0 ₽)
- PAYMENT_BUCKET_AFTER_REISSUE (card): 22000.0 ₽ (+7500.0 ₽)
- SALES_COUNT_AFTER_REISSUE: 26 (+1)
- ITEMS_COUNT_AFTER_REISSUE: 26 (+1)
- SUPERSEDED_SALE_EXCLUDED_FROM_REVENUE: true
- REISSUED_SALE_INCLUDED_EXACTLY_ONCE: true

## REPORT_FILTERS
- Default (YTD): HTTP 200 OK (2026-01-01 to Today)
- Today: HTTP 200 OK (Today to Today)
- Week: HTTP 200 OK (Monday to Today)
- Month: HTTP 200 OK (1st of Month to Today)
- Year: HTTP 200 OK (2026-01-01 to Today)

## BARCODE_RUNTIME
- TOTAL_PRODUCTS: 66
- WITH_BARCODE: 59
- WITHOUT_BARCODE: 7 (Freshly generated test items)
- DUPLICATES: 0
- Strict barcode (/by-barcode/{barcode}): HTTP 200 OK
- SKU rejected (/by-barcode/{sku}): HTTP 404 Not Found
- ID rejected (/by-barcode/{id}): HTTP 404 Not Found

## SCANNER_RUNTIME
- in_stock: HTTP 200, Cart Changed: yes
- reserved: HTTP 200, Message: "Товар найден, но зарезервирован и недоступен для продажи.", Cart Changed: no
- sold: HTTP 200, Message: "Товар уже продан и недоступен для продажи.", Cart Changed: no
- draft: HTTP 200, Message: "Товар ещё не готов к продаже.", Cart Changed: no
- quantity_zero: HTTP 200, Message: "Товар найден, но отсутствует в остатках.", Cart Changed: no
- wrong_location: HTTP 200, Message: "Товар находится в локации 'warehouse_north' и недоступен для продажи из магазина.", Cart Changed: no
- unknown: HTTP 200, Message: "Товар с таким штрихкодом не найден (999999999999).", Cart Changed: no
- SKU: HTTP 200, Message: "Товар с таким штрихкодом не найден (MONEY-99fe8e).", Cart Changed: no
- ID: HTTP 200, Message: "Товар с таким штрихкодом не найден (66).", Cart Changed: no

## PRICE_TAG_RUNTIME
- PRODUCT_ID: 66
- BARCODE: 200000000111
- PRODUCT_PRICE_BEFORE: 7500.0 ₽
- PRINT_PRICE: 88888.0 ₽
- PRODUCT_PRICE_AFTER: 7500.0 ₽
- UNCHANGED: true
- PRINT_CSS (58mm 40mm): true (@page { size: 58mm 40mm; })
- BARCODE_SVG: true (Vector Code128)

## FINAL_TESTS
- Core: 111 passed
- Inventory: 88 passed
- Avito: 12 passed

## SAFETY_SCAN
- DB/Cache/Temp files: PASSED (0 matches)
- Direct DB access in inventory-sales-module: PASSED
- Destructive SQL statements: PASSED
- Sensitive keys/env files: PASSED

## FILES_CHANGED
- `docs/stage04i_r3_final_runtime_acceptance_validation.md`
- `reports/stage04i_r3_final_runtime_acceptance_validation_report.md`
- `logs/2026-07-23.md`
- `.agents/received_prompts/TECHNOREBOOT_STAGE04I_R3_FINAL_RUNTIME_ACCEPTANCE_VALIDATION_PROMPT.md`

## COMMIT
- Message: `"Validate Stage 04I runtime acceptance"`

## PUSH
- Destination: `origin/main`

## FINAL_GIT_STATUS
- Clean working tree

## OWNER_CHECK_GUIDE
1. Open Cart `/cart` (`http://localhost:8030/cart`).
2. Scan barcode for item with non-store location (e.g. `warehouse_north`) -> verify error: *"Товар находится в локации 'warehouse_north' и недоступен для продажи из магазина."*
3. Scan barcode for reserved item -> verify error: *"Товар найден, но зарезервирован и недоступен для продажи."*
4. Create sale -> verify revenue increases by sale amount. Cancel sale -> verify revenue returns to original amount and item quantity is restored. Reissue sale -> verify revenue includes reissued sale exactly once.

## FINAL_STATUS
TECHNOREBOOT_STAGE04I_R3_FINAL_RUNTIME_ACCEPTANCE_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
