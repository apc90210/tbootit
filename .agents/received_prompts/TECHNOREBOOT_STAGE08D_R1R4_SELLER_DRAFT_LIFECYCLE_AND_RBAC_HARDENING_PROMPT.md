# TECHNOREBOOT — Stage 08D-R1R4
## Seller draft lifecycle + RBAC hardening

**Project:** ТехноРебут
**Local workspace:** `C:\tbootit`
**Production VDS:** `https://144.31.50.134`
**Stage:** `Stage 08D-R1R4 — Seller Draft Lifecycle and RBAC Hardening`

# 0. WHY THIS REVISION EXISTS

The previous security/RBAC stage is mostly correct, but supervisor audit found one lifecycle loophole that must be closed before acceptance.

Current report states that `draft` was added as a valid transition from:

```text
in_stock
reserved
imported
written_off
```

and that draft can then be returned to `in_stock`.

This creates a dangerous bypass:

```text
written_off -> draft -> in_stock
reserved    -> draft -> in_stock
```

A SELLER must not be able to resurrect written-off stock or bypass reservation state by using `draft`.

Owner requirement is narrower:

> Seller may hide an available product in draft and return that draft to availability.

Therefore the safe seller workflow is:

```text
in_stock -> draft
draft -> in_stock
```

No other status may use `draft` as a bypass.

This revision must also produce safe production RBAC proof without invoking destructive production actions.

Do NOT reset, seed, restore, or replace production data.
Do NOT copy local data to VDS.
Deploy code only.

First copy this prompt unchanged:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE08D_R1R4_SELLER_DRAFT_LIFECYCLE_AND_RBAC_HARDENING_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE08D_R1R4_SELLER_DRAFT_LIFECYCLE_AND_RBAC_HARDENING_PROMPT.md`

---

# 1. PREFLIGHT

Record:

```text
LOCAL_HEAD
ORIGIN_MAIN_HEAD
LOCAL_GIT_STATUS
VDS_REPO_HEAD
VDS_PRODUCTS
VDS_SALES
VDS_REPAIRS
VDS_PHOTOS
VDS_EXTERNAL_LISTINGS
VDS_DB_SHA256
VDS_CA_SHA256
```

Production currently contains real data. Preserve it.

Expected recent baseline from report:

```text
PRODUCTS=149
SALES=0
REPAIRS=0
PHOTOS=149
LISTINGS=149
```

If counts have changed because real users are already working, that is acceptable:
- record current values;
- never overwrite or reset them.

---

# 2. FIX DRAFT STATUS LIFECYCLE

Audit `core/app/routers/products.py` and all UI/API status-change paths.

Required seller-safe behavior:

```text
in_stock -> draft    ALLOWED
draft -> in_stock    ALLOWED

reserved -> draft    FORBIDDEN
written_off -> draft FORBIDDEN
sold -> draft        FORBIDDEN
archive -> draft     FORBIDDEN
```

If `imported` is still an active runtime status:
- do NOT use `draft` as a generic escape hatch;
- preserve the existing intended import lifecycle;
- only allow `imported -> draft` if there is a documented real business need and it cannot bypass stock/accounting semantics;
- otherwise forbid it too.

Preferred minimal rule for `draft`:

```text
draft is a temporary visibility state for available stock only.
```

Do not change unrelated status transitions.

---

# 3. UI RULES

For SELLER UI:

- show **"Убрать в черновик"** only for an `in_stock` product;
- show **"Вернуть в наличие"** only for a `draft` product;
- do not show draft actions for `reserved`, `written_off`, `sold`, `archive`.

Backend remains authoritative even if UI is bypassed.

OWNER may see the same safe draft workflow.
Do not add a hidden owner bypass from `written_off` through `draft`.

If future OWNER restore of written-off goods is needed, it must be a separate explicit audited operation, not abuse `draft`.

---

# 4. BACKEND TESTS FOR STATUS SAFETY

Add focused tests proving:

```text
in_stock -> draft = 200
draft -> in_stock = 200

reserved -> draft = rejected
written_off -> draft = rejected
sold -> draft = rejected
archive -> draft = rejected
```

Also prove invalid transition does not alter:
- product status;
- quantity;
- storage location;
- audit history except an allowed rejection log if one intentionally exists.

Required:

```text
FAILED = 0
```

---

# 5. SAFE SELLER RBAC PROOF

Do NOT call a potentially destructive production endpoint merely to see whether USER is blocked.

Instead prove the layers safely.

## A. Gateway auth proof

Using a valid USER certificate against `/internal-auth/verify` or the equivalent auth-request validation path, simulate/validate these target paths:

```text
/admin-api/dev-reset
/admin-api/seed
/dev-reset
/seed
/admin-api/avito/profiles/<test-key>
/backups
/certificates
```

Required USER result:

```text
403 OWNER certificate required
```

Do not invoke the underlying destructive handler.

## B. OWNER route policy proof

Verify OWNER authorization is accepted by the auth layer for OWNER-only routes, without executing destructive actions.

For production `/admin-api/dev-reset`, separately prove the production guard rejects OWNER with 403.

## C. Backend direct tests

Use local TestClient/unit/integration tests to prove:
- USER cannot call reset;
- USER cannot call seed;
- USER cannot delete Avito profile;
- production reset is forbidden even to OWNER;
- OWNER-only UI controls are absent for USER.

---

# 6. NO HARD DELETE AUDIT — SELLER

Perform a route inventory across:
- core;
- admin-shell;
- inventory-sales-module;
- repairs-module;
- avito-module.

Enumerate every `DELETE` route and every action whose implementation physically deletes DB rows.

For each one classify:

```text
ROUTE
ENTITY
HARD_DELETE_OR_SOFT_DELETE
OWNER_ONLY
USER_ALLOWED
AUDITED
```

Acceptance requirement:

> No USER-accessible route may physically delete persistent business information.

Soft business actions are allowed only when they preserve the record and audit trail.

Explicitly verify at minimum:
- products;
- sales;
- repairs;
- customers;
- categories;
- product photos;
- Avito profiles;
- external listings;
- stock/inventory records.

If any USER-accessible hard-delete path exists:
- close it;
- prefer soft state transition or OWNER-only policy as appropriate;
- add regression test.

Do not invent new hard-delete functions.

---

# 7. EXTENSION HOST-PERMISSION AUDIT

Audit Chrome Extension v0.2.55 `manifest.json`.

Previous version used broad:

```text
https://*/*
```

If this broad permission is still present, determine whether it is truly required.

Preferred production-safe permissions:
- current VDS origin `https://144.31.50.134/*`;
- localhost/127.0.0.1 dev origins;
- Avito origins genuinely required by the extension.

Avoid blanket `https://*/*` unless the implementation genuinely requires arbitrary HTTPS server targets.

If dynamic arbitrary server support is needed, prefer `optional_host_permissions` + explicit user-granted permission rather than permanent blanket access.

If manifest changes:
- bump extension version to `0.2.56`;
- rebuild ZIP;
- run extension regression tests;
- production extension page must serve the matching version.

Do not change extension version if no manifest/runtime change is required.

---

# 8. TESTS

Run at minimum:

```text
core/tests/test_product_safety_and_draft.py
core/tests/test_products.py
admin-shell/tests/test_seller_rbac_and_data_safety.py
admin-shell/tests/test_certificate_auth.py
tests/test_production_data_guard.py
tests/test_stage08b_r1_production_baseline.py
```

Plus:
- new DELETE-route inventory tests;
- extension tests if manifest changes.

Required:

```text
FAILED=0
```

---

# 9. CODE-ONLY PRODUCTION DEPLOY

Before deploy:
- create VDS production backup;
- record current business counts;
- record DB SHA256 and CA SHA256.

Deploy ONLY through:

```text
deploy/production/update_code_only.sh origin/main
```

Never use bootstrap restore.
Never copy local DB/media/auth/Avito business state.

After deploy:
- all 6 services healthy;
- counts unchanged;
- CA unchanged.

---

# 10. NON-DESTRUCTIVE PRODUCTION PROOF

Do NOT mutate a real product for verification.

On VDS prove:
- relevant source/runtime commit deployed;
- route/auth policy active;
- USER auth layer rejects owner-only destructive paths safely;
- OWNER production reset guard returns 403;
- all primary UI routes remain healthy.

Do not call production seed.
Do not delete Avito profiles.
Do not change a real product status.

Production data must remain unchanged during proof.

---

# 11. DOCUMENTATION

Create:

`reports/stage08d_r1r4_seller_draft_lifecycle_and_rbac_hardening_report.md`

Update:

`docs/production_status.md`

`docs/production_deployment_model.md`

`logs/2026-09-12.md`

Preserve received prompt.

---

# 12. GIT / SAFETY

Never commit:
- production DB;
- media;
- backup archives;
- TLS/client private keys;
- production secrets.

Commit safe code/tests/docs/reports.

Push `origin/main`.

Final worktree clean.

---

# 13. FINAL REPORT CONTRACT

Return:

```text
# Stage 08D-R1R4 — Seller Draft Lifecycle and RBAC Hardening

## Draft Lifecycle
IN_STOCK_TO_DRAFT:
DRAFT_TO_IN_STOCK:
RESERVED_TO_DRAFT:
WRITTEN_OFF_TO_DRAFT:
SOLD_TO_DRAFT:
ARCHIVE_TO_DRAFT:
IMPORTED_TO_DRAFT:
DRAFT_BYPASS_CLOSED:

## UI
SELLER_DRAFT_BUTTON_IN_STOCK:
SELLER_RETURN_BUTTON_DRAFT:
DRAFT_ACTION_RESERVED_HIDDEN:
DRAFT_ACTION_WRITTEN_OFF_HIDDEN:
DRAFT_ACTION_SOLD_HIDDEN:

## RBAC
USER_DEV_RESET_AUTH:
USER_SEED_AUTH:
USER_AVITO_PROFILE_DELETE_AUTH:
USER_BACKUPS_AUTH:
USER_CERTIFICATES_AUTH:
OWNER_PRODUCTION_DEV_RESET:
DESTRUCTIVE_HANDLER_INVOKED_DURING_PROOF: false

## Hard Delete Audit
DELETE_ROUTES_FOUND:
USER_ACCESSIBLE_HARD_DELETE_ROUTES:
PRODUCTS:
SALES:
REPAIRS:
CUSTOMERS:
CATEGORIES:
PRODUCT_PHOTOS:
AVITO_PROFILES:
EXTERNAL_LISTINGS:
INVENTORY:
SELLER_NO_HARD_DELETE_PROVEN:

## Extension
EXTENSION_VERSION:
BROAD_HTTPS_HOST_PERMISSION_PRESENT:
HOST_PERMISSION_RESULT:
ZIP_REBUILT:

## Tests
FAILED:

## Production Safety
PRE_DEPLOY_BACKUP:
PRODUCTS_BEFORE:
PRODUCTS_AFTER:
SALES_BEFORE:
SALES_AFTER:
REPAIRS_BEFORE:
REPAIRS_AFTER:
PHOTOS_BEFORE:
PHOTOS_AFTER:
LISTINGS_BEFORE:
LISTINGS_AFTER:
DB_SHA256_BEFORE:
DB_SHA256_AFTER:
CLIENT_CA_SHA256_UNCHANGED:
LOCAL_DATA_SYNCED_TO_VDS: false

## Runtime
ALL_SERVICES_HEALTHY:
PRODUCTION_URL: https://144.31.50.134

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE08D_R1R4_SELLER_DRAFT_LIFECYCLE_AND_RBAC_HARDENED

PRODUCTION_DATA_PRESERVED: true
FUTURE_DEPLOYS_CODE_ONLY: true
DO_NOT_START_NEXT_STAGE_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- reserved/written_off can still reach draft;
- USER can hard-delete persistent business data;
- destructive production proof mutates real data;
- production data changes unexpectedly;
- tests fail.

---

# 14. STOP

After proof, STOP.

Wait for Owner/Supervisor acceptance.
