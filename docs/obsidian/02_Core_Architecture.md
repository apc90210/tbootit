# 02 Core Architecture

## Главный принцип

Core API является основой системы.

```text
Core API + Database + Storage = ядро.
```

Все остальные модули являются клиентами ядра.

## Почему так

Эта архитектура позволяет:

- менять БД без переписывания внешних модулей;
- централизовать бизнес-логику;
- централизовать фото;
- контролировать статусы товаров;
- вести audit log;
- подключать новые модули постепенно;
- запускать внешние модули где угодно.

## Компоненты ядра

```text
Core API
Database
File Storage
Business Services
Admin API
Public API
Audit Log
Backup/Export Tools
```

## Внешние модули

```text
Admin/Test Shell
Public Site
Repair UI
Sales UI
Avito Module
Telegram Bot
Analytics Module
```

## Правило доступа

Внешний модуль не должен знать:

- структуру таблиц;
- путь к SQLite/PostgreSQL;
- внутренние storage paths;
- внутренние ORM-модели.

Внешний модуль знает только:

```text
CORE_API_URL
CORE_API_TOKEN
HTTP API contract
```

## MVP-контейнеризация

На первом этапе:

```text
core container:
  FastAPI
  SQLite
  file storage
  admin endpoints

admin-shell container:
  simple external UI
  HTTP requests to core
```

## Будущая эволюция

MVP:

```text
SQLite + local storage
```

Позже:

```text
PostgreSQL
backup scheduler
auth service
object storage or S3-compatible storage
reverse proxy
HTTPS
```
