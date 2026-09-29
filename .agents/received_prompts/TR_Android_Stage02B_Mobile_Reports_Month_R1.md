# TR_Android_Stage02B_Mobile_Reports_Month_R1.md

## PROJECT

`C:\tbootit`

Current accepted HEAD:

`7012b3bbb3a2c7193e07a0ce947cb5d52aa7b5b3`

Production VDS:

`144.31.15.88`

Stage02A is ACCEPTED.

Confirmed on physical Samsung Galaxy S22 Ultra:

- foreground/background update download PASS;
- screen-off download PASS;
- interrupted download resume with HTTP Range/206 PASS;
- fresh TRMOBILE1 auth on resumed request PASS;
- SHA-256 PASS;
- signer verification PASS;
- physical v3 -> v4 update PASS;
- session preservation PASS;
- reports after update PASS.

Production MUST NOT be modified in this stage.

## GOAL

Add the missing required mobile sales-report period:

`Месяц`

The mobile report selector must become:

`Сегодня | Неделя | Месяц | Год`

Do NOT remove `Год`.

Mandatory primary periods are:
- Сегодня
- Неделя
- Месяц

`Год` remains as the fourth existing period.

## 0. PREFLIGHT

Run:

`git status`

`git log -n 5 --oneline`

Confirm HEAD contains:

`7012b3bbb3a2c7193e07a0ce947cb5d52aa7b5b3`

Forbidden:
- `git add .`
- `git add -A`
- `git reset --hard`
- `git clean`

Production/VDS untouched.

## 1. CANONICAL REPORT SEMANTICS

Add canonical period:

`month`

Definition:
- start = first calendar day of the CURRENT month;
- end = current date/time boundary using the SAME timezone/date semantics already used by current reports;
- only sales inside current calendar month;
- canceled sales excluded exactly as in current Today/Week/Year logic;
- totals, sales_count, payment breakdown and `sales[]` must all use the same filtered set.

Do not implement "last 30 days".

Example:

If today is `2026-09-28`:
- month start: `2026-09-01`
- month end: `2026-09-28`

## 2. CORE AS SOURCE OF TRUTH

Extend the canonical Core sales report implementation.

Expected API:

`GET /api/reports/sales?period=month`

Core remains the only owner of report business calculations.

Do NOT duplicate sales SQL/business calculations in admin-shell.

admin-shell must continue to call Core through the existing HTTP service boundary.

## 3. MOBILE API

Existing:

`GET /api/mobile/reports/sales?period=...`

Extend allowed periods to:
- `today`
- `week`
- `month`
- `year`

Keep:
- TRMOBILE1 authentication;
- parent/device revoke behavior;
- server-side `x-api-token` for admin-shell -> Core;
- controlled upstream failures;
- existing response schema.

No auth redesign.

## 4. ANDROID MODEL

Extend report-period model with:

`MONTH`

Display label:

`Месяц`

Wire value:

`month`

Do not rename existing wire values.

## 5. ANDROID UI

Report selector must show four choices:

`Сегодня`
`Неделя`
`Месяц`
`Год`

Requirements:
- all fit cleanly on typical phone width;
- selected state remains visually clear;
- no clipping;
- no horizontal UI breakage;
- existing loading/error/empty states preserved.

If four equal-width tabs/buttons are too cramped, use an adaptive implementation while keeping all four immediately accessible.

## 6. MONTH BOUNDARY TESTS

Add deterministic tests.

At minimum test:

Current date fixture:
`2026-09-28`

Sales:
- `2026-09-01` -> INCLUDED
- `2026-09-15` -> INCLUDED
- `2026-09-28` -> INCLUDED
- `2026-08-31` -> EXCLUDED

Year boundary fixture:

Current date:
`2026-01-05`

- `2026-01-01` -> INCLUDED
- `2025-12-31` -> EXCLUDED

## 7. CONSISTENCY TESTS

For `month`, prove:
- `sales_count == len(sales[])`;
- `revenue_total == sum(sales amounts)`;
- payment-method totals equal sales set;
- canceled sales excluded from list and totals;
- date_from/date_to correct;
- label = `Месяц`;
- currency preserved.

## 8. MOBILE AUTH TESTS

For `period=month` verify:
- active USER -> PASS;
- active OWNER -> PASS;
- revoked device -> DENY;
- revoked parent -> DENY;
- tampered query (`month` changed after signing) -> DENY;
- invalid period -> controlled 4xx.

Do not weaken TRMOBILE1.

## 9. ANDROID UNIT TESTS

Add/extend tests for:
- parsing `month`;
- Month label;
- selecting Month;
- Month API request path/query;
- four-period state handling;
- existing Today/Week/Year unchanged.

Keep all current update/resume tests.

Run:

`.\gradlew.bat testDebugUnitTest`

Must PASS.

## 10. SERVER TESTS

Run focused mobile-report tests including new Month cases.

Then full relevant server regression:
- Stage01A
- Stage01B
- Stage01C
- Stage01D
- Stage02A
- Stage02B

No production DB mutation.

## 11. BUILD / LINT

Run:

`.\gradlew.bat assembleDebug`

`.\gradlew.bat lintDebug`

Requirements:
- BUILD SUCCESSFUL;
- lint 0 errors;
- 0 security-critical warnings.

## 12. PHYSICAL DEVICE CHECK

Use connected Samsung Galaxy S22 Ultra.

Install/update LOCAL debug build through the now-accepted in-app update mechanism if practical.

Verify on real phone:
- Today opens;
- Week opens;
- Month opens;
- Year opens;
- Month displays correct current-month data;
- switching between all four works;
- no clipping/layout defect;
- session preserved.

This is intentionally the first normal functional feature delivered after proving resumable updates.

## 13. DB INTEGRITY

Run local:
- `PRAGMA foreign_key_check`
- `PRAGMA quick_check`

Must PASS.

## 14. COMMIT

If PASS:

explicitly stage only accepted Stage02B files.

Commit:

`feat: add monthly Android sales report`

Do not commit:
- APKs;
- screenshots;
- signing keys;
- temporary test files;
- `.part`;
- local.properties.

## ACCEPTANCE

Stage02B PASS only if:
1. Core supports `period=month`;
2. month means current calendar month, not last 30 days;
3. mobile API supports month;
4. Today/Week/Month/Year all work;
5. Year remains available;
6. Month boundaries proven by tests;
7. totals/list/payment breakdown consistent;
8. canceled sales excluded;
9. TRMOBILE1 behavior unchanged;
10. Android UI clean with four periods;
11. Android tests PASS;
12. server regression PASS;
13. assembleDebug PASS;
14. lint PASS;
15. physical phone check PASS;
16. DB integrity PASS;
17. production untouched.

## FINAL REPORT

Return:

1. FINAL_STATUS
2. Current HEAD
3. Core month implementation location
4. Month date semantics
5. Core month test result
6. Mobile API month result
7. USER auth result
8. OWNER auth result
9. Revoked device result
10. Revoked parent result
11. Tampered month-query result
12. Android four-period UI result
13. Today result
14. Week result
15. Month result
16. Year result
17. Month boundary tests
18. Month totals consistency
19. Android/JUnit total
20. Server test total
21. assembleDebug
22. lintDebug
23. Physical Samsung result
24. Session preservation
25. DB foreign_key_check
26. DB quick_check
27. Files changed
28. Commit hash if PASS
29. git status
30. Production/VDS touched — MUST be NO
31. Stage02B accepted YES/NO
32. Ready for combined production rollout of resumable updater + Month report YES/NO

После отчёта остановиться.
