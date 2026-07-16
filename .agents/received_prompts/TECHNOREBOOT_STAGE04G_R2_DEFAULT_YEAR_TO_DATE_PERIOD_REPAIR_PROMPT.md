# PROMPT — Техноребут / Stage 04G-R2 Default Report Period From January 1 to Today

## Роль агента

Ты senior fullstack developer, FastAPI reporting engineer, Jinja2 UI developer, Docker runtime validator и QA/release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — выполнить дополнительное исправление Stage04G-R до ручной проверки владельцем.

Это не новый этап. Это обязательный repair текущего отчёта продаж.

---

# 1. Owner requirement

Владелец сообщил:

```text
пока я не проверил, сразу исправление,
по умолчанию свободный период
с первого января текущего года до сегодня
```

Требуемое поведение:

```text
1. При открытии /reports/sales без query-параметров:
   - date_from = 1 января текущего года;
   - date_to = сегодняшняя дата.

2. Страница сразу показывает:
   - продажи с 1 января текущего года по сегодня;
   - денежную сводку за этот же период;
   - детализацию продаж за этот же период.

3. Поля "Дата с" и "Дата по" сразу заполнены:
   - YYYY-01-01;
   - сегодняшней датой.

4. Это должен быть именно свободный/custom период,
   а не period=today и не period=year.

5. Быстрые кнопки:
   - Сегодня;
   - Неделя;
   - Месяц;
   - Год
   остаются и продолжают работать.

6. При повторном открытии чистого URL:
   /reports/sales
   снова должен применяться диапазон:
   1 января текущего года — сегодня.
```

---

# 2. Current status

Текущий статус:

```text
STAGE04G_R_READY_FOR_OWNER_RECHECK_BUT_DEFAULT_PERIOD_CHANGE_REQUIRED
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04G_R2_DEFAULT_YEAR_TO_DATE_PERIOD_READY_FOR_OWNER_RECHECK
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
убирать быстрые фильтры Сегодня/Неделя/Месяц/Год
делать direct DB access из inventory-sales-module
создавать отдельную DB
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset
использовать git clean
использовать rebase
использовать force push
коммитить runtime DB/temp/cache
делать Base.metadata.drop_all/create_all
```

Разрешено:

```text
точечное изменение default report period
точечное изменение UI filter defaults
Core API normalization if needed
tests
runtime smoke
report/docs/log
targeted commit
normal push
```

---

# 4. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04G_R2_DEFAULT_YEAR_TO_DATE_PERIOD_REPAIR_PROMPT.md
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

Если prompt найден в Downloads — скопировать в:

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
git rev-parse HEAD
git log --oneline -10
git diff --name-status
git diff --stat
docker compose ps
```

Если worktree dirty — сначала установить причину.

---

# 6. Inspect current behavior

Проверить:

```text
core/app/routers/reports.py
inventory-sales-module/app/core_client.py
inventory-sales-module/app/routers/reports.py
inventory-sales-module/app/templates/reports_sales.html
core/tests/test_sales_reports.py
inventory-sales-module/tests/test_sales_reports_ui.py
```

Определить:

```text
1. Где сейчас задаётся default period.
2. Что происходит при отсутствии period/date_from/date_to.
3. Какие значения подставляются в поля формы.
4. Какие параметры Inventory передаёт в Core.
```

---

# 7. Required default date logic

Использовать текущую календарную дату runtime.

Python logic:

```python
from datetime import date

today = date.today()
default_date_from = date(today.year, 1, 1)
default_date_to = today
```

Требование:

```text
Не прописывать год вручную.
Не использовать фиксированную дату.
Каждый новый год default_date_from должен автоматически стать 1 января нового года.
```

Например:

```text
Если сегодня 2026-07-16:
date_from = 2026-01-01
date_to = 2026-07-16
```

---

# 8. Inventory UI route behavior

Для:

```text
GET /reports/sales
```

если отсутствуют все параметры:

```text
period
date_from
date_to
```

Inventory route должен установить:

```text
period = custom или None
date_from = 1 января текущего года
date_to = сегодня
```

И передать в Core:

```text
date_from=YYYY-01-01
date_to=YYYY-MM-DD
```

Не передавать одновременно конфликтующий:

```text
period=today
```

Предпочтительное правило приоритетов:

```text
1. Если есть date_from или date_to — custom dates имеют приоритет.
2. Если есть только period — использовать period.
3. Если нет ничего — default custom range 01.01 текущего года — сегодня.
```

---

# 9. Core API behavior

Core endpoint:

```text
GET /api/reports/sales
```

должен устойчиво поддерживать:

```text
date_from=YYYY-01-01
date_to=today
```

Можно также изменить default Core behavior:

```text
если нет period/date_from/date_to:
использовать year-to-date custom range
```

Это желательно, чтобы Core и UI имели одинаковый default.

Обязательное поведение:

```text
GET /api/reports/sales
```

возвращает:

```text
date_from = 1 января текущего года
date_to = сегодня
```

и данные за этот период.

---

# 10. Filter form values

На странице:

```text
http://127.0.0.1:8030/reports/sales
```

поля должны быть сразу заполнены:

```html
<input type="date" name="date_from" value="YYYY-01-01">
<input type="date" name="date_to" value="YYYY-MM-DD">
```

Заголовок/подпись периода должна показывать понятный диапазон:

```text
Период: 01.01.YYYY — DD.MM.YYYY
```

или эквивалентно.

---

# 11. Quick filters behavior

Кнопки должны остаться:

```text
Сегодня
Неделя
Месяц
Год
```

При нажатии:

```text
Сегодня → period=today
Неделя → period=week
Месяц → period=month
Год → period=year
```

После нажатия отчёт должен обновляться корректно.

При возврате на:

```text
/reports/sales
```

default снова:

```text
01.01 текущего года — сегодня
```

---

# 12. Empty custom form behavior

Если пользователь очистил обе даты и нажал «Применить»:

```text
не должно быть 500
```

Допустимое требуемое поведение:

```text
снова подставить default:
1 января текущего года — сегодня
```

То есть:

```text
date_from=""
date_to=""
```

нормализуются в default year-to-date range.

Если заполнена только одна дата:

```text
date_from заполнена, date_to пустая:
date_to = сегодня

date_from пустая, date_to заполнена:
date_from = 1 января года date_to
```

Не выдавать Internal Server Error.

---

# 13. Tests — Core

Обновить:

```text
core/tests/test_sales_reports.py
```

Добавить/проверить:

```text
1. GET /api/reports/sales without params returns 200.
2. Default date_from is January 1 of current year.
3. Default date_to is today.
4. Default report only includes sales from year start to today.
5. Empty date_from/date_to returns same year-to-date default.
6. date_from only uses date_to=today.
7. date_to only uses date_from=January 1 of date_to.year.
8. period=today still works.
9. period=week still works.
10. period=month still works.
11. period=year still works.
12. No default path returns 500.
```

Не использовать фиксированный текущий год в тестах.

Использовать:

```python
today = date.today()
expected_start = date(today.year, 1, 1)
```

---

# 14. Tests — Inventory

Обновить:

```text
inventory-sales-module/tests/test_sales_reports_ui.py
```

Добавить/проверить:

```text
1. /reports/sales returns 200.
2. CoreClient is called with date_from=January 1 current year.
3. CoreClient is called with date_to=today.
4. HTML date_from input contains YYYY-01-01.
5. HTML date_to input contains today's YYYY-MM-DD.
6. Page shows money summary for default range.
7. Empty date query does not 500 and restores defaults.
8. One-sided dates do not 500.
9. Quick period buttons remain.
10. period=today/week/month/year still return 200.
```

---

# 15. Fresh Docker rebuild

После изменений:

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose ps
```

---

# 16. Full regression

Обязательно:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Все должны пройти.

---

# 17. Runtime smoke

Получить текущую дату PowerShell:

```powershell
$today = Get-Date
$dateFrom = Get-Date -Year $today.Year -Month 1 -Day 1
$expectedFrom = $dateFrom.ToString("yyyy-MM-dd")
$expectedTo = $today.ToString("yyyy-MM-dd")

Write-Output "EXPECTED_FROM=$expectedFrom"
Write-Output "EXPECTED_TO=$expectedTo"
```

Проверить Core:

```powershell
$report = Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales"
$report | ConvertTo-Json -Depth 20

Write-Output "API_FROM=$($report.date_from)"
Write-Output "API_TO=$($report.date_to)"
```

Ожидаемо:

```text
API_FROM == EXPECTED_FROM
API_TO == EXPECTED_TO
```

Проверить UI:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/reports/sales" -UseBasicParsing -TimeoutSec 15
$page.StatusCode
$page.Content | Select-String "value=`"$expectedFrom`""
$page.Content | Select-String "value=`"$expectedTo`""
$page.Content | Select-String "Сводка денег за период"
```

Ожидаемо:

```text
200
оба значения дат найдены
сводка найдена
```

---

# 18. Filter smoke

Проверить:

```powershell
$urls = @(
    "http://127.0.0.1:8030/reports/sales",
    "http://127.0.0.1:8030/reports/sales?period=today",
    "http://127.0.0.1:8030/reports/sales?period=week",
    "http://127.0.0.1:8030/reports/sales?period=month",
    "http://127.0.0.1:8030/reports/sales?period=year",
    "http://127.0.0.1:8030/reports/sales?date_from=&date_to=",
    "http://127.0.0.1:8030/reports/sales?date_from=$expectedFrom&date_to=$expectedTo",
    "http://127.0.0.1:8030/reports/sales?date_from=$expectedFrom&date_to=",
    "http://127.0.0.1:8030/reports/sales?date_from=&date_to=$expectedTo"
)

foreach ($url in $urls) {
    try {
        $response = Invoke-WebRequest $url -UseBasicParsing -TimeoutSec 15
        Write-Output "$($response.StatusCode) $url"
    }
    catch {
        Write-Output "FAIL $url"
        Write-Output $_.Exception.Message
    }
}
```

Ожидаемо везде:

```text
200
```

---

# 19. Validate summary range

Проверить, что:

```text
money_summary
total_amount
sales
```

относятся именно к диапазону:

```text
1 января текущего года — сегодня
```

Не только поля формы, но и фактические данные API.

---

# 20. Safety scans

Выполнить:

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

# 21. Documentation and report

Создать:

```text
reports/stage04g_r2_default_year_to_date_period_report.md
docs/stage04g_r2_default_year_to_date_period.md
```

Обновить:

```text
logs/2026-07-16.md
```

Report structure:

```text
# Stage 04G-R2 Default Year-to-Date Period Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## OWNER_REQUIREMENT

## PREVIOUS_DEFAULT

## NEW_DEFAULT

date_from:
date_to:
mode:

## IMPLEMENTATION

### Core default

### Inventory route default

### Filter form values

### Empty and one-sided dates

### Quick period buttons

## TESTS

Core:
Inventory:
Avito:

## RUNTIME_SMOKE

Expected date_from:
Expected date_to:
Core date_from:
Core date_to:
UI date_from:
UI date_to:
Default status:
Quick filters:
Empty dates:
One-sided dates:

## SAFETY_SCAN

## FILES_CHANGED

## COMMIT

## PUSH

## FINAL_GIT_STATUS

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04G_R2_DEFAULT_YEAR_TO_DATE_PERIOD_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 22. Git

Использовать только targeted add.

Возможные файлы:

```powershell
git add core/app/routers/reports.py
git add core/tests/test_sales_reports.py

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/reports.py
git add inventory-sales-module/app/templates/reports_sales.html
git add inventory-sales-module/tests/test_sales_reports_ui.py

git add docs/stage04g_r2_default_year_to_date_period.md
git add reports/stage04g_r2_default_year_to_date_period_report.md
git add logs/2026-07-16.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04G_R2_DEFAULT_YEAR_TO_DATE_PERIOD_REPAIR_PROMPT.md
```

Коммит:

```powershell
git commit -m "Set default sales report period from year start to today"
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

Готово только если:

```text
/reports/sales default date_from is January 1 current year
/reports/sales default date_to is today
Core default response uses same dates
date input fields show same dates
money summary uses same period
sales table uses same period
empty dates restore same defaults
one-sided dates do not 500
quick filters still work
Core tests pass
Inventory tests pass
Avito tests pass
runtime smoke pass
safety scans clean
targeted commit
push
final git status clean
owner manual check still required
```

---

# 24. Final answer required from agent

Финальный ответ должен быть подробным.

Обязательно указать:

```text
текущую фактическую дату проверки
какой date_from установлен
какой date_to установлен
что вернул Core
что показал UI
результаты всех тестов
commit hash
push result
final git status
```

Успешный статус:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_R2_DEFAULT_YEAR_TO_DATE_PERIOD_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если проблема осталась:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_R2_DEFAULT_YEAR_TO_DATE_PERIOD_FAIL

BLOCKERS:
...
```
