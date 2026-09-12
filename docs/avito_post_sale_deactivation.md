# Avito Post-Sale Deactivation Automation

**Stage:** Stage 09A LOCAL  
**Environment:** LOCAL Development Sandbox (`https://localhost:8443`)  
**Status:** Implemented & Verified in LOCAL  
**Production VDS Impact:** NONE (Strict Schema Guard enforced; VDS migration deferred)

---

## 1. Overview & Architecture

When a sale is completed in Technoreboot, any sold item that is linked to an active Avito listing triggers a post-sale deactivation follow-up.

### Key Architectural Principles
1. **Sale Integrity First:** Sale completion and physical inventory decrement are committed strictly BEFORE any Avito interaction. Avito unavailability or errors NEVER block, roll back, or invalidate a sale.
2. **Persistent Task Lifecycle:** Tasks are stored in SQLite table `avito_post_sale_tasks`, stateful and idempotent.
3. **Capability Hierarchy:**
   - **Official Avito API:** Capability probe checks `can_deactivate_listing`. In Stage 09A, `OFFICIAL_API_AVAILABLE = False`.
   - **Chrome Extension Task Channel:** Browser-assisted execution via paired extension token.
   - **Manual Required Fallback:** If selectors/UI change or errors exceed 3 attempts, task transitions to `manual_required`.
4. **Physical Stock Non-Mutation:** Physical stock is managed solely by sales and inventory modules. Avito tasks NEVER alter product quantities.
5. **No Automatic Republishing:** If a sale is canceled after deactivation, the listing remains archived. Automatic republication is strictly prevented.

---

## 2. UX & Seller Workflow

### Single-Item Sale
Upon completing a sale of a product with an active Avito listing:
```text
Продажа оформлена.
Товар: HP LaserJet Pro M404n
Avito №1234567890 активно.

Снять объявление с Avito?
[ Не сейчас ]   [ Снять с Avito ]
```

- **[ Не сейчас ]:** Dismisses the prompt from the sales view. The task remains saved in status `suggested` in the post-sale queue (`/avito/post-sale`).
- **[ Снять с Avito ]:** Transitions task to `queued` for automated deactivation.

### Multi-Item Cart Sale
When multiple items are sold simultaneously:
```text
Продажа оформлена.
Найдено активных объявлений Avito: 3

[ Не сейчас ]   [ Снять все (3) ]
```

---

## 3. Persistent Task Model (`avito_post_sale_tasks`)

### Table Schema
| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | No (PK) | Auto-increment task ID |
| `sale_id` | INTEGER | No | FK -> `sales.id` |
| `product_id` | INTEGER | No | FK -> `products.id` |
| `external_listing_id` | INTEGER | Yes | FK -> `product_external_listings.id` |
| `avito_listing_id` | TEXT | No | External Avito ID (e.g. `"1234567890"`) |
| `listing_url` | TEXT | No | Canonical Avito URL |
| `status` | TEXT | No | Task state |
| `action` | TEXT | No | Default: `'deactivate'` |
| `requested_by` | TEXT | Yes | Seller name / identity |
| `requested_at` | DATETIME | No | Timestamp task was created |
| `started_at` | DATETIME | Yes | Timestamp task processing began |
| `finished_at` | DATETIME | Yes | Timestamp task reached terminal state |
| `attempt_count` | INTEGER | No | Number of execution attempts (default 0) |
| `last_error` | TEXT | Yes | Error message from last failure |
| `execution_mode` | TEXT | No | `'extension'`, `'official_api'`, or `'manual'` |
| `result_metadata` | TEXT (JSON) | Yes | Structured execution results |

### Idempotency Key
Unique constraint `uix_sale_prod_avito_deact` on:
```sql
UNIQUE (sale_id, product_id, avito_listing_id, action)
```
Duplicate clicks, page reloads, or duplicate API calls safely return the existing task.

### Task States
```text
suggested  ──[ Seller clicks "Снять" ]──>  queued
                                              │
                                              ▼ (Extension pops task)
                                          processing
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    │                                                   │
        [ External Confirmation ]                           [ Failure ]
                    │                                                   │
                    ▼                                                   ▼
                 success                                           failed
                                                                        │
                                                    ┌───────────────────┴───────────────────┐
                                                    │                                       │
                                           (attempt < 3)                    (attempt >= 3)
                                                    │                                       │
                                                    ▼                                       ▼
                                              [ Retry / Queue ]                     manual_required
                                                    │                                       │
                                                    ▼                                       ▼
                                                 queued                              (Staff manual check)
```

---

## 4. Chrome Extension Task Channel (v0.2.57)

### Bridge Endpoints (`avito-module`)
- `GET /tasks/next`: Fetches oldest `queued` task, transitions to `processing`, increments `attempt_count`.
- `POST /tasks/{task_id}/started`: Acknowledges execution start.
- `POST /tasks/{task_id}/success`: Confirms external listing deactivation.
- `POST /tasks/{task_id}/failed`: Reports execution failure.

### Security Validation
Before dispatching a task to the browser, the backend enforces:
1. `listing_url` domain must be `avito.ru` or `*.avito.ru`.
2. URL scheme must be `http` or `https`.
3. `avito_listing_id` must match the URL path.
If validation fails, the task transitions immediately to `manual_required` with `can_retry: false` to prevent arbitrary URL injection.

---

## 5. Success Semantics & Audit Log

Task is marked `success` **only** upon external confirmation.
When success is confirmed:
1. `avito_post_sale_tasks.status = 'success'`
2. `product_external_listings.remote_status = 'archived'`
3. Audit event written to `audit_log`:
   - `action`: `'avito_listing_deactivated_after_sale'`
   - `entity_type`: `'avito_post_sale_task'`
   - `entity_id`: task ID
   - `new_value`: contains `sale_id`, `product_id`, `avito_listing_id`, `execution_mode`, `timestamp`.

---

## 6. RBAC Matrix

| Action / Resource | USER Role (Seller) | OWNER Role |
| :--- | :---: | :---: |
| View Post-Sale Follow-up in Sale Detail | Allowed | Allowed |
| Queue Deactivation (`POST /sales/{id}/avito-deactivate`) | Allowed | Allowed |
| View Cleanup Queue UI (`/avito/post-sale`) | Allowed | Allowed |
| List Tasks API (`GET /admin-api/avito/post-sale-tasks`) | Allowed | Allowed |
| Retry / Queue / Cancel Post-Sale Task | Allowed | Allowed |
| Delete / Administer Avito Profiles | **Forbidden (403)** | Allowed |
| Operations Page (`/system/operations`) | **Forbidden (403)** | Allowed |

---

## 7. Schema Guard Compliance

Adding table `avito_post_sale_tasks` constitutes a schema expansion:
1. Local databases `data/db/technoreboot.db` and `core/technoreboot.db` contain the table.
2. `deploy/production/schema_contract.json` updated with SHA256: `ae36c0163d7dcd5fa4a4f8e977008566f84f1016b2aa3d686bd31228f43aa886`.
3. `deploy/production/deployment_compatibility.json` set to:
   ```json
   {
     "requires_manual_migration": true,
     "database_change": true,
     "reason": "Stage 09A: added avito_post_sale_tasks table for post-sale deactivation workflow"
   }
   ```
4. VDS deployment is **BLOCKED** by Schema Guard until a dedicated manual migration stage is approved by the Owner.
