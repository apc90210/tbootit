# PROMPT — Техноребут / Stage 02 v2 Avito-Style Product Cards & JSON Import

## Роль агента

Ты senior backend/fullstack developer, архитектор товарного каталога и интеграционный инженер проекта «Техноребут».

Ты работаешь в репозитории:

```powershell
C:\tbootit
```

Твоя задача — выполнить обновленный Stage 02: построить товарную карточку системы, отталкиваясь от состава карточки Авито, и добавить импорт карточек через JSON.

---

# 1. Контекст проекта

«Техноребут» — ИТ-система магазина и сервисного центра по ремонту и продаже компьютерной и оргтехники, преимущественно БУ-техники.

Главная архитектура:

```text
Core API + DB + Storage = единое ядро системы.
Все остальные модули работают только через HTTP API.
```

Core API владеет:

```text
БД
файлами
фото
товарными карточками
историей
audit log
импортом JSON
подготовкой к сайту/Авито
```

Admin Shell — русскоязычная внешняя тестовая оболочка.

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

---

# 3. Ключевое решение владельца

Stage 02 нужно строить не как обычную складскую карточку, а как карточку, близкую к составу карточки Авито.

Также принят будущий рабочий процесс:

```text
Карточки товара будут импортироваться через JSON.
JSON-карточки будет готовить ChatGPT.
Система должна уметь принять JSON, проверить его, создать/обновить товар и сохранить Avito-compatible payload.
```

Это значит:

```text
внутри системы должна быть нормализованная карточка товара
+
слой avito_card / marketplace_card / listing payload
+
импорт через JSON
```

---

# 4. Главное правило UI

Все пользовательские интерфейсы должны быть на русском языке.

Допустимо оставлять на английском только технические внутренние сущности:

```text
API endpoints
имена таблиц
имена полей
переменные
классы
docker service names
enum values в БД
pytest names
JSON keys
```

Но все, что видит пользователь в Admin Shell, должно быть на русском.

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

В отчете указать:

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

Не начинать реализацию, если есть непонятный dirty state.

---

# 7. Главный результат Stage 02 v2

После реализации должно быть возможно:

```text
1. Открыть Admin Shell.
2. Вставить JSON карточки товара.
3. Нажать "Импортировать карточку".
4. Core API валидирует JSON.
5. Система создает или обновляет товар.
6. Система сохраняет Avito-style карточку.
7. В карточке товара видны:
   - складские данные
   - описание для продажи
   - параметры/характеристики
   - цена
   - фото/ссылки на фото
   - местоположение
   - подготовка к сайту
   - подготовка к Авито
   - история импорта
8. Товар можно искать и фильтровать.
9. Старые функции Stage 01 не ломаются.
```

---

# 8. Концепция карточки

Карточка товара должна состоять из 3 слоев.

## 8.1 Внутренний слой товара

Это нормализованные поля для магазина:

```text
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
quantity
reserved_quantity
storage_location
notes
```

## 8.2 Avito-style слой объявления

Это поля, похожие на состав объявления:

```text
listing_title
listing_description
category_path
goods_type
condition
price
contact_name
phone
address
seller_type
parameters
photos
publication_status
```

Важно: на этом этапе не делать реальную публикацию в Авито API.  
Нужно только хранить и готовить данные.

## 8.3 JSON import layer

Это входной payload, который может подготовить ChatGPT.

Сохранять:

```text
source_json
source_type
import_status
validation_errors
imported_at
```

---

# 9. База данных

Сохранить существующую таблицу `products`.

Добавить новые поля к `products`, если их нет:

```text
quantity
reserved_quantity
min_price
market_price
notes
is_published_site
is_published_avito
site_title
site_description
avito_title
avito_description
avito_category_path
avito_goods_type
avito_condition
avito_params_json
avito_contact_name
avito_phone
avito_address
avito_seller_type
source_json
source_type
last_imported_at
```

Если добавлять много колонок рискованно, можно сделать отдельную таблицу.

Рекомендуемая отдельная таблица:

```text
product_cards
id
product_id
source_type
source_json
normalized_json
avito_json
validation_status
validation_errors
created_at
updated_at
```

Рекомендуемая таблица истории:

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

Рекомендуемая таблица движения остатков:

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

Если SQLite без миграций, реализовать безопасное добавление недостающих колонок или создать новые таблицы без удаления данных.

---

# 10. JSON Schema карточки

Создать документацию:

```text
docs/product_card_json_schema.md
```

Создать пример:

```text
docs/examples/product_card_lenovo_t480.json
```

Базовый формат JSON:

```json
{
  "source": "chatgpt",
  "schema_version": "1.0",
  "operation": "create_or_update",
  "product": {
    "sku": "NB-LENOVO-T480-001",
    "title": "Ноутбук Lenovo ThinkPad T480",
    "category_path": ["Компьютерная техника", "Ноутбуки"],
    "brand": "Lenovo",
    "model": "ThinkPad T480",
    "serial_number": "",
    "condition": "БУ, рабочий",
    "description": "Надежный офисный ноутбук Lenovo ThinkPad T480.",
    "purchase_price": 15000,
    "sale_price": 25000,
    "min_price": 23000,
    "market_price": 27000,
    "quantity": 1,
    "storage_location": "Склад 1",
    "notes": "Проверить батарею перед продажей."
  },
  "avito": {
    "title": "Ноутбук Lenovo ThinkPad T480, Core i5, 8 ГБ RAM, SSD",
    "description": "Продается проверенный ноутбук Lenovo ThinkPad T480. Подходит для офиса, учебы и работы.",
    "category_path": ["Электроника", "Ноутбуки"],
    "goods_type": "Ноутбук",
    "condition": "Б/у",
    "price": 25000,
    "seller_type": "company",
    "contact_name": "Техноребут",
    "phone": "",
    "address": "",
    "parameters": {
      "Производитель": "Lenovo",
      "Модель": "ThinkPad T480",
      "Процессор": "Intel Core i5",
      "Оперативная память": "8 ГБ",
      "Накопитель": "SSD 256 ГБ",
      "Диагональ": "14",
      "Состояние": "Б/у"
    },
    "photos": []
  },
  "site": {
    "title": "Ноутбук Lenovo ThinkPad T480",
    "description": "Проверенный БУ ноутбук для работы и учебы.",
    "publish_ready": true
  }
}
```

---

# 11. Core API — импорт JSON

Добавить endpoints:

```text
POST /api/product-cards/import-json
POST /api/product-cards/validate-json
GET  /api/product-cards/imports
GET  /api/product-cards/imports/{import_id}
```

## 11.1 Validate JSON

`POST /api/product-cards/validate-json`

Должен:

```text
проверить обязательные поля
проверить типы
проверить sku/title/price
проверить product и avito sections
вернуть список ошибок/предупреждений
ничего не сохранять
```

Response пример:

```json
{
  "valid": true,
  "errors": [],
  "warnings": ["Не указан телефон для Авито"]
}
```

## 11.2 Import JSON

`POST /api/product-cards/import-json`

Должен:

```text
валидировать JSON
создать или обновить category
создать или обновить product по sku
сохранить avito fields
сохранить site fields
сохранить source_json
записать product_events
записать audit_log
вернуть product_id и статус
```

Response пример:

```json
{
  "status": "imported",
  "operation": "created",
  "product_id": 10,
  "sku": "NB-LENOVO-T480-001",
  "warnings": []
}
```

Если `sku` уже есть:

```text
обновить существующий товар
operation = updated
```

Не плодить дубли.

---

# 12. Core API — карточка товара

Добавить/расширить:

```text
GET /api/products/{product_id}/details
GET /api/products/{product_id}/events
```

`details` должен вернуть:

```text
product
category
photos
product_card
avito
site
events
computed
```

Computed:

```text
margin
available_quantity
has_photos
avito_ready
site_ready
```

---

# 13. Core API — поиск и фильтры

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
model
storage_location
min_price
max_price
avito_ready
site_ready
limit
offset
```

Минимум:

```text
q
status
brand
storage_location
limit
offset
```

---

# 14. Admin Shell — JSON импорт

Admin Shell должен быть на русском.

Добавить раздел:

```text
Импорт JSON-карточки
```

Функции:

```text
textarea для JSON
кнопка "Проверить JSON"
кнопка "Импортировать JSON"
вывод ошибок валидации
вывод предупреждений
вывод product_id после импорта
кнопка "Открыть карточку товара"
```

Добавить подсказку:

```text
Вставьте JSON-карточку товара, подготовленную ChatGPT.
Система проверит структуру и создаст или обновит товар по артикулу/SKU.
```

---

# 15. Admin Shell — карточка товара

Добавить русскоязычную карточку:

```text
Основные данные
Склад и остатки
Цены
Описание
Характеристики Авито
Подготовка к сайту
Подготовка к Авито
Фото
История
```

Показывать Avito-style параметры:

```text
Категория Авито
Тип товара
Состояние
Цена
Контакт
Адрес
Параметры
Описание для Авито
```

---

# 16. Seed-данные Stage 02 v2

Расширить seed через тот же JSON-import путь, если возможно.

То есть seed может импортировать несколько JSON карточек.

Минимум 5 карточек:

```text
Ноутбук Lenovo ThinkPad T480
Принтер HP LaserJet 2055dn
Монитор Dell P2419H
SSD Kingston 480 ГБ
Клавиатура Logitech K120
```

Seed должен быть idempotent.

---

# 17. Фото

В JSON поле `photos` пока может содержать:

```text
локальные media URL
будущие внешние URL
пустой список
```

На Stage 02 не нужно скачивать внешние фото автоматически.

Сделать так:

```text
photos в JSON сохраняются как metadata/source list
загрузка реальных файлов остается через существующий upload
в карточке товара показывать сохраненный список ссылок/имён, если есть
```

---

# 18. Тесты

Добавить тесты:

```text
core/tests/test_product_card_json_validate.py
core/tests/test_product_card_json_import.py
core/tests/test_product_details_avito_card.py
core/tests/test_products_search_filters.py
```

Проверить:

```text
валидный JSON проходит validate
невалидный JSON возвращает errors
import создает product
повторный import по тому же sku обновляет, а не создает дубль
details содержит avito/site/product_card
поиск q работает
фильтр status работает
```

---

# 19. Документация

Создать/обновить:

```text
docs/stage02_avito_style_product_cards.md
docs/product_card_json_schema.md
docs/examples/product_card_lenovo_t480.json
docs/manual_test.md
docs/api_contract.md
docs/database.md
README.md
```

Документация должна быть понятна:

```text
как устроена карточка
как импортировать JSON
какой JSON готовить через ChatGPT
как проверить импорт
как открыть карточку
что пока не является реальной публикацией Авито
```

---

# 20. Самопроверка

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

Validate JSON smoke:

```powershell
$json = Get-Content .\docs\examples\product_card_lenovo_t480.json -Raw

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/product-cards/validate-json `
  -ContentType "application/json" `
  -Body $json
```

Import JSON smoke:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/product-cards/import-json `
  -ContentType "application/json" `
  -Body $json
```

Details smoke:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/products/1/details
```

Tests:

```powershell
docker compose exec core pytest
```

Admin Shell smoke:

```text
http://127.0.0.1:8011
```

Проверить вручную:

```text
раздел "Импорт JSON-карточки"
проверка JSON
импорт JSON
товар появился в списке
карточка товара открывается
Avito-style поля видны
UI на русском
```

---

# 21. Persistence check

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/api/admin/seed
Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats

docker compose down
docker compose up -d

Start-Sleep -Seconds 5

Invoke-RestMethod http://127.0.0.1:8000/api/admin/stats
```

Данные должны сохраниться.

---

# 22. Отчет

Создать:

```text
reports/stage02_avito_style_product_cards_json_import_report.md
```

Структура:

```text
# Stage 02 v2 Avito-Style Product Cards & JSON Import Report

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

## JSON IMPORT

## AVITO-STYLE CARD FIELDS

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
- Stage 02B — product card UX repair
- Stage 03 — Repair Module Hardening
- Stage 05 — Public Site Module MVP
```

---

# 23. Git

После успешных проверок:

```powershell
git status
git add .
git commit -m "Add Avito-style product cards and JSON import"
git status
```

Не выполнять push без отдельной команды владельца.

---

# 24. Definition of Done

Stage 02 v2 считается готовым, если:

```text
Core API запускается
Admin Shell запускается на http://127.0.0.1:8011
старые функции Stage 01 не сломаны
JSON validate endpoint работает
JSON import endpoint работает
валидная карточка импортируется
повторный импорт по SKU обновляет товар
карточка товара содержит Avito-style поля
details endpoint показывает product/card/avito/site/events
Admin Shell имеет раздел импорта JSON
Admin Shell показывает карточку товара на русском
seed создает реалистичные карточки
pytest проходит
persistence проходит
документация обновлена
отчет создан
git commit создан
```

---

# 25. Стоп-условия

Остановиться и отчитаться, если:

```text
существующая БД не может быть безопасно расширена
нужна полноценная миграционная система перед продолжением
Docker не запускается
pytest ломается и не удается исправить
Admin Shell требует полной переработки
есть конфликт незакоммиченных изменений
```

---

# 26. Главный принцип

Stage 02 v2 должен сделать товарную карточку пригодной для реального магазина и будущего Авито-модуля.

Но сейчас не делать реальную публикацию в Авито.

Нужно сделать:

```text
карточку
JSON-import
валидацию
хранение Avito-style данных
русский UI
проверяемость
```
