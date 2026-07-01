# 04 Core MVP Scope

## Назначение Core MVP

Core MVP — первый большой рабочий модуль системы. Он нужен, чтобы доказать, что архитектура жизнеспособна и основные бизнес-сценарии работают.

## Входит в MVP

### Core API

- health;
- version;
- products;
- categories;
- customers;
- repairs;
- sales;
- photos;
- admin endpoints;
- audit log.

### БД

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

### Storage

```text
product_photos
repair_photos
exports
backups
```

### Admin/Test Shell

- dashboard;
- товары;
- клиенты;
- ремонты;
- продажи;
- структура БД;
- администрирование.

## Не входит в MVP

- роли;
- сложная авторизация;
- касса;
- онлайн-оплата;
- полноценный сайт;
- полноценный Авито API;
- 1С;
- сложные отчеты.

## MVP Definition of Done

```text
Core запускается
Shell запускается
товары создаются
фото загружаются
клиенты создаются
ремонты создаются
продажи создаются
структура БД видна
audit log пишется
данные сохраняются
есть документация
есть отчет
```
