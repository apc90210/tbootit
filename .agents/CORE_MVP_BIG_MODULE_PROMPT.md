# PROMPT — Stage 01 Core MVP Big Module

## Роль

Ты senior backend/fullstack developer и архитектор проекта «Техноребут».

Твоя задача — в репозитории `C:\tbootit` создать полностью рабочий прототип ядра системы и простую внешнюю оболочку для тестирования.

## Контекст проекта

«Техноребут» — магазин и сервисный центр по ремонту и продаже компьютерной и оргтехники, преимущественно БУ-техники.

Архитектурное решение:

```text
Core API + DB + Storage = единое ядро.
Все остальные модули работают только через HTTP API.
```

Core API является владельцем данных. База данных и фото находятся внутри Core-модуля. Внешняя оболочка работает через API и может быть заменена будущими модулями.

## Рабочая директория

```powershell
C:\tbootit
```

## Главная задача

Создать рабочий MVP-прототип:

```text
Core API
встроенная БД
файловое хранилище
административные endpoints
простая внешняя оболочка Admin/Test Shell
Docker Compose запуск
документация
самопроверки
отчет
```

## Технологический стек MVP

Предпочтительно:

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

Допустимо использовать простой HTML/JS без React/Vue, чтобы быстрее получить рабочий прототип.

## Важное требование к контейнерам

На MVP:

- Core API, БД и storage должны быть в одном Core-модуле.
- SQLite-файл должен храниться в volume `./data/db`.
- Фото и файлы должны храниться в volume `./data/storage`.
- Admin/Test Shell должен быть внешней оболочкой и работать через HTTP API.

Можно сделать shell отдельным контейнером или простой статикой, но он не должен работать напрямую с БД.

## Ожидаемая структура проекта

```text
C:\tbootit
│
├── docker-compose.yml
├── .env.example
├── README.md
│
├── core
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── services
│   │   ├── routers
│   │   │   ├── health.py
│   │   │   ├── products.py
│   │   │   ├── categories.py
│   │   │   ├── customers.py
│   │   │   ├── repairs.py
│   │   │   ├── sales.py
│   │   │   ├── photos.py
│   │   │   └── admin.py
│   │   └── storage.py
│   └── tests
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

## Docker Compose

Должны быть сервисы:

```text
core
admin-shell
```

Порты:

```text
Core API:    8000
Admin Shell: 8010
```

Данные:

```text
./data/db:/data/db
./data/storage:/data/storage
./data/backups:/data/backups
```

## Core API endpoints

### System

```text
GET /health
GET /api/version
```

### Products

```text
GET    /api/products
POST   /api/products
GET    /api/products/{product_id}
PATCH  /api/products/{product_id}
PATCH  /api/products/{product_id}/status
DELETE /api/products/{product_id}
```

Product поля минимум:

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

Статусы:

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

### Categories

```text
GET  /api/categories
POST /api/categories
```

### Customers

```text
GET  /api/customers
POST /api/customers
GET  /api/customers/{customer_id}
```

Customer поля:

```text
id
name
phone
email
comment
created_at
updated_at
```

### Repairs

```text
GET   /api/repairs
POST  /api/repairs
GET   /api/repairs/{repair_id}
PATCH /api/repairs/{repair_id}
PATCH /api/repairs/{repair_id}/status
```

Repair поля:

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

Статусы:

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

### Sales

```text
GET  /api/sales
POST /api/sales
GET  /api/sales/{sale_id}
```

При продаже товара:

- создать запись sales;
- создать sale item;
- перевести товар в `sold`;
- записать audit log.

### Photos

```text
POST   /api/products/{product_id}/photos
GET    /api/products/{product_id}/photos
GET    /media/products/{product_id}/{filename}
DELETE /api/products/{product_id}/photos/{photo_id}
```

Фото хранятся в:

```text
/data/storage/product_photos/{product_id}/
```

### Admin

```text
GET  /api/admin/db/schema
GET  /api/admin/db/tables
GET  /api/admin/stats
GET  /api/admin/audit-log
POST /api/admin/seed
POST /api/admin/backup
POST /api/admin/dev-reset
```

`dev-reset` четко пометить как dev-only.

## База данных

Минимальные таблицы:

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

Создание таблиц может выполняться автоматически при старте MVP. Миграции Alembic можно отложить, но архитектурно не запрещать.

## Admin/Test Shell

Создай простую оболочку на `http://127.0.0.1:8010`.

Функции:

1. Dashboard:
   - health Core;
   - количество товаров;
   - количество клиентов;
   - количество ремонтов;
   - количество продаж.

2. Products:
   - список товаров;
   - форма добавления товара;
   - просмотр карточки;
   - изменение статуса;
   - загрузка фото;
   - просмотр фото.

3. Customers:
   - список клиентов;
   - форма добавления клиента.

4. Repairs:
   - список ремонтов;
   - форма создания ремонта;
   - изменение статуса.

5. Sales:
   - список продаж;
   - форма продажи товара.

6. DB Structure:
   - список таблиц;
   - поля таблиц;
   - количество записей.

7. Admin:
   - seed data;
   - backup;
   - audit log;
   - dev reset, если реализован.

Интерфейс может быть максимально простой, но должен быть рабочим.

## Требования к API для Shell

Admin Shell не должен импортировать модели Core и не должен подключаться к БД напрямую. Только HTTP-запросы к Core API.

## Документация

Создай:

```text
docs/architecture.md
docs/api_contract.md
docs/database.md
docs/storage.md
docs/manual_test.md
README.md
```

## Тесты

Минимум pytest для Core:

```text
test_health.py
test_products.py
test_admin_schema.py
```

Если времени достаточно, добавь:

```text
test_customers.py
test_repairs.py
test_sales.py
test_photos.py
```

## Самопроверка

После реализации выполни:

```powershell
docker compose config
docker compose up --build
```

Проверь:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
http://127.0.0.1:8010
```

API smoke:

```powershell
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/version
curl http://127.0.0.1:8000/api/admin/db/schema
curl http://127.0.0.1:8000/api/products
```

Если PowerShell curl конфликтует, используй:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Итоговый отчет

Создай:

```text
reports/core_mvp_implementation_report.md
```

В отчете укажи:

```text
STATUS
BRANCH
COMMIT
WHAT_CREATED
PROJECT_STRUCTURE
ENDPOINTS
HOW_TO_RUN
HOW_TO_TEST
SELF_CHECK_RESULTS
KNOWN_LIMITATIONS
NEXT_MODULE_RECOMMENDATION
```

## Git

После успешных проверок:

```powershell
git status
git add .
git commit -m "Implement Technoreboot Core MVP prototype"
```

Не выполняй push без отдельной команды пользователя.

## Definition of Done

Модуль считается готовым, если:

```text
docker compose up --build запускается
Core API отвечает
Admin Shell открывается
товар можно добавить через shell или API
товар можно посмотреть
фото можно загрузить и открыть
структура БД видна через shell/API
клиент создается
ремонт создается
продажа создается
audit log пишется
данные сохраняются после перезапуска
создан отчет
создана документация
есть git commit
```

## Стоп-условия

Остановись и отчитайся, если:

- Docker не запускается после нескольких попыток исправления;
- заняты порты и невозможно продолжить без решения пользователя;
- обнаружена несовместимость окружения;
- проект уже содержит важный код, который конфликтует с задачей.

Не удаляй существующие данные без явной необходимости.
