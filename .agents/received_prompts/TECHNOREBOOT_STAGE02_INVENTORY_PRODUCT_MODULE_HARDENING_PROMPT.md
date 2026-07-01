# PROMPT — Техноребут / Stage 02 Inventory & Product Module Hardening

## Роль агента

Ты senior backend/fullstack developer, архитектор товарного учёта и технический исполнитель проекта «Техноребут».

Ты работаешь в репозитории:

```powershell
C:\tbootit
```

Твоя задача — выполнить Stage 02: усилить товарный модуль, карточку товара, остатки, фильтры, статусы, историю изменений и подготовку товаров к будущим внешним модулям сайта/Авито.

---

# 1. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ-техники.

Главная архитектурная фиксация:

```text
Core API + DB + Storage = единое ядро системы.
Все остальные модули работают только через HTTP API.
```

Core API владеет:

```text
БД
файлами
фото
бизнес-логикой
audit log
admin endpoints
media endpoints
```

Admin Shell — временная внешняя русскоязычная тестовая оболочка для проверки Core MVP.  
Она должна работать только через HTTP API/proxy, без прямого доступа к БД.

---

# 2. Уже выполненные этапы

В проекте уже выполнены:

```text
Stage 01  — Core MVP Big Module
Stage 01R — Admin Shell Core API Connection Repair
Stage 01S — Admin Shell CRUD & Seed Completion Repair
Stage 01A — Independent Core MVP Audit
Stage 01T — Russian UI Localization for Admin Shell
```

Текущие адреса:

```text
Core API:    http://127.0.0.1:8000
API Docs:    http://127.0.0.1:8000/docs
Admin Shell: http://127.0.0.1:8011
```

Важно:

```text
Admin Shell порт 8011, потому что 8010 был занят.
```

---

# 3. Главное новое требование

Все пользовательские интерфейсы должны быть на русском языке.

Правило:

```text
Все, что видит обычный пользователь, должно быть на русском.
```

Допустимо оставлять на английском только технические внутренние элементы:

```text
API endpoints
имена таблиц
имена полей
переменные
классы
docker service names
enum/status values в БД
pytest names
```

Но если статус показывается в UI, рядом или вместо него должен быть русский вариант:

```text
in_stock → В наличии
reserved → Зарезервирован
sold → Продан
```

---

# 4. Цель Stage 02

Сделать товарный модуль достаточно сильным для реальной работы магазина.

После Stage 02 должно быть удобно:

```text
добавлять товар
искать товар
фильтровать товары
открывать полноценную карточку товара
видеть фото
видеть историю товара
видеть движения/события по товару
менять статусы
готовить товар к сайту
готовить товар к Авито
вести базовый учет остатков
понимать цену закупки/продажи/маржу
понимать местонахождение товара
```

Stage 02 не должен начинать отдельный сайт или полноценный Авито-модуль.  
Он должен подготовить Core API и Admin Shell к этим будущим модулям.

---

# 5. Обязательное правило поиска prompt-файлов

Перед началом работы обязательно найти актуальные prompt-файлы.

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

Выполни:

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

В итоговом отчете обязательно указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

---

# 6. Preflight

Выполни:

```powershell
Set-Location C:\tbootit

git status
git branch
git log --oneline -10

docker compose ps
docker compose config
```

Проверить наличие отчетов:

```text
reports/core_mvp_implementation_report.md
reports/stage01r_admin_shell_core_api_connection_repair_report.md
reports/stage01s_admin_shell_crud_seed_completion_report.md
reports/stage01a_independent_core_mvp_audit_report.md
reports/stage01t_russian_ui_localization_report.md
```

Если есть незакоммиченные изменения — разобраться, что это.  
Не начинать реализацию поверх непонятного dirty state.

---

# 7. Главный принцип реализации

Не ломать Stage 01.

Сначала сохранить совместимость существующих endpoints:

```text
GET    /api/products
POST   /api/products
GET    /api/products/{product_id}
PATCH  /api/products/{product_id}
PATCH  /api/products/{product_id}/status
DELETE /api/products/{product_id}
```

Можно добавлять новые поля и endpoints, но существующие сценарии должны продолжить работать.

---

# 8. Что нужно усилить в данных

Текущая БД может быть простой. На Stage 02 можно расширить модель.

## 8.1 Product fields

Проверить существующую модель `products` и добавить, если отсутствует и это безопасно:

```text
id
sku
title
category_id
brand
model
serial_number
condition
description
purchase_price
sale_price
status
storage_location
created_at
updated_at
```

Новые полезные поля Stage 02:

```text
quantity              количество, для простого учета остатков
reserved_quantity     зарезервировано
min_price             минимальная цена продажи
market_price          ориентир рыночной цены
notes                 внутренние заметки
is_published_site     флаг готовности/публикации на сайт
is_published_avito    флаг готовности/публикации на Авито
site_title            заголовок для сайта
site_description      описание для сайта
avito_title           заголовок для Авито
avito_description     описание для Авито
```

Если миграций Alembic нет, аккуратно реализовать авто-добавление недостающих колонок для SQLite или другой безопасный механизм, чтобы существующая БД не падала.

Не удалять старые данные.

## 8.2 Новая таблица product_events

Добавить таблицу истории товара:

```text
product_events
id
product_id
event_type
old_value
new_value
comment
created_at
```

Она нужна для истории:

```text
создан товар
изменён товар
изменён статус
изменена цена
изменено количество
товар зарезервирован
товар продан
товар списан
подготовлен к сайту
подготовлен к Авито
добавлено фото
```

События товара могут также дублироваться в `audit_log`, но `product_events` удобны для карточки товара.

## 8.3 Простое движение остатков

Добавить таблицу, если быстро и безопасно:

```text
stock_movements
id
product_id
movement_type
quantity_delta
old_quantity
new_quantity
reason
comment
created_at
```

Типы движения:

```text
initial
increase
decrease
reserve
unreserve
sale
write_off
repair
manual_adjustment
```

Если полноценная таблица слишком рискованна, минимум реализовать `product_events` и поле `quantity`.

---

# 9. Core API — новые/расширенные endpoints

Сохранить старые endpoints и добавить новые.

## 9.1 Поиск и фильтры товаров

Расширить:

```text
GET /api/products
```

Поддержать query parameters:

```text
q
status
category_id
brand
storage_location
min_price
max_price
has_photo
published_site
published_avito
sort
limit
offset
```

Минимум обязательно:

```text
q
status
category_id
brand
storage_location
limit
offset
```

Примеры:

```text
GET /api/products?q=lenovo
GET /api/products?status=in_stock
GET /api/products?brand=HP
GET /api/products?storage_location=Склад%201
```

## 9.2 Карточка товара

Добавить endpoint:

```text
GET /api/products/{product_id}/details
```

Он должен вернуть:

```text
product
category
photos
events
stock_movements если есть
computed fields
```

Computed fields:

```text
margin = sale_price - purchase_price
available_quantity = quantity - reserved_quantity
has_photos = true/false
```

## 9.3 История товара

Добавить:

```text
GET /api/products/{product_id}/events
POST /api/products/{product_id}/events
```

POST можно сделать простым:

```json
{
  "event_type": "manual_note",
  "comment": "Проверено перед продажей"
}
```

## 9.4 Изменение количества

Добавить:

```text
POST /api/products/{product_id}/stock-adjustment
```

Body:

```json
{
  "quantity_delta": 1,
  "reason": "manual_adjustment",
  "comment": "Корректировка после пересчета"
}
```

Должно:

```text
изменить quantity
записать stock_movements
записать product_events
записать audit_log
```

Если `stock_movements` не реализуется, всё равно записать `product_events`.

## 9.5 Подготовка к сайту

Добавить:

```text
PATCH /api/products/{product_id}/site-publication
```

Body:

```json
{
  "is_published_site": true,
  "site_title": "Ноутбук Lenovo ThinkPad T480",
  "site_description": "БУ ноутбук, проверен, готов к работе"
}
```

## 9.6 Подготовка к Авито

Добавить:

```text
PATCH /api/products/{product_id}/avito-publication
```

Body:

```json
{
  "is_published_avito": true,
  "avito_title": "Ноутбук Lenovo ThinkPad T480",
  "avito_description": "Рабочий ноутбук Lenovo ThinkPad T480..."
}
```

## 9.7 Справочники для UI

Добавить, если удобно:

```text
GET /api/products/meta
```

Возвращает:

```text
product_statuses with ru labels
repair_statuses with ru labels
brands existing
storage_locations existing
```

---

# 10. Admin Shell — русскоязычное усиление UI

Admin Shell должен остаться на русском.

Основной файл:

```text
admin-shell/app/templates/index.html
```

Возможный backend proxy:

```text
admin-shell/app/main.py
```

## 10.1 Раздел "Товары"

Улучшить список товаров:

```text
поиск по названию/SKU/бренду/модели/серийному номеру
фильтр по статусу
фильтр по категории
фильтр по бренду
фильтр по месту хранения
кнопка обновить
```

Таблица должна показывать:

```text
ID
Артикул
Название
Категория
Бренд
Модель
Статус
Количество
Доступно
Цена продажи
Маржа
Место хранения
Фото
Действия
```

## 10.2 Карточка товара

Добавить просмотр карточки товара прямо в Admin Shell.

Минимум:

```text
основные поля
цены
количество
статус
фото
история событий
движения остатков, если есть
подготовка к сайту
подготовка к Авито
```

Кнопка:

```text
Открыть карточку
```

## 10.3 Форма добавления товара

Расширить форму:

```text
артикул
название
категория
бренд
модель
серийный номер
состояние
описание
цена закупки
цена продажи
минимальная цена
рыночная цена
количество
место хранения
внутренние заметки
```

Все подписи на русском.

## 10.4 Изменение количества

Добавить UI-блок:

```text
Корректировка остатка
товар
изменение количества +/-
причина
комментарий
кнопка "Применить"
```

## 10.5 Подготовка к сайту/Авито

Добавить UI-блоки:

```text
Подготовка к сайту
- заголовок
- описание
- флаг опубликовано/готово

Подготовка к Авито
- заголовок
- описание
- флаг опубликовано/готово
```

Не делать реальную публикацию. Только подготовка и хранение данных в Core.

## 10.6 История товара

В карточке товара показывать:

```text
последние события
дата
тип события
комментарий
старое значение
новое значение
```

---

# 11. Фото

Сохранить существующую загрузку фото.

Улучшить UI, если быстро:

```text
показывать количество фото в списке товаров
в карточке товара показывать мини-список ссылок/превью
после загрузки фото обновлять карточку
```

Не делать сложный drag-and-drop, если это замедлит этап.

---

# 12. Seed-данные Stage 02

Расширить seed, чтобы были реалистичные товары для фильтров.

Категории:

```text
Ноутбуки
Принтеры
Мониторы
Комплектующие
Периферия
Системные блоки
Оргтехника
```

Товары:

```text
Ноутбук Lenovo ThinkPad T480
Ноутбук HP ProBook 450 G6
Принтер HP LaserJet 2055dn
Принтер Canon i-SENSYS LBP6030B
Монитор Dell P2419H
Монитор Samsung SyncMaster
SSD Kingston 480 ГБ
Оперативная память DDR4 8 ГБ
Клавиатура Logitech K120
Мышь A4Tech OP-620D
Системный блок Intel Core i5
МФУ Kyocera Ecosys
```

Разные статусы:

```text
in_stock
reserved
in_repair
for_parts
published_site
published_avito
```

Разные места хранения:

```text
Склад 1
Витрина
Сервисная зона
Полка запчастей
```

Seed должен быть idempotent.

---

# 13. Audit/Product Events

Каждое важное действие должно писать:

```text
audit_log
product_events
```

Минимум:

```text
создание товара
изменение статуса
изменение количества
изменение цены
подготовка к сайту
подготовка к Авито
загрузка фото
продажа
списание
```

---

# 14. Тесты

Добавить или обновить тесты:

```text
core/tests/test_products_search_filters.py
core/tests/test_product_details.py
core/tests/test_product_events.py
core/tests/test_stock_adjustment.py
core/tests/test_product_publication_flags.py
```

Если полное покрытие долго, минимум:

```text
test_products_search_filters.py
test_product_details.py
test_stock_adjustment.py
```

Проверить:

```text
поиск q работает
фильтр status работает
details возвращает product/photos/events
stock adjustment меняет quantity
product_events пишутся
site-publication сохраняется
avito-publication сохраняется
seed idempotent
```

---

# 15. Документация

Обновить:

```text
README.md
docs/api_contract.md
docs/database.md
docs/manual_test.md
docs/architecture.md если нужно
```

Создать:

```text
docs/stage02_inventory_product_module.md
```

В документации описать:

```text
что добавлено
новые поля товара
новые endpoints
как пользоваться в Admin Shell
как тестировать
что отложено
```

Manual test должен быть на русском.

---

# 16. Самопроверка

После реализации выполнить:

```powershell
Set-Location C:\tbootit

docker compose config
docker compose up --build -d
docker compose ps
```

Core smoke:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
```

Seed smoke:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod http://127.0.0.1:8000/api/products
Invoke-RestMethod "http://127.0.0.1:8000/api/products?q=Lenovo"
Invoke-RestMethod "http://127.0.0.1:8000/api/products?status=in_stock"
```

Product details smoke:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/products/1/details
Invoke-RestMethod http://127.0.0.1:8000/api/products/1/events
```

Stock adjustment smoke:

```powershell
$body = @{
  quantity_delta = 1
  reason = "manual_adjustment"
  comment = "Проверка Stage 02"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/products/1/stock-adjustment `
  -ContentType "application/json" `
  -Body $body
```

Tests:

```powershell
docker compose exec core pytest
```

Admin Shell manual smoke:

```text
http://127.0.0.1:8011
```

Проверить:

```text
интерфейс на русском
поиск товаров
фильтр статуса
фильтр категории/бренда, если реализован
открытие карточки товара
история товара
изменение количества
подготовка к сайту
подготовка к Авито
создание товара
смена статуса
```

---

# 17. Persistence check

Проверить, что данные сохраняются:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats

docker compose down
docker compose up -d

Start-Sleep -Seconds 5

Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
```

---

# 18. Отчет

Создать:

```text
reports/stage02_inventory_product_module_hardening_report.md
```

Структура:

```text
# Stage 02 Inventory & Product Module Hardening Report

## STATUS

PASS / PASS_WITH_NOTES / FAIL

## BRANCH

## COMMIT

## PROMPT DISCOVERY

PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:

## WHAT IMPLEMENTED

## DATABASE CHANGES

## API CHANGES

## ADMIN SHELL CHANGES

## RUSSIAN UI CHECK

## SEED DATA

## TESTS ADDED

## COMMANDS RUN

## SELF_CHECK_RESULTS

## PERSISTENCE_CHECK

## FILES_CHANGED

## KNOWN_LIMITATIONS

## OWNER_TESTING_GUIDE

## NEXT_RECOMMENDED_STAGE

Варианты:
- Stage 02A — independent audit
- Stage 03 — Repair Module Hardening
- Stage 04 — Sales Module Hardening
- Stage 05 — Public Site Module MVP
```

---

# 19. Git

После успешных проверок:

```powershell
git status
git add .
git commit -m "Harden inventory and product module"
git status
```

Не выполнять push без отдельной команды владельца.

---

# 20. Definition of Done

Stage 02 считается готовым, если:

```text
Core API запускается
Admin Shell запускается на http://127.0.0.1:8011
старые функции Stage 01 не сломаны
товары ищутся
товары фильтруются
карточка товара открывается
видна история товара
можно изменить количество
можно подготовить товар к сайту
можно подготовить товар к Авито
seed создает реалистичный набор товаров
UI остается на русском
pytest проходит
persistence проходит
документация обновлена
отчет создан
git commit создан
```

---

# 21. Стоп-условия

Остановиться и отчитаться, если:

```text
существующая БД не может быть безопасно обновлена
нужна полноценная миграционная система перед продолжением
Docker не запускается
pytest ломается и не удается исправить
Admin Shell требует полной переработки для Stage 02
есть конфликт незакоммиченных изменений
```

---

# 22. Главный принцип Stage 02

Stage 02 должен сделать товарный контур основой реального магазина.

Не нужно делать красиво.  
Нужно сделать удобно, полно и проверяемо для товара, остатков, статусов, фото, истории и подготовки к публикациям.
