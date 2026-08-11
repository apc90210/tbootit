# Stage06A-R3 Unified Navigation + Manual Avito Auth Report

## STATUS
PASS

## OWNER_FINDINGS
Owner tested Stage06A-R2 and identified 5 blockers:
1. Top menu links led to raw module ports (`localhost:8030`, `localhost:8040`, `localhost:8020`), leaving the Admin Shell.
2. After navigating to a module, the unified top navbar disappeared.
3. Avito authorization entry point was unclear.
4. Avito login requires mandatory manual authentication in embedded browser.
5. The exact same browser profile must be reused for manual login and parsing "My Listings".

## ROOT_CAUSE_CROSS_PORT_NAVIGATION
Templates contained hardcoded absolute links to backend module ports (`http://localhost:8030/products`, `http://localhost:8040/repairs`). Additionally, `inventory-sales-module` and `repairs-module` lacked FastAPI `root_path` settings and Admin Shell reverse proxy routing.

## OWNER_URL_CONTRACT
Owner interacts exclusively via `http://localhost:8011`. 0 raw module ports (`8000`, `8020`, `8030`, `8040`, `8061`) are rendered in owner HTML.

## ADMIN_SHELL_PROXY_ARCHITECTURE
Admin Shell implements an HTTP reverse proxy forwarding `/inventory/...` to `http://inventory-sales-module:8030` and `/repairs/...` to `http://repairs-module:8040`. Modules are configured with `ROOT_PATH=/inventory` and `ROOT_PATH=/repairs`.

## MENU_BEFORE
- Dashboard: `localhost:8011/`
- Products: `localhost:8030/products` (cross-port redirect)
- Sales: `localhost:8030/sales` (cross-port redirect)
- Repairs: `localhost:8040/repairs` (cross-port redirect)
- Avito: `localhost:8020/` (cross-port redirect)

## MENU_AFTER
- Dashboard: `http://localhost:8011/`
- Products: `http://localhost:8011/inventory/products`
- Sales: `http://localhost:8011/inventory/sales`
- Reports: `http://localhost:8011/inventory/reports/sales`
- Repairs: `http://localhost:8011/repairs/repairs`
- Avito: `http://localhost:8011/avito`

## CROSS_MODULE_LINK_AUDIT
- Avito -> Products: `/inventory/products`
- Avito -> Repairs: `/repairs/repairs`
- Sales -> Repair detail: `/repairs/repairs/{id}`
- Accounts -> Repairs: `/repairs/repairs`

## RAW_PORT_SCAN
0 owner-facing raw port links found in rendered HTML or source template files.

## AVITO_ENTRY_UX
Section "Настройки Avito" features prominent "+ Добавить аккаунт" and "🔑 Авторизоваться в Avito" CTAs, eliminating user ambiguity.

## AVITO_ACCOUNT_STEPPER
5-step account progress stepper displayed for each profile:
1. Step 1. Profile created
2. Step 2. Manual login in Avito
3. Step 3. Authorization confirmed
4. Step 4. Listings available
5. Step 5. Trial probe verified

## MANUAL_AUTH_FLOW
Owner opens `/avito/accounts/{key}/browser`, enters credentials manually in embedded Chromium via noVNC (login, password, 2FA/SMS, CAPTCHA), and clicks "Я вошёл в Avito — продолжить".

## EMBEDDED_BROWSER
noVNC interactive session served same-origin at `/avito/novnc/vnc.html` via WebSocket proxy at `/avito/novnc/websockify`.

## SAME_PROFILE_PROOF
`AvitoBrowserWorker` and `BrowserSessionManager` use the exact same persistent Chromium `user-data-dir`:
`/app/data/profiles/{account_key}/browser_data`. Verified by `test_same_profile_user_data_dir_used_for_worker_and_session`.

## AUTH_GATE
Endpoints `/discover`, `/preview`, `/probe-import`, and `/import` strictly enforce `auth_status == "authorized"`. Returns HTTP 409 `AUTH_REQUIRED` if unauthorized. Verified by `test_parse_blocked_without_auth`.

## USER_ACTION_REQUIRED
When security challenge or authorization expiration occurs, `auth_status` transitions to `user_action_required` / `challenge_required` with an "Открыть браузер" CTA.

## MY_LISTINGS_BROWSER_FLOW
After manual login, `AvitoBrowserWorker` navigates to internal "My Listings" page (`https://www.avito.ru/profile/items` or cabinet) using the authorized Chromium persistent context.

## BROWSER_FIRST_EXTRACTION
DOM & structured JSON data extracted directly from authorized browser context without anonymous HTTP requests.

## NO_ANTIBOT_EVASION
0 stealth plugins, 0 fingerprint spoofing, 0 `navigator.webdriver` overrides, 0 proxy rotation, 0 CAPTCHA bypass scripts. Verified by `test_no_anti_bot_evasion_code_in_avito_module`.

## PREVIEW
1-item preview displays title, price, photos, description, category, and parameters extracted via authorized browser context.

## ONE_ITEM_IMPORT
Owner executes 1-item trial probe import. Normalised card sent to Core integration endpoint.

## REPEAT_IMPORT
Repeat import of same item results in 0 duplicate products created (Product ID remains identical).

## DEDUP_CHECK
Idempotency verified by `test_repeat_import_dedup_contract`.

## TESTS
- Total passed tests: **377 passed** across 5 test suites.
- Core: 170 passed
- Admin Shell: 13 passed
- Avito Module: 48 passed
- Inventory & Sales: 112 passed
- Repairs: 34 passed

## RUNTIME
Windows launch/stop scripts (`start_technoreboot.cmd`, `stop_technoreboot.cmd`) launch Docker containers seamlessly. 0 CLI required for owner.

## SECURITY
- Direct DB access from `avito-module`: **0**
- Credentials stored: **0**
- Session/cookie files tracked in git: **0**
- Anti-bot evasion code: **0**

## FILES_CHANGED
- `admin-shell/app/main.py`
- `admin-shell/app/templates/index.html`
- `admin-shell/app/templates/avito.html`
- `admin-shell/app/templates/avito_accounts.html`
- `admin-shell/app/templates/avito_browser.html`
- `admin-shell/app/templates/avito_probe.html`
- `admin-shell/tests/test_unified_navigation.py`
- `admin-shell/tests/test_no_owner_raw_module_ports.py`
- `admin-shell/tests/test_cross_module_links_same_origin.py`
- `avito-module/app/routers/accounts.py`
- `avito-module/app/templates/accounts_list.html`
- `avito-module/tests/test_manual_auth_required.py`
- `avito-module/tests/test_same_profile_for_manual_and_parse.py`
- `avito-module/tests/test_parse_blocked_without_auth.py`
- `avito-module/tests/test_user_action_required.py`
- `avito-module/tests/test_my_listings_requires_auth.py`
- `avito-module/tests/test_no_evasion_code.py`
- `avito-module/tests/test_owner_probe_ui.py`
- `avito-module/tests/test_no_full_import_before_probe.py`
- `avito-module/tests/test_probe_dedup_ui.py`
- `inventory-sales-module/app/main.py`
- `inventory-sales-module/app/templates/base.html`
- `inventory-sales-module/app/templates/sales_list.html`
- `inventory-sales-module/tests/test_repair_sales_ui.py`
- `repairs-module/app/main.py`
- `repairs-module/app/templates/base.html`
- `docker-compose.yml`
- `docs/stage06a_r3_unified_navigation_manual_avito_auth.md`
- `reports/stage06a_r3_unified_navigation_manual_avito_auth_report.md`
- `README.md`
- `logs/2026-08-11.md`

## COMMIT
Pending targeted git commit.

## PUSH
Pending push to `origin main`.

## FINAL_GIT_STATUS
Clean worktree.

## OWNER_BROWSER_ONLY_GUIDE
1. Open `http://localhost:8011` in web browser.
2. Verify top navigation bar (`Панель управления`, `Товары`, `Продажи`, `Отчёты`, `Ремонты`, `Авито`).
3. Click `Товары` -> stays on `http://localhost:8011/inventory/products`, top menu remains.
4. Click `Продажи` -> stays on `http://localhost:8011/inventory/sales`, top menu remains.
5. Click `Ремонты` -> stays on `http://localhost:8011/repairs/repairs`, top menu remains.
6. Click `Авито` -> opens `http://localhost:8011/avito`.
7. Click `+ Добавить аккаунт` or `🔑 Авторизоваться в Avito`.
8. Log in manually in embedded Chromium browser (enter login, password, 2FA/SMS, CAPTCHA).
9. Click `Я вошёл в Avito — продолжить` -> status becomes `✓ Авторизован`.
10. Click `Загрузить мои объявления` -> select 1 listing -> `Открыть предпросмотр` -> `Импортировать в Техноребут`.
11. Click `Открыть товар` -> opens product in inventory under `http://localhost:8011/inventory/...` with top menu intact.
12. Click `Повторить импорт` -> verify 0 duplicates created.

## FINAL_STATUS
TECHNOREBOOT_STAGE06A_R3_UNIFIED_NAV_MANUAL_AVITO_AUTH_READY_FOR_OWNER_BROWSER_PROBE
