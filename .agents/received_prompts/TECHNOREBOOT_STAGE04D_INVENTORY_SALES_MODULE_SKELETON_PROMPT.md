# PROMPT — Техноребут / Stage 04D Inventory/Sales Module Skeleton

## Роль агента

Ты senior fullstack developer, backend/frontend integrator и Docker-oriented engineer проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — реализовать Stage 04D: создать отдельный `inventory-sales-module` как рабочий skeleton-модуль магазина.

Это первый технический этап нового модуля.  
На этом этапе делаем только read-only основу:

```text
health
Core API client
список товаров
карточка товара
базовый русский UI
Docker service
тесты
документация
```

Не реализовывать продажу товара и ценники в Stage04D.

---

# 1. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ.

Главная архитектура:

```text
Core API + DB + Storage = единое ядро.
Все остальные модули работают только через HTTP API.
```

Внешние модули не должны читать или писать БД напрямую.

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
```

Известный итог Stage04C-Audit:

```text
STATUS: PASS
sales flow hardened
Stage04C implementation committed
Stage04C audit committed
recommended next stage: Stage04D — Inventory/Sales Module Skeleton
```

Важная caveat:

```text
финальный лог Stage04C-Audit явно указал только test_sales_flow.py (3/3 passed)
поэтому Stage04D preflight обязан запустить полный core pytest и avito-module pytest
```

---

# 3. Цель Stage04D

Создать отдельный Docker-модуль:

```text
inventory-sales-module
```

Порт:

```text
8030
```

URL:

```text
http://127.0.0.1:8030
```

Назначение Stage04D:

```text
1. Поднять отдельный сервис.
2. Сделать health/version endpoints.
3. Сделать Core API client.
4. Сделать русскоязычный read-only UI.
5. Показать список товаров из Core.
6. Показать карточку товара из Core.
7. Показать базовую страницу статуса связи с Core.
8. Добавить tests.
9. Добавить docs/report.
```

Stage04D — это skeleton, не полноценный sales UI.

---

# 4. Что запрещено в Stage04D

Не делать:

```text
продажу товара через UI
POST /api/sales из UI
отмену продажи
ценники
PDF
печать
изменение Avito Module
изменение Admin Shell
прямой доступ к Core DB
собственную БД модуля
browser automation
crawling
```

Разрешено:

```text
read-only запросы к Core
получение списка товаров
получение карточки товара
простая русская HTML-оболочка
Docker service
tests
docs/report
```

Если нужен action button «Продать» или «Ценник», сделать его disabled/placeholder с надписью:

```text
Будет реализовано на следующем этапе
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

Обязательно запустить full regression:

```powershell
docker compose exec core pytest
docker compose exec avito-module pytest
```

Если full regression не проходит — не начинать Stage04D.  
Сначала зафиксировать проблему и остановиться.

Проверить наличие отчетов:

```text
reports/stage04b_inventory_sales_price_tags_module_planning_report.md
reports/stage04c_core_sales_flow_hardening_report.md
reports/stage04c_audit_core_sales_flow_hardening_report.md
```

---

# 7. Структура нового модуля

Создать:

```text
inventory-sales-module/
  Dockerfile
  requirements.txt
  README.md
  app/
    __init__.py
    main.py
    config.py
    core_client.py
    schemas.py
    routers/
      __init__.py
      health.py
      products.py
    templates/
      base.html
      index.html
      products.html
      product_detail.html
      error.html
    static/
      app.css
      app.js
  tests/
    test_health.py
    test_core_client.py
    test_products_routes.py
    test_no_direct_db_access.py
```

Не создавать БД для модуля.

---

# 8. Docker Compose

Добавить сервис в корневой `docker-compose.yml`:

```yaml
  inventory-sales-module:
    build:
      context: ./inventory-sales-module
    container_name: technoreboot-inventory-sales-module
    environment:
      INVENTORY_SALES_MODULE_NAME: technoreboot-inventory-sales-module
      CORE_API_BASE_URL: http://core:8000
    ports:
      - "8030:8030"
    depends_on:
      - core
```

Для dev-удобства можно добавить volume mounts:

```yaml
    volumes:
      - ./inventory-sales-module/app:/app/app
      - ./inventory-sales-module/tests:/app/tests
```

Но убедиться, что это не ломает production build.

---

# 9. Requirements

Минимальный стек:

```text
fastapi
uvicorn[standard]
httpx
jinja2
pydantic
pytest
```

Не добавлять:

```text
sqlalchemy
sqlite
playwright
selenium
browser automation dependencies
PDF generators
```

---

# 10. Core client

Создать:

```text
inventory-sales-module/app/core_client.py
```

CoreClient должен уметь:

```text
health()
get_products(params)
get_product(product_id)
get_product_details(product_id)
```

Не должен уметь на Stage04D:

```text
create_sale()
cancel_sale()
patch_product()
change_status()
```

Эти методы можно оставить как TODO в docs, но не реализовывать.

Error handling:

```text
если Core недоступен — UI показывает понятную русскую ошибку
если Core вернул 404 — UI показывает "Товар не найден"
если Core вернул 500 — UI показывает "Ошибка Core API"
```

---

# 11. API endpoints модуля

Добавить endpoints:

```text
GET /health
GET /api/version
GET /api/core/health
```

Ожидаемый `/health`:

```json
{
  "status": "ok",
  "module": "inventory-sales-module"
}
```

Ожидаемый `/api/core/health`:

```json
{
  "core_available": true,
  "core_response": {...}
}
```

---

# 12. HTML UI routes

Добавить UI routes:

```text
GET /
GET /products
GET /products/{product_id}
```

## 12.1 Главная `/`

Русский dashboard skeleton:

```text
Техноребут — Рабочее место магазина
Статус Core API
Быстрые ссылки:
- Товары
- Продажи — скоро
- Ценники — скоро
```

## 12.2 Список товаров `/products`

Должен через Core API вызвать:

```text
GET /api/products
```

Поддержать query params:

```text
q
status
limit
offset
sort
```

UI:

```text
поисковая строка
фильтр статус
таблица товаров
пагинация минимум "Назад/Вперед"
```

Таблица:

```text
Артикул
Название
Статус
Цена
Остаток
Место хранения
Действия
```

Действия:

```text
Открыть
Продать — disabled, "Stage04E"
Ценник — disabled, "Stage04F"
```

## 12.3 Карточка товара `/products/{product_id}`

Должна через Core API вызвать:

```text
GET /api/products/{id}/details
```

Показать:

```text
Название
Артикул
Статус
Цена
Бренд
Модель
Описание
Остаток
Место хранения
Avito status/link если есть
Site status если есть
История событий, если есть в details
```

Кнопки:

```text
Назад к товарам
Продать — disabled
Ценник — disabled
```

---

# 13. Русский UI

Весь пользовательский UI должен быть на русском.

Запрещены пользовательские английские кнопки:

```text
Products
Sales
Price Tags
Open
Sell
Print
Error
```

Допустимы технические имена в коде/API.

---

# 14. Tests

Добавить tests:

```text
inventory-sales-module/tests/test_health.py
inventory-sales-module/tests/test_core_client.py
inventory-sales-module/tests/test_products_routes.py
inventory-sales-module/tests/test_no_direct_db_access.py
```

Проверить:

```text
/health returns ok
/api/version returns module info
CoreClient builds requests to Core
/products route renders with mocked Core response
/products/{id} route renders with mocked Core response
no direct DB imports/dependencies
requirements.txt does not include sqlalchemy/sqlite/playwright/selenium
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
Invoke-RestMethod http://127.0.0.1:8030/api/version
Invoke-RestMethod http://127.0.0.1:8030/api/core/health
```

Проверить HTML:

```text
http://127.0.0.1:8030/
http://127.0.0.1:8030/products
http://127.0.0.1:8030/products/<existing_product_id>
```

---

# 16. Regression tests

После реализации обязательно:

```powershell
docker compose exec core pytest
docker compose exec avito-module pytest
docker compose exec inventory-sales-module pytest
```

Если один из сервисов не поднялся — исправить или остановиться с FAIL.

---

# 17. Safety scans

Выполнить:

```powershell
git grep -n -I "create_engine\|SessionLocal\|sqlite\|technoreboot.db\|data/db\|sqlalchemy" -- inventory-sales-module
```

Ожидание:

```text
нет прямого DB access
```

Выполнить:

```powershell
git grep -n -I "selenium\|playwright\|webdriver\|undetected\|pyppeteer\|captcha solver\|captcha-solver\|bypass captcha\|обход капчи\|автологин\|auto login\|chromium" -- core admin-shell avito-module inventory-sales-module
```

Ожидание:

```text
нет browser automation/captcha bypass
```

Проверить runtime data:

```powershell
git status --ignored --short --untracked-files=all -- data/db
git status --ignored --short --untracked-files=all -- data/avito-module
```

---

# 18. Documentation

Создать/обновить:

```text
inventory-sales-module/README.md
docs/stage04d_inventory_sales_module_skeleton.md
docs/inventory_sales_module_architecture.md
docs/inventory_sales_module_ui_map.md
```

В docs указать:

```text
Stage04D — read-only skeleton
Продажи будут Stage04E
Ценники будут Stage04F
Модуль работает только через Core API
Прямой доступ к DB запрещен
```

---

# 19. Report

Создать:

```text
reports/stage04d_inventory_sales_module_skeleton_report.md
```

Структура:

```text
# Stage 04D Inventory/Sales Module Skeleton Report

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

## MODULE_BOUNDARY

## DOCKER_SERVICE

## UI_ROUTES

## API_ENDPOINTS

## CORE_CLIENT

## RUSSIAN_UI

## TESTS

## MANUAL_SMOKE

## REGRESSION_CHECKS

## SAFETY_SCAN

## FILES_CREATED

## FILES_MODIFIED

## BLOCKERS

## NEXT_RECOMMENDED_STAGE

Stage04D-Audit — Inventory/Sales Module Skeleton Audit
```

Expected final status:

```text
TECHNOREBOOT_STAGE04D_INVENTORY_SALES_MODULE_SKELETON_READY_FOR_AUDIT
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
full regression before start
files changed
tests
manual smoke
final status
```

---

# 21. Git

После успешной проверки:

```powershell
git status --short --untracked-files=all

git add inventory-sales-module/Dockerfile
git add inventory-sales-module/requirements.txt
git add inventory-sales-module/README.md
git add inventory-sales-module/app/__init__.py
git add inventory-sales-module/app/main.py
git add inventory-sales-module/app/config.py
git add inventory-sales-module/app/core_client.py
git add inventory-sales-module/app/schemas.py
git add inventory-sales-module/app/routers/__init__.py
git add inventory-sales-module/app/routers/health.py
git add inventory-sales-module/app/routers/products.py
git add inventory-sales-module/app/templates/base.html
git add inventory-sales-module/app/templates/index.html
git add inventory-sales-module/app/templates/products.html
git add inventory-sales-module/app/templates/product_detail.html
git add inventory-sales-module/app/templates/error.html
git add inventory-sales-module/app/static/app.css
git add inventory-sales-module/app/static/app.js
git add inventory-sales-module/tests/test_health.py
git add inventory-sales-module/tests/test_core_client.py
git add inventory-sales-module/tests/test_products_routes.py
git add inventory-sales-module/tests/test_no_direct_db_access.py
git add docker-compose.yml
git add docs/stage04d_inventory_sales_module_skeleton.md
git add docs/inventory_sales_module_architecture.md
git add docs/inventory_sales_module_ui_map.md
git add reports/stage04d_inventory_sales_module_skeleton_report.md
git add logs/2026-07-01.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04D_INVENTORY_SALES_MODULE_SKELETON_PROMPT.md

git commit -m "Add inventory sales module skeleton"
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

Stage04D готов, если:

```text
prompt найден и скопирован
preflight выполнен
full core pytest before start passed
full avito-module pytest before start passed
создан inventory-sales-module
добавлен Docker service 8030
/health работает
/api/version работает
/api/core/health работает
/ открывается
/products открывается и показывает данные Core
/products/{id} открывается и показывает карточку Core
UI на русском
продажи disabled/placeholder
ценники disabled/placeholder
нет прямого DB access
tests inventory-sales-module pass
core pytest pass
avito-module pytest pass
manual smoke pass
docs/report/logs созданы
commit создан
```

---

# 23. Главный принцип

Stage04D — это отдельный read-only рабочий модуль магазина.

Он должен показать:

```text
товары из Core видны в отдельном модуле
карточки товаров открываются
Core API связь стабильна
```

Но еще не должен:

```text
продавать
печатать ценники
изменять товары
```

Продажи — Stage04E.  
Ценники — Stage04F.
