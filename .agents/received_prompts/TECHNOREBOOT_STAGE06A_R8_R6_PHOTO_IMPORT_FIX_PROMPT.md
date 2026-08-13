# TECHNOREBOOT — Stage06A-R8-R6 Fix Avito Photo Import

Репозиторий:

```powershell
C:\tbootit
```

Старт:

```text
Stage06A-R8-R5
Commit: 2395d32
```

Corrective stage. Не начинать R9 и Stage06B.

## Реальный owner result

Одиночный импорт собственного объявления уже проходит:

```text
Avito ID: 8313765236
Product ID: 58
Result: updated
Price: 6900 ₽
```

Но owner проверил Product 58:

```text
фотографий нет вообще
```

Значит:

```text
CORE_FIELDS_IMPORT = PASS
PHOTO_IMPORT = FAIL
```

Одиночный импорт пока НЕ считать полностью принятым.

## Цель

Довести фото по всей цепочке:

```text
Avito page
→ Chrome Extension
→ Local Bridge
→ avito-module
→ Core API
→ Core storage
→ product_photos
→ Product 58 UI
```

Не создавать новый Product.

Сохранять:

```text
Product ID 58
Avito ID 8313765236
price 6900
source_origin=avito
```

## Сначала диагностика

До исправлений зафиксировать:

```text
EXTENSION_EXTRACTED_PHOTO_COUNT
PAYLOAD_PHOTO_COUNT
BRIDGE_RECEIVED_PHOTO_COUNT
IMPORT_SERVICE_PHOTO_COUNT
CORE_PHOTO_REQUEST_COUNT
CORE_PHOTO_RESPONSES
PRODUCT_58_DB_PHOTO_COUNT
PRODUCT_58_STORAGE_FILE_COUNT
ROOT_CAUSE
```

Не логировать cookies, extension token, credentials, полный HTML страницы.

## Проверить content.js

Проверить фактическое извлечение фото с Avito.

Приоритет:

```text
1. JSON-LD image
2. embedded page JSON/state
3. semantic gallery DOM
4. img/src/srcset fallback
```

Поддержать JSON-LD:

```json
"image": "https://..."
```

```json
"image": ["https://...", "https://..."]
```

```json
"image": {"url": "https://..."}
```

Для `srcset` брать качественный вариант, а не маленький thumbnail.

До отправки:

```text
normalize
deduplicate
preserve gallery order
```

## Явный photo payload contract

Extension и bridge должны использовать один формат, например:

```json
"photos": [
  {"url": "https://...", "position": 0}
]
```

или существующий canonical формат проекта.

Не допускать ситуации:

```text
extension sends string[]
import_service expects dict[]
```

Добавить schema validation.

## Bridge diagnostics

В last ingest хранить safe metadata:

```text
photos_received
photos_forwarded
photos_imported
```

На `/avito/extension` показывать:

```text
Фотографий получено: N
Фотографий импортировано: M
```

Без длинных URL.

## Core owns photo persistence

Avito-module НЕ пишет напрямую в БД и storage.

Использовать Core HTTP API.

Если Core уже умеет remote photo import — использовать существующий endpoint.

Если нет — добавить минимальный Core-owned endpoint/service:

```text
HTTPS image URL
→ validate
→ download with timeout/size limit
→ validate Content-Type image/*
→ save through Core storage
→ create product_photos row
```

## SSRF safety

Если Core скачивает remote URL, блокировать:

```text
localhost
127.0.0.0/8
::1
private ranges
link-local
file://
ftp://
```

Разрешать обычные публичные HTTPS CDN URL.

## Если Avito CDN требует browser session

НЕ использовать:

```text
cookie export
session token export
debugger
stealth/fingerprint spoofing
```

Допустимый fallback только если диагностика докажет необходимость:

```text
extension fetches image as Blob inside ordinary authorized Chrome
→ sends only image bytes + filename/content-type to local bridge
→ bridge forwards multipart to Core
```

Cookies/session headers из Chrome наружу не передаются.

## Update semantics

После исправления повторная передача объявления должна:

```text
update Product 58
not create Product 59
not duplicate ProductExternalListing
add missing photos
```

## Idempotency

Повторный импорт тех же фото:

```text
does not duplicate photos
```

Использовать существующий Core dedup contract (URL/hash/external identity).

## Ordering

Сохранять порядок:

```text
position 0 = main photo
position 1...
```

## Partial failure

Если Product update прошёл, а photo import упал:

```text
status = partial
product_id = 58
photo_import = failed
```

Popup НЕ должен показывать полный success.

Показывать:

```text
Основные данные обновлены, но фотографии импортировать не удалось.
```

## Popup success

Только если фото тоже прошли:

```text
✓ Объявление импортировано.
Product ID: 58
Фотографий: N
```

## Tests — extension

Добавить:

```text
chrome-extension/technoreboot-avito/tests/test_photo_extraction_jsonld.py
chrome-extension/technoreboot-avito/tests/test_photo_extraction_gallery.py
chrome-extension/technoreboot-avito/tests/test_photo_srcset_quality.py
chrome-extension/technoreboot-avito/tests/test_photo_deduplication.py
```

## Tests — avito-module

Добавить:

```text
avito-module/tests/test_extension_photo_payload_contract.py
avito-module/tests/test_extension_photo_forwarding.py
avito-module/tests/test_extension_photo_import_result_counts.py
avito-module/tests/test_extension_photo_idempotency.py
```

## Tests — Core

Если Core меняется:

```text
core-api/tests/test_remote_product_photo_import.py
core-api/tests/test_remote_photo_ssrf_block.py
core-api/tests/test_remote_photo_content_type.py
core-api/tests/test_remote_photo_size_limit.py
core-api/tests/test_remote_photo_dedup.py
```

## Explicit regression

Для fixture объявления:

```text
Avito ID 8313765236
Product ID 58
photos >= 1
```

После isolated import:

```text
same Product ID
photo records > 0
photo files exist
photo URLs resolve in UI
```

## Live owner data safety

Не изменять Product 58 автоматически.

До owner action только read-only проверки.

Owner сам повторно передаст карточку после fix.

## Extension version

Если extension меняется:

```text
0.1.3 → 0.1.4
```

Обновить manifest, version labels, ZIP и Admin Shell download.

## Regression

Обязательно:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test_core_safe.ps1
docker compose exec -T inventory-sales-module pytest
docker compose exec -T avito-module pytest
docker compose exec -T repairs-module pytest
pytest admin-shell/tests
pytest chrome-extension/technoreboot-avito/tests
```

## Security

Проверить:

```text
cookies permission = absent
debugger permission = absent
proxy permission = absent
cookies transferred = 0
credentials transferred = 0
direct DB from avito-module = 0
direct storage from avito-module = 0
unsafe remote fetch = 0
```

## Docs

Обновить:

```text
docs/stage06a_r8_extension_photo_import.md
reports/stage06a_r8_r6_photo_import_report.md
chrome-extension/technoreboot-avito/README.md
README.md
logs/2026-08-12.md
```

## Git

Expected HEAD:

```text
2395d32
```

Only targeted add.

Запрещено:

```text
git add .
git add -A
git add -u
git reset
git clean
git rebase
git commit --amend
force push
```

Commit:

```powershell
git commit -m "Fix Avito extension photo import"
git push origin main
```

## Definition of Done

```text
photo-loss root cause found
extension extracts real photos
bridge receives photos
photo contract validated
Core owns persistence
Product 58 not duplicated
photos idempotent
order preserved
partial failures visible
all tests PASS
commit pushed
git clean
```

## Owner check

После R8-R6:

```text
1. Install extension 0.1.4 if version changed.
2. Open own Avito listing 8313765236.
3. Click «Передать объявление в Техноребут» ONE TIME.
4. Confirm Product ID remains 58.
5. Open Product 58.
6. Verify photos are visible.
7. Compare count/order/main photo with Avito.
```

STOP. Full account import still not authorized.

## Final status

```text
FINAL_STATUS:
TECHNOREBOOT_STAGE06A_R8_R6_PHOTO_IMPORT_READY_FOR_OWNER_CHECK

OWNER_PRODUCT_58_PHOTO_CHECK_REQUIRED: true
OWNER_ONE_ITEM_EXTENSION_IMPORT_NOT_YET_FULLY_ACCEPTED: true
FULL_ACCOUNT_IMPORT_NOT_YET_AUTHORIZED: true
DO_NOT_START_STAGE06A_R9_WITHOUT_OWNER_ACCEPTANCE: true
DO_NOT_START_STAGE06B_REVERSE_SYNC_WITHOUT_OWNER_ACCEPTANCE: true
```
