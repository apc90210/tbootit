# PROMPT — Техноребут / Stage 04C Core Sales Flow Hardening

## Роль агента

Ты senior backend developer, API designer, business-logic engineer и auditor-aware implementer проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — реализовать Stage 04C: усилить Core Sales Flow, чтобы продажа товара была безопасной, валидируемой, логируемой и готовой для будущего `inventory-sales-module`.

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

Правильная схема будущих продаж:

```text
inventory-sales-module → Core API → Core DB
```

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
```

Известный результат Stage04B:

```text
STATUS: PLANNING_READY
inventory-sales-module planned
port 8030 planned
price tags will be rendered by inventory-sales-module
next recommended stage: Stage04C — Core Sales Flow Hardening
```

---

# 3. Выявленные gaps Stage04B

Текущий `/api/sales` недостаточен:

```text
POST /api/sales обходит строгие product lifecycle transitions
POST /api/sales не валидирует статус товара перед продажей
может продать already sold / written_off / in_repair товар
не пишет ProductEvent при продаже
GET /api/sales возвращает .all() без pagination
нет фильтрации по датам
нет GET /api/sales/{id}
нет GET /api/sales/today
нет POST /api/sales/{id}/cancel
```

Stage04C должен это исправить.

---

# 4. Цель Stage04C

Реализовать безопасную Core-логику продаж.

Нужно сделать:

```text
1. Harden POST /api/sales.
2. Добавить строгую валидацию статуса товара перед продажей.
3. После продажи корректно менять status=sold через общую lifecycle-логику.
4. Создавать ProductEvent.
5. Создавать AuditLog.
6. Добавить payment_method validation.
7. Добавить GET /api/sales с pagination и фильтрами.
8. Добавить GET /api/sales/{id}.
9. Добавить GET /api/sales/today.
10. Добавить POST /api/sales/{id}/cancel.
11. Добавить tests.
12. Не ломать import-json, products API, avito-module.
```

---

# 5. Что запрещено в Stage04C

Не делать:

```text
inventory-sales-module UI
price tags
Admin Shell redesign
Avito Module changes
browser automation
crawling
прямой доступ внешних модулей к БД
production deployment
```

Разрешено менять только Core backend и tests/docs/reports.

Разрешенные зоны:

```text
core/app/routers/sales.py
core/app/schemas.py
core/app/models.py — только если нужна минимальная модельная доработка
core/tests/*
docs/*
reports/*
logs/*
.agents/received_prompts/*
```

Не использовать:

```text
git add .
git add -u
git reset
git clean
git commit --amend
git rebase
git push --force
```

---

# 6. Обязательное правило поиска prompt-файлов

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

# 7. Preflight

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

Проверить наличие:

```text
reports/stage04b_inventory_sales_price_tags_module_planning_report.md
docs/inventory_sales_module_core_api_contract.md
docs/stage04b_inventory_sales_price_tags_planning.md
```

Не начинать работу поверх непонятного dirty state.

---

# 8. Изучить текущую реализацию Sales

Открыть:

```text
core/app/routers/sales.py
core/app/schemas.py
core/app/models.py
core/tests/*
```

Понять:

```text
как сейчас создается Sale
как сейчас создаются SaleItem
как сейчас меняется Product.status
есть ли ProductEvent model/table
как пишется AuditLog
как реализован status lifecycle в products.py
```

Если в products.py уже есть функция status transition — переиспользовать ее или вынести безопасно в service helper.

---

# 9. Требования к статусам продаж

Разрешить продажу только если товар:

```text
in_stock
reserved
```

Запретить продажу, если товар:

```text
draft
sold
written_off
in_repair
for_parts
published_site
published_avito — если это только publication status, не должен мешать продаже; но если это product.status, оценить аккуратно
```

Если текущая модель использует `published_site/published_avito` как product.status, не ломать старую логику. Для MVP можно разрешить продажу только `in_stock` и `reserved`, остальные статусы отклонять.

При продаже:

```text
product.status = sold
Sale создается
SaleItem создается
ProductEvent создается
AuditLog создается
```

---

# 10. Payment method validation

Добавить допустимые payment methods:

```text
cash
card
transfer
mixed
other
```

Русские подписи будут в UI позже, в Core хранить enum-like строки.

Если передан неизвестный payment_method — вернуть 400/422.

Если payment_method не передан — использовать:

```text
cash
```

или явно требовать поле. Для MVP предпочтительно default `cash`, но зафиксировать в docs/report.

---

# 11. Sales API contract

## 11.1 POST /api/sales

Request example:

```json
{
  "customer_id": null,
  "payment_method": "cash",
  "notes": "Розничная продажа",
  "items": [
    {
      "product_id": 1,
      "quantity": 1,
      "price": 25000
    }
  ]
}
```

Validation:

```text
items не пустой
quantity > 0
price >= 0
product exists
product.status in [in_stock, reserved]
для MVP quantity must be 1, если учет остатков поштучный
нельзя продать один и тот же product дважды в одном sale
```

Response должен включать:

```text
sale id
total_amount
payment_method
items
created_at
```

Если продажа запрещена:

```text
HTTP 400
понятное сообщение
```

## 11.2 GET /api/sales

Добавить:

```text
limit
offset
date_from
date_to
payment_method
customer_id
```

Response:

```json
{
  "items": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

## 11.3 GET /api/sales/{id}

Вернуть:

```text
sale
items
customer if exists
products basic data if possible
```

## 11.4 GET /api/sales/today

Вернуть продажи за сегодняшний день по локальной дате сервера.

Минимум:

```json
{
  "items": [],
  "total": 0,
  "total_amount": 0
}
```

## 11.5 POST /api/sales/{id}/cancel

Request:

```json
{
  "reason": "Возврат / ошибочная продажа"
}
```

Behavior:

```text
если sale уже cancelled — вернуть 400
sale.status = cancelled
товары из sale_items вернуть в in_stock
создать ProductEvent по каждому товару
создать AuditLog
```

Если в модели Sale нет `status`, добавить поле:

```text
status: completed / cancelled
```

Если migration отсутствует, аккуратно обеспечить совместимость для SQLite dev DB.

---

# 12. DB / migration policy

Проект сейчас MVP на SQLite.

Если нужно добавить поля в existing tables:

```text
sales.status
sales.payment_method
sales.cancelled_at
sales.cancel_reason
```

Сделать безопасную lightweight migration при startup или в init_db:

```text
проверить PRAGMA table_info
ALTER TABLE ADD COLUMN если нет
```

Не удалять данные.

Не коммитить runtime DB.

---

# 13. ProductEvent / AuditLog

При продаже создать product event:

```text
event_type = sale_completed
old_status = in_stock/reserved
new_status = sold
description/details: sale_id, price, payment_method
```

При отмене продажи:

```text
event_type = sale_cancelled
old_status = sold
new_status = in_stock
description/details: sale_id, reason
```

AuditLog:

```text
entity_type = sale
entity_id = sale.id
action = create/cancel
details JSON serializable with default=str if needed
```

Избегать datetime serialization bug.

---

# 14. Tests

Добавить/обновить tests:

```text
core/tests/test_sales_flow.py
```

Покрыть:

```text
test_create_sale_from_in_stock_product
test_create_sale_from_reserved_product
test_reject_sale_from_sold_product
test_reject_sale_from_written_off_product
test_reject_sale_from_in_repair_product
test_reject_unknown_payment_method
test_reject_empty_items
test_reject_duplicate_product_in_same_sale
test_sale_changes_product_status_to_sold
test_sale_creates_product_event
test_get_sales_paginated
test_get_sale_detail
test_get_sales_today
test_cancel_sale_restores_product_to_in_stock
test_cancel_sale_twice_rejected
test_cancel_sale_creates_product_event
test_import_json_regression_after_sales_changes
```

Запустить:

```powershell
docker compose exec core pytest
docker compose exec avito-module pytest
```

---

# 15. Manual smoke

После реализации выполнить:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/products | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/sales | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/sales/today | ConvertTo-Json -Depth 5
```

Создать тестовый товар через import-json или существующий seed.

Поставить статус:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/products/<id>/status `
  -ContentType "application/json" `
  -Body '{"status":"in_stock","reason":"Stage04C smoke"}'
```

Продать:

```powershell
$sale = @{
  customer_id = $null
  payment_method = "cash"
  notes = "Stage04C smoke sale"
  items = @(
    @{
      product_id = <id>
      quantity = 1
      price = 25000
    }
  )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/sales `
  -ContentType "application/json" `
  -Body $sale
```

Проверить товар:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/products/<id> | ConvertTo-Json -Depth 5
```

Проверить отмену:

```powershell
$cancel = @{
  reason = "Stage04C smoke cancel"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/sales/<sale_id>/cancel `
  -ContentType "application/json" `
  -Body $cancel
```

---

# 16. Safety scans

Выполнить:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module
```

Проверить runtime data:

```powershell
git status --ignored --short --untracked-files=all -- data/db
git status --ignored --short --untracked-files=all -- data/avito-module
```

Ожидание:

```text
runtime data ignored
*.db не в индексе
```

---

# 17. Documentation

Обновить/создать:

```text
docs/core_sales_flow.md
docs/inventory_sales_module_core_api_contract.md
docs/stage04c_core_sales_flow_hardening.md
```

В docs описать:

```text
allowed statuses for sale
payment methods
sale create flow
sale cancel flow
events/audit behavior
known limitations
```

---

# 18. Report

Создать:

```text
reports/stage04c_core_sales_flow_hardening_report.md
```

Структура:

```text
# Stage 04C Core Sales Flow Hardening Report

## STATUS

READY_FOR_AUDIT / FAIL

## BRANCH

## HEAD

## PROMPT DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## IMPLEMENTED

## API CHANGES

## DB CHANGES

## SALES_VALIDATION_RULES

## STATUS_LIFECYCLE

## PAYMENT_METHODS

## SALE_CANCEL_FLOW

## PRODUCT_EVENTS

## AUDIT_LOG

## TESTS

## MANUAL_SMOKE

## REGRESSION_CHECKS

## SAFETY_SCAN

## FILES_CHANGED

## BLOCKERS

## NEXT_RECOMMENDED_STAGE

Stage 04C-Audit — Core Sales Flow Hardening Audit
```

Expected final status:

```text
TECHNOREBOOT_STAGE04C_CORE_SALES_FLOW_HARDENING_READY_FOR_AUDIT
```

---

# 19. Logging

Добавить запись в:

```text
logs/2026-07-01.md
```

Минимум:

```text
prompt filename
prompt source
local copy
branch/head
preflight
files changed
tests
manual smoke
final status
```

---

# 20. Git

После успешной проверки:

```powershell
git status --short --untracked-files=all

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
git status --short --untracked-files=all
```

Не использовать `git add .`.

Не выполнять push без отдельной команды владельца.

---

# 21. Definition of Done

Stage04C готов, если:

```text
prompt найден и скопирован
preflight выполнен
POST /api/sales hardened
GET /api/sales paginated
GET /api/sales/{id} добавлен
GET /api/sales/today добавлен
POST /api/sales/{id}/cancel добавлен
payment_method validation работает
status validation работает
sold/written_off/in_repair нельзя продать
sale sets product status=sold
cancel restores product status=in_stock
ProductEvent пишется
AuditLog пишется
Core tests pass
Avito-module tests pass
manual smoke pass
docs updated
report created
commit created
```

---

# 22. Главный принцип

Stage04C — это не UI.

Stage04C должен сделать Core sales logic надежной, чтобы после него можно было:

```text
товар из Core → продажа через API → status sold → история и audit log
```

Только после этого строить UI продаж и ценников.
