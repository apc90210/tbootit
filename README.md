# Technoreboot Core MVP

## Overview
This is the MVP prototype for the Technoreboot project. It consists of:
- **Core API**: FastAPI backend managing the database and storage.
- **Admin Shell**: Simple HTML/FastAPI frontend for managing data.

## How to run
Make sure you have Docker and Docker Compose installed.
```bash
docker compose up --build -d
```

## Service URLs
- Core API: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs
- Admin Shell: http://127.0.0.1:8011

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
