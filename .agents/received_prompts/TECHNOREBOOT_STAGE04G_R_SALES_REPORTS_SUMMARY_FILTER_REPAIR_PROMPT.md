# PROMPT — Техноребут / Stage 04G-R Sales Reports Summary Table and Filter Error Repair

## Роль агента

Ты senior fullstack bugfix engineer, FastAPI reporting engineer, Jinja2 UI developer, QA regression engineer и release auditor проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — исправить owner-check blockers после Stage04G: нужна компактная денежная сводная таблица сверху отчёта и нужно устранить `Internal Server Error` при работе фильтра отчёта.

Это repair-этап Stage04G, не новый функциональный этап.

---

# 1. Owner-reported fail

Владелец сообщил:

```text
в отчете нужна маленкая сводная таблица сверху
за период только деньги,
отдельно приход нал безнал перевод и т д и общая сумма.
ошибка Internal Server Error при работе фильтра
```

Интерпретация:

```text
1. В отчёте продаж сверху должна быть компактная сводная таблица по деньгам за выбранный период.
2. В этой таблице не нужны товары/кол-во — только деньги.
3. Нужны отдельные колонки/строки по способам поступления денег:
   - Наличные
   - Безнал / карта / эквайринг
   - Перевод
   - СБП
   - Счёт юрлица
   - Другое
   - Не указано
   - Итого
4. При использовании фильтра отчёта возникает Internal Server Error.
```

---

# 2. Target status

Текущий статус:

```text
STAGE04G_OWNER_CHECK_FAILED_SUMMARY_TABLE_AND_FILTER_500
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04G_R_SALES_REPORTS_SUMMARY_FILTER_REPAIR_READY_FOR_OWNER_RECHECK
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
делать новый функционал вне ремонта Stage04G
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
точечный bugfix Core reports API
точечный bugfix Inventory reports UI/router/CoreClient
добавить денежную summary table
tests
report/log
targeted commit
normal push
```

---

# 4. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04G_R_SALES_REPORTS_SUMMARY_FILTER_REPAIR_PROMPT.md
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

# 6. Reproduce Internal Server Error

Проверить UI:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=today" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=week" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=month" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=year" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?date_from=&date_to=" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?date_from=2026-07-01&date_to=2026-07-03" -TimeoutSec 15 | Select-Object StatusCode
```

Проверить Core API:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=today" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=week" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=month" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=year" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?date_from=&date_to=" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?date_from=2026-07-01&date_to=2026-07-03" | ConvertTo-Json -Depth 10
```

Снять логи:

```powershell
docker compose logs --tail 100 core
docker compose logs --tail 100 inventory-sales-module
```

В report указать точный root cause.

Вероятные причины:

```text
1. Пустые date_from/date_to передаются как "" и падает date parsing.
2. period не нормализуется.
3. date_from/date_to в UI уходят пустыми параметрами.
4. Jinja template ожидает поле, которого нет в API response.
5. payment_breakdown имеет иной формат, чем ожидает template.
6. старые продажи имеют payment_method=None и ломают grouping/labeling.
```

---

# 7. Fix A — robust report query params

Исправить Core `/api/reports/sales` и Inventory `/reports/sales`.

Требования:

```text
1. Empty strings from query params must be treated as None.
2. period default = today or current month — выбрать и явно указать в UI.
3. date_from/date_to:
   - если оба пустые — использовать period;
   - если один пустой — не падать, либо подставить второй, либо показать понятную ошибку;
   - invalid date не должен давать 500, должен дать понятную validation error или UI message.
4. UI must never show Internal Server Error for normal filter use.
```

Рекомендуемая утилита:

```python
def clean_param(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None
```

Для дат:

```python
def parse_date_or_none(value):
    value = clean_param(value)
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректная дата")
```

Inventory CoreClient должен удалять пустые параметры перед запросом в Core.

---

# 8. Fix B — compact money summary table on top

На странице:

```text
/reports/sales
```

сразу сверху после заголовка/фильтра или перед таблицей продаж добавить компактную сводную таблицу.

Название:

```text
Сводка денег за период
```

Структура минимум:

```text
| Наличные | Безнал / карта | Перевод | СБП | Счёт юрлица | Другое | Не указано | Итого |
| 1 000 ₽  | 2 000 ₽        | 0 ₽     | 500 ₽ | 3 000 ₽    | 0 ₽    | 0 ₽        | 6 500 ₽ |
```

Можно сделать вертикально, если так проще:

```text
Способ поступления | Сумма
Наличные          | ...
Безнал / карта    | ...
Перевод           | ...
СБП               | ...
Счёт юрлица       | ...
Другое            | ...
Не указано        | ...
Итого             | ...
```

Owner просит "маленькая сводная таблица сверху" — компактнее лучше горизонтальная или небольшая вертикальная.

Обязательно:

```text
1. Таблица должна быть сверху, до списка продаж.
2. Только деньги, без товаров/количества.
3. Итого должно равняться общей сумме продаж за период.
4. "Счёт юрлица" должен быть отдельной строкой/колонкой.
```

---

# 9. Fix C — API response should support summary table

Core API должен вернуть удобную структуру.

Можно добавить поле:

```json
"money_summary": {
  "cash": 1000,
  "card": 2000,
  "transfer": 0,
  "sbp": 500,
  "legal_entity_account": 3000,
  "other": 0,
  "unspecified": 0,
  "total": 6500
}
```

И labels:

```json
"payment_labels": {
  "cash": "Наличные",
  "card": "Безнал / карта",
  "transfer": "Перевод",
  "sbp": "СБП",
  "legal_entity_account": "Счёт юрлица",
  "other": "Другое",
  "unspecified": "Не указано"
}
```

Если уже есть `payment_breakdown`, можно оставить его, но UI summary table должна быть стабильной и показывать все категории даже с нулём.

---

# 10. Payment method normalization

Нужно нормализовать способы оплаты:

```text
cash → Наличные
card → Безнал / карта
bank_card → Безнал / карта
acquiring → Безнал / карта
transfer → Перевод
sbp → СБП
legal_entity_account → Счёт юрлица
other → Другое
None / "" / unknown → Не указано
```

В отчёте не должно быть сырых значений типа:

```text
legal_entity_account
None
""
```

---

# 11. Tests — Core

Добавить/обновить:

```text
core/tests/test_sales_reports.py
```

Покрыть:

```text
1. /api/reports/sales?period=today does not 500.
2. /api/reports/sales?period=week does not 500.
3. /api/reports/sales?period=month does not 500.
4. /api/reports/sales?period=year does not 500.
5. /api/reports/sales?date_from=&date_to= does not 500.
6. /api/reports/sales?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD works.
7. invalid date returns 400/422, not 500.
8. money_summary contains all keys:
   cash, card, transfer, sbp, legal_entity_account, other, unspecified, total.
9. total equals sum of categories.
10. legal_entity_account sale is counted under "Счёт юрлица".
11. None/blank payment_method goes to unspecified.
```

---

# 12. Tests — Inventory

Добавить/обновить:

```text
inventory-sales-module/tests/test_sales_reports_ui.py
inventory-sales-module/tests/test_sales_payment_channels_ui.py
```

Покрыть:

```text
1. /reports/sales opens 200.
2. /reports/sales?period=today opens 200.
3. /reports/sales?period=week opens 200.
4. /reports/sales?period=year opens 200.
5. /reports/sales?date_from=&date_to= opens 200, no Internal Server Error.
6. /reports/sales?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD opens 200.
7. Page contains "Сводка денег за период".
8. Page contains "Наличные".
9. Page contains "Безнал / карта".
10. Page contains "Перевод".
11. Page contains "СБП".
12. Page contains "Счёт юрлица".
13. Page contains "Итого".
14. Summary table is before detailed sales table.
15. Invalid Core response does not crash template; shows safe empty summary or error message.
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
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=today" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=week" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?period=year" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/reports/sales?date_from=&date_to=" -TimeoutSec 15 | Select-Object StatusCode
```

All expected:

```text
200
```

Check summary table content:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/reports/sales" -TimeoutSec 15
$page.Content | Select-String "Сводка денег за период"
$page.Content | Select-String "Наличные"
$page.Content | Select-String "Безнал"
$page.Content | Select-String "Перевод"
$page.Content | Select-String "СБП"
$page.Content | Select-String "Счёт юрлица"
$page.Content | Select-String "Итого"
```

Check Core:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?period=today" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/reports/sales?date_from=&date_to=" | ConvertTo-Json -Depth 10
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
reports/stage04g_r_sales_reports_summary_filter_repair_report.md
docs/stage04g_r_sales_reports_summary_filter_repair.md
```

Update:

```text
logs/2026-07-03.md
```

Report structure:

```text
# Stage 04G-R Sales Reports Summary Table and Filter Repair Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## OWNER_REPORTED_FAIL

## ROOT_CAUSE

Internal Server Error:
Missing compact money table:

## FIXES

### Report filter 500 repair

### Query params sanitization

### Money summary table

### Payment method normalization

## MONEY_SUMMARY_FIELDS

cash:
card:
transfer:
sbp:
legal_entity_account:
other:
unspecified:
total:

## TESTS

Core:
Inventory:
Avito:

## MANUAL_SMOKE

/reports/sales:
period filters:
empty date filters:
custom date filters:
summary table:

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

TECHNOREBOOT_STAGE04G_R_SALES_REPORTS_SUMMARY_FILTER_REPAIR_READY_FOR_OWNER_RECHECK
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

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/reports.py
git add inventory-sales-module/app/templates/reports_sales.html
git add inventory-sales-module/tests/test_sales_reports_ui.py
git add inventory-sales-module/tests/test_sales_payment_channels_ui.py

git add docs/stage04g_r_sales_reports_summary_filter_repair.md
git add reports/stage04g_r_sales_reports_summary_filter_repair_report.md
git add logs/2026-07-03.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04G_R_SALES_REPORTS_SUMMARY_FILTER_REPAIR_PROMPT.md

git commit -m "Repair Stage 04G sales report filters and summary table"
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
/reports/sales no 500
period filters no 500
empty date filters no 500
custom date filters no 500
compact money summary table appears at top
summary table includes cash/card/transfer/sbp/legal_entity_account/other/unspecified/total
Итого equals sum of payment categories
sales table still visible below
Core/inventory/avito tests pass
safety scans clean
targeted commit
push
READY_FOR_OWNER_RECHECK
```

---

# 19. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_R_SALES_REPORTS_SUMMARY_FILTER_REPAIR_READY_FOR_OWNER_RECHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04G_R_SALES_REPORTS_SUMMARY_FILTER_REPAIR_FAIL

BLOCKERS:
...
```
