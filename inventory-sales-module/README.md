# Inventory / Sales Module

This module serves as the primary Russian-localized UI for inventory and sales operations in the Technoreboot platform.

**Stage 04D (Current):** Skeleton and Read-Only Catalog  
*Sales are scheduled for Stage 04E, Price Tags for Stage 04F.*

## Architecture Constraint
- Works strictly via REST HTTP calls to `core`.
- Prohibits direct manipulation of databases or SQL execution.
- Disallows automated browser integration logic (Selenium/Playwright).

## Quick Start
```bash
docker compose up -d inventory-sales-module
```
Running on `http://localhost:8030`.
