# Stage 04G-R2 Default Year-to-Date Period Report

## STATUS

READY_FOR_OWNER_RECHECK

## OWNER_REQUIREMENT

По умолчанию при отсутствии query параметров, отчёт по продажам должен формироваться за свободный период (custom) с 1 января текущего года по сегодняшнюю дату. Кнопки быстрых фильтров должны продолжать работать. Открытие страницы должно сразу отображать эти даты в фильтрах и отфильтрованные данные, а также денежную сводку за этот период.

## PREVIOUS_DEFAULT

period=today

## NEW_DEFAULT

date_from: 2026-01-01 (1 января текущего года)
date_to: 2026-07-16 (текущая дата)
mode: custom

## IMPLEMENTATION

### Core default
В core/app/routers/reports.py изменен дефолтный fallback, когда period, date_from и date_to отсутствуют. Теперь при пустых параметрах Core применяет period="today" (и это работает в комбинации с Inventory, который явно передает даты), но при period="custom" и пустых датах падает на year-to-date. (Инвентаризация передает даты). Также починена логика односторонних дат: date_from использует текущую дату для date_to. date_to использует 1 января своего года для date_from.

### Inventory route default
В inventory-sales-module/app/routers/reports.py при обращении к /reports/sales без параметров period устанавливается в custom, а date_from и date_to принудительно задаются как 1 января текущего года и сегодняшняя дата. Эти параметры передаются в Core API.

### Filter form values
Значения автоматически передаются в шаблон eports_sales.html, и HTML инпуты содержат нужные даты.

### Empty and one-sided dates
Если пользователь очищает обе даты и отправляет форму, логика приравнивается к отсутствующим датам при period=custom, и диапазон возвращается к year-to-date (с 1 января по сегодня). 500 ошибка устранена.

### Quick period buttons
При нажатии на Сегодня/Неделя/Месяц/Год в URL передается period=... без date_from и date_to. Логика их обрабатывает приоритетно.

## TESTS

Core: 88 passed
Inventory: 59 passed
Avito: 12 passed

## RUNTIME_SMOKE

Expected date_from: 2026-01-01
Expected date_to: 2026-07-16
Core date_from: 2026-01-01
Core date_to: 2026-07-16
UI date_from: 2026-01-01
UI date_to: 2026-07-16
Default status: 200 OK
Quick filters: 200 OK
Empty dates: 200 OK, falls back to default
One-sided dates: 200 OK

## SAFETY_SCAN

Clean.

## FILES_CHANGED

- core/app/routers/reports.py
- core/tests/test_sales_reports.py
- inventory-sales-module/app/routers/reports.py
- inventory-sales-module/tests/test_sales_reports_ui.py
- reports/stage04g_r2_default_year_to_date_period_report.md
- docs/stage04g_r2_default_year_to_date_period.md
- logs/2026-07-16.md

## COMMIT

TBD

## PUSH

TBD

## FINAL_GIT_STATUS

TBD

## OWNER_RECHECK_GUIDE

1. Открыть \http://127.0.0.1:8030/reports/sales\ без параметров.
2. Убедиться, что выбраны даты с 1 января по сегодня.
3. Очистить обе даты и нажать "Применить" - даты должны снова стать 1 января - сегодня.
4. Выбрать только "Дату с" или "Дату по" - запрос должен выполниться успешно, заполнив недостающую дату.

## FINAL_STATUS

TECHNOREBOOT_STAGE04G_R2_DEFAULT_YEAR_TO_DATE_PERIOD_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
