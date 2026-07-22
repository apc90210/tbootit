# PROMPT — Техноребут / Stage 04G-R4 Quick Filter End Date Must Be Today

## Роль агента

Ты senior fullstack bugfix engineer, FastAPI reporting engineer, Jinja2 UI developer, Docker runtime validator и QA/release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — исправить неверную реализацию Stage04G-R3.

Это repair текущего отчёта продаж. Следующий этап не начинать.

---

# 1. Требование владельца

Нужное поведение:

```text
Сегодня:
Дата с = сегодня
Дата по = сегодня

Неделя:
Дата с = понедельник текущей недели
Дата по = сегодня

Месяц:
Дата с = первое число текущего месяца
Дата по = сегодня

Год:
Дата с = 1 января текущего года
Дата по = сегодня
```

Критически важно:

```text
Дата по всегда должна быть сегодняшней датой.
```

Нельзя подставлять:

```text
конец недели
последний день месяца
31 декабря
```

---

# 2. Owner-check fail

Предыдущая реализация дала:

```text
today:
2026-07-22 — 2026-07-22

week:
2026-07-20 — 2026-07-26

month:
2026-07-01 — 2026-07-31

year:
2026-01-01 — 2026-12-31
```

Это неправильно.

Правильно для 2026-07-22:

```text
today:
2026-07-22 — 2026-07-22

week:
2026-07-20 — 2026-07-22

month:
2026-07-01 — 2026-07-22

year:
2026-01-01 — 2026-07-22
```

---

# 3. Дополнительные пробелы прошлого отчёта

Предыдущий агент не доказал:

```text
свежий avito-module pytest
успешный git push
финальный git status после push
```

Это обязательно выполнить и показать.

---

# 4. Статус

Текущий статус:

```text
STAGE04G_R3_OWNER_CHECK_FAILED_PERIOD_END_DATE_IN_FUTURE
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04G_R4_QUICK_FILTER_END_TODAY_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 5. Запреты

Запрещено:

```text
начинать следующий этап
оставлять week/month/year date_to в будущем
убирать быстрые фильтры
убирать свободный период
direct DB access из inventory-sales-module
отдельная DB
git add .
git add -A
git add -u
git commit --amend
git reset
git clean
rebase
force push
runtime DB/temp/cache в git
Base.metadata.drop_all/create_all
```

---

# 6. Prompt discovery

Найти:

```text
TECHNOREBOOT_STAGE04G_R4_QUICK_FILTER_END_TODAY_REPAIR_PROMPT.md
```

Искать:

```text
C:\Users\Apc\Downloads
C:\tbootit
C:\tbootit\.agents
C:\tbootit\.agents\received_prompts
C:\tbootit\prompts
C:\tbootit\docs
```

Если найден в Downloads — скопировать в:

```text
C:\tbootit\.agents\received_prompts\
```

В отчёте указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 7. Preflight

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git rev-parse HEAD
git log --oneline -10
git diff --name-status
git diff --stat
docker compose ps
```

Если worktree dirty — сначала определить причину.

---

# 8. Проверить текущую реализацию

Изучить:

```text
core/app/routers/reports.py
inventory-sales-module/app/routers/reports.py
inventory-sales-module/app/templates/reports_sales.html
core/tests/test_sales_reports.py
inventory-sales-module/tests/test_sales_reports_ui.py
```

Найти, почему сейчас вычисляется:

```text
week_end = Sunday
month_end = last day of month
year_end = December 31
```

---

# 9. Правильная логика периодов

Использовать:

```python
from datetime import date, timedelta

today = date.today()

today_from = today
today_to = today

week_from = today - timedelta(days=today.weekday())
week_to = today

month_from = date(today.year, today.month, 1)
month_to = today

year_from = date(today.year, 1, 1)
year_to = today
```

Не вычислять будущие конечные даты.

---

# 10. Core API

Для:

```text
GET /api/reports/sales?period=today
GET /api/reports/sales?period=week
GET /api/reports/sales?period=month
GET /api/reports/sales?period=year
```

Core должен возвращать:

```text
today:
date_from=today
date_to=today

week:
date_from=Monday current week
date_to=today

month:
date_from=first day current month
date_to=today

year:
date_from=January 1 current year
date_to=today
```

---

# 11. Inventory UI

После нажатия быстрых кнопок поля должны показывать:

```text
Дата с = report.date_from
Дата по = report.date_to
```

Видимые поля не должны содержать будущие даты.

---

# 12. Сохранить поведение R2

Сохранить:

```text
/reports/sales без параметров:
1 января текущего года — сегодня

custom dates:
редактируются вручную

обе даты пустые:
1 января текущего года — сегодня

только date_from:
date_to = сегодня

только date_to:
date_from = 1 января года date_to
```

Без Internal Server Error.

---

# 13. Core tests

Обновить:

```text
core/tests/test_sales_reports.py
```

Добавить проверки:

```text
period=today:
date_from == today
date_to == today

period=week:
date_from == Monday current week
date_to == today

period=month:
date_from == first day current month
date_to == today

period=year:
date_from == January 1 current year
date_to == today
```

Добавить:

```python
assert date.fromisoformat(data["date_to"]) <= date.today()
```

для всех быстрых периодов.

Не использовать фиксированный год.

---

# 14. Inventory tests

Обновить:

```text
inventory-sales-module/tests/test_sales_reports_ui.py
```

Проверить HTML:

```text
today:
оба input value = today

week:
date_from = Monday
date_to = today

month:
date_from = first day month
date_to = today

year:
date_from = January 1
date_to = today
```

Добавить assertion:

```text
date_to никогда не больше сегодняшней даты.
```

---

# 15. Docker rebuild

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose up -d avito-module
docker compose ps
```

---

# 16. Full regression

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Все три результата показать в финальном отчёте.

---

# 17. Core runtime smoke

```powershell
$today = Get-Date
$todayValue = $today.ToString("yyyy-MM-dd")

$weekStart = $today.AddDays(-(([int]$today.DayOfWeek + 6) % 7))
$weekStartValue = $weekStart.ToString("yyyy-MM-dd")

$monthStart = Get-Date -Year $today.Year -Month $today.Month -Day 1
$monthStartValue = $monthStart.ToString("yyyy-MM-dd")

$yearStart = Get-Date -Year $today.Year -Month 1 -Day 1
$yearStartValue = $yearStart.ToString("yyyy-MM-dd")
```

Проверить:

```powershell
$todayReport = Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=today"
$weekReport = Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=week"
$monthReport = Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=month"
$yearReport = Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=year"

$todayReport | Select-Object period,date_from,date_to
$weekReport | Select-Object period,date_from,date_to
$monthReport | Select-Object period,date_from,date_to
$yearReport | Select-Object period,date_from,date_to
```

Expected:

```text
today: todayValue / todayValue
week: weekStartValue / todayValue
month: monthStartValue / todayValue
year: yearStartValue / todayValue
```

---

# 18. UI runtime smoke

Проверить:

```powershell
$urls = @(
    "http://127.0.0.1:8030/reports/sales?period=today",
    "http://127.0.0.1:8030/reports/sales?period=week",
    "http://127.0.0.1:8030/reports/sales?period=month",
    "http://127.0.0.1:8030/reports/sales?period=year"
)

foreach ($url in $urls) {
    $response = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 15
    Write-Output "$($response.StatusCode) $url"
}
```

Проверить значения `date_from` и `date_to` в HTML для каждого периода.

---

# 19. Consistency check

Для каждого периода проверить:

```text
Core date_from/date_to
UI input date_from/date_to
денежная сводка
детализация продаж
```

Все должны использовать один диапазон.

---

# 20. Safety scans

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

```powershell
git grep -n -I "drop_all\|DROP TABLE\|DELETE FROM" -- core inventory-sales-module
```

```powershell
git ls-files | Select-String -Pattern "\.env$|id_rsa|id_ed25519|private_key|\.pem|\.p12|\.pfx"
```

---

# 21. Документация

Создать:

```text
reports/stage04g_r4_quick_filter_end_today_repair_report.md
docs/stage04g_r4_quick_filter_end_today_repair.md
```

Обновить:

```text
logs/2026-07-22.md
```

Report structure:

```text
# Stage 04G-R4 Quick Filter End Today Repair Report

## STATUS

## OWNER_REQUIREMENT

## PREVIOUS_WRONG_RANGES

## FIXED_RANGES

## ROOT_CAUSE

## FIXES

## FRESH_TESTS

Core:
Inventory:
Avito:

## CORE_RUNTIME_SMOKE

## UI_RUNTIME_SMOKE

## CONSISTENCY

## SAFETY_SCAN

## FILES_CHANGED

## COMMIT

## PUSH

## FINAL_GIT_STATUS

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04G_R4_QUICK_FILTER_END_TODAY_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 22. Git

Использовать только targeted add.

```powershell
git add core/app/routers/reports.py
git add core/tests/test_sales_reports.py
git add inventory-sales-module/app/routers/reports.py
git add inventory-sales-module/app/templates/reports_sales.html
git add inventory-sales-module/tests/test_sales_reports_ui.py
git add docs/stage04g_r4_quick_filter_end_today_repair.md
git add reports/stage04g_r4_quick_filter_end_today_repair_report.md
git add logs/2026-07-22.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04G_R4_QUICK_FILTER_END_TODAY_REPAIR_PROMPT.md
```

Коммит:

```powershell
git commit -m "Fix quick report filters to end at today"
git push
```

После push:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -3
```

Финальный status должен быть пустым.

---

# 23. Definition of Done

```text
today = today/today
week = Monday/today
month = first day month/today
year = January 1/today
no quick filter date_to is in future
Core and UI dates match
summary and sales detail use same dates
clean URL remains January 1/today
custom dates remain editable
Core tests pass
Inventory tests pass
Avito tests pass
runtime smoke pass
safety scans clean
targeted commit
push completed
final git status clean
owner manual check required
```

---

# 24. Final answer required from agent

Обязательно указать:

```text
текущую дату
предыдущие неверные диапазоны
новые правильные диапазоны
Core runtime results
UI runtime results
Core test result
Inventory test result
Avito test result
commit hash
push result
final git status
```

Успешный статус:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_R4_QUICK_FILTER_END_TODAY_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

При проблеме:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_R4_QUICK_FILTER_END_TODAY_FAIL

BLOCKERS:
...
```
