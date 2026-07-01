# PROMPT — Техноребут / Stage 04C-Audit Core Sales Flow Hardening

## Роль агента

Ты senior QA/audit engineer, backend/API reviewer, database migration auditor и бизнес-логический аудитор проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — провести независимый аудит реализованного этапа:

```text
Stage 04C — Core Sales Flow Hardening
```

Это аудит, а не новая разработка.

---

# 1. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ.

Главная архитектура:

```text
Core API + DB + Storage = единое ядро.
Все остальные модули работают только через HTTP API.
```

Core владеет:

```text
БД
товарами
статусами
продажами
историей
audit log
product events
```

Внешние модули не должны писать напрямую в БД.

---

# 2. Уже выполненные этапы

В проекте уже выполнены:

```text
Stage 01  — Core MVP Big Module
Stage 01R — Admin Shell Core API Connection Repair
Stage 01S — Admin Shell CRUD & Seed Completion Repair
Stage 01A — Independent Core MVP Audit
Stage 01T — Russian UI Localization for Admin Shell
Stage 02 v2 — Avito-Style Product Cards & JSON Import
Stage 02A — Independent Audit for Avito-Style Product Cards & JSON Import
Stage 03A — Avito Parser Module MVP
Stage 04A — Core Product API Gaps
Stage 04A-Audit — Core Product API Gaps Audit
Stage 04B — Inventory/Sales/Price Tags Module Planning
Stage 04C — Core Sales Flow Hardening
```

Известный заявленный результат Stage04C:

```text
созданы поля sales.status, cancelled_at, cancel_reason
добавлены safe ad-hoc SQLite migrations
POST /api/sales переписан с validation product statuses/payment_method
GET /api/sales получил filtering/pagination
добавлен /api/sales/{id}/cancel
добавлены event/audit logging
создан core/tests/test_sales_flow.py
создан reports/stage04c_core_sales_flow_hardening_report.md
status в отчете: READY_FOR_AUDIT
```

Важное замечание по присланному логу:

```text
не видно финального git commit Stage04C
агент несколько раз удалял runtime SQLite DB внутри контейнера:
docker compose exec core rm -f technoreboot.db ...
```

Аудит обязан отдельно проверить:

```text
worktree status
наличие commit или незакоммиченных изменений
миграции на чистой БД
миграции на существующей БД
что runtime DB не попала в git
```

---

# 3. Цель Stage04C-Audit

Проверить, что Core Sales Flow действительно готов для будущего `inventory-sales-module`.

Ответить:

```text
можно ли переходить к Stage04D — Inventory/Sales Module Skeleton?
```

Проверить:

```text
POST /api/sales
GET /api/sales
GET /api/sales/{id}
GET /api/sales/today
POST /api/sales/{id}/cancel
payment_method validation
product status validation
sale status
cancel flow
ProductEvent
AuditLog
SQLite migrations
tests
manual smoke
regressions
git hygiene
runtime data safety
```

---

# 4. Что запрещено делать в аудите

Не делать новую разработку.

Запрещено:

```text
начинать inventory-sales-module
начинать UI продаж
начинать ценники
менять avito-module runtime code
менять admin-shell
делать прямой доступ внешних модулей к БД
коммитить runtime DB
коммитить *.db / *.sqlite / __pycache__
использовать git add .
использовать git reset / git clean / amend / rebase / force push
```

Разрешены только мелкие audit fixes:

```text
отчет
документация
очевидные typos
безопасные тестовые исправления
очевидная минимальная правка, если audit smoke нашел 500 bug
```

Если найден серьезный баг — зафиксировать `FAIL` и рекомендовать `Stage04C-R`.

---

# 5. Обязательное правило поиска prompt-файлов

Перед началом работы найти актуальные prompt-файлы.

Искать в:

```text
C:\tbootit
C:\tbootit\.agents
C:\tbootit\docs
C:\tbootit\docs\obsidian
C:\tbootit\prompts
C:\tbootit\logs\prompts
C:\Users\Apc\Downloads
```

Выполнить:

```powershell
Set-Location C:\tbootit

$PromptSearchRoots = @(
  "C:\tbootit",
  "C:\tbootit\.agents",
  "C:\tbootit\docs",
  "C:\tbootit\docs\obsidian",
  "C:\tbootit\prompts",
  "C:\tbootit\logs\prompts",
  "C:\Users\Apc\Downloads"
)

$PromptFiles = foreach ($Root in $PromptSearchRoots) {
  if (Test-Path $Root) {
    Get-ChildItem -Path $Root -Recurse -File -ErrorAction SilentlyContinue |
      Where-Object {
        $_.Name -match "prompt|PROMPT|промт|ПРОМТ" -or
        $_.Extension -in ".md", ".txt"
      } |
      Select-Object FullName, LastWriteTime, Length
  }
}

$PromptFiles | Sort-Object LastWriteTime -Descending | Format-Table -AutoSize
```

Если этот prompt найден в:

```text
C:\Users\Apc\Downloads
```

скопировать его в:

```text
C:\tbootit\.agents\received_prompts\
```

В отчете указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 6. Preflight / Git state

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -15
git show --name-status --oneline --stat HEAD

docker compose ps
docker compose config
```

Проверить:

```text
есть ли Stage04C commit
или Stage04C changes всё еще uncommitted
```

Ожидаемые файлы Stage04C:

```text
core/app/routers/sales.py
core/app/schemas.py
core/app/models.py
core/tests/test_sales_flow.py
docs/core_sales_flow.md
docs/inventory_sales_module_core_api_contract.md
docs/stage04c_core_sales_flow_hardening.md
reports/stage04c_core_sales_flow_hardening_report.md
logs/2026-07-01.md
.agents/received_prompts/TECHNOREBOOT_STAGE04C_CORE_SALES_FLOW_HARDENING_PROMPT.md
```

Если worktree dirty — не игнорировать. Зафиксировать в отчете и привести к clean state только безопасным targeted git add, если все изменения ожидаемые.

---

# 7. Scope audit

Проверить actual changes:

```powershell
git status --short --untracked-files=all
git diff --name-status
git diff --stat
```

Если Stage04C был committed:

```powershell
git show --name-status --oneline --stat HEAD
```

Оценить:

```text
не начат UI
не начаты price tags
не изменен avito-module runtime
не изменен admin-shell без причины
не закоммичена runtime DB
```

---

# 8. Docker rebuild audit

Выполнить:

```powershell
docker compose down
docker compose up --build -d
docker compose ps
```

Проверить:

```text
core up
admin-shell up
avito-module up
нет restart loop
```

Логи:

```powershell
docker compose logs --tail=200 core
docker compose logs --tail=100 avito-module
```

---

# 9. SQLite migration audit

Проверить, что migration logic безопасна.

Открыть:

```text
core/app/main.py
core/app/database.py
core/app/models.py
core/app/routers/sales.py
```

Проверить:

```text
sales.status добавляется, если отсутствует
sales.payment_method если нужно добавляется/есть
sales.cancelled_at добавляется, если отсутствует
sales.cancel_reason добавляется, если отсутствует
migration не удаляет данные
migration не делает drop_all
migration не требует ручного rm technoreboot.db
```

Проверить на текущей БД:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/sales | ConvertTo-Json -Depth 5
```

Если возможно, проверить на fresh DB без коммита runtime данных:

```powershell
docker compose down
# НЕ УДАЛЯТЬ git tracked files. Удалять только ignored runtime DB, если она ignored.
# Если data/db ignored, можно переименовать runtime DB backup на время audit:
# Rename-Item data\db\technoreboot.db technoreboot.db.audit_backup
docker compose up --build -d
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/sales
# восстановить backup, если делался
```

Если fresh DB audit рискован — не делать destructive action, но зафиксировать why skipped.

---

# 10. API smoke

Выполнить:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
Invoke-RestMethod http://127.0.0.1:8000/api/products | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/sales | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/sales/today | ConvertTo-Json -Depth 5
```

Проверить:

```text
нет 500
GET /api/sales возвращает paginated wrapper
GET /api/sales/today возвращает total/total_amount/items
```

---

# 11. Sale creation audit

Создать или найти тестовый товар.

Рекомендуемый безопасный путь:

```powershell
$json = Get-Content .\docs\examples\product_card_lenovo_t480.json -Raw

$res = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/product-cards/import-json `
  -ContentType "application/json" `
  -Body $json

$productId = $res.product_id
```

Поставить статус in_stock:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/products/$productId/status" `
  -ContentType "application/json" `
  -Body '{"status":"in_stock","reason":"Stage04C audit sale smoke"}'
```

Продать:

```powershell
$sale = @{
  customer_id = $null
  payment_method = "cash"
  notes = "Stage04C audit sale"
  items = @(
    @{
      product_id = $productId
      quantity = 1
      price = 25000
    }
  )
} | ConvertTo-Json -Depth 10

$saleResult = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/sales `
  -ContentType "application/json" `
  -Body $sale

$saleResult | ConvertTo-Json -Depth 10
```

Проверить:

```text
sale создан
sale.total_amount корректен
payment_method сохранен
product.status стал sold
```

---

# 12. Reject invalid sales

Проверить:

```text
sold product нельзя продать повторно
written_off product нельзя продать
in_repair product нельзя продать
draft product нельзя продать
unknown payment_method отклоняется
empty items отклоняется
duplicate product in same sale отклоняется
quantity <= 0 отклоняется
price < 0 отклоняется
```

Команды можно выполнить через pytest или manual Invoke-RestMethod.

---

# 13. Sale detail / list / today audit

Проверить:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/sales?limit=5&offset=0" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/sales?payment_method=cash" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/sales/today" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/sales/$($saleResult.id)" | ConvertTo-Json -Depth 10
```

Проверить:

```text
pagination работает
payment_method filter работает
today включает сегодняшнюю продажу
detail возвращает sale + items
```

---

# 14. Cancel sale audit

Отменить sale:

```powershell
$cancel = @{
  reason = "Stage04C audit cancel"
} | ConvertTo-Json

$cancelResult = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/sales/$($saleResult.id)/cancel" `
  -ContentType "application/json" `
  -Body $cancel

$cancelResult | ConvertTo-Json -Depth 10
```

Проверить:

```text
sale.status = cancelled
sale.cancelled_at заполнен
sale.cancel_reason заполнен
product.status вернулся в in_stock
ProductEvent создан
AuditLog создан
```

Повторная отмена:

```powershell
try {
  Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/api/sales/$($saleResult.id)/cancel" `
    -ContentType "application/json" `
    -Body $cancel
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

Ожидание:

```text
400/409
```

---

# 15. ProductEvent / AuditLog audit

Проверить через API, если есть endpoints:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/products/$productId/details | ConvertTo-Json -Depth 10
Invoke-RestMethod http://127.0.0.1:8000/api/admin/audit-log | ConvertTo-Json -Depth 10
```

Проверить:

```text
есть событие sale_completed
есть событие sale_cancelled
audit log содержит sale create/cancel
datetime JSON serialization не падает
```

---

# 16. Regression audit

Проверить, что не сломано:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/products | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/product-cards/imports | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8020/health
Invoke-RestMethod http://127.0.0.1:8020/api/core/health
```

---

# 17. Tests audit

Запустить:

```powershell
docker compose exec core pytest
docker compose exec avito-module pytest
```

Ожидание:

```text
Core tests pass
Avito module tests pass
```

Отдельно проверить:

```powershell
docker compose exec core pytest tests/test_sales_flow.py
```

---

# 18. Safety scans

Выполнить:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module
```

Runtime data:

```powershell
git status --ignored --short --untracked-files=all -- data/db
git status --ignored --short --untracked-files=all -- data/avito-module
```

Проверить:

```text
runtime data ignored
*.db не в индексе
нет downloaded HTML в индексе
```

---

# 19. Documentation audit

Проверить:

```text
docs/core_sales_flow.md
docs/inventory_sales_module_core_api_contract.md
docs/stage04c_core_sales_flow_hardening.md
reports/stage04c_core_sales_flow_hardening_report.md
logs/2026-07-01.md
```

Отчет Stage04C должен содержать:

```text
READY_FOR_AUDIT
implemented
API changes
DB changes
sales validation rules
status lifecycle
payment methods
sale cancel flow
product events
audit log
tests
manual smoke
regression checks
safety scan
```

---

# 20. Итоговый отчет

Создать:

```text
reports/stage04c_audit_core_sales_flow_hardening_report.md
```

Структура:

```text
# Stage 04C-Audit Core Sales Flow Hardening Report

## STATUS

PASS / PASS_WITH_NOTES / FAIL

## EXECUTIVE SUMMARY

Коротко: можно ли переходить к Stage04D.

## PROMPT DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## ENVIRONMENT

Branch:
Head:
Core URL:
Admin Shell URL:
Avito Module URL:
Docker status:

## GIT_STATE_AUDIT

Stage04C committed:
Worktree status:
Findings:

## SCOPE_AUDIT

Expected files:
Actual files:
Findings:

## MIGRATION_AUDIT

## SALES_CREATE_AUDIT

## SALES_VALIDATION_AUDIT

## SALES_LIST_DETAIL_TODAY_AUDIT

## SALES_CANCEL_AUDIT

## PRODUCT_EVENT_AUDIT

## AUDIT_LOG_AUDIT

## REGRESSION_AUDIT

## TESTS

## SAFETY_SCAN

## RUNTIME_DATA_AUDIT

## DOCUMENTATION_AUDIT

## BLOCKERS

## NON_BLOCKING_ISSUES

## RECOMMENDED_NEXT_STAGE

Варианты:
- Stage04C-R — repair, если есть блокеры
- Stage04D — Inventory/Sales Module Skeleton
```

---

# 21. Git commit

Если Stage04C changes еще не были committed, и аудит подтвердил, что они корректны, сначала сделать targeted commit Stage04C implementation:

```powershell
git add core/app/routers/sales.py
git add core/app/schemas.py
git add core/app/models.py
git add core/tests/test_sales_flow.py
git add docs/core_sales_flow.md
git add docs/inventory_sales_module_core_api_contract.md
git add docs/stage04c_core_sales_flow_hardening.md
git add reports/stage04c_core_sales_flow_hardening_report.md
git add logs/2026-07-01.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04C_CORE_SALES_FLOW_HARDENING_PROMPT.md
git commit -m "Harden Core sales flow"
```

Затем commit audit report:

```powershell
git add reports/stage04c_audit_core_sales_flow_hardening_report.md
git add logs/2026-07-01.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04C_AUDIT_CORE_SALES_FLOW_HARDENING_PROMPT.md
git commit -m "Audit Stage 04C Core sales flow hardening"
```

Не использовать:

```text
git add .
git add -u
git commit --amend
```

Не выполнять push без отдельной команды владельца.

---

# 22. Definition of Done

Stage04C-Audit готов, если:

```text
prompt найден и скопирован
preflight выполнен
git state проверен
scope проверен
Docker rebuild выполнен
SQLite migration проверена
sale create проверен
invalid sale validation проверен
sales list/detail/today проверены
cancel sale проверен
ProductEvent проверен
AuditLog проверен
regressions проверены
Core tests pass
Avito module tests pass
safety scans выполнены
runtime data проверена
docs проверены
audit report создан
commits созданы при необходимости
рекомендован следующий этап
```

---

# 23. Ожидаемый итог

Если всё хорошо:

```text
STATUS: PASS
Recommended next stage: Stage04D — Inventory/Sales Module Skeleton
```

Если есть мелкие замечания:

```text
STATUS: PASS_WITH_NOTES
Recommended next stage: Stage04D или Stage04C-R
```

Если есть блокеры:

```text
STATUS: FAIL
Recommended next stage: Stage04C-R
```

---

# 24. Главный принцип

После Stage04C Core должен уметь надежно:

```text
товар in_stock/reserved → продажа → status sold → event/audit
sale cancelled → товар вернулся in_stock → event/audit
```

Только после этого можно строить рабочий UI продаж.
