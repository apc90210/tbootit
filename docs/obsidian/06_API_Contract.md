# 06 API Contract

## Base URL

Локально:

```text
http://127.0.0.1:8000
```

В Docker-сети:

```text
http://core:8000
```

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

## Photos

```text
POST   /api/products/{product_id}/photos
GET    /api/products/{product_id}/photos
GET    /media/products/{product_id}/{filename}
DELETE /api/products/{product_id}/photos/{photo_id}
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

## Правила для внешних модулей

Внешние модули:

- используют только HTTP;
- не импортируют код Core;
- не подключаются к БД;
- не читают файлы напрямую;
- получают фото через media URL.

## Ошибки

API должен возвращать понятные ошибки:

```json
{
  "detail": "Product not found"
}
```

## Версионирование

Для MVP можно использовать:

```text
/api/...
```

Позже возможно:

```text
/api/v1/...
```
