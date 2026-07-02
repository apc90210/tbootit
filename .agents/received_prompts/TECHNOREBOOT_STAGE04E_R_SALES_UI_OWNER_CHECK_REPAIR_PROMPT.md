# PROMPT — Техноребут / Stage 04E-R Sales UI MVP Owner Check Repair

## Роль агента

Ты senior fullstack debugger, QA engineer, FastAPI/Jinja2 developer и owner-check repair engineer проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — выполнить repair после проваленной ручной проверки владельцем Stage04E.

Это repair stage, а не новый функциональный этап.

---

# 1. Причина repair

После Stage04E-Audit был заявлен PASS, но владелец вручную открыл UI и увидел страницу ошибки:

```text
Главная Товары Продажи Ценники — скоро
Ошибка
Ошибка Core API

На главную К списку товаров
```

Это означает:

```text
OWNER_MANUAL_CHECK: FAILED
Stage04E нельзя считать принятым
Stage04F начинать запрещено
нужно исправить ошибку UI/Core API integration
```

---

# 2. Главный статус

Текущий статус:

```text
STAGE04E_AUDIT_PASS_BUT_OWNER_MANUAL_CHECK_FAILED
```

Целевой статус repair:

```text
TECHNOREBOOT_STAGE04E_R_SALES_UI_OWNER_CHECK_REPAIR_READY_FOR_OWNER_RECHECK
```

После repair нельзя автоматически идти в Stage04F.

Нужен gate:

```text
OWNER_MANUAL_CHECK_REQUIRED: true
OWNER_ACCEPTANCE_REQUIRED: true
DO_NOT_START_STAGE04F_WITHOUT_OWNER_ACCEPTANCE: true
```

---

# 3. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ.

Архитектура:

```text
Core API + DB + Storage = единое ядро.
inventory-sales-module работает только через Core API.
```

Правильно:

```text
inventory-sales-module → Core API → Core DB
```

Запрещено:

```text
inventory-sales-module → Core DB напрямую
```

---

# 4. Что уже реализовано

Stage04E заявил:

```text
sales UI routes
sales_new.html
sales_list.html
sales_detail.html
кнопка Продать
POST /sales/create
CoreClient sales methods
python-multipart
tests inventory-sales-module 26 passed
Core tests 34 passed after SKU isolation fix
Avito tests passed
Stage04E implementation committed
Stage04E audit committed
```

Но owner manual check показал:

```text
Ошибка Core API
```

Поэтому audit PASS не принимается владельцем.

---

# 5. Что запрещено в repair

Не делать:

```text
Stage04F
ценники
печать
PDF
возвраты/отмена продажи через UI
новый Avito функционал
browser automation
прямой DB access из inventory-sales-module
собственную БД inventory-sales-module
git commit --amend
git add .
git add -u
git reset
git clean
git rebase
git push --force
```

Если после commit нужно дописать лог — сделать отдельный normal commit, не amend.

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

Если этот prompt найден в `C:\Users\Apc\Downloads`, скопировать его в:

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

Проверить:

```text
последний Stage04E implementation commit
последний Stage04E audit commit
нет dirty worktree
если dirty — сначала зафиксировать и объяснить
```

---

# 8. Reproduce owner error

Нужно воспроизвести именно ошибку владельца.

Проверить все ключевые страницы:

```powershell
Invoke-WebRequest http://127.0.0.1:8030/ | Select-Object StatusCode
Invoke-WebRequest http://127.0.0.1:8030/products | Select-Object StatusCode
Invoke-WebRequest http://127.0.0.1:8030/sales | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/sales/new?product_id=1" | Select-Object StatusCode
```

Если какая-то страница возвращает HTML с:

```text
Ошибка Core API
```

сохранить:

```text
URL
HTTP status
response fragment
timestamp
```

Проверить также браузерный/manual URL, который вероятнее всего открыл владелец:

```text
/products
/products/<id>
/sales
/sales/new?product_id=<id>
/sales/<id>
```

---

# 9. Logs diagnostics

Снять логи:

```powershell
docker compose logs --tail=250 inventory-sales-module
docker compose logs --tail=250 core
```

Искать:

```text
httpx errors
connection refused
response parsing errors
KeyError
ValidationError
TemplateError
404 from Core
500 from Core
wrong endpoint path
wrong JSON structure
sale detail shape mismatch
products paginated response mismatch
```

---

# 10. Core API diagnostics

Проверить напрямую Core:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/products | ConvertTo-Json -Depth 10
Invoke-RestMethod http://127.0.0.1:8000/api/sales | ConvertTo-Json -Depth 10
Invoke-RestMethod http://127.0.0.1:8000/api/sales/today | ConvertTo-Json -Depth 10
```

Если ошибка в продаже/detail, проверить конкретный sale id/product id из UI.

---

# 11. Вероятные причины

Проверить эти типовые причины:

## 11.1 CoreClient ожидает неправильный JSON shape

Например:

```text
Core /api/sales возвращает paginated wrapper: items/total/limit/offset
UI ожидает list
```

## 11.2 Sale detail response отличается от ожиданий UI

Например:

```text
GET /api/sales/{id} возвращает item structure не как template ожидает
```

## 11.3 Product detail route падает на missing optional field

Например:

```text
photo/url/events/avito fields отсутствуют
template не проверяет None
```

## 11.4 Core API недоступен из контейнера

Проверить из контейнера:

```powershell
docker compose exec inventory-sales-module python -c "import httpx; print(httpx.get('http://core:8000/health').json())"
```

## 11.5 Wrong environment CORE_API_BASE_URL

Проверить:

```powershell
docker compose exec inventory-sales-module env
```

## 11.6 Ошибка после продажи

Например:

```text
POST /sales/create проходит,
но redirect на /sales/{id} падает из-за sale detail parser/template.
```

---

# 12. Repair requirements

Исправить root cause минимально.

Обязательные требования после repair:

```text
/ открывается
/products открывается
/products/{id} открывается
/sales открывается
/sales/new?product_id=<sellable_product_id> открывается
POST /sales/create работает
/sales/{id} открывается после продажи
товар после продажи sold
повторная продажа blocked
нет страницы "Ошибка Core API" на нормальном happy path
```

Если Core вернул реальную бизнес-ошибку, UI должен показывать понятное русское сообщение:

```text
Товар нельзя продать в текущем статусе
Товар уже продан
Продажа недоступна
Core API временно недоступен
```

Но не generic "Ошибка Core API" для обычного успешного сценария.

---

# 13. Tests to add/update

Добавить regression tests на найденный bug.

Минимум:

```text
test_owner_reported_core_api_error_reproduced_and_fixed
test_sales_list_accepts_core_paginated_response
test_sale_detail_accepts_core_response_shape
test_product_detail_handles_missing_optional_fields
test_sales_create_redirect_detail_page_does_not_error
```

Выбрать только релевантные к root cause.

Запуск:

```powershell
docker compose exec inventory-sales-module pytest
docker compose exec core pytest
docker compose exec avito-module pytest
```

---

# 14. Real owner flow smoke

Создать уникальный тестовый товар через Core API:

```powershell
$sku = "OWNER-RECHECK-SALE-" + [guid]::NewGuid().ToString("N").Substring(0,8)

$payload = @{
  source = "owner_recheck"
  schema_version = "1.0"
  operation = "create_or_update"
  product = @{
    sku = $sku
    title = "Товар для проверки владельцем"
    category_path = @("Проверка")
    sale_price = 12345
  }
} | ConvertTo-Json -Depth 10

$res = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/product-cards/import-json `
  -ContentType "application/json" `
  -Body $payload

$productId = $res.product_id

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/products/$productId/status" `
  -ContentType "application/json" `
  -Body '{"status":"in_stock","reason":"Stage04E-R owner recheck smoke"}'
```

Проверить UI:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/products/$productId" | Select-Object StatusCode
Invoke-WebRequest "http://127.0.0.1:8030/sales/new?product_id=$productId" | Select-Object StatusCode
```

Продать через UI route:

```powershell
$form = @{
  product_id = $productId
  price = "12345"
  payment_method = "cash"
  notes = "Stage04E-R owner recheck smoke"
}

$saleResponse = Invoke-WebRequest `
  -Method Post `
  -Uri http://127.0.0.1:8030/sales/create `
  -Body $form `
  -MaximumRedirection 0 `
  -ErrorAction SilentlyContinue
```

Проверить:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/products/$productId"
Invoke-WebRequest "http://127.0.0.1:8030/sales" | Select-Object StatusCode
```

---

# 15. Safety scans

Direct DB access:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Browser automation:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
```

Runtime data:

```powershell
git status --ignored --short --untracked-files=all -- data/db
git status --ignored --short --untracked-files=all -- data/avito-module
```

---

# 16. Documentation

Создать/обновить:

```text
docs/stage04e_r_sales_ui_owner_check_repair.md
reports/stage04e_r_sales_ui_owner_check_repair_report.md
logs/2026-07-02.md
```

Report structure:

```text
# Stage 04E-R Sales UI Owner Check Repair Report

## STATUS

READY_FOR_OWNER_RECHECK / FAIL

## OWNER_REPORTED_ERROR

Text:
Likely URL:
Reproduced: yes/no

## ROOT_CAUSE

## FIX_IMPLEMENTED

## TESTS_ADDED_OR_UPDATED

## MANUAL_SMOKE

## REGRESSION_CHECKS

## SAFETY_SCAN

## FILES_CHANGED

## PROCESS_NOTES

Mention previous amend caveat and confirm no amend used in repair.

## OWNER_RECHECK_GUIDE

Give exact URLs and steps for owner.

## FINAL_STATUS

TECHNOREBOOT_STAGE04E_R_SALES_UI_OWNER_CHECK_REPAIR_READY_FOR_OWNER_RECHECK
```

---

# 17. Git

Use targeted add only:

```powershell
git status --short --untracked-files=all

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/templates/base.html
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/templates/product_detail.html
git add inventory-sales-module/app/templates/sales_new.html
git add inventory-sales-module/app/templates/sales_detail.html
git add inventory-sales-module/app/templates/sales_list.html
git add inventory-sales-module/tests/test_sales_routes.py
git add inventory-sales-module/tests/test_core_client_sales.py
git add inventory-sales-module/tests/test_sales_ui_russian.py
git add docs/stage04e_r_sales_ui_owner_check_repair.md
git add reports/stage04e_r_sales_ui_owner_check_repair_report.md
git add logs/2026-07-02.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_R_SALES_UI_OWNER_CHECK_REPAIR_PROMPT.md

git commit -m "Repair Stage 04E sales UI owner check failure"
git status --short --untracked-files=all
```

If another file was actually changed, add it explicitly and list it in report.

Strictly forbidden:

```text
git add .
git add -u
git commit --amend
```

---

# 18. Definition of Done

Repair готов, если:

```text
owner error reproduced or convincingly diagnosed
root cause found
fix implemented
/products works
/products/{id} works
/sales works
/sales/new works
/sales/create works
/sales/{id} works
generic "Ошибка Core API" gone from happy path
product sold after UI sale
repeat sale blocked
tests pass: inventory-sales-module, core, avito-module
no direct DB access
no price tags started
report created
commit created without amend
final status READY_FOR_OWNER_RECHECK
```

---

# 19. Главное правило

После этого repair не переходить к Stage04F.

Финальный ответ должен быть:

```text
TECHNOREBOOT_STAGE04E_R_SALES_UI_OWNER_CHECK_REPAIR_READY_FOR_OWNER_RECHECK
OWNER_MANUAL_CHECK_REQUIRED: true
NEXT_STEP: владелец вручную проверяет UI продажу
```
