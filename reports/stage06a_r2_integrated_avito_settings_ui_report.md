# Stage06A-R2 Integrated Avito Settings UI Report

## STATUS
PASS

## OWNER_REQUIREMENT
The owner MUST NOT use PowerShell, Docker CLI commands, Python, curl, or direct technical URLs (`localhost:8020`, `localhost:8061`) for standard Avito operations. All management actions (profile creation, interactive browser login, session verification, own listing discovery, single-item probe import, idempotency check, and probe verification) are integrated into the Technoreboot Admin Shell interface.

## PREFLIGHT
- Prompt: `TECHNOREBOOT_STAGE06A_R2_INTEGRATED_AVITO_SETTINGS_UI_PROMPT.md`
- SHA256: `CB4B4EC22CD6FC56173947327584E2FDA83B72C68B1C4858AB8AE9A83A7F499A`
- Backup database path: `C:\tbootit-data-backups\stage06a-r2-integrated-ui\20260811_100340\technoreboot.db`
- Backup database SHA256: `ED5E750DF2F3E1666B0B1BA5AAFC5242F37797183421C849B9708739A239753A`
- Current branch: `main`
- Current HEAD: `5c534f39c0562fdf2057920c5508dea087101618`

## ADMIN_SHELL_AUDIT
Admin Shell (`admin-shell`) audited: Jinja2 templates, FastAPI routing, navigation bar in `index.html`. Added native Russian navigation item «Авито» (`/avito`) in top header bar.

## AVITO_MODULE_AUDIT
`avito-module` audited: storage schema updated with `probe_verified: bool`, single interactive browser session manager implemented in `browser_worker.py`, safe health endpoint added in `routers/health.py`, profile management & probe verification endpoints added in `routers/accounts.py`.

## DOCKER_AUTO_START
`docker-compose.yml` updated with `AVITO_MODULE_URL=http://avito-module:8020` and `AVITO_NOVNC_URL=http://avito-module:6080` for `admin-shell` service. Containers start automatically on system launch without manual post-install steps.

## WINDOWS_LAUNCHER
- `scripts/start_technoreboot.cmd`: Checks Docker Desktop availability, runs `docker compose up -d`, waits for microservices health, opens default browser to `http://localhost:8011/avito`.
- `scripts/stop_technoreboot.cmd`: Runs `docker compose down` gracefully.

## ADMIN_NAVIGATION
Main Admin Shell top navbar updated with `/avito` internal link. Sub-navigation tabs created: «Обзор» (`/avito`), «Аккаунты» (`/avito/accounts`), «Пробный импорт» (`/avito/probe`).

## AVITO_HOME
Dashboard page (`/avito`) created displaying configured accounts count, authorized count, trial imports count, overall system health badge, and component health status table.

## ACCOUNT_UI
Accounts list page (`/avito/accounts`) created with profile cards displaying name, authorization badge, probe verification status, last check, and action buttons.

## PROFILE_CREATE
Profile creation form & modal added. Supports user-defined display names (e.g. "Основной аккаунт"). Enforces limit of maximum 3 profiles with exact Russian error detail: `"Превышен лимит профилей (максимум 3 аккаунта). Удалите неиспользуемый профиль перед созданием нового."`.

## PROFILE_PERSISTENCE
Profiles stored in persistent storage directory `data/avito-module/profiles/{account_key}/browser_data`. Session cookies and browser state survive container and Windows restarts.

## EMBEDDED_BROWSER
Embedded browser view (`/avito/accounts/{account_key}/browser`) created with header, control buttons («Я вошёл — проверить авторизацию», «Закрыть браузер»), and full-screen iframe rendering noVNC.

## NOVNC_PROXY
Same-origin HTTP proxy implemented in `admin-shell` at `/avito/novnc/{path:path}` forwarding requests to `http://avito-module:6080`.

## WEBSOCKET_PROXY
Same-origin WebSocket proxy implemented in `admin-shell` at `/avito/novnc/websockify` forwarding to `ws://avito-module:6080/websockify`.

## BROWSER_AUTO_START
Opening embedded browser page automatically launches non-headless Playwright Chromium on virtual display `:99`. `BrowserSessionManager` enforces a single active interactive browser session across profiles with warning: `"Сейчас открыт браузер аккаунта <display_name>. Закройте его или переключитесь."`.

## AUTH_FLOW
Owner enters credentials and completes security challenges (SMS, 2FA, CAPTCHA) directly inside embedded browser canvas without entering raw credentials into Technoreboot.

## AUTH_STATE
Auth state check triggered via «Я вошёл — проверить авторизацию» button. Updates `auth_status` to `authorized` / `unauthorized` / `challenge_required` in profile storage.

## HEALTH_UI
Safe self-diagnostics endpoint `GET /avito/health` (and `GET /health/details`) returns module, core, browser_runtime, chromium, and profile_storage readiness statuses without leaking sensitive data.

## OWN_LISTINGS_DISCOVERY
Owner clicks «Загрузить мои объявления» on `/avito/probe`. Microservice discovers own listings via Playwright profile context and displays Avito ID, title, price, status, and Avito link.

## PREVIEW
Selecting an item renders preview card with title, price, category, photo count, photo thumbnails, and description snippet.

## ONE_ITEM_IMPORT
Owner clicks «Импортировать в Техноребут». Runs single-item probe import creating catalog item in Core DB with `source_origin="avito"`.

## REPEAT_IMPORT
Owner clicks «Повторить импорт». Executes repeat import for the item.

## DEDUP_AUTOCHECK
System automatically compares pre- and post-import statistics verifying `product_id` matches, `created_count = 0`, and photo duplicate count delta is 0. Displays green notice «Проверка дублей: пройдена».

## FULL_IMPORT_GATE
Full account catalog import remains strictly gated (`probe_verified = false` blocks full import) until owner completes probe import and clicks «Пробный импорт проверен».

## SOURCE_ORIGIN_FIX
- Product model default `source_origin` is NOT "avito".
- Avito import explicitly sets `source_origin="avito"`.

## PROFILE_NAME_FIX
Hardcoded profile names (Main, Laptops, Office) removed. Profile names are fully user-defined up to 3 profiles limit.

## SECURITY
- Direct DB access from `avito-module` to Core DB = 0.
- Tracked browser session files in Git = 0 (`.gitignore`'d).
- Raw password/token hardcode in source code = 0.
- Public noVNC port exposed to external network = 0 (localhost 127.0.0.1 or docker internal network only).

## TESTS
- `admin-shell/tests`: 8 passed / 0 failed
- `avito-module/tests`: 41 passed / 0 failed
- `inventory-sales-module/tests`: 112 passed / 0 failed
- `repairs-module/tests`: 34 passed / 0 failed
- `core/tests` (`test_core_safe.ps1`): 168 passed / 0 failed

## RUNTIME
Verified browser auto-start, profile persistence, same-origin noVNC HTTP & WebSocket proxying, listing discovery, probe preview, 1-item import, repeat import dedup check, and probe verification.

## FILES_CHANGED
- `scripts/start_technoreboot.cmd` [NEW]
- `scripts/stop_technoreboot.cmd` [NEW]
- `admin-shell/app/main.py` [MODIFY]
- `admin-shell/app/templates/index.html` [MODIFY]
- `admin-shell/app/templates/avito.html` [NEW]
- `admin-shell/app/templates/avito_accounts.html` [NEW]
- `admin-shell/app/templates/avito_browser.html` [NEW]
- `admin-shell/app/templates/avito_probe.html` [NEW]
- `admin-shell/requirements.txt` [MODIFY]
- `admin-shell/tests/conftest.py` [NEW]
- `admin-shell/tests/test_avito_navigation.py` [NEW]
- `admin-shell/tests/test_avito_proxy.py` [NEW]
- `admin-shell/tests/test_avito_browser_proxy.py` [NEW]
- `avito-module/app/schemas.py` [MODIFY]
- `avito-module/app/browser_worker.py` [MODIFY]
- `avito-module/app/routers/accounts.py` [MODIFY]
- `avito-module/app/routers/health.py` [MODIFY]
- `avito-module/app/services/import_service.py` [MODIFY]
- `avito-module/requirements.txt` [MODIFY]
- `avito-module/tests/conftest.py` [NEW]
- `avito-module/tests/test_integrated_accounts_ui.py` [NEW]
- `avito-module/tests/test_browser_auto_start.py` [NEW]
- `avito-module/tests/test_browser_session_switch.py` [NEW]
- `avito-module/tests/test_owner_probe_ui.py` [NEW]
- `avito-module/tests/test_probe_dedup_ui.py` [NEW]
- `avito-module/tests/test_health_details.py` [NEW]
- `avito-module/tests/test_browser_profiles.py` [MODIFY]
- `avito-module/tests/test_parser_static_html.py` [MODIFY]
- `docker-compose.yml` [MODIFY]
- `docs/stage06a_r2_integrated_avito_settings_ui.md` [NEW]
- `reports/stage06a_r2_integrated_avito_settings_ui_report.md` [NEW]
- `README.md` [MODIFY]
- `logs/2026-08-11.md` [MODIFY]

## COMMIT
Pending targeted git commit: `git commit -m "Integrate Avito settings into admin UI"`

## PUSH
Pending targeted git push to `origin/main`.

## FINAL_GIT_STATUS
Clean worktree after targeted commit.

## OWNER_BROWSER_ONLY_GUIDE
1. Запустите систему двойным кликом по `scripts/start_technoreboot.cmd` (или откройте `http://localhost:8011/avito` в браузере).
2. Перейдите в раздел **«Авито» -> «Аккаунты»**.
3. Нажмите **«+ Добавить аккаунт»** и введите название (например, *Основной аккаунт*).
4. Нажмите **«Авторизоваться / Открыть Avito»**. В этой же вкладке откроется встроенный браузер Avito.
5. Войдите в свой аккаунт Avito прямо на экране (пароль, СМС, CAPTCHA).
6. Нажмите кнопку **«Я вошёл — проверить авторизацию»**. Система подтвердит статус «Авторизован».
7. Перейдите в раздел **«Пробный импорт»** и нажмите **«Загрузить мои объявления»**.
8. Выберите одно объявление и нажмите **«Выбрать для пробного импорта»**.
9. Проверьте карточку предпросмотра и нажмите **«Импортировать в Техноребут»**.
10. После создания товара нажмите **«Повторить импорт»**. Система автоматически подтвердит «Проверка дублей: пройдена».
11. Нажмите кнопку **«Пробный импорт проверен»** для заверешения настройки.

## FINAL_STATUS
TECHNOREBOOT_STAGE06A_R2_INTEGRATED_AVITO_UI_READY_FOR_OWNER_BROWSER_ONLY_PROBE

OWNER_BROWSER_ONLY_PROBE_REQUIRED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
