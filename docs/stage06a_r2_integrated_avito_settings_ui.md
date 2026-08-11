# Stage06A-R2 Integrated Avito Settings UI & Zero-CLI Owner Workflow Documentation

## 1. Overview
Stage06A-R2 establishes a seamless, integrated Avito Settings and Management system directly inside the Technoreboot Admin Shell interface (`http://localhost:8011/avito`).
Owners can configure Avito account profiles, authorize accounts via an embedded Playwright browser view (powered by same-origin noVNC reverse proxying), discover own listings, run a trial 1-item probe import, verify idempotency, and grant full-account import authorization — without ever using PowerShell, Docker commands, or raw port links.

## 2. Architecture & Operational Boundary
- **Admin Shell Integration**: All operational workflows are available under the `/avito` navigation tree in Admin Shell.
- **Module Boundaries**: `avito-module` remains an isolated Docker microservice. Admin Shell communicates via HTTP API proxying to `http://avito-module:8020`.
- **Browser Runtime & noVNC**: Playwright non-headless Chromium renders to virtual display `:99` (Xvfb), streamed over `x11vnc` (port 5900) to `websockify` (port 6080).
- **Same-Origin Reverse Proxy**: Admin Shell proxies noVNC HTTP static assets (`/avito/novnc/...`) and WebSocket traffic (`/avito/novnc/websockify`) to `http://avito-module:6080`.
- **Zero Raw Ports**: Raw VNC/noVNC internal ports (`8061`, `6080`) are never exposed or presented to regular non-developer users in the UI.

## 3. Owner Workflow Step-by-Step
1. **Open System**: Owner launches Technoreboot using `scripts/start_technoreboot.cmd` (or opening `http://localhost:8011/avito`).
2. **Account Setup**: On the «Аккаунты» page (`/avito/accounts`), owner clicks «Добавить аккаунт» and enters a custom display name (e.g. "Основной аккаунт"). Up to 3 account profiles are supported.
3. **Interactive Login**: Owner clicks «Авторизоваться / Открыть Avito». The embedded browser page (`/avito/accounts/{account_key}/browser`) opens.
4. **Credential Input & Verification**: Inside the embedded browser canvas, the owner inputs credentials and completes any security challenge (SMS, 2FA, CAPTCHA) directly on Avito.
5. **Auth Check**: Owner clicks «Я вошёл — проверить авторизацию». System verifies session state and updates `auth_status` to `authorized`.
6. **Own Listings Discovery**: On the «Пробный импорт» page (`/avito/probe`), owner selects the account and clicks «Загрузить мои объявления».
7. **Item Preview & Probe Import**: Owner selects an item, inspects item details and photos, and clicks «Импортировать в Техноребут».
8. **Idempotency Verification**: Owner clicks «Повторить импорт». The system automatically runs an owner-check diagnostic verifying that `product_id` is unchanged, `created_count = 0`, and no photo duplicates were created.
9. **Probe Verification Approval**: Owner clicks «Пробный импорт проверен». This records `probe_verified = true` for the profile and unlocks full-account import gating.

## 4. Windows Launcher Scripts
- `scripts/start_technoreboot.cmd`: Checks Docker Desktop availability, starts containers with `docker compose up -d`, waits for readiness, and opens default browser to `http://localhost:8011/avito`.
- `scripts/stop_technoreboot.cmd`: Gracefully stops container services via `docker compose down`.

## 5. Security & Isolation Controls
- No passwords, SMS codes, or 2FA tokens are stored in Technoreboot DB or source control.
- Persistent browser profiles are stored in `.gitignore`'d directory `data/avito-module/profiles/{account_key}/browser_data`.
- Direct database access from `avito-module` to `core` DB remains 0.
- Full account catalog import remains strictly gated until probe verification is completed.
