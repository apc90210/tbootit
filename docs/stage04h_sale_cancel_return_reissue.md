# Stage 04H — Sale Cancellation, Stock Return and Reissue Flow Documentation

## Overview
This document describes the architectural design and functional implementation of Stage 04H in project "Technoreboot": Sale Cancellation, Stock Return, and Reissue Flow.

---

## 1. Sale Status Lifecycle

Each sale (`Sale`) possesses one of the following statuses:

1. **`completed`**: Standard active completed sale. Included in revenue reports.
2. **`canceled`**: Canceled sale. Products are returned to inventory stock atomically. Excluded from revenue and money summary reports.
3. **`superseded`**: Original canceled sale that has been replaced by a new reissued sale. Excluded from revenue and money summary reports. Links to the replacement sale via `superseded_by_sale_id` (`replaced_by_sale_id`).
4. **`reissued`**: New sale created from a canceled sale. Included in revenue reports as an active valid sale. Links to the original sale via `source_sale_id` (`original_sale_id`).

---

## 2. Transactional Cancel Flow (`POST /api/sales/{sale_id}/cancel`)

### Operations:
1. Validate sale existence and current status. If status is already `canceled` or `superseded`, return `409 Conflict`.
2. Update sale status to `canceled`, record `cancelled_at = UTC NOW`, `cancel_reason`, and `canceled_by`.
3. For each `SaleItem` in the sale:
   - Increment `db_product.quantity += item.quantity`.
   - If `db_product.status == "sold"` and `db_product.quantity > 0`, restore `db_product.status = "in_stock"`.
   - Record `StockMovement` (type `sale_cancel`).
   - Record product event (`sale_canceled`).
4. Record audit event (`log_audit`).
5. Commit transaction atomically. If any error occurs, perform full rollback.

---

## 3. Transactional Reissue Flow (`POST /api/sales/{sale_id}/reissue`)

### Operations:
1. Validate original sale `sale_id`: must be in status `canceled`. If already `superseded`, return `409 Conflict`. If `completed`, return `400 Bad Request`.
2. Validate available stock for new sale items.
3. Create new sale record:
   - `status = "reissued"`
   - `source_sale_id = sale_id`
   - `reissued_at = UTC NOW`
   - `total_amount`, `payment_method`, `items`.
4. Update old sale:
   - `status = "superseded"`
   - `superseded_by_sale_id = new_sale.id`.
5. Deduct inventory stock for new sale items:
   - Decrement `db_product.quantity`.
   - If `quantity == 0`, set `db_product.status = "sold"`.
   - Record stock movements (`sale_reissue_deduct`) and product events (`sale_reissue_deduct`).
6. Record audit log events for old (`superseded`) and new (`reissued`) sales.
7. Commit transaction atomically.

---

## 4. Reports Integration

All sales report endpoints (`GET /api/reports/sales`) filter sales query:
- Includes: `status == "completed"` or `status == "reissued"` or `status IS NULL`.
- Excludes: `status == "canceled"` or `status == "superseded"`.
- Results: Canceled and superseded sales do not affect `total_amount`, `sales_count`, `items_count`, `payment_breakdown`, or `money_summary`.

---

## 5. UI Integration (inventory-sales-module)

- **Sales List (`/sales`)**: Provides status tabs (`Все`, `Завершённые`, `Отменённые`, `Заменённые`, `Повторно оформленные`) and color-coded status badges.
- **Sale Details (`/sales/{id}`)**: Shows status banners, cancellation metadata (date, reason, user), links between superseded and reissued sales, and action buttons ("Отменить продажу", "Оформить повторно").
- **Receipt Preview (`/sales/{id}/receipt`)**: For `reissued` sales, displays reissue banner referencing source sale. For `canceled`/`superseded` sales, displays historical watermark notice.
