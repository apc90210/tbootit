# Stage 11B — Repair Issue -> Sale + Warranty Receipt

## Status Flow
READY_EXISTS: true (repair status 'ready' marks technical readiness only, zero sales created)
ISSUED_EXISTS: true (repair status 'issued' marks final customer handover and financial completion)
READY_CREATES_SALE: false (strict invariant: Готов != продажа; no revenue or sale generated on ready)
ISSUED_REQUIRES_PAYMENT_CONFIRMATION: true (transition to 'issued' requires operator input of final_amount, payment_method, and warranty_days)

## Issue Modal
FINAL_AMOUNT_REQUIRED: true (validated >= 0, prepopulated with estimated_repair_amount)
PAYMENT_METHOD_REQUIRED: true (validated against canonical methods: cash, card, transfer, sbp, legal_entity_account, mixed, other)
WARRANTY_TERM_REQUIRED: true (validated >= 0 days; 0 = без гарантии; supports custom days and quick selection buttons)
CANCEL_LEAVES_READY: true (canceling modal leaves repair in 'ready' status with no sale or payment finalization)

## Linked Sale
SALE_CREATED_ON_ISSUE: true (atomically creates linked Sale on ready -> issued)
EXACTLY_ONE_SALE_PER_REPAIR: true (idempotent; double submit / retry updates existing linked sale without duplicate sales)
REPAIR_SALE_LINK: true (RepairOrder.sale_id foreign key links directly to Sale.id)
SALE_REPAIR_LINK: true (Sale.source_type='repair' and Sale.source_id=repair.id)
SERVICE_NOT_FAKE_INVENTORY_PRODUCT: true (SaleItem.product_id=None; represents repair service work without polluting inventory)
REPORTS_INCLUDE_REPAIR_SALE: true (completed repair sales are included in daily/weekly/monthly revenue and payment breakdowns)

## Audit
ISSUE_ACTOR_RECORDED: true (captured in RepairStatusHistory.changed_by and core audit log)
ISSUE_TIMESTAMP_RECORDED: true (captured in RepairStatusHistory.changed_at)
AMOUNT_RECORDED: true (RepairOrder.final_amount and RepairStatusHistory.comment)
PAYMENT_RECORDED: true (RepairOrder.payment_method and RepairStatusHistory.comment)
WARRANTY_RECORDED: true (RepairOrder.warranty_days and RepairStatusHistory.comment)
SALE_ID_RECORDED: true (RepairOrder.sale_id and RepairStatusHistory.comment)

## Receipt
REPAIR_RECEIPT_ROUTE: GET /repairs/{repair_id}/receipt (renders printable repair warranty receipt / гарантийный талон)
PRINT_BUTTON: true (renders [🖨️ Печать квитанции] with window.print() and dedicated @media print stylesheet)
DEVICE_INFO_PRESENT: true (device_type, brand, model, serial_number, reported_issue, completed work_description)
FINAL_AMOUNT_PRESENT: true (final_amount formatted with currency symbol)
PAYMENT_METHOD_PRESENT: true (human-readable payment method label, e.g. "Безнал / карта", "Наличные")
WARRANTY_PRESENT: true (warranty duration in days, exact expiration date calculated from issue date, warranty terms)

## Stage11A Compatibility
REPAIR_SALE_CORRECTION_SUPPORTED: true (POST /api/sales/{sale_id}/correct allows modifying price, payment method, comment)
FINANCIAL_FIELDS_STAY_CONSISTENT: true (correcting a repair sale transactionally synchronizes RepairOrder.final_amount and payment_method)
AUDIT_PRESERVED: true (appends audit event to RepairStatusHistory documenting revision number, previous amount, new amount, and actor)

## Tests
AUTOMATED_TESTS: 15 Stage 11B tests in tests/test_stage11b_repair_issue.py passed (100%) + 21 Stage 11A tests passed + 5 core repair regression tests passed + 164 targeted baseline tests passed
LOCAL_6_SERVICES_HEALTHY: true (core, inventory-sales-module, repairs-module, admin-shell, gateway, avito-module running)
LOCAL_SMOKE: true (verified issue modal, receipt endpoint, status transition guard against backward transitions, and schema contract)

## Production
PRODUCTION_TOUCHED: false
DEPLOYED_TO_144_31_15_88: false

FINAL_STATUS:
TECHNOREBOOT_STAGE11B_LOCAL_READY_FOR_OWNER_ACCEPTANCE
