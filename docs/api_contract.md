# API Contract

## Endpoints
- `GET /health`
- `GET /api/version`
- `GET/POST /api/products` (GET supports filtering via query params)
- `GET /api/products/meta`
- `GET /api/products/{id}/details`
- `PATCH /api/products/{id}`
- `PATCH /api/products/{id}/status`
- `POST /api/products/{id}/stock-adjustment`
- `PATCH /api/products/{id}/site-publication`
- `PATCH /api/products/{id}/avito-publication`
- `GET/POST /api/products/{id}/events`
- `DELETE /api/products/{id}` (soft delete)
- `POST /api/products/{id}/photos`
- `GET /api/products/{id}/photos`
- `DELETE /api/products/{id}/photos/{photo_id}`
- `GET/POST /api/categories`
- `GET/POST/PATCH /api/customers`
- `GET/POST/PATCH /api/repairs`
- `PATCH /api/repairs/{id}/status`
- `GET/POST /api/sales`

## Admin
- `GET /api/admin/db/schema`
- `GET /api/admin/stats`
- `GET /api/admin/audit-log`
- `POST /api/admin/seed`
- `POST /api/admin/dev-reset`
