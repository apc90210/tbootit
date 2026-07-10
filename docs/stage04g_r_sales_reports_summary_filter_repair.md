# Stage 04G-R: Sales Reports Summary Table and Filter Repair

## Overview

Repair stage for Stage 04G. Fixes two owner-reported blockers:
1. Internal Server Error when using the report filter (clicking "Применить" with empty dates)
2. Missing compact money summary table at the top of the sales report page

## Changes

### Core API (`core/app/routers/reports.py`)
- Added `clean_param()` and `parse_date_or_none()` utilities for safe parameter handling
- `get_date_range()` now returns effective period (3 values) and falls back gracefully instead of raising errors
- Custom period with empty dates falls back to "today"
- Added `money_summary` aggregation: cash, card, transfer, sbp, legal_entity_account, other, unspecified, total
- Added `payment_labels` dict with Russian labels
- Payment method normalization: bank_card/acquiring → card, mixed → other, None/"" → unspecified

### Core Schemas (`core/app/schemas.py`)
- Added `MoneySummary` Pydantic model
- Extended `SalesReportResponse` with `money_summary` and `payment_labels` fields

### Inventory Reports Router (`inventory-sales-module/app/routers/reports.py`)
- Sanitizes query params before passing to CoreClient
- Handles Core API errors gracefully with `DEFAULT_REPORT_DATA` fallback
- Passes `error_message` to template for user feedback

### Inventory CoreClient (`inventory-sales-module/app/core_client.py`)
- Strips empty string params before forwarding to Core
- Extracts error detail from Core responses for better error messages

### Inventory Template (`inventory-sales-module/app/templates/reports_sales.html`)
- Added compact horizontal "Сводка денег за период" summary table above stats cards
- Shows all payment categories even when zero
- Handles both dict and object data access safely
- Displays error messages in alert box
- Summary table → Stats cards → Payment breakdown → Sales detail (top to bottom)

## API Response Format

```json
{
  "money_summary": {
    "cash": 0.0,
    "card": 0.0,
    "transfer": 0.0,
    "sbp": 0.0,
    "legal_entity_account": 0.0,
    "other": 0.0,
    "unspecified": 0.0,
    "total": 0.0
  },
  "payment_labels": {
    "cash": "Наличные",
    "card": "Безнал / карта",
    "transfer": "Перевод",
    "sbp": "СБП",
    "legal_entity_account": "Счёт юрлица",
    "other": "Другое",
    "unspecified": "Не указано"
  }
}
```

## Payment Method Normalization

| Raw value | Summary key | Label |
|---|---|---|
| cash | cash | Наличные |
| card | card | Безнал / карта |
| bank_card | card | Безнал / карта |
| acquiring | card | Безнал / карта |
| transfer | transfer | Перевод |
| sbp | sbp | СБП |
| legal_entity_account | legal_entity_account | Счёт юрлица |
| mixed | other | Другое |
| other | other | Другое |
| None / "" | unspecified | Не указано |
