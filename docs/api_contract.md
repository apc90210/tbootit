# API Contract

## Endpoints
- `GET /health`
- `GET /api/version`
- `GET/POST /api/products`
- `PATCH /api/products/{id}`
- `PATCH /api/products/{id}/status`
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
