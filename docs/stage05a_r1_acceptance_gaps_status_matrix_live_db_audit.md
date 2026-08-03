# Stage 05A-R1: Repair Workflow Acceptance Gaps, Status Matrix & Live DB Audit Documentation

## 1. Overview
Stage 05A-R1 resolves all acceptance gaps and workflow audit findings for **Stage 05A (Repair Intake & Registry MVP)**. It guarantees complete status transition matrix enforcement, verifies all Core API endpoints and query filters, audits legacy database records, and validates Customer model integration.

---

## 2. Complete Status Transition Matrix
The repair lifecycle is governed by the following exact matrix:
- **`received`** ➔ `diagnostics`, `canceled`
- **`diagnostics`** ➔ `waiting_customer`, `waiting_parts`, `in_repair`, `unrepairable`, `canceled`
- **`waiting_customer`** ➔ `diagnostics`, `waiting_parts`, `in_repair`, `unrepairable`, `canceled`
- **`waiting_parts`** ➔ `waiting_customer`, `in_repair`, `unrepairable`, `canceled`
- **`in_repair`** ➔ `waiting_customer`, `waiting_parts`, `ready`, `unrepairable`, `canceled`
- **`ready`** ➔ `in_repair`, `issued`
- **`unrepairable`** ➔ `issued`, `canceled`
- **`issued`** ➔ *terminal* (Editing & status modification blocked with HTTP 409 Conflict)
- **`canceled`** ➔ *terminal* (Editing & status modification blocked with HTTP 409 Conflict)

---

## 3. Legacy Database Record Reconciliation
Additive idempotent migration `run_repair_additive_migration()` safely updated legacy repair records in `technoreboot.db`:
- Legacy Row ID #1 (`Принтер HP LaserJet 2055dn`): Assigned unique number `R-20260803-0003`, default customer snapshot, and initial status history row.
- Legacy Row ID #2 (`Lenovo ThinkPad T480`): Assigned unique number `R-20260803-0004`, default customer snapshot, and initial status history row.
- Zero legacy data lost, zero duplicate numbers.

---

## 4. Customer Model Integration Audit
- Core API `create_repair` checks for existing `Customer` by `customer_id` or `phone`.
- If found, `customer_id` is linked and name/phone/email are snapshotted into `RepairOrder`.
- If not found, a new `Customer` record is created automatically and linked.
- Subsequent changes to `Customer` profiles do not alter past `RepairOrder` intake snapshots.

---

## 5. UI Status Filters in `repairs-module` (Port 8040)
The registry interface (`/repairs`) renders filter buttons for **ALL 9 statuses**:
- `Все`, `Приняты`, `Диагностика`, `Ожидают клиента`, `Ожидают запчасти`, `В ремонте`, `Готовы`, `Ремонт невозможен`, `Выданы`, `Отменены`.
- Clicking any status filter preserves active search parameter `q`.

---

## 6. Verification & Test Suite Summary
- **Core Safe Unit Tests**: **136 PASSED** (`test_core_safe.ps1`).
- **Inventory Unit Tests**: **110 PASSED**.
- **Avito Unit Tests**: **12 PASSED**.
- **Repairs Unit Tests**: **8 PASSED**.
- **Live DB Preservation**: SHA256 `c26c5c2723a318c1d0500cc658d9736acf360e8fdc2db6244f0fa8801287d42e` **100% IDENTICAL** before and after running test suites.
