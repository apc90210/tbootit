# Stage06A-R3 Unified Admin Navigation + Mandatory Manual Avito Login Documentation

## 1. Overview
Stage06A-R3 addresses and resolves all 5 blockers identified during owner UI testing of Stage06A-R2:
1. **Unified Navigation**: Top menu (`Панель управления`, `Товары`, `Продажи`, `Отчёты`, `Ремонты`, `Авито`) remains visible on all owner-facing sections and stays on same-origin `http://localhost:8011`.
2. **Same-Origin Reverse Proxy**: All microservices (`inventory-sales-module`, `repairs-module`, `avito-module`) are proxied under `http://localhost:8011` using path prefixes (`/inventory`, `/repairs`, `/avito`).
3. **Avito Entry UX**: Clear "Настройки Avito" section with 5-step stepper for profile setup and prominent "+ Добавить аккаунт" and "🔑 Авторизоваться в Avito" CTAs.
4. **Mandatory Manual Auth**: Requires owner to perform manual login in embedded Chromium (noVNC) for each account. Headless/automated login attempts are strictly prohibited.
5. **Single Persistent Profile**: The same Chromium `user-data-dir` profile used during manual login is preserved and reused for discovery and parsing of "My Listings".

## 2. Same-Origin URL Routing Table
| Owner Path | Proxied Internal URL | Section Description |
|---|---|---|
| `/` | `http://localhost:8011` | Admin Shell Dashboard |
| `/inventory/products` | `http://inventory-sales-module:8030/products` | Products / Stock |
| `/inventory/sales` | `http://inventory-sales-module:8030/sales` | Sales Management |
| `/inventory/reports/sales` | `http://inventory-sales-module:8030/reports/sales` | Sales Reports |
| `/repairs/repairs` | `http://repairs-module:8040/repairs` | Repairs Management |
| `/avito` | `http://avito-module:8020/avito` | Avito Settings & Overview |
| `/avito/accounts` | `http://avito-module:8020/avito/accounts` | Avito Account Profiles |
| `/avito/accounts/{key}/browser` | `http://avito-module:8020/avito/accounts/{key}/browser` | Avito Embedded Login Browser |
| `/avito/probe` | `http://avito-module:8020/avito/probe` | 1-Item Trial Probe Import |

## 3. Account Setup Stepper Workflow
Each account profile follows a 5-step progress workflow:
1. **Step 1. Profile**: Account profile created in system storage.
2. **Step 2. Login**: Manual login required in embedded Chromium browser.
3. **Step 3. Confirmation**: Login status verified ("✓ Авторизован").
4. **Step 4. Listings**: "My Listings" accessible for discovery.
5. **Step 5. Trial Probe**: 1-Item trial probe import verified before full import authorization.

## 4. Verification & Testing
- 377 automated unit tests passing across all microservices.
- 0 raw owner-facing module port links in HTML templates.
- 0 direct DB access calls in `avito-module`.
- 0 tracked session / cookie files in git.
- 0 anti-bot evasion / stealth code in production repository.
