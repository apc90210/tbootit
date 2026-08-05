# Stage05B Simple Repair Diagnosis and Manual Estimate

## Overview

Stage05B implements a lightweight, manual diagnosis and repair estimate workflow for the TechnoReboot platform. In accordance with owner scope reduction directives, complex entities (such as separate `RepairDiagnosis` / `RepairEstimate` / `RepairEstimateItem` tables, diagnosis versions, line-item pricing tables, client approval history, new repair statuses, automatic stock reservations, or separate printable estimates) have been explicitly excluded.

Instead, four simple fields are added directly to `RepairOrder` for free-text manual entry and a single manual estimated total amount.

## Field Specifications

1. **`diagnosis_text`**: Free multiline text (`TEXT` in SQLite/SQLAlchemy, `Optional[str]` in Pydantic). Stores diagnostic findings (e.g., "Неисправен разъём питания.").
2. **`planned_works_text`**: Free multiline text (`TEXT` in SQLite/SQLAlchemy, `Optional[str]` in Pydantic). Stores list of planned labor/services entered manually (e.g., "1. Разборка - 500 ₽\n2. Замена разъёма - 1500 ₽").
3. **`planned_parts_text`**: Free multiline text (`TEXT` in SQLite/SQLAlchemy, `Optional[str]` in Pydantic). Stores list of planned parts and materials entered manually (e.g., "1. Разъём питания - 800 ₽").
4. **`estimated_repair_amount`**: Whole integer rubles (`INTEGER` in SQLite/SQLAlchemy, `Optional[int]` in Pydantic, `step="1" min="0"` in HTML). Stores total manual estimated cost (e.g., `4100` or `0`). Nullable prior to diagnosis. Decimal inputs (like `4100.5`) or negative values are strictly rejected with HTTP 422.

## Core API Integration

- **Model & Schemas**: `RepairOrder`, `RepairOrderBase`, `RepairOrderUpdate` updated with the 4 fields.
- **PATCH Endpoint**: `PATCH /api/repairs/{id}` receives JSON payload and updates fields without auto-triggering status transitions or stock movements. Audit log records `repair.updated` action.
- **Terminal Protection**: Attempting to edit a closed (`issued`) or canceled (`canceled`) repair via `PATCH` returns HTTP 409 Conflict.

## UI Integration

- **Detail Card** (`/repairs/{id}`): Displays block "Диагностика и предварительная стоимость". Preserves line breaks (`white-space: pre-wrap;`). Displays `Не указано` for null/empty fields and formatted rubles (e.g., `4100 ₽` or `0 ₽`) for amount.
- **Edit Form** (`/repairs/{id}/edit`): Renders Section 5 with textareas for diagnosis, works, and parts, and a number input (`step="1" min="0"`) for estimated repair amount. Preserves entered values upon validation error and escapes user HTML/JS against XSS.
- **Intake Form** (`/repairs/new`): Diagnosis fields are intentionally excluded from primary intake, as diagnosis is performed post-intake.

## Print Order Decision

The 2-page A4 printable work order (`repair_print_order.html`) remains unchanged to ensure strict adherence to the approved legal document layout and page budget. No extra pages or separate estimate documents are created.
