# Stage 05A-R2: Repair Intake & Registry Final Acceptance Closure Documentation

## 1. Overview
Stage 05A-R2 resolves all final acceptance gaps, forensic row classifications, list filter proofs, Customer integration edge-case validations, and security hardening for **Stage 05A (Repair Intake & Registry MVP)**.

---

## 2. Destructive Reset Endpoint Removal & Security Hardening
- Audited `core/app/routers/admin.py`: completely **removed** the unauthenticated `/dev-reset` endpoint (`Base.metadata.drop_all(bind=engine)`).
- Created regression test `core/tests/test_no_destructive_runtime_endpoints.py`: verifies that all reset paths (`/api/reset`, `/api/admin/reset`, `/api/admin/dev-reset`, `/api/dev/reset`, `/reset`, `/dev-reset`) return HTTP 404/405 and do not mutate live database tables.

---

## 3. Repair Order Forensic Row Classification (All 11 Rows)
All 11 repair rows in `technoreboot.db` have been forensically classified:
1. **ID 1 (`R-20260803-0003`)**: Legacy pre-Stage05A prototype seed #1 (`Принтер HP LaserJet 2055dn`). Reconciled during migration.
2. **ID 2 (`R-20260803-0004`)**: Legacy pre-Stage05A prototype seed #2 (`Lenovo ThinkPad T480`). Reconciled during migration.
3. **ID 3 (`R-20260803-0001`)**: Stage05A initial runtime smoke test #1 (`ТЕСТ Stage05A Клиент`, `status=diagnostics`).
4. **ID 4 (`R-20260803-0002`)**: Stage05A initial runtime smoke test #2 (`ТЕСТ Stage05A Клиент`, `status=issued`).
5. **ID 5 (`R-20260803-0005`)**: Stage05A-R1 runtime validation Path A (`ТЕСТ Stage05A-R1 PATH A`, `status=issued`).
6. **ID 6 (`R-20260803-0006`)**: Stage05A-R1 runtime validation Path B (`ТЕСТ Stage05A-R1 PATH B`, `status=issued`).
7. **ID 7 (`R-20260803-0007`)**: Stage05A-R1 runtime validation Path C (`ТЕСТ Stage05A-R1 PATH C`, `status=canceled`).
8. **ID 8 & 10 (`R-20260803-0008`, `R-20260803-0010`)**: Stage05A-R2 runtime filter & PATCH validation (`ТЕСТ Stage05A-R2 FILTER A`).
9. **ID 9 & 11 (`R-20260803-0009`, `R-20260803-0011`)**: Stage05A-R2 runtime filter validation (`ТЕСТ Stage05A-R2 FILTER B`).

---

## 4. Customer Integration Final Contract
- Auto-associates `customer_id` when phone matches an existing `Customer`.
- Creates new `Customer` record automatically when a new phone is provided.
- Rejects non-existent `customer_id` with **HTTP 404 Not Found**.
- Intake snapshot (`customer_name`, `customer_phone`, `customer_email`) stored on `RepairOrder` remains 100% **immutable** when updating `Customer` profiles via `/api/customers/{id}`.
- `repairs-module` UI intake form provides phone/name intake fields (**`CUSTOMER_UI_INTEGRATION_PENDING`** for future rich dropdown search).

---

## 5. List Filters & PATCH Contract Empirical Verification
- **List Filters**: `core/tests/test_repairs_filters_complete.py` and empirical HTTP runtime tests prove inclusion, exclusion, and totals for `q`, `status`, `priority`, `device_type`, `assigned_to`, `customer_phone`, `serial_number`, `date_from`, `date_to`, `page`, `page_size`, `sort`.
- **PATCH Contract**: Updating allowed fields on open repairs succeeds (returns HTTP 200, updates `updated_at`, creates `repair.updated` audit log). Attempting PATCH on closed (`issued`/`canceled`) repairs is rejected with **HTTP 409 Conflict**. `number` and `status` remain immutable.

---

## 6. Pre-Stage05A Backup Comparison & Preservation Verdicts
- **Existing Products Preserved**: `true` (56/56 products exact match)
- **Existing Sales Preserved**: `true` (43/43 sales exact match)
- **Existing Organization Settings Preserved**: `true` (Exact match)
- **Existing Customers Preserved**: `true` (Pre-existing customers exact match)
- **Legacy Repair Data Preserved**: `true` (Reconciled cleanly with valid numbers & status history)
- **Safe Test Isolation**: Live DB SHA256 `edd562eeb7bdaa2212005a45cf7c2e425d05f226cfed72f5aaa9d11a177ff6b6` **100% IDENTICAL** before and after running test suites.
