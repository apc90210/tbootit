# PROMPT — Техноребут / Stage 01 Core MVP Big Module

## Роль агента

Ты senior backend/fullstack developer, архитектор и технический исполнитель проекта «Техноребут».

Ты работаешь в репозитории:

```powershell
C:\tbootit
```

Твоя задача — создать первый полностью рабочий прототип ядра системы «Техноребут» и простую внешнюю оболочку для работы с ним и тестирования.

---

# 1. Контекст проекта

«Техноребут» — магазин и сервисный центр по ремонту и продаже компьютерной и оргтехники, преимущественно БУ-техники.

Система строится модульно.

Главная архитектурная фиксация:

```text
Core API + DB + Storage = единое ядро системы.
Все остальные модули работают только через HTTP API.
```

Core API является владельцем данных.  
База данных и фото находятся внутри Core-модуля.  
Внешние модули не имеют прямого доступа к БД и файлам.  
Все будущие модули — сайт, Авито, ремонты, продажи, Telegram, аналитика — должны работать через API.

---

# 2. Обязательное правило поиска prompt-файлов

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

Выполни PowerShell:

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

Если актуальный prompt найден в:

```text
C:\Users\Apc\Downloads
```

скопируй его в:

```text
C:\tbootit\.agents\received_prompts\
```

Команда:

```powershell
New-Item -ItemType Directory -Force -Path "C:\tbootit\.agents\received_prompts"
Copy-Item "<FULL_PROMPT_PATH_FROM_DOWNLOADS>" "C:\tbootit\.agents\received_prompts\" -Force
```

В итоговом отчете обязательно указать:

```text
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
```

Если найдено несколько похожих prompt-файлов и невозможно надежно определить актуальный — не начинать реализацию, показать список и запросить выбор пользователя.

---

# 3. Главная задача Stage 01

Создать полностью рабочий MVP-прототип ядра:

```text
Core API
встроенная БД
файловое хранилище
административные endpoints
простая внешняя оболочка Admin/Test Shell
Docker Compose запуск
документация
самопроверки
итоговый отчет
git commit
```

---

# 4. Технологический стек MVP

Использовать простой и надежный стек:

```text
Python
FastAPI
SQLAlchemy
SQLite
Jinja2 или простой HTML/JS
Docker
Docker Compose
pytest
```

Допустимо сделать Admin/Test Shell максимально простой: HTML, формы, таблицы, немного CSS/JS.

Не использовать тяжелый frontend-фреймворк без необходимости.

---

# 5. Контейнерная архитектура MVP

На первом этапе должно быть два сервиса:

```text
core
admin-shell
```

## core

Внутри Core-модуля:

```text
FastAPI
SQLite DB
file storage
business logic
admin endpoints
media endpoints
```

## admin-shell

Внешняя простая оболочка:

```text
работает через HTTP API
не подключается к БД напрямую
не импортирует модели Core
может быть заменена будущими внешними модулями
```

Порты:

```text
Core API:    http://127.0.0.1:8000
API Docs:    http://127.0.0.1:8000/docs
Admin Shell: http://127.0.0.1:8010
```

---

# 6. Ожидаемая структура проекта

Создать структуру:

```text
C:\tbootit
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
│
├── core
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── storage.py
│   │   ├── services
│   │   │   └── __init__.py
│   │   └── routers
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── products.py
│   │       ├── categories.py
│   │       ├── customers.py
│   │       ├── repairs.py
│   │       ├── sales.py
│   │       ├── photos.py
│   │       └── admin.py
│   └── tests
│       ├── test_health.py
│       ├── test_products.py
│       └── test_admin_schema.py
│
├── admin-shell
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app
│       ├── main.py
│       └── templates
│           └── index.html
│
├── data
│   ├── db
│   ├── storage
│   └── backups
│
├── docs
│   ├── architecture.md
│   ├── api_contract.md
│   ├── database.md
│   ├── storage.md
│   └── manual_test.md
│
└── reports
    └── core_mvp_implementation_report.md
```

Если часть структуры уже есть — не удалять без необходимости, а аккуратно дополнить.

---

# 7. Docker Compose

Создать `docker-compose.yml`.

Минимально:

```yaml
services:
  core:
    build: ./core
    container_name: technoreboot-core
    ports:
      - "8000:8000"
    volumes:
      - ./data/db:/data/db
      - ./data/storage:/data/storage
      - ./data/backups:/data/backups
    environment:
      - APP_ENV=dev
      - DATABASE_URL=sqlite:////data/db/technoreboot.db
      - STORAGE_ROOT=/data/storage
      - BACKUP_ROOT=/data/backups
      - API_TOKEN=dev-token

  admin-shell:
    build: ./admin-shell
    container_name: technoreboot-admin-shell
    ports:
      - "8010:8010"
    environment:
      - CORE_API_URL=http://core:8000
      - CORE_API_TOKEN=dev-token
    depends_on:
      - core
```

---

# 8. База данных MVP

Использовать SQLite.

Файл БД:

```text
/data/db/technoreboot.db
```

На хосте:

```text
C:\tbootit\data\db\technoreboot.db
```

Создание таблиц можно сделать автоматически при старте приложения через SQLAlchemy `Base.metadata.create_all`.

Alembic можно отложить на следующий этап.

---

# 9. Таблицы MVP

Реализовать минимум:

```text
categories
products
product_photos
customers
repair_orders
sales
sale_items
audit_log
```

## categories

```text
id
name
slug
description
created_at
updated_at
```

## products

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

Статусы товара:

```text
draft
in_stock
reserved
sold
in_repair
for_parts
written_off
published_site
published_avito
```

## product_photos

```text
id
product_id
filename
storage_path
media_url
sort_order
created_at
```

## customers

```text
id
name
phone
email
comment
created_at
updated_at
```

## repair_orders

```text
id
customer_id
device_title
device_serial
problem_description
diagnostics_result
work_description
parts_description
price
status
created_at
updated_at
closed_at
```

Статусы ремонта:

```text
new
accepted
diagnostics
waiting_parts
in_progress
ready
issued
cancelled
```

## sales

```text
id
customer_id
total_amount
payment_method
comment
created_at
```

## sale_items

```text
id
sale_id
product_id
title
price
quantity
created_at
```

## audit_log

```text
id
entity_type
entity_id
action
old_value
new_value
comment
created_at
```

---

# 10. Core API endpoints

## System

```text
GET /health
GET /api/version
```

## Products

```text
GET    /api/products
POST   /api/products
GET    /api/products/{product_id}
PATCH  /api/products/{product_id}
PATCH  /api/products/{product_id}/status
DELETE /api/products/{product_id}
```

При удалении для MVP лучше делать мягкое удаление через статус `written_off`, если это проще и безопаснее.

## Categories

```text
GET  /api/categories
POST /api/categories
```

## Customers

```text
GET  /api/customers
POST /api/customers
GET  /api/customers/{customer_id}
PATCH /api/customers/{customer_id}
```

## Repairs

```text
GET   /api/repairs
POST  /api/repairs
GET   /api/repairs/{repair_id}
PATCH /api/repairs/{repair_id}
PATCH /api/repairs/{repair_id}/status
```

## Sales

```text
GET  /api/sales
POST /api/sales
GET  /api/sales/{sale_id}
```

При продаже товара:

1. Создать запись `sales`.
2. Создать `sale_items`.
3. Перевести товар в `sold`.
4. Записать событие в `audit_log`.

## Photos

```text
POST   /api/products/{product_id}/photos
GET    /api/products/{product_id}/photos
GET    /media/products/{product_id}/{filename}
DELETE /api/products/{product_id}/photos/{photo_id}
```

Фото хранить:

```text
/data/storage/product_photos/{product_id}/
```

## Admin

```text
GET  /api/admin/db/schema
GET  /api/admin/db/tables
GET  /api/admin/stats
GET  /api/admin/audit-log
POST /api/admin/seed
POST /api/admin/backup
POST /api/admin/dev-reset
```

`dev-reset` обязательно пометить как dev-only.

---

# 11. Admin/Test Shell

Создать простую оболочку на:

```text
http://127.0.0.1:8010
```

Она должна работать только через Core API.

## Разделы оболочки

### Dashboard

Показать:

```text
Core health
количество товаров
количество клиентов
количество ремонтов
количество продаж
```

### Products

Функции:

```text
список товаров
добавление товара
просмотр товара
изменение статуса
загрузка фото
просмотр фото
```

### Customers

Функции:

```text
список клиентов
добавление клиента
редактирование клиента, если успеваешь
```

### Repairs

Функции:

```text
список ремонтов
создание ремонта
изменение статуса ремонта
```

### Sales

Функции:

```text
список продаж
продажа товара
автоматический перевод товара в sold
```

### DB Structure

Функции:

```text
список таблиц
поля таблиц
количество записей
```

### Admin

Функции:

```text
seed data
backup
audit log
dev reset
```

---

# 12. Требования к audit log

Записывать минимум:

```text
создание товара
изменение товара
изменение статуса товара
загрузка фото
создание клиента
создание ремонта
изменение статуса ремонта
создание продажи
seed
backup
dev reset
```

Для MVP можно писать JSON-строку в `old_value` / `new_value`.

---

# 13. Документация

Создать и заполнить:

```text
README.md
docs/architecture.md
docs/api_contract.md
docs/database.md
docs/storage.md
docs/manual_test.md
```

## README.md должен содержать

```text
что это
как запустить
адреса сервисов
как проверить
как остановить
где лежит БД
где лежат фото
известные ограничения MVP
```

## manual_test.md должен содержать

Сценарии ручной проверки:

```text
добавить товар
загрузить фото
изменить статус
создать клиента
создать ремонт
провести продажу
посмотреть структуру БД
посмотреть audit log
перезапустить Docker и проверить сохранение
```

---

# 14. Тесты

Создать минимум:

```text
core/tests/test_health.py
core/tests/test_products.py
core/tests/test_admin_schema.py
```

Желательно:

```text
core/tests/test_customers.py
core/tests/test_repairs.py
core/tests/test_sales.py
core/tests/test_photos.py
```

Если полноценные тесты мешают быстро получить рабочий MVP, минимум должен быть smoke-level.

---

# 15. Самопроверка после реализации

Выполнить:

```powershell
Set-Location C:\tbootit

docker compose config
docker compose up --build
```

Проверить:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/version
http://127.0.0.1:8000/docs
http://127.0.0.1:8010
```

PowerShell smoke:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/version
Invoke-RestMethod http://127.0.0.1:8000/api/admin/db/schema
Invoke-RestMethod http://127.0.0.1:8000/api/products
```

Если pytest доступен:

```powershell
docker compose exec core pytest
```

или локально:

```powershell
pytest
```

---

# 16. Проверка сохранения данных

После создания тестовых данных:

```powershell
docker compose down
docker compose up
```

Проверить, что данные остались.

---

# 17. Итоговый отчет

Создать файл:

```text
reports/core_mvp_implementation_report.md
```

В отчете обязательно указать:

```text
STATUS:
BRANCH:
COMMIT:
PROMPT_SEARCH_DONE:
PROMPT_USED:
PROMPT_SOURCE:
PROMPT_LOCAL_COPY:
WHAT_CREATED:
PROJECT_STRUCTURE:
ENDPOINTS:
HOW_TO_RUN:
HOW_TO_TEST:
SELF_CHECK_RESULTS:
KNOWN_LIMITATIONS:
OWNER_TESTING_READY:
NEXT_MODULE_RECOMMENDATION:
```

---

# 18. Git

После успешной реализации и самопроверок:

```powershell
git status
git add .
git commit -m "Implement Technoreboot Core MVP prototype"
git status
```

Не выполнять push без отдельной команды пользователя.

---

# 19. Definition of Done

Stage 01 считается готовым, если:

```text
docker compose up --build запускается
Core API отвечает
API Docs открывается
Admin Shell открывается
товар можно добавить
товар можно посмотреть
статус товара можно изменить
фото можно загрузить и открыть
клиент создается
ремонт создается
статус ремонта меняется
продажа создается
товар после продажи становится sold
структура БД видна
audit log пишется
данные сохраняются после перезапуска
документация создана
отчет создан
git commit создан
```

---

# 20. Стоп-условия

Остановись и отчитайся, если:

```text
Docker не запускается после нескольких попыток исправления
порты 8000 или 8010 заняты и невозможно безопасно выбрать другие
найдены важные существующие файлы, которые конфликтуют с задачей
невозможно определить актуальный prompt
возникла ошибка, требующая решения владельца
```

Не удаляй существующие данные без явной необходимости.

---

# 21. Приоритет результата

Главный приоритет — рабочее ядро MVP.

Лучше простой, но полностью работающий прототип, чем сложная архитектура без запуска.

Сначала сделать:

```text
работающий Docker
работающий Core API
работающую БД
работающий Admin Shell
основные CRUD-сценарии
отчет
```

После этого будут отдельные внешние модули.
