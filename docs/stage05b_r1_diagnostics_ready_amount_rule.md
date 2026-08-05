# Stage05B-R1 Diagnostics-to-Ready Amount Rule

## Overview

Stage05B-R1 refines the status transition rule for repair orders moving from `diagnostics` to `ready` («Диагностика» -> «Готов»). In accordance with owner requirements:

1. **Single Criteria**: The ONLY mandatory condition for transitioning from `diagnostics` to `ready` is that `estimated_repair_amount` must be populated (`estimated_repair_amount is not None`).
2. **Zero Value Handled Correctly**: `0` is a valid, filled integer amount (`0 ₽`). It is NOT treated as empty or falsy.
3. **No Text Field Constraints**: `diagnosis_text`, `planned_works_text`, `planned_parts_text`, and the status transition `comment` are completely OPTIONAL. The transition cannot be blocked due to empty text fields or empty comments.
4. **Validation Error Message**: If `estimated_repair_amount` is `None` (null), the transition is blocked with HTTP 400 and returns:
   `"Для перехода в статус «Готов» укажите предполагаемую стоимость ремонта. Можно указать 0 ₽."`
5. **UI Convenience**: The UI displays the user-friendly Russian error message and includes a direct action button/link: `"Указать стоимость ремонта"` leading to `/repairs/{id}/edit`.

## Core API Changes

- In `core/app/routers/repairs.py` (`update_repair_status`), status transition `diagnostics -> ready` evaluates `if db_repair.estimated_repair_amount is None: raise HTTPException(400, detail=...)`.
- Removed mandatory status comment requirement for `diagnostics -> ready`.
- When comment is provided, it is stored in `RepairStatusHistory.comment`. If omitted, `comment=None` is stored.

## UI Changes

- In `repairs-module/app/routers/repairs.py` (`update_repair_status_submit`), removed comment validation for `diagnostics -> ready`. Added pre-check for `estimated_repair_amount is None` returning Russian error.
- In `repairs-module/app/templates/repair_detail.html`, error message box includes button/link `"Указать стоимость ремонта"` leading to `/repairs/{{ repair.id }}/edit`.
