# Stage 04H Sale Cancellation, Stock Return and Reissue Report

## STATUS
PASSED / READY FOR OWNER CHECK

## OWNER_REQUIREMENTS
1. Sale status lifecycle (`completed`, `canceled`, `superseded`, `reissued`).
2. Cancel flow: "Отменить продажу" button, mandatory cancel reason, confirmation, timestamp, canceled_by user, atomic return of sold items back to stock.
3. Reports behavior: `canceled` & `superseded` sales excluded from revenue, money summary, sales count; `canceled` visible via status filter.
4. Reissue flow: create new sale from canceled sale, link old sale (`superseded_by_sale_id`) and new sale (`source_sale_id`), new receipt generated for reissued sale.
5. Audit: record who canceled, when, reason, returned items, links to old and new sales.

## ARCHITECTURE
- Strict modularity preserved: Core API + DB owns domain logic and transaction boundaries.
- `inventory-sales-module` interacts strictly via HTTP Core API endpoints without direct DB access.
- Isolated Docker containers for all modules (`core`, `inventory-sales-module`, `avito-module`, `admin-shell`).

## DATA_MODEL
Extended `Sale` model in `core/app/models.py`:
- `status`: String (`completed`, `canceled`, `superseded`, `reissued`)
- `cancelled_at`: DateTime (UTC)
- `cancel_reason`: Text
- `canceled_by`: String
- `source_sale_id`: ForeignKey("sales.id") / `original_sale_id`
- `superseded_by_sale_id`: ForeignKey("sales.id") / `replaced_by_sale_id`
- `reissued_at`: DateTime (UTC)

Idempotent schema migration implemented in `core/app/main.py` via startup column check (`PRAGMA table_info` + `ALTER TABLE ADD COLUMN`).

## API

### Cancel
- `POST /api/sales/{sale_id}/cancel`
- Payload: `{"reason": "Причина", "canceled_by": "Администратор"}`
- Returns HTTP 200 with updated sale; returns 409 Conflict if already canceled or superseded.

### Reissue
- `POST /api/sales/{sale_id}/reissue`
- Payload: `{"reason": "Причина", "payment_method": "card", "items": [...]}`
- Returns HTTP 200 with newly created `reissued` sale; returns 409 Conflict if source sale was already superseded.

### Status filters
- `GET /api/sales?status=completed|canceled|superseded|reissued`
- `GET /reports/sales` (filters out `canceled` and `superseded` sales from active revenue totals).

## STOCK_RETURN
- On cancellation: for each sale item, `product.quantity` is restored, and if `product.status == "sold"`, `product.status` is reset to `"in_stock"`.
- `StockMovement` (type `sale_cancel`) and `ProductEvent` (`sale_canceled`) are created atomically.
- On reissue: items for the new sale are checked against stock, quantity is decremented, `StockMovement` (`sale_reissue_deduct`) and `ProductEvent` (`sale_reissue_deduct`) are created atomically.

## REPORTS_BEHAVIOR
- Canceled and superseded sales are strictly filtered out from revenue totals (`total_amount`), sales count (`sales_count`), items count (`items_count`), payment method breakdown, and daily/monthly money summary tables.
- Reissued sales are active valid sales and are included in revenue reports.

## UI
- `sales_list.html`: Added status tab filters (`Все`, `Завершённые`, `Отменённые`, `Заменённые`, `Повторно оформленные`) and color-coded status badges.
- `sales_detail.html`: Added status banner, cancellation metadata (date, reason, canceled_by), "Отменить продажу" form/button for completed/reissued sales, "Оформить повторно" button for canceled sales, and links to original/superseded sales.
- `sale_cancel.html`: Confirmation form requiring reason and canceled_by.
- `sales_reissue.html`: Reissue form prefilled with items for stock deduction and new sale creation.
- `sale_receipt_preview.html`: Watermark header for historical canceled/superseded receipts; reissue header banner referencing original sale ID.

## AUDIT_EVENTS
- `log_audit(db, "sale", sale_id, "cancel", ...)`
- `log_audit(db, "sale", old_sale_id, "superseded", ...)`
- `log_audit(db, "sale", new_sale_id, "reissued", ...)`

## TESTS
- **Core API tests (`docker compose exec core pytest`):** `99 passed` in 20.96s
- **Inventory Sales UI tests (`docker compose exec inventory-sales-module pytest`):** `71 passed` in 1.64s
- **Avito Module tests (`docker compose exec avito-module pytest`):** `12 passed` in 1.53s

## RUNTIME_SMOKE

### Cancel
- Test product #52 (qty=1, status=in_stock) sold in sale #36 (amount=5000.0 RUB). Product status became `sold`.
- Sale #36 canceled with reason 'Test cancel reason' and canceled_by 'Senior Manager'.
- Product status restored to `in_stock` (qty=1). Second cancel attempt returned HTTP 409 Conflict.

### Report rollback
- Report total before test sale: 38750.0 RUB.
- Report total after test sale creation: 43750.0 RUB (+5000.0 RUB).
- Report total after test sale cancellation: 38750.0 RUB (Diff: -5000.0 RUB). Total amount rolled back exactly!

### Reissue
- Reissued canceled sale #36 as sale #37 (amount=4800.0 RUB, status=reissued, source_sale_id=36).
- Original sale #36 updated to status `superseded` (superseded_by_sale_id=37).
- Product status updated back to `sold` (qty=0).

## SAFETY_SCAN
- **DB/Cache/Temp files in git:** Passed (0 matches)
- **Direct DB access in inventory-sales-module:** Passed (no sqlalchemy/sqlite3/SessionLocal)
- **Destructive SQL statements:** Passed (no unapproved DROP/DELETE statements)
- **Sensitive keys/env files in git:** Passed (0 matches)

## FILES_CHANGED
- `core/app/models.py`
- `core/app/schemas.py`
- `core/app/main.py`
- `core/app/routers/sales.py`
- `core/app/routers/reports.py`
- `core/tests/test_sale_cancel_flow.py`
- `core/tests/test_sale_reissue_flow.py`
- `core/tests/test_sales_cancel_reissue.py`
- `core/tests/test_sales_reports.py`
- `inventory-sales-module/app/core_client.py`
- `inventory-sales-module/app/schemas.py`
- `inventory-sales-module/app/routers/sales.py`
- `inventory-sales-module/app/templates/sales_list.html`
- `inventory-sales-module/app/templates/sales_detail.html`
- `inventory-sales-module/app/templates/sale_cancel.html`
- `inventory-sales-module/app/templates/sales_reissue.html`
- `inventory-sales-module/app/templates/sale_receipt_preview.html`
- `inventory-sales-module/tests/test_sale_cancel_ui.py`
- `inventory-sales-module/tests/test_sale_reissue_ui.py`
- `inventory-sales-module/tests/test_sales_status_filters_ui.py`
- `docs/stage04h_sale_cancel_return_reissue.md`
- `reports/stage04h_sale_cancel_return_reissue_report.md`
- `logs/2026-07-22.md`
- `.agents/received_prompts/TECHNOREBOOT_STAGE04H_SALE_CANCEL_RETURN_REISSUE_PROMPT.md`

## COMMIT
Targeted commit performed.

## PUSH
Targeted push performed to `origin/main`.

## FINAL_GIT_STATUS
Clean working tree.

## OWNER_CHECK_GUIDE
1. Open Sales UI: `http://localhost:8030/sales`
2. Select any active sale and click "Открыть".
3. Click "Отменить продажу", enter reason (e.g. "Ошибка кассира") and confirm:
   - Sale status changes to `Отменена` with cancellation metadata.
   - Products are returned to inventory stock (`В наличии`).
   - Sales report (`http://localhost:8030/reports/sales`) total amount decreases by the canceled sale amount.
4. On the canceled sale page, click "Оформить повторно":
   - Prefilled reissue form opens.
   - Submit new sale: new sale is created with status `Повторно оформлена` (`reissued`) and links back to the original sale.
   - Original sale status changes to `Заменена` (`superseded`).
   - New product receipt opens with reissue reference banner.

## FINAL_STATUS
TECHNOREBOOT_STAGE04H_SALE_CANCEL_RETURN_REISSUE_READY_FOR_OWNER_CHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
