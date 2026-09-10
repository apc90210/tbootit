# ТехноРебут — Stage 07C-R1-R3: JSON Create/Open UX & Product List Shortcut

## Overview

Stage 07C-R1-R3 provides two critical Owner-facing UX improvements for the JSON product management workflow:
1. **Direct Product Open from Import Results (Requirement A):** Enables opening a newly created (or updated) product directly in a new browser tab (`target="_blank" rel="noopener noreferrer"`) without leaving `/products/json` and without resetting import outcome status.
2. **Product List Shortcut (Requirement B):** Adds a clearly visible quick-action button `+ Добавить новый товар через JSON` at the top of the main product catalog (`/inventory/products`) adjacent to the existing location controls (*Магазин*, *Мастерская*, *Архив*, *Черновики*).

---

## Architectural Changes & Implementation Details

### 1. Core Service Contract (`core/app/services/product_json_service.py`)
- In `import_canonical_products`, ensured the result dictionaries explicitly return both `product_id` and `id` representing the newly created or updated product integer primary key:
  ```python
  results.append({
      "index": idx,
      "id": product.id,
      "product_id": product.id,
      "sku": product.sku,
      "title": product.title,
      "status": "created",
      "error": None
  })
  ```
- Guaranteed that error and skipped rows without valid product entities do not contain valid positive IDs.

### 2. Admin Shell JSON Import UI (`admin-shell/app/templates/products_json.html`)
- Updated the results table renderer to inspect `r.product_id || r.id`:
  - For rows with `created` or `updated` status and a valid positive ID:
    ```html
    <a href="/inventory/products/${prodId}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm btn-open-product">↗ Открыть товар</a>
    ```
  - The product title in the table is also rendered as a clickable link opening `/inventory/products/${prodId}` in a new tab.
  - For error or skipped rows without a valid ID, a neutral dash (`—`) is rendered, preventing misleading or broken navigation.
- The original `/products/json` tab remains undisturbed with all import summary counters, filter tabs, and results tables intact.

### 3. Main Product List Quick Action (`inventory-sales-module/app/templates/products.html`)
- Positioned the quick-action button inside the primary top controls container (`.d-flex.flex-wrap.align-items-center.gap-2.mb-3`):
  ```html
  <a id="btn-add-product-json" href="/products/json" class="btn btn-success" style="background: #28a745; color: #fff; border: 1px solid #28a745; padding: 10px 20px; font-size: 16px; font-weight: bold; text-decoration: none; margin-left: auto;">+ Добавить новый товар через JSON</a>
  ```
- Preserved all existing controls and filters:
  - `Все` (`/inventory/products`)
  - `Магазин` (`/inventory/products?location=store`)
  - `Мастерская` (`/inventory/products?location=workshop`)
  - `Архив` (`/inventory/products?location=archive`)
  - `Черновики` (`/inventory/products?location=draft`)
- Styled with `margin-left: auto` to ensure prominent visibility at standard desktop and laptop resolutions without horizontal scrolling.

---

## Security and Access Policy

- **Authentication:** Enforced at the Nginx Gateway (`https://127.0.0.1:8443`) via mutual TLS (mTLS).
- **Access Control:**
  - `OWNER` certificate: Full access to `/inventory/products`, `/products/json`, and `/admin-api/products/json/*`.
  - `USER` certificate: Accessible under standard product management permissions.
  - Unauthenticated requests: Gateway immediately returns `403 Forbidden`.
- **New Tab Isolation:** Enforced `rel="noopener noreferrer"` on all `target="_blank"` anchor links to prevent reverse-tabnabbing vulnerabilities.

---

## Verification & Testing Matrix

| Test Suite | Scope | Result |
| :--- | :--- | :--- |
| `admin-shell/tests/test_products_json_ui.py` | Import UX, open button markup, target="_blank", list shortcut | 13 passed |
| `admin-shell` (Full Suite) | Navigation, cert auth, proxying, backup/restore | 82 passed, 1 skipped |
| `core` (Full Suite) | Canonical JSON validation, imports, models, database safety | 228 passed |
| `inventory-sales-module` (Full Suite) | Products routes, quick controls, cart, sales | 125 passed |
| `avito-module` (Full Suite) | Capability model, browser profiles, extension API | 95 passed |
| Live Gateway mTLS | Real Nginx 8443 mTLS, unauth 403, Owner 200, 2-product import, detail verification, exports | PASS |
