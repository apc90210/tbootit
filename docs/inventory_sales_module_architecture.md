# Inventory/Sales Module Architecture

## Purpose
The primary point-of-sale interface for shop employees and technicians to interact with inventory, initiate sales, and print required documentation.

## Strict Independence
- **No SQLite:** The module must not connect to `technoreboot.db`.
- **Core HTTP Transport:** All reading and writing goes through `http://core:8000/api/*`.
- **Fallback Tolerant:** Returns localized `error.html` views safely if the `core` goes offline.

## Technologies
- `FastAPI`: High performance routing.
- `Jinja2`: HTML generation engine.
- `HTTPX`: Asynchronous client for making non-blocking calls to `core`.
