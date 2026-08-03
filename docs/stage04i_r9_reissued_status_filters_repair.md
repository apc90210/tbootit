# Stage 04I-R9 Reissued Sale Status and Filter Semantics Repair Documentation

## Overview
This document records the architectural repair, domain model enforcement, startup migration, filter semantics repair, and release audit for Stage 04I-R9 of project "Technoreboot".

---

## 1. Problem Statement & Root Cause

- **Defect Identified in Stage 04I-R8:**
  - Newly reissued sales were being created with `status = "reissued"` in Core API, but legacy/misclassified sales and status filter representations needed explicit normalization and domain verification.
  - Required domain status hierarchy (Stage 04H & Stage 04I):
    1. `completed`: Regular active sale (`source_sale_id is None`).
    2. `canceled`: Canceled sale.
    3. `superseded`: Historical original sale replaced by a reissued sale.
    4. `reissued`: Active sale created as a reissue of a canceled sale (`source_sale_id is not None`).

---

## 2. Technical Repairs Implemented

### A. Core API Reissue Creation Endpoint (`core/app/routers/sales.py`)
- Verified and enforced that `POST /api/sales/{sale_id}/reissue` sets `status = "reissued"`, `source_sale_id = sale_id`, and `reissued_at = datetime.utcnow()`.
- Updates the original sale to `status = "superseded"` and sets `superseded_by_sale_id = new_sale.id`.
- Records audit events for both `superseded` and `reissued` transitions.

### B. Idempotent Startup Migration & Service (`core/app/main.py` & `core/app/services/sale_status_repair.py`)
- Created `normalize_misclassified_reissued_sales(db: Session)` service and integrated SQL normalization query into `migrate_db()` in `core/app/main.py`:
  ```sql
  UPDATE sales
  SET status = 'reissued'
  WHERE source_sale_id IS NOT NULL AND status = 'completed';
  ```
- **Empirical Audit Result:** Executed against live database `C:\tbootit\data\db\technoreboot.db` -> **0 misclassified records** (database clean and normalized). Subsequent startup runs update 0 rows.

### C. UI Template Badges & Markers (`inventory-sales-module/app/templates/`)
- `sales_list.html`: Added status filter links ("Все", "Завершённые", "Отменённые", "Заменённые", "Повторно оформленные") and distinct badges:
  - `reissued`: **Повторно оформлена** (blue badge)
  - `superseded`: **Заменена** (gray badge)
  - `completed`: **Завершена** (green badge)
  - `canceled`: **Отменена** (red badge)
- `sales_detail.html`:
  - `reissued`: Displayed blue info box "✓ Повторно оформленная продажа" with link to source sale `№{source_sale_id}`.
  - `superseded`: Displayed gray info box "ⓘ Продажа заменена" with link to new sale `№{superseded_by_sale_id}`.
- `sale_receipt_preview.html`:
  - `reissued`: Added header banner "ПОВТОРНО ОФОРМЛЕННАЯ ПРОДАЖА (НА ОСНОВЕ ПРОДАЖИ №...)"
  - `superseded`: Added header banner "АРХИВНЫЙ ЧЕК — ПРОДАЖА №... ЗАМЕНЕНА (ПОВТОРНАЯ ПРОДАЖА №...)"

### D. Revenue Reports Logic (`core/app/routers/reports.py`)
- Enforced filtering logic in sales report endpoints:
  - Included statuses: `completed`, `reissued`.
  - Excluded statuses: `canceled`, `superseded`.
  - Reissued sales are counted in revenue exactly once.

---

## 3. Test Coverage

- **Core API Unit Tests (`core/tests/test_sale_reissue_status_semantics.py`):**
  Covered reissue creation semantics, `superseded` and `reissued` statuses, filter queries, revenue report inclusion/exclusion, and startup migration idempotency (**122 passed**).
- **Inventory UI Unit Tests (`inventory-sales-module/tests/test_reissued_status_ui.py`):**
  Covered status filter badges, sales detail info boxes, and receipt banners (**94 passed**).
- **Avito Module Tests (`avito-module`):** **12 passed**.

---

## 4. Live Empirical HTTP Runtime Validation

1. **New Reissue Flow:**
   - Created Product #54, created Sale #40 (1234.0 ₽), canceled Sale #40 (`status = "canceled"`), reissued Sale #40 -> Created Sale #41.
   - Resulting Statuses: Sale #40 `status = "superseded"` (`superseded_by_sale_id = 41`), Sale #41 `status = "reissued"` (`source_sale_id = 40`).
2. **Filters Validation:**
   - `GET /sales?status=completed` -> Sale #41 is NOT present.
   - `GET /sales?status=reissued` -> Sale #41 IS present.
   - `GET /sales?status=superseded` -> Sale #40 IS present.
3. **Receipts Validation:**
   - `GET /sales/41/receipt` -> Displayed "ПОВТОРНО ОФОРМЛЕННАЯ ПРОДАЖА (НА ОСНОВЕ ПРОДАЖИ №40)".
   - `GET /sales/40/receipt` -> Displayed "АРХИВНЫЙ ЧЕК — ПРОДАЖА №40 ЗАМЕНЕНА (ПОВТОРНАЯ ПРОДАЖА №41)".
