# Manual Testing Scenarios

1. Add a product (via Admin Shell API or Docs).
2. Upload a photo via Docs `POST /api/products/{id}/photos`.
3. Change product status to `sold` via Admin Shell.
4. Create a customer.
5. Create a repair.
6. Conduct a sale (product status should update).
7. View DB structure at `http://127.0.0.1:8000/api/admin/db/schema`.
8. View Audit Log at `http://127.0.0.1:8000/api/admin/audit-log`.
9. Restart Docker: `docker compose down` then `docker compose up`. Verify data persists.
