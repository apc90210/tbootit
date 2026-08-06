# Stage 05B-R3 Primary Repair Status Filter Documentation

## Overview

Stage 05B-R3 implements the primary repair status filter ("Статус ремонта") on the main repairs registry page (`http://localhost:8040/repairs`) and verifies seamless exact-match filtering in Core API (`GET /api/repairs`).

## Key Changes

### 1. Core API (`core/app/routers/repairs.py` & `core/app/schemas.py`)
- Standardized status contract in `schemas.REPAIR_STATUSES`:
  - `received` -> Принят
  - `diagnostics` -> Диагностика
  - `waiting_customer` -> Ожидает клиента
  - `waiting_parts` -> Ожидает запчасти
  - `in_repair` -> В ремонте
  - `ready` -> Готов
  - `unrepairable` -> Ремонт невозможен
  - `issued` -> Выдан
  - `canceled` -> Отменён
- Endpoint `GET /api/repairs` filters repair orders using exact equality `models.RepairOrder.status == status.strip()`. Substring matching is strictly excluded.
- Unknown status parameter values return HTTP 200 OK with `total: 0` and `items: []` without triggering an HTTP 500 error.

### 2. Repairs Module (`repairs-module/app/routers/repairs.py` & `repairs-module/app/templates/repairs_list.html`)
- `list_repairs` router passes all search, status, priority, device type, assignment, date range, pagination, and sorting parameters to Core API and renders them in Jinja context.
- Added visible dropdown `<select name="status" id="status" onchange="this.form.submit()">` as the FIRST main filter in the repairs registry search form.
- First option is "Все статусы" (`value=""`), followed by all active status options dynamically retrieved from Core API.
- Selected status value persists across page refreshes (`selected` attribute).
- Hidden inputs preserve other active filter parameters when submitting the form.
- Pagination links preserve `status` and all other query parameters.
- Form submission automatically resets `page=1`.
- When filtering yields 0 records, renders clear message `"Ремонты с выбранным статусом не найдены."` and a `"Сбросить фильтры"` button leading to `/repairs`.

## Verification & Isolation

- **Core Safe Unit Tests**: 159 passed.
- **Inventory Sales Module Tests**: 110 passed.
- **Avito Module Tests**: 12 passed.
- **Repairs Module Tests**: 32 passed.
- **Total Tests Passed**: 313.
- **Live DB Isolation**: Production database `data/db/technoreboot.db` SHA256 (`6b71e3806379bd62fed4b22dd2cc362d6db3f1a21e2da707225c8b1f1c8fef36`) and record counts (repair_orders: 46, products: 56, sales: 43) remained 100% untouched.
- **Safety Scans**: All 3 safety scans passed clean with zero violations.
