# Technoreboot Core MVP

## Overview
This is the MVP prototype for the Technoreboot project. It consists of:
- **Core API**: FastAPI backend managing the database, storage, inventory, and repair orders.
- **Admin Shell**: Simple HTML/FastAPI frontend for managing data.
- **Repairs Module**: Dedicated microservice for repair intake, registry, status filtering, diagnostic fee management, simple repair diagnosis, manual estimate tracking, and automatic accounting integration with sales (Stage 05C).
- **Avito Module**: Microservice for authorized Avito catalog import, multi-account browser profile management, embedded noVNC authentication, 1-item trial probe import, and idempotency verification (Stage 06A-R2).

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

## Service URLs
- Admin Shell & Avito Management UI: http://127.0.0.1:8011 (or http://127.0.0.1:8011/avito)
- Core API: http://127.0.0.1:8000
- Core API Docs: http://127.0.0.1:8000/docs
- Inventory & Sales UI: http://127.0.0.1:8030
- Repairs Module UI: http://127.0.0.1:8040

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
