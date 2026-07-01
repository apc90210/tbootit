# 05 Database Baseline

## MVP БД

На первом этапе используется SQLite в Core-модуле.

Файл:

```text
/data/db/technoreboot.db
```

На хосте:

```text
./data/db/technoreboot.db
```

## Почему SQLite допустим для MVP

- быстрый старт;
- один Core-контейнер;
- простые бэкапы;
- меньше инфраструктуры;
- достаточно для прототипа.

## Будущий переход

После стабилизации модели данных можно перейти на PostgreSQL.

Важно: внешние модули не заметят перехода, потому что работают через API.

## Таблицы MVP

### categories

```text
id
name
slug
description
created_at
updated_at
```

### products

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

### product_photos

```text
id
product_id
filename
storage_path
media_url
sort_order
created_at
```

### customers

```text
id
name
phone
email
comment
created_at
updated_at
```

### repair_orders

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

### sales

```text
id
customer_id
total_amount
payment_method
comment
created_at
```

### sale_items

```text
id
sale_id
product_id
title
price
quantity
created_at
```

### audit_log

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

## Статусы товаров

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

## Статусы ремонтов

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
