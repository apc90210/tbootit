# PROMPT — Техноребут / Stage 04E-Audit Sales UI MVP

## Роль агента

Ты senior QA/audit engineer, fullstack reviewer, business-flow auditor и regression investigator проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — провести независимый аудит реализованного этапа:

```text
Stage 04E — Sales UI MVP
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

`inventory-sales-module` — отдельный внешний рабочий модуль магазина.

Правильная схема:

```text
inventory-sales-module → Core API → Core DB
```

Неправильная схема:

```text
inventory-sales-module → Core DB напрямую
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
Stage 04C — Core Sales Flow Hardening
Stage 04C-Audit — Core Sales Flow Hardening Audit
Stage 04D — Inventory/Sales Module Skeleton
Stage 04D-Audit — Inventory/Sales Module Skeleton Audit
Stage 04E — Sales UI MVP
```

Известный заявленный результат Stage04E:

```text
создана форма продажи sales_new.html
создан список продаж sales_list.html
создана страница продажи sales_detail.html
добавлен router inventory-sales-module/app/routers/sales.py
CoreClient расширен методами продаж
кнопка "Продать" активирована для товаров в наличии
python-multipart добавлен в requirements.txt
обновлены docs и README
создан reports/stage04e_sales_ui_mvp_report.md
лог закрыт в logs/2026-07-02.md
inventory-sales-module pytest: 26 passed
работа НЕ закоммичена, оставлена на аудит
```

Важные caveats:

```text
1. Работа Stage04E не закоммичена.
2. Core pytest имел падение test_create_product_and_sale из-за persistent SKU collision SALE-TEST-001.
3. Агент заявил, что это не code regression, а существующая коллизия БД.
4. Аудит обязан это проверить, а не принимать на веру.
5. Нельзя переходить к ценникам до успешного Stage04E-Audit.
```

---

# 3. Цель Stage04E-Audit

Проверить, что Sales UI MVP действительно работает:

```text
товар из inventory-sales-module продается через Core API
Core создает продажу
Core меняет товар status=sold
UI показывает успешную продажу
повторная продажа становится недоступна
нет прямого DB access
ценники/печать не начаты
```

Ответить:

```text
можно ли переходить к Stage04F — Price Tags MVP?
```

---

# 4. Что запрещено делать в аудите

Не делать новую разработку.

Запрещено:

```text
начинать Stage04F Price Tags
добавлять печать
добавлять PDF
добавлять возвраты/отмену продажи через UI
менять avito-module runtime
менять admin-shell
делать прямой DB access
делать browser automation
коммитить runtime DB
использовать git add .
использовать git add -u
использовать git reset / git clean / commit --amend / rebase / force push
```

Разрешены только audit fixes:

```text
отчет
лог
документация
очевидные typos
тестовая изоляция SKU collision
минимальная правка явного 500 bug, если UI smoke обнаружит проблему
```

Если найден серьезный баг — зафиксировать `FAIL` и рекомендовать `Stage04E-R`.

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

# 6. Preflight / dirty worktree audit

Выполнить:

```powershell
Set-Location C:\tbootit

git status --short --untracked-files=all
git branch --show-current
git log --oneline -15
git diff --name-status
git diff --stat
docker compose ps
docker compose config
```

Так как Stage04E специально оставлен uncommitted, нужно:

```text
1. Зафиксировать все dirty files.
2. Проверить, что dirty files относятся только к Stage04E.
3. Проверить, что нет runtime DB/data/cache.
4. После успешного аудита сделать targeted commit Stage04E implementation.
5. Потом отдельный commit audit report.
```

Ожидаемые Stage04E files:

```text
inventory-sales-module/requirements.txt
inventory-sales-module/app/core_client.py
inventory-sales-module/app/schemas.py
inventory-sales-module/app/routers/sales.py
inventory-sales-module/app/routers/products.py
inventory-sales-module/app/main.py
inventory-sales-module/app/templates/base.html
inventory-sales-module/app/templates/index.html
inventory-sales-module/app/templates/products.html
inventory-sales-module/app/templates/product_detail.html
inventory-sales-module/app/templates/sales_new.html
inventory-sales-module/app/templates/sales_detail.html
inventory-sales-module/app/templates/sales_list.html
inventory-sales-module/app/static/app.css
inventory-sales-module/app/static/app.js
inventory-sales-module/tests/test_sales_routes.py
inventory-sales-module/tests/test_core_client_sales.py
inventory-sales-module/tests/test_sales_ui_russian.py
inventory-sales-module/tests/test_sales_no_direct_db_access.py
docs/stage04e_sales_ui_mvp.md
docs/inventory_sales_module_ui_map.md
docs/inventory_sales_module_core_api_contract.md
inventory-sales-module/README.md
reports/stage04e_sales_ui_mvp_report.md
logs/2026-07-02.md
.agents/received_prompts/TECHNOREBOOT_STAGE04E_SALES_UI_MVP_PROMPT.md
```

---

# 7. Docker rebuild audit

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
inventory-sales-module up
нет restart loop
inventory-sales-module порт 8030
```

Логи:

```powershell
docker compose logs --tail=200 inventory-sales-module
docker compose logs --tail=150 core
docker compose logs --tail=100 avito-module
```

---

# 8. Core regression investigation: SKU collision

Обязательно расследовать падение Core pytest:

```text
test_create_product_and_sale
SKU collision SALE-TEST-001
```

Выполнить:

```powershell
docker compose exec core pytest -q
```

Если падает из-за persistent DB collision:

```text
не принимать просто как "existing issue"
проверить, можно ли сделать тест уникальным SKU
проверить, нет ли теста, зависящего от persistent DB state
```

Найти тест:

```powershell
Select-String -Path core\tests\*.py -Pattern "SALE-TEST-001|test_create_product_and_sale|SALE-TEST"
```

Если тест использует фиксированный SKU, это test isolation bug. Разрешено исправить тест безопасно:

```text
использовать uuid suffix
или clean test setup
```

После исправления:

```powershell
docker compose exec core pytest
```

Ожидание:

```text
полный Core pytest должен проходить
```

Если не удалось исправить быстро — Stage04E-Audit = FAIL или PASS_WITH_NOTES только если четко доказано, что Stage04E не виноват и есть отдельный repair prompt.

---

# 9. Inventory-sales-module tests

Выполнить:

```powershell
docker compose exec inventory-sales-module pytest -v
```

Ожидание:

```text
26 tests passed или больше
```

Проверить, что tests покрывают:

```text
sales routes
CoreClient sales methods
русский UI
нет direct DB access
```

---

# 10. Avito regression

Выполнить:

```powershell
docker compose exec avito-module pytest
Invoke-RestMethod http://127.0.0.1:8020/health
Invoke-RestMethod http://127.0.0.1:8020/api/core/health
```

Ожидание:

```text
avito-module не сломан
```

---

# 11. API smoke inventory-sales-module

Проверить:

```powershell
Invoke-RestMethod http://127.0.0.1:8030/health
Invoke-RestMethod http://127.0.0.1:8030/api/version
Invoke-RestMethod http://127.0.0.1:8030/api/core/health
Invoke-WebRequest http://127.0.0.1:8030/products | Select-Object StatusCode
Invoke-WebRequest http://127.0.0.1:8030/sales | Select-Object StatusCode
```

Ожидание:

```text
все 200
нет 500
```

---

# 12. Real UI sale smoke

Нужно проверить реальный flow через HTTP.

## 12.1 Найти или создать товар

Взять товар in_stock/reserved:

```powershell
$products = Invoke-RestMethod "http://127.0.0.1:8000/api/products?status=in_stock&limit=5"
$productId = $products.items[0].id
```

Если нет товара, создать тестовый через import-json с уникальным SKU.

Пример допустимого test payload:

```powershell
$sku = "UI-SALE-AUDIT-" + [guid]::NewGuid().ToString("N").Substring(0,8)

$payload = @{
  source = "audit"
  schema_version = "1.0"
  operation = "create_or_update"
  product = @{
    sku = $sku
    title = "Тестовый товар для аудита продажи"
    category_path = @("Аудит")
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
  -Body '{"status":"in_stock","reason":"Stage04E audit UI sale smoke"}'
```

## 12.2 Проверить форму продажи

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/sales/new?product_id=$productId" | Select-Object StatusCode
```

Проверить HTML содержит:

```text
Подтвердить продажу
Цена продажи
Способ оплаты
Наличные
```

## 12.3 Отправить продажу через UI route

```powershell
$form = @{
  product_id = $productId
  price = "12345"
  payment_method = "cash"
  notes = "Stage04E audit UI sale"
}

$saleResponse = Invoke-WebRequest `
  -Method Post `
  -Uri http://127.0.0.1:8030/sales/create `
  -Body $form `
  -MaximumRedirection 0 `
  -ErrorAction SilentlyContinue
```

Если redirect ожидаемый, проверить Location.

Потом проверить товар:

```powershell
$productAfter = Invoke-RestMethod "http://127.0.0.1:8000/api/products/$productId"
$productAfter.status
```

Ожидание:

```text
sold
```

## 12.4 Проверить повторная продажа недоступна

```powershell
$page = Invoke-WebRequest "http://127.0.0.1:8030/sales/new?product_id=$productId"
$page.Content
```

Ожидание:

```text
Товар нельзя продать
или кнопка подтверждения отсутствует/disabled
```

---

# 13. Sale detail/list audit

Проверить:

```powershell
Invoke-WebRequest http://127.0.0.1:8030/sales | Select-Object StatusCode
```

Если sale_id известен:

```powershell
Invoke-WebRequest "http://127.0.0.1:8030/sales/<sale_id>" | Select-Object StatusCode
```

Проверить в HTML:

```text
Продажа оформлена
Номер продажи
Способ оплаты
Вернуться к товарам
```

---

# 14. Core status/audit validation

Проверить через Core:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/products/$productId/details" | ConvertTo-Json -Depth 10
Invoke-RestMethod "http://127.0.0.1:8000/api/sales/today" | ConvertTo-Json -Depth 10
```

Проверить:

```text
product status sold
sale видна в sales/today
product event есть, если details возвращает events
```

---

# 15. Russian UI audit

Проверить templates:

```powershell
Get-ChildItem inventory-sales-module\app\templates -Recurse -File |
  Select-String -Pattern "Sale|Sell|Payment|Submit|Success|Error|Back|Price Tags|Products" -CaseSensitive:$false
```

Оценить:

```text
пользовательский английский — issue
технические переменные/classes — допустимо
```

Проверить, что есть русский текст:

```powershell
Get-ChildItem inventory-sales-module\app\templates -Recurse -File |
  Select-String -Pattern "Продажа|Продать|Подтвердить продажу|Цена продажи|Способ оплаты|Наличные|Карта|Перевод|Продажа оформлена|Товар нельзя продать|Вернуться к товарам"
```

---

# 16. No price tags / no cancel UI audit

Проверить, что Stage04E не начал Stage04F или отмену продаж:

```powershell
git grep -n -I "price-tag\|price_tag\|window.print\|Печать\|PDF\|cancel_sale\|/cancel\|Отменить продажу\|Возврат" -- inventory-sales-module
```

Оценить:

```text
placeholder "Ценники — скоро" допустим
реальная печать/PDF — блокер
cancel sale UI — out of scope
```

---

# 17. Direct DB access audit

Выполнить:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Ожидание:

```text
нет прямого DB access
```

---

# 18. Safety scans

Выполнить:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
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
```

---

# 19. Documentation audit

Проверить:

```text
docs/stage04e_sales_ui_mvp.md
docs/inventory_sales_module_ui_map.md
docs/inventory_sales_module_core_api_contract.md
inventory-sales-module/README.md
reports/stage04e_sales_ui_mvp_report.md
logs/2026-07-02.md
```

Документация должна отражать:

```text
Stage04E — продажа через UI
только через Core API
после продажи status=sold
повторная продажа недоступна
отмена продажи не входит
ценники не входят
```

---

# 20. Audit report

Создать:

```text
reports/stage04e_audit_sales_ui_mvp_report.md
```

Структура:

```text
# Stage 04E-Audit Sales UI MVP Report

## STATUS

PASS / PASS_WITH_NOTES / FAIL

## EXECUTIVE SUMMARY

Можно ли переходить к Stage04F.

## PROMPT DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## ENVIRONMENT

Branch:
Head:
Core URL:
Inventory/Sales URL:
Docker status:

## GIT_STATE_AUDIT

Worktree before audit:
Uncommitted Stage04E files:
Unexpected files:
Findings:

## CORE_REGRESSION_SKU_COLLISION_AUDIT

What failed:
Root cause:
Fix applied:
Final core pytest:

## INVENTORY_TESTS

## AVITO_REGRESSION

## API_SMOKE

## REAL_UI_SALE_SMOKE

Product id:
Sale id:
Result:
Product status after sale:
Repeat sale blocked:

## SALE_LIST_DETAIL_AUDIT

## CORE_STATUS_AUDIT

## RUSSIAN_UI_AUDIT

## OUT_OF_SCOPE_AUDIT

Price tags started:
Cancel sale UI started:
Findings:

## DIRECT_DB_ACCESS_AUDIT

## SAFETY_SCAN

## RUNTIME_DATA_AUDIT

## DOCUMENTATION_AUDIT

## BLOCKERS

## NON_BLOCKING_ISSUES

## RECOMMENDED_NEXT_STAGE

Варианты:
- Stage04E-R — repair, если есть блокеры
- Stage04F — Price Tags MVP
```

---

# 21. Git commit strategy

Если аудит PASS/PASS_WITH_NOTES и Stage04E implementation корректна:

## 21.1 Сначала commit Stage04E implementation

Targeted add only.

```powershell
git add inventory-sales-module/requirements.txt
git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/schemas.py
git add inventory-sales-module/app/routers/sales.py
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/main.py
git add inventory-sales-module/app/templates/base.html
git add inventory-sales-module/app/templates/index.html
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/templates/product_detail.html
git add inventory-sales-module/app/templates/sales_new.html
git add inventory-sales-module/app/templates/sales_detail.html
git add inventory-sales-module/app/templates/sales_list.html
git add inventory-sales-module/app/static/app.css
git add inventory-sales-module/app/static/app.js
git add inventory-sales-module/tests/test_sales_routes.py
git add inventory-sales-module/tests/test_core_client_sales.py
git add inventory-sales-module/tests/test_sales_ui_russian.py
git add inventory-sales-module/tests/test_sales_no_direct_db_access.py
git add docs/stage04e_sales_ui_mvp.md
git add docs/inventory_sales_module_ui_map.md
git add docs/inventory_sales_module_core_api_contract.md
git add inventory-sales-module/README.md
git add reports/stage04e_sales_ui_mvp_report.md
git add logs/2026-07-02.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_SALES_UI_MVP_PROMPT.md

git commit -m "Add sales UI MVP"
```

If core test isolation fix was needed:

```powershell
git add core/tests/<changed_test_file>.py
git commit -m "Fix Core sales test isolation"
```

or include before implementation commit only if clearly part of audit repair and document it.

## 21.2 Затем commit audit report

```powershell
git add reports/stage04e_audit_sales_ui_mvp_report.md
git add logs/2026-07-02.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_AUDIT_SALES_UI_MVP_PROMPT.md

git commit -m "Audit Stage 04E sales UI MVP"
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

Stage04E-Audit готов, если:

```text
prompt найден и скопирован
dirty worktree Stage04E проверен
unexpected files отсутствуют
Docker rebuild выполнен
Core SKU collision расследован
Core pytest pass
inventory-sales-module pytest pass
avito-module pytest pass
/sales opens
/sales/new opens
POST /sales/create реально создает sale через Core
товар становится sold
повторная продажа заблокирована
/sales/{id} показывает sale
UI русский
нет direct DB access
ценники не начаты
cancel sale UI не начат
runtime data не закоммичена
docs/report проверены
Stage04E implementation commit создан
audit commit создан
```

---

# 23. Ожидаемый итог

Если всё хорошо:

```text
STATUS: PASS
Recommended next stage: Stage04F — Price Tags MVP
```

Если есть мелкие замечания:

```text
STATUS: PASS_WITH_NOTES
Recommended next stage: Stage04F или Stage04E-R
```

Если есть блокеры:

```text
STATUS: FAIL
Recommended next stage: Stage04E-R
```

---

# 24. Главный принцип

Stage04E должен доказать реальный рабочий цикл:

```text
товар в Core → продажа через inventory-sales-module UI → Core sale → product status sold → повторная продажа заблокирована
```

Ценники делать только после успешного Stage04E-Audit.
