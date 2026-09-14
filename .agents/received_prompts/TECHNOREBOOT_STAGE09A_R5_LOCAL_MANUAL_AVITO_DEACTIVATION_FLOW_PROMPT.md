# TECHNOREBOOT — Stage 09A-R5 LOCAL
## Simplify Avito removal to manual operator workflow

**Project:** ТехноРебут  
**Local workspace:** `C:\tbootit`  
**LOCAL URL:** `https://localhost:8443`  
**Production VDS:** `https://144.31.50.134`  
**Stage:** `Stage 09A-R5 LOCAL — Manual Avito Deactivation Flow`

# 0. OWNER DECISION — FINAL FOR CURRENT VERSION

Automatic browser deactivation is NOT reliable enough.

Do not keep trying to auto-click Avito controls in the normal workflow.

For the current production design, use a simple operator-assisted flow:

```text
Sale completed
↓
System detects linked active Avito listing
↓
Large prompt:
"Снять объявление с Avito?"
↓
[ Снять с Avito вручную ]   [ Не снимать ]
↓
If operator chooses manual removal:
open the exact linked Avito listing in browser
↓
operator manually removes it from publication on Avito
```

The system MUST NOT attempt to click Avito buttons automatically.

The system MUST NOT mark `success` merely because the page was opened.

This stage is LOCAL ONLY.
Do NOT deploy to VDS.

---

# 1. PROMPT PRESERVATION

Copy unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE09A_R5_LOCAL_MANUAL_AVITO_DEACTIVATION_FLOW_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE09A_R5_LOCAL_MANUAL_AVITO_DEACTIVATION_FLOW_PROMPT.md`

---

# 2. PREFLIGHT

Record:

```text
LOCAL_HEAD:
LOCAL_GIT_STATUS:
LOCAL_STACK_HEALTHY:
EXTENSION_VERSION:
CURRENT_POST_SALE_TASK_MODEL:
CURRENT_AUTOMATIC_DEACTIVATION_EXECUTOR:
```

Verify LOCAL-only environment.

Do not touch VDS.

---

# 3. REMOVE AUTOMATIC AVITO CLICK EXECUTION FROM NORMAL FLOW

Disable/remove normal runtime behavior that:

- polls post-sale deactivation tasks and auto-opens Avito;
- searches DOM for `Снять с публикации`;
- clicks deactivation controls;
- handles Avito removal confirmation dialogs;
- reports automatic success after browser execution.

The Chrome extension may still be used for other existing Avito features.

Do NOT break:
- Avito import;
- pairing;
- other accepted extension functionality.

Only remove/disable the automatic post-sale deactivation executor.

---

# 4. POST-SALE LARGE PROMPT

Immediately after successful sale, if one or more sold products have linked active Avito listings, show a large clear modal/card.

Single item example:

```text
Продажа оформлена

Товар:
AMD Athlon X4 950 AM4. Гарантия

Объявление Avito №7353766377 ещё активно.

[ Снять с Avito вручную ]
[ Не снимать ]
```

Requirements:

- modal appears AFTER sale commit;
- sale is already completed regardless of choice;
- button is large and obvious;
- no technical wording like Dry-Run / Armed / task / executor.

---

# 5. BUTTON: "СНЯТЬ С AVITO ВРУЧНУЮ"

When pressed:

1. Use the exact canonical linked Avito URL.
2. Open that exact listing in a new browser tab/window.
3. Do NOT run automatic DOM clicking.
4. Leave operator on the Avito page to remove it manually.
5. Keep TechnoReboot sale page intact in the original tab.

For a multi-item sale:

```text
Найдено 3 активных объявления Avito
```

Show each item separately with:

```text
[ Открыть объявление ]
```

Do not open many tabs automatically without an explicit click per listing.

---

# 6. BUTTON: "НЕ СНИМАТЬ"

When pressed:

- close/dismiss the prompt;
- do not open Avito;
- do not mutate listing status;
- do not fail or roll back the sale;
- keep the linked listing unchanged.

This is a normal valid choice.

---

# 7. PERMANENT ACTION ON SALE DETAIL PAGE

On every completed sale detail page, keep a permanent action near:

```text
[ Товарный чек ]
[ Вернуться к продажам ]
```

Add:

```text
[ Снять с Avito вручную ]
```

Behavior:

- always available later for linked Avito listings;
- opens the exact linked Avito listing;
- does not auto-click anything;
- does not disappear because operator previously clicked `Не снимать`.

If multiple listings are linked, show a small selection/modal with each product and Avito ID.

If no linked listing:

```text
Для этой продажи нет связанного объявления Avito
```

If known already inactive:

```text
Объявление уже снято с Avito
```

---

# 8. TASK / QUEUE SEMANTICS

Keep the persistent post-sale task model if useful for audit and pending cleanup.

But simplify the meaning:

```text
suggested      = operator has not chosen yet
manual_required = operator chose to open Avito for manual removal
success        = only when confirmed separately, not because the page opened
canceled       = operator chose "Не снимать" if current semantics use canceled
```

Do NOT set `success` when:
- link opened;
- browser tab opened;
- operator clicked the TechnoReboot button.

If there is no reliable automatic status confirmation, leave as `manual_required` / pending manual cleanup.

---

# 9. OPTIONAL MANUAL CONFIRMATION

If existing UX benefits from it, add a simple button on the queue/sale detail:

```text
[ Я снял объявление ]
```

This is OPTIONAL.

If implemented:
- require explicit user click;
- update local task to success/manual-confirmed;
- record `execution_mode = manual`;
- write audit event;
- do not pretend this was externally verified.

If not implemented, remote status may update later through existing Avito sync/import mechanisms.

Do not overcomplicate this stage.

---

# 10. POST-SALE QUEUE

Keep `/avito/post-sale` but make it operator-oriented.

Suggested columns:

```text
Дата
Продажа
Товар
Avito ID
Статус
Действие
```

Actions:

```text
[ Открыть объявление ]
[ Не снимать ]
```

If optional manual confirmation is implemented:

```text
[ Я снял объявление ]
```

Remove misleading automatic-executor wording.

---

# 11. CHROME EXTENSION

Do NOT require the extension to remove the listing anymore.

For this manual flow, opening the exact Avito URL may use normal browser navigation from TechnoReboot UI.

Prefer simplest implementation:

```text
target="_blank"
```

or equivalent controlled browser open.

Do not depend on extension polling merely to open the page.

The extension remains available for its other accepted features.

---

# 12. SECURITY / TARGET ACCURACY

Even for manual mode:

- use only exact linked Avito URL from canonical relation;
- validate hostname is `avito.ru` / subdomain;
- validate Avito ID matches linked listing;
- never construct arbitrary external URLs from user input.

---

# 13. CLEAN UP OLD AUTO-DEACTIVATION UX

Remove from seller-facing UI:

- Dry-Run;
- Armed;
- automatic deactivation progress;
- "Снимаю с публикации" automatic steps;
- automatic executor status;
- misleading messages implying the system removed the listing itself.

Use simple wording:

```text
Открыть объявление Avito для ручного снятия
```

---

# 14. VERSION

If Chrome extension source is changed only to remove obsolete auto-deactivation code/UI, bump:

```text
0.2.60 -> 0.2.61
```

If extension source does not need changes because manual flow is handled entirely by web UI:
- do not bump unnecessarily.

Report the decision.

---

# 15. TESTS

Add/update tests:

## Post-sale
- active linked listing -> large manual prompt;
- `Снять с Avito вручную` returns/opens exact canonical URL;
- `Не снимать` does not mutate listing;
- sale remains completed in both cases.

## Sale detail
- permanent manual button exists;
- old sale supported;
- exact URL used;
- multiple listings handled;
- no linked listing message;
- inactive listing message.

## Queue
- manual_required/pending displayed honestly;
- open listing action works;
- no automatic success on open.

## Safety
- invalid external domain rejected;
- mismatched Avito ID rejected;
- no auto DOM click executor in normal flow.

## Regression
- Avito import/pairing still work;
- sales/stock unaffected.

Required:

```text
FAILED = 0
```

---

# 16. LOCAL MANUAL OWNER TEST

Required final LOCAL check:

1. Complete/open a sale with linked active Avito listing.
2. Verify large post-sale prompt appears.
3. Press:
   ```text
   Снять с Avito вручную
   ```
4. Exact linked Avito listing opens.
5. Verify TechnoReboot does NOT attempt any automatic click.
6. Manually remove listing on Avito.
7. Return to TechnoReboot.
8. Verify sale remains valid.
9. Verify permanent manual button remains available in sale detail.
10. Test `Не снимать` on another eligible/manual test path:
    - prompt closes;
    - no Avito page opens;
    - no status is falsely changed to success.

---

# 17. VDS SAFETY

Strictly:

```text
VDS_DEPLOYED = false
VDS_CODE_MODIFIED = false
VDS_DATA_MODIFIED = false
UPDATE_VDS_RUN = false
```

No deployment in this stage.

---

# 18. DOCUMENTATION

Update:

```text
docs/avito_post_sale_deactivation.md
docs/production_status.md
reports/stage09a_r5_local_manual_avito_deactivation_report.md
logs/2026-09-14.md
```

Canonical user rule:

```text
После продажи система предлагает открыть точное объявление Avito.
Оператор снимает его вручную.
```

---

# 19. GIT

Commit LOCAL changes.

Do not deploy VDS.

Report:

```text
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:
```

---

# 20. FINAL REPORT CONTRACT

Return:

```text
# Stage 09A-R5 LOCAL — Manual Avito Deactivation Flow

## UX
POST_SALE_LARGE_PROMPT:
MANUAL_OPEN_BUTTON:
CANCEL_BUTTON:
SALE_DETAIL_PERMANENT_BUTTON:
MULTI_ITEM_SUPPORTED:

## Behavior
EXACT_AVITO_URL_OPENED:
AUTOMATIC_AVITO_CLICKING_DISABLED:
OPENING_LINK_MARKS_SUCCESS: false
SALE_BLOCKED_BY_AVITO: false
CANCEL_MUTATES_LISTING: false

## Queue
PERSISTENT_TASK_MODEL_KEPT:
MANUAL_REQUIRED_USED:
OPTIONAL_MANUAL_CONFIRMATION_IMPLEMENTED:
FALSE_SUCCESS_BLOCKED:

## Extension
AUTO_DEACTIVATION_EXECUTOR_DISABLED:
OTHER_AVITO_EXTENSION_FEATURES_PRESERVED:
EXTENSION_CHANGED:
EXTENSION_VERSION:

## Local Proof
SALE_ID:
PRODUCT:
AVITO_ID:
MANUAL_BUTTON_CLICKED:
EXACT_LISTING_OPENED:
AUTO_CLICK_ATTEMPTED: false
CANCEL_PATH_TESTED:
SALE_STILL_COMPLETED:

## Tests
FAILED:

## VDS Safety
VDS_DEPLOYED: false
VDS_CODE_MODIFIED: false
VDS_DATA_MODIFIED: false
UPDATE_VDS_RUN: false

## Git
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:

FINAL_STATUS:
TECHNOREBOOT_STAGE09A_R5_LOCAL_MANUAL_AVITO_DEACTIVATION_READY_FOR_OWNER_ACCEPTANCE

DO_NOT_DEPLOY_TO_VDS_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- automatic Avito clicking remains in normal seller flow;
- opening the link is falsely reported as success;
- cancel mutates listing;
- exact linked Avito URL is not used;
- VDS is touched;
- tests fail.

---

# 21. STOP

After LOCAL implementation and manual browser proof:

STOP.

Wait for Owner acceptance.

Do not deploy to VDS.
