# Stage 05A-R3: Default Intake Text & Diagnostics-to-Ready Transition Documentation

## 1. Overview
Stage 05A-R3 delivers two targeted owner-requested refinements for **Stage 05A (Repair Intake & Registry MVP)**:
1. **Pre-populated Intake Defaults**: Pre-populates the exact default lists for "Комплектность" and "Внешний вид" when opening `GET /repairs/new`.
2. **`diagnostics -> ready` Transition with Mandatory Comment**: Enables direct transition from `diagnostics` status to `ready` status with mandatory non-empty work summary comment.

---

## 2. Intake Defaults Specification
- **`completeness` Default**: `"Ноутбук, зарядка, чехол..."`
- **`appearance` Default**: `"Потёртости, царпины..."`
- **Application Rule**: Pre-populated as actual input values (`value="..."`) on clean initial `GET /repairs/new`.
- **User Modification**: Users can edit text, remove items, clear fields completely, or add new details.
- **Validation Retention**: When form validation fails, submitted values (modified or cleared) are preserved — defaults are **not** restored over user edits or empty strings.
- **Edit Isolation**: `GET /repairs/{id}/edit` renders only saved database values and never overlays defaults over saved empty strings.
- **API Decoupling**: Core API does not force UI defaults on raw intake endpoints.

---

## 3. `diagnostics -> ready` Transition Specification
- **Transition Matrix**: Updated `diagnostics` valid next statuses: `waiting_customer`, `waiting_parts`, `in_repair`, `ready`, `unrepairable`, `canceled`.
- **Mandatory Comment**: `diagnostics -> ready` requires a non-empty comment describing completed repair/fix.
- **Validation**: If comment is empty or whitespace-only, Core API returns **HTTP 400 Bad Request** (`detail="Для перехода из диагностики в статус 'Готов' требуется указать комментарий с описанием выполненных работ"`). Status remains `diagnostics`, no history or audit entries created.
- **Success Behavior**: When valid comment is provided, status becomes `ready`, `updated_at` updates, `RepairStatusHistory` record stores comment, `repair.status_changed` audit event is logged. Note that `ready` status does **not** close repair (`closed_at` remains `None`).
- **UI Integration**: `repair_detail.html` displays "Готов" option under `diagnostics` status, and `repairs-module` validates and displays user-friendly Russian error message if comment is omitted.
