# Stage 12B — Production Deploy Extension Connection Switching

## Target
PRODUCTION_VDS: 144.31.15.88
LEGACY_VDS_TOUCHED: false

## Preflight
LOCAL_ACCEPTED_HEAD: 9bb8f121ed2e3398724d2391cf520e984773ad42
PROD_HEAD_BEFORE: 9316ada2e43f9ae5811fc36f5e2cb295fafba25f
PROD_6_SERVICES_HEALTHY_BEFORE: true
PROD_DB_QUICK_CHECK_BEFORE: ok

## Safety
BACKUP_CREATED: true
BACKUP_SHA256: c867b8e4639646621ad773b58d5c26b187d99f9dac5c89733ea4fb15adcbc887
BACKUP_MANIFEST_OK: true
CHECKPOINT_CREATED: true
CHECKPOINT_ID: checkpoint_20260917_121040_9316ada2

## Deployment
PROD_HEAD_AFTER: 9bb8f121ed2e3398724d2391cf520e984773ad42
ADMIN_SHELL_REBUILT: true
AVITO_MODULE_REBUILT: true
OTHER_SERVICES_REBUILT: false
DB_MIGRATION_APPLIED: false
LOCAL_DB_COPIED_TO_PROD: false
LOCAL_MEDIA_COPIED_TO_PROD: false

## Extension
EXTENSION_VERSION: 0.2.63
EXTENSION_DOWNLOAD_OK: true
EXTENSION_ZIP_SHA256: bbaf780f75647c598c0725ad2de30239f865ea311ca529d405978960d1a16f9b
EXTENSION_HASH_MATCHES_ACCEPTED: true
CURRENT_SERVER_ADDRESS_UI_PRESENT: true
DISCONNECT_UI_PRESENT: true
RECONNECT_UI_PRESENT: true
LEGACY_VDS_NOT_DEFAULT: true
DYNAMIC_HOST_PERMISSION_PRESENT: true

## Pairing API
REVOKE_ENDPOINT_PRESENT: true
UNPAIR_ENDPOINT_PRESENT: true
ISOLATED_TOKEN_REVOKE_TEST: passed
REAL_OWNER_TOKEN_PRESERVED: true

## Business Invariants
PRODUCTS_BEFORE: 241
PRODUCTS_AFTER: 241
SALES_BEFORE: 5
SALES_AFTER: 5
REPAIRS_BEFORE: 1
REPAIRS_AFTER: 1
PHOTOS_BEFORE: 237
PHOTOS_AFTER: 237
EXTERNAL_LISTINGS_BEFORE: 237
EXTERNAL_LISTINGS_AFTER: 237
AVITO_TASKS_BEFORE: 5
AVITO_TASKS_AFTER: 5
STORAGE_FILES_BEFORE: 237
STORAGE_FILES_AFTER: 237
BUSINESS_DATA_PRESERVED: true

## Runtime
PROD_6_SERVICES_HEALTHY_AFTER: true
DB_QUICK_CHECK_AFTER: ok
FOREIGN_KEY_CHECK: ok (0 violations)
MTLS_REQUIRED: true (403 without cert)
INTERNAL_PORTS_PRIVATE: true (only 22, 80, 443 listening)
ROOT_OK: true (200 OK)
AVITO_EXTENSION_PAGE_OK: true (200 OK)
AVITO_EXTENSION_DOWNLOAD_OK: true (200 OK, 73096 bytes)
SALES_OK: true (200 OK)
REPAIRS_OK: true (200 OK)
HELP_OK: true (200 OK)

## Owner Acceptance
OWNER_BROWSER_ACCEPTANCE: PENDING

FINAL_STATUS:
TECHNOREBOOT_STAGE12B_PRODUCTION_READY_FOR_OWNER_ACCEPTANCE

## Owner Browser Acceptance Steps
1. Open in Google Chrome: `https://144.31.15.88/avito/extension` (using Owner client certificate).
2. Download and update extension v0.2.63 via button «Скачать расширение (ZIP, v0.2.63)».
3. Open extension popup in Chrome toolbar.
4. Confirm current server address `https://144.31.15.88` is displayed at the top with green status «✓ Подключено к серверу».
5. Click red button `[Отключиться]`.
6. Confirm popup transitions to «Расширение не подключено к серверу» and shows the pairing form.
7. On web page `https://144.31.15.88/avito/extension`, click «Сгенерировать код».
8. Enter the 6-digit code in the extension popup and click `[Подключить]`.
9. Confirm popup again shows `https://144.31.15.88` and is fully paired.
