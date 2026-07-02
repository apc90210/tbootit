# PROMPT — Техноребут / Stage 04E Sales UI MVP

## Роль агента

Ты senior fullstack developer, backend/frontend integrator и business-flow engineer проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — реализовать Stage 04E: добавить в `inventory-sales-module` MVP-продажу товара через UI, используя только Core API.

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
```

Известный итог Stage04D-Audit:

```text
STATUS: PASS
inventory-sales-module работает на 8030
UI на русском
прямого DB access нет
tests passed: inventory-sales 8, core 34, avito 12
recommended next stage: Stage04E — Sales UI MVP
```

Важный caveat:

```text
после audit commit Stage04D агент дописал final entry в logs/2026-07-01.md
перед началом Stage04E обязательно проверить git status
если logs/2026-07-01.md dirty — сделать targeted commit только этого лога или включить в Stage04E commit, явно описав в report
```

---

# 3. Цель Stage04E

Добавить в `inventory-sales-module` реальный MVP flow продажи товара через Core API.

Пользовательский сценарий:

```text
1. Оператор открывает список товаров.
2. Видит товар в статусе "В наличии" или "Резерв".
3. Нажимает "Продать".
4. Открывается форма продажи.
5. Оператор проверяет товар, цену, способ оплаты.
6. Нажимает "Подтвердить продажу".
7. inventory-sales-module отправляет POST /api/sales в Core.
8. Core создает продажу.
9. Core меняет товар status=sold.
10. UI показывает успешную продажу.
11. Товар больше нельзя продать повторно.
```

Stage04E должен реализовать только продажу через UI.

---

# 4. Что запрещено в Stage04E

Не делать:

```text
ценники
печать
PDF
bulk sales
корзину из нескольких товаров, если это сильно усложняет
отмену продажи через UI
возврат через UI
редактирование товара
изменение Core DB напрямую
собственную БД inventory-sales-module
изменение avito-module
изменение admin-shell
browser automation
crawling
```

Разрешено:

```text
изменять inventory-sales-module
минимально расширить Core client в inventory-sales-module
добавить sales UI routes/templates/tests
добавить docs/report/logs
при необходимости добавить малые безопасные fixes в Core, если Stage04E smoke обнаружит явный 500 bug, но лучше остановиться и зафиксировать issue
```

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

# 6. Preflight

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

Особо проверить:

```text
не остался ли dirty logs/2026-07-01.md после Stage04D-Audit
```

Если dirty только expected log final entry — можно включить в Stage04E commit, но обязательно описать в report.

Если есть другие unexpected dirty files — остановиться и разобраться.

Обязательно запустить regression перед началом:

```powershell
docker compose exec core pytest
docker compose exec avito-module pytest
docker compose exec inventory-sales-module pytest
```

Если regression не проходит — не начинать Stage04E.

---

# 7. Проверка Core Sales API перед UI

Перед реализацией проверить, что Core sales API работает:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/sales | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/sales/today | ConvertTo-Json -Depth 5
```

Проверить, что есть хотя бы один товар.

Если нет товара в статусе `in_stock`, можно создать/импортировать тестовый товар через existing Core API или использовать seed/dev flow, но не коммитить runtime DB.

---

# 8. Функциональные требования Sales UI MVP

## 8.1 Кнопка "Продать" в списке товаров

В `/products`:

```text
если status in_stock или reserved:
  кнопка "Продать" активна
иначе:
  кнопка "Продать" disabled с подсказкой "Продажа недоступна для этого статуса"
```

Кнопка ведет:

```text
GET /sales/new?product_id=<id>
```

## 8.2 Кнопка "Продать" в карточке товара

В `/products/{id}`:

```text
если товар можно продать — активная кнопка "Продать"
если нельзя — disabled/подсказка
```

## 8.3 Форма продажи

Добавить route:

```text
GET /sales/new
```

Query:

```text
product_id
```

Форма должна показать:

```text
товар
артикул
статус
цена
поле "Цена продажи"
способ оплаты
примечание
кнопка "Подтвердить продажу"
кнопка "Назад"
```

Способы оплаты в UI:

```text
cash      → Наличные
card      → Карта
transfer  → Перевод
mixed     → Смешанная оплата
other     → Другое
```

Если товар нельзя продать:

```text
показать ошибку "Товар нельзя продать в текущем статусе"
не показывать кнопку подтверждения
```

## 8.4 Создание продажи

Добавить route:

```text
POST /sales/create
```

Форма отправляет:

```text
product_id
price
payment_method
notes
```

`inventory-sales-module` должен отправить в Core:

```text
POST http://core:8000/api/sales
```

Payload:

```json
{
  "customer_id": null,
  "payment_method": "cash",
  "notes": "....",
  "items": [
    {
      "product_id": 1,
      "quantity": 1,
      "price": 25000
    }
  ]
}
```

После успеха:

```text
redirect на /sales/{sale_id}
или страница success
```

Рекомендуемый route:

```text
GET /sales/{sale_id}
```

## 8.5 Страница успешной продажи

Добавить:

```text
GET /sales/{sale_id}
```

Показывает:

```text
Продажа оформлена
Номер продажи
Дата/время
Товар
Цена
Способ оплаты
Статус товара после продажи
Ссылка "Вернуться к товарам"
```

## 8.6 Список продаж MVP

Добавить route:

```text
GET /sales
```

Показывает:

```text
последние продажи
pagination простая
sale id
дата
сумма
способ оплаты
статус
```

---

# 9. CoreClient changes

Расширить `inventory-sales-module/app/core_client.py`.

Добавить методы:

```text
create_sale(product_id, price, payment_method, notes=None)
get_sale(sale_id)
get_sales(params=None)
get_sales_today()
```

Не добавлять:

```text
cancel_sale
patch_product
change_status
```

Cancel будет позже.

---

# 10. Schemas

Расширить `inventory-sales-module/app/schemas.py`.

Добавить:

```text
SaleCreateForm
SaleView
SaleListItem
PaymentMethod enum-like validation
```

Можно держать Pydantic минимальным, но UI validation должна быть понятной.

---

# 11. UI templates

Создать:

```text
inventory-sales-module/app/templates/sales_new.html
inventory-sales-module/app/templates/sales_detail.html
inventory-sales-module/app/templates/sales_list.html
```

Обновить:

```text
base.html
index.html
products.html
product_detail.html
```

Навигация:

```text
Главная
Товары
Продажи
Ценники — скоро
```

`Ценники` пока placeholder.

---

# 12. Русский UI

Весь пользовательский текст — русский.

Использовать:

```text
Продажа
Новая продажа
Подтвердить продажу
Цена продажи
Способ оплаты
Наличные
Карта
Перевод
Смешанная оплата
Другое
Продажа оформлена
Ошибка продажи
Товар нельзя продать
Вернуться к товарам
```

Не использовать пользовательские английские:

```text
Sale
Sell
Payment
Submit
Success
Error
Back
```

---

# 13. Error handling

Если Core вернул ошибку при продаже:

```text
показать страницу/блок ошибки на русском
не скрывать причину полностью
не показывать raw traceback
```

Примеры:

```text
Товар уже продан
Товар нельзя продать в текущем статусе
Некорректный способ оплаты
Ошибка Core API
```

---

# 14. Tests

Добавить/обновить tests:

```text
inventory-sales-module/tests/test_sales_routes.py
inventory-sales-module/tests/test_core_client_sales.py
inventory-sales-module/tests/test_sales_ui_russian.py
inventory-sales-module/tests/test_sales_no_direct_db_access.py
```

Покрыть:

```text
GET /sales returns list page
GET /sales/new?product_id=... renders sale form for sellable product
GET /sales/new rejects sold product / shows disabled error
POST /sales/create calls CoreClient.create_sale
successful sale redirects/shows sale detail
Core error is rendered in Russian
GET /sales/{id} renders sale detail
products page has "Продать" button
non-sellable product disables sale action
no direct DB access
```

Запуск:

```powershell
docker compose exec inventory-sales-module pytest
```

---

# 15. Manual smoke

После реализации:

```powershell
docker compose up --build -d
docker compose ps
```

Проверить:

```powershell
Invoke-RestMethod http://127.0.0.1:8030/health
Invoke-RestMethod http://127.0.0.1:8030/api/core/health
Invoke-WebRequest http://127.0.0.1:8030/products | Select-Object StatusCode
Invoke-WebRequest http://127.0.0.1:8030/sales | Select-Object StatusCode
```

Ручной flow:

```text
1. Открыть http://127.0.0.1:8030/products
2. Выбрать товар in_stock/reserved
3. Нажать "Продать"
4. Указать цену и способ оплаты
5. Подтвердить продажу
6. Увидеть страницу успешной продажи
7. Вернуться к карточке товара
8. Проверить, что статус стал sold
9. Проверить, что повторная продажа недоступна
```

---

# 16. Regression tests

После реализации обязательно:

```powershell
docker compose exec inventory-sales-module pytest
docker compose exec core pytest
docker compose exec avito-module pytest
```

---

# 17. Safety scans

Direct DB access:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy\|SELECT .* FROM\|INSERT INTO" -- inventory-sales-module
```

Ожидание:

```text
нет прямого DB access
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

# 18. Documentation

Создать/обновить:

```text
docs/stage04e_sales_ui_mvp.md
docs/inventory_sales_module_ui_map.md
docs/inventory_sales_module_core_api_contract.md
inventory-sales-module/README.md
```

Документация должна сказать:

```text
Stage04E реализует продажу через UI
Продажа идет только через Core API
После продажи Core меняет status=sold
Повторная продажа недоступна
Отмена продажи не входит в Stage04E
Ценники не входят в Stage04E
```

---

# 19. Report

Создать:

```text
reports/stage04e_sales_ui_mvp_report.md
```

Структура:

```text
# Stage 04E Sales UI MVP Report

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

## ROUTES

## CORE_CLIENT_CHANGES

## UI_FLOW

## SELLABLE_STATUS_RULES

## PAYMENT_METHODS

## ERROR_HANDLING

## RUSSIAN_UI

## TESTS

## MANUAL_SMOKE

## REGRESSION_CHECKS

## SAFETY_SCAN

## FILES_CREATED

## FILES_MODIFIED

## BLOCKERS

## NEXT_RECOMMENDED_STAGE

Stage04E-Audit — Sales UI MVP Audit
```

Expected final status:

```text
TECHNOREBOOT_STAGE04E_SALES_UI_MVP_READY_FOR_AUDIT
```

---

# 20. Logging

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
dirty worktree handling from Stage04D, if any
files changed
tests
manual smoke
final status
```

---

# 21. Git

После успешной проверки использовать только targeted git add.

Пример:

```powershell
git status --short --untracked-files=all

git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/schemas.py
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/routers/sales.py
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
git add logs/2026-07-01.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04E_SALES_UI_MVP_PROMPT.md

git commit -m "Add sales UI MVP"
git status --short --untracked-files=all
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

Stage04E готов, если:

```text
prompt найден и скопирован
preflight выполнен
dirty worktree после Stage04D обработан
full regression before start passed
/products показывает active "Продать" для sellable товаров
/products/{id} показывает active "Продать" для sellable товара
/sales открывается
/sales/new?product_id=... открывается
POST /sales/create создает продажу через Core API
после продажи товар становится sold
повторная продажа недоступна
/sales/{id} показывает продажу
ошибки Core отображаются на русском
нет прямого DB access
нет ценников/печати
inventory-sales-module tests pass
core tests pass
avito-module tests pass
manual smoke pass
docs/report/logs созданы
commit создан
```

---

# 23. Главный принцип

Stage04E должен доказать:

```text
оператор может продать товар из отдельного inventory-sales-module
продажа проходит через Core API
Core меняет товар на sold
UI показывает результат на русском
```

Ценники — следующий этап Stage04F.
