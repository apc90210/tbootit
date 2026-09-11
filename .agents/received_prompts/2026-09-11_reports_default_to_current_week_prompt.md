# TECHNOREBOOT — Owner Voice Request: Reports Default to Current Week

**Date:** 2026-09-11 14:39:31+03:00  
**Source:** Audio file attached to user request at 14:39:31+03:00  
**Target:** `inventory-sales-module/app/routers/reports.py`, `inventory-sales-module/app/templates/reports_sales.html`

## Transcript of Owner Voice Request
> "Сделай пожалуйста, чтобы при нажатии 'Отчёты' сразу текущая неделя была активна, то есть сразу выводила просто кнопка текущая неделя, отчёт за текущую неделю, а потом уже остальные кнопки это уже отдельно нажимались. По умолчанию чтобы так было."

## Requirements
1. In `inventory-sales-module/app/routers/reports.py`:
   - When opening `/reports/sales` (or `/inventory/reports/sales`) without query parameters, default `period` to `"week"` (current week) instead of custom year-to-date.
   - Pass `period="week"` to `core_client.get_sales_report(period="week")`.
2. In `inventory-sales-module/app/templates/reports_sales.html`:
   - Update quick period button label to "Текущая неделя" (or ensure active class is applied when `period == 'week'`).
   - When opening the reports page by clicking "Отчёты", the "Текущая неделя" button must be visually active by default.
   - The date pickers should synchronize to the week start (Monday) and current day.
   - Clicking other buttons ("Сегодня", "Месяц", "Год", or custom date submit) must continue to work as expected.
3. Update tests in `inventory-sales-module/tests/test_sales_reports_ui.py` to assert that default `/reports/sales` defaults to `period="week"` with the active week button.
4. Run full test suites across all modules and live verification via Gateway 8443 (mTLS).
5. Zero CLI for Owner.
