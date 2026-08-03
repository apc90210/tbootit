# Stage05A-R6 Diagnostic Fee Money Contract and Runtime Acceptance

## Overview

Stage05A-R6 hardens the monetary contract for repair diagnostic fees across the TechnoReboot platform. Float representation and arbitrary template fallbacks (`else 500`, `| int`) have been eliminated in favor of a strict Integer Money Contract (whole integer rubles, `step="1"`, `min="0"`). All runtime scenarios (default 500, custom 800, edit 800 -> 650, zero 0, and decimal 500.5 rejection) have been empirically verified against live Core and Repairs API/UI services with 100% test isolation.

## Integer Money Contract Specification

- **Database Column**: `repair_orders.diagnostic_fee` (`INTEGER DEFAULT 500 NOT NULL`).
- **Python / Pydantic Types**: `int` (Pydantic V2 strictly validates integers and rejects floats with fractional parts like `500.5` with HTTP 422 Unprocessable Entity).
- **Core Options API**: `GET /api/repairs/options` returns `"default_diagnostic_fee": 500`.
- **HTML Inputs**: `<input type="number" step="1" min="0" ...>`.
- **Print & Detail Templates**: `{{ repair.diagnostic_fee }}` (or `{{ repair.get('diagnostic_fee') }}`) without `| int` or `else 500` fallbacks.
- **Missing Fee Guard**: `GET /repairs/{repair_id}/print` returns HTTP 400 error if `diagnostic_fee` is missing from database records.

## Empirical Runtime Verification

- **Scenario A (Default 500)**: Repair `R-20260803-0034` created without fee -> API returns `500` (int), card displays `500 ₽`, print work order, ticket, and Page 2 terms render `500 рублей`.
- **Scenario B (Custom 800)**: Repair `R-20260803-0035` created with fee `800` -> API returns `800` (int), card displays `800 ₽`, print work order, ticket, and Page 2 terms render `800 рублей`. Stale `500 рублей` agreement text absent.
- **Scenario C (Edit 800 -> 650)**: Repair `R-20260803-0035` updated to `650` -> API returns `650` (int), card displays `650 ₽`, print work order, ticket, and Page 2 terms render `650 рублей`. Stale `800 рублей` agreement text absent. Repair A remains `500`. Audit log `repair.updated` recorded.
- **Scenario D (Zero 0)**: Repair `R-20260803-0036` created with fee `0` -> API returns `0` (int), card displays `0 ₽`, print work order, ticket, and Page 2 terms render `0 рублей`. No 500 fallback.
- **Scenario E (Decimal 500.5 Rejection)**: `POST /api/repairs/` with `diagnostic_fee: 500.5` -> Core API returns HTTP 422 Unprocessable Entity. Request is strictly rejected without rounding or saving.

## Test Isolation Proof

- Live DB SHA256 before unit tests: `8bef396fc9ce239ce6003a0c429b7a4ab623d4aa6ee0cc8b9ad23952b1daf1a4`
- Live DB SHA256 after unit tests: `8bef396fc9ce239ce6003a0c429b7a4ab623d4aa6ee0cc8b9ad23952b1daf1a4`
- Record counts (products: 56, sales: 43, customers: 16, repairs: 36, history: 63, audit: 236) remained 100% identical.
