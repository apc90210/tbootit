# PROMPT — Техноребут / Stage 04G-S Finalization Audit & Commit

## Роль агента

Ты senior release engineer, QA auditor, FastAPI/Jinja2 reviewer и Git hygiene engineer проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — финализировать Stage 04G-S Daily Money Summary Refinement после реализации дневной/месячной верхней денежной сводки.

Это не новый функционал. Это finalization/audit/commit этап.

---

# 1. Почему нужен этот этап

Предыдущий исполнитель сообщил:

```text
Stage 04G-S implementation completed
core tests pass: 77
inventory-sales-module tests pass: 56
worktree has uncommitted functional changes
avito-module pytest not shown
docs/report not created
commit/push not done
```

Также была ошибка в понимании правил:

```text
"strict repository instruction forbidding me from adding or committing files"
```

Это неверно.

Запрещены только:

```text
git add .
git add -A
git add -u
git commit --amend
git reset / git clean / rebase / force push
```

Разрешены и обязательны для готовности этапа:

```text
targeted git add
normal git commit
normal git push
```

Пока изменения не закоммичены и не запушены, owner manual recheck невозможен.

---

# 2. Заявленные изменения Stage04G-S

Проверить и финализировать:

```text
core/app/schemas.py
core/app/routers/reports.py
inventory-sales-module/app/templates/reports_sales.html
core/tests/test_sales_reports.py
inventory-sales-module/tests/test_sales_reports_ui.py
logs/2026-07-10.md
```

Заявлено:

```text
1. Core API добавил money_summary_rows.
2. Core API добавил money_summary_total.
3. Core API добавил money_summary_granularity.
4. today возвращает 1 строку.
5. week возвращает 7 строк по дням.
6. month возвращает строки по дням месяца.
7. custom возвращает строки по дням периода.
8. year возвращает 12 строк по месяцам.
9. UI верхней таблицы показывает rows и footer total.
```

---

# 3. Целевой статус

Текущий статус:

```text
STAGE04G_S_IMPLEMENTED_BUT_UNCOMMITTED_AND_NOT_FULLY_FINALIZED
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04G_S_FINALIZED_READY_FOR_OWNER_RECHECK
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
начинать следующий этап
делать новый функционал
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset / git clean / rebase / force push
коммитить runtime DB/temp/cache
делать Base.metadata.drop_all/create_all
делать direct DB access из inventory-sales-module
```

Разрешено:

```text
точечный bugfix, если regression выявит ошибку
создать report/doc
обновить log
targeted commit
обычный git push, если remote существует
```

---

# 5. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04G_S_FINALIZATION_AUDIT_COMMIT_PROMPT.md
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

# 6. Preflight

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -10
git diff --name-status
git diff --stat
git diff -- core/app/schemas.py core/app/routers/reports.py core/tests/test_sales_reports.py
git diff -- inventory-sales-module/app/templates/reports_sales.html inventory-sales-module/tests/test_sales_reports_ui.py
git diff -- logs/2026-07-10.md
docker compose ps
```

Проверить:

```text
1. Какие файлы изменены.
2. Нет ли лишних temp/runtime файлов.
3. Нет ли accidental changes вне Stage04G-S.
4. Нет ли staged changes от предыдущего агента.
```

Если есть staged changes:

```powershell
git diff --cached --name-status
git diff --cached --stat
```

Не сбрасывать staged changes. Проверить их и продолжить targeted commit, если корректны.

---

# 7. Code review checklist

## Core API

Проверить:

```text
core/app/schemas.py
core/app/routers/reports.py
```

Обязательно:

```text
1. SalesReportResponse содержит:
   - money_summary
   - money_summary_rows
   - money_summary_total
   - money_summary_granularity

2. Для today:
   - money_summary_rows length = 1
   - granularity = day

3. Для week:
   - money_summary_rows length = 7
   - строки идут по дням недели
   - есть нулевые дни, если продаж нет

4. Для month:
   - rows count = количество дней в месяце

5. Для custom:
   - rows count = количество дней date_from..date_to inclusive

6. Для year:
   - rows count = 12
   - granularity = month

7. row.total = сумма каналов:
   cash + card + transfer + sbp + legal_entity_account + other + unspecified

8. money_summary_total = сумма всех rows

9. old money_summary remains compatible with money_summary_total

10. Нет 500 на пустых date_from/date_to.
```

## UI

Проверить:

```text
inventory-sales-module/app/templates/reports_sales.html
```

Обязательно:

```text
1. Верхняя таблица находится до детальной таблицы продаж.
2. Колонки:
   - Дата / Период
   - Наличные
   - Безнал / карта
   - Перевод
   - СБП
   - Счёт юрлица
   - Другое
   - Не указано
   - Итого
3. Есть footer:
   - Итого за период / неделю / месяц / год
4. Детальная таблица продаж осталась ниже.
5. Нет сырых значений payment_method.
```

---

# 8. Required full tests

Обязательно выполнить:

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose ps

docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Если любой тест падает:

```text
исправить точечно
повторить полный regression
```

---

# 9. Manual smoke

Проверить UI:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=today" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=week" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=month" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=year" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?date_from=&date_to=" -TimeoutSec 15 | Select-Object StatusCode
```

Все должны вернуть:

```text
200
```

Проверить Core rows:

```powershell
$r = Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=week"
$r.money_summary_rows.Count
$r.money_summary_granularity
$r.money_summary_total | ConvertTo-Json -Depth 5

$r = Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=year"
$r.money_summary_rows.Count
$r.money_summary_granularity
```

Ожидаемо:

```text
week rows = 7
week granularity = day
year rows = 12
year granularity = month
```

Проверить HTML:

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

# 10. Safety scans

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

All should be clean.

---

# 11. Docs/report/log

Создать/обновить:

```text
reports/stage04g_s_finalization_audit_commit_report.md
docs/stage04g_s_daily_money_summary_refinement.md
logs/2026-07-10.md
```

Report structure:

```text
# Stage 04G-S Finalization Audit & Commit Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## REASON

## PROMPT_DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## PRE_COMMIT_STATE

Branch:
HEAD:
Dirty files:
Untracked files:
Staged files:

## CODE_REVIEW

Core API:
UI top table:
Compatibility:
No filter 500:

## API_VERIFICATION

today:
week:
month:
year:
custom:
empty dates:

## MONEY_SUMMARY_ROWS

Today rows:
Week rows:
Month rows:
Year rows:
Custom rows:
Total row:

## TESTS

Core:
Inventory:
Avito:

## MANUAL_SMOKE

/reports/sales today:
week:
month:
year:
empty dates:

## SAFETY_SCAN

Runtime tracked:
Direct DB access:
Destructive DB calls:
Secrets:

## FILES_COMMITTED

## PUSH_STATUS

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04G_S_FINALIZED_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 12. Git

Use targeted add only.

Possible files:

```powershell
git add core/app/routers/reports.py
git add core/app/schemas.py
git add core/tests/test_sales_reports.py

git add inventory-sales-module/app/templates/reports_sales.html
git add inventory-sales-module/tests/test_sales_reports_ui.py

git add docs/stage04g_s_daily_money_summary_refinement.md
git add reports/stage04g_s_finalization_audit_commit_report.md
git add logs/2026-07-10.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04G_S_FINALIZATION_AUDIT_COMMIT_PROMPT.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04G_S_DAILY_MONEY_SUMMARY_REFINEMENT_PROMPT.md

git commit -m "Finalize Stage 04G S daily money summary refinement"
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

# 13. Definition of Done

Готово, если:

```text
all uncommitted Stage04G-S changes reviewed
today rows = 1
week rows = 7
month rows = days in month
year rows = 12
custom rows = inclusive day count
UI top table renders rows and totals
detailed sales table remains below
no filter 500
full core pytest PASS
full inventory-sales-module pytest PASS
full avito-module pytest PASS
safety scans clean
report created
targeted commit created
push done
final git status clean
READY_FOR_OWNER_RECHECK
```

---

# 14. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_S_FINALIZED_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_S_FINALIZATION_FAIL

BLOCKERS:
...
```
