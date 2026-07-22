# Stage 04E-R3 Sales Warranty Receipt Print Actions Report

## STATUS
READY_FOR_OWNER_RECHECK

## PROMPT_DISCOVERY
```text
PROMPT_SEARCH_DONE: true
PROMPT_USED: TECHNOREBOOT_STAGE04E_R3_SALES_WARRANTY_RECEIPT_PRINT_ACTIONS_PROMPT.md
PROMPT_SOURCE: C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE04E_R3_SALES_WARRANTY_RECEIPT_PRINT_ACTIONS_PROMPT (1).md
PROMPT_LOCAL_COPY: c:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE04E_R3_SALES_WARRANTY_RECEIPT_PRINT_ACTIONS_PROMPT.md
```

## OWNER_REQUEST
1. Remove standalone "Ценники — скоро" section from main navigation. Price tag printing must be a product-level action button for items in stock.
2. Sales form must allow manual price editing and quantity input.
3. Sales form must include warranty duration in days (default 30) and "Без гарантии" checkbox.
4. Sale details page must provide "Товарный чек" button rendering printable warranty receipt preview.
5. Printable templates (price tag, receipt) must include explicit placeholder disclaimer notes until final owner templates are approved.

## IMPLEMENTED
1. **Navigation Cleanup:** Removed "Ценники — скоро" link from main nav bar in `base.html`. Added "Печать ценника" action buttons to `/products` table rows and `/products/{id}` detail pages for `in_stock` products.
2. **Product Price Tag Preview (`GET /products/{id}/price-tag`):** Renders 58x40mm preview layout with `window.print()` print action button and placeholder note.
3. **Direct Sales Form (`GET /sales/new?product_id=<id>` & `POST /sales/create`):** Created `sales_new.html` template supporting manual price, quantity input, payment method, warranty duration (default 30), and "Без гарантии" toggle.
4. **Warranty Receipt Preview (`GET /sales/{sale_id}/receipt`):** Renders receipt preview displaying warranty duration or no-warranty disclaimer ("Товар продаётся без гарантии..."), print action button, and placeholder note.

## UI_CHANGES
- `base.html`: Navigation bar streamlined (`Главная`, `Товары`, `Продажи`, `Отчёты`, `Корзина`, `Настройки`).
- `products.html`: Added "Продать" and "Печать ценника" buttons for `in_stock` items.
- `product_detail.html`: Added "Продать" and "Печать ценника" buttons for `in_stock` items.
- `sales_new.html`: New template for single product sales with price, quantity, warranty options.
- `price_tag_preview.html`: Added placeholder disclaimer note.
- `sale_receipt_preview.html`: Added placeholder disclaimer note.

## CORE_API_CHANGES
- Utilized Core API `POST /api/sales/` payload fields (`warranty_days`, `warranty_enabled`, `comment`, `items` with `price` and `quantity`). No breaking schema changes required.

## WARRANTY_LOGIC
- Default warranty duration: 30 days.
- When "Без гарантии" checkbox is checked, `warranty_days` is disabled and sent as `None`/`null`, and `warranty_enabled` is set to `False`.
- Receipt template dynamically renders either *"Гарантия: {warranty_days} дней"* or *"Товар продаётся без гарантии, в том состоянии, в котором есть. Покупатель внимательно осмотрел товар при покупке."*.

## QUANTITY_LOGIC
- Quantity field added to sales form (default `1`, minimum `1`).
- Validated against available product quantity prior to submission.

## PRICE_TAG_ACTION
- Available on product list and detail pages for `in_stock` products.
- Disabled/hidden for sold, draft, or out of stock items.

## RECEIPT_PRINT_ACTION
- Available on sale detail page (`/sales/{sale_id}/receipt`).
- Includes printable layout and `@media print` rules.

## TEMPLATES_PLACEHOLDER_NOTE
- Price Tag: *"Предварительная форма ценника. Финальный шаблон будет подключен после утверждения."*
- Receipt: *"Предварительная форма товарного чека. Финальный шаблон будет подключен после утверждения."*

## TESTS
- **Core pytest:** `99 passed`
- **Inventory Sales pytest:** `79 passed` (including `test_sales_warranty_ui.py`, `test_price_tag_print_action.py`, `test_receipt_print_action.py`, `test_navigation_no_price_tags_section.py`)
- **Avito Module pytest:** `12 passed`

## MANUAL_SMOKE
- Open `/products` -> Verify "Ценники — скоро" is absent from navigation.
- Find `in_stock` item -> Click "Печать ценника" -> Preview opens with print button and placeholder note.
- Click "Продать" -> `/sales/new` opens with manual price, quantity=1, warranty=30 days.
- Submit sale with warranty -> Redirects to `/sales/{id}` -> Click "Товарный чек" -> Receipt renders "Гарантия: 30 дней".
- Submit sale with "Без гарантии" -> Click "Товарный чек" -> Receipt renders no warranty disclaimer text.

## SAFETY_SCAN
- DB/Cache/Temp files: PASSED (0 matches)
- Direct DB access in inventory-sales-module: PASSED
- Browser automation / bot code: PASSED
- Sensitive keys/env files: PASSED

## FILES_CHANGED
- `inventory-sales-module/app/routers/sales.py`
- `inventory-sales-module/app/templates/base.html`
- `inventory-sales-module/app/templates/products.html`
- `inventory-sales-module/app/templates/product_detail.html`
- `inventory-sales-module/app/templates/sales_new.html`
- `inventory-sales-module/app/templates/price_tag_preview.html`
- `inventory-sales-module/app/templates/sale_receipt_preview.html`
- `inventory-sales-module/tests/test_sales_warranty_ui.py`
- `inventory-sales-module/tests/test_price_tag_print_action.py`
- `inventory-sales-module/tests/test_receipt_print_action.py`
- `inventory-sales-module/tests/test_navigation_no_price_tags_section.py`
- `docs/stage04e_r3_sales_warranty_receipt_print_actions.md`
- `reports/stage04e_r3_sales_warranty_receipt_print_actions_report.md`
- `logs/2026-07-22.md`
- `.agents/received_prompts/TECHNOREBOOT_STAGE04E_R3_SALES_WARRANTY_RECEIPT_PRINT_ACTIONS_PROMPT.md`

## OWNER_RECHECK_GUIDE
1. Open UI: `http://localhost:8030/products`
2. Verify top navigation menu has no "Ценники — скоро" link.
3. For any item in stock, click "Печать ценника" to open preview.
4. Click "Продать" to open `/sales/new?product_id=<id>`.
5. Test selling with 30 days warranty and with "Без гарантии" checkbox.
6. Open sales receipt for both sales and verify warranty text rendering.

## FINAL_STATUS
TECHNOREBOOT_STAGE04E_R3_SALES_WARRANTY_RECEIPT_PRINT_ACTIONS_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
