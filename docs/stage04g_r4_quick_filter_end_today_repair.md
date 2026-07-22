# Stage 04G-R4 Quick Filter End Today Repair Documentation

## Overview
This documentation describes the repair implemented in Stage 04G-R4 for the Sales Reports module.

## Business & Functional Rules
For quick period filter buttons in Sales Reports:
- **Сегодня (`today`)**: `date_from = today`, `date_to = today`
- **Неделя (`week`)**: `date_from = Monday of current week`, `date_to = today`
- **Месяц (`month`)**: `date_from = 1st of current month`, `date_to = today`
- **Год (`year`)**: `date_from = Jan 1 of current year`, `date_to = today`

### Key Constraint
`date_to` for ALL quick filter period selections MUST ALWAYS end at today's date (`today`) and MUST NEVER be set to a future date (such as end of week, last day of month, or Dec 31).

---

## Implementation Details

1. **`core/app/routers/reports.py`**:
   - `get_date_range()` was updated so that for `week`, `month`, and `year`, `end_dt` is set to `datetime.combine(today, time.max)`.
   - Money summary rows and total aggregation compute daily and monthly breakdown rows up to today.

2. **`inventory-sales-module/app/routers/reports.py`**:
   - UI router synchronization extracts `date_from` and `date_to` from `report_data` returned by Core API, populating template input fields `<input type="date">` with the exact effective dates (`date_to` == today).

---

## Verification
- Unit test suites in `core`, `inventory-sales-module`, and `avito-module` pass cleanly.
- Runtime smoke tests confirm `date_to` matches `today` for all quick filters across Core API and Inventory UI.
