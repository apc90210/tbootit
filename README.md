# Technoreboot Core MVP

## Overview
This is the MVP prototype for the Technoreboot project. It consists of:
- **Core API**: FastAPI backend managing the database, storage, inventory, and repair orders.
- **Admin Shell**: Simple HTML/FastAPI frontend for managing data.
- **Repairs Module**: Dedicated microservice for repair intake, registry, status filtering, diagnostic fee management, simple repair diagnosis, manual estimate tracking, and automatic accounting integration with sales (Stage 05C).
- **Avito Module**: Microservice for authorized Avito catalog import, multi-account browser profile management, and account listings sync (Stage 06A).

## How to run
Make sure you have Docker and Docker Compose installed.
```bash
docker compose up --build -d
```

## Service URLs
- Core API: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs
- Admin Shell: http://127.0.0.1:8011
- Avito Accounts UI: http://127.0.0.1:8020/accounts
- noVNC Browser Login: http://127.0.0.1:8061

## How to test
See `docs/manual_test.md` for manual testing scenarios.
You can run automated tests via:
```bash
docker compose exec core pytest
```

## How to stop
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
