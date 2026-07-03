# Stage 04E-R6-R: Organization Receipt Runtime Backfill Repair

## Overview
This document summarizes the repair done to fix empty organization settings and receipt warranty texts encountered by the owner after Stage 04E-R6.

## Root Causes
- The initial defaults seeding in Core only occurred if the `OrganizationSettings` row was completely missing. If the row existed but had blank values (which is a valid state if created during previous tests or DB migrations), the blank values were served.
- The UI in `inventory-sales-module` had a bad route path `/settings/organization` (missing `/api/` prefix) when calling Core, resulting in a 404. Since there was no fallback in the UI, empty fields were rendered.

## Resolution
1. **Core Backfill Logic**: Refactored defaults into `core/app/defaults.py` and updated `core/app/routers/settings.py` so that a `GET /api/settings/organization` actively backfills any blank fields on an existing DB row, commits the change, and returns the effective settings.
2. **UI Fallback Logic**: Added `inventory-sales-module/app/defaults.py` to store fallback values. The API client path was fixed in `inventory-sales-module/app/core_client.py` to properly target `/api/settings/organization`. The UI routers (`sales.py` and `settings.py`) were updated to use `get_effective_settings()`, which ensures that if Core is ever down or returns invalid/blank data, the UI still safely renders the defaults.
3. **Tests added**: New Pytest functions added to both Core and Inventory modules to cover the backfill and fallback behaviors.
