# PROMPT — Техноребут / Stage 04G-S Sales Reports Daily Money Summary Refinement

## Роль агента

Ты senior fullstack developer, FastAPI reporting engineer, Jinja2 UI developer, business reporting analyst и QA/release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — уточнить верхнюю денежную таблицу в отчётах продаж. Это refinement/repair Stage04G, не новый модуль.

---

# 1. Owner requirement

Владелец уточнил:

```text
Нужно верхнюю таблицу по деньгам сделать следующим образом.
Когда нажимаешь сегодня, оно отображает только сегодняшнее,
написана дата и сегодняшние деньги.

Когда нажимаешь на неделю, она эту таблицу верхнюю делает по дням.
То есть за такой-то день пришло столько-то нал, безнал, юрлица и общая сумма.
Потом следующий день, число, то же самое.
То есть, грубо говоря, 7 дней за эту неделю.
И внизу итоговая цифра за неделю.

За месяц то же самое.
То есть каждый день по дням делает разбивку по нал, безнал, юрлица.
А в конце итоговый месяц денег по пунктам, нал, безнал и итого за месяц.
```

Интерпретация:

```text
1. Верхняя таблица "Сводка денег за период" должна быть таблицей по дням.
2. Для "Сегодня":
   - одна строка с сегодняшней датой;
   - деньги за сегодня по каналам;
   - итог за день.
3. Для "Неделя":
   - 7 строк, каждый день недели;
   - по каждой дате: нал, безнал, перевод, СБП, счёт юрлица, другое/не указано, итого;
   - внизу итоговая строка за неделю.
4. Для "Месяц":
   - строки по каждому дню месяца;
   - внизу итоговая строка за месяц.
5. Для custom date_from/date_to:
   - строки по каждому дню выбранного периода;
   - внизу итоговая строка за период.
6. Для "Год":
   - по умолчанию сделать строки по месяцам, чтобы не выводить 365 строк;
   - внизу итоговая строка за год.
   - В отчёте явно подписать: "Сводка по месяцам за год".
```

---

# 2. Target status

Текущий статус:

```text
STAGE04G_R_OWNER_RECHECK_NEEDS_DAILY_MONEY_SUMMARY
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04G_S_DAILY_MONEY_SUMMARY_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Strict prohibitions

Запрещено:

```text
начинать следующий этап
делать новый модуль
делать direct DB access из inventory-sales-module
создавать отдельную DB для отчетов
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset / git clean / rebase / force push
коммитить runtime DB/temp/cache
делать Base.metadata.drop_all/create_all
```

Разрешено:

```text
точечный refinement Core reports API
точечный refinement Inventory reports UI/router/CoreClient
добавить period_money_rows / daily_money_summary
tests
report/log
targeted commit
normal push
```

---

# 4. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04G_S_DAILY_MONEY_SUMMARY_REFINEMENT_PROMPT.md
```

Искать:

```text
C:\tbootit
C:\tbootit\.agents
C:\tbootit\docs
C:\tbootit\docs\obsidian
C:\tbootit\prompts
C:\tbootit\logs\prompts
C:\Users\Apc\Downloads
```

Если найден в Downloads — скопировать в:

```text
C:\tbootit\.agents\received_prompts\
```

В report указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 5. Preflight

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -10
git diff --name-status
git diff --stat
docker compose ps
```

Если worktree dirty — STOP и разобраться.

---

# 6. Current behavior to inspect

Проверить текущие файлы:

```text
core/app/routers/reports.py
core/app/schemas.py
core/tests/test_sales_reports.py

inventory-sales-module/app/core_client.py
inventory-sales-module/app/routers/reports.py
inventory-sales-module/app/templates/reports_sales.html
inventory-sales-module/tests/test_sales_reports_ui.py
```

Проверить текущий API:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=today" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=week" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=month" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=year" | ConvertTo-Json -Depth 10
```

---

# 7. API requirement — period money rows

В Core response добавить новую структуру, например:

```json
"money_summary_rows": [
  {
    "period_key": "2026-07-10",
    "label": "10.07.2026",
    "cash": 1000,
    "card": 2000,
    "transfer": 0,
    "sbp": 500,
    "legal_entity_account": 3000,
    "other": 0,
    "unspecified": 0,
    "total": 6500
  }
],
"money_summary_total": {
  "cash": 1000,
  "card": 2000,
  "transfer": 0,
  "sbp": 500,
  "legal_entity_account": 3000,
  "other": 0,
  "unspecified": 0,
  "total": 6500
},
"money_summary_granularity": "day"
```

Для года:

```json
"money_summary_granularity": "month"
```

И rows:

```json
[
  {"period_key": "2026-01", "label": "Январь 2026", ...},
  {"period_key": "2026-02", "label": "Февраль 2026", ...}
]
```

Оставить старое поле:

```text
money_summary
```

для совместимости, но UI должен использовать новую таблицу rows + total.

---

# 8. Row generation logic

Нужно генерировать строки даже для дней без продаж.

## today

```text
1 row:
- today date
- all payment columns
- total
```

## week

```text
7 rows:
- Monday
- Tuesday
- Wednesday
- Thursday
- Friday
- Saturday
- Sunday
```

Каждая строка содержит суммы по этой дате.

## month

```text
N rows, где N = количество дней в текущем месяце.
```

## custom

```text
Все даты от date_from до date_to включительно.
Если период слишком большой > 120 дней:
- можно группировать по месяцам
- или вернуть понятное ограничение
```

Для MVP можно разрешить до 366 дней.

## year

```text
12 rows по месяцам.
```

---

# 9. Payment columns

В верхней таблице должны быть стабильные колонки:

```text
Дата / Период
Наличные
Безнал / карта
Перевод
СБП
Счёт юрлица
Другое
Не указано
Итого
```

Нормализация:

```text
cash → Наличные
card → Безнал / карта
bank_card → Безнал / карта
acquiring → Безнал / карта
transfer → Перевод
sbp → СБП
legal_entity_account → Счёт юрлица
other → Другое
mixed → Другое
None / "" / unknown → Не указано
```

---

# 10. UI requirement

В `reports_sales.html` заменить текущую верхнюю одноразовую summary table на новую таблицу:

Заголовок:

```text
Сводка денег за период
```

Подзаголовок:

```text
Сегодня: по дням
Неделя: по дням
Месяц: по дням
Год: по месяцам
Произвольный период: по дням
```

Таблица:

```text
| Дата | Наличные | Безнал / карта | Перевод | СБП | Счёт юрлица | Другое | Не указано | Итого |
| 10.07.2026 | ... |
| Итого за период | ... |
```

Для недели:

```text
7 строк + "Итого за неделю"
```

Для месяца:

```text
каждый день месяца + "Итого за месяц"
```

Для года:

```text
12 строк по месяцам + "Итого за год"
```

Таблица должна быть сверху, до детального списка продаж.

---

# 11. Core tests

Обновить:

```text
core/tests/test_sales_reports.py
```

Добавить tests:

```text
1. today returns money_summary_rows length 1.
2. week returns 7 day rows.
3. month returns number of days in current month.
4. year returns 12 month rows.
5. custom range 2026-07-01..2026-07-03 returns 3 rows.
6. rows include zero-money days.
7. row total = sum payment columns.
8. money_summary_total = sum of rows.
9. legal_entity_account counted in correct day row.
10. blank/None payment_method counted in unspecified.
11. old money_summary total remains compatible with money_summary_total.total.
```

---

# 12. Inventory tests

Обновить:

```text
inventory-sales-module/tests/test_sales_reports_ui.py
```

Добавить tests:

```text
1. /reports/sales?period=today renders "Сводка денег за период".
2. today renders at least one date row.
3. week renders seven rows from mocked report.
4. month renders daily rows from mocked report.
5. year renders month rows from mocked report.
6. table contains columns:
   Дата, Наличные, Безнал / карта, Перевод, СБП, Счёт юрлица, Итого.
7. table contains "Итого за период" or period-specific total.
8. summary table appears before detailed sales table.
9. no Internal Server Error with empty date filters.
```

---

# 13. Manual smoke

After implementation:

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose ps
```

Check UI:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=today" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=week" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=month" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=year" -TimeoutSec 15 | Select-Object StatusCode
```

Check Core rows:

```powershell
$r = Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=week"
$r.money_summary_rows.Count
$r.money_summary_total | ConvertTo-Json -Depth 5
```

Expected:

```text
week count = 7
year count = 12
```

Check UI content:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=week" -TimeoutSec 15
$page.Content | Select-String "Сводка денег за период"
$page.Content | Select-String "Дата"
$page.Content | Select-String "Наличные"
$page.Content | Select-String "Безнал / карта"
$page.Content | Select-String "Счёт юрлица"
$page.Content | Select-String "Итого"
```

---

# 14. Full regression

Run:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

All must pass.

---

# 15. Safety scans

Runtime tracked:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

Direct DB access in inventory-sales-module:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Destructive DB calls:

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core inventory-sales-module
```

Secrets:

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 16. Docs/report/log

Create:

```text
reports/stage04g_s_daily_money_summary_refinement_report.md
docs/stage04g_s_daily_money_summary_refinement.md
```

Update:

```text
logs/2026-07-10.md
```

Report structure:

```text
# Stage 04G-S Daily Money Summary Refinement Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## OWNER_REQUIREMENT

## IMPLEMENTED

### Daily summary rows

### Weekly summary rows

### Monthly summary rows

### Yearly month rows

### Totals row

## API

money_summary_rows:
money_summary_total:
money_summary_granularity:

## UI

Top table:
Columns:
Total row:
Detailed sales below:

## TESTS

Core:
Inventory:
Avito:

## MANUAL_SMOKE

Today:
Week:
Month:
Year:
Custom:

## SAFETY_SCAN

Runtime tracked:
Direct DB access:
Destructive DB calls:
Secrets:

## FILES_CHANGED

## COMMIT

## PUSH

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04G_S_DAILY_MONEY_SUMMARY_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 17. Git

Use targeted add only.

Possible files:

```powershell
git add core/app/routers/reports.py
git add core/app/schemas.py
git add core/tests/test_sales_reports.py

git add inventory-sales-module/app/templates/reports_sales.html
git add inventory-sales-module/tests/test_sales_reports_ui.py

git add docs/stage04g_s_daily_money_summary_refinement.md
git add reports/stage04g_s_daily_money_summary_refinement_report.md
git add logs/2026-07-10.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04G_S_DAILY_MONEY_SUMMARY_REFINEMENT_PROMPT.md

git commit -m "Refine Stage 04G sales reports daily money summary"
git status --short --untracked-files=all
```

Forbidden:

```text
git add .
git add -A
git add -u
git commit --amend
```

If remote exists:

```powershell
git push
```

No force push.

---

# 18. Definition of Done

Готово, если:

```text
Today top summary = one row for today + total
Week top summary = 7 day rows + weekly total
Month top summary = each month day + monthly total
Year top summary = 12 month rows + yearly total
Custom range top summary = each day + total
Columns include cash/card/transfer/sbp/legal_entity_account/other/unspecified/total
Detailed sales table remains below
No filter 500
Core/inventory/avito tests pass
Safety scans clean
Targeted commit
Push
READY_FOR_OWNER_RECHECK
```

---

# 19. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_S_DAILY_MONEY_SUMMARY_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_S_DAILY_MONEY_SUMMARY_FAIL

BLOCKERS:
...
```
