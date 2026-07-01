# PROMPT — Техноребут / Stage 04B Inventory, Sales & Price Tags Module Planning

## Роль агента

Ты senior product architect, fullstack architect, backend/API designer и постановщик задач проекта «Техноребут».

Рабочий репозиторий:

```powershell
C:\tbootit
```

Твоя задача — выполнить Stage 04B: спроектировать отдельный рабочий модуль для товаров, продаж и ценников, который будет работать только через Core API.

Это planning/design stage. Не начинать полноценную реализацию UI, продаж или печати ценников.

---

# 1. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ-техники.

Главная архитектура:

```text
Core API + DB + Storage = единое ядро.
Все остальные модули работают только через HTTP API.
```

Core владеет:

```text
БД
товарами
карточками
продажами
статусами
историей
фото
audit log
```

Внешние модули не должны напрямую читать или писать БД.

Правильная схема:

```text
inventory-sales-module → Core API → Core DB
```

Неправильная схема:

```text
inventory-sales-module → Core DB напрямую
```

---

# 2. Текущий статус проекта

Уже выполнены и приняты/проверены:

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
```

Известный итог Stage04A-Audit:

```text
STATUS: PASS_WITH_NOTES
datetime serialization bug in audit/event logging found and fixed
Core pytest passed
Avito-module pytest passed
recommended next stage: Stage 04B — Inventory/Sales/Price Tags Module Planning
```

Текущие сервисы:

```text
Core API:      http://127.0.0.1:8000
Admin Shell:   http://127.0.0.1:8011
Avito Module:  http://127.0.0.1:8020
```

---

# 3. Бизнес-порядок, зафиксированный владельцем

Владелец зафиксировал общий порядок:

```text
1. Парсинг объявлений с Авито.
2. Добавление скачанных объявлений в базу Core через API.
3. Модуль работы с базой/товарами:
   - видеть товары в базе
   - продавать товары
   - делать ценники для печати
```

На Stage04B мы проектируем пункт 3.

---

# 4. Цель Stage04B

Спроектировать отдельный модуль:

```text
inventory-sales-module
```

Рабочее назначение:

```text
оператор магазина открывает модуль
видит товары из Core
ищет/фильтрует товары
открывает карточку товара
проверяет цену и остаток
продает товар
видит историю
печатает ценник
печатает лист ценников
```

Stage04B должен дать:

```text
архитектуру
API contract
UI map
data flows
sales flow
price tag flow
print layout requirements
Core API gaps для будущих stages
план этапов Stage04C/04D/04E
```

Stage04B не должен писать полноценную реализацию.

---

# 5. Что запрещено в Stage04B

Не делать:

```text
полноценную реализацию inventory-sales-module
реальный UI implementation
реальные продажи
реальную печать PDF
прямой доступ к БД
изменение avito-module
изменение admin-shell
browser automation
crawling
```

Разрешено:

```text
создать docs
создать planning report
создать API contract draft
создать UI mock/spec в Markdown
создать staged implementation prompts outline
проверить текущие Core API capabilities
обнаружить недостающие Core endpoints
создать небольшой read-only smoke script только если нужно
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

Проверить наличие отчетов:

```text
reports/stage04a_core_product_api_gaps_report.md
reports/stage04a_audit_core_product_api_gaps_report.md
```

Если отчеты называются иначе — найти в `reports`.

Не начинать planning поверх непонятного dirty state.

---

# 8. Проверка текущих Core API capabilities

Проверить и описать в planning report:

```text
GET /api/products
GET /api/products/{id}
GET /api/products/{id}/details
PATCH /api/products/{id}
POST /api/products/{id}/status
POST /api/product-cards/import-json
GET /api/customers
POST /api/customers
GET /api/sales
POST /api/sales
GET /api/admin/stats
```

Выполнить smoke:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/products | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/customers | ConvertTo-Json -Depth 5
Invoke-RestMethod http://127.0.0.1:8000/api/sales | ConvertTo-Json -Depth 5
```

Цель — понять, каких endpoints не хватает для будущего inventory-sales-module.

---

# 9. Проектируемый модуль

Название:

```text
inventory-sales-module
```

Порт будущего модуля:

```text
8030
```

Будущий URL:

```text
http://127.0.0.1:8030
```

Назначение:

```text
рабочее место магазина
```

Не путать с Admin Shell:

```text
Admin Shell — временная тестовая оболочка Core
inventory-sales-module — рабочий модуль магазина для оператора
```

---

# 10. Основные разделы будущего UI

Спроектировать UI map на русском.

## 10.1 Главная / Обзор

Показывает:

```text
товаров в наличии
товаров зарезервировано
товаров продано сегодня
товаров без ценника
товаров без фото
последние продажи
быстрые действия
```

## 10.2 Товары

Функции:

```text
поиск
фильтр по статусу
фильтр по категории
фильтр по бренду
фильтр по месту хранения
фильтр "готово к Авито"
фильтр "готово к сайту"
таблица товаров
открытие карточки
```

Таблица:

```text
Артикул
Название
Статус
Цена
Остаток
Место
Фото
Авито
Сайт
Действия
```

## 10.3 Карточка товара

Блоки:

```text
Основное
Фото
Цена и маржа
Остаток
История
Авито
Сайт
Продажа
Ценник
```

Действия:

```text
изменить цену
изменить статус
зарезервировать
продать
напечатать ценник
```

## 10.4 Продажа

MVP flow:

```text
выбрать товар
проверить статус in_stock/reserved
указать покупателя или "розничный покупатель"
указать цену продажи
указать способ оплаты
подтвердить продажу
Core создает sale
Core меняет товар status=sold
```

Способы оплаты:

```text
cash
card
transfer
mixed
other
```

В UI отображать:

```text
Наличные
Карта
Перевод
Смешанная оплата
Другое
```

## 10.5 Ценники

MVP flow:

```text
выбрать товар
выбрать шаблон ценника
сформировать HTML/PDF
распечатать через браузер
```

Поля ценника:

```text
название
цена
артикул
краткие характеристики
гарантия/пометка БУ
QR/штрихкод в будущем
дата печати
```

Форматы:

```text
маленький ценник
стандартный ценник
лист A4 с несколькими ценниками
```

На первом этапе можно планировать HTML print view, PDF позже.

---

# 11. Продажи: Core API gaps

Проверить существующий `POST /api/sales`.

Спроектировать, что нужно для нормального sales flow.

Вероятные endpoints:

```text
POST /api/sales
GET /api/sales
GET /api/sales/{id}
POST /api/sales/{id}/cancel
GET /api/sales/today
```

Требования к продаже:

```text
нельзя продать written_off
нельзя продать sold
нельзя продать in_repair
можно продать in_stock
можно продать reserved
после продажи товар status=sold
sale_items создаются
audit_log пишется
product_event пишется
```

Если текущий Core этого не делает — зафиксировать как Stage04C Core Sales Flow gaps.

---

# 12. Ценники: Core/API contract

Ценник не обязан храниться в Core на MVP.

Но нужно решить:

## Вариант A — price tags render в inventory-sales-module

```text
inventory-sales-module берет product details из Core
сам генерирует HTML/PDF ценник
Core ничего не знает о печати
```

## Вариант B — Core хранит price_tag templates

```text
Core хранит шаблоны ценников
модуль запрашивает template
модуль печатает
```

Рекомендация для MVP:

```text
Вариант A.
```

Потому что ценники — UI/print задача, а не базовая бизнес-логика Core.

Но Core должен отдавать все данные:

```text
title
sku
price
brand
model
condition
short specs
photos optional
```

---

# 13. Будущая структура модуля

Спроектировать структуру будущего модуля:

```text
inventory-sales-module/
  Dockerfile
  requirements.txt
  README.md
  app/
    main.py
    config.py
    core_client.py
    schemas.py
    routers/
      health.py
      products.py
      sales.py
      price_tags.py
    templates/
      index.html
      products.html
      product_detail.html
      sale.html
      price_tag.html
      price_tag_sheet.html
    static/
      app.css
      app.js
  tests/
    test_health.py
    test_core_client.py
    test_products_ui_contract.py
    test_sales_contract.py
    test_price_tag_render.py
```

Docker service:

```text
inventory-sales-module
port 8030
CORE_API_BASE_URL=http://core:8000
```

---

# 14. Data flows

Создать docs с data flows:

```text
docs/stage04b_inventory_sales_price_tags_planning.md
docs/inventory_sales_module_architecture.md
docs/inventory_sales_module_ui_map.md
docs/inventory_sales_module_core_api_contract.md
docs/price_tag_printing_design.md
```

Описать flows:

```text
product browsing flow
product detail flow
sale flow
price tag print flow
status transition flow
```

---

# 15. Разбиение дальнейших stages

Предложить следующий план:

## Stage04C — Core Sales Flow Hardening

Цель:

```text
закрыть Core gaps для продаж
валидировать продажу
sale items
status=sold
audit/product events
cancel sale если нужно
```

## Stage04D — Inventory/Sales Module Skeleton

Цель:

```text
создать отдельный модуль
Docker service 8030
health
Core client
список товаров read-only
карточка товара read-only
```

## Stage04E — Sales UI MVP

Цель:

```text
продажа товара через UI
создание sale через Core API
статус товара sold
```

## Stage04F — Price Tags MVP

Цель:

```text
HTML print view
один ценник
лист ценников
печать через браузер
```

---

# 16. Самопроверка

После planning выполнить:

```powershell
git status --short --untracked-files=all
docker compose ps
docker compose exec core pytest
docker compose exec avito-module pytest
```

Не запускать новые сервисы Stage04B, если они не создавались.

---

# 17. Отчет

Создать:

```text
reports/stage04b_inventory_sales_price_tags_module_planning_report.md
```

Структура:

```text
# Stage 04B Inventory/Sales/Price Tags Module Planning Report

## STATUS

PLANNING_READY / FAIL

## BRANCH

## HEAD

## PROMPT DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## CURRENT CORE CAPABILITIES

## IDENTIFIED CORE GAPS

## PROPOSED MODULE

Name:
Port:
Purpose:

## UI MAP

## PRODUCT BROWSING FLOW

## PRODUCT DETAIL FLOW

## SALES FLOW

## PRICE TAG FLOW

## CORE API CONTRACT

## PRICE TAG DESIGN DECISION

Chosen option:
Reason:

## FUTURE STAGES

Stage04C:
Stage04D:
Stage04E:
Stage04F:

## COMMANDS RUN

## TESTS

## FILES_CREATED

## FILES_MODIFIED

## BLOCKERS

## NEXT_RECOMMENDED_STAGE
```

Expected status:

```text
TECHNOREBOOT_STAGE04B_INVENTORY_SALES_PRICE_TAGS_PLANNING_READY
```

---

# 18. Git

После создания docs/report:

```powershell
git status --short --untracked-files=all

git add docs/stage04b_inventory_sales_price_tags_planning.md
git add docs/inventory_sales_module_architecture.md
git add docs/inventory_sales_module_ui_map.md
git add docs/inventory_sales_module_core_api_contract.md
git add docs/price_tag_printing_design.md
git add reports/stage04b_inventory_sales_price_tags_module_planning_report.md
git add logs/2026-07-01.md
git add .agents/received_prompts/TECHNOREBOOT_STAGE04B_INVENTORY_SALES_PRICE_TAGS_MODULE_PLANNING_PROMPT.md

git commit -m "Plan inventory sales price tags module"
git status --short --untracked-files=all
```

Не использовать `git add .`.

Не выполнять push без отдельной команды владельца.

---

# 19. Definition of Done

Stage04B готов, если:

```text
prompt найден и скопирован
preflight выполнен
Core API capabilities проверены
Core gaps описаны
inventory-sales-module спроектирован
UI map создан
sales flow описан
price tag flow описан
Core API contract описан
дальнейшие stages Stage04C/04D/04E/04F разложены
документация создана
отчет создан
tests regression запущены
git commit создан
```

---

# 20. Главный принцип

Stage04B — это планирование рабочего модуля магазина.

Не реализовывать UI, продажи и ценники в этом этапе.  
Сначала согласовать архитектуру, API-контракт и этапы.
