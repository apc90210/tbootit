# Stage05B-R2 Inline Repair Amount in Status Change Form

## Overview

Stage05B-R2 integrates the entry of `estimated_repair_amount` directly into the repair status change form on `/repairs/{id}`. Staff members no longer need to navigate to the separate `/repairs/{id}/edit` page to enter the repair amount before advancing a repair out of «Диагностика».

## Key Requirements & Capabilities

1. **Inline Form Entry**:
   When a repair is in status `diagnostics`, an input field `Стоимость ремонта, ₽` (`<input type="number" step="1" min="0">`) is displayed right above the comment field in the "Изменить статус" action card on `/repairs/{id}`.
2. **Initial Value Logic**:
   - If `estimated_repair_amount` is `None`, the field is empty (no forced defaults).
   - If `estimated_repair_amount` is already saved (e.g. `0` or `2800`), the input displays the saved integer (`value="0"`, `value="2800"`).
3. **Atomic Single Operation**:
   Submitting the status form sends status, comment, changed_by, and estimated_repair_amount in a single HTTP request to `POST /api/repairs/{id}/status`. Core processes the amount validation, model update, status change, status history recording, and audit logging in a single DB transaction.
4. **Validation Rules**:
   - Exiting `diagnostics` to any allowed target status (`ready`, `waiting_customer`, `waiting_parts`, `in_repair`, `unrepairable`, `canceled`) requires `estimated_repair_amount is not None` (or using pre-saved non-null amount).
   - `0` is a valid non-negative integer amount (`0 ₽`).
   - If no amount is provided, transition is blocked with HTTP 400 and detail message:
     `"Для выхода из статуса «Диагностика» укажите стоимость ремонта. Можно указать 0 ₽."`
   - Negative values or non-integer decimals are strictly rejected with HTTP 422 in API / Russian validation in UI.

## Core API Contract Update

- `schemas.RepairOrderStatusUpdate` expanded to include `estimated_repair_amount: Optional[int] = Field(None)`.
- `POST /api/repairs/{repair_id}/status` evaluates effective amount and updates `db_repair.estimated_repair_amount` atomically with `db_repair.status`.
