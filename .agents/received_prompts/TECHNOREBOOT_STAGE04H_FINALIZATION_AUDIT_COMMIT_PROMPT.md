# PROMPT — Техноребут / Stage 04H Finalization Audit & Commit

## Роль агента

Ты senior release engineer, QA auditor, FastAPI/Jinja2 reviewer, inventory workflow auditor и Git hygiene engineer проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — финализировать Stage 04H после неполной реализации: проверить все незакоммиченные изменения, прогнать полный regression, создать docs/report, сделать targeted commit и push.

Это не новый функционал. Это finalization/audit/commit этап.

---

# 1. Почему нужен этот этап

Предыдущий исполнитель сообщил, что Stage04H реализован, но финальное состояние неприемлемо для owner manual check:

```text
worktree clean true/false: false
committed files: None yet
tests run and results: 81 tests PASSED
```

Проблемы:

```text
1. Функциональные изменения не закоммичены.
2. Проверены только core tests.
3. inventory-sales-module pytest не подтверждён.
4. avito-module pytest не подтверждён.
5. docs/report в репозитории не созданы.
6. commit/push не сделаны.
7. implementation_plan.md и walkthrough.md созданы в Antigravity brain path, а не как проектные docs/reports.
```

Пока изменения не закоммичены и не запушены, Stage04H нельзя отдавать владельцу на ручную проверку.

---

# 2. Что заявлено как реализованное

Проверить и финализировать заявленный Stage04H scope:

## Product Locations

```text
storage_location:
- store = Магазин
- workshop = Мастерская
- archive = Архив
- draft = Черновик
```

Заявлено:

```text
1. Добавлены location filters в /products.
2. Добавлена ручная правка location в product detail.
3. Добавлена ручная правка quantity в product detail.
4. Продавать можно только location=store.
```

## Sale Cancel / Reissue

Заявлено:

```text
1. Отмена продажи возвращает stock.
2. Переоформление возвращает старый stock и создаёт новую продажу.
3. Отменённые и переоформленные продажи исключаются из reports.
4. Добавлены UI кнопки Cancel/Reissue.
```

---

# 3. Целевой статус

Текущий статус:

```text
STAGE04H_IMPLEMENTED_BUT_UNCOMMITTED_AND_NOT_FULLY_TESTED
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04H_FINALIZED_READY_FOR_OWNER_CHECK
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
делать новый функционал вне финализации Stage04H
использовать git add .
использовать git add -A
использовать git add -u
использовать git commit --amend
использовать git reset / git clean / rebase / force push
коммитить runtime DB/temp/cache
делать Base.metadata.drop_all/create_all
делать direct DB access из inventory-sales-module
бесследно переписывать completed sales без status/audit/history
```

Разрешено:

```text
точечный bugfix, если regression выявит ошибку
создать report/doc в репозитории
обновить log
targeted commit
обычный git push
```

---

# 5. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04H_FINALIZATION_AUDIT_COMMIT_PROMPT.md
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

# 6. Preflight — обязательно

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -10
git diff --name-status
git diff --stat
git diff --cached --name-status
git diff --cached --stat
docker compose ps
```

В report зафиксировать:

```text
Branch:
HEAD before commit:
Dirty files:
Untracked files:
Staged files:
```

Если есть файлы вне Stage04H — не коммитить их без анализа.

---

# 7. Code review checklist

Проверить все изменённые файлы.

Ожидаемые группы изменений:

## Core

```text
core/app/models.py
core/app/schemas.py
core/app/routers/products.py
core/app/routers/sales.py
core/app/routers/reports.py
core/tests/test_product_locations_and_quantity.py
core/tests/test_sales_cancel_reissue.py
core/tests/test_sales_reports.py
core/tests/test_sales_flow.py
core/tests/test_sales_warranty.py
```

Проверить:

```text
1. Product location validation.
2. Product quantity validation.
3. No negative quantity.
4. Sale creation deducts quantity correctly.
5. Cancel returns quantity.
6. Reissue returns old quantity and deducts new quantity.
7. Sale statuses:
   - completed
   - canceled
   - superseded
8. Reports include only active completed sales.
9. Backward compatibility:
   - old products without location default to store;
   - old products without quantity default safe;
   - old sales without status treated as completed.
```

## Inventory-sales-module

```text
inventory-sales-module/app/core_client.py
inventory-sales-module/app/routers/products.py
inventory-sales-module/app/routers/sales.py
inventory-sales-module/app/templates/products.html
inventory-sales-module/app/templates/product_detail.html
inventory-sales-module/app/templates/sales_detail.html
inventory-sales-module/app/templates/sales_reissue.html
inventory-sales-module/app/templates/reports_sales.html
```

Проверить:

```text
1. No direct DB access.
2. /products has big filter buttons:
   - Магазин
   - Мастерская
   - Архив
   - Черновик
   - Все
3. /products?location=store/workshop/archive/draft works.
4. product detail can update location.
5. product detail can update quantity.
6. sale detail has cancel and reissue actions.
7. reissue form works via Core API.
8. reports page still opens.
```

---

# 8. Full tests — обязательно

Сначала rebuild:

```powershell
docker compose up --build -d --force-recreate core inventory-sales-module
docker compose ps
```

Потом полный regression:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Если любой тест падает:

```text
1. Исправить точечно.
2. Повторить полный regression.
3. Не коммитить FAIL.
```

---

# 9. Manual smoke — обязательно

## Product filters

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/products" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?location=store" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?location=workshop" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?location=archive" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?location=draft" -TimeoutSec 15 | Select-Object StatusCode
```

HTML:

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/products" -TimeoutSec 15
$page.Content | Select-String "Магазин"
$page.Content | Select-String "Мастерская"
$page.Content | Select-String "Архив"
$page.Content | Select-String "Черновик"
```

## Product detail

Проверить хотя бы один реальный товар:

```text
1. открыть товар;
2. увидеть location dropdown;
3. увидеть quantity input;
4. сохранить изменение;
5. проверить, что список/деталь показывают новое значение.
```

## Sale cancel/reissue

Если безопасно создать тестовую продажу:

```text
1. Создать продажу.
2. Проверить reports total before cancel.
3. Отменить продажу.
4. Проверить:
   - sale status = canceled;
   - товар вернулся на остаток;
   - reports total уменьшился.
5. Создать ещё одну продажу.
6. Переоформить её.
7. Проверить:
   - old sale status = superseded;
   - new sale status = completed;
   - reports include only new sale.
```

Если runtime data нельзя трогать:

```text
Выполнить через тестовый fixture/API smoke с тестовым товаром и продажей.
```

---

# 10. Safety scans — обязательно

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

All should be clean or explained.

---

# 11. Docs/report/log

Создать/обновить в репозитории:

```text
reports/stage04h_finalization_audit_commit_report.md
docs/stage04h_product_locations_stock_sales_reissue.md
logs/2026-07-10.md
```

Не использовать только Antigravity brain artifacts как финальный отчёт.

Report structure:

```text
# Stage 04H Finalization Audit & Commit Report

## STATUS

READY_FOR_OWNER_CHECK / FAIL

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

## IMPLEMENTATION_REVIEW

### Product location filters

### Product location/quantity editing

### Sale cancel workflow

### Sale reissue workflow

### Reports integration

## API_VERIFICATION

Products:
Sales cancel:
Sales reissue:
Reports:

## UI_VERIFICATION

Products page:
Product detail:
Sale detail:
Reissue page:
Reports page:

## TESTS

Core:
Inventory:
Avito:

## MANUAL_SMOKE

Product filters:
Product edit:
Sale cancel:
Sale reissue:
Reports recalculation:

## SAFETY_SCAN

Runtime tracked:
Direct DB access:
Destructive DB calls:
Secrets:

## FILES_COMMITTED

## COMMITS

## PUSH_STATUS

## OWNER_CHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04H_FINALIZED_READY_FOR_OWNER_CHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 12. Git — targeted only

Use targeted add only.

Possible files:

```powershell
git add core/app/models.py
git add core/app/schemas.py
git add core/app/routers/products.py
git add core/app/routers/sales.py
git add core/app/routers/reports.py
git add core/tests/test_product_locations_and_quantity.py
git add core/tests/test_sales_cancel_reissue.py
git add core/tests/test_sales_reports.py
git add core/tests/test_sales_flow.py
git add core/tests/test_sales_warranty.py

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/templates/product_detail.html
git add inventory-sales-module/app/templates/sales_detail.html
git add inventory-sales-module/app/templates/sales_reissue.html
git add inventory-sales-module/app/templates/reports_sales.html
git add inventory-sales-module/tests/test_product_location_filters_ui.py
git add inventory-sales-module/tests/test_product_location_quantity_edit_ui.py
git add inventory-sales-module/tests/test_sales_cancel_reissue_ui.py
git add inventory-sales-module/tests/test_sales_reports_ui.py

git add docs/stage04h_product_locations_stock_sales_reissue.md
git add reports/stage04h_finalization_audit_commit_report.md
git add logs/2026-07-10.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04H_PRODUCT_LOCATIONS_STOCK_AND_SALES_REISSUE_PROMPT.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04H_FINALIZATION_AUDIT_COMMIT_PROMPT.md

git commit -m "Finalize Stage 04H product locations stock and sales reissue"
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

If logs are ignored and `git add logs/2026-07-10.md` fails:

```powershell
git add -f logs/2026-07-10.md
```

This is allowed for the specific log file only.

---

# 13. Definition of Done

Готово, если:

```text
worktree functional changes reviewed
/products location filters work
product detail location/quantity edit works
sale cancel works
sale reissue works
reports exclude canceled/superseded
full core pytest PASS
full inventory-sales-module pytest PASS
full avito-module pytest PASS
safety scans clean
report created in repo
doc created in repo
targeted commit created
push done
final git status clean
READY_FOR_OWNER_CHECK
```

---

# 14. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04H_FINALIZED_READY_FOR_OWNER_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04H_FINALIZATION_FAIL

BLOCKERS:
...
```
