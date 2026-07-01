# Stage 04D: Inventory/Sales Module Skeleton

This stage introduces the foundational `inventory-sales-module`.

## Goal
Establish a reliable, segregated frontend application container connected seamlessly to the `core` API, ensuring that inventory inspection operations function completely separated from the backend logic/DB layer.

## Architecture Guidelines
- Port: `8030`
- Uses `FastAPI` to render `Jinja2` templates dynamically.
- Interfaces via `CoreClient` exclusively for API querying.

## Included Routes
- `/`: Main dashboard (Russian UI).
- `/products`: Searchable, filterable list of all known inventory.
- `/products/{product_id}`: Dedicated detail page.
- `/api/core/health`: Downstream `core` probe.
