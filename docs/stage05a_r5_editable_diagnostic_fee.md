# Stage05A-R5 Editable Diagnostic Fee Across Repair Documents

## Overview

Stage05A-R5 implements editable diagnostic fee support across the entire TechnoReboot ecosystem. The diagnostic fee is stored as a snapshot field on each `RepairOrder`, defaulted to 500 rubles, and can be customized at intake or during edit of active repairs. All UI forms, repair detail views, and printable documents (work order, detachable ticket, detailed back-side clauses) dynamically display the repair-specific diagnostic fee.

## Core API & Model Changes

- Added `diagnostic_fee` column to `repair_orders` table (Float, NOT NULL, default=500.0).
- Additive database migration automatically backfills existing repair orders with 500.0.
- `RepairOrderCreate` accepts `diagnostic_fee` (optional, defaults to 500.0, minimum 0.0).
- `RepairOrderUpdate` allows updating `diagnostic_fee` (minimum 0.0) for active repairs (blocks terminal `issued`/`canceled` repairs with HTTP 409 Conflict).
- `GET /api/repairs/options` returns `"default_diagnostic_fee": 500`.
- Audit logs capture `repair.created` and `repair.updated` with diagnostic fee metadata.

## Repairs Module & UI Changes

- `GET /repairs/new` form renders "Стоимость диагностики, ₽" with value default 500 (from Core options API).
- Custom values (e.g. 750, 800) and zero (0) are saved and retained without resetting to 500.
- Negative values block submit with Russian validation message "Стоимость диагностики не может быть отрицательной".
- Edit form (`/repairs/{id}/edit`) renders saved diagnostic fee and blocks terminal repairs.
- Repair detail (`/repairs/{id}`) displays "Стоимость диагностики: N ₽".
- Printable work order (`/repairs/{id}/print`) renders dynamic diagnostic fee in main terms, detachable ticket, and back-side terms without literal "500 рублей" hardcode for custom fee repairs.

## Verification

- Core safe tests: 147 passed
- Inventory-Sales module tests: 110 passed
- Avito module tests: 12 passed
- Repairs module tests: 15 passed
- Live DB preservation: Verified 100% (products: 56, sales: 43, customers: 13, repairs: 26).
