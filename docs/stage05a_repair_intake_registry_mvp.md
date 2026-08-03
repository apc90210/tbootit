# Stage 05A: Repair Intake & Registry MVP Documentation

## 1. Overview
Stage 05A introduces the standalone **Repair Intake & Registry MVP** microservice (`repairs-module`) operating on port `8040` alongside upgraded Core API endpoints (`/api/repairs`). The system provides full repair intake lifecycle management, automated unique repair numbering (`R-YYYYMMDD-XXXX`), strict status transition matrix enforcement, and full status history audit tracking.

---

## 2. Core API Architecture & Schema Upgrades
The Core SQLite `repair_orders` table was updated via **100% additive idempotent schema migrations**:
- **Added Columns**: `number`, `customer_name`, `customer_phone`, `customer_email`, `device_type`, `brand`, `model`, `serial_number`, `reported_issue`, `completeness`, `appearance`, `customer_comment`, `internal_note`, `access_code_provided`, `assigned_to`, `priority`, `accepted_at`, `created_at`, `updated_at`, `closed_at`, `issued_at`, `canceled_at`.
- **New Table**: `repair_status_history` tracking `(repair_id, old_status, new_status, comment, changed_by, changed_at)`.
- **Indexes**: Created indexes on `number` (UNIQUE), `status`, `customer_phone`, `serial_number`, and `repair_id`.

---

## 3. Status Transition Matrix Enforcement
The repair lifecycle is governed by strict, unidirectionally validated transitions:
- `received` ➔ `diagnostics`, `canceled`
- `diagnostics` ➔ `waiting_customer`, `waiting_parts`, `in_repair`, `unrepairable`, `canceled`
- `waiting_customer` ➔ `diagnostics`, `waiting_parts`, `in_repair`, `unrepairable`, `canceled`
- `waiting_parts` ➔ `waiting_customer`, `in_repair`, `unrepairable`, `canceled`
- `in_repair` ➔ `waiting_customer`, `waiting_parts`, `ready`, `unrepairable`, `canceled`
- `ready` ➔ `in_repair`, `issued`
- `unrepairable` ➔ `issued`, `canceled`
- `issued` ➔ *terminal* (Editing & status change blocked with HTTP 409 Conflict)
- `canceled` ➔ *terminal* (Editing & status change blocked with HTTP 409 Conflict)

---

## 4. Microservice: `repairs-module` (Port 8040)
- Built with **FastAPI** + **Jinja2** templates + Vanilla CSS (`app.css`).
- Communicates **EXCLUSIVELY** via HTTP REST API (`CORE_API_BASE_URL`).
- **Zero direct database imports** (0 SQLAlchemy/SQLite imports).
- **Security Guarantee**: No password, PIN code, or unlock code fields exist anywhere in the module or models; only a boolean `access_code_provided` flag is supported.

---

## 5. Verification Results
- **Core Safe Unit Tests**: 136 passed cleanly (`scripts/test_core_safe.ps1`).
- **Inventory & Sales Tests**: 110 passed cleanly (`inventory-sales-module`).
- **Avito Module Tests**: 12 passed cleanly (`avito-module`).
- **Repairs Module Tests**: 7 passed cleanly (`repairs-module`).
- **Live HTTP Smoke Test**: Successfully created repair `ТЕСТ Stage05A` (`R-20260803-0002`), transitioned through statuses, closed, verified HTTP 409 on invalid transition, and confirmed live HTML rendering at `http://localhost:8040/repairs`.
