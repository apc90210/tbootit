# Stage 11A — Sale Corrections + Audit History

## Implementation
SALE_CORRECTION_API: POST /api/sales/{sale_id}/correct implemented in core/app/routers/sales.py, proxied via inventory-sales-module core_client.correct_sale
SALE_REVISION_STORAGE: Model SaleRevision (table `sale_revisions`) storing id, sale_id, revision_no, changed_at, changed_by, comment, before_snapshot, after_snapshot, structured_diff
ACTOR_SOURCE: Captured from request `changed_by` (default: "Администратор" or authenticated identity), stored in `sale_revisions.changed_by` and audit log
ATOMIC_TRANSACTION: Entire correction operation executes inside a single DB transaction (read -> validate -> snapshot -> reconcile stock -> update items -> append revision -> commit). Rollback on any failure.
SCHEMA_GUARD: `scripts/db_schema_contract.py verify` PASSED; compare on data/db/technoreboot.db and core/technoreboot.db PASSED with SAFE status (0 diffs).

## Editable Fields
ITEM_ADD: Supported (searches warehouse stock, verifies sufficiency, deducts quantity)
ITEM_REMOVE: Supported (returns product quantity to warehouse stock, switches status from sold to in_stock if applicable)
ITEM_REPLACE: Supported (restores old item stock, deducts new item stock in one atomic step)
PRICE_AMOUNT_EDIT: Supported (line item prices edited, sale total amount recalculated canonically)
PAYMENT_METHOD_EDIT: Supported (validates against VALID_PAYMENT_METHODS: cash, card, transfer, sbp, legal_entity_account, mixed, other)

## Inventory
REMOVED_ITEM_RESTORES_STOCK: true (creates StockMovement movement_type='sale_correction_return', restores Product.quantity, status='in_stock', storage_location='store')
ADDED_ITEM_DEDUCTS_STOCK: true (creates StockMovement movement_type='sale_correction_deduct', decrements Product.quantity, status='sold' if 0)
REPLACEMENT_RECONCILES_BOTH: true (atomic reconciliation of both old and new product deltas)
ROLLBACK_ON_FAILURE: true (insufficient stock or invalid payload rolls back all DB mutations without creating revisions)

## Audit
EDITED_MARKER_IN_LIST: true (renders `✎ Изменена` / `✎ Изменена ×N` badge with tooltip in sales_list.html)
REVISION_COUNT_VISIBLE: true (displayed in sales list badge and sale detail header)
DETAIL_HISTORY_VISIBLE: true (new "История изменений" card in sales_detail.html rendering all historical revisions)
TIMESTAMP_RECORDED: true (recorded in `sale_revisions.changed_at`)
ACTOR_RECORDED: true (recorded in `sale_revisions.changed_by`)
BEFORE_AFTER_DIFF_VISIBLE: true (human-readable bullets generated and rendered: payment method change, total diff, removed items, added items, price/quantity edits)

## Reports / Receipt
REPORTS_USE_CORRECTED_STATE: true (Today, Week, Year, payment breakdown and money summary use updated sale total and payment method)
NO_DOUBLE_REVENUE: true (sale ID is updated in-place; revisions are not separate sales; zero duplicate revenue)
RECEIPT_USES_CORRECTED_STATE: true (warranty/sale receipt preview uses updated items, price, and prints note: `Продажа скорректирована — ревизия №N`)

## Avito
AUTO_DEACTIVATION_DISABLED: true (OFFICIAL_API_AVAILABLE remains False; no remote automated API calls)
MANUAL_POST_SALE_TASKS_RECONCILED: true (removing a product cancels pending/suggested AvitoPostSaleTask; manual operator flow preserved)

## Tests
AUTOMATED_TESTS: 21 tests passed (15 backend tests in tests/test_stage11a_sale_corrections.py + 6 UI tests in inventory-sales-module/tests/test_sale_corrections_ui.py) + 164 targeted baseline regression tests passed (core: 27, admin-shell: 28, root: 109)
LOCAL_6_SERVICES_HEALTHY: true (technoreboot-core, admin-shell, avito-module, gateway, inventory-sales-module, repairs-module all running)
LOCAL_SMOKE: true (verified core /health, inventory-sales /health, schema verification, and simulated corrections)

## Production
PRODUCTION_TOUCHED: false
DEPLOYED_TO_144_31_15_88: false

FINAL_STATUS:
TECHNOREBOOT_STAGE11A_LOCAL_READY_FOR_OWNER_ACCEPTANCE
