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

## 4. Chrome Extension Task Channel & Real Deactivation Executor (v0.2.58)

### Extension Lifecycle & Modules
- **Manifest:** Version `0.2.58`, permissions include `"alarms"` and `"storage"`.
- **Background Service Worker (`service_worker.js`):**
  - Polling loop via `chrome.alarms` (and fallback `setInterval`) calling `/tasks/next`.
  - **Active Task Locking & Persistence:** Exactly one task executed at a time. The active task is stored in `chrome.storage.local` with timestamp. If a task exceeds 5 minutes (300 seconds), timeout recovery clears the stale lock.
  - **Target Validation:** Verifies host is `avito.ru` or `*.avito.ru`, URL scheme is `http`/`https`, and `avito_listing_id` matches the URL path. Mismatches fail fast to `manual_required`.
  - Coordinates tab navigation, waits for `status === "complete"`, and dispatches message `execute_deactivation` to the content script.
  - Handles response events: `dry_run_ready`, `confirmed`, `manual_required`, and communicates status back to `/tasks/{id}/started`, `/tasks/{id}/success`, or `/tasks/{id}/failed`.
- **Content Script (`content.js`):**
  - Validates current host is `avito.ru` and page listing ID matches task target.
  - **Conservative DOM Discovery:**
    - Checks `DEACTIVATION_WHITELIST`: `["снять с публикации", "снять объявление", "деактивировать", "архивировать", "убрать с публикации"]`.
    - Enforces `DEACTIVATION_BLACKLIST`: rejects buttons/links containing `оплатить`, `продвинуть`, `разместить`, `редактировать`, `поднять`, `турбо`, `x2`, `x5`, `x10`, `x20`, `активировать`, `купить`, `доставка`.
    - Rejects ambiguous states: if multiple matching controls are found without an exact unambiguous match, fails fast to `manual_required`.
  - **Inactive Check:** If the listing is already inactive (`объявление снято с публикации`, `в архиве`, or presence of `опубликовать снова`), reports confirmed inactive state without redundant clicks.
  - **Modal Handling:** Detects Avito post-click confirmation modal and selects safe reason (`Товар продан на Авито` or `Снял с продажи`).
  - **Mandatory Confirmation:** Success is reported **only** when DOM confirms inactive state (`waitForConfirmedInactiveState`).
- **Dry-Run Safety Mode (`avito_deactivation_dry_run = true`):**
  - Enabled by default to prevent accidental deactivations during testing and development.
  - Finds and highlights the deactivation button with dashed yellow border (`outline: 3px dashed #eab308`).
  - Displays non-destructive floating banner on page: `"Тестовый режим (Dry-Run): кнопка деактивации найдена, клик заблокирован"`.
  - Updates popup status to `"Готово к снятию: кнопка найдена"`.
  - **Safety Contract:** Never clicks destructive control and never reports success to server.
- **Popup UX (`popup.html`, `popup.js`):**
  - Card showing active post-sale task ID, target Avito ID, and dry-run toggle checkbox.
  - Mode badge: `ТЕСТОВЫЙ РЕЖИМ (Dry-Run)` vs `РЕАЛЬНЫЙ РЕЖИМ (Armed)`.
  - 6-step progress indicator:
    1. Поиск задачи в очереди
    2. Задача получена
    3. Открытие страницы Avito
    4. Анализ страницы
    5. Выполнение деактивации (или Dry-Run проверка)
    6. Подтверждение и завершение

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

---

## 8. Stage 09A-R2: Action Contract Alignment & Permanent Sale Detail UX

### Action Contract Discrepancy & Resolution
During real Owner testing with Avito ID `7353766377` (Sale #1), tasks failed with:
`Status: manual_required, Attempts: 1 / 3, Error: Unsupported action: deactivate`

- **Root Cause:** 
  The Core business model and SQLite DB record `action = "deactivate"`.
  The Chrome Extension v0.2.58 `service_worker.js` strictly required `task.action === "deactivate_listing"`.
- **Resolution (Zero-DB-Migration):**
  1. **Bridge Adapter Mapping:** `avito-module/app/routers/extension_bridge.py` defines `BUSINESS_ACTION_DEACTIVATE = "deactivate"` and `EXTENSION_ACTION_DEACTIVATE_LISTING = "deactivate_listing"`. When serializing tasks for the extension (`/admin-api/avito-extension/tasks/next`), the adapter maps `deactivate` to `deactivate_listing`.
  2. **Extension Tolerance & Security Guard:** `chrome-extension/technoreboot-avito/service_worker.js` defines `SUPPORTED_DEACTIVATION_ACTIONS = ["deactivate_listing", "deactivate"]`. Both actions are accepted. Any unauthorized or unknown actions (e.g. `delete_account`, `publish_listing`, `pay_promotion`) are strictly rejected with `Unsupported action: ${task.action}`.
  3. **Version Bump:** Extension bumped to `0.2.59` across `manifest.json`, `service_worker.js`, `content.js`, `popup.html`, `popup.js`, and `admin-shell`.

### Permanent Sale Detail UX (Section 6A)
- The sale detail view (`/sales/{sale_id}` or `/inventory/sales/{sale_id}`) now provides a permanent `[ Снять с Avito ]` action button next to `[ Товарный чек ]`.
- Sellers can request deactivation at any time, even if dismissed immediately post-sale or if previous attempts failed.
- In multi-item sales, an interactive dialog confirms deactivation of all linked active Avito listings.
- Clear status banners provide immediate, honest feedback:
  - `✓ Объявление уже снято с Avito`
  - `ⓘ Задачи на снятие с Avito уже обрабатываются`
  - `ⓘ Для этой продажи нет связанных объявлений Avito`
  - `✓ Задачи на снятие с Avito поставлены в очередь`

### Robust Browser Navigation & DOM Discovery (Section 6B)
- **Canonical URL Navigation:** Extension navigates directly to `https://www.avito.ru/{avito_listing_id}` or the stored canonical item URL.
- **Exact ID Verification:** `content.js` inspects `extractAvitoItemId(url)` and DOM `[data-item-id]` to verify that the active page matches the task's Avito ID. If IDs mismatch, execution aborts with `manual_required`.
- **Action Menu & Profile Card Discovery:** If deactivation controls are hidden in a submenu ("...", "Действия") or within profile cards (`/profile/items`), `content.js` dynamically expands the menu to find the control.
- **Tab Focus Preservation:** `service_worker.js` captures the `originalTabId` before opening the task tab. Upon completion in Armed mode, it restores focus to the seller's original working tab and closes the temporary Avito tab.

