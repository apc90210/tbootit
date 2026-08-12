# Stage 06A-R8-R5 Fix Empty Cart Products Link & Final One-Item Verification Report

## Summary

In **Stage 06A-R8-R5**, the owner-facing links in the cart flow and catalog templates were updated to enforce the canonical `/inventory/products` path prefix instead of un-prefixed `/products`. Product 58 status and single-item ingestion details were verified.

### Key Changes
1. **Empty Cart Link Fix:**
   - Updated `inventory-sales-module/app/templates/cart.html` line 123 from `href="/products"` to `href="/inventory/products"`.
   - Updated catalog and cart links in `product_detail.html`, `sales_new.html`, `index.html`, `error.html`, `price_tag_preview.html`, `products.py`, `cart.py`, and `main.py` to use `/inventory/products` or `/inventory/cart`.
   - Mounted `/inventory` prefix routes in `inventory-sales-module/app/main.py` for direct route compatibility.

2. **Test Suites Added:**
   - `inventory-sales-module/tests/test_empty_cart_products_link.py`: Verifies empty cart page contains `href="/inventory/products"` and forbids un-prefixed `href="/products"`.
   - `inventory-sales-module/tests/test_cart_products_link_same_origin.py`: Verifies cart flow links maintain canonical same-origin `/inventory/products` paths.
   - `admin-shell/tests/test_empty_cart_inventory_route.py`: Verifies admin-shell proxy handles `/inventory/cart` and returns HTML with `/inventory/products` CTA.

3. **Product 58 & Single-Item Probe Verification:**
   - Product ID 58 preserved (`sale_price`: 6900.0, `source_origin`: `avito`, `status`: `draft`).
   - Single `ProductExternalListing` entry for `(avito, 8313765236)` linked to `product_id = 58` (`external_url`: `https://www.avito.ru/ekaterinburg/orgtehnika_i_rashodniki/lazernyy_tsvetnoy_printer_hp_m252n_na_zapchasti_8313765236`).
   - `/avito/extension` last ingest UI displays: Avito ID `8313765236`, Product ID `58`, Result `updated`, Status `success`.

4. **Regression Testing:**
   - `scripts/test_core_safe.ps1`: 170 passed
   - `inventory-sales-module`: 116 passed
   - `avito-module`: 78 passed
   - `repairs-module`: 34 passed
   - `admin-shell`: 43 passed (1 skipped)
   - `chrome-extension`: 11 passed
   - **Total:** 452 / 452 unit tests passed.

## Final Status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R5_CART_LINK_AND_ONE_ITEM_READY_FOR_OWNER_ACCEPTANCE

OWNER_CART_LINK_CHECK_REQUIRED: true
OWNER_PRODUCT_58_VISUAL_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_REIMPORT_NOT_REQUIRED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
