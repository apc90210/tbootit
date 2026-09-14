# TECHNOREBOOT — Stage 09A-R4 LOCAL
## Remove Dry-Run/Armed complexity and make Avito deactivation a direct real action

**Project:** ТехноРебут  
**Local workspace:** `C:\tbootit`  
**LOCAL URL:** `https://localhost:8443`  
**Production VDS:** `https://144.31.50.134`  
**Stage:** `Stage 09A-R4 LOCAL — Simple Real Avito Deactivation`

# 0. OWNER UX REQUIREMENT — CRITICAL

Owner rejects Dry-Run, Armed mode, manual arming, test-mode toggles, and technical safety switches in the normal seller workflow.

The required product behavior is simple:

```text
Open completed sale
↓
Press [ Снять с Avito ]
↓
System immediately executes REAL deactivation of the exact linked Avito listing
↓
If Avito confirms inactive:
    show SUCCESS / СНЯТО
Else:
    show the real error
```

The button itself is explicit user authorization for the destructive Avito action.

Do NOT require:
- Dry-Run;
- Armed mode;
- manual "arm task";
- global test-mode toggle;
- second technical confirmation;
- developer-only switching before every deactivation.

This stage is LOCAL ONLY.
Do NOT deploy to VDS.

---

# 1. PROMPT PRESERVATION

Copy unchanged from:

`C:\Users\Apc\Downloads\TECHNOREBOOT_STAGE09A_R4_LOCAL_REMOVE_DRYRUN_SIMPLIFY_REAL_AVITO_DEACTIVATION_PROMPT.md`

to:

`C:\tbootit\.agents\received_prompts\TECHNOREBOOT_STAGE09A_R4_LOCAL_REMOVE_DRYRUN_SIMPLIFY_REAL_AVITO_DEACTIVATION_PROMPT.md`

---

# 2. PREFLIGHT

Record:

```text
LOCAL_HEAD:
LOCAL_GIT_STATUS:
LOCAL_STACK_HEALTHY:
EXTENSION_VERSION:
CURRENT_DRY_RUN_IMPLEMENTATION:
CURRENT_ARMED_MODE_IMPLEMENTATION:
CURRENT_REAL_DEACTIVATION_PATH:
```

Verify LOCAL-only environment.

Do not touch VDS.

---

# 3. REMOVE NORMAL-WORKFLOW DRY-RUN

Remove Dry-Run from the normal product workflow.

This includes removing or disabling product-facing behavior for:

```text
avito_deactivation_dry_run
ТЕСТОВЫЙ РЕЖИМ
Dry-Run
final-click blocked because dry-run
```

The seller must not have to understand or toggle this.

If a low-level internal developer safeguard is retained in code for automated tests, it must:
- not appear in normal UI;
- not block normal real deactivation;
- not require manual switching;
- not affect seller workflow.

Preferred: delete obsolete runtime Dry-Run path if no longer needed.

---

# 4. REMOVE ARMED MODE

Remove normal-workflow Armed mode introduced in Stage09A-R3.

Remove/retire:

```text
arm-task/{avito_listing_id}
disarm
armed-status
armed_listing_id
approved_for_real_execution
ВООРУЖЁН
Вооружить
```

unless an internal compatibility shim is temporarily required.

Normal task authorization is now:

```text
valid authenticated seller/owner
+
explicit click [ Снять с Avito ]
+
exact linked sale/product/listing identity
```

That is sufficient authorization.

Do not leave confusing dead controls in popup/UI.

---

# 5. SIMPLE SALE DETAIL UX

On every completed sale detail page keep a permanent button:

```text
[ Снять с Avito ]
```

Behavior:

## Active linked listing

Pressing button:

```text
queue/reuse task
-> extension receives task
-> immediately performs real deactivation
-> UI waits/polls for result
-> show "Снято с Avito" on success
```

## Already inactive / archived / success

Show:

```text
Объявление уже снято с Avito
```

Do not create duplicate task.

## No linked Avito listing

Show:

```text
Для этой продажи нет связанного объявления Avito
```

## Failure

Show concrete failure:

```text
Не удалось снять с Avito:
<real error>
```

and keep Retry available.

---

# 6. TASK MODEL

Preserve persistent task model and idempotency.

States remain:

```text
suggested
queued
processing
success
failed
manual_required
canceled
```

But do not expose technical complexity unnecessarily.

For explicit seller click:

```text
suggested/manual_required/failed
-> queued
```

Extension executes real action immediately.

No separate arm state.

---

# 7. EXTENSION EXECUTION

Required direct path:

```text
task.action = deactivate_listing
↓
open/focus exact canonical Avito URL
↓
verify exact listing ID
↓
reach management context
↓
find exact "Снять с публикации" / equivalent
↓
click it
↓
handle confirmation/reason
↓
wait for confirmed inactive state
↓
report success
```

This is always the normal path after user clicks `[ Снять с Avito ]`.

No dry-run branch.

---

# 8. SAFETY THAT MUST REMAIN

Removing Dry-Run does NOT mean removing identity/safety validation.

Keep:

- exact Avito hostname validation;
- exact Avito listing ID validation;
- exact canonical URL relation;
- one task at a time;
- no approximate title matching;
- no unrelated listing action;
- no payment/promotion actions;
- no publication/republish actions;
- no generic click-by-coordinate;
- no success without external inactive confirmation;
- unknown/ambiguous DOM => fail honestly;
- retries bounded;
- sale/stock unaffected by Avito failure.

The safety mechanism is exact targeting, not a test-mode toggle.

---

# 9. ERROR UX

If execution fails:

Store and display useful errors, e.g.:

```text
Кнопка снятия не найдена
Не совпал Avito ID
Страница управления не открылась
Avito запросил неизвестный тип подтверждения
Не удалось подтвердить, что объявление снято
Сессия Avito не авторизована
```

Do not show generic developer errors if a clearer seller-facing message can be produced.

Keep technical details in logs/result_metadata.

---

# 10. RETRY

On sale detail and post-sale queue:

```text
[ Повторить снятие ]
```

must simply requeue the same idempotent task and attempt the real action again.

No arming, no dry-run toggles.

---

# 11. EXTENSION POPUP SIMPLIFICATION

Simplify extension popup.

Remove:
- Dry-Run badge;
- Armed badge;
- arm button;
- disarm button;
- test-mode instructions.

Keep useful status only:

```text
Подключено к ТехноРебут
Текущая задача:
Avito №...
Статус:
- Получена
- Открываю объявление
- Проверяю ID
- Снимаю с публикации
- Подтверждаю результат
- Снято
```

On error:

```text
Ошибка: ...
```

---

# 12. API CLEANUP

Audit whether these Stage09A-R3 endpoints are still needed:

```text
POST /admin-api/avito-extension/arm-task/{id}
POST /admin-api/avito-extension/disarm
GET  /admin-api/avito-extension/armed-status
```

Preferred:
- remove them if only used for test-mode arming;
- remove related storage files/state;
- update tests/docs.

If compatibility requires temporary retention, mark deprecated and ensure they are not used by normal workflow.

---

# 13. VERSION

Because extension behavior/UI changes materially:

```text
0.2.59 -> 0.2.60
```

Update all version references.

Rebuild:

```text
dist/technoreboot-avito-extension-0.2.60.zip
admin-shell/app/technoreboot-avito-extension.zip
```

---

# 14. REAL LOCAL E2E — MANDATORY

Use a real active Avito listing linked to a LOCAL sale.

Owner explicitly allows real deactivation and can reactivate manually later.

Required proof:

```text
open sale
press [ Снять с Avito ]
extension auto-fetches
exact listing opens
exact ID verified
real final click performed
Avito confirms inactive
task becomes success
listing becomes archived/inactive locally
```

No Dry-Run.
No Armed mode.

If the previously used listing `7353766377` has already been reactivated and is active, it may be reused.

If it is not active, use another explicitly linked active LOCAL Avito listing/sale without touching VDS.

---

# 15. FAILURE CASE PROOF

Also prove one controlled failure path without destructive side effects, for example:
- invalid/mismatched ID fixture;
- mocked unknown DOM;
- unauthorized session fixture.

Required:

```text
failure -> honest failed/manual_required
sale remains completed
stock unchanged
no false success
```

---

# 16. SALE DETAIL PAGE RESULT

After success:

```text
[ Снять с Avito ]
```

may remain visible, but page must clearly show:

```text
Снято с Avito
```

Repeated click must not create duplicate task or trigger unrelated action.

---

# 17. POST-SALE QUEUE

`/avito/post-sale` must remain useful:

- success rows show `Снято`;
- failed/manual rows show error + `Повторить`;
- no Dry-Run/Armed columns or controls.

---

# 18. TESTS

Update/add tests:

## UX
- no Dry-Run text in seller UI;
- no Armed mode text/control;
- sale detail button permanent;
- already removed message;
- failure message;
- retry action.

## Extension
- no runtime Dry-Run gating for normal task;
- no arm requirement;
- exact ID validation retained;
- real execute path called after valid task;
- unknown action rejected;
- ambiguous control fails safely.

## API
- normal execution works without arm endpoint;
- obsolete arm endpoints removed/deprecated as designed.

## Integrity
- no duplicate tasks;
- no sale mutation;
- no stock mutation;
- success only after external confirmation.

Required:

```text
FAILED = 0
```

Run full targeted regression suite.

---

# 19. VDS SAFETY

Strictly:

```text
VDS_DEPLOYED = false
VDS_CODE_MODIFIED = false
VDS_DATA_MODIFIED = false
UPDATE_VDS_RUN = false
```

No VDS deployment in this stage.

---

# 20. DOCUMENTATION

Update:

```text
docs/avito_post_sale_deactivation.md
docs/production_status.md
reports/stage09a_r4_local_simple_real_avito_deactivation_report.md
logs/2026-09-14.md
```

Documentation must describe the simple product rule:

```text
Нажал "Снять с Avito" -> система реально снимает объявление.
```

No Dry-Run workflow in user documentation.

---

# 21. GIT

Commit LOCAL changes.

Do not deploy.

Report:

```text
COMMIT:
PUSH:
HEAD_AFTER:
FINAL_GIT_STATUS:
```

---

# 22. FINAL REPORT CONTRACT

Return:

```text
# Stage 09A-R4 LOCAL — Simple Real Avito Deactivation

## UX
SALE_DETAIL_BUTTON_ALWAYS_VISIBLE:
BUTTON_PERFORMS_REAL_ACTION_IMMEDIATELY:
DRY_RUN_USER_MODE_REMOVED:
ARMED_USER_MODE_REMOVED:
SECOND_TECHNICAL_CONFIRMATION_REQUIRED: false
RETRY_SIMPLE:

## Extension
VERSION: 0.2.60
REAL_EXECUTION_DEFAULT:
EXACT_ID_VALIDATION:
EXACT_URL_VALIDATION:
PAYMENT_PUBLISH_ACTIONS_BLOCKED:
SUCCESS_REQUIRES_EXTERNAL_CONFIRMATION:

## API Cleanup
ARM_ENDPOINT_REMOVED_OR_DEPRECATED:
DISARM_ENDPOINT_REMOVED_OR_DEPRECATED:
ARMED_STATUS_REMOVED_OR_DEPRECATED:
OBSOLETE_ARM_STORAGE_REMOVED:

## Real Local E2E
SALE_ID:
PRODUCT:
AVITO_ID:
BUTTON_CLICKED:
TASK_FETCHED:
EXACT_LISTING_OPENED:
EXACT_ID_VERIFIED:
FINAL_DEACTIVATION_CLICK_PERFORMED:
REAL_EXTERNAL_INACTIVE_CONFIRMED:
TASK_STATUS_AFTER:
LISTING_STATUS_AFTER:
FALSE_SUCCESS: false

## Failure Path
CONTROLLED_FAILURE_TESTED:
ERROR_SHOWN_HONESTLY:
SALE_CHANGED: false
STOCK_CHANGED: false

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
TECHNOREBOOT_STAGE09A_R4_LOCAL_SIMPLE_REAL_AVITO_DEACTIVATION_READY_FOR_OWNER_ACCEPTANCE

DO_NOT_DEPLOY_TO_VDS_WITHOUT_OWNER_ACCEPTANCE: true
```

Return BLOCKED if:
- normal seller flow still requires Dry-Run/Armed toggle;
- button does not perform real action;
- success occurs without external inactive confirmation;
- wrong listing can be targeted;
- VDS is touched;
- tests fail.

---

# 23. STOP

After implementation and real LOCAL end-to-end proof:

STOP.

Wait for Owner acceptance.

Do not deploy to VDS.
