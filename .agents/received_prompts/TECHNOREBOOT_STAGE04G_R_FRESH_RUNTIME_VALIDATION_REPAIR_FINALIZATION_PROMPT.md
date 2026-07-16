# PROMPT — Техноребут / Stage 04G-R Fresh Runtime Validation, Repair and Finalization

## Роль агента

Ты senior fullstack engineer, FastAPI/Jinja2 debugger, Docker runtime auditor, QA engineer и release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — не читать старые отчёты вместо работы, а выполнить свежую фактическую проверку Stage04G-R на текущем коде и текущем Docker runtime.

Если проблема существует — исправить её.
Если код уже исправлен — доказать это свежими командами, тестами и runtime smoke.
После этого привести Git в чистое состояние, сделать targeted commit/push при наличии изменений и выдать подробный отчёт в чат.

---

# 1. Критическое замечание

Предыдущий агент сделал только следующее:

```text
прочитал старый commit dc0f401
прочитал старый report
создал logs/2026-07-16.md
объявил READY_FOR_OWNER_RECHECK
```

Это не является свежей проверкой.

Нельзя завершать задачу только на основании:

```text
старого отчёта
старого коммита
предыдущих результатов pytest
предыдущих smoke tests
```

Обязательно выполнить команды заново в текущем runtime.

---

# 2. Owner-reported requirements

Владелец требует:

```text
1. В отчёте сверху должна быть маленькая сводная таблица только по деньгам за выбранный период.

2. В ней отдельно:
   - Наличные
   - Безнал / карта
   - Перевод
   - СБП
   - Счёт юрлица
   - Другое
   - Не указано
   - Итого

3. При работе фильтра отчёта не должно быть Internal Server Error.

4. Фильтры должны работать:
   - Сегодня
   - Неделя
   - Месяц
   - Год
   - произвольные даты
   - пустые даты
```

---

# 3. Текущий статус

Считать текущим статусом:

```text
STAGE04G_R_FRESH_RUNTIME_VALIDATION_REQUIRED
```

Не считать задачу принятой.

Целевой статус:

```text
TECHNOREBOOT_STAGE04G_R_FRESH_RUNTIME_VALIDATED_READY_FOR_OWNER_RECHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 4. Строгие запреты

Запрещено:

```text
завершать задачу только чтением старого отчёта
завершать задачу без docker rebuild
завершать задачу без свежих pytest
завершать задачу без проверки runtime URL
начинать следующий этап
делать direct DB access из inventory-sales-module
создавать отдельную DB для отчётов
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
скрывать ошибку 500 только DEFAULT_REPORT_DATA без исправления первопричины
```

Разрешено:

```text
свежая runtime проверка
точечный repair Core reports API
точечный repair Inventory reports router/CoreClient/template
tests
docs/report/log
targeted commit
normal push
```

---

# 5. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04G_R_FRESH_RUNTIME_VALIDATION_REPAIR_FINALIZATION_PROMPT.md
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

Если prompt найден в Downloads — скопировать его в:

```text
C:\tbootit\.agents\received_prompts\
```

В итоговом отчёте указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 6. Preflight

Выполнить именно сейчас:

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

Зафиксировать вывод в отчёте.

Особенно проверить:

```text
logs/2026-07-16.md
```

Если файл создан предыдущим агентом и не закоммичен:

```text
не удалять
проверить содержание
доработать свежими результатами этой проверки
потом включить targeted add
```

---

# 7. Inspect implementation

Проверить текущий код:

```powershell
Get-Content core/app/routers/reports.py
Get-Content inventory-sales-module/app/routers/reports.py
Get-Content inventory-sales-module/app/core_client.py
Get-Content inventory-sales-module/app/templates/reports_sales.html
Get-Content core/tests/test_sales_reports.py
Get-Content inventory-sales-module/tests/test_sales_reports_ui.py
```

Проверить наличие:

```text
clean_param
date parsing
money_summary
payment_labels
DEFAULT_REPORT_DATA
compact summary table
```

Проверить, что таблица находится до подробного списка продаж.

---

# 8. Mandatory fresh Docker rebuild

Обязательно выполнить:

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose ps
```

После запуска дождаться готовности сервисов.

Проверить health:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8030/health" | ConvertTo-Json -Depth 10
```

Если endpoint другой — найти корректный health endpoint.

---

# 9. Fresh full regression tests

Обязательно выполнить заново:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Нельзя ссылаться на старые количества тестов.

В отчёте указать свежие результаты:

```text
Core:
Inventory:
Avito:
```

Если любой test FAIL:

```text
исправить
пересобрать нужные контейнеры
перезапустить полный regression
```

---

# 10. Fresh Core API smoke

Проверить все варианты фильтра:

```powershell
$coreUrls = @(
    "http://127.0.0.1:8000/api/reports/sales",
    "http://127.0.0.1:8000/api/reports/sales?period=today",
    "http://127.0.0.1:8000/api/reports/sales?period=week",
    "http://127.0.0.1:8000/api/reports/sales?period=month",
    "http://127.0.0.1:8000/api/reports/sales?period=year",
    "http://127.0.0.1:8000/api/reports/sales?date_from=&date_to=",
    "http://127.0.0.1:8000/api/reports/sales?date_from=2026-07-01&date_to=2026-07-16",
    "http://127.0.0.1:8000/api/reports/sales?period=unknown"
)

foreach ($url in $coreUrls) {
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

Ожидаемо:

```text
обычные фильтры: 200
пустые даты: 200
custom dates: 200
unknown period: либо 200 fallback, либо корректный 400/422, но не 500
```

Проверить JSON:

```powershell
$report = Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=today"
$report | ConvertTo-Json -Depth 20
```

В JSON должны быть:

```text
money_summary
payment_labels
sales
total_amount
```

Проверить обязательные ключи:

```powershell
$report.money_summary
```

Ожидаемые поля:

```text
cash
card
transfer
sbp
legal_entity_account
other
unspecified
total
```

---

# 11. Fresh Inventory UI smoke

Проверить все URL:

```powershell
$uiUrls = @(
    "http://127.0.0.1:8030/reports/sales",
    "http://127.0.0.1:8030/reports/sales?period=today",
    "http://127.0.0.1:8030/reports/sales?period=week",
    "http://127.0.0.1:8030/reports/sales?period=month",
    "http://127.0.0.1:8030/reports/sales?period=year",
    "http://127.0.0.1:8030/reports/sales?date_from=&date_to=",
    "http://127.0.0.1:8030/reports/sales?date_from=2026-07-01&date_to=2026-07-16"
)

foreach ($url in $uiUrls) {
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

Если где-то:

```text
500
Internal Server Error
```

сразу снять логи:

```powershell
docker compose logs --tail 200 core
docker compose logs --tail 200 inventory-sales-module
```

Найти точную первопричину и исправить.

---

# 12. Validate compact summary table

Получить HTML:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=today" -UseBasicParsing -TimeoutSec 15
$html = $page.Content
```

Проверить:

```powershell
$html | Select-String "Сводка денег за период"
$html | Select-String "Наличные"
$html | Select-String "Безнал"
$html | Select-String "Перевод"
$html | Select-String "СБП"
$html | Select-String "Счёт юрлица"
$html | Select-String "Другое"
$html | Select-String "Не указано"
$html | Select-String "Итого"
```

Все строки должны находиться.

Проверить порядок:

```text
Сводка денег за период
должна располагаться выше подробной таблицы продаж.
```

Проверить, что сводная таблица содержит только деньги, а не количество товаров.

---

# 13. Verify totals

Через API проверить:

```powershell
$report = Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=today"

$calculated = `
    [decimal]$report.money_summary.cash +
    [decimal]$report.money_summary.card +
    [decimal]$report.money_summary.transfer +
    [decimal]$report.money_summary.sbp +
    [decimal]$report.money_summary.legal_entity_account +
    [decimal]$report.money_summary.other +
    [decimal]$report.money_summary.unspecified

Write-Output "CALCULATED=$calculated"
Write-Output "TOTAL=$($report.money_summary.total)"
Write-Output "REPORT_TOTAL=$($report.total_amount)"
```

Должно выполняться:

```text
CALCULATED == money_summary.total
money_summary.total == report.total_amount
```

Если нет — исправить агрегацию.

---

# 14. Payment normalization

Проверить normalization:

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

Не должно быть сырых значений в UI:

```text
legal_entity_account
bank_card
None
unspecified
```

---

# 15. Fix requirements if runtime fails

Если найден 500, исправлять первопричину.

Вероятные точки:

```text
core/app/routers/reports.py
inventory-sales-module/app/core_client.py
inventory-sales-module/app/routers/reports.py
inventory-sales-module/app/templates/reports_sales.html
```

Обязательное поведение:

```text
1. Пустые query params превращаются в None.
2. Пустые даты не передаются в Core.
3. Неверная дата не вызывает 500.
4. Jinja template получает полную стабильную структуру.
5. DEFAULT_REPORT_DATA содержит:
   - money_summary
   - payment_labels
   - sales
   - total_amount
6. При ошибке Core UI показывает понятное сообщение, но не Internal Server Error.
7. Fallback не должен скрывать системную ошибку в отчёте агента.
```

---

# 16. Required tests if a fix is made

Core:

```text
core/tests/test_sales_reports.py
```

Проверить/добавить:

```text
period=today → 200
period=week → 200
period=month → 200
period=year → 200
empty date_from/date_to → 200
custom dates → 200
invalid date → 400/422, not 500
unknown period → controlled response, not 500
money_summary has all required keys
total equals sum of payment groups
```

Inventory:

```text
inventory-sales-module/tests/test_sales_reports_ui.py
```

Проверить/добавить:

```text
all period filters → 200
empty dates → 200
custom dates → 200
template with Core error → no Jinja crash
summary table visible
summary before sales table
all payment labels visible
```

После изменений снова обязательно выполнить полный regression всех трёх модулей.

---

# 17. Fresh safety scans

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

Ожидаемо:

```text
runtime DB not tracked
no direct DB access in inventory
no destructive DB calls
no secrets
```

---

# 18. Documentation and log

Создать или обновить:

```text
reports/stage04g_r_fresh_runtime_validation_repair_finalization_report.md
docs/stage04g_r_fresh_runtime_validation_repair_finalization.md
logs/2026-07-16.md
```

Файл `logs/2026-07-16.md`, созданный предыдущим агентом, использовать как текущий лог и дополнить реальными командами.

Report structure:

```text
# Stage 04G-R Fresh Runtime Validation, Repair and Finalization Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## PREVIOUS_AGENT_GAP

## PREFLIGHT

Branch:
HEAD:
Initial git status:

## DOCKER_REBUILD

Command:
Result:
Container status:

## FRESH_TESTS

Core:
Inventory:
Avito:

## CORE_API_SMOKE

default:
today:
week:
month:
year:
empty dates:
custom dates:
unknown period:

## UI_SMOKE

default:
today:
week:
month:
year:
empty dates:
custom dates:

## SUMMARY_TABLE

Title:
Labels:
Position:
Only money:
Legal entity account:

## TOTAL_VALIDATION

Calculated:
Money summary total:
Report total:
Match:

## ROOT_CAUSE

Only if a bug was reproduced.

## FIXES

Only if code was changed.

## SAFETY_SCAN

Runtime tracked:
Direct DB access:
Destructive DB:
Secrets:

## FILES_CHANGED

## COMMIT

## PUSH

## FINAL_GIT_STATUS

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04G_R_FRESH_RUNTIME_VALIDATED_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 19. Git finalization

Сначала проверить:

```powershell
git status --short --untracked-files=all
git diff --name-status
git diff --stat
```

Использовать только targeted add.

Возможные файлы:

```powershell
git add core/app/routers/reports.py
git add core/app/schemas.py
git add core/tests/test_sales_reports.py

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/reports.py
git add inventory-sales-module/app/templates/reports_sales.html
git add inventory-sales-module/tests/test_sales_reports_ui.py
git add inventory-sales-module/tests/test_sales_payment_channels_ui.py

git add docs/stage04g_r_fresh_runtime_validation_repair_finalization.md
git add reports/stage04g_r_fresh_runtime_validation_repair_finalization_report.md
git add logs/2026-07-16.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04G_R_FRESH_RUNTIME_VALIDATION_REPAIR_FINALIZATION_PROMPT.md
```

Если были изменения:

```powershell
git commit -m "Finalize Stage 04G-R runtime validation and report filters"
git push
```

Если код не изменён, но созданы report/docs/log/prompt:

```powershell
git commit -m "Validate Stage 04G-R runtime and finalize reports"
git push
```

После push обязательно:

```powershell
git status --short --untracked-files=all
git rev-parse HEAD
git log --oneline -3
```

Финальный `git status` должен быть пустым.

---

# 20. Definition of Done

Готово только если:

```text
fresh Docker rebuild executed
fresh Core pytest PASS
fresh Inventory pytest PASS
fresh Avito pytest PASS
all Core report URLs checked now
all UI report URLs checked now
no Internal Server Error
empty dates no 500
custom dates no 500
compact money summary visible at top
cash/card/transfer/sbp/legal entity/other/unspecified/total visible
summary contains only money
total mathematically verified
safety scans clean
report/docs/log updated
targeted commit created
push completed
final git status clean
owner manual check still required
```

---

# 21. Final answer required from agent

Финальный ответ в чат должен быть подробным.

Не писать только сухой статус.

Обязательно указать:

```text
что реально выполнено сейчас
какие команды выполнены
какие URL проверены
результаты свежих тестов
был ли воспроизведён 500
точную первопричину, если был
что исправлено
commit hash
push result
final git status
инструкцию владельцу
```

Успешный финальный статус:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_R_FRESH_RUNTIME_VALIDATED_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

При любой нерешённой проблеме:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_R_FRESH_RUNTIME_VALIDATION_FAIL

BLOCKERS:
...
```
