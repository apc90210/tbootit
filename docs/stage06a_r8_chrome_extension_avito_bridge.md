# Stage 06A-R8 Architecture & Extension Package Documentation (v0.1.3)

## Overview
The **Technoreboot Avito Chrome Extension (v0.1.3)** provides a pure Manifest V3 local extension interface. It allows the owner to manually transfer Avito listing metadata from standard desktop Google Chrome into Technoreboot without automation, credentials, or cookies.

## Pairing State Machine & Security Contracts
- **Server Reachable vs. Extension Paired:**
  - `GET /admin-api/avito-extension/status` returns `paired: true` ONLY when the caller provides a valid `X-Extension-Token` header.
  - If no token (or an invalid token) is supplied, `paired` returns `false`.
- **States:**
  - **STATE A (Server Offline):** Displays offline warning. Pairing & Transfer disabled.
  - **STATE B (Server Reachable, Unpaired):** Displays "Сервер доступен", reveals 6-digit numeric input and "Подключить" button. Transfer button is disabled with notice: *"Передача станет доступна после привязки расширения (введите код выше)"*.
  - **STATE C (Token Expired / Revoked):** Detects HTTP 401 or `token_valid: false`, clears invalid token from `chrome.storage.local`, and displays pairing form.
  - **STATE D (Paired & Active):** Displays "Расширение привязано" (green badge). Hides pairing form. Enables transfer button when an Avito listing page is detected.
- **Cache Prevention:** Download endpoint `/avito/extension/download` sends `Cache-Control: no-store, no-cache, must-revalidate` headers.

## Empty Cart Products Link & Same-Origin Navigation (Stage06A-R8-R5)
- All empty-cart and catalog navigation CTAs across `cart.html`, `product_detail.html`, `sales_new.html`, `index.html`, `error.html`, `price_tag_preview.html`, `products.py`, `cart.py`, and `main.py` enforce the canonical `/inventory/products` path.
- Standalone un-prefixed `/products` CTAs are completely removed from owner templates.
- Clicking «Товары» or «Перейти к товарам» in empty cart routes directly to `/inventory/products` and returns HTTP 200 OK on `http://localhost:8011`.

## Product 58 & Single-Item Verification
- **Product ID 58:** Preserved with `sale_price` = 6900.0, `source_origin` = `avito`, and `status` = `draft`.
- **External Listing:** Single `ProductExternalListing` entry for `(avito, 8313765236)` referencing `product_id = 58`.
- **Last Ingest Status:** Verified on `/avito/extension` as `Result: updated`, `Status: success`, Avito ID: `8313765236`, Product ID: `58`.

