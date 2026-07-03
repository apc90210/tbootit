# PROMPT — Техноребут / Stage 04E-R5 Audit Finalization Repair

## Роль агента

Ты senior release auditor, QA engineer, Git/process safety engineer и FastAPI schema reviewer проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — исправить незавершённый Stage04E-R5-Audit и довести его до корректного состояния:

```text
clean worktree
понятный audit verdict
full tests core + inventory-sales-module + avito-module
без runtime/temp в git
без незакоммиченных code changes
```

Это не новый функциональный этап.

---

# 1. Почему нужен repair

Предыдущий аудит Stage04E-R5 заявил:

```text
TECHNOREBOOT_STAGE04E_R5_AUDIT_READY_FOR_OWNER_MANUAL_CHECK
```

Но в его же финальном логе есть проблемы:

```text
worktree clean: false
committed files: None
```

Также во время аудита были действия, требующие проверки:

```text
1. Изменён core/app/schemas.py:
   ProductBase.sku и ProductBase.title были сделаны optional.

2. Это функциональный code change внутри audit.
   Нужно проверить, правильный ли это fix:
   - если DB/model реально допускает null — schema/UI должны безопасно работать;
   - если title по бизнес-логике обязателен — надо чинить test fixtures, а не ослаблять Product schema.

3. В финальном сообщении подтверждены только core/inventory tests.
   avito-module pytest не подтвержден в final status.

4. Выполнялись удаления runtime DB:
   - docker compose exec core rm tbootit.db
   - Remove-Item core/tbootit.db
   Нужно проверить, что это не повредило runtime и DB не tracked.

5. Финальный audit report создан, но не закоммичен.
```

Текущий статус:

```text
STAGE04E_R5_AUDIT_REPORTED_READY_BUT_DIRTY_UNCOMMITTED
```

Целевой статус:

```text
TECHNOREBOOT_STAGE04E_R5_AUDIT_FINALIZATION_REPAIR_READY_FOR_OWNER_MANUAL_CHECK
```

Gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 2. Строгие запреты

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
удалять runtime данные без необходимости
делать Base.metadata.drop_all/create_all
```

Разрешено:

```text
точечный bugfix, если он уже был сделан и признан правильным
точечный revert/исправление test fixtures, если schema change неправильный
audit report/log finalization
targeted commit
```

---

# 3. Prompt discovery

Найти prompt:

```text
TECHNOREBOOT_STAGE04E_R5_AUDIT_FINALIZATION_REPAIR_PROMPT.md
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

В отчёте указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 4. Preflight

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -20
git diff --name-status
git diff --stat
git diff -- core/app/schemas.py
git diff -- logs/2026-07-03.md
git diff -- reports/stage04e_r5_audit_cascading_dynamic_product_filters_report.md
```

Проверить:

```text
какие файлы dirty
есть ли untracked implementation_plan.md/task.md
есть ли audit report
есть ли prompt copy
есть ли runtime/temp tracked
```

Danger scan:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py|task\.md|implementation_plan\.md"
```

---

# 5. Schema fix review

Открыть:

```text
core/app/models.py
core/app/schemas.py
core/tests/test_product_filter_options_cascading.py
core/tests/test_products.py
```

Проверить:

```text
1. Product model: nullable ли sku/title?
2. ProductCreate/ProductUpdate/ProductResponse: что должно быть required по бизнес-логике?
3. UI может ли жить без title?
4. Тесты создавали некорректные mock/test products без title/sku?
```

Решение:

## Вариант A — schema change правильный

Если `sku` и/или `title` реально nullable в модели/старых данных:

```text
оставить Optional
добавить fallback в UI/tests, если нужно
добавить тест, что product response работает с отсутствующим sku/title
```

## Вариант B — schema change неправильный

Если `title` должен быть обязательным:

```text
вернуть title как required
исправить test fixtures, чтобы они создавали валидный title
оставить sku optional только если действительно nullable/необязателен
```

Важно:

```text
Нельзя ослаблять Product schema только ради прохождения тестов.
```

В report явно описать выбранное решение.

---

# 6. Runtime DB safety check

Проверить, что удаление DB не повредило систему:

```powershell
Test-Path core\tbootit.db
docker compose ps
docker compose exec core sh -c "find . -maxdepth 3 -name '*.db' -o -name '*.sqlite*'"
```

Проверить, что DB не tracked:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db"
```

Ожидание:

```text
tracked runtime DB отсутствует
```

Не коммитить DB.

---

# 7. Full tests

Обязательно выполнить все три:

```powershell
docker compose exec core pytest
docker compose exec inventory-sales-module pytest
docker compose exec avito-module pytest
```

Если контейнеры не подняты:

```powershell
docker compose up -d
```

Если менялся код core, пересобрать:

```powershell
docker compose build core
docker compose up -d core
```

Ожидание:

```text
core PASS
inventory-sales-module PASS
avito-module PASS
```

---

# 8. No-hang smoke

Проверить, что ранее зависавший URL не зависает:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/products?category_id=1" -TimeoutSec 15 | Select-Object StatusCode
```

Также:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/products" -TimeoutSec 15 | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/products?brand=Lenovo" -TimeoutSec 15 | Select-Object StatusCode
```

Если зависает — статус FAIL и нужен Stage04E-R5-R.

---

# 9. Cascading API quick verification

Проверить:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/products/filter-options" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/products/filter-options?category_id=1" | ConvertTo-Json -Depth 10
```

Если есть brand/model из ответа, проверить:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/products/filter-options?category_id=1&brand=<brand>" | ConvertTo-Json -Depth 10
```

Проверить:

```text
selected
order
counts
нет очевидных 0-count options
```

---

# 10. Safety scans

Direct DB access in inventory-sales-module:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|tbootit.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Runtime tracked files:

```powershell
git ls-files | Select-String -Pattern "tbootit\.db|technoreboot\.db|\.sqlite|\.sqlite3|data/db|data/avito-module|__pycache__|\.pytest_cache|debug\.py"
```

Browser/captcha automation:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
```

---

# 11. Report

Создать/обновить:

```text
reports/stage04e_r5_audit_finalization_repair_report.md
```

Структура:

```text
# Stage 04E-R5 Audit Finalization Repair Report

## STATUS

READY_FOR_OWNER_MANUAL_CHECK / FAIL

## REASON

## PROMPT_DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## BEFORE_STATE

Branch:
HEAD:
Dirty files:
Untracked files:
Runtime tracked scan:

## SCHEMA_FIX_REVIEW

Product model nullability:
Schema before:
Decision:
Files changed:
Why this is correct:

## RUNTIME_DB_SAFETY

DB physical presence:
Tracked DB scan:
Impact:

## FULL_TESTS

Core:
Inventory:
Avito:

## NO_HANG_SMOKE

/products:
/products?category_id=1:
/products?brand=Lenovo:

## CASCADING_API_SMOKE

filter-options:
filter-options?category_id=1:
filter-options?category_id=1&brand=...:

## SAFETY_SCAN

Direct DB access:
Runtime tracked:
Browser/captcha automation:

## GIT_STATUS_AFTER

## BLOCKERS

## OWNER_RECHECK_GUIDE

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R5_AUDIT_FINALIZATION_REPAIR_READY_FOR_OWNER_MANUAL_CHECK
OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 12. Logs

Append to:

```text
logs/2026-07-03.md
```

Include:

```text
prompt filename
before HEAD
dirty files
schema decision
tests core/inventory/avito
no-hang smoke
final git status
final status
```

---

# 13. Git

Use targeted add only.

Potential files:

```powershell
git add core/app/schemas.py
git add core/tests/test_product_filter_options_cascading.py
git add reports/stage04e_r5_audit_cascading_dynamic_product_filters_report.md
git add reports/stage04e_r5_audit_finalization_repair_report.md
git add logs/2026-07-03.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R5_AUDIT_FINALIZATION_REPAIR_PROMPT.md

git commit -m "Finalize Stage 04E R5 audit state"
git status --short --untracked-files=all
```

Only add files that actually changed and are correct.

Forbidden:

```text
git add .
git add -A
git add -u
git commit --amend
```

---

# 14. Definition of Done

Готово, если:

```text
schema.py change reviewed and either committed correctly or fixed
audit report committed
log committed
core pytest PASS
inventory-sales-module pytest PASS
avito-module pytest PASS
/products?category_id=1 no hang
runtime DB not tracked
temp/debug files not tracked
final git status clean or only acceptable ignored local runtime files
no amend/add-A used
READY_FOR_OWNER_MANUAL_CHECK
```

---

# 15. Final answer required from agent

Финальный ответ должен быть подробным в чат.

Обязательно:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R5_AUDIT_FINALIZATION_REPAIR_READY_FOR_OWNER_MANUAL_CHECK

OWNER_MANUAL_CHECK_REQUIRED: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Если есть blockers:

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE04E_R5_AUDIT_FINALIZATION_REPAIR_FAIL

BLOCKERS:
...
```
