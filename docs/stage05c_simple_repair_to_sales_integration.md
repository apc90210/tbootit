# Stage 05C Simple Repair-to-Sales Integration Documentation

## Overview

Stage 05C establishes automatic accounting integration between completed repair orders (`ready` status) and the general sales system (`Sale`).

When a repair order transitions to `ready` ("Готов"), a linked `Sale` record is automatically created or updated in Core API with `source_type="repair"` and `source_id=repair.id`, setting `total_amount = repair.estimated_repair_amount`.

## Architectural Design

### 1. Data Ownership & Transaction Atomicity (Core API)
- Core API controls `RepairOrder`, `Sale`, `SaleItem`, status transitions, and audit logging.
- Transitioning a repair order to `ready` via `POST /api/repairs/{id}/status` executes status change, `estimated_repair_amount` saving, `RepairStatusHistory` record creation, `AuditLog` entry, and linked `Sale` creation/update in **one atomic database transaction**.
- If sale creation fails, the transaction rolls back completely.

### 2. Idempotency & Uniqueness
- Each `RepairOrder` has at most one linked `Sale` of type `repair`.
- Enforced via unique constraint `(source_type, source_id)` on `sales` table.
- Subsequent transitions to `ready` update the existing `Sale` amount and description without creating duplicates.
- Transitioning a repair with a linked sale to `canceled` automatically sets the linked `Sale` status to `canceled` (excluding it from completed sales revenue).

### 3. Sales Module Presentation (`inventory-sales-module`)
- Repair sales appear in the general sales registry (`/sales`) marked with a `"Ремонт"` badge.
- Displays repair description (`comment`) and a direct link to repair details: `http://localhost:8040/repairs/{repair_id}`.
- Included in overall sales reports (today, week, month, year, arbitrary range).

### 4. 100% Stock & Product Isolation
- Does NOT create dummy `Product` records.
- Does NOT deduct product stock (`quantity`).
- Does NOT generate `StockMovement` records.

## Verification & Isolation Results

- **Core Safe Unit Tests**: 163 passed.
- **Inventory Sales Module Tests**: 112 passed.
- **Avito Module Tests**: 12 passed.
- **Repairs Module Tests**: 34 passed.
- **Total Unit Tests Passed**: 321.
- **Empirical Live Runtime Checks**: Scenarios A (2800 RUB repair sale), B (0 RUB free repair sale), C (Idempotent update to 3200 RUB), and D (Stock isolation) all passed successfully.
- **Safety Scans**: All 3 safety scans clean with zero violations.
