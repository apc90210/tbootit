# Stage 06D: Production Rollout — Mobile Inventory Catalog & Sales Reports Drill-Down

- **Date:** 2026-10-09
- **Stage:** Stage 06D — Controlled Production Rollout
- **Status:** **DEPLOYED_AWAITING_OWNER_ACCEPTANCE**
- **Target Host:** Production VDS (`144.31.15.88`)
- **Deployed Commit:** `58439fb04bb5ca1f5d606ebbf4f3aa348f946d49` (Branch: `release/stage06d-catalog-reports`)
- **Baseline Commit Prior to Deploy:** `5ce792ce35f63cd8e3b78fa65e8e748e454cb33c`
- **Scope Included:** Stage06A (Mobile Inventory Catalog, image proxy, price sort, brand priority) + Stage06B (Mobile Sales Reports single-level drilldown Today / Week / Month / Year) + In-App OTA Update publication.

---

## 1. Executive Summary & Gates Verification

In response to the explicit `OWNER GO — Stage06D production rollout` instruction, a controlled zero-data-loss deployment was successfully executed against the production server `144.31.15.88`.

### Gate Compliance Matrix
| Gate | Назначение | Статус | Подтверждение |
|---|---|---|---|
| **Gate 0** | Baseline & Scope | **PASS** | Проверен рабочий baseline на VDS: commit `5ce792c`, package `com.technoreboot.mobile`, `versionCode=22`, `versionName="1.6.0"`. Сверен точный diff. |
| **Gate 1** | Release Signing & Build | **PASS** | Локализован production release keystore (`C:\tbootit_secrets\android\production-signing.env`). Отпечаток SHA-256 проверен: `741ffd5582e3ab46aee12a746a3aae7454fcaa79553b9702102bf3a4ec47bcd1` (100% совпадение). Собран release APK `com.technoreboot.mobile`, `versionCode=23`, `versionName="1.7.0"`, размер 33,098,662 байт, SHA-256: `5e913aac0dfd79beb0c17c618595a4002202f0700f9d2f2f47b7c00f9e646c7f`. |
| **Gate 2** | Production Backup | **PASS** | Выполнен атомарный SQLite backup на VDS: `/srv/technoreboot/data/backups/pre_stage06d_rollout_20261009_045426`. `PRAGMA quick_check=ok`, `PRAGMA foreign_key_check=[]`. Сохранены `app-release-v22.apk`, `manifest.json.predeploy`, `deployed_commit.txt`. |
| **Gate 3** | Backend Deployment | **PASS** | Код перенесен на VDS через `origin/release/stage06d-catalog-reports`. Выполнен контролируемый запуск через `update_code_only.sh`. Образы `production-core`, `production-admin-shell`, `production-repairs-module`, `production-inventory-sales-module`, `production-avito-module` пересобраны. Все 6/6 сервисов переведены в состояние Healthy. Зафиксирована неизменность бизнес-данных: `PRODUCTS=452`, `SALES=94`, `REPAIRS=2`, `MOVEMENTS=143`. |
| **Gate 4** | In-App OTA Publish | **PASS** | Релизный APK `app-release-v23.apk` загружен на VDS по пути `/srv/technoreboot/data/releases/mobile/app-release-v23.apk` (размер 33,098,662 байт, SHA-256 проверен на диске). `manifest.json` обновлен на версию 23 (v1.7.0). Предыдущий манифест сохранен как `manifest.json.v22.bak`. Проверена защита PoP (401 без ключа). |
| **Gate 5** | Physical Acceptance | **PENDING** | В соответствии с регламентом, статус зафиксирован как `DEPLOYED_AWAITING_OWNER_ACCEPTANCE`. Требуется физическая установка обновления владельцем на Samsung Galaxy S22 Ultra через системный интерфейс «Настройки → Проверить обновления». |

---

## 2. Release Artifacts & Parameters

### 2.1. Опубликованный Production APK
- **Application ID:** `com.technoreboot.mobile`
- **Version Code:** `23`
- **Version Name:** `1.7.0`
- **Файл на VDS:** `/srv/technoreboot/data/releases/mobile/app-release-v23.apk`
- **Размер файла:** `33,098,662` байт
- **SHA-256 хеш:** `5e913aac0dfd79beb0c17c618595a4002202f0700f9d2f2f47b7c00f9e646c7f`
- **Отпечаток сертификата подписи (SHA-256):** `741ffd5582e3ab46aee12a746a3aae7454fcaa79553b9702102bf3a4ec47bcd1`
- **Имя субъекта сертификата:** `CN=Technoreboot Production, O=Technoreboot, C=RU`

### 2.2. Опубликованный Манифест (`/srv/technoreboot/data/releases/mobile/manifest.json`)
```json
{
  "application_id": "com.technoreboot.mobile",
  "version_code": 23,
  "version_name": "1.7.0",
  "min_sdk": 26,
  "apk_filename": "app-release-v23.apk",
  "apk_size": 33098662,
  "sha256": "5e913aac0dfd79beb0c17c618595a4002202f0700f9d2f2f47b7c00f9e646c7f",
  "signing_cert_sha256": "741ffd5582e3ab46aee12a746a3aae7454fcaa79553b9702102bf3a4ec47bcd1",
  "release_notes": "Техноребут 1.7.0: Каталог товаров инвентаря с сортировкой цен и иерархические отчёты о продажах с drill-down",
  "mandatory": false
}
```

---

## 3. Проверка целостности базы данных и инвариантов

Вся раскатка выполнена строго без мутации продакшн-данных:
- **Локальная база данных НЕ переносилась.**
- **Искусственные продажи (#67–#73) и фикстуры LOCAL НЕ переносились.**
- **Синтетические тестовые продажи на проде НЕ создавались.**
- **Сверка счетчиков сущностей до и после деплоя:**
  - `products`: **452** (до: 452, после: 452)
  - `sales`: **94** (до: 94, после: 94)
  - `repair_orders`: **2** (до: 2, после: 2)
  - `stock_movements`: **143** (до: 143, после: 143)
  - `product_reference_models`: **125** (до: 125, после: 125)
  - `product_reference_aliases`: **533** (до: 533, после: 533)
  - `product_external_listings`: **408** (до: 408, после: 408)
  - `mobile_devices`: **3** (до: 3, после: 3, все активны)
- `PRAGMA quick_check`: `ok`
- `PRAGMA foreign_key_check`: `[]` (0 ошибок)

---

## 4. Результаты Smoke-тестов на продакшне (`scripts/smoke_stage06d_production.py`)

- **Шлюз / admin-shell mTLS:** `GET /health` -> `200 OK` (`status: ok`)
- **Защита PoP для неавторизованных клиентов:**
  - `GET /api/mobile/catalog/products` -> `401 Unauthorized`
  - `GET /api/mobile/reports/sales?period=today` -> `401 Unauthorized`
  - `GET /api/mobile/app/update/manifest` -> `401 Unauthorized`
  - `GET /api/mobile/app/update/apk?version_code=23` -> `401 Unauthorized`
  - `GET /api/mobile/products/by-barcode/200000000230` -> `401 Unauthorized`
- **Core внутренние read-only операции:**
  - `GET /health` -> `200 OK`
  - `GET /api/products/by-barcode/200000000230` -> `200 OK` (`Лазерное мфу 3 в 1 HP LaserJet 3052`)
  - `GET /api/products/?q=hp&status=in_stock&limit=3` -> `200 OK`
  - `GET /api/reports/sales?period=today` -> `200 OK`
- **Контейнеры VDS:**
  - `technoreboot-prod-core`: Up (healthy)
  - `technoreboot-prod-admin-shell`: Up (healthy)
  - `technoreboot-prod-repairs`: Up (healthy)
  - `technoreboot-prod-inventory-sales`: Up (healthy)
  - `technoreboot-prod-avito`: Up (healthy)
  - `technoreboot-prod-gateway`: Up (healthy)

---

## 5. План и готовность к откату (Rollback Readiness)

1. **Серверный откат:**
   - Пре-релизный коммит сохранен: `5ce792ce35f63cd8e3b78fa65e8e748e454cb33c`.
   - В случае необходимости отката серверного кода:
     ```bash
     bash /srv/technoreboot/app/deploy/production/update_code_only.sh 5ce792ce35f63cd8e3b78fa65e8e748e454cb33c
     ```
2. **Откат обновления приложения:**
   - На сервере сохранен предыдущий манифест: `/srv/technoreboot/data/releases/mobile/manifest.json.v22.bak`.
   - На сервере сохранен предыдущий APK: `/srv/technoreboot/data/releases/mobile/app-release-v22.apk`.
   - Если OTA не должен предлагаться:
     ```bash
     cp /srv/technoreboot/data/releases/mobile/manifest.json.v22.bak /srv/technoreboot/data/releases/mobile/manifest.json
     ```
3. **Резервная копия базы данных:**
   - Путь на VDS: `/srv/technoreboot/data/backups/pre_stage06d_rollout_20261009_045426/technoreboot.db`.

---

## 6. Единственное следующее действие владельца (Next Single OWNER Action)

На физическом телефоне **Samsung Galaxy S22 Ultra**:
1. Открыть установленное приложение **«Техноребут»** (боевая версия 1.6.0).
2. Перейти в **«Настройки»** -> нажать кнопку **«Проверить обновления»** (либо дождаться баннера обновления).
3. При появлении сообщения о версии **1.7.0 (сборка 23)** нажать **«Обновить»** -> подтвердить стандартную системную установку поверх существующего приложения без удаления данных.
4. Проверить работоспособность:
   - Вкладка **«Каталог»**: просмотр товаров, фильтрация по брендам и сортировка по цене.
   - Вкладка **«Отчеты»**: drill-down по цепочке Сегодня / Неделя / Месяц / Год и возврат кнопкой «Назад».
   - Вкладка **«POS»**: сканирование штрихкода товара.
