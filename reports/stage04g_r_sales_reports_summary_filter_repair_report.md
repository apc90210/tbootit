# Stage 04G-R Sales Reports Summary Table and Filter Repair Report

## STATUS

TECHNOREBOOT_STAGE04G_R_SALES_REPORTS_SUMMARY_FILTER_REPAIR_READY_FOR_OWNER_RECHECK

## OWNER_REPORTED_FAIL

```text
в отчете нужна маленкая сводная таблица сверху
за период только деньги,
отдельно приход нал безнал перевод и т д и общая сумма.
ошибка Internal Server Error при работе фильтра
```

## ROOT_CAUSE

### Internal Server Error
- HTML form has `<input type="hidden" name="period" value="custom">` — always sends `period=custom` when user clicks "Применить"
- If date fields are empty, Core returns 400 ("date_from and date_to are required for custom period")
- Inventory `core_client.get_sales_report()` returns `{"error": True, "status_code": 400}` dict
- Template tries to access `.total_amount` on this error dict → Jinja2 UndefinedError → 500

### Missing compact money table
- Feature was not implemented in Stage04G — no `money_summary` field in API, no compact table in template

## FIXES

### Report filter 500 repair
- Core `get_date_range()` now returns 3 values: `start_dt, end_dt, effective_period`
- Custom period with empty dates falls back to "today" instead of raising 400
- Unknown period values fall back to "today" instead of raising 400

### Query params sanitization
- Added `clean_param()` utility to Core and Inventory: treats empty strings as None
- Added `parse_date_or_none()` to Core: validates date format, returns 400 with human-readable message on invalid format
- Inventory `CoreClient.get_sales_report()` now strips empty string params before forwarding to Core
- Inventory reports router sanitizes `period`, `date_from`, `date_to` before passing to CoreClient
- Inventory reports router handles Core error responses with `DEFAULT_REPORT_DATA` fallback — template never crashes

### Money summary table
- Core API now returns `money_summary` with all payment categories: cash, card, transfer, sbp, legal_entity_account, other, unspecified, total
- Core API returns `payment_labels` dict with human-readable labels for each category
- Template renders compact horizontal summary table "Сводка денег за период" above stats cards and sales detail

### Payment method normalization
- `bank_card` and `acquiring` → mapped to `card` (Безнал / карта) in summary
- `mixed` → mapped to `other` (Другое) in summary
- `None`, empty string → mapped to `unspecified` (Не указано)
- Labels updated: "Карта / эквайринг" → "Безнал / карта" per owner specification

## MONEY_SUMMARY_FIELDS

```text
cash: Наличные
card: Безнал / карта
transfer: Перевод
sbp: СБП
legal_entity_account: Счёт юрлица
other: Другое
unspecified: Не указано
total: Итого (sum of all above)
```

## TESTS

### Core: 66 passed
- test_reports_empty_date_from_date_to_no_500
- test_reports_custom_empty_dates_falls_back
- test_reports_invalid_date_returns_400
- test_reports_money_summary_has_all_keys
- test_reports_money_summary_total_equals_sum
- test_reports_legal_entity_in_summary
- test_reports_none_payment_goes_to_unspecified
- test_reports_payment_labels_present
- (plus all 9 original tests retained)

### Inventory: 50 passed
- test_reports_sales_default_200
- test_reports_sales_today_200
- test_reports_sales_week_200
- test_reports_sales_year_200
- test_reports_sales_empty_dates_200
- test_reports_sales_custom_dates_200
- test_reports_sales_contains_summary_title
- test_reports_sales_contains_cash
- test_reports_sales_contains_card
- test_reports_sales_contains_transfer
- test_reports_sales_contains_sbp
- test_reports_sales_contains_legal_entity
- test_reports_sales_contains_total
- test_summary_table_before_sales_table
- test_core_error_does_not_crash_template
- (plus all original tests retained)

### Avito: 12 passed
- No changes, full regression passed

## MANUAL_SMOKE

```text
/reports/sales: 200 ✅
period=today: 200 ✅
period=week: 200 ✅
period=month: 200 ✅
period=year: 200 ✅
date_from=&date_to=: 200 ✅ (was 500)
period=custom&date_from=&date_to=: 200 ✅ (was 500)
custom date range: 200 ✅
summary table present: ✅
all payment labels present: ✅
```

## SAFETY_SCAN

```text
Runtime tracked: clean ✅
Direct DB access (inventory-sales-module): clean ✅
Destructive DB calls: clean ✅
Secrets: clean ✅
```

## FILES_CHANGED

```text
core/app/routers/reports.py — sanitize params, build money_summary, return payment_labels
core/app/schemas.py — add MoneySummary schema, extend SalesReportResponse
core/tests/test_sales_reports.py — add 8 new tests for filter and summary

inventory-sales-module/app/routers/reports.py — sanitize params, error handling with fallback
inventory-sales-module/app/core_client.py — strip empty params, extract error detail
inventory-sales-module/app/templates/reports_sales.html — compact money summary table, error display, safe dict access
inventory-sales-module/tests/test_sales_reports_ui.py — add 15 new tests
inventory-sales-module/tests/test_sales_payment_channels_ui.py — preserved (no changes needed)

reports/stage04g_r_sales_reports_summary_filter_repair_report.md — this report
docs/stage04g_r_sales_reports_summary_filter_repair.md — docs
logs/2026-07-10.md — execution log

.agents/received_prompts/TECHNOREBOOT_STAGE04G_R_SALES_REPORTS_SUMMARY_FILTER_REPAIR_PROMPT.md — prompt copy
```

## COMMIT

Pending

## PUSH

Pending

## OWNER_RECHECK_GUIDE

1. Открыть http://127.0.0.1:8030/reports/sales
2. Убедиться что сверху есть "Сводка денег за период" с колонками: Наличные | Безнал / карта | Перевод | СБП | Счёт юрлица | Другое | Не указано | Итого
3. Нажать "Применить" с пустыми датами — должен загрузиться отчёт за сегодня, НЕ Internal Server Error
4. Проверить фильтры Сегодня / Неделя / Месяц / Год — все должны работать
5. Указать даты и нажать "Применить" — должен отработать кастомный диапазон
6. Создать продажу с оплатой "Счёт юрлица" и убедиться что сумма появилась в сводке
7. Таблица "Детализация продаж" должна быть НИЖЕ сводки

## FINAL_STATUS

TECHNOREBOOT_STAGE04G_R_SALES_REPORTS_SUMMARY_FILTER_REPAIR_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
