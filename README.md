# Technoreboot Core MVP

## Overview
This is the MVP prototype for the Technoreboot project. It consists of:
- **Core API**: FastAPI backend managing the database, storage, inventory, and repair orders.
- **Admin Shell**: Unified navigation interface (`http://localhost:8011`) reverse-proxying all modules under a single top menu bar.
- **Repairs Module**: Dedicated microservice for repair intake, registry, status filtering, diagnostic fee management, simple repair diagnosis, manual estimate tracking, and automatic accounting integration with sales (Stage 05C).
- **Avito Module**: Microservice for mandatory manual Avito login via embedded noVNC Chromium browser (`Xvfb`, `x11vnc`, `websockify` auto-started runtime), persistent account profiles, 1-item trial probe import, and same-origin parsing (Stage 06A-R5).

## How to run
For standard non-technical usage (Zero-CLI owner workflow on Windows):
Double-click `scripts/start_technoreboot.cmd` or run in command prompt:
```cmd
scripts/start_technoreboot.cmd
```
For developers:
```bash
docker compose up --build -d
```

## Service URLs (Owner Access)
- **Single Owner Interface**: http://localhost:8011
  - Dashboard: `http://localhost:8011/`
  - Products & Inventory: `http://localhost:8011/inventory/products`
  - Sales & Reports: `http://localhost:8011/inventory/sales`
  - Repairs: `http://localhost:8011/repairs/repairs`
  - Avito Settings & Auth: `http://localhost:8011/avito`

## How to test
Run automated tests across modules:
```bash
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
pytest admin-shell/tests
pytest avito-module/tests
```

## How to stop
Run `scripts/stop_technoreboot.cmd` or:
```bash
docker compose down
```


## Data Locations
- Database: `./data/db/technoreboot.db`
- Photos: `./data/storage/product_photos/`

## Known Limitations
- Admin Shell is highly simplified and meant for testing.
- No frontend framework is used for Admin Shell.
- Hard deletions are replaced with soft deletions (`written_off` status).
