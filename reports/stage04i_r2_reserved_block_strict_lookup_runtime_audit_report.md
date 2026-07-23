# Stage 04I-R2 Reserved Block, Strict Barcode Lookup and Runtime Audit Report

## FINAL_STATUS
TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_LOOKUP_RUNTIME_AUDIT_READY_FOR_OWNER_RECHECK

## REJECTION_REASON_AUDIT
1. **Previous Failure:** Stage 04I allowed `reserved` status products to be sold via scanner flow (`available = in_stock/reserved`).
   - **Resolution:** Updated `scan_barcode_to_cart` in `cart.py` to block `reserved` items with explicit Russian error: *"Товар найден, но зарезервирован и недоступен для продажи."*
2. **Previous Failure:** `GET /api/products/by-barcode/{barcode}` searched SKU and numeric product ID as fallback.
   - **Resolution:** Updated `get_product_by_barcode` in `products.py` to strictly query `Product.barcode == barcode` only. SKU/ID lookups return HTTP 404.
3. **Previous Failure:** Missing empirical live runtime audit metrics and single test count consistency.
   - **Resolution:** Executed full live runtime audits against running services and single consistent test counts (Core: 111 passed, Inventory: 88 passed, Avito: 12 passed).

## PROMPT_HASHES
- PROMPT_SEARCH_DONE: true
- PROMPT_USED: TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_BARCODE_RUNTIME_AUDIT_PROMPT.md
- PROMPT_SOURCE: C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_BARCODE_RUNTIME_AUDIT_PROMPT.md
- PROMPT_LOCAL_COPY: C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04I_R2_RESERVED_BLOCK_STRICT_BARCODE_RUNTIME_AUDIT_PROMPT.md
- REPAIR_PROMPT_SHA256: 8DFF97A3C7DB90B869331CCEF152170F5DD15B90127361AEAB745BE13FFFB68A
- STAGE04I_PROMPT_SHA256: FA686ABB5048D78B9BB402FF7BF6D1732CDEF04EEC22B0DB9DEB1FEF64AB0F9D

## COMMIT_32AB7A0_AUDIT
- Stat & Diff audit confirmed that Stage 04H cancel/reissue UI and Stage 04G sales report quick filters remain 100% intact and clean.

## LIVE_BARCODE_RUNTIME_METRICS
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
- `OLD_PRODUCTS_BARCODED`: 51

## LIVE_STRICT_LOOKUP_AUDIT
- `by-barcode/{barcode}`: HTTP 200 (exact match)
- `by-barcode/{sku}`: HTTP 404 (strictly blocked)
- `by-barcode/{id}`: HTTP 404 (strictly blocked)
- `/api/products/?q={sku}`: HTTP 200 (generic search succeeds)
- `/api/products/?q={id}`: HTTP 200 (generic search succeeds)

## LIVE_SCANNER_SELLABILITY_AUDIT
- `in_stock` barcode -> Added to cart (HTTP 200/303)
- `reserved` barcode -> Blocked: *"Товар найден, но зарезервирован и недоступен для продажи."*
- `sold` barcode -> Blocked: *"Товар уже продан и недоступен для продажи."*
- `draft` barcode -> Blocked: *"Товар ещё не готов к продаже."*
- `quantity=0` barcode -> Blocked: *"Товар найден, но отсутствует в остатках."*
- `unknown` barcode -> Blocked: *"Товар с таким штрихкодом не найден (999999999999)."*
- `SKU` input -> Blocked: *"Товар с таким штрихкодом не найден (TEST-NOWTY-4b60aec4)."*
- `ID` input -> Blocked: *"Товар с таким штрихкодом не найден (48)."*

## LIVE_PRICE_TAG_IMMUTABILITY_AUDIT
- `PRODUCT_ID`: 48
- `PRODUCT_PRICE_BEFORE`: 0.0 ₽
- Preview with `print_price=99999.0` rendered correctly on label preview.
- `PRODUCT_PRICE_AFTER`: 0.0 ₽ (Verified unchanged in Core DB)

## LIVE_STAGE04H_REGRESSION_AUDIT
- `PRODUCT_ID`: 60
- `ORIGINAL_SALE_ID`: 38
- `REISSUED_SALE_ID`: 39
- `REPORT_TOTAL_BEFORE`: 0.0 ₽
- `REPORT_TOTAL_AFTER_SALE`: 0.0 ₽
- `REPORT_TOTAL_AFTER_CANCEL`: 0.0 ₽
- `REPORT_TOTAL_AFTER_REISSUE`: 0.0 ₽
- `STOCK_RETURNED_AFTER_CANCEL`: True
- `REISSUE_LINKAGE_OK`: True

## LIVE_STAGE04G_REGRESSION_AUDIT
- `/reports/sales?period=today`: HTTP 200 (OK)
- `/reports/sales?period=week`: HTTP 200 (OK)
- `/reports/sales?period=month`: HTTP 200 (OK)
- `/reports/sales?period=year`: HTTP 200 (OK)

## TEST_RESULTS
- **Core pytest:** 111 passed
- **Inventory pytest:** 88 passed
- **Avito pytest:** 12 passed

## SAFETY_SCANS
- DB/Cache/Temp files: PASSED (0 matches)
- Direct DB access in inventory-sales-module: PASSED
- Destructive SQL statements: PASSED
- Sensitive keys/env files: PASSED

## COMMIT_AND_PUSH
- Branch: `main`
- Target Files Staged & Committed
- Push to `origin/main` Complete
- Working Tree: Clean

OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
